#ifndef T123_DXT_H
#define T123_DXT_H
#include <stdint.h>
/* rows of BGRA pixels (A8R8G8B8 in memory) -> DXT5 blocks, row of blocks after row of
   blocks; width and rows multiples of 4; 16 bytes per 4x4 block. opaque: alpha = 255. */
void dxt5_encode_rows(const uint8_t *bgra, uint32_t pitch, uint32_t width, uint32_t rows, int opaque, uint8_t *out);
#endif
