/* Host support: guest heap, virtual memory, handles, path mapping, imports, traces. */
#include "win32.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- traces ---------------------------------------------------------------------------- */
static FILE *trace_file;
unsigned long long import_calls;

void trace(const char *fmt, ...) {
    if (!trace_file) {
        trace_file = fopen("host-trace.log", "w");
        if (!trace_file)
            return;
    }
    va_list ap;
    va_start(ap, fmt);
    vfprintf(trace_file, fmt, ap);
    va_end(ap);
    fputc('\n', trace_file);
    fflush(trace_file);
}

/* -- guest heap -------------------------------------------------------------------------
 * Size-class free lists (16-byte classes up to 4 KiB) plus a first-fit list for large
 * blocks; a 16-byte header before every block holds the requested size. Blocks are not
 * coalesced: adequate for bring-up, to be measured before Vita (F3). */
enum { HDR = 16, CLASS_STEP = 16, CLASSES = 256, MAGIC = 0x48454150u /* "HEAP" */ };
static uint32_t heap_top = GUEST_HEAP_BASE, heap_committed = GUEST_HEAP_BASE;
static uint32_t free_class[CLASSES + 1];
static uint32_t free_large;

static uint32_t round_up(uint32_t n) { return (n + CLASS_STEP - 1) & ~(uint32_t)(CLASS_STEP - 1); }

static uint32_t block_capacity(uint32_t p) { return rd32(p - HDR + 8); }

static uint32_t carve(uint32_t capacity) {
    uint32_t block = heap_top;
    uint32_t end = block + HDR + capacity;
    if (end > GUEST_HEAP_BASE + GUEST_HEAP_SIZE)
        return 0;
    while (heap_committed < end) {
        if (guest_map(heap_committed, 0x100000))
            return 0;
        heap_committed += 0x100000;
    }
    heap_top = end;
    wr32(block + 8, capacity);
    return block + HDR;
}

uint32_t heap_alloc(uint32_t size, int zero) {
    uint32_t capacity = round_up(size ? size : 1), p = 0;
    if (capacity / CLASS_STEP <= CLASSES) {
        uint32_t k = capacity / CLASS_STEP;
        if (free_class[k]) {
            p = free_class[k];
            free_class[k] = rd32(p);
        }
    } else {
        uint32_t prev = 0;
        for (uint32_t q = free_large; q; prev = q, q = rd32(q)) {
            if (block_capacity(q) >= capacity && block_capacity(q) <= capacity * 2) {
                if (prev) wr32(prev, rd32(q)); else free_large = rd32(q);
                p = q;
                break;
            }
        }
    }
    if (!p)
        p = carve(capacity);
    if (!p)
        return 0;
    wr32(p - HDR, size);
    wr32(p - HDR + 4, MAGIC);
    if (zero)
        memset(G(p), 0, block_capacity(p));
    return p;
}

void heap_free(uint32_t p) {
    if (!p || rd32(p - HDR + 4) != MAGIC)
        return;
    wr32(p - HDR + 4, 0);
    uint32_t capacity = block_capacity(p);
    if (capacity / CLASS_STEP <= CLASSES) {
        wr32(p, free_class[capacity / CLASS_STEP]);
        free_class[capacity / CLASS_STEP] = p;
    } else {
        wr32(p, free_large);
        free_large = p;
    }
}

uint32_t heap_size(uint32_t p) {
    return p && rd32(p - HDR + 4) == MAGIC ? rd32(p - HDR) : 0xFFFFFFFFu;
}

uint32_t heap_realloc(uint32_t p, uint32_t size, int zero) {
    if (!p)
        return heap_alloc(size, zero);
    uint32_t old = heap_size(p);
    if (size <= block_capacity(p)) {
        if (zero && size > old)
            memset(G(p + old), 0, size - old);
        wr32(p - HDR, size);
        return p;
    }
    uint32_t q = heap_alloc(size, zero);
    if (!q)
        return 0;
    memcpy(G(q), G(p), old);
    heap_free(p);
    return q;
}

uint32_t guest_strdup(const char *s) {
    uint32_t p = heap_alloc((uint32_t)strlen(s) + 1, 0);
    if (p)
        strcpy(STR(p), s);
    return p;
}

/* -- virtual memory: bump allocation in its own region, committed on request -------- */
static uint32_t virtual_top = GUEST_VIRTUAL_BASE;

uint32_t virtual_alloc(uint32_t address, uint32_t size) {
    size = (size + 0xFFFF) & ~0xFFFFu;
    if (address) {
        /* Commit inside an earlier reservation. */
        return guest_map(address, size) ? 0 : address;
    }
    if (virtual_top + size > GUEST_VIRTUAL_BASE + GUEST_VIRTUAL_SIZE || guest_map(virtual_top, size))
        return 0;
    uint32_t r = virtual_top;
    virtual_top += size;
    return r;
}

/* -- handles --------------------------------------------------------------------------- */
typedef struct { int type; void *host; uint32_t extra; } Handle;
static Handle handles[4096];
uint32_t last_error;

uint32_t handle_new(int type, void *host, uint32_t extra) {
    for (unsigned i = 1; i < 4096; i++) {
        if (!handles[i].type) {
            handles[i] = (Handle){type, host, extra};
            return 0x1000u + i * 4;
        }
    }
    return 0;
}

static Handle *slot(uint32_t h) {
    if (h < 0x1000u || ((h - 0x1000u) & 3))
        return NULL;
    unsigned i = (h - 0x1000u) / 4;
    return i < 4096 && handles[i].type ? &handles[i] : NULL;
}

void *handle_get(uint32_t h, int type) {
    Handle *s = slot(h);
    return s && s->type == type ? s->host : NULL;
}

void handle_close(uint32_t h) {
    Handle *s = slot(h);
    if (!s)
        return;
    if (s->type == H_FILE && s->host)
        fclose(s->host);
    memset(s, 0, sizeof *s);
}

/* -- paths ------------------------------------------------------------------------------- */
char host_data_dir[1024] = ".";
const char *guest_exe_path = "C:\\th123\\th123.exe";

void path_to_host(const char *guest_path, char *out, size_t size) {
    const char *p = guest_path;
    static const char prefix[] = "C:\\th123\\";
    if (!_strnicmp(p, prefix, sizeof prefix - 1))
        p += sizeof prefix - 1;
    else if (p[0] && p[1] == ':')
        p += 2; /* other absolute paths are kept under the data directory */
    while (*p == '\\' || *p == '/')
        p++;
    snprintf(out, size, "%s/%s", host_data_dir, p);
    for (char *q = out; *q; q++)
        if (*q == '\\')
            *q = '/';
}

/* -- imports ------------------------------------------------------------------------------ */
typedef struct { char name[64]; GuestFn fn; unsigned long long calls; } Fake;
static Fake fakes[1024];
static unsigned fake_count;
static unsigned recent[64], recent_pos;

/* Every fake address dispatches here: count, remember, then run the implementation. */
static void api_dispatch(Cpu *c) {
    unsigned i = (guest_current_target - GUEST_FAKE_BASE) / 16;
    fakes[i].calls++;
    import_calls++;
    recent[recent_pos++ % 64] = i;
    fakes[i].fn(c);
}

void trace_summary(void) {
    trace("# Win32 calls by function:");
    for (unsigned i = 0; i < fake_count; i++)
        if (fakes[i].calls)
            trace("#   %8llu %s", fakes[i].calls, fakes[i].name);
    trace("# last calls (oldest first):");
    unsigned n = recent_pos < 64 ? recent_pos : 64;
    for (unsigned k = 0; k < n; k++)
        trace("#   %s", fakes[recent[(recent_pos - n + k) % 64]].name);
}

static void unimplemented(Cpu *c) {
    const char *name = api_name(guest_current_target);
    char why[160];
    snprintf(why, sizeof why, "import %s is not implemented", name ? name : "?");
    host_exit(c, 0xDEAD, why);
}

static GuestFn lookup(const char *name) {
    const ApiEntry *tables[] = {win32_kernel32, win32_other};
    for (unsigned t = 0; t < 2; t++)
        for (const ApiEntry *e = tables[t]; e->name; e++)
            if (!strcmp(e->name, name))
                return e->fn;
    return NULL;
}

static uint32_t fake_for(const char *name, int create_unimplemented) {
    for (unsigned i = 0; i < fake_count; i++)
        if (!strcmp(fakes[i].name, name))
            return GUEST_FAKE_BASE + 16u * i;
    GuestFn fn = lookup(name);
    if (!fn && !create_unimplemented)
        return 0;
    if (fake_count == 1024)
        return 0;
    snprintf(fakes[fake_count].name, sizeof fakes[0].name, "%s", name);
    fakes[fake_count].fn = fn ? fn : unimplemented;
    uint32_t address = GUEST_FAKE_BASE + 16u * fake_count;
    guest_intercept(address, api_dispatch);
    fake_count++;
    return address;
}

const char *api_name(uint32_t fake) {
    if (fake < GUEST_FAKE_BASE || (fake - GUEST_FAKE_BASE) / 16 >= fake_count)
        return NULL;
    return fakes[(fake - GUEST_FAKE_BASE) / 16].name;
}

uint32_t api_address(const char *name) { return fake_for(name, 0); }

int imports_init(void) {
    uint32_t base = guest_image_base;
    uint32_t pe = base + rd32(base + 0x3C);
    uint32_t dir = rd32(pe + 24 + 104); /* optional header: import directory RVA */
    unsigned total = 0, implemented = 0;
    for (uint32_t d = base + dir; rd32(d + 12); d += 20) {
        uint32_t names = rd32(d) ? rd32(d) : rd32(d + 16);
        uint32_t iat = base + rd32(d + 16);
        for (unsigned i = 0;; i++) {
            uint32_t thunk = rd32(base + names + 4 * i);
            if (!thunk)
                break;
            char name[64];
            if (thunk & 0x80000000u)
                snprintf(name, sizeof name, "%s#%u", STR(base + rd32(d + 12)), thunk & 0xFFFF);
            else
                snprintf(name, sizeof name, "%s", STR(base + thunk + 2));
            wr32(iat + 4 * i, fake_for(name, 1));
            total++;
            implemented += lookup(name) != NULL;
        }
    }
    trace("# imports: %u, implemented: %u", total, implemented);
    return 0;
}
