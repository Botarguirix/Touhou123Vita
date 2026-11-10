/* The Vita keyboard for the game's text fields (profile name, IP address, ...).
 *
 * th123.exe edits text through window messages (see docs/TECLADO_Y_ADHOC.md): a global
 * byte at 0x8a0cff says a text field is active, the text lives in a Shift-JIS buffer at
 * 0x8a02f8 (cursor 0x8a0d00, maximum length 0x8a0cf8), and 0x40f000 handles WM_KEYDOWN,
 * WM_CHAR and WM_IME_ENDCOMPOSITION. When that byte rises, this opens the system
 * on-screen keyboard (sceImeDialog) with the field's current text. On OK the old text is
 * deleted with Backspace messages, the new text is handed to the game as the result of an
 * IME composition (other.c answers ImmGetCompositionStringA with it) and Enter closes the
 * field; on Cancel the game receives Escape.
 *
 * ime_poll runs once per presented frame on the thread that presents; the messages are
 * queued and processed by the game's own message loop. */
#include <psp2/common_dialog.h>
#include <psp2/ime_dialog.h>
#include <stdio.h>
#include <string.h>

#include "../host/net.h"
#include "../host/sjis.h"
#include "../host/win32.h"

enum {
    FIELD_ACTIVE = 0x8a0cffu, TEXT_BUFFER = 0x8a02f8u, TEXT_MAX = 0x8a0cf8u,
    TEXT_CHANGED = 0x8a0cfdu, TEXT_COMPOSING = 0x8a0cfeu,
    WM_KEYDOWN = 0x100, WM_CHAR = 0x102, WM_IME_ENDCOMPOSITION = 0x10e,
    VK_BACK = 0x08, VK_RETURN = 0x0d, VK_RIGHT = 0x27, VK_ESCAPE = 0x1b
};

static int enter_pending;
static unsigned enter_frames;
static int dialog_open;
static int armed = 1;   /* a field must close (the byte drops) before the keyboard opens again */
static SceWChar16 title[32], initial[SCE_IME_DIALOG_MAX_TEXT_LENGTH + 1], input[SCE_IME_DIALOG_MAX_TEXT_LENGTH + 1];

int ime_dialog_active(void) { return dialog_open; }

static void open_dialog(void) {
    armed = 0;
    const uint8_t *text = G(TEXT_BUFFER);
    unsigned used = 0;
    while (used < 0x3ff && text[used]) used++;
    uint8_t current[0x400];
    memcpy(current, text, used);
    current[used] = 0;
    memset(initial, 0, sizeof initial);
    if (used) sjis_to_utf16(current, -1, initial, SCE_IME_DIALOG_MAX_TEXT_LENGTH);
    memset(input, 0, sizeof input);
    /* in Wi-Fi mode the title also tells this Vita's address, to type it on the other one */
    char label[64];
    const char *ip = net_enabled() ? net_own_ip() : "";
    snprintf(label, sizeof label, *ip ? "Text - this Vita: %s" : "Texto / Text", ip);
    memset(title, 0, sizeof title);
    for (unsigned i = 0; label[i] && i < 31; i++) title[i] = (SceWChar16)(unsigned char)label[i];
    uint32_t max_bytes = rd32(TEXT_MAX);
    if (max_bytes < 1 || max_bytes > 255) max_bytes = 255;

    /* With every language of the system the keyboard opened in the Japanese kana layout, where
       the digits are mixed in among the kana keys and an IP address could not be typed. It now
       opens in English (QWERTY, digit row, "."), or as a numeric pad when the field already
       holds something that looks like an address. ime-ja.txt in the data directory brings the
       system languages back (for typing a Japanese name). */
    int looks_numeric = used > 0;
    for (unsigned i = 0; i < used; i++) {
        char ch = (char)current[i];
        if (!((ch >= '0' && ch <= '9') || ch == '.' || ch == ':')) looks_numeric = 0;
    }
    FILE *ja = fopen("ux0:data/touhou123vita/ime-ja.txt", "rb");
    if (ja) fclose(ja);

    SceImeDialogParam p;
    sceImeDialogParamInit(&p);
    if (ja) {
        p.supportedLanguages = 0x000FFFFFull; /* every language the system keyboard has */
        p.languagesForced = SCE_FALSE;
        p.type = 0;                            /* SCE_IME_TYPE_DEFAULT */
    } else {
        p.supportedLanguages = 0x4ull;         /* SCE_IME_LANGUAGE_ENGLISH */
        p.languagesForced = SCE_TRUE;
        p.type = looks_numeric ? 3 /* SCE_IME_TYPE_EXTENDED_NUMBER */ : 1 /* SCE_IME_TYPE_BASIC_LATIN */;
    }
    p.dialogMode = SCE_IME_DIALOG_DIALOG_MODE_WITH_CANCEL;
    p.textBoxMode = SCE_IME_DIALOG_TEXTBOX_MODE_WITH_CLEAR;
    p.title = title;
    p.maxTextLength = max_bytes;
    p.initialText = initial;
    p.inputTextBuffer = input;
    int r = sceImeDialogInit(&p);
    if (r < 0) {
        trace("# keyboard: sceImeDialogInit failed (%08x)", (unsigned)r);
        return;
    }
    dialog_open = 1;
    trace("# keyboard: text field active (frame %llu), %u bytes now, at most %u: dialog open", d3d_frames, used, max_bytes);
}

static void post_key(uint32_t vk) { host_post_message(WM_KEYDOWN, vk, 0); }

static void close_dialog(void) {
    SceImeDialogResult res;
    memset(&res, 0, sizeof res);
    sceImeDialogGetResult(&res);
    sceImeDialogTerm();
    dialog_open = 0;
    if (res.button != SCE_IME_DIALOG_BUTTON_ENTER) {
        trace("# keyboard: cancelled (button %d): sending Escape", res.button);
        host_post_message(WM_CHAR, VK_ESCAPE, 0);
        return;
    }
    uint8_t sjis[0x400];
    int defaulted = 0;
    int n = utf16_to_sjis(input, -1, sjis, sizeof sjis, &defaulted);
    if (n > 0 && sjis[n - 1] == 0) n--; /* without the terminator */
    if (n < 0) n = 0;
    /* delete what the field holds (the game's cursor is at its end after VK_END), then
       insert the new text as an IME result and press Enter */
    unsigned old_len = 0;
    const uint8_t *text = G(TEXT_BUFFER);
    while (old_len < 0x3ff && text[old_len]) old_len++;
    if (old_len > 200) old_len = 200;
    /* the field only has Left, Right, Backspace and Delete (0x40f000): Right n times puts
       the cursor at the end, Backspace n times empties it */
    for (unsigned i = 0; i < old_len; i++) post_key(VK_RIGHT);
    for (unsigned i = 0; i < old_len; i++) post_key(VK_BACK);
    host_ime_set_result(sjis, (size_t)n);
    host_post_message(WM_IME_ENDCOMPOSITION, 0, 0);
    /* Enter (0x40efb0) is ignored while the "text changed" and "composing" flags are set,
       and the game clears them a little later: it is sent when they are clear */
    enter_pending = 1;
    enter_frames = 0;
    trace("# keyboard: typing %d bytes for the game (replacing %u), Enter follows when the field settles%s", n, old_len,
          defaulted ? " [some characters have no Shift-JIS form]" : "");
}

static void pump_enter(void) {
    if (!enter_pending) return;
    enter_frames++;
    int settled = !*G(TEXT_CHANGED) && !*G(TEXT_COMPOSING);
    if ((enter_frames >= 6 && settled) || enter_frames > 240) {
        post_key(VK_RETURN);
        enter_pending = 0;
        trace("# keyboard: Enter sent after %u frames (changed %u, composing %u)", enter_frames, *G(TEXT_CHANGED), *G(TEXT_COMPOSING));
    }
}

void ime_poll(void) {
    pump_enter();
    if (dialog_open) {
        if (sceImeDialogGetStatus() == SCE_COMMON_DIALOG_STATUS_FINISHED)
            close_dialog();
        return;
    }
    if (!*G(FIELD_ACTIVE)) {
        armed = 1;
        return;
    }
    if (armed)
        open_dialog();
}
