#ifndef T123_GLYPH_H
#define T123_GLYPH_H
#include <stdint.h>
typedef struct {
    uint32_t black_box_x, black_box_y;
    int32_t origin_x, origin_y;
    int16_t cell_inc_x, cell_inc_y;
} GlyphMetrics;
/* Un rostro global protegido por mutex; init correcto invalida la cache previa.
 * Enlazar FreeType y pthread. La fuente la suministra el host. */
int glyph_init(const char *font_path);
uint32_t glyph_gray4(int height, int weight, uint16_t code, GlyphMetrics *gm,
                     uint8_t *buf, uint32_t size);
#endif
