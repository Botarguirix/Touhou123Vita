/* Host-implemented COM objects visible to the recompiled game (F2.2).
 *
 * A guest object is { +0 vtable, +4 reference count, +8 host index }. Its vtable holds
 * one fake address per method, in the order of the public headers
 * (com_vtables.h); calls dispatch to the C function bound to that method name, or
 * stop the program naming the missing method. */
#ifndef T123_COM_H
#define T123_COM_H

#include "com_vtables.h"
#include "win32.h"

typedef struct ComClass {
    const char *name;
    const ComMethod *methods;
    unsigned count;
    GuestFn impl[128];
    unsigned long long calls[128], us[128]; /* per method, for the trace summary */
    uint32_t vtable; /* guest address, created on first use */
    unsigned id;
} ComClass;

#define COM_CLASS(iface) {#iface, iface##_methods, iface##_count, {0}, {0}, {0}, 0, 0}

void com_bind(ComClass *cls, const char *method, GuestFn fn);
void com_bind_ok(ComClass *cls, const char *method); /* returns S_OK, pops its arguments */
uint32_t com_new(ComClass *cls, uint32_t host_index, uint32_t extra_bytes);
static inline uint32_t com_index(uint32_t object) { return rd32(object + 8); }

enum { S_OK = 0, E_FAIL = 0x80004005u, E_NOINTERFACE = 0x80004002u };

#endif
