/* Texture storage on the Vita: the game keeps ~155 MiB of textures alive, stored
 * deflated by d3d9.c (~16 MiB). The C heap (32 MiB) is too small next to the rest
 * of the host, so they live in one user-RAM block reserved before vitaGL claims the
 * remaining memory (CDRAM is left to vitaGL for the uploaded textures), managed as an
 * address-ordered free list that splits on allocation and merges neighbours on free. */
#include <psp2/kernel/sysmem.h>
#include <pthread.h>
#include <stdint.h>
#include <string.h>

#include "../host/win32.h"

#define POOL_BYTES (24u << 20) /* deflated textures peak at 16 MiB (Vita3K, 60 s) */
enum { ALIGN = 64, MIN_SPLIT = 4096 };

typedef struct Block { size_t size; struct Block *next; } Block; /* size includes header */

static uint8_t *pool;
static Block *free_list;
static size_t live, peak;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static int pool_init(void) {
    SceUID id = sceKernelAllocMemBlock("t123_textures", SCE_KERNEL_MEMBLOCK_TYPE_USER_RW, POOL_BYTES, NULL);
    if (id < 0 || sceKernelGetMemBlockBase(id, (void **)&pool) < 0) {
        trace("# texture pool: block of %u MiB not available (%08x)", POOL_BYTES >> 20, (unsigned)id);
        return -1;
    }
    free_list = (Block *)pool;
    free_list->size = POOL_BYTES;
    free_list->next = NULL;
    return 0;
}

void texture_pool_reserve(void) {
    pthread_mutex_lock(&lock);
    if (!pool) pool_init();
    pthread_mutex_unlock(&lock);
}

/* Under lock: address-ordered insert of a free block, merging with touching neighbours. */
static void insert_free(Block *b) {
    Block *prev = NULL, *next = free_list;
    while (next && next < b) { prev = next; next = next->next; }
    if (next && (uint8_t *)b + b->size == (uint8_t *)next) {
        b->size += next->size;
        next = next->next;
    }
    b->next = next;
    if (prev && (uint8_t *)prev + prev->size == (uint8_t *)b) {
        prev->size += b->size;
        prev->next = next;
    } else if (prev) {
        prev->next = b;
    } else {
        free_list = b;
    }
}

static void *take(size_t need) {
    Block **link = &free_list;
    for (Block *b = free_list; b; link = &b->next, b = b->next) {
        if (b->size < need)
            continue;
        if (b->size - need >= MIN_SPLIT) {
            Block *rest = (Block *)((uint8_t *)b + need);
            rest->size = b->size - need;
            rest->next = b->next;
            *link = rest;
            b->size = need;
        } else {
            *link = b->next;
        }
        live += b->size;
        if (live > peak) peak = live;
        return b + 1;
    }
    return NULL;
}

/* The first 24 MiB ran out once the game went past the title (hardware): the pool
   grows by 4 MiB chunks, from CDRAM first, then from user RAM while 8 MiB stay free
   for thread stacks and file buffers. */
enum { CHUNK = 4u << 20, USER_RESERVE = 8u << 20 };
static int grow(void) {
    static unsigned chunks;
    SceKernelFreeMemorySizeInfo info = {sizeof info};
    sceKernelGetFreeMemorySize(&info);
    SceKernelMemBlockType types[2] = {SCE_KERNEL_MEMBLOCK_TYPE_USER_CDRAM_RW, SCE_KERNEL_MEMBLOCK_TYPE_USER_RW};
    int allowed[2] = {info.size_cdram >= CHUNK, info.size_user >= CHUNK + USER_RESERVE};
    for (unsigned k = 0; k < 2; k++) {
        if (!allowed[k])
            continue;
        void *base = NULL;
        SceUID id = sceKernelAllocMemBlock("t123_textures+", types[k], CHUNK, NULL);
        if (id < 0 || sceKernelGetMemBlockBase(id, &base) < 0)
            continue;
        Block *b = base;
        b->size = CHUNK;
        insert_free(b);
        chunks++;
        trace("# texture pool: +%u MiB from %s (chunk %u, live %u KiB)", CHUNK >> 20,
              k ? "user RAM" : "CDRAM", chunks, (unsigned)(live >> 10));
        return 0;
    }
    return -1;
}

void *platform_texture_alloc(size_t bytes) {
    size_t need = (bytes + sizeof(Block) + ALIGN - 1) & ~(size_t)(ALIGN - 1);
    void *result = NULL;
    pthread_mutex_lock(&lock);
    if (pool || pool_init() == 0) {
        result = take(need);
        if (!result && need <= CHUNK && grow() == 0)
            result = take(need);
        if (!result)
            trace("# texture pool exhausted: request %u bytes, live %u KiB, peak %u KiB",
                  (unsigned)bytes, (unsigned)(live >> 10), (unsigned)(peak >> 10));
    }
    pthread_mutex_unlock(&lock);
    if (result)
        memset(result, 0, bytes);
    return result;
}

void platform_texture_free(void *p) {
    if (!p)
        return;
    Block *b = (Block *)p - 1;
    pthread_mutex_lock(&lock);
    live -= b->size;
    insert_free(b);
    pthread_mutex_unlock(&lock);
}
