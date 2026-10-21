#include "t123/core.h"
/* Diagnostic determinism contract only. No recovered game logic yet. */
void t123_init(T123State *s) { s->frame = 0; s->input = 0; s->digest = 2166136261u; }
void t123_step(T123State *s, uint32_t input) {
    s->input = input;
    s->digest = (s->digest ^ input) * 16777619u;
    s->digest = (s->digest ^ s->frame) * 16777619u;
    ++s->frame;
}
uint32_t t123_smoke_digest(void) {
    T123State s; t123_init(&s);
    for (uint32_t i = 0; i < T123_SMOKE_FRAMES; ++i) t123_step(&s, i % 7u);
    return s.digest;
}
