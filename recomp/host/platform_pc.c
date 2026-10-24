/* PC platform hooks for the host (the Vita versions are in recomp/vita/). */
#include "win32.h"

#include <stdio.h>
#include <time.h>

void platform_log(const char *line) { (void)line; }

uint64_t platform_ticks_us(void) {
    struct timespec ts;
    timespec_get(&ts, TIME_UTC);
    return (uint64_t)ts.tv_sec * 1000000u + (uint64_t)ts.tv_nsec / 1000u;
}

void platform_finish(const char *summary) { printf("%s\n", summary); }

void platform_sleep_ms(uint32_t ms) {
    struct timespec ts = {ms / 1000, (long)(ms % 1000) * 1000000L};
    nanosleep(&ts, NULL);
}

void platform_memory_report(char *out, size_t size) { snprintf(out, size, "(no memory report on PC)"); }
