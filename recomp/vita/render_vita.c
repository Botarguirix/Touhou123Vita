/* Vita placeholder for render.h until the vitaGL backend (H3): the D3D9 layer runs
 * and counts frames, nothing is drawn. Render state is kept so GetRenderState works. */
#include "../host/render.h"
#include "../host/win32.h"

static uint32_t states[256];

int render_init(uint32_t width, uint32_t height) { (void)width; (void)height; return 0; }
void render_clear(uint32_t flags, uint32_t color, float z, uint32_t stencil) {
    (void)flags; (void)color; (void)z; (void)stencil;
}
void render_state(uint32_t state, uint32_t value) { if (state < 256) states[state] = value; }
uint32_t render_get_state(uint32_t state) { return state < 256 ? states[state] : 0; }
void render_texture(uint32_t stage, RenderTexture *t) { (void)stage; (void)t; }
void render_texture_free(RenderTexture *t) { (void)t; }
void render_stage_state(uint32_t stage, uint32_t type, uint32_t value) { (void)stage; (void)type; (void)value; }
void render_sampler_state(uint32_t sampler, uint32_t type, uint32_t value) { (void)sampler; (void)type; (void)value; }
void render_fvf(uint32_t fvf) { (void)fvf; }
void render_draw_up(uint32_t type, uint32_t count, uint32_t data, uint32_t stride) {
    (void)type; (void)count; (void)data; (void)stride;
}
/* Without a GPU present the game would run its frames as fast as the CPU allows,
   while loading proceeds on its own clock; pace to 60 Hz like vsync on PC. */
void render_present(void) {
    static uint64_t next;
    uint64_t now = platform_ticks_us();
    if (!next || now > next + 100000u)
        next = now;
    next += 16667u;
    if (next > now)
        platform_sleep_ms((uint32_t)((next - now) / 1000u));
}
int render_pump_events(void) { return 0; }
int render_quit_requested(void) { return 0; }
int render_capture_bmp(const char *path) { (void)path; return -1; }
