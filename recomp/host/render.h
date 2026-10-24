/* Rendering backend behind the D3D9 layer: fixed-function OpenGL (desktop GL on PC,
 * vitaGL's fixed-function emulation on the Vita for H3). */
#ifndef T123_RENDER_H
#define T123_RENDER_H

#include <stdint.h>

#define RENDER_MAX_TEXTURES 4096

typedef struct {
    uint32_t width, height, format, pitch;
    uint8_t *data;   /* level 0, host memory (keeps the guest heap for the game) */
    uint32_t pixels; /* guest staging copy while locked, else 0 */
    int dirty;
    unsigned gl;
    unsigned next_free; /* d3d9.c slot free list */
} RenderTexture;

int render_init(uint32_t width, uint32_t height);
void render_clear(uint32_t flags, uint32_t color, float z, uint32_t stencil);
void render_state(uint32_t state, uint32_t value);
uint32_t render_get_state(uint32_t state);
void render_texture(uint32_t stage, RenderTexture *t);
void render_texture_free(RenderTexture *t);
void render_stage_state(uint32_t stage, uint32_t type, uint32_t value);
void render_sampler_state(uint32_t sampler, uint32_t type, uint32_t value);
void render_fvf(uint32_t fvf);
void render_draw_up(uint32_t type, uint32_t count, uint32_t data, uint32_t stride);
void render_present(void);
int render_pump_events(void);  /* returns 1 when the user closed the window */
int render_quit_requested(void);
int render_capture_bmp(const char *path);

#endif
