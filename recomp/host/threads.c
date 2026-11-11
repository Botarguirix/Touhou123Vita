/* Real threads for the recompiled game (F2.1): every guest thread is a host thread
 * with its own Cpu, guest stack, TIB (fs:) and TLS slots. Critical sections, events
 * and waits map to pthread primitives. Portable: pthreads exist on the PC toolchain
 * (winpthreads) and in VitaSDK. */
#include "win32.h"

#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef __vita__
#include <psp2/kernel/threadmgr.h>
#endif

/* Guest layout for secondary threads: TIBs after the main TIB/PEB, stacks in the free
   range below the heap. */
enum { MAX_THREADS = 24, THREAD_TIB_BASE = 0x00902000u, THREAD_STACK_BASE = 0x00A00000u,
       THREAD_STACK_SIZE = 0x00040000u };
_Static_assert(THREAD_STACK_BASE + MAX_THREADS * THREAD_STACK_SIZE <= GUEST_HEAP_BASE, "thread stacks");

#define API(name) static void name(Cpu *c)

typedef struct {
    pthread_mutex_t m;
    pthread_cond_t cv;
    int manual, signaled;
    uint64_t set_at;     /* when SetEvent last ran (wake-up latency probe, prof.txt only) */
} Event;

/* Wake-up latency: time from SetEvent to the waiter running again, per waiting thread.
   Only measured while the sampling profiler is on. */
/* NOTE: VitaSDK's __thread is one address for all threads, so wake_tag is only right on
   PC; the per-thread labels of "# wake-ups" are unreliable on the Vita (the totals are
   fine). The game thread is identified by its Cpu instead. */
static __thread uint32_t wake_tag;
static Cpu *game_cpu;
static pthread_mutex_t table_lock_wake = PTHREAD_MUTEX_INITIALIZER;
static struct { uint32_t tag; uint64_t n, sum, max, over1, over4, over8; } wake[16];
static uint64_t wake_report_at;
static void wake_record(uint64_t lat) {
    pthread_mutex_lock(&table_lock_wake);
    unsigned i = 0;
    while (i < 15 && wake[i].tag && wake[i].tag != wake_tag) i++;
    wake[i].tag = wake_tag;
    wake[i].n++; wake[i].sum += lat;
    if (lat > wake[i].max) wake[i].max = lat;
    wake[i].over1 += lat > 1000; wake[i].over4 += lat > 4000; wake[i].over8 += lat > 8000;
    uint64_t now = platform_ticks_us();
    if (!wake_report_at) wake_report_at = now + 10000000;
    if (now >= wake_report_at) {
        wake_report_at = now + 10000000;
        for (unsigned k = 0; k < 16; k++)
            if (wake[k].n > 50)
                trace("# wake-ups: thread %08x: %llu, %llu us avg, worst %llu us, >1 ms %llu, >4 ms %llu, >8 ms %llu",
                      wake[k].tag, (unsigned long long)wake[k].n, (unsigned long long)(wake[k].sum / wake[k].n),
                      (unsigned long long)wake[k].max, (unsigned long long)wake[k].over1,
                      (unsigned long long)wake[k].over4, (unsigned long long)wake[k].over8);
        memset(wake, 0, sizeof wake);
    }
    pthread_mutex_unlock(&table_lock_wake);
}

typedef struct {
    Event done;          /* signaled when the guest thread returns */
    uint32_t start, param, exit_code, tib;
    unsigned index;
    pthread_t host;
    int uid, priority;   /* Vita thread and its pending Win32 priority (SetThreadPriority) */
    Cpu cpu;            /* not _Thread_local: shared by all threads on the Vita */
} Thread;

static pthread_mutex_t table_lock = PTHREAD_MUTEX_INITIALIZER;
static Thread *threads[MAX_THREADS];

static void event_init(Event *e, int manual, int signaled) {
    pthread_mutex_init(&e->m, NULL);
    pthread_cond_init(&e->cv, NULL);
    e->manual = manual;
    e->signaled = signaled;
}

static void event_set(Event *e) {
    pthread_mutex_lock(&e->m);
    if (vprof_active()) e->set_at = platform_ticks_us();
    e->signaled = 1;
    pthread_cond_broadcast(&e->cv);
    pthread_mutex_unlock(&e->m);
}

/* The game's frame clock is a thread that waits 16 or 17 ms on an event, forever (0x4192a0),
   and wakes the game's threads each time: a timed wait that ends a few tenths of a
   millisecond late costs the game its 60 Hz (the traces showed 59.0 steps per second even
   in idle menus). Timed waits of 8 ms or more therefore sleep to ~1.5 ms before the
   deadline and spin the rest. The lateness of those waits is reported every 10 s. */
enum { SPIN_US = 1500, PRECISE_MIN_MS = 8 };
static uint64_t tw_count, tw_late_sum, tw_late_max, tw_report_at;
static void timed_wait_report(uint64_t now) {
    if (!tw_report_at) tw_report_at = now + 10000000;
    if (now < tw_report_at || !tw_count) return;
    tw_report_at = now + 10000000;
    trace("# timed waits (>= %d ms): %llu, ended %llu us late on average, worst %llu us", PRECISE_MIN_MS,
          (unsigned long long)tw_count, (unsigned long long)(tw_late_sum / tw_count), (unsigned long long)tw_late_max);
    tw_count = tw_late_sum = tw_late_max = 0;
}

/* 0 = signaled (WAIT_OBJECT_0), 0x102 = WAIT_TIMEOUT */
static uint32_t event_wait(Event *e, uint32_t ms) {
    pthread_mutex_lock(&e->m);
    int blocked = !e->signaled && ms != 0; /* had to wait for a SetEvent */
    if (!e->signaled && ms != 0xFFFFFFFFu) {
        uint64_t start = platform_ticks_us(), deadline = start + (uint64_t)ms * 1000u;
        int precise = ms >= PRECISE_MIN_MS;
        uint64_t coarse_us = precise ? (uint64_t)ms * 1000u - SPIN_US : (uint64_t)ms * 1000u;
        struct timespec until;
        clock_gettime(CLOCK_REALTIME, &until);
        until.tv_sec += (time_t)(coarse_us / 1000000u);
        until.tv_nsec += (long)(coarse_us % 1000000u) * 1000L;
        if (until.tv_nsec >= 1000000000L) { until.tv_sec++; until.tv_nsec -= 1000000000L; }
        while (!e->signaled)
            if (pthread_cond_timedwait(&e->cv, &e->m, &until) == ETIMEDOUT)
                break;
        if (precise && !e->signaled) {
            /* fine part: poll with the lock released so SetEvent can still get in */
            while (!e->signaled && platform_ticks_us() < deadline) {
                pthread_mutex_unlock(&e->m);
                pthread_mutex_lock(&e->m);
            }
            if (!e->signaled) {
                uint64_t end = platform_ticks_us(), late = end > deadline ? end - deadline : 0;
                tw_count++; tw_late_sum += late;
                if (late > tw_late_max) tw_late_max = late;
                timed_wait_report(end);
            }
        }
    } else {
        while (!e->signaled)
            pthread_cond_wait(&e->cv, &e->m);
    }
    uint32_t r = e->signaled ? 0 : 0x102;
    uint64_t lat = 0;
    if (e->signaled && blocked && e->set_at && vprof_active()) {
        uint64_t now = platform_ticks_us();
        lat = now > e->set_at ? now - e->set_at : 0;
    }
    if (e->signaled && !e->manual)
        e->signaled = 0;
    pthread_mutex_unlock(&e->m);
    if (lat || (blocked && r == 0 && vprof_active() && e->set_at)) wake_record(lat);
    return r;
}

/* -- critical sections, keyed by the guest CRITICAL_SECTION address --------------- */
enum { CS_SLOTS = 4096 };
static struct { uint32_t address; pthread_mutex_t m; } sections[CS_SLOTS];

static pthread_mutex_t *section(uint32_t address) {
    unsigned h = (address >> 2) % CS_SLOTS;
    pthread_mutex_lock(&table_lock);
    for (unsigned k = 0; k < CS_SLOTS; k++, h = (h + 1) % CS_SLOTS) {
        if (sections[h].address == address) break;
        if (!sections[h].address) {
            pthread_mutexattr_t attr;
            pthread_mutexattr_init(&attr);
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
            pthread_mutex_init(&sections[h].m, &attr);
            sections[h].address = address;
            break;
        }
    }
    pthread_mutex_unlock(&table_lock);
    return &sections[h].m;
}

API(InitializeCriticalSection) { (void)section(ARG(c, 0)); ret_stdcall(c, 0, 1); }
API(InitializeCriticalSectionAndSpinCount) { (void)section(ARG(c, 0)); ret_stdcall(c, 1, 2); }
API(DeleteCriticalSection) { ret_stdcall(c, 0, 1); }
API(EnterCriticalSection) { pthread_mutex_lock(section(ARG(c, 0))); ret_stdcall(c, 0, 1); }
API(LeaveCriticalSection) { pthread_mutex_unlock(section(ARG(c, 0))); ret_stdcall(c, 0, 1); }
API(TryEnterCriticalSection) { ret_stdcall(c, pthread_mutex_trylock(section(ARG(c, 0))) == 0, 1); }

/* -- events and waits --------------------------------------------------------------- */
API(CreateEventA) {
    Event *e = malloc(sizeof *e);
    event_init(e, (int)ARG(c, 1), (int)ARG(c, 2));
    uint32_t h = handle_new(H_EVENT, e, 0);
    trace("CreateEventA(manual=%u, initial=%u) = %08x", ARG(c, 1), ARG(c, 2), h);
    ret_stdcall(c, h, 4);
}
API(SetEvent) {
    Event *e = handle_get(ARG(c, 0), H_EVENT);
    if (e) event_set(e);
    ret_stdcall(c, e != NULL, 1);
}
__thread uint64_t host_wait_us, host_sleep_us, host_wait_calls;
API(WaitForSingleObject) {
    uint32_t h = ARG(c, 0), ms = ARG(c, 1), r = 0;
    Event *e = handle_get(h, H_EVENT);
    Thread *t = handle_get(h, H_THREAD);
    uint64_t t0 = platform_ticks_us();
    if (e) r = event_wait(e, ms);
    else if (t) {
        r = event_wait(&t->done, ms);
        if (!r) event_set(&t->done); /* a finished thread stays signaled */
    }
    uint64_t dur = platform_ticks_us() - t0;
    host_wait_us += dur;
    host_wait_calls++;
    if (c == game_cpu && vprof_active()) { /* long steps: what ran between two waits */
        static uint64_t last_end, window_at;
        static unsigned dumped;
        char draws[320];
        render_draw_stats(draws, sizeof draws, 1); /* drawing done in this step, then reset */
        if (t0 >= window_at) { /* one ordinary step every 10 s, for comparison */
            window_at = t0 + 10000000; dumped = 0;
            trace("# step (reference): %llu us of work, drew %s",
                  (unsigned long long)(last_end ? t0 - last_end : 0), draws);
        }
        if (last_end && t0 - last_end > 20000 && dumped < 25) {
            dumped++;
            vprof_window(last_end, t0, t0 - last_end);
            trace("#   that step drew %s", draws);
        }
        /* after the trace writes: their SD card time is the profiler's, not the game's
           (v19 charged ~12 ms of it to the next step, which chained long steps) */
        last_end = platform_ticks_us();
    }
    if (c == game_cpu && vprof_active()) { /* the game thread's waits, by kind */
        static struct { uint32_t h, ms, r; uint64_t n, sum, max; } w[8];
        static uint64_t at;
        unsigned i = 0;
        while (i < 7 && w[i].n && !(w[i].h == h && w[i].ms == ms && w[i].r == r)) i++;
        w[i].h = h; w[i].ms = ms; w[i].r = r; w[i].n++; w[i].sum += dur;
        if (dur > w[i].max) w[i].max = dur;
        uint64_t now = t0 + dur;
        if (!at) at = now + 10000000;
        if (now >= at) {
            at = now + 10000000;
            for (unsigned k = 0; k < 8; k++)
                if (w[k].n)
                    trace("# game waits: handle %08x (%s) ms %d -> %s: %llu, %llu us avg, worst %llu us", w[k].h,
                          handle_get(w[k].h, H_EVENT) ? "event" : handle_get(w[k].h, H_THREAD) ? "thread" : "other",
                          (int)w[k].ms, w[k].r ? "timeout" : "signaled", (unsigned long long)w[k].n,
                          (unsigned long long)(w[k].sum / w[k].n), (unsigned long long)w[k].max);
            memset(w, 0, sizeof w);
        }
    }
    ret_stdcall(c, r, 2);
}
API(CreateMutexA) {
    trace("CreateMutexA(%s)", ARG(c, 2) ? STR(ARG(c, 2)) : "NULL");
    last_error = 0;
    ret_stdcall(c, handle_new(H_MUTEX, NULL, 0), 3);
}

/* -- threads ------------------------------------------------------------------------- */
#ifdef __vita__
/* The game raises its music streaming threads to TIME_CRITICAL (15) and drops the
   loaders to IDLE (-15). The Vita scheduler is strictly by priority, so ignoring that
   let the loading threads starve the music refill, and the looping stream buffer
   replayed stale chunks (robotic first music). Lower Vita numbers run first. */
static int host_file_exists(const char *name) {
    char path[1100];
    snprintf(path, sizeof path, "%s/%s", host_data_dir, name);
    FILE *f = fopen(path, "rb");
    if (f) fclose(f);
    return f != NULL;
}

static void apply_priority(Thread *t) {
    int win = t->priority, delta = win >= 15 ? -40 : win <= -15 ? 24 : -4 * win;
    int p = 160 + delta; /* 160: the user default (SCE_KERNEL_DEFAULT_PRIORITY_USER) */
    /* The frame clock (0x4192a0) is TIME_CRITICAL like the music threads, and at the same
       Vita priority a music decode kept it off the CPU: its 16/17 ms waits ended up to
       13 ms late (v15 trace), the game thread then waited 17-26 ms for a tick and steps
       were lost. It now runs above them (the audio output stays at 96). */
    if (t->start == 0x004192a0u && !host_file_exists("oldclock.txt")) p = 100;
    p = p < 64 ? 64 : p > 191 ? 191 : p;
    /* 120 came back 0x80028021 (illegal priority) on hardware: the application's
       range is narrower than 64..191, so step towards the default until one is taken */
    int r;
    while ((r = sceKernelChangeThreadPriority(t->uid, p)) == (int)0x80028021 && p != 160)
        p += p < 160 ? 4 : -4;
    trace("# thread %u: Win32 priority %d -> Vita %d (%08x)", t->index, win, p, (unsigned)r);
}
#endif

static void *thread_main(void *arg) {
    Thread *t = arg;
    Cpu *c = &t->cpu;
#ifdef __vita__
    pthread_mutex_lock(&table_lock);
    t->uid = sceKernelGetThreadId();
    if (t->priority) apply_priority(t);
    pthread_mutex_unlock(&table_lock);
    /* The on-Vita profile (v9) showed the game thread (0x4083d0, logic + drawing) idle
       30-50 % of a fight in its frame wait, yet with 25-34 ms steps: it was being delayed,
       not overloaded. It gets user core 1 to itself; every other guest thread runs on
       cores 0 and 2. Measured in v10: no better, so it is now opt-in with cores.txt. */
    {
        static int off = -1;
        if (off < 0) {
            FILE *f = fopen("ux0:data/touhou123vita/cores.txt", "rb");
            off = f == NULL;
            if (f) fclose(f);
        }
        if (!off) {
            int game = t->start == 0x004083d0u;
            int mask = game ? 0x20000 : 0x10000 | 0x40000; /* SCE_KERNEL_CPU_MASK_USER_1 / _0|_2 */
            int r = sceKernelChangeThreadCpuAffinityMask(t->uid, mask);
            trace("# thread %u (start %08x): cores %s (%08x)", t->index, t->start, game ? "1" : "0+2", (unsigned)r);
        }
    }
#else
    profile_register_thread(0x1004 + 4 * t->index);
#endif
    memset(c, 0, sizeof *c);
    x87_reset(c);
    x87_set_cw(c, 0x027F);
    c->fs_base = t->tib;
    vprof_register(c, t->start);
    wake_tag = t->start;
    if (t->start == 0x004083d0u) { game_cpu = c; vprof_set_game(c); }
    uint32_t stack = THREAD_STACK_BASE + t->index * THREAD_STACK_SIZE;
    c->esp.d = stack + THREAD_STACK_SIZE - 16;
    jmp_buf trap;
    guest_fault_trap = &trap;
    if (setjmp(trap) == 0) {
        uint32_t param = t->param;
        t->exit_code = guest_invoke(c, t->start, 1, &param);
        trace("# thread %u (start %08x) returned %u", t->index, t->start, t->exit_code);
    } else {
        trace("# thread %u (start %08x): %s", t->index, t->start, guest_fault_text);
        t->exit_code = 0xFA17;
    }
    event_set(&t->done);
    pthread_mutex_lock(&table_lock);
    threads[t->index] = NULL; /* the slot (stack, TIB) can be reused */
    pthread_mutex_unlock(&table_lock);
    return NULL;
}

API(CreateThread) {
    uint32_t start = ARG(c, 2), param = ARG(c, 3), flags = ARG(c, 4);
    pthread_mutex_lock(&table_lock);
    unsigned index = 1;
    while (index < MAX_THREADS && threads[index]) index++;
    Thread *t = index < MAX_THREADS && !(flags & 4) ? calloc(1, sizeof *t) : NULL;
    if (t) threads[index] = t;
    pthread_mutex_unlock(&table_lock);
    if (index == MAX_THREADS || (flags & 4 /* CREATE_SUSPENDED */)) {
        trace("CreateThread(start=%08x, flags=%08x): not supported", start, flags);
        ret_stdcall(c, 0, 6);
        return;
    }
    event_init(&t->done, 1, 0);
    t->start = start;
    t->param = param;
    t->index = index;
    t->tib = THREAD_TIB_BASE + (index - 1) * 0x1000u;
    uint32_t stack = THREAD_STACK_BASE + index * THREAD_STACK_SIZE;
    guest_map(stack, THREAD_STACK_SIZE);
    guest_map(t->tib, 0x1000);
    memset(G(t->tib), 0, 0x1000);
    wr32(t->tib + 0x00, 0xFFFFFFFFu);
    wr32(t->tib + 0x04, stack + THREAD_STACK_SIZE);
    wr32(t->tib + 0x08, stack);
    wr32(t->tib + 0x18, t->tib);
    wr32(t->tib + 0x20, 0x1000);
    wr32(t->tib + 0x24, 0x1004 + 4 * index);
    wr32(t->tib + 0x2C, t->tib + 0xE10);
    wr32(t->tib + 0x30, GUEST_PEB);
    uint32_t h = handle_new(H_THREAD, t, 0);
    if (ARG(c, 5))
        wr32(ARG(c, 5), 0x1004 + 4 * index);
    pthread_attr_t attr;
    pthread_attr_init(&attr);
#ifdef __vita__
    /* host stack for nested guest calls; 2 MiB each left too little for the 11th thread
       after vitaGL took its pools (EAGAIN on hardware) */
    pthread_attr_setstacksize(&attr, 1u << 20);
#else
    pthread_attr_setstacksize(&attr, 8u << 20);
#endif
    /* nobody joins a guest thread (waits use t->done): a joinable one kept its 1 MiB
       stack after returning, and the loading threads of each fight used up the Vita's
       memory until CreateThread failed (black screen after a few fights) */
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
    int err = pthread_create(&t->host, &attr, thread_main, t);
    pthread_attr_destroy(&attr);
    if (err) {
        trace("CreateThread(start=%08x): pthread_create failed (%d)", start, err);
        pthread_mutex_lock(&table_lock);
        threads[index] = NULL;
        pthread_mutex_unlock(&table_lock);
        ret_stdcall(c, 0, 6);
        return;
    }
    trace("CreateThread(start=%08x, param=%08x) = %08x (guest thread %u)", start, param, h, index);
    ret_stdcall(c, h, 6);
}
API(GetExitCodeThread) {
    Thread *t = handle_get(ARG(c, 0), H_THREAD);
    uint32_t code = 259; /* STILL_ACTIVE */
    if (t && event_wait(&t->done, 0) == 0) { code = t->exit_code; event_set(&t->done); }
    wr32(ARG(c, 1), code);
    ret_stdcall(c, t != NULL, 2);
}
API(SetThreadPriority) {
    trace("SetThreadPriority(%08x, %d) from thread %08x", ARG(c, 0), (int32_t)ARG(c, 1), rd32(c->fs_base + 0x24));
#ifdef __vita__
    Thread *t = handle_get(ARG(c, 0), H_THREAD);
    if (t) {
        pthread_mutex_lock(&table_lock);
        t->priority = (int32_t)ARG(c, 1);
        if (t->uid) apply_priority(t);
        pthread_mutex_unlock(&table_lock);
    }
#endif
    ret_stdcall(c, 1, 2);
}
API(GetCurrentThreadId) { ret_stdcall(c, rd32(c->fs_base + 0x24), 0); }
API(Sleep) {
    uint64_t t0 = platform_ticks_us();
    platform_sleep_ms(ARG(c, 0));
    host_sleep_us += platform_ticks_us() - t0;
    ret_stdcall(c, 0, 1);
}

#define E(name) {#name, name}
const ApiEntry win32_threads[] = {
    E(InitializeCriticalSection), E(InitializeCriticalSectionAndSpinCount), E(DeleteCriticalSection),
    E(EnterCriticalSection), E(LeaveCriticalSection), E(TryEnterCriticalSection),
    E(CreateEventA), E(SetEvent), E(WaitForSingleObject), E(CreateMutexA),
    E(CreateThread), E(GetExitCodeThread), E(SetThreadPriority), E(GetCurrentThreadId), E(Sleep),
    {NULL, NULL},
};
