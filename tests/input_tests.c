#include <stdio.h>
#include <string.h>
#include "t123/input.h"

#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "line %d: %s\n", __LINE__, #condition); return 1; \
} } while (0)

static void set_tail(T123InputHistory *history, const uint16_t *samples,
                     unsigned count) {
    t123_input_history_reset(history, 0);
    unsigned first = T123_INPUT_HISTORY_CAPACITY - count;
    for (unsigned i = 0; i < count; ++i)
        history->samples[first + i] = samples[i];
}

int main(void) {
    T123InputHistory h;
    static const uint16_t n_r_n_r[] = {0, 0x02, 0, 0x02};
    static const uint16_t n_l_n_l[] = {0, 0x01, 0, 0x01};
    static const uint16_t down_down[] = {0x80, 0x80};
    static const uint16_t n_zero_nine[] = {0, 0x08, 0x06};
    static const uint16_t two_n_two_a[] = {0x08, 0, 0x08, 0x10};

    set_tail(&h, n_r_n_r, 4);
    CHECK(t123_input_match(&h, "NRNR", 15, 1) == 1);
    CHECK(t123_input_match(&h, "NRNR", 3, 1) == 0);
    set_tail(&h, n_l_n_l, 4);
    CHECK(t123_input_match(&h, "NLNL", 15, -1) == 1);
    set_tail(&h, down_down, 2);
    CHECK(t123_input_match(&h, "DD", 15, 1) == 1);
    set_tail(&h, n_zero_nine, 3);
    CHECK(t123_input_match(&h, "N09", 20, 1) == 1);
    CHECK(t123_input_match(&h, "N09", 20, -1) == 0);
    set_tail(&h, two_n_two_a, 4);
    CHECK(t123_input_match(&h, "2N2A", 15, 1) == 1);

    for (unsigned button = 0; button < 4; ++button) {
        uint16_t sample = (uint16_t)(0x10u << button);
        set_tail(&h, &sample, 1);
        CHECK(t123_input_match(&h, "X", 15, 1) == button + 1);
    }
    {
        static const uint16_t altered[] = {0, 0x02, 0, 0x01};
        set_tail(&h, altered, 4);
        CHECK(t123_input_match(&h, "NRNR", 15, 1) == 0);
    }

    t123_input_history_reset(&h, 0);
    for (unsigned i = 0; i < 100; ++i)
        t123_input_history_push(&h, (uint16_t)i);
    CHECK(h.count == 90);
    CHECK(t123_input_history_get(&h, 0) == 10);
    CHECK(t123_input_history_get(&h, 89) == 99);
    puts("input matcher contracts: passed");
    return 0;
}
