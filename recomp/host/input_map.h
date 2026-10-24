#ifndef T123_INPUT_MAP_H
#define T123_INPUT_MAP_H
#include <stdint.h>
/* SDL2 scancode fisico, no SDL_Keycode ni caracter dependiente del layout. */
uint8_t dik_from_sdl_scancode(int scancode);
/* Sobrescribe exactamente 256 bytes: 0x80 pulsado, cero liberado. */
void dik_state_from_vita_buttons(uint32_t buttons,uint8_t state[256]);
#endif
