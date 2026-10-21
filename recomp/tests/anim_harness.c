/* Runs the lifted animation kernel (0x438c60 and the vtable methods it reaches)
 * on the inputs of tools/x86_animation_oracle.py and prints rows in the oracle's
 * CSV format, so the two outputs can be compared line by line.
 *
 * usage: anim_harness <th123.exe> <oracle.csv>
 */
#include <stdio.h>
#include <stdlib.h>

#include "guest.h"

extern const GuestEntry t123_lifted[];
extern const unsigned t123_lifted_count;

enum {
    OBJ = 0x1000000, SEQ = 0x1010000, FRAMES = 0x1020000, VT = 0x1030000,
    STACK = 0x2000000, STOP = 0x3000000,
    ADVANCE = 0x438c60, NEXT_POSE = 0x464b70, SET_POSE = 0x464b50, NEXT_SEQUENCE = 0x464bf0,
    GRAPHICS = 0x43a250,
};

static unsigned refresh_calls;

/* Same interception as the oracle: return before the render-info refresh. */
static void graphics_refresh(Cpu *c) {
    refresh_calls++;
    c->esp.d += 4;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s th123.exe oracle.csv\n", argv[0]);
        return 2;
    }
    if (guest_mem_init() || guest_load_pe(argv[1])) {
        fprintf(stderr, "cannot load %s\n", argv[1]);
        return 2;
    }
    const uint32_t regions[][2] = {{OBJ, 4096}, {SEQ, 4096}, {FRAMES, 4096}, {VT, 4096},
                                   {STACK, 65536}, {STOP, 4096}};
    for (unsigned i = 0; i < 6; i++)
        guest_map(regions[i][0], regions[i][1]);
    guest_register(t123_lifted, t123_lifted_count);
    guest_intercept(GRAPHICS, graphics_refresh);
    wr32(VT + 5 * 4, NEXT_SEQUENCE);
    wr32(VT + 7 * 4, SET_POSE);
    wr32(VT + 8 * 4, NEXT_POSE);

    FILE *in = fopen(argv[2], "r");
    if (!in) {
        fprintf(stderr, "cannot open %s\n", argv[2]);
        return 2;
    }
    unsigned n, a, b, loop, zero, pose, pf, dt;
    unsigned long cf;
    char rest[256];
    while (fscanf(in, "%u,%u,%u,%u,%u,%u,%u,%lu,%u,%255s", &n, &a, &b, &loop, &zero, &pose, &pf,
                  &cf, &dt, rest) == 10) {
        memset(G(OBJ), 0, 4096);
        memset(G(SEQ), 0, 4096);
        memset(G(FRAMES), 0, 4096);
        wr32(OBJ, VT);
        wr16(OBJ + 0x13e, 0);
        wr16(OBJ + 0x140, (uint16_t)pose);
        wr16(OBJ + 0x142, (uint16_t)pf);
        wr32(OBJ + 0x144, (uint32_t)cf);
        wr16(OBJ + 0x148, (uint16_t)n);
        wr16(OBJ + 0x14a, 0);
        wr16(OBJ + 0x14c, (uint16_t)dt);
        wr32(OBJ + 0x15c, SEQ);
        wr32(SEQ + 4, FRAMES);
        wr32(SEQ + 8, FRAMES + n * 0xa8);
        wr8(SEQ + 0x14, (uint8_t)loop);
        wr32(SEQ + 0x18, 0);
        wr32(SEQ + 0x1c, SEQ);
        wr16(FRAMES + 8, (uint16_t)a);
        wr16(FRAMES + 0xa8 + 8, (uint16_t)b);

        Cpu cpu = {0};
        x87_reset(&cpu);
        cpu.ecx.d = OBJ;
        cpu.esp.d = STACK + 65532;
        wr32(cpu.esp.d, STOP);
        guest_call(&cpu, ADVANCE);
        if (cpu.esp.d != STACK + 65536) {
            fprintf(stderr, "stack imbalance after case: esp=%08x\n", cpu.esp.d);
            return 1;
        }
        printf("%u,%u,%u,%u,%u,%u,%u,%lu,%u,%u,%u,%u,%u,%u,%u\n", n, a, b, loop, zero, pose, pf,
               cf, dt, cpu.eax.d & 255, rd16(OBJ + 0x13e), rd16(OBJ + 0x140), rd16(OBJ + 0x142),
               rd32(OBJ + 0x144), rd16(OBJ + 0x14c));
    }
    fclose(in);
    fprintf(stderr, "graphics refresh callbacks: %u\n", refresh_calls);
    return 0;
}
