#ifndef T123_CORE_H
#define T123_CORE_H
#include <stdint.h>
#define T123_NATIVE_WIDTH 640
#define T123_NATIVE_HEIGHT 480
#define T123_VITA_WIDTH 960
#define T123_VITA_HEIGHT 544
#define T123_SMOKE_FRAMES 120
typedef struct { uint32_t frame; uint32_t input; uint32_t digest; } T123State;
void t123_init(T123State *state);
void t123_step(T123State *state, uint32_t input);
uint32_t t123_smoke_digest(void);
#endif
