/* Direct3D 9 and D3DX for the recompiled game, limited to what docs/COM_USAGE.md
 * (Codex T3) measured: device, swap chain, textures/surfaces, DrawPrimitiveUP,
 * render/sampler/stage state, effects. Rendering goes through render.h; this file
 * owns the COM surface and the guest-visible data (caps, descriptors, locks). */
#include "com.h"
#include "render.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define API(name) static void name(Cpu *c)

static ComClass d3d9_class = COM_CLASS(IDirect3D9);
static ComClass device_class = COM_CLASS(IDirect3DDevice9);
static ComClass swapchain_class = COM_CLASS(IDirect3DSwapChain9);
static ComClass texture_class = COM_CLASS(IDirect3DTexture9);
static ComClass surface_class = COM_CLASS(IDirect3DSurface9);
static ComClass effect_class = COM_CLASS(ID3DXEffect);

static uint32_t device_object, swapchain_object;
unsigned long long d3d_frames, d3d_draws;
static unsigned long long frame_limit = 300;

/* -- textures --------------------------------------------------------------------- */
RenderTexture textures[RENDER_MAX_TEXTURES];
static unsigned texture_count = 1; /* index 0 = none */
static unsigned free_texture;      /* released slots, linked through next_free */

static unsigned format_bpp(uint32_t format) {
    switch (format) {
    case 21: case 22: return 4;          /* A8R8G8B8, X8R8G8B8 */
    case 23: case 24: case 25: case 26:  /* R5G6B5, X1R5G5B5, A1R5G5B5, A4R4G4B4 */
        return 2;
    case 28: case 50: return 1;          /* A8, L8 */
    default: return 4;
    }
}

static uint32_t texture_new(uint32_t w, uint32_t h, uint32_t format) {
    unsigned i = free_texture;
    if (i)
        free_texture = textures[i].next_free;
    else if (texture_count == RENDER_MAX_TEXTURES)
        return 0;
    else
        i = texture_count++;
    RenderTexture *t = &textures[i];
    memset(t, 0, sizeof *t);
    t->width = w;
    t->height = h;
    t->format = format;
    t->pitch = w * format_bpp(format);
    t->data = calloc(h, t->pitch);
    t->dirty = 1;
    return com_new(&texture_class, i, 0);
}

/* The game streams textures while loading: a released texture gives back its pixels
   and its slot, or the guest heap runs out during boot. */
static uint32_t texture_release(uint32_t o) {
    uint32_t n = rd32(o + 4);
    if (n) wr32(o + 4, --n);
    if (!n) {
        unsigned i = com_index(o);
        RenderTexture *t = &textures[i];
        render_texture_free(t);
        heap_free(t->pixels);
        free(t->data);
        memset(t, 0, sizeof *t);
        t->next_free = free_texture;
        free_texture = i;
        heap_free(o);
    }
    return n;
}
API(Texture_Release) { ret_stdcall(c, texture_release(ARG(c, 0)), 1); }
API(Surface_Release) {
    uint32_t o = ARG(c, 0), n = rd32(o + 4);
    if (n) wr32(o + 4, --n);
    if (!n) { texture_release(rd32(o + 12)); heap_free(o); }
    ret_stdcall(c, n, 1);
}

/* -- IDirect3D9 ------------------------------------------------------------------------- */
API(GetAdapterDisplayMode) {
    uint32_t m = ARG(c, 2);
    wr32(m, 1280); wr32(m + 4, 720); wr32(m + 8, 60); wr32(m + 12, 22 /* X8R8G8B8 */);
    ret_stdcall(c, S_OK, 3);
}

static void fill_caps(uint32_t p) {
    memset(G(p), 0, 304);
    wr32(p + 0, 1);                                   /* DeviceType HAL */
    for (uint32_t off = 8; off <= 84; off += 4)       /* capability bit fields: all */
        wr32(p + off, 0xFFFFFFFFu);
    wr32(p + 88, 4096); wr32(p + 92, 4096);           /* MaxTextureWidth/Height */
    wr32(p + 100, 8192); wr32(p + 104, 8192);
    wr32(p + 108, 16);
    for (uint32_t off = 136; off <= 144; off += 4) wr32(p + off, 0xFFFFFFFFu);
    wr32(p + 148, 8); wr32(p + 152, 8);               /* texture stages */
    wr32(p + 156, 0xFFFFFFFFu);
    wr32(p + 180, 0xFFFFF); wr32(p + 184, 0xFFFFFF); wr32(p + 188, 16); wr32(p + 192, 255);
    wr32(p + 196, 0xFFFE0200u);                       /* vs_2_0 */
    wr32(p + 200, 256);
    wr32(p + 204, 0xFFFF0200u);                       /* ps_2_0 */
    float max_value = 65504.0f;
    memcpy(G(p + 208), &max_value, 4);
}

API(D3D9_GetDeviceCaps) { fill_caps(ARG(c, 3)); ret_stdcall(c, S_OK, 4); }

API(CreateDevice) {
    uint32_t params = ARG(c, 5), out = ARG(c, 6);
    uint32_t w = rd32(params), h = rd32(params + 4);
    trace("IDirect3D9::CreateDevice(type=%u, flags=%08x, backbuffer %ux%u, windowed=%u)",
          ARG(c, 2), ARG(c, 4), w, h, rd32(params + 32));
    if (render_init(w ? w : 640, h ? h : 480)) {
        ret_stdcall(c, E_FAIL, 7);
        return;
    }
    device_object = com_new(&device_class, 0, 0);
    swapchain_object = com_new(&swapchain_class, 0, 0);
    wr32(out, device_object);
    ret_stdcall(c, S_OK, 7);
}

/* -- IDirect3DDevice9 ------------------------------------------------------------------ */
API(TestCooperativeLevel) { ret_stdcall(c, S_OK, 1); }
API(Device_GetDeviceCaps) { fill_caps(ARG(c, 1)); ret_stdcall(c, S_OK, 2); }
API(GetSwapChain) {
    wr32(ARG(c, 2), swapchain_object);
    wr32(swapchain_object + 4, rd32(swapchain_object + 4) + 1);
    ret_stdcall(c, S_OK, 3);
}
API(Reset) { trace("IDirect3DDevice9::Reset"); ret_stdcall(c, S_OK, 2); }
API(BeginScene) { ret_stdcall(c, S_OK, 1); }
API(EndScene) { ret_stdcall(c, S_OK, 1); }
API(Clear) {
    render_clear(ARG(c, 3), ARG(c, 4), *(float *)G(c->esp.d + 4 + 4 * 5), ARG(c, 6));
    ret_stdcall(c, S_OK, 7);
}
API(SetRenderState) { render_state(ARG(c, 1), ARG(c, 2)); ret_stdcall(c, S_OK, 3); }
API(GetRenderState) { wr32(ARG(c, 2), render_get_state(ARG(c, 1))); ret_stdcall(c, S_OK, 3); }
API(SetTexture) {
    uint32_t t = ARG(c, 2);
    render_texture(ARG(c, 1), t ? &textures[com_index(t)] : NULL);
    ret_stdcall(c, S_OK, 3);
}
API(SetTextureStageState) { render_stage_state(ARG(c, 1), ARG(c, 2), ARG(c, 3)); ret_stdcall(c, S_OK, 4); }
API(SetSamplerState) { render_sampler_state(ARG(c, 1), ARG(c, 2), ARG(c, 3)); ret_stdcall(c, S_OK, 4); }
API(SetFVF) { render_fvf(ARG(c, 1)); ret_stdcall(c, S_OK, 2); }
API(DrawPrimitiveUP) {
    d3d_draws++;
    render_draw_up(ARG(c, 1), ARG(c, 2), ARG(c, 3), ARG(c, 4));
    ret_stdcall(c, S_OK, 5);
}

/* -- IDirect3DSwapChain9 ------------------------------------------------------------------ */
API(Present) {
    render_present();
    d3d_frames++;
    if (d3d_frames == 1 || d3d_frames % 60 == 0)
        trace("# frame %llu: %llu draws so far", d3d_frames, d3d_draws);
    if (frame_limit && d3d_frames >= frame_limit) {
        char why[96];
        snprintf(why, sizeof why, "frame limit reached (%llu frames presented)", d3d_frames);
        host_exit(c, 0, why);
    }
    ret_stdcall(c, render_quit_requested() ? 0x88760868u /* D3DERR_DEVICELOST */ : S_OK, 6);
}

/* -- textures and surfaces -------------------------------------------------------------- */
API(GetSurfaceLevel) {
    uint32_t t = ARG(c, 0);
    uint32_t s = com_new(&surface_class, com_index(t), 4);
    wr32(s + 12, t);              /* the container stays alive while the level is held */
    wr32(t + 4, rd32(t + 4) + 1);
    wr32(ARG(c, 2), s);
    ret_stdcall(c, S_OK, 3);
}
static void write_desc(uint32_t d, RenderTexture *t) {
    wr32(d, t->format); wr32(d + 4, 3 /* D3DRTYPE_TEXTURE */); wr32(d + 8, 0); wr32(d + 12, 1 /* MANAGED */);
    wr32(d + 16, 0); wr32(d + 20, 0); wr32(d + 24, t->width); wr32(d + 28, t->height);
}
API(Surface_GetDesc) { write_desc(ARG(c, 1), &textures[com_index(ARG(c, 0))]); ret_stdcall(c, S_OK, 2); }
API(Texture_GetLevelDesc) { write_desc(ARG(c, 2), &textures[com_index(ARG(c, 0))]); ret_stdcall(c, S_OK, 3); }
API(Texture_LockRect) {
    RenderTexture *t = &textures[com_index(ARG(c, 0))];
    if (!t->pixels) { /* guest staging copy for the duration of the lock */
        t->pixels = heap_alloc(t->pitch * t->height, 0);
        memcpy(G(t->pixels), t->data, t->pitch * t->height);
    }
    uint32_t lock = ARG(c, 2), rect = ARG(c, 3), bits = t->pixels;
    if (rect)
        bits += rd32(rect + 4) * t->pitch + rd32(rect) * format_bpp(t->format);
    wr32(lock, t->pitch);
    wr32(lock + 4, bits);
    ret_stdcall(c, S_OK, 5);
}
API(Texture_UnlockRect) {
    RenderTexture *t = &textures[com_index(ARG(c, 0))];
    if (t->pixels) {
        memcpy(t->data, G(t->pixels), t->pitch * t->height);
        heap_free(t->pixels);
        t->pixels = 0;
    }
    t->dirty = 1;
    ret_stdcall(c, S_OK, 2);
}

/* -- ID3DXEffect: parameters are recorded, passes draw with the fixed pipeline ---------- */
API(Effect_Begin) { if (ARG(c, 1)) wr32(ARG(c, 1), 1); ret_stdcall(c, S_OK, 3); }

/* -- D3DX imports ------------------------------------------------------------------------ */
API(D3DXCreateTexture) {
    uint32_t w = ARG(c, 1), h = ARG(c, 2), format = ARG(c, 5);
    uint32_t t = texture_new(w, h, format);
    wr32(ARG(c, 7), t);
    ret_stdcall(c, t ? S_OK : E_FAIL, 8);
}
API(D3DXCreateEffect) {
    trace("D3DXCreateEffect(size=%u)", ARG(c, 2));
    wr32(ARG(c, 7), com_new(&effect_class, 0, 0));
    if (ARG(c, 8)) wr32(ARG(c, 8), 0);
    ret_stdcall(c, S_OK, 9);
}
static float rdf(uint32_t a) { float f; memcpy(&f, G(a), 4); return f; }
static void wrf(uint32_t a, float f) { memcpy(G(a), &f, 4); }
API(D3DXVec2Normalize) {
    uint32_t out = ARG(c, 0), v = ARG(c, 1);
    float x = rdf(v), y = rdf(v + 4), l = sqrtf(x * x + y * y);
    wrf(out, l ? x / l : 0); wrf(out + 4, l ? y / l : 0);
    ret_stdcall(c, out, 2);
}
API(D3DXVec2Hermite) {
    uint32_t out = ARG(c, 0), v1 = ARG(c, 1), t1 = ARG(c, 2), v2 = ARG(c, 3), t2 = ARG(c, 4);
    float s = rdf(c->esp.d + 4 + 4 * 5), s2 = s * s, s3 = s2 * s;
    float h1 = 2 * s3 - 3 * s2 + 1, h2 = -2 * s3 + 3 * s2, h3 = s3 - 2 * s2 + s, h4 = s3 - s2;
    for (int k = 0; k < 2; k++)
        wrf(out + 4 * k, h1 * rdf(v1 + 4 * k) + h2 * rdf(v2 + 4 * k) + h3 * rdf(t1 + 4 * k) + h4 * rdf(t2 + 4 * k));
    ret_stdcall(c, out, 6);
}
API(Direct3DCreate9) {
    trace("Direct3DCreate9(SDK %u)", ARG(c, 0));
    ret_stdcall(c, com_new(&d3d9_class, 0, 0), 1);
}

static void bind_all(void) {
    com_bind(&d3d9_class, "GetAdapterDisplayMode", GetAdapterDisplayMode);
    com_bind(&d3d9_class, "GetDeviceCaps", D3D9_GetDeviceCaps);
    com_bind(&d3d9_class, "CreateDevice", CreateDevice);
    com_bind(&device_class, "TestCooperativeLevel", TestCooperativeLevel);
    com_bind(&device_class, "GetDeviceCaps", Device_GetDeviceCaps);
    com_bind(&device_class, "GetSwapChain", GetSwapChain);
    com_bind(&device_class, "Reset", Reset);
    com_bind(&device_class, "BeginScene", BeginScene);
    com_bind(&device_class, "EndScene", EndScene);
    com_bind(&device_class, "Clear", Clear);
    com_bind(&device_class, "SetRenderState", SetRenderState);
    com_bind(&device_class, "GetRenderState", GetRenderState);
    com_bind(&device_class, "SetTexture", SetTexture);
    com_bind(&device_class, "SetTextureStageState", SetTextureStageState);
    com_bind(&device_class, "SetSamplerState", SetSamplerState);
    com_bind(&device_class, "SetFVF", SetFVF);
    com_bind(&device_class, "DrawPrimitiveUP", DrawPrimitiveUP);
    com_bind(&swapchain_class, "Present", Present);
    com_bind(&texture_class, "Release", Texture_Release);
    com_bind(&texture_class, "GetSurfaceLevel", GetSurfaceLevel);
    com_bind(&texture_class, "GetLevelDesc", Texture_GetLevelDesc);
    com_bind(&texture_class, "LockRect", Texture_LockRect);
    com_bind(&texture_class, "UnlockRect", Texture_UnlockRect);
    com_bind(&surface_class, "GetDesc", Surface_GetDesc);
    com_bind(&surface_class, "Release", Surface_Release);
    com_bind(&effect_class, "Begin", Effect_Begin);
    const char *effect_ok[] = {"SetFloat", "SetVector", "SetInt", "SetBool", "SetTexture", "SetMatrix",
                               "BeginPass", "CommitChanges", "EndPass", "End", "OnLostDevice",
                               "OnResetDevice", "SetTechnique"};
    for (unsigned i = 0; i < sizeof effect_ok / sizeof *effect_ok; i++)
        com_bind_ok(&effect_class, effect_ok[i]);
}

void d3d9_init(void) {
    static int done;
    if (!done) {
        done = 1;
        bind_all();
    }
}

void d3d9_set_frame_limit(unsigned long long frames) { frame_limit = frames; }

#define E(name) {#name, name}
const ApiEntry win32_d3d9[] = {
    E(Direct3DCreate9), E(D3DXCreateTexture), E(D3DXCreateEffect), E(D3DXVec2Normalize), E(D3DXVec2Hermite),
    {NULL, NULL},
};
