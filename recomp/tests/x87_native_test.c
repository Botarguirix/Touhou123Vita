/* Compares the runtime's explicit-state x87 model with the host's real x87 FPU.
 *
 * For every control word in {PC 24, 53, 64} x {RC nearest, down, up, zero} it runs
 * the same operation natively (inline asm, x86 hosts only) and through the runtime
 * (the code path generated code uses), and requires bit-identical results:
 *   fld m64; f{add,sub,subr,mul,div,divr} m64     (D8/DC memory forms)
 *   chained a op b op c                          (PC rounding of intermediates)
 *   fsqrt, frndint
 *   fstp m32 / fstp m64 / fistp m32               (store-time rounding)
 *   fprem1                                        (IEEE remainder, complete case)
 * Operands are float-representable for PC=24 (where double rounding through 53 bits
 * is proven innocuous) and kept inside the float/double exponent range, because the
 * runtime does not model the extended exponent of x87 registers.
 *
 * usage: x87_native_test [cases]   prints a summary; exit status 1 on any mismatch.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "guest.h"

#if !(defined(__x86_64__) || defined(__i386__))
int main(void) { puts("x87_native_test: not an x86 host, skipped"); return 0; }
#else

enum { OPS = 6 };
static const char *op_names[OPS] = {"add", "sub", "subr", "mul", "div", "divr"};
static const int op_codes[OPS] = {X87_ADD, X87_SUB, X87_SUBR, X87_MUL, X87_DIV, X87_DIVR};

static uint64_t rng = 0x9E3779B97F4A7C15ull;
static uint64_t next(void) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return rng;
}

/* Random finite double with a moderate exponent; float-exact when `as_float`. */
static double random_operand(int as_float) {
    double m = (double)(next() >> 11) / 9007199254740992.0 + 0.5;
    int e = (int)(next() % 61) - 30;
    double v = ldexp(m, e) * ((next() & 1) ? -1 : 1);
    if ((next() & 15) == 0)
        v = (double)(int32_t)(next() % 2001) - 1000; /* small integers, exact ties */
    if ((next() & 15) == 1)
        v = ldexp(1.0, e) + ldexp(1.0, e - 24) * (double)(next() % 3); /* near float ties */
    return as_float ? (double)(float)v : v;
}

/* -- native ------------------------------------------------------------------------- */
static long double native_binop(uint16_t cw, int op, double a, double b) {
    long double r;
    uint16_t saved;
    __asm__ volatile("fnstcw %0" : "=m"(saved));
    __asm__ volatile("fldcw %0" ::"m"(cw));
    switch (op) {
    case 0: __asm__ volatile("fldl %1\n\tfaddl %2\n\tfstpt %0" : "=m"(r) : "m"(a), "m"(b)); break;
    case 1: __asm__ volatile("fldl %1\n\tfsubl %2\n\tfstpt %0" : "=m"(r) : "m"(a), "m"(b)); break;
    case 2: __asm__ volatile("fldl %1\n\tfsubrl %2\n\tfstpt %0" : "=m"(r) : "m"(a), "m"(b)); break;
    case 3: __asm__ volatile("fldl %1\n\tfmull %2\n\tfstpt %0" : "=m"(r) : "m"(a), "m"(b)); break;
    case 4: __asm__ volatile("fldl %1\n\tfdivl %2\n\tfstpt %0" : "=m"(r) : "m"(a), "m"(b)); break;
    default: __asm__ volatile("fldl %1\n\tfdivrl %2\n\tfstpt %0" : "=m"(r) : "m"(a), "m"(b)); break;
    }
    __asm__ volatile("fldcw %0" ::"m"(saved));
    return r;
}

static long double native_chain(uint16_t cw, double a, double b, double c) {
    long double r;
    uint16_t saved;
    __asm__ volatile("fnstcw %0" : "=m"(saved));
    __asm__ volatile("fldcw %0" ::"m"(cw));
    __asm__ volatile("fldl %1\n\tfmull %2\n\tfaddl %3\n\tfdivl %2\n\tfstpt %0"
                     : "=m"(r) : "m"(a), "m"(b), "m"(c));
    __asm__ volatile("fldcw %0" ::"m"(saved));
    return r;
}

static long double native_unary(uint16_t cw, int which, double a) {
    long double r;
    uint16_t saved;
    __asm__ volatile("fnstcw %0" : "=m"(saved));
    __asm__ volatile("fldcw %0" ::"m"(cw));
    if (which == 0)
        __asm__ volatile("fldl %1\n\tfsqrt\n\tfstpt %0" : "=m"(r) : "m"(a));
    else
        __asm__ volatile("fldl %1\n\tfrndint\n\tfstpt %0" : "=m"(r) : "m"(a));
    __asm__ volatile("fldcw %0" ::"m"(saved));
    return r;
}

static Cpu cpu_with(uint16_t cw);

/* fprem1 (IEEE remainder of st0 by st1); the stack is left empty. */
static long double native_fprem1(double a, double b) {
    long double r;
    __asm__ volatile("fldl %2\n\tfldl %1\n\tfprem1\n\tfstpt %0\n\tfstp %%st(0)"
                     : "=m"(r) : "m"(a), "m"(b));
    return r;
}

static long double runtime_fprem1(double a, double b) {
    Cpu c = cpu_with(0x037F);
    x87_push(&c, b);
    x87_push(&c, a);
    x87_binary_special(&c, 6);
    return x87_st(&c, 0);
}

static void native_stores(uint16_t cw, long double v, float *f, double *d, int32_t *i) {
    uint16_t saved;
    __asm__ volatile("fnstcw %0" : "=m"(saved));
    __asm__ volatile("fldcw %0" ::"m"(cw));
    __asm__ volatile("fldt %3\n\tfsts %0\n\tfstl %1\n\tfistpl %2"
                     : "=m"(*f), "=m"(*d), "=m"(*i) : "m"(v));
    __asm__ volatile("fldcw %0" ::"m"(saved));
}

/* -- runtime ------------------------------------------------------------------------ */
enum { SCRATCH = 0x10000 };

static Cpu cpu_with(uint16_t cw) {
    Cpu c = {0};
    x87_reset(&c);
    x87_set_cw(&c, cw);
    return c;
}

static long double runtime_binop(uint16_t cw, int op, double a, double b) {
    Cpu c = cpu_with(cw);
    wr64(SCRATCH, 0); memcpy(G(SCRATCH), &a, 8); memcpy(G(SCRATCH + 8), &b, 8);
    x87_fld_m64(&c, SCRATCH);
    x87_arith(&c, op_codes[op], 0, x87_m64(SCRATCH + 8), 0);
    return x87_st(&c, 0);
}

static long double runtime_chain(uint16_t cw, double a, double b, double cc) {
    Cpu c = cpu_with(cw);
    memcpy(G(SCRATCH), &a, 8); memcpy(G(SCRATCH + 8), &b, 8); memcpy(G(SCRATCH + 16), &cc, 8);
    x87_fld_m64(&c, SCRATCH);
    x87_arith(&c, X87_MUL, 0, x87_m64(SCRATCH + 8), 0);
    x87_arith(&c, X87_ADD, 0, x87_m64(SCRATCH + 16), 0);
    x87_arith(&c, X87_DIV, 0, x87_m64(SCRATCH + 8), 0);
    return x87_st(&c, 0);
}

static long double runtime_unary(uint16_t cw, int which, double a) {
    Cpu c = cpu_with(cw);
    memcpy(G(SCRATCH), &a, 8);
    x87_fld_m64(&c, SCRATCH);
    x87_unary(&c, which == 0 ? 2 : 3);
    return x87_st(&c, 0);
}

static void runtime_stores(uint16_t cw, long double v, float *f, double *d, int32_t *i) {
    Cpu c = cpu_with(cw);
    x87_push(&c, v);
    x87_fst_m32(&c, SCRATCH, 0);
    x87_fst_m64(&c, SCRATCH + 8, 0);
    x87_fist(&c, SCRATCH + 16, 4, 1, 0);
    memcpy(f, G(SCRATCH), 4); memcpy(d, G(SCRATCH + 8), 8); memcpy(i, G(SCRATCH + 16), 4);
}

static int same(long double a, long double b) {
    if (isnan(a) || isnan(b))
        return isnan(a) && isnan(b);
    return memcmp(&a, &b, 10) == 0 || (a == 0 && b == 0 && signbit(a) == signbit(b));
}

static int mismatches, reported;
static unsigned pc_sensitive, rc_sensitive;
static void report(const char *what, uint16_t cw, double a, double b, long double n, long double r) {
    mismatches++;
    if (reported++ < 12)
        printf("MISMATCH %s cw=%04x a=%.17g b=%.17g native=%.21Lg runtime=%.21Lg\n", what, cw, a, b, n, r);
}

int main(int argc, char **argv) {
    unsigned cases = argc > 1 ? (unsigned)atoi(argv[1]) : 20000;
    if (guest_mem_init() || guest_map(SCRATCH, 4096)) {
        puts("cannot map guest memory");
        return 2;
    }
    /* The runtime's PC=64 path computes with long double on this host. */
    uint16_t host_cw = 0x037F;
    __asm__ volatile("fldcw %0" ::"m"(host_cw));
    const uint16_t pcs[3] = {0x0000, 0x0200, 0x0300};
    unsigned checks = 0;
    for (unsigned p = 0; p < 3; p++) {
        for (unsigned rc = 0; rc < 4; rc++) {
            uint16_t cw = (uint16_t)(0x007F | pcs[p] | rc << 10);
            int float_inputs = p == 0;
            for (unsigned k = 0; k < cases; k++) {
                double a = random_operand(float_inputs), b = random_operand(float_inputs);
                double c = random_operand(float_inputs);
                for (int op = 0; op < OPS; op++) {
                    long double n = native_binop(cw, op, a, b), r = runtime_binop(cw, op, a, b);
                    checks++;
                    if (!same(n, r)) report(op_names[op], cw, a, b, n, r);
                    /* Sensitivity: the data must expose PC and RC, or a runtime that
                       ignored the control word would pass too. */
                    if (p != 2 && !same(n, native_binop((uint16_t)(cw | 0x0300), op, a, b)))
                        pc_sensitive++;
                    if (rc && !same(n, native_binop((uint16_t)(cw & ~0x0C00), op, a, b)))
                        rc_sensitive++;
                }
                if (p != 0) { /* chained intermediates are not float-exact under PC=24 */
                    long double n = native_chain(cw, a, b, c), r = runtime_chain(cw, a, b, c);
                    checks++;
                    if (!same(n, r)) report("chain", cw, a, b, n, r);
                }
                double s = fabs(a);
                long double n = native_unary(cw, 0, s), r = runtime_unary(cw, 0, s);
                checks++;
                if (!same(n, r)) report("fsqrt", cw, s, 0, n, r);
                double half = (double)(int32_t)(next() % 20001 - 10000) / 2 + (k & 1 ? 0.25 : 0);
                n = native_unary(cw, 1, half); r = runtime_unary(cw, 1, half);
                checks++;
                if (!same(n, r)) report("frndint", cw, half, 0, n, r);
                long double v = native_binop(0x037F, 3, a, b) / 3; /* 64-bit value to store */
                if (fabsl(v) < 2e9L && fabsl(v) > 1e-30L) {
                    float nf, rf; double nd, rd; int32_t ni, ri;
                    native_stores(cw, v, &nf, &nd, &ni);
                    runtime_stores(cw, v, &rf, &rd, &ri);
                    checks += 3;
                    if (memcmp(&nf, &rf, 4)) report("fst m32", cw, (double)v, 0, nf, rf);
                    if (memcmp(&nd, &rd, 8)) report("fst m64", cw, (double)v, 0, nd, rd);
                    if (ni != ri) report("fistp m32", cw, (double)v, 0, ni, ri);
                }
            }
        }
    }
    /* fprem1 with exponent differences small enough for a complete remainder. */
    for (unsigned k = 0; k < cases; k++) {
        double a = random_operand(0), b = random_operand(0);
        if (b == 0 || fabs(log2(fabs(a / b))) > 60)
            continue;
        long double n = native_fprem1(a, b), r = runtime_fprem1(a, b);
        checks++;
        if (!same(n, r)) report("fprem1", 0x037F, a, b, n, r);
    }
    printf("x87 native comparison: %u checks, %d mismatches; "
           "control-word sensitivity: PC %u, RC %u\n", checks, mismatches, pc_sensitive, rc_sensitive);
    if (!pc_sensitive || !rc_sensitive) {
        puts("test data does not exercise precision/rounding control");
        return 1;
    }
    return mismatches ? 1 : 0;
}
#endif
