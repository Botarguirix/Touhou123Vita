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
#include "net.h"
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
/* Render resolution: the display unit scales 720x408, 640x368 and 480x272 to the
   screen, so a lower one is cheaper to fill and just looks coarser. Chosen at start-up
   (render resolution test: 640x368 by default; res.txt in the data directory holds
   960, 720, 640 or 480 to pick another). */
static int vita_w = 640, vita_h = 368;
#define VITA_W vita_w
#define VITA_H vita_h
#define VIEW_W vita_w
#define VIEW_X 0
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
    char memory[256];
    platform_clock_report(memory, sizeof memory);
    trace("# clocks: %s", memory);
    platform_memory_report(memory, sizeof memory);
    trace("# before vitaGL: %s", memory);
    /* Explicit pool sizes (the threshold variant derives them from the remaining
       budget). The return value is not a success flag: vitaGL returns whether it had
       to lower the resolution, i.e. GL_FALSE after a normal start, so it is ignored. */
    /* Triple buffering (before vglInit): with two buffers and vsync a logic step of 17 ms
       missed the 16.7 ms vblank and waited until 33 ms, which also tripped the frame skip
       (heartbeats showed ~58 steps but only ~42 frames drawn per second). */
    vglSetDisplayBufferCount(3);
    {
        FILE *rf = fopen("ux0:data/touhou123vita/res.txt", "rb");
        int want = 0;
        if (rf) { /* (fscanf pulled in libc code that vita-elf-create crashed on) */
            char text[16] = "";
            if (fgets(text, sizeof text, rf)) want = atoi(text);
            fclose(rf);
        }
        if (want == 960) { vita_w = 960; vita_h = 544; }
        else if (want == 720) { vita_w = 720; vita_h = 408; }
        else if (want == 480) { vita_w = 480; vita_h = 272; }
        else { vita_w = 640; vita_h = 368; }
        trace("# display: render resolution %dx%d (res.txt: %d)", vita_w, vita_h, want);
    }
    vglInitWithCustomSizes(0, VITA_W, VITA_H, 8 << 20, 64 << 20, 16 << 20, 0, SCE_GXM_MULTISAMPLE_NONE);
    {   /* vsync-off.txt in the data directory: present without waiting for the vblank (tearing) */
        FILE *vs = fopen("ux0:data/touhou123vita/vsync-off.txt", "rb");
        if (vs) { fclose(vs); vglWaitVblankStart(GL_FALSE); }
        trace("# display: 3 buffers, vsync %s", vs ? "off (vsync-off.txt)" : "on");
    }
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
/* GL_TRUE while a system dialog (the keyboard) is on screen: vitaGL then lets the
   common dialog draw over the frame and updates it */
static void platform_swap(void) { vglSwapBuffers(ime_dialog_active() ? GL_TRUE : GL_FALSE); }
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

/* Vita frame skipping: the game's logic advances one step per presented frame, so a
   lower frame rate would slow the game down. Instead, when a frame took longer than a
   refresh, the next one is not drawn (its clears and draws are dropped and it is not
   swapped), never twice in a row: the game keeps its speed and the screen shows at
   least 30 FPS. */
static int skip_drawing;
static uint64_t swap_us_sum, swap_count; /* time inside vglSwapBuffers, for the pacing report */

void render_clear(uint32_t flags, uint32_t color, float z, uint32_t stencil) {
    if (skip_drawing) return;
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
static uint64_t gpu_t_query, gpu_t_scan, gpu_t_delete, gpu_short_stops; /* microseconds, see up_report */

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
/* vglMemFree walks vitaGL's allocator and cost ~4.5 ms per upload (24.9 s of 26.6 s of
   "making room" in a 14 minute fight), so it is asked at most once every 6 frames; in
   between the free memory is the last answer minus what was uploaded since (deferred
   frees only make that estimate pessimistic). */
static uint64_t gpu_free_cache, gpu_added_since, gpu_free_frame = ~0ull;
static int gpu_memory_short(uint64_t need) {
#ifdef __vita__
    if (gpu_free_frame == ~0ull || d3d_frames - gpu_free_frame >= 6) {
        gpu_free_cache = (uint64_t)vglMemFree(VGL_MEM_VRAM) + vglMemFree(VGL_MEM_PHYCONT);
        gpu_free_frame = d3d_frames;
        gpu_added_since = 0;
    }
    uint64_t free_now = gpu_free_cache > gpu_added_since ? gpu_free_cache - gpu_added_since : 0;
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
    /* vitaGL frees a deleted texture late, so its free memory does not rise while this
       loop evicts: with the short-memory test alone it kept dropping every older
       texture (3500 evictions with ~11-30 MiB resident in a 10 minute fight, "making
       room" 56 % of the upload time). When only that test asks for room, evict about
       the size of the new texture and stop; glTexImage2D's retry in upload() still
       evicts more if the allocation really fails. */
    uint64_t freed = 0;
    for (;;) {
        uint64_t q0 = platform_ticks_us();
        int over_budget = gpu_bytes + need > gpu_budget;
        int short_mem = !over_budget && gpu_bytes && gpu_memory_short(need);
        gpu_t_query += platform_ticks_us() - q0;
        if (!over_budget && !short_mem) break;
        if (!over_budget && freed >= need) { gpu_short_stops++; break; }
        uint64_t s0 = platform_ticks_us();
        RenderTexture *oldest = NULL;
        for (unsigned i = 1; i < RENDER_MAX_TEXTURES; i++) {
            RenderTexture *t = &textures[i];
            if (t->gl && t->used_frame < d3d_frames && (!oldest || t->used_frame < oldest->used_frame))
                oldest = t;
        }
        gpu_t_scan += platform_ticks_us() - s0;
        if (!oldest) return; /* everything was drawn this frame: go over budget */
        freed += oldest->gpu_bytes;
        uint64_t d0 = platform_ticks_us();
        gpu_forget(oldest);
        gpu_t_delete += platform_ticks_us() - d0;
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
/* The format switch is outside the pixel loops (it ran once per pixel before), and the
   5-bit channel expansion uses a table instead of a multiply and divide per channel. */
static uint8_t expand5[32], expand6[64];
static void init_expand_tables(void) {
    for (unsigned i = 0; i < 32; i++) expand5[i] = (uint8_t)(i * 255 / 31);
    for (unsigned i = 0; i < 64; i++) expand6[i] = (uint8_t)(i * 255 / 63);
}

static void convert_rows(const RenderTexture *t, const uint8_t *src, uint8_t *rgba, uint32_t n) {
    if (!expand5[31]) init_expand_tables();
    const uint32_t w = t->width, fmt = t->format;
    for (uint32_t y = 0; y < n; y++) {
        const uint8_t *p = src + (size_t)y * t->pitch;
        uint8_t *o = rgba + (size_t)y * w * 4;
        switch (fmt) {
        case 21: case 22:
            for (uint32_t x = 0; x < w; x++, p += 4, o += 4) {
                o[0] = p[2]; o[1] = p[1]; o[2] = p[0]; o[3] = fmt == 22 ? 255 : p[3];
            }
            break;
        case 26: /* A4R4G4B4 */
            for (uint32_t x = 0; x < w; x++, p += 2, o += 4) {
                uint32_t v = p[0] | p[1] << 8;
                o[0] = ((v >> 8) & 15) * 17; o[1] = ((v >> 4) & 15) * 17; o[2] = (v & 15) * 17; o[3] = (v >> 12) * 17;
            }
            break;
        case 25: case 24: /* A1R5G5B5, X1R5G5B5 */
            for (uint32_t x = 0; x < w; x++, p += 2, o += 4) {
                uint32_t v = p[0] | p[1] << 8;
                o[0] = expand5[(v >> 10) & 31]; o[1] = expand5[(v >> 5) & 31]; o[2] = expand5[v & 31];
                o[3] = fmt == 24 || (v >> 15) ? 255 : 0;
            }
            break;
        case 23: /* R5G6B5 */
            for (uint32_t x = 0; x < w; x++, p += 2, o += 4) {
                uint32_t v = p[0] | p[1] << 8;
                o[0] = expand5[(v >> 11) & 31]; o[1] = expand6[(v >> 5) & 63]; o[2] = expand5[v & 31]; o[3] = 255;
            }
            break;
        case 28: /* A8 */
            for (uint32_t x = 0; x < w; x++, o += 4) { o[0] = o[1] = o[2] = 0; o[3] = p[x]; }
            break;
        case 50: /* L8 */
            for (uint32_t x = 0; x < w; x++, o += 4) { o[0] = o[1] = o[2] = p[x]; o[3] = 255; }
            break;
        default:
            for (uint32_t x = 0; x < w; x++, o += 4) { o[0] = 255; o[1] = 0; o[2] = 255; o[3] = 255; } /* unknown: magenta */
            break;
        }
    }
}

/* Where upload time goes (microseconds), reported every 10 s while uploads happen. */
static struct { uint64_t n, total, room, alloc, fill, last_report; } up_stats;
static void up_report(uint64_t now) {
    if (!up_stats.n || now - up_stats.last_report < 10000000) return;
    trace("# texture uploads: %llu in %llu ms (making room %llu ms [free query %llu, scan %llu, delete %llu], GL alloc %llu ms, fill = inflate+convert+GL %llu ms), %llu evictions so far, %llu short-memory stops",
          (unsigned long long)up_stats.n, (unsigned long long)(up_stats.total / 1000), (unsigned long long)(up_stats.room / 1000),
          (unsigned long long)(gpu_t_query / 1000), (unsigned long long)(gpu_t_scan / 1000), (unsigned long long)(gpu_t_delete / 1000),
          (unsigned long long)(up_stats.alloc / 1000), (unsigned long long)(up_stats.fill / 1000), (unsigned long long)gpu_evictions,
          (unsigned long long)gpu_short_stops);
    gpu_t_query = gpu_t_scan = gpu_t_delete = 0;
    uint64_t last = now;
    memset(&up_stats, 0, sizeof up_stats);
    up_stats.last_report = last;
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
/* Only the 640+ backgrounds are halved by default. The resolution test that halved every
   texture of 512x512 and up also halved the game's text (the result screen draws its
   spell-card names into one of those big textures, and came out as 5-pixel smears) and
   it gained no frame rate, so it is off now. half-sprites.txt in the data directory turns
   it back on, for measuring. */
static int half_min_side(void) {
    static int min_side;
    if (!min_side) {
#ifdef __vita__
        FILE *f = fopen("ux0:data/touhou123vita/half-sprites.txt", "rb");
        min_side = f ? 512 : 640;
        if (f) fclose(f);
        trace("# textures: halving textures with both sides >= %d (half-sprites.txt present: %d)", min_side, f != NULL);
#else
        min_side = getenv("T123_HALF_SPRITES") ? 512 : 640;
#endif
    }
    return min_side;
}
static int wants_half(const RenderTexture *t) {
    if (half_res_enabled < 0) half_res_enabled = getenv("T123_HALF_RES") != NULL;
    int m = half_min_side();
    return half_res_enabled && t->format == 21 && t->pitch == t->width * 4 && !(t->width & 1) &&
           t->width >= (uint32_t)m && t->height >= (uint32_t)m;
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

/* 16-bit upload (RGBA4444): half the GPU memory and half the upload traffic for the
   large 32-bit sprite sheets. vitaGL copies 16-bit data raw into a U4U4U4U4_RGBA
   texture, so the pixels are packed here as the GL type says (R in the top nibble).
   On the Vita it is on unless tex32.txt exists in the data directory; on PC
   T123_TEX16=1 turns it on to look at it. Only A8R8G8B8/X8R8G8B8 textures of at least
   256x256 are packed: small UI textures keep their 32 bits. */
static int tex16_enabled(void) {
    static int state = -1;
    if (state < 0) {
#ifdef __vita__
        FILE *f = fopen("ux0:data/touhou123vita/tex32.txt", "rb");
        state = f == NULL;
        if (f) fclose(f);
        trace("# textures: 16-bit upload %s", state ? "on (tex32.txt turns it off)" : "off (tex32.txt present)");
#else
        state = getenv("T123_TEX16") != NULL;
#endif
    }
    return state;
}

static uint8_t q4[256];
static uint16_t band16[BAND_BYTES / 4]; /* a band of 32-bit rows holds at most BAND_BYTES/4 pixels */
static void upload_band_16(void *ctx, const uint8_t *rows, uint32_t y, uint32_t n) {
    RenderTexture *t = ctx;
    if (!q4[255]) for (unsigned i = 0; i < 256; i++) q4[i] = (uint8_t)((i * 15 + 127) / 255);
    const uint8_t *p = rows;
    uint16_t *o = band16;
    const int opaque = t->format == 22;
    for (size_t i = 0, count = (size_t)n * t->width; i < count; i++, p += 4)
        *o++ = (uint16_t)(q4[p[2]] << 12 | q4[p[1]] << 8 | q4[p[0]] << 4 | (opaque ? 15 : q4[p[3]]));
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, (GLint)y, (GLsizei)t->width, (GLsizei)n, GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4, band16);
}

/* what the game really creates, to decide what else is worth compressing */
static struct { unsigned n, n16; uint64_t px; } fmt_census[64];
static void census_report(uint64_t now) { /* once a minute: uploads per D3D format, and how many went out as 16 bits */
    static uint64_t last;
    if (now - last < 60000000) return;
    last = now;
    char line[300];
    int len = snprintf(line, sizeof line, "# texture formats (uploads, Mpixels, as 16-bit):");
    for (unsigned f = 0; f < 64 && len < (int)sizeof line - 40; f++)
        if (fmt_census[f].n)
            len += snprintf(line + len, sizeof line - len, " fmt%u %u/%u.%02u/%u;", f, fmt_census[f].n,
                            (unsigned)(fmt_census[f].px / 1000000), (unsigned)(fmt_census[f].px / 10000 % 100), fmt_census[f].n16);
    trace("%s", line);
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
    int use16 = !half && (t->format == 21 || t->format == 22) && t->pitch == t->width * 4 &&
                (uint64_t)t->width * t->height >= 256 * 256 && tex16_enabled();
    GLenum gtype = use16 ? GL_UNSIGNED_SHORT_4_4_4_4 : GL_UNSIGNED_BYTE;
    size_t out_bytes = (size_t)gw * gh * (use16 ? 2 : 4);
    if (t->format < 64) {
        fmt_census[t->format].n++;
        fmt_census[t->format].n16 += use16;
        fmt_census[t->format].px += (uint64_t)t->width * t->height;
    }
    if (t->pitch > BAND_BYTES || (size_t)t->width * 4 > sizeof band_rgba) {
        trace("# texture upload %ux%u: rows wider than the upload band", t->width, t->height);
        return;
    }
    uint64_t t0 = platform_ticks_us();
    gpu_forget(t);
    gpu_make_room(out_bytes);
    uint64_t t1 = platform_ticks_us();
    glGenTextures(1, &t->gl);
    glBindTexture(GL_TEXTURE_2D, t->gl);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    /* When vitaGL cannot allocate the storage, glTexSubImage2D writes through a NULL
       pointer (a crash in write_rgba8888 in Story mode): evict and retry, and if there
       is still no room leave the texture empty for this frame. */
    while (glGetError()) {}
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, (GLsizei)gw, (GLsizei)gh, 0, GL_RGBA, gtype, NULL);
    for (unsigned attempt = 0; glGetError() != GL_NO_ERROR; attempt++) {
        RenderTexture *oldest = NULL;
        for (unsigned i = 1; i < RENDER_MAX_TEXTURES; i++) {
            RenderTexture *o = &textures[i];
            if (o != t && o->gl && (!oldest || o->used_frame < oldest->used_frame))
                oldest = o;
        }
        if (!oldest || attempt == 64) {
            trace("# texture upload %ux%u: no GPU memory, skipped", t->width, t->height);
            glDeleteTextures(1, &t->gl);
            t->gl = 0;
            return;
        }
        gpu_forget(oldest);
        glBindTexture(GL_TEXTURE_2D, t->gl);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, (GLsizei)gw, (GLsizei)gh, 0, GL_RGBA, gtype, NULL);
    }
    /* band rows: bounded by both buffers (16-bit formats widen to 4 bytes per pixel);
       even, so a half-resolution band starts on a whole output row */
    uint64_t t2 = platform_ticks_us();
    size_t rows = BAND_BYTES / t->pitch, rgba_rows = sizeof band_rgba / ((size_t)t->width * 4);
    if (rgba_rows < rows) rows = rgba_rows;
    if (rows > 1) rows &= ~(size_t)1;
    t->gpu16 = (uint8_t)use16;
    render_texture_rows(t, band, rows * t->pitch, half ? upload_band_half : use16 ? upload_band_16 : upload_band, t);
    uint64_t t3 = platform_ticks_us();
    up_stats.n++; up_stats.total += t3 - t0; up_stats.room += t1 - t0; up_stats.alloc += t2 - t1; up_stats.fill += t3 - t2;
    up_report(t3);
    census_report(t3);
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
    gpu_added_since += out_bytes;
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
    if (skip_drawing) return;
    static const GLenum modes[] = {0, GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN};
    uint32_t n = type == 1 ? count : type == 2 ? count * 2 : type == 3 ? count + 1
               : type == 4 ? count * 3 : count + 2;
    if (type < 1 || type > 6 || !n || n > 65536)
        return;
    /* XYZW (0x4002) comes only from the effect passes (Utsuho's pshaderEx0), whose
       vertex shader takes screen pixels, so it is drawn like XYZRHW */
    int rhw = (fvf & 0x400E) == 0x004 || (fvf & 0x400E) == 0x4002;
    uint32_t off = rhw ? 16 : 12;
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

/* Every 10 s: game steps, frames drawn and music decode cost, so a run that freezes
   (and never writes its exit report) still shows where it was going. */
static void heartbeat(int drawn) {
    static uint64_t next, steps, draws;
    uint64_t now = platform_ticks_us();
    steps++;
    draws += drawn != 0;
    /* Where a logic step goes: the interval between presents of this thread, split into
       time blocked in WaitForSingleObject, Sleep and the swap; the rest is the guest's own
       code plus the host calls it makes. The histogram shows whether the intervals sit at
       the game's own limiter (~17 ms) or are spikes of work. */
    static uint64_t last_present, w_wait, w_sleep, w_calls, sum_interval, intervals, hist[7];
    static uint64_t prev_wait, prev_sleep, prev_calls, thread_switches;
    static uint64_t *thread_tag; /* the wait counters are per thread: the address of one identifies the caller */
    if (thread_tag != &host_wait_us) {
        if (thread_tag) thread_switches++;
        thread_tag = &host_wait_us;
        prev_wait = host_wait_us; prev_sleep = host_sleep_us; prev_calls = host_wait_calls;
        last_present = 0; /* a step measured across two threads is meaningless */
    }
    if (last_present) {
        uint64_t iv = now - last_present;
        sum_interval += iv;
        intervals++;
        hist[iv < 15000 ? 0 : iv < 16500 ? 1 : iv < 17500 ? 2 : iv < 20000 ? 3 : iv < 25000 ? 4 : iv < 34000 ? 5 : 6]++;
        w_wait += host_wait_us - prev_wait;
        w_sleep += host_sleep_us - prev_sleep;
        w_calls += host_wait_calls - prev_calls;
    }
    prev_wait = host_wait_us; prev_sleep = host_sleep_us; prev_calls = host_wait_calls;
    last_present = now;
    if (!next) next = now + 10000000;
    if (now < next) return;
    if (intervals) {
        uint64_t n = intervals;
        uint64_t swap_avg = swap_count ? swap_us_sum / swap_count : 0;
        long long other = (long long)(sum_interval / n) - (long long)(w_wait / n) - (long long)(w_sleep / n) - (long long)swap_avg;
        trace("# pacing: %llu steps, interval %llu us avg = wait %llu us (%llu calls) + sleep %llu us + swap %llu us + other %lld us; "
              "present thread changed %llu times; "
              "intervals <15ms %llu, 15-16.5 %llu, 16.5-17.5 %llu, 17.5-20 %llu, 20-25 %llu, 25-34 %llu, >=34 %llu",
              (unsigned long long)n, (unsigned long long)(sum_interval / n), (unsigned long long)(w_wait / n),
              (unsigned long long)(w_calls / n), (unsigned long long)(w_sleep / n), (unsigned long long)swap_avg,
              other, (unsigned long long)thread_switches,
              (unsigned long long)hist[0], (unsigned long long)hist[1], (unsigned long long)hist[2], (unsigned long long)hist[3],
              (unsigned long long)hist[4], (unsigned long long)hist[5], (unsigned long long)hist[6]);
        swap_us_sum = swap_count = 0;
    }
    w_wait = w_sleep = w_calls = sum_interval = intervals = 0;
    memset(hist, 0, sizeof hist);
    uint64_t us, bytes;
    vorbis_stats(&us, &bytes);
    char memory[128];
    platform_memory_report(memory, sizeof memory);
    trace("# heartbeat: frame %llu, %llu steps and %llu frames drawn in the last 10 s, "
          "music decode %llu ms for %llu KiB; guest heap %u KiB live of %u KiB, "
          "textures %llu KiB on the GPU, %llu KiB stored, %s", (unsigned long long)d3d_frames,
          (unsigned long long)steps, (unsigned long long)draws, (unsigned long long)(us / 1000),
          (unsigned long long)(bytes >> 10), heap_live_bytes() >> 10, heap_used() >> 10,
          (unsigned long long)(gpu_bytes >> 10), (unsigned long long)(texture_live >> 10), memory);
    steps = draws = 0;
    next = now + 10000000;
}

void render_present(void) {
    ime_poll();                                  /* the keyboard for text fields (Vita) */
    net_poll();                                  /* SceNet + ad-hoc search, from the first frame (Vita) */
    if (ime_dialog_active()) skip_drawing = 0;   /* the dialog needs a swap every frame */
    heartbeat(!skip_drawing);
#ifdef __vita__
    static uint64_t last_swap, skipped;
    if (skip_drawing) { /* nothing was drawn: no swap, no wait for the display */
        skip_drawing = 0;
        last_swap = platform_ticks_us(); /* measure the next frame on its own */
        if (++skipped % 600 == 1)
            trace("# frame skip: %llu frames not drawn so far (frame %llu)", (unsigned long long)skipped, d3d_frames);
        return;
    }
#endif
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
    {
        uint64_t s0 = platform_ticks_us();
        platform_swap();
        swap_us_sum += platform_ticks_us() - s0;
        swap_count++;
    }
#ifdef __vita__
    {
        uint64_t now = platform_ticks_us(); /* a frame slower than ~50 FPS: skip drawing the next */
        if (last_swap && now - last_swap > 20000) skip_drawing = 1;
        last_swap = now;
    }
#endif
    /* (The screen used to be copied here once a second for the final BMP: reading 2 MiB of
       uncached framebuffer and waiting for a vblank cost 20-50 ms, one slow logic step
       every second. The copy now happens in render_capture_bmp, when it is needed.) */
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
#ifdef __vita__
    /* the displayed buffer is copied only now (see render_present) */
    if (!last_frame)
        last_frame = malloc((size_t)VITA_W * VITA_H * 4);
    capture_w = VITA_W;
    capture_h = VITA_H;
    if (last_frame) {
        SceDisplayFrameBuf fb;
        memset(&fb, 0, sizeof fb);
        fb.size = sizeof fb;
        if (sceDisplayGetFrameBuf(&fb, SCE_DISPLAY_SETBUF_NEXTFRAME) >= 0 && fb.base)
            for (uint32_t y = 0; y < VITA_H; y++) /* stored bottom-up, like GL rows */
                memcpy(last_frame + (size_t)(VITA_H - 1 - y) * VITA_W * 4,
                       (const uint8_t *)fb.base + (size_t)y * fb.pitch * 4, VITA_W * 4);
    }
#endif
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
