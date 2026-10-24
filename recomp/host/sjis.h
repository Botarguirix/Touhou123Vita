#ifndef T123_SJIS_H
#define T123_SJIS_H
#include <stddef.h>
#include <stdint.h>
/* CP932, flags=0. Longitud negativa incluye el NUL final. Consulta si out==NULL
 * u out_len==0. Devuelve 0 para argumentos invalidos o espacio insuficiente.
 * Bytes invalidos -> U+30FB. UTF-16 no representable -> '?'. Sin estado global. */
int sjis_to_utf16(const uint8_t *in, int in_len, uint16_t *out, int out_len);
int utf16_to_sjis(const uint16_t *in, int in_len, uint8_t *out, int out_len,
                  int *used_default);
#endif
