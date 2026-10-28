/* Fixed-function OpenGL implementation of render.h, shared by both platforms:
 *   PC    SDL2 window + desktop GL (vsync);
 *   Vita  vitaGL (H3), whose fixed-function emulation compiles its shaders at run
 *         time with ur0:data/libshacccg.suprx. The 640x480 game fills the 960x544
 *         screen. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __vita__
#include <psp2/ctrl.h>
#include <psp2/display.h>
#include <pthread.h>
#include <vitaGL.h>
#else
#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
#endif

#include "input_map.h"
#include "render.h"
#include "win32.h"

static uint32_t screen_w, screen_h, fvf;
static uint32_t states[256];
static RenderTexture *bound;
static int quit, ready;
static int mag_linear, min_linear;

/* -- platform glue: context, presentation, input ------------------------------------ */
#ifdef __vita__
/* The 640x480 game is stretched to the whole 16:9 screen (the user's choice); set
   VIEW_W to 725 for centred 4:3 with black side bars. */
enum { VITA_W = 960, VITA_H = 544, VIEW_W = 960, VIEW_X = (VITA_W - VIEW_W) / 2 };
/* vitaGL has no per-thread context, but it is not thread-safe: the device is created
   on one guest thread and two others draw, so every call goes through one lock. */
static pthread_mutex_t gl_lock = PTHREAD_MUTEX_INITIALIZER;
static void gl_enter(void) { pthread_mutex_lock(&gl_lock); }
static void gl_leave(void) { pthread_mutex_unlock(&gl_lock); }
#define blend_equation glBlendEquation

static int platform_init(uint32_t width, uint32_t height) {
    /* Texture storage is reserved first, then vitaGL gets fixed pools: 8 MiB of the
       ~32 MiB user RAM left (the rest is for ~20 thread stacks and file buffers), 64 MiB
       of CDRAM (the rest grows the texture pool) and 16 MiB of physically contiguous memory. */
    texture_pool_reserve();
    char memory[160];
    platform_memory_report(memory, sizeof memory);
    trace("# before vitaGL: %s", memory);
    /* Explicit pool sizes (the threshold variant derives them from the remaining
       budget). The return value is not a success flag: vitaGL returns whether it had
       to lower the resolution, i.e. GL_FALSE after a normal start, so it is ignored. */
    vglInitWithCustomSizes(0, VITA_W, VITA_H, 8 << 20, 64 << 20, 16 << 20, 0, SCE_GXM_MULTISAMPLE_NONE);
    platform_memory_report(memory, sizeof memory);
    trace("# after vitaGL: %s", memory);
    platform_display_taken();
    sceCtrlSetSamplingMode(SCE_CTRL_MODE_DIGITAL);
    glClearColor(0, 0, 0, 1);
    glClear(GL_COLOR_BUFFER_BIT);
    glViewport(VIEW_X, 0, VIEW_W, VITA_H);
    /* vitaGL does not clip to the viewport: keep sprites that slide in from outside the
       640x480 screen off the side bars */
    glEnable(GL_SCISSOR_TEST);
    glScissor(VIEW_X, 0, VIEW_W, VITA_H);
    (void)width; (void)height;
    return 0;
}
static void platform_swap(void) { vglSwapBuffers(GL_FALSE); }
int render_pump_events(void) { return 0; }
void render_keyboard_state(uint8_t dik[256]) {
    SceCtrlData pad;
    memset(&pad, 0, sizeof pad);
    sceCtrlPeekBufferPositive(0, &pad, 1);
    /* every change goes to the trace: the idle game left the title on its own on the
       Vita but not on PC, so check what the pad reports */
    static uint32_t last = 0xFFFFFFFFu;
    if (pad.buttons != last) {
        trace("# vita buttons: %08x (frame %llu)", (unsigned)pad.buttons, d3d_frames);
        last = pad.buttons;
    }
    /* START + SELECT held for 2 s ends the run and writes the trace, capture and result */
    static uint64_t held_since;
    uint32_t combo = SCE_CTRL_START | SCE_CTRL_SELECT;
    if ((pad.buttons & combo) == combo) {
        uint64_t now = platform_ticks_us();
        if (!held_since) held_since = now;
        else if (now - held_since > 2000000u) host_exit(NULL, 0, "START+SELECT pressed");
    } else {
        held_since = 0;
    }
    dik_state_from_vita_buttons(pad.buttons, dik);
}
#else
static SDL_Window *window;
static SDL_GLContext context;
static void (APIENTRY *blend_equation)(GLenum);

/* Desktop GL contexts are per thread: every render call takes the context under a
   lock and releases it on the way out (wglMakeCurrent refuses a context current on
   another thread). */
static SDL_mutex *gl_lock;
static void *gl_holder; /* thread that has the context current, or NULL */
static _Thread_local char gl_me;

static void gl_enter(void) {
    SDL_LockMutex(gl_lock);
    if (gl_holder == &gl_me)
        return;
    if (SDL_GL_MakeCurrent(window, context) == 0)
        gl_holder = &gl_me;
    else
        trace("# GL context unavailable on host thread %lu: %s", SDL_ThreadID(), SDL_GetError());
}
static void gl_leave(void) {
    SDL_GL_MakeCurrent(window, NULL);
    gl_holder = NULL;
    SDL_UnlockMutex(gl_lock);
}

static int platform_init(uint32_t width, uint32_t height) {
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS)) {
        trace("# SDL_Init failed: %s", SDL_GetError());
        return -1;
    }
    SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    window = SDL_CreateWindow("Touhou 12.3 (recompiled)", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              (int)width, (int)height, SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN);
    if (!window || !(context = SDL_GL_CreateContext(window))) {
        trace("# window/GL context failed: %s", SDL_GetError());
        return -1;
    }
    SDL_GL_SetSwapInterval(1);
    blend_equation = (void (APIENTRY *)(GLenum))SDL_GL_GetProcAddress("glBlendEquation");
    gl_lock = SDL_CreateMutex();
    glViewport(0, 0, (GLsizei)width, (GLsizei)height);
    return 0;
}
static void platform_swap(void) { SDL_GL_SwapWindow(window); }

int render_pump_events(void) {
    SDL_Event e;
    while (SDL_PollEvent(&e))
        if (e.type == SDL_QUIT)
            quit = 1;
    return quit;
}

/* T123_PRESS="first-last:scancode[,...]" holds an SDL scancode down during those
   presented frames, so runs can be scripted without a person at the window. */
static void scripted_keys(uint8_t dik[256]) {
    const char *p = getenv("T123_PRESS");
    while (p && *p) {
        unsigned long long first, last;
        int sc, used = 0;
        if (sscanf(p, "%llu-%llu:%d%n", &first, &last, &sc, &used) != 3)
            return;
        if (d3d_frames >= first && d3d_frames <= last && dik_from_sdl_scancode(sc))
            dik[dik_from_sdl_scancode(sc)] = 0x80;
        p += used;
        if (*p == ',') p++;
    }
}

void render_keyboard_state(uint8_t dik[256]) {
    scripted_keys(dik);
    int count = 0;
    const Uint8 *keys = SDL_GetKeyboardState(&count);
    for (int sc = 0; sc < count; sc++)
        if (keys[sc]) {
            uint8_t code = dik_from_sdl_scancode(sc);
            if (code) dik[code] = 0x80;
        }
}
#endif

int render_quit_requested(void) { return quit; }

/* -- common ------------------------------------------------------------------------- */
int render_init(uint32_t width, uint32_t height) {
    if (ready)
        return 0;
    if (platform_init(width, height))
        return -1;
    screen_w = width;
    screen_h = height;
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrtho(0, width, height, 0, -1, 1);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glDisable(GL_CULL_FACE);
    glDisable(GL_LIGHTING);
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    trace("# renderer: %s / %s", (const char *)glGetString(GL_RENDERER), (const char *)glGetString(GL_VERSION));
#ifndef __vita__
    SDL_GL_MakeCurrent(window, NULL);
#endif
    ready = 1;
    return 0;
}

static void color4(uint32_t argb, float out[4]) {
    out[0] = ((argb >> 16) & 255) / 255.0f;
    out[1] = ((argb >> 8) & 255) / 255.0f;
    out[2] = (argb & 255) / 255.0f;
    out[3] = (argb >> 24) / 255.0f;
}

void render_clear(uint32_t flags, uint32_t color, float z, uint32_t stencil) {
    gl_enter();
    float c[4];
    color4(color, c);
    glClearColor(c[0], c[1], c[2], c[3]);
    glClearDepth(z);
    glClearStencil((GLint)stencil);
    GLbitfield mask = (flags & 1 ? GL_COLOR_BUFFER_BIT : 0) | (flags & 2 ? GL_DEPTH_BUFFER_BIT : 0) |
                      (flags & 4 ? GL_STENCIL_BUFFER_BIT : 0);
    glDepthMask(GL_TRUE);
    glClear(mask);
    glDepthMask(states[14] ? GL_TRUE : GL_FALSE);
    gl_leave();
}

static GLenum blend_factor(uint32_t b) {
    static const GLenum map[] = {GL_ONE, GL_ZERO, GL_ONE, GL_SRC_COLOR, GL_ONE_MINUS_SRC_COLOR, GL_SRC_ALPHA,
                                 GL_ONE_MINUS_SRC_ALPHA, GL_DST_ALPHA, GL_ONE_MINUS_DST_ALPHA, GL_DST_COLOR,
                                 GL_ONE_MINUS_DST_COLOR, GL_SRC_ALPHA_SATURATE};
    return b < sizeof map / sizeof *map ? map[b] : GL_ONE;
}

static GLenum compare(uint32_t f) { return f >= 1 && f <= 8 ? GL_NEVER + (f - 1) : GL_ALWAYS; }

static void apply_states(void) {
    if (states[27]) glEnable(GL_BLEND); else glDisable(GL_BLEND);
    glBlendFunc(blend_factor(states[19] ? states[19] : 2), blend_factor(states[20] ? states[20] : 1));
    if (blend_equation) {
        static const GLenum ops[] = {0x8006, 0x8006, 0x800A, 0x800B, 0x8007, 0x8008}; /* ADD SUB REVSUB MIN MAX */
        blend_equation(states[171] < 6 ? ops[states[171]] : 0x8006);
    }
    if (states[15]) glEnable(GL_ALPHA_TEST); else glDisable(GL_ALPHA_TEST);
    glAlphaFunc(compare(states[25] ? states[25] : 8), (states[24] & 255) / 255.0f);
    if (states[7]) glEnable(GL_DEPTH_TEST); else glDisable(GL_DEPTH_TEST);
    glDepthFunc(compare(states[23] ? states[23] : 4));
    glDepthMask(states[14] ? GL_TRUE : GL_FALSE);
}

void render_state(uint32_t state, uint32_t value) {
    if (state < 256)
        states[state] = value;
}
uint32_t render_get_state(uint32_t state) { return state < 256 ? states[state] : 0; }

void render_stage_state(uint32_t stage, uint32_t type, uint32_t value) { (void)stage; (void)type; (void)value; }

void render_sampler_state(uint32_t sampler, uint32_t type, uint32_t value) {
    if (sampler) return;
    if (type == 5) mag_linear = value == 2;
    if (type == 6) min_linear = value == 2;
}

void render_fvf(uint32_t value) { fvf = value; }

/* Uploaded textures stay on the GPU until the game releases them. In a fight on the
   Vita that filled vitaGL's memory (sprites vanished, then ~10 FPS), so the Vita keeps
   a budget and drops the textures drawn longest ago; a dropped texture is uploaded
   again from its stored copy the next time it is drawn. */
extern RenderTexture textures[RENDER_MAX_TEXTURES];
#ifdef __vita__
static uint64_t gpu_budget = 44u << 20; /* of vitaGL's 64 MiB of CDRAM */
#else
static uint64_t gpu_budget = UINT64_MAX; /* T123_GPU_BUDGET_MB to test the Vita's eviction */
#endif
static uint64_t gpu_bytes, gpu_evictions;

static void gpu_forget(RenderTexture *t) { /* under the GL lock */
    if (!t->gl) return;
    glDeleteTextures(1, &t->gl);
    t->gl = 0;
    gpu_bytes -= t->gpu_bytes;
    t->gpu_bytes = 0;
}

/* vitaGL frees a deleted texture only once the GPU is done with it, so its real free
   memory can be far below what the budget suggests: 5300 evictions in a long fight
   ended in a GPU crash on the Vita (52 MiB budget). Room is also made while vitaGL's
   own free memory is short. */
static int gpu_memory_short(uint64_t need) {
#ifdef __vita__
    size_t free_now = vglMemFree(VGL_MEM_VRAM) + vglMemFree(VGL_MEM_PHYCONT);
    return free_now < need + (8u << 20);
#else
    (void)need;
    return 0;
#endif
}

static void gpu_make_room(uint64_t need) {
#ifndef __vita__
    static int read_env;
    if (!read_env++ && getenv("T123_GPU_BUDGET_MB"))
        gpu_budget = strtoull(getenv("T123_GPU_BUDGET_MB"), NULL, 10) << 20;
#endif
    while (gpu_bytes + need > gpu_budget || (gpu_bytes && gpu_memory_short(need))) {
        RenderTexture *oldest = NULL;
        for (unsigned i = 1; i < RENDER_MAX_TEXTURES; i++) {
            RenderTexture *t = &textures[i];
            if (t->gl && t->used_frame < d3d_frames && (!oldest || t->used_frame < oldest->used_frame))
                oldest = t;
        }
        if (!oldest) return; /* everything was drawn this frame: go over budget */
        gpu_forget(oldest);
        if (++gpu_evictions % 100 == 1)
#ifdef __vita__
            trace("# GPU texture budget: %llu evictions so far, %llu KiB uploaded, vitaGL free %u KiB VRAM %u KiB phycont",
                  (unsigned long long)gpu_evictions, (unsigned long long)(gpu_bytes >> 10),
                  (unsigned)(vglMemFree(VGL_MEM_VRAM) >> 10), (unsigned)(vglMemFree(VGL_MEM_PHYCONT) >> 10));
#else
            trace("# GPU texture budget: %llu evictions so far, %llu KiB uploaded",
                  (unsigned long long)gpu_evictions, (unsigned long long)(gpu_bytes >> 10));
#endif
    }
}

/* D3D formats -> RGBA8, n rows. */
static void convert_rows(const RenderTexture *t, const uint8_t *src, uint8_t *rgba, uint32_t n) {
    for (uint32_t y = 0; y < n; y++) {
        for (uint32_t x = 0; x < t->width; x++) {
            uint8_t *o = rgba + ((size_t)y * t->width + x) * 4;
            const uint8_t *p = src + (size_t)y * t->pitch;
            uint32_t v;
            switch (t->format) {
            case 21: case 22:
                p += x * 4;
                o[0] = p[2]; o[1] = p[1]; o[2] = p[0]; o[3] = t->format == 22 ? 255 : p[3];
                break;
            case 26: /* A4R4G4B4 */
                v = p[x * 2] | p[x * 2 + 1] << 8;
                o[0] = ((v >> 8) & 15) * 17; o[1] = ((v >> 4) & 15) * 17; o[2] = (v & 15) * 17; o[3] = (v >> 12) * 17;
                break;
            case 25: case 24: /* A1R5G5B5, X1R5G5B5 */
                v = p[x * 2] | p[x * 2 + 1] << 8;
                o[0] = ((v >> 10) & 31) * 255 / 31; o[1] = ((v >> 5) & 31) * 255 / 31; o[2] = (v & 31) * 255 / 31;
                o[3] = t->format == 24 || (v >> 15) ? 255 : 0;
                break;
            case 23: /* R5G6B5 */
                v = p[x * 2] | p[x * 2 + 1] << 8;
                o[0] = ((v >> 11) & 31) * 255 / 31; o[1] = ((v >> 5) & 63) * 255 / 63; o[2] = (v & 31) * 255 / 31; o[3] = 255;
                break;
            case 28: /* A8 */
                o[0] = o[1] = o[2] = 0; o[3] = p[x];
                break;
            case 50: /* L8 */
                o[0] = o[1] = o[2] = p[x]; o[3] = 255;
                break;
            default:
                o[0] = 255; o[1] = 0; o[2] = 255; o[3] = 255; /* unknown format: magenta */
                break;
            }
        }
    }
}

/* Upload in bands: the texture is created empty and filled row band by row band from
   the stored pixels (inflated a band at a time on the Vita), so no buffer the size of
   the texture is needed. A whole-texture scratch buffer (4 MiB for 1024x1024) could
   not be found once memory was fragmented on the Vita, and the game then waited
   forever for that texture on its loading screen. */
enum { BAND_BYTES = 256 * 1024 };
static uint8_t band[BAND_BYTES], band_rgba[BAND_BYTES * 2];

/* Large textures (both sides >= 640: backgrounds and scenery, not the 512x512 and
   smaller sprite sheets) go to the GPU at half resolution on the Vita, a quarter of
   the memory; the texture coordinates are normalised, so the game does not notice.
   Each 2x2 block of BGRA pixels becomes its average. */
#ifdef __vita__
static int half_res_enabled = 1;
#else
static int half_res_enabled = -1; /* T123_HALF_RES=1 to see it on PC */
#endif
static int wants_half(const RenderTexture *t) {
    if (half_res_enabled < 0) half_res_enabled = getenv("T123_HALF_RES") != NULL;
    return half_res_enabled && t->format == 21 && t->pitch == t->width * 4 && t->width >= 640 && t->height >= 640;
}

static void upload_band_half(void *ctx, const uint8_t *rows, uint32_t y, uint32_t n) {
    RenderTexture *t = ctx;
    uint32_t w = t->width / 2, out_rows = (n + 1) / 2;
    for (uint32_t r = 0; r < out_rows; r++) {
        const uint8_t *a = rows + (size_t)(2 * r) * t->pitch;
        const uint8_t *b = 2 * r + 1 < n ? a + t->pitch : a; /* odd last row: reuse it */
        uint8_t *o = band_rgba + (size_t)r * w * 4;
        for (uint32_t x = 0; x < w; x++, a += 8, b += 8, o += 4)
            for (unsigned k = 0; k < 4; k++)
                o[k] = (uint8_t)((a[k] + a[k + 4] + b[k] + b[k + 4] + 2) >> 2);
    }
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, (GLint)(y / 2), (GLsizei)w, (GLsizei)out_rows, GL_BGRA, GL_UNSIGNED_BYTE, band_rgba);
}

static void upload_band(void *ctx, const uint8_t *rows, uint32_t y, uint32_t n) {
    RenderTexture *t = ctx;
    if (t->format == 21 && t->pitch == t->width * 4) { /* A8R8G8B8 is BGRA in memory: as is */
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, (GLint)y, (GLsizei)t->width, (GLsizei)n, GL_BGRA, GL_UNSIGNED_BYTE, rows);
    } else {
        convert_rows(t, rows, band_rgba, n);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, (GLint)y, (GLsizei)t->width, (GLsizei)n, GL_RGBA, GL_UNSIGNED_BYTE, band_rgba);
    }
}

static void upload(RenderTexture *t) {
    int half = wants_half(t);
    uint32_t gw = half ? t->width / 2 : t->width, gh = half ? (t->height + 1) / 2 : t->height;
    size_t out_bytes = (size_t)gw * gh * 4;
    if (t->pitch > BAND_BYTES || (size_t)t->width * 4 > sizeof band_rgba) {
        trace("# texture upload %ux%u: rows wider than the upload band", t->width, t->height);
        return;
    }
    gpu_forget(t);
    gpu_make_room(out_bytes);
    glGenTextures(1, &t->gl);
    glBindTexture(GL_TEXTURE_2D, t->gl);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, (GLsizei)gw, (GLsizei)gh, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
    /* band rows: bounded by both buffers (16-bit formats widen to 4 bytes per pixel);
       even, so a half-resolution band starts on a whole output row */
    size_t rows = BAND_BYTES / t->pitch, rgba_rows = sizeof band_rgba / ((size_t)t->width * 4);
    if (rgba_rows < rows) rows = rgba_rows;
    if (rows > 1) rows &= ~(size_t)1;
    render_texture_rows(t, band, rows * t->pitch, half ? upload_band_half : upload_band, t);
    t->half = (uint8_t)half;
    GLenum error = glGetError();
    if (error) {
        static unsigned reported;
        if (reported++ < 20)
            trace("# texture upload %ux%u failed: GL error %04x (%llu KiB uploaded)", t->width, t->height,
                  (unsigned)error, (unsigned long long)(gpu_bytes >> 10));
    }
    t->gpu_bytes = (uint32_t)out_bytes;
    gpu_bytes += out_bytes;
    t->dirty = 0;
}
void render_texture_free(RenderTexture *t) {
    if (!t->gl) return;
    gl_enter();
    gpu_forget(t);
    gl_leave();
}

void render_texture(uint32_t stage, RenderTexture *t) {
    if (!stage)
        bound = t;
}

void render_draw_up(uint32_t type, uint32_t count, uint32_t data, uint32_t stride) {
    static const GLenum modes[] = {0, GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN};
    uint32_t n = type == 1 ? count : type == 2 ? count * 2 : type == 3 ? count + 1
               : type == 4 ? count * 3 : count + 2;
    if (type < 1 || type > 6 || !n || n > 65536)
        return;
    int rhw = (fvf & 0x00E) == 0x004;
    uint32_t off = (fvf & 0x00E) == 0x002 ? 12 : rhw ? 16 : 12;
    if (fvf & 0x010) off += 12;
    uint32_t diffuse = fvf & 0x040 ? off : 0xFFFFFFFFu;
    if (fvf & 0x040) off += 4;
    if (fvf & 0x080) off += 4;
    uint32_t tex = ((fvf >> 8) & 15) ? off : 0xFFFFFFFFu;
    gl_enter(); /* the vertex arrays below are shared by the drawing threads */
    static float pos[65536 * 3], uv[65536 * 2];
    static uint8_t col[65536 * 4];
    for (uint32_t i = 0; i < n; i++) {
        uint32_t v = data + i * stride;
        float xyz[3];
        memcpy(xyz, G(v), 12);
        pos[i * 3] = xyz[0] + (rhw ? 0.5f : 0);   /* D3D9 pixel centres */
        pos[i * 3 + 1] = xyz[1] + (rhw ? 0.5f : 0);
        pos[i * 3 + 2] = 0;
        uint32_t argb = diffuse != 0xFFFFFFFFu ? rd32(v + diffuse) : 0xFFFFFFFFu;
        col[i * 4] = (uint8_t)(argb >> 16); col[i * 4 + 1] = (uint8_t)(argb >> 8);
        col[i * 4 + 2] = (uint8_t)argb; col[i * 4 + 3] = (uint8_t)(argb >> 24);
        if (tex != 0xFFFFFFFFu)
            memcpy(&uv[i * 2], G(v + tex), 8);
    }
    apply_states();
    if (bound && tex != 0xFFFFFFFFu) {
        if (bound->dirty || !bound->gl)
            upload(bound);
        bound->drawn++;
        bound->used_frame = d3d_frames;
        glEnable(GL_TEXTURE_2D);
        glBindTexture(GL_TEXTURE_2D, bound->gl);
        int smooth = bound->half; /* a half-resolution texture is scaled back up */
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_linear || smooth ? GL_LINEAR : GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_linear || smooth ? GL_LINEAR : GL_NEAREST);
        glEnableClientState(GL_TEXTURE_COORD_ARRAY);
        glTexCoordPointer(2, GL_FLOAT, 0, uv);
    } else {
        glDisable(GL_TEXTURE_2D);
        glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    }
    glEnableClientState(GL_VERTEX_ARRAY);
    glVertexPointer(3, GL_FLOAT, 0, pos);
    glEnableClientState(GL_COLOR_ARRAY);
    glColorPointer(4, GL_UNSIGNED_BYTE, 0, col);
    glDrawArrays(modes[type], 0, (GLsizei)n);
    gl_leave();
}

/* The last frame is kept for the capture written at exit. Reading it back stalls the
   GPU, so the Vita only does it once a second. */
static uint8_t *last_frame;
static uint32_t capture_w, capture_h;

void render_present(void) {
    gl_enter();
#ifdef __vita__
    /* vitaGL only runs the frame's draws at the swap, so glReadPixels here returned
       the cleared target; the capture is copied from the displayed buffer below. */
    capture_w = VITA_W;
    capture_h = VITA_H;
    int read = 0;
#else
    capture_w = screen_w;
    capture_h = screen_h;
    int read = 1;
#endif
    if (!last_frame)
        last_frame = malloc((size_t)capture_w * capture_h * 4);
    if (read && last_frame)
        glReadPixels(0, 0, (GLsizei)capture_w, (GLsizei)capture_h, GL_RGBA, GL_UNSIGNED_BYTE, last_frame);
#ifdef __vita__
    /* The side bars of the 960x544 screen are outside the game's 4:3 area: clear them
       every frame, or each of vitaGL's display buffers keeps whatever was there. */
    if (VIEW_X > 0) {
    GLfloat clear[4];
    glGetFloatv(GL_COLOR_CLEAR_VALUE, clear);
    glClearColor(0, 0, 0, 1);
    glScissor(0, 0, VIEW_X, VITA_H);
    glClear(GL_COLOR_BUFFER_BIT);
    glScissor(VIEW_X + VIEW_W, 0, VITA_W - VIEW_X - VIEW_W, VITA_H);
    glClear(GL_COLOR_BUFFER_BIT);
    glScissor(VIEW_X, 0, VIEW_W, VITA_H);
    glClearColor(clear[0], clear[1], clear[2], clear[3]);
    }
#endif
    platform_swap();
#ifdef __vita__
    if (d3d_frames % 60 == 0 && last_frame) { /* once a second: copy what is on screen */
        SceDisplayFrameBuf fb;
        memset(&fb, 0, sizeof fb);
        fb.size = sizeof fb;
        sceDisplayWaitVblankStart();
        if (sceDisplayGetFrameBuf(&fb, SCE_DISPLAY_SETBUF_NEXTFRAME) >= 0 && fb.base)
            for (uint32_t y = 0; y < VITA_H; y++) /* stored bottom-up, like GL rows */
                memcpy(last_frame + (size_t)(VITA_H - 1 - y) * VITA_W * 4,
                       (const uint8_t *)fb.base + (size_t)y * fb.pitch * 4, VITA_W * 4);
    }
#endif
    gl_leave();
#ifndef __vita__
    /* T123_CAPTURE="n[,n...]" saves frame-<n>.bmp at those presented frames, so a
       scripted run (T123_PRESS) can be checked screen by screen. */
    const char *list = getenv("T123_CAPTURE");
    for (const char *p = list; p && *p; ) {
        char *end;
        unsigned long long n = strtoull(p, &end, 10);
        if (end == p) break;
        if (n == d3d_frames) {
            char name[64];
            snprintf(name, sizeof name, "frame-%llu.bmp", n);
            render_capture_bmp(name);
        }
        p = *end == ',' ? end + 1 : end;
    }
#endif
    render_pump_events();
}

int render_capture_bmp(const char *path) {
    if (!last_frame)
        return -1;
    char full[1200];
#ifdef __vita__
    snprintf(full, sizeof full, "%s/recomp-screen.bmp", host_data_dir); /* where the Vita runner looks */
    (void)path;
#else
    snprintf(full, sizeof full, "%s", path);
#endif
    FILE *f = fopen(full, "wb");
    if (!f)
        return -1;
    uint32_t data = capture_w * capture_h * 3;
    uint32_t header[13] = {54 + data, 0, 54, 40, capture_w, capture_h, 0x00180001u, 0, data, 2835, 2835, 0, 0};
    fwrite("BM", 1, 2, f);
    fwrite(header, 4, 13, f);
    for (uint32_t i = 0; i < capture_w * capture_h; i++) { /* GL rows are bottom-up, like BMP */
        uint8_t bgr[3] = {last_frame[i * 4 + 2], last_frame[i * 4 + 1], last_frame[i * 4]};
        fwrite(bgr, 1, 3, f);
    }
    fclose(f);
    return 0;
}
