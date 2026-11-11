/* Sampling profiler that runs on the Vita itself (the PC profile misleads: long double,
 * -O1). Active only when prof.txt exists in the data directory. Every generated function
 * stores its address in Cpu.cur_fn on entry (T123_ENTER); a sampler thread reads that
 * every ~1 ms for each registered guest thread and, every 10 s, writes the most frequent
 * functions to the trace as "# prof" lines.
 *
 * Caveat: cur_fn is the LAST function entered, not the one running, so after a callee
 * returns its time is still charged to the callee until the next call; blocked threads
 * keep their last function. It ranks "where the thread spends its calls", good enough to
 * pick the functions to optimise, not an exact profile. */
#include "win32.h"

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { MAX_CPUS = 12, SLOTS = 4096, TOP = 20 };
const char *com_name(uint32_t fake, char *buf, unsigned size); /* com.c */
static void ring_push(void);

typedef struct {
    Cpu *cpu;
    uint32_t tag;
    uint32_t key[SLOTS];
    uint32_t count[SLOTS];
    uint32_t total;
} Slot;

static Slot slots[MAX_CPUS];
static volatile int active, started;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static int enabled(void) {
#ifdef __vita__
    FILE *f = fopen("ux0:data/touhou123vita/prof.txt", "rb");
#else
    FILE *f = fopen("prof.txt", "rb");
#endif
    if (f) fclose(f);
    return f != NULL;
}

static void sample(Slot *s) {
    uint32_t fn = s->cpu->cur_fn;
    if (!fn) return;
    unsigned h = (fn >> 2) * 2654435761u % SLOTS;
    for (unsigned k = 0; k < SLOTS; k++, h = (h + 1) % SLOTS) {
        if (s->key[h] == fn) { s->count[h]++; break; }
        if (!s->key[h]) { s->key[h] = fn; s->count[h] = 1; break; }
    }
    s->total++;
}

static void report(void) {
    for (unsigned i = 0; i < MAX_CPUS; i++) {
        Slot *s = &slots[i];
        if (!s->cpu || s->total < 200) { if (s->cpu) { memset(s->key, 0, sizeof s->key); s->total = 0; } continue; }
        trace("# prof: thread %08x, %u samples", s->tag, s->total);
        for (unsigned n = 0; n < TOP; n++) {
            unsigned best = SLOTS;
            for (unsigned h = 0; h < SLOTS; h++)
                if (s->key[h] && (best == SLOTS || s->count[h] > s->count[best])) best = h;
            if (best == SLOTS || s->count[best] * 200 < s->total) break; /* under 0.5 % */
            char buf[96];
            const char *name = api_name(s->key[best]);
            if (!name) name = com_name(s->key[best], buf, sizeof buf);
            if (name)
                trace("# prof:   [host] %s %5.1f %%", name, 100.0 * s->count[best] / s->total);
            else
                trace("# prof:   f_%08x %5.1f %%", s->key[best], 100.0 * s->count[best] / s->total);
            s->count[best] = 0; s->key[best] = 0xFFFFFFFFu; /* mark as listed */
        }
        memset(s->key, 0, sizeof s->key);
        memset(s->count, 0, sizeof s->count);
        s->total = 0;
    }
}

static void *sampler(void *arg) {
    (void)arg;
    uint64_t next = platform_ticks_us() + 10000000;
    for (;;) {
        platform_sleep_ms(1);
        pthread_mutex_lock(&lock);
        for (unsigned i = 0; i < MAX_CPUS; i++)
            if (slots[i].cpu) sample(&slots[i]);
        ring_push();
        if (platform_ticks_us() >= next) { report(); next += 10000000; }
        pthread_mutex_unlock(&lock);
    }
    return NULL;
}

int vprof_active(void) { return active; }

/* Samples of the game thread with their time, to explain single long steps. */
enum { RING = 4096 };
static Cpu *game;
static uint32_t ring_fn[RING];
static uint64_t ring_t[RING];
static unsigned ring_pos;
void vprof_set_game(Cpu *c) { game = c; }
static void ring_push(void) {
    if (!game) return;
    ring_fn[ring_pos % RING] = game->cur_fn;
    ring_t[ring_pos % RING] = platform_ticks_us();
    ring_pos++;
}
/* One trace line: the functions sampled on the game thread between from and to. */
void vprof_window(uint64_t from, uint64_t to, uint64_t work) {
    if (!active) return;
    static uint32_t key[64], cnt[64];
    unsigned n = 0, total = 0;
    memset(cnt, 0, sizeof cnt);
    pthread_mutex_lock(&lock);
    for (unsigned k = 0; k < RING && k < ring_pos; k++) {
        unsigned i = (ring_pos - 1 - k) % RING;
        if (ring_t[i] < from) break;
        if (ring_t[i] > to) continue;
        uint32_t fn = ring_fn[i];
        unsigned j = 0;
        while (j < n && key[j] != fn) j++;
        if (j == n && n < 64) key[n++] = fn;
        if (j < 64) cnt[j]++;
        total++;
    }
    pthread_mutex_unlock(&lock);
    char line[512];
    int len = snprintf(line, sizeof line, "# long step: %llu us of work, %u samples:", (unsigned long long)work, total);
    for (unsigned r = 0; r < 6; r++) {
        unsigned best = 64;
        for (unsigned j = 0; j < n; j++) if (cnt[j] && (best == 64 || cnt[j] > cnt[best])) best = j;
        if (best == 64) break;
        char buf[96];
        const char *name = api_name(key[best]);
        if (!name) name = com_name(key[best], buf, sizeof buf);
        if (name) len += snprintf(line + len, sizeof line - len, " %s %u", name, cnt[best]);
        else len += snprintf(line + len, sizeof line - len, " f_%08x %u", key[best], cnt[best]);
        cnt[best] = 0;
        if (len >= (int)sizeof line - 100) break;
    }
    trace("%s", line);
}

void vprof_register(Cpu *c, uint32_t tag) {
    static int checked;
    if (!checked) { checked = 1; active = enabled(); }
    if (!active) return;
    pthread_mutex_lock(&lock);
    for (unsigned i = 0; i < MAX_CPUS; i++)
        if (!slots[i].cpu || slots[i].cpu == c) { slots[i].cpu = c; slots[i].tag = tag; break; }
    if (!started) {
        started = 1;
        pthread_t t;
        pthread_create(&t, NULL, sampler, NULL);
        trace("# prof: sampling profiler on (prof.txt)");
    }
    pthread_mutex_unlock(&lock);
}
