#include "com.h"

#include <stdio.h>
#include <string.h>

enum { COM_FAKE_BASE = 0x7E000000u, CLASS_SPAN = 0x1000u, METHOD_SPAN = 8u };

static ComClass *classes[64];
static unsigned class_count;

static void com_dispatch(Cpu *c) {
    uint32_t off = guest_current_target - COM_FAKE_BASE;
    ComClass *cls = classes[off / CLASS_SPAN];
    unsigned m = (off % CLASS_SPAN) / METHOD_SPAN;
    import_calls++;
    if (cls->impl[m]) {
        uint64_t t0 = platform_ticks_us();
        cls->impl[m](c);
        cls->calls[m]++;
        cls->us[m] += platform_ticks_us() - t0;
        return;
    }
    char why[160];
    snprintf(why, sizeof why, "COM method %s::%s is not implemented", cls->name, cls->methods[m].name);
    host_exit(c, 0xC0C0, why);
}

/* Generic implementations. */
static void addref(Cpu *c) {
    uint32_t o = ARG(c, 0), n = rd32(o + 4) + 1;
    wr32(o + 4, n);
    ret_stdcall(c, n, 1);
}
static void release(Cpu *c) {
    uint32_t o = ARG(c, 0), n = rd32(o + 4);
    if (n) wr32(o + 4, --n);
    ret_stdcall(c, n, 1); /* host state is kept: objects are few and long-lived */
}
static void return_ok(Cpu *c) {
    uint32_t off = guest_current_target - COM_FAKE_BASE;
    ComClass *cls = classes[off / CLASS_SPAN];
    ret_stdcall(c, S_OK, cls->methods[(off % CLASS_SPAN) / METHOD_SPAN].args);
}

static int method_index(ComClass *cls, const char *method) {
    for (unsigned i = 0; i < cls->count; i++)
        if (!strcmp(cls->methods[i].name, method))
            return (int)i;
    trace("# com_bind: %s has no method %s", cls->name, method);
    return -1;
}

void com_bind(ComClass *cls, const char *method, GuestFn fn) {
    int i = method_index(cls, method);
    if (i >= 0)
        cls->impl[i] = fn;
}

void com_bind_ok(ComClass *cls, const char *method) { com_bind(cls, method, return_ok); }

uint32_t com_new(ComClass *cls, uint32_t host_index, uint32_t extra_bytes) {
    if (!cls->vtable) {
        cls->id = class_count;
        classes[class_count++] = cls;
        if (!cls->impl[1]) cls->impl[1] = addref;
        if (!cls->impl[2]) cls->impl[2] = release;
        cls->vtable = heap_alloc(4 * cls->count, 1);
        for (unsigned i = 0; i < cls->count; i++) {
            uint32_t fake = COM_FAKE_BASE + cls->id * CLASS_SPAN + i * METHOD_SPAN;
            wr32(cls->vtable + 4 * i, fake);
            guest_intercept(fake, com_dispatch);
        }
    }
    uint32_t o = heap_alloc(12 + extra_bytes, 1);
    wr32(o, cls->vtable);
    wr32(o + 4, 1);
    wr32(o + 8, host_index);
    return o;
}

/* COM methods that took host time, for the trace summary (load-time profiling). */
void com_summary(void) {
    trace("# COM methods (calls, host time):");
    for (unsigned k = 0; k < class_count; k++)
        for (unsigned m = 0; m < classes[k]->count; m++)
            if (classes[k]->us[m] >= 1000)
                trace("#   %8llu %s::%s (%llu ms)", classes[k]->calls[m], classes[k]->name,
                      classes[k]->methods[m].name, classes[k]->us[m] / 1000);
}