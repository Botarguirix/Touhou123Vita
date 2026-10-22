/* PC host for the recompiled th123.exe (F2): loads the user's executable, fills its
 * IAT with host implementations, builds the thread environment and runs the CRT
 * entry point. Every Win32 call is written to host-trace.log; the run stops at the
 * first unimplemented import or guest_fault and reports how far it got.
 *
 * usage: th123_host <th123.exe> [data directory]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "win32.h"

#ifdef _WIN32
#include <windows.h>

/* A host access violation inside the guest window is a guest memory fault: report
   the guest address and the last guest functions entered, then stop. */
static LONG WINAPI guest_access_violation(EXCEPTION_POINTERS *info) {
    if (info->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION)
        return EXCEPTION_CONTINUE_SEARCH;
    uintptr_t host = (uintptr_t)info->ExceptionRecord->ExceptionInformation[1];
    int write = (int)info->ExceptionRecord->ExceptionInformation[0];
    if (host < (uintptr_t)guest_base || host >= (uintptr_t)guest_base + ((uintptr_t)1 << 32))
        return EXCEPTION_CONTINUE_SEARCH;
    uint32_t guest = (uint32_t)(host - (uintptr_t)guest_base);
    fprintf(stderr, "guest memory fault: %s of unmapped guest address %08x\n", write ? "write" : "read", guest);
    trace("# guest memory fault: %s %08x; last guest functions entered (oldest first):",
          write ? "write" : "read", guest);
    for (unsigned k = 0; k < 64; k++) {
        uint32_t f = guest_trace_ring[(guest_trace_pos + k) & 63];
        if (f)
            trace("#   %08x", f);
    }
    trace_summary();
    fflush(NULL);
    ExitProcess(0xFA17);
}
#endif

extern const GuestEntry t123_lifted[];
extern const unsigned t123_lifted_count;

static jmp_buf finished;
static uint32_t exit_code;
static const char *exit_reason = "returned";

_Noreturn void host_exit(Cpu *c, uint32_t code, const char *why) {
    (void)c;
    exit_code = code;
    exit_reason = why;
    trace("# exit: %s (code %08x)", why, code);
    longjmp(finished, 1);
}

static void setup_thread_environment(Cpu *c) {
    guest_map(GUEST_STACK_BASE, GUEST_STACK_SIZE);
    guest_map(GUEST_TIB, 0x2000); /* TIB + PEB */
    memset(G(GUEST_TIB), 0, 0x2000);
    wr32(GUEST_TIB + 0x00, 0xFFFFFFFFu);                         /* SEH chain end */
    wr32(GUEST_TIB + 0x04, GUEST_STACK_BASE + GUEST_STACK_SIZE); /* stack base */
    wr32(GUEST_TIB + 0x08, GUEST_STACK_BASE);                    /* stack limit */
    wr32(GUEST_TIB + 0x18, GUEST_TIB);                           /* self */
    wr32(GUEST_TIB + 0x20, 0x1000);                              /* process id */
    wr32(GUEST_TIB + 0x24, 0x1004);                              /* thread id */
    wr32(GUEST_TIB + 0x2C, GUEST_TIB + 0xE10);                   /* TLS array */
    wr32(GUEST_TIB + 0x30, GUEST_PEB);
    wr32(GUEST_PEB + 0x08, guest_image_base);                    /* ImageBaseAddress */
    memset(c, 0, sizeof *c);
    x87_reset(c);
    x87_set_cw(c, 0x027F); /* the MSVC process default: PC=53, round to nearest */
    c->fs_base = GUEST_TIB;
    c->esp.d = GUEST_STACK_BASE + GUEST_STACK_SIZE - 16;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s th123.exe [data directory]\n", argv[0]);
        return 2;
    }
    if (argc > 2)
        snprintf(host_data_dir, sizeof host_data_dir, "%s", argv[2]);
    if (guest_mem_init() || guest_load_pe(argv[1])) {
        fprintf(stderr, "cannot load %s\n", argv[1]);
        return 2;
    }
    guest_register(t123_lifted, t123_lifted_count);
    imports_init();
#ifdef _WIN32
    AddVectoredExceptionHandler(1, guest_access_violation);
#endif

    static Cpu cpu;
    setup_thread_environment(&cpu);
    uint32_t pe = guest_image_base + rd32(guest_image_base + 0x3C);
    uint32_t entry = guest_image_base + rd32(pe + 40);
    trace("# entry %08x, data directory %s", entry, host_data_dir);

    jmp_buf fault;
    guest_fault_trap = &fault;
    if (setjmp(finished) == 0) {
        if (setjmp(fault) == 0) {
            push32(&cpu, GUEST_RETURN_SENTINEL);
            guest_call(&cpu, entry);
            exit_code = cpu.eax.d;
        } else {
            exit_reason = "guest_fault (see stderr)";
            exit_code = 0xFA17;
        }
    }
    trace_summary();
    printf("th123 host: %s, exit code %08x, %llu Win32 calls (trace: host-trace.log)\n",
           exit_reason, exit_code, import_calls);
    return exit_code == 0 ? 0 : 1;
}
