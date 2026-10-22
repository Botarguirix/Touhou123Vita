/* USER32, GDI32, WINMM, OLE32, IMM32, WS2_32 and D3D9 for the bring-up (F2.0).
 *
 * No window or graphics exist yet: windows are handles, messages never arrive and
 * Direct3DCreate9 fails on purpose, so the run shows how far the game gets before it
 * needs graphics. MessageBoxA texts are written to the trace. */
#include "win32.h"

#include <stdio.h>
#include <string.h>
#include <time.h>

#define API(name) static void name(Cpu *c)

/* -- WINMM -------------------------------------------------------------------------- */
API(timeBeginPeriod) { ret_stdcall(c, 0, 1); }
API(timeGetTime) { ret_stdcall(c, (uint32_t)((uint64_t)clock() * 1000u / CLOCKS_PER_SEC), 0); }

/* -- USER32 ------------------------------------------------------------------------- */
enum { FAKE_HWND = 0x00010010u, FAKE_HDC = 0x00020020u, FAKE_HICON = 0x00030030u };
static uint32_t window_proc;

API(RegisterClassExA) {
    uint32_t wc = ARG(c, 0);
    window_proc = rd32(wc + 8);
    trace("RegisterClassExA(%s, wndproc=%08x)", rd32(wc + 40) >= 0x10000 ? STR(rd32(wc + 40)) : "#atom",
          window_proc);
    ret_stdcall(c, 0xC001, 1);
}
API(CreateWindowExA) {
    trace("CreateWindowExA(class=%s, title=%s, style=%08x, %dx%d)",
          ARG(c, 1) >= 0x10000 ? STR(ARG(c, 1)) : "#atom", ARG(c, 2) ? STR(ARG(c, 2)) : "",
          ARG(c, 3), (int)ARG(c, 6), (int)ARG(c, 7));
    ret_stdcall(c, FAKE_HWND, 12);
}
API(ShowWindow) { ret_stdcall(c, 0, 2); }
API(UpdateWindow) { ret_stdcall(c, 1, 1); }
API(SetWindowPos) { ret_stdcall(c, 1, 7); }
API(SetWindowTextA) { ret_stdcall(c, 1, 2); }
API(GetWindowRect) {
    uint32_t r = ARG(c, 1);
    wr32(r, 0); wr32(r + 4, 0); wr32(r + 8, 640); wr32(r + 12, 480);
    ret_stdcall(c, 1, 2);
}
API(GetWindowLongA) { ret_stdcall(c, 0, 2); }
API(GetWindowInfo) {
    uint32_t p = ARG(c, 1);
    memset(G(p + 4), 0, 56);
    wr32(p + 4 + 8, 640); wr32(p + 4 + 12, 480);   /* rcWindow */
    wr32(p + 20 + 8, 640); wr32(p + 20 + 12, 480); /* rcClient */
    ret_stdcall(c, 1, 2);
}
API(SetRect) {
    uint32_t r = ARG(c, 0);
    wr32(r, ARG(c, 1)); wr32(r + 4, ARG(c, 2)); wr32(r + 8, ARG(c, 3)); wr32(r + 12, ARG(c, 4));
    ret_stdcall(c, 1, 5);
}
API(GetSystemMetrics) {
    uint32_t i = ARG(c, 0);
    ret_stdcall(c, i == 0 ? 960 : i == 1 ? 544 : 0, 1); /* screen: the Vita's 960x544 */
}
API(LoadCursorA) { ret_stdcall(c, FAKE_HICON, 2); }
API(LoadIconA) { ret_stdcall(c, FAKE_HICON, 2); }
API(LoadImageA) { ret_stdcall(c, FAKE_HICON, 6); }
API(LoadStringA) {
    if (ARG(c, 3)) wr8(ARG(c, 2), 0);
    ret_stdcall(c, 0, 4);
}
API(MessageBoxA) {
    trace("MessageBoxA(title=\"%s\"): %s", ARG(c, 2) ? STR(ARG(c, 2)) : "",
          ARG(c, 1) ? STR(ARG(c, 1)) : "");
    ret_stdcall(c, 1 /* IDOK */, 4);
}
API(PeekMessageA) { ret_stdcall(c, 0, 5); }
API(GetMessageA) { host_exit(c, 0, "GetMessageA: message loop reached (no window system yet)"); }
API(DispatchMessageA) { ret_stdcall(c, 0, 1); }
API(TranslateMessage) { ret_stdcall(c, 0, 1); }
API(DefWindowProcA) { ret_stdcall(c, 0, 4); }
API(PostQuitMessage) { ret_stdcall(c, 0, 1); }
API(SendMessageA) { ret_stdcall(c, 0, 4); }
API(ShowCursor) { ret_stdcall(c, 0, 1); }
API(GetDC) { ret_stdcall(c, FAKE_HDC, 1); }
API(ReleaseDC) { ret_stdcall(c, 1, 2); }
API(OpenClipboard) { ret_stdcall(c, 0, 1); }
API(CloseClipboard) { ret_stdcall(c, 1, 0); }
API(GetClipboardData) { ret_stdcall(c, 0, 1); }
API(ToAscii) { ret_stdcall(c, 0, 5); }

/* wsprintfA(buffer, format, ...): cdecl with guest varargs. Supports the conversions
   wsprintf has (%d %i %u %x %X %c %s %%, flags '-' '0' '#', width, 'l'/'h'). */
API(wsprintfA) {
    uint32_t out = ARG(c, 0);
    const char *f = STR(ARG(c, 1));
    unsigned arg = 2;
    char buf[1025];
    size_t n = 0;
    while (*f && n < 1024) {
        if (*f != '%') { buf[n++] = *f++; continue; }
        char spec[16] = "%";
        size_t k = 1;
        f++;
        while (*f && strchr("-0#", *f) && k < 6) spec[k++] = *f++;
        while (*f >= '0' && *f <= '9' && k < 10) spec[k++] = *f++;
        while (*f == 'l' || *f == 'h') f++;
        char conv = *f ? *f++ : 0;
        char piece[512];
        if (conv == 's') {
            uint32_t s = ARG(c, arg++);
            spec[k++] = 's'; spec[k] = 0;
            snprintf(piece, sizeof piece, spec, s ? STR(s) : "(null)");
        } else if (conv == 'c') {
            spec[k++] = 'c'; spec[k] = 0;
            snprintf(piece, sizeof piece, spec, (int)(uint8_t)ARG(c, arg++));
        } else if (conv == 'd' || conv == 'i') {
            spec[k++] = 'd'; spec[k] = 0;
            snprintf(piece, sizeof piece, spec, (int32_t)ARG(c, arg++));
        } else if (conv == 'u' || conv == 'x' || conv == 'X') {
            spec[k++] = conv; spec[k] = 0;
            snprintf(piece, sizeof piece, spec, ARG(c, arg++));
        } else {
            snprintf(piece, sizeof piece, "%c", conv ? conv : '%');
        }
        for (const char *p = piece; *p && n < 1024; p++) buf[n++] = *p;
    }
    buf[n] = 0;
    memcpy(G(out), buf, n + 1);
    ret_cdecl(c, (uint32_t)n);
}

/* -- GDI32 ---------------------------------------------------------------------------- */
API(CreateFontA) {
    trace("CreateFontA(height=%d, weight=%d, charset=%u, face=%s)", (int)ARG(c, 0), (int)ARG(c, 4),
          ARG(c, 8), ARG(c, 13) ? STR(ARG(c, 13)) : "");
    ret_stdcall(c, 0x00040040u, 14);
}
API(SelectObject) { ret_stdcall(c, 0x00040040u, 2); }
API(DeleteObject) { ret_stdcall(c, 1, 1); }
API(GetStockObject) { ret_stdcall(c, 0x00040050u, 1); }
API(GetTextMetricsA) {
    memset(G(ARG(c, 1)), 0, 53);
    ret_stdcall(c, 1, 2);
}
API(GetGlyphOutlineA) {
    trace("GetGlyphOutlineA(char=%04x, format=%u): glyph rasteriser pending (T5)", ARG(c, 1), ARG(c, 2));
    ret_stdcall(c, 0xFFFFFFFFu /* GDI_ERROR */, 7);
}

/* -- IMM32 ----------------------------------------------------------------------------- */
API(ImmGetContext) { ret_stdcall(c, 0, 1); }
API(ImmReleaseContext) { ret_stdcall(c, 1, 2); }
API(ImmGetCompositionStringA) { ret_stdcall(c, 0, 4); }
API(ImmSetCandidateWindow) { ret_stdcall(c, 1, 2); }

/* -- OLE32: COM objects (DirectSound8, DirectInput8) are not provided yet ---------- */
API(CoInitialize) { ret_stdcall(c, 0, 1); }
API(CoUninitialize) { ret_stdcall(c, 0, 0); }
API(CoCreateInstance) {
    uint32_t clsid = ARG(c, 0);
    trace("CoCreateInstance(clsid=%08x-%04x-%04x): not available yet", rd32(clsid), rd16(clsid + 4),
          rd16(clsid + 6));
    if (ARG(c, 4))
        wr32(ARG(c, 4), 0);
    ret_stdcall(c, 0x80040154u /* REGDB_E_CLASSNOTREG */, 5);
}

/* -- WS2_32: networking stays off --------------------------------------------------------- */
API(WSAStartup) {
    memset(G(ARG(c, 1)), 0, 400);
    wr16(ARG(c, 1), 0x0202);
    ret_stdcall(c, 0, 2);
}
API(WSACleanup) { ret_stdcall(c, 0, 0); }

/* -- D3D9: fails on purpose until the graphics layer exists (F2.2) ----------------- */
API(Direct3DCreate9) {
    trace("Direct3DCreate9(SDK %u): returning NULL, graphics layer pending (F2.2)", ARG(c, 0));
    ret_stdcall(c, 0, 1);
}

/* -- IMAGEHLP ---------------------------------------------------------------------------- */
API(MakeSureDirectoryPathExists) {
    trace("MakeSureDirectoryPathExists(%s)", STR(ARG(c, 0)));
    ret_stdcall(c, 1, 1);
}

#define E(name) {#name, name}
const ApiEntry win32_other[] = {
    E(timeBeginPeriod), E(timeGetTime),
    E(RegisterClassExA), E(CreateWindowExA), E(ShowWindow), E(UpdateWindow), E(SetWindowPos),
    E(SetWindowTextA), E(GetWindowRect), E(GetWindowLongA), E(GetWindowInfo), E(SetRect),
    E(GetSystemMetrics), E(LoadCursorA), E(LoadIconA), E(LoadImageA), E(LoadStringA), E(MessageBoxA),
    E(PeekMessageA), E(GetMessageA), E(DispatchMessageA), E(TranslateMessage), E(DefWindowProcA),
    E(PostQuitMessage), E(SendMessageA), E(ShowCursor), E(GetDC), E(ReleaseDC), E(OpenClipboard),
    E(CloseClipboard), E(GetClipboardData), E(ToAscii), E(wsprintfA),
    E(CreateFontA), E(SelectObject), E(DeleteObject), E(GetStockObject), E(GetTextMetricsA),
    E(GetGlyphOutlineA),
    E(ImmGetContext), E(ImmReleaseContext), E(ImmGetCompositionStringA), E(ImmSetCandidateWindow),
    E(CoInitialize), E(CoUninitialize), E(CoCreateInstance),
    E(WSAStartup), E(WSACleanup),
    E(Direct3DCreate9), E(MakeSureDirectoryPathExists),
    {NULL, NULL},
};
