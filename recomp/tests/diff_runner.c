/* Differential runner: executes lifted functions from explicit initial states and
 * writes the final state, for comparison with the original code run in Unicorn
 * (tests/test_recomp_x87_functions.py builds the cases and the reference).
 *
 * usage: diff_runner <th123.exe> <cases.bin> <results.bin>
 *
 * Case (little endian):  u32 entry, u32 regs[8] (eax ecx edx ebx esp ebp esi edi;
 *                         esp is ignored), u16 fpu_cw, u8 data[DATA_SIZE],
 *                         u8 args[ARGS_SIZE], f64 st_in (pushed on the x87 stack)
 * Result:                 u8 status (0 returned, 1 guest_fault), u32 regs[8],
 *                         u16 fpu_sw (with TOP), u8 depth, u8 st0[10], u8 data[DATA_SIZE]
 * The image is restored before every case, as the Unicorn reference does.
 */
#include <stdio.h>
#include <stdlib.h>

#include "guest.h"

extern const GuestEntry t123_lifted[];
extern const unsigned t123_lifted_count;

enum { DATA = 0x1000000, DATA_SIZE = 1024, ARGS_SIZE = 64, STACK = 0x2000000, STACK_SIZE = 0x10000,
       STOP = 0x3000000 };

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s th123.exe cases.bin results.bin\n", argv[0]);
        return 2;
    }
    if (guest_mem_init() || guest_load_pe(argv[1]) || guest_map(DATA, 0x1000) ||
        guest_map(STACK, STACK_SIZE)) {
        fprintf(stderr, "cannot prepare guest memory\n");
        return 2;
    }
    guest_register(t123_lifted, t123_lifted_count);
    /* Globals written by one case must not leak into the next: restore the image. */
    uint8_t *image = malloc(guest_image_size);
    memcpy(image, G(guest_image_base), guest_image_size);
    FILE *in = fopen(argv[2], "rb"), *out = fopen(argv[3], "wb");
    if (!in || !out)
        return 2;
    uint32_t entry, regs[8];
    uint16_t cw;
    uint8_t data[DATA_SIZE], args[ARGS_SIZE];
    double st_in;
    while (fread(&entry, 4, 1, in) == 1 && fread(regs, 4, 8, in) == 8 && fread(&cw, 2, 1, in) == 1 &&
           fread(data, 1, DATA_SIZE, in) == DATA_SIZE && fread(args, 1, ARGS_SIZE, in) == ARGS_SIZE &&
           fread(&st_in, 8, 1, in) == 1) {
        static Cpu c;
        memcpy(G(guest_image_base), image, guest_image_size);
        memset(&c, 0, sizeof c);
        x87_reset(&c);
        x87_set_cw(&c, cw);
        x87_push(&c, st_in);
        GuestReg *r[8] = {&c.eax, &c.ecx, &c.edx, &c.ebx, &c.esp, &c.ebp, &c.esi, &c.edi};
        for (int i = 0; i < 8; i++)
            r[i]->d = regs[i];
        memcpy(G(DATA), data, DATA_SIZE);
        c.esp.d = STACK + STACK_SIZE - ARGS_SIZE - 4;
        memcpy(G(c.esp.d + 4), args, ARGS_SIZE);
        wr32(c.esp.d, STOP);

        jmp_buf trap;
        uint8_t status = 0;
        guest_fault_trap = &trap;
        if (setjmp(trap) == 0)
            guest_call(&c, entry);
        else
            status = 1;
        guest_fault_trap = NULL;

        uint32_t final[8];
        for (int i = 0; i < 8; i++)
            final[i] = r[i]->d;
        /* Depth from TOP, as the reference computes it (cases start empty, TOP=0). */
        uint16_t sw = x87_get_sw(&c);
        uint8_t depth = (uint8_t)((8 - c.fpu.top) & 7);
        long double st0 = depth ? (long double)x87_st(&c, 0) : 0.0L;
        uint8_t st0_bytes[10];
        memcpy(st0_bytes, &st0, 10);
        fwrite(&status, 1, 1, out);
        fwrite(final, 4, 8, out);
        fwrite(&sw, 2, 1, out);
        fwrite(&depth, 1, 1, out);
        fwrite(st0_bytes, 1, 10, out);
        fwrite(G(DATA), 1, DATA_SIZE, out);
    }
    fclose(in);
    fclose(out);
    return 0;
}
