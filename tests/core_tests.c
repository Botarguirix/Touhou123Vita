#include <stdio.h>
#include "t123/core.h"
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "failed: %s\n", #x); return 1; } } while (0)
int main(void) {
    T123State a, b; t123_init(&a); t123_init(&b);
    CHECK(a.frame == 0 && a.input == 0);
    for (unsigned i=0;i<120;i++) { t123_step(&a,i%7); t123_step(&b,i%7); }
    CHECK(a.frame == 120 && a.digest == b.digest);
    CHECK(a.digest == t123_smoke_digest());
    t123_init(&b); for (unsigned i=0;i<120;i++) t123_step(&b,0);
    CHECK(a.digest != b.digest);
    return 0;
}
