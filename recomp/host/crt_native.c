/* Native replacements for statically linked MSVC CRT routines. An intercept takes
 * priority over the lifted function at the same address. Only routines whose
 * contract is standard and verified are replaced here:
 *   0x820850, 0x8236b0  memcpy / memmove (cdecl dst, src, n -> dst). The lifted
 *                       versions dispatch through tables the discovery could not
 *                       bound (docs/F1_COVERAGE.md); memmove is a valid memcpy. */
#include "win32.h"

#include <string.h>

static void crt_memmove(Cpu *c) {
    uint32_t dst = ARG(c, 0), src = ARG(c, 1), n = ARG(c, 2);
    if (n)
        memmove(G(dst), G(src), n);
    ret_cdecl(c, dst);
}

void crt_native_init(void) {
    guest_intercept(0x00820850u, crt_memmove);
    guest_intercept(0x008236b0u, crt_memmove);
}
