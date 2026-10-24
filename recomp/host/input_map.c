/* Mapeo propio de valores publicos SDL2 (USB HID) y DIK (DirectInput).
 * Ver docs/INPUT_MAP.md: todos los indices sin equivalente quedan a cero.
 * No incluye SDL, DirectX ni las cabeceras de VitaSDK. */
#include "input_map.h"
#include <string.h>
static const uint8_t scancode_to_dik[512] = {
    [4] = 0x1e, /* SDL_SCANCODE_A -> DIK_A */
    [5] = 0x30, /* SDL_SCANCODE_B -> DIK_B */
    [6] = 0x2e, /* SDL_SCANCODE_C -> DIK_C */
    [7] = 0x20, /* SDL_SCANCODE_D -> DIK_D */
    [8] = 0x12, /* SDL_SCANCODE_E -> DIK_E */
    [9] = 0x21, /* SDL_SCANCODE_F -> DIK_F */
    [10] = 0x22, /* SDL_SCANCODE_G -> DIK_G */
    [11] = 0x23, /* SDL_SCANCODE_H -> DIK_H */
    [12] = 0x17, /* SDL_SCANCODE_I -> DIK_I */
    [13] = 0x24, /* SDL_SCANCODE_J -> DIK_J */
    [14] = 0x25, /* SDL_SCANCODE_K -> DIK_K */
    [15] = 0x26, /* SDL_SCANCODE_L -> DIK_L */
    [16] = 0x32, /* SDL_SCANCODE_M -> DIK_M */
    [17] = 0x31, /* SDL_SCANCODE_N -> DIK_N */
    [18] = 0x18, /* SDL_SCANCODE_O -> DIK_O */
    [19] = 0x19, /* SDL_SCANCODE_P -> DIK_P */
    [20] = 0x10, /* SDL_SCANCODE_Q -> DIK_Q */
    [21] = 0x13, /* SDL_SCANCODE_R -> DIK_R */
    [22] = 0x1f, /* SDL_SCANCODE_S -> DIK_S */
    [23] = 0x14, /* SDL_SCANCODE_T -> DIK_T */
    [24] = 0x16, /* SDL_SCANCODE_U -> DIK_U */
    [25] = 0x2f, /* SDL_SCANCODE_V -> DIK_V */
    [26] = 0x11, /* SDL_SCANCODE_W -> DIK_W */
    [27] = 0x2d, /* SDL_SCANCODE_X -> DIK_X */
    [28] = 0x15, /* SDL_SCANCODE_Y -> DIK_Y */
    [29] = 0x2c, /* SDL_SCANCODE_Z -> DIK_Z */
    [30] = 0x02, /* SDL_SCANCODE_1 -> DIK_1 */
    [31] = 0x03, /* SDL_SCANCODE_2 -> DIK_2 */
    [32] = 0x04, /* SDL_SCANCODE_3 -> DIK_3 */
    [33] = 0x05, /* SDL_SCANCODE_4 -> DIK_4 */
    [34] = 0x06, /* SDL_SCANCODE_5 -> DIK_5 */
    [35] = 0x07, /* SDL_SCANCODE_6 -> DIK_6 */
    [36] = 0x08, /* SDL_SCANCODE_7 -> DIK_7 */
    [37] = 0x09, /* SDL_SCANCODE_8 -> DIK_8 */
    [38] = 0x0a, /* SDL_SCANCODE_9 -> DIK_9 */
    [39] = 0x0b, /* SDL_SCANCODE_0 -> DIK_0 */
    [40] = 0x1c, /* SDL_SCANCODE_RETURN -> DIK_RETURN */
    [41] = 0x01, /* SDL_SCANCODE_ESCAPE -> DIK_ESCAPE */
    [42] = 0x0e, /* SDL_SCANCODE_BACKSPACE -> DIK_BACK */
    [43] = 0x0f, /* SDL_SCANCODE_TAB -> DIK_TAB */
    [44] = 0x39, /* SDL_SCANCODE_SPACE -> DIK_SPACE */
    [45] = 0x0c, /* SDL_SCANCODE_MINUS -> DIK_MINUS */
    [46] = 0x0d, /* SDL_SCANCODE_EQUALS -> DIK_EQUALS */
    [47] = 0x1a, /* SDL_SCANCODE_LEFTBRACKET -> DIK_LBRACKET */
    [48] = 0x1b, /* SDL_SCANCODE_RIGHTBRACKET -> DIK_RBRACKET */
    [49] = 0x2b, /* SDL_SCANCODE_BACKSLASH -> DIK_BACKSLASH */
    [50] = 0x2b, /* SDL_SCANCODE_NONUSHASH -> DIK_BACKSLASH */
    [51] = 0x27, /* SDL_SCANCODE_SEMICOLON -> DIK_SEMICOLON */
    [52] = 0x28, /* SDL_SCANCODE_APOSTROPHE -> DIK_APOSTROPHE */
    [53] = 0x29, /* SDL_SCANCODE_GRAVE -> DIK_GRAVE */
    [54] = 0x33, /* SDL_SCANCODE_COMMA -> DIK_COMMA */
    [55] = 0x34, /* SDL_SCANCODE_PERIOD -> DIK_PERIOD */
    [56] = 0x35, /* SDL_SCANCODE_SLASH -> DIK_SLASH */
    [57] = 0x3a, /* SDL_SCANCODE_CAPSLOCK -> DIK_CAPITAL */
    [58] = 0x3b, /* SDL_SCANCODE_F1 -> DIK_F1 */
    [59] = 0x3c, /* SDL_SCANCODE_F2 -> DIK_F2 */
    [60] = 0x3d, /* SDL_SCANCODE_F3 -> DIK_F3 */
    [61] = 0x3e, /* SDL_SCANCODE_F4 -> DIK_F4 */
    [62] = 0x3f, /* SDL_SCANCODE_F5 -> DIK_F5 */
    [63] = 0x40, /* SDL_SCANCODE_F6 -> DIK_F6 */
    [64] = 0x41, /* SDL_SCANCODE_F7 -> DIK_F7 */
    [65] = 0x42, /* SDL_SCANCODE_F8 -> DIK_F8 */
    [66] = 0x43, /* SDL_SCANCODE_F9 -> DIK_F9 */
    [67] = 0x44, /* SDL_SCANCODE_F10 -> DIK_F10 */
    [68] = 0x57, /* SDL_SCANCODE_F11 -> DIK_F11 */
    [69] = 0x58, /* SDL_SCANCODE_F12 -> DIK_F12 */
    [70] = 0xb7, /* SDL_SCANCODE_PRINTSCREEN -> DIK_SYSRQ */
    [71] = 0x46, /* SDL_SCANCODE_SCROLLLOCK -> DIK_SCROLL */
    [72] = 0xc5, /* SDL_SCANCODE_PAUSE -> DIK_PAUSE */
    [73] = 0xd2, /* SDL_SCANCODE_INSERT -> DIK_INSERT */
    [74] = 0xc7, /* SDL_SCANCODE_HOME -> DIK_HOME */
    [75] = 0xc9, /* SDL_SCANCODE_PAGEUP -> DIK_PRIOR */
    [76] = 0xd3, /* SDL_SCANCODE_DELETE -> DIK_DELETE */
    [77] = 0xcf, /* SDL_SCANCODE_END -> DIK_END */
    [78] = 0xd1, /* SDL_SCANCODE_PAGEDOWN -> DIK_NEXT */
    [79] = 0xcd, /* SDL_SCANCODE_RIGHT -> DIK_RIGHT */
    [80] = 0xcb, /* SDL_SCANCODE_LEFT -> DIK_LEFT */
    [81] = 0xd0, /* SDL_SCANCODE_DOWN -> DIK_DOWN */
    [82] = 0xc8, /* SDL_SCANCODE_UP -> DIK_UP */
    [83] = 0x45, /* SDL_SCANCODE_NUMLOCKCLEAR -> DIK_NUMLOCK */
    [84] = 0xb5, /* SDL_SCANCODE_KP_DIVIDE -> DIK_DIVIDE */
    [85] = 0x37, /* SDL_SCANCODE_KP_MULTIPLY -> DIK_MULTIPLY */
    [86] = 0x4a, /* SDL_SCANCODE_KP_MINUS -> DIK_SUBTRACT */
    [87] = 0x4e, /* SDL_SCANCODE_KP_PLUS -> DIK_ADD */
    [88] = 0x9c, /* SDL_SCANCODE_KP_ENTER -> DIK_NUMPADENTER */
    [89] = 0x4f, /* SDL_SCANCODE_KP_1 -> DIK_NUMPAD1 */
    [90] = 0x50, /* SDL_SCANCODE_KP_2 -> DIK_NUMPAD2 */
    [91] = 0x51, /* SDL_SCANCODE_KP_3 -> DIK_NUMPAD3 */
    [92] = 0x4b, /* SDL_SCANCODE_KP_4 -> DIK_NUMPAD4 */
    [93] = 0x4c, /* SDL_SCANCODE_KP_5 -> DIK_NUMPAD5 */
    [94] = 0x4d, /* SDL_SCANCODE_KP_6 -> DIK_NUMPAD6 */
    [95] = 0x47, /* SDL_SCANCODE_KP_7 -> DIK_NUMPAD7 */
    [96] = 0x48, /* SDL_SCANCODE_KP_8 -> DIK_NUMPAD8 */
    [97] = 0x49, /* SDL_SCANCODE_KP_9 -> DIK_NUMPAD9 */
    [98] = 0x52, /* SDL_SCANCODE_KP_0 -> DIK_NUMPAD0 */
    [99] = 0x53, /* SDL_SCANCODE_KP_PERIOD -> DIK_DECIMAL */
    [100] = 0x56, /* SDL_SCANCODE_NONUSBACKSLASH -> DIK_OEM_102 */
    [101] = 0xdd, /* SDL_SCANCODE_APPLICATION -> DIK_APPS */
    [102] = 0xde, /* SDL_SCANCODE_POWER -> DIK_POWER */
    [103] = 0x8d, /* SDL_SCANCODE_KP_EQUALS -> DIK_NUMPADEQUALS */
    [104] = 0x64, /* SDL_SCANCODE_F13 -> DIK_F13 */
    [105] = 0x65, /* SDL_SCANCODE_F14 -> DIK_F14 */
    [106] = 0x66, /* SDL_SCANCODE_F15 -> DIK_F15 */
    [127] = 0xa0, /* SDL_SCANCODE_MUTE -> DIK_MUTE */
    [128] = 0xb0, /* SDL_SCANCODE_VOLUMEUP -> DIK_VOLUMEUP */
    [129] = 0xae, /* SDL_SCANCODE_VOLUMEDOWN -> DIK_VOLUMEDOWN */
    [133] = 0xb3, /* SDL_SCANCODE_KP_COMMA -> DIK_NUMPADCOMMA */
    [134] = 0x8d, /* SDL_SCANCODE_KP_EQUALSAS400 -> DIK_NUMPADEQUALS */
    [135] = 0x73, /* SDL_SCANCODE_INTERNATIONAL1 -> DIK_ABNT_C1 */
    [136] = 0x70, /* SDL_SCANCODE_INTERNATIONAL2 -> DIK_KANA */
    [137] = 0x7d, /* SDL_SCANCODE_INTERNATIONAL3 -> DIK_YEN */
    [138] = 0x79, /* SDL_SCANCODE_INTERNATIONAL4 -> DIK_CONVERT */
    [139] = 0x7b, /* SDL_SCANCODE_INTERNATIONAL5 -> DIK_NOCONVERT */
    [154] = 0xb7, /* SDL_SCANCODE_SYSREQ -> DIK_SYSRQ */
    [157] = 0xc9, /* SDL_SCANCODE_PRIOR -> DIK_PRIOR */
    [224] = 0x1d, /* SDL_SCANCODE_LCTRL -> DIK_LCONTROL */
    [225] = 0x2a, /* SDL_SCANCODE_LSHIFT -> DIK_LSHIFT */
    [226] = 0x38, /* SDL_SCANCODE_LALT -> DIK_LMENU */
    [227] = 0xdb, /* SDL_SCANCODE_LGUI -> DIK_LWIN */
    [228] = 0x9d, /* SDL_SCANCODE_RCTRL -> DIK_RCONTROL */
    [229] = 0x36, /* SDL_SCANCODE_RSHIFT -> DIK_RSHIFT */
    [230] = 0xb8, /* SDL_SCANCODE_RALT -> DIK_RMENU */
    [231] = 0xdc, /* SDL_SCANCODE_RGUI -> DIK_RWIN */
    [258] = 0x99, /* SDL_SCANCODE_AUDIONEXT -> DIK_NEXTTRACK */
    [259] = 0x90, /* SDL_SCANCODE_AUDIOPREV -> DIK_PREVTRACK */
    [260] = 0xa4, /* SDL_SCANCODE_AUDIOSTOP -> DIK_MEDIASTOP */
    [261] = 0xa2, /* SDL_SCANCODE_AUDIOPLAY -> DIK_PLAYPAUSE */
    [262] = 0xa0, /* SDL_SCANCODE_AUDIOMUTE -> DIK_MUTE */
    [263] = 0xed, /* SDL_SCANCODE_MEDIASELECT -> DIK_MEDIASELECT */
    [264] = 0xb2, /* SDL_SCANCODE_WWW -> DIK_WEBHOME */
    [265] = 0xec, /* SDL_SCANCODE_MAIL -> DIK_MAIL */
    [266] = 0xa1, /* SDL_SCANCODE_CALCULATOR -> DIK_CALCULATOR */
    [267] = 0xeb, /* SDL_SCANCODE_COMPUTER -> DIK_MYCOMPUTER */
    [268] = 0xe5, /* SDL_SCANCODE_AC_SEARCH -> DIK_WEBSEARCH */
    [269] = 0xb2, /* SDL_SCANCODE_AC_HOME -> DIK_WEBHOME */
    [270] = 0xea, /* SDL_SCANCODE_AC_BACK -> DIK_WEBBACK */
    [271] = 0xe9, /* SDL_SCANCODE_AC_FORWARD -> DIK_WEBFORWARD */
    [272] = 0xe8, /* SDL_SCANCODE_AC_STOP -> DIK_WEBSTOP */
    [273] = 0xe7, /* SDL_SCANCODE_AC_REFRESH -> DIK_WEBREFRESH */
    [274] = 0xe6, /* SDL_SCANCODE_AC_BOOKMARKS -> DIK_WEBFAVORITES */
    [282] = 0xdf, /* SDL_SCANCODE_SLEEP -> DIK_SLEEP */
};
uint8_t dik_from_sdl_scancode(int scancode) {
    return scancode>=0 && scancode<512 ? scancode_to_dik[scancode]:0;
}
void dik_state_from_vita_buttons(uint32_t buttons,uint8_t state[256]) {
    if (!state) return;
    memset(state,0,256);
    /* Valores SCE_CTRL_* de psp2common/ctrl.h. Perfil Soku: pausa Q. */
    static const struct { uint32_t button;uint8_t dik; } bindings[] = {
        {0x00000010,0xc8}, /* UP */
        {0x00000040,0xd0}, /* DOWN */
        {0x00000080,0xcb}, /* LEFT */
        {0x00000020,0xcd}, /* RIGHT */
        {0x00004000,0x2c}, /* CROSS -> Z, A/melee */
        {0x00002000,0x2d}, /* CIRCLE -> X, B */
        {0x00008000,0x2e}, /* SQUARE -> C */
        {0x00001000,0x1e}, /* TRIANGLE -> A, D/dash */
        {0x00000100,0x1f}, /* LTRIGGER -> S, cambiar carta */
        {0x00000200,0x20}, /* RTRIGGER -> D, usar carta */
        {0x00000008,0x10}, /* START -> Q, pausa del perfil */
    };
    for (unsigned i=0;i<sizeof bindings/sizeof bindings[0];++i)
        if (buttons&bindings[i].button) state[bindings[i].dik]=0x80;
}
