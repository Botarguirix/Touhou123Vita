/* Texture storage on the Vita. The C heap (_newlib_heap_size_user, 32 MiB) ran out
 * during loading (core dump: memcpy from NULL in Texture_LockRect), while the game
 * keeps about 60 MiB of textures alive on PC. They go to one CPU-mapped CDRAM block
 * instead, managed as an address-ordered free list that splits on allocation and
 * merges neighbours on free. vitaGL (H3) will take over this memory. */
#include <psp2/kernel/sysmem.h>
#include <pthread.h>
#include <stdint.h>
#include <string.h>

#include "../host/win32.h"

#define POOL_BYTES (96u << 20)
enum { ALIGN = 64, MIN_SPLIT = 4096 };

typedef struct Block { size_t size; struct Block *next; } Block; /* size includes header */

static uint8_t *pool;
static Block *free_list;
static size_t live, peak;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static int pool_init(void) {
    SceUID id = sceKernelAllocMemBlock("t123_textures", SCE_KERNEL_MEMBLOCK_TYPE_USER_CDRAM_RW, POOL_BYTES, NULL);
    if (id < 0 || sceKernelGetMemBlockBase(id, (void **)&pool) < 0) {
        trace("# texture pool: CDRAM block of %u MiB not available (%08x)", POOL_BYTES >> 20, (unsigned)id);
        return -1;
    }
    free_list = (Block *)pool;
    free_list->size = POOL_BYTES;
    free_list->next = NULL;
    return 0;
}

void *platform_texture_alloc(size_t bytes) {
    size_t need = (bytes + sizeof(Block) + ALIGN - 1) & ~(size_t)(ALIGN - 1);
    void *result = NULL;
    pthread_mutex_lock(&lock);
    if (pool || pool_init() == 0) {
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
            result = b + 1;
            break;
        }
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
    pthread_mutex_unlock(&lock);
}
