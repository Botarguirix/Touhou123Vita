/* No FreeType in VitaSDK yet (docs/GLYPHS.md): the Vita build reports no font, so
 * GetGlyphOutlineA fails as it did before T8. Replaced by glyph.c once it links. */
#include "../host/glyph.h"

int glyph_init(const char *font_path) { (void)font_path; return -1; }
uint32_t glyph_gray4(int height, int weight, uint16_t code, GlyphMetrics *gm, uint8_t *buf, uint32_t size) {
    (void)height; (void)weight; (void)code; (void)gm; (void)buf; (void)size;
    return 0xFFFFFFFFu;
}
