/* Fast DXT5 (BC3) encoder for texture uploads: 1 byte per pixel on the GPU instead of
 * 4 (RGBA8) or 2 (RGBA4444). A fight's ~52 MiB of 32-bit textures no longer fit the
 * Vita's GPU budget and were evicted and re-uploaded constantly (v22: 1800 evictions).
 *
 * Bounding-box endpoints with a small inset and projection onto the endpoint line
 * (the "real-time DXT" method): far from optimal, but it runs per upload on the A9. */
#include "dxt.h"

#include <string.h>

/* No integer division anywhere per pixel: the Vita's Cortex-A9 has no divide
   instruction, and v23's divisions made encoding cost ~30 ms per texture. */
static inline uint16_t to565(int r, int g, int b) {
    return (uint16_t)((r >> 3) << 11 | (g >> 2) << 5 | (b >> 3));
}
static inline void from565(uint16_t c, int *r, int *g, int *b) {
    int r5 = c >> 11, g6 = (c >> 5) & 63, b5 = c & 31;
    *r = (r5 << 3) | (r5 >> 2); *g = (g6 << 2) | (g6 >> 4); *b = (b5 << 3) | (b5 >> 2);
}

/* px: 16 pixels as R,G,B,A */
static void encode_block(const uint8_t px[64], uint8_t out[16]) {
    int mn[4] = {255, 255, 255, 255}, mx[4] = {0, 0, 0, 0};
    for (int i = 0; i < 16; i++)
        for (int k = 0; k < 4; k++) {
            int v = px[i * 4 + k];
            if (v < mn[k]) mn[k] = v;
            if (v > mx[k]) mx[k] = v;
        }
    /* alpha: 8-value mode, a0 > a1 */
    int a0 = mx[3], a1 = mn[3];
    out[0] = (uint8_t)a0; out[1] = (uint8_t)a1;
    uint64_t abits = 0;
    if (a0 > a1) {
        float scale = 7.0f / (float)(a0 - a1);
        for (int i = 0; i < 16; i++) {
            int t = (int)((float)(px[i * 4 + 3] - a1) * scale + 0.5f); /* 0..7, weight of a0 */
            int idx = t == 7 ? 0 : t == 0 ? 1 : 8 - t;
            abits |= (uint64_t)idx << (3 * i);
        }
    }
    for (int k = 0; k < 6; k++) out[2 + k] = (uint8_t)(abits >> (8 * k));

    /* colour: inset bounding box */
    for (int k = 0; k < 3; k++) {
        int inset = (mx[k] - mn[k]) >> 4; /* shift, not a divide */
        mx[k] -= inset; mn[k] += inset;
    }
    uint16_t c0 = to565(mx[0], mx[1], mx[2]), c1 = to565(mn[0], mn[1], mn[2]);
    uint32_t cbits = 0;
    if (c0 < c1) { uint16_t s = c0; c0 = c1; c1 = s; }
    if (c0 != c1) {
        int r0, g0, b0, r1, g1, b1;
        from565(c0, &r0, &g0, &b0);
        from565(c1, &r1, &g1, &b1);
        int dr = r0 - r1, dg = g0 - g1, db = b0 - b1;
        int len = dr * dr + dg * dg + db * db;
        if (len) {
            float scale = 3.0f / (float)len;
            for (int i = 0; i < 16; i++) {
                int d = (px[i * 4] - r1) * dr + (px[i * 4 + 1] - g1) * dg + (px[i * 4 + 2] - b1) * db;
                int t = (int)((float)d * scale + 0.5f + 8.0f) - 8; /* 0..3, weight of c0 (floor of negatives) */
                if (t < 0) t = 0;
                if (t > 3) t = 3;
                static const uint8_t map[4] = {1, 3, 2, 0};
                cbits |= (uint32_t)map[t] << (2 * i);
            }
        }
    }
    out[8] = (uint8_t)c0; out[9] = (uint8_t)(c0 >> 8);
    out[10] = (uint8_t)c1; out[11] = (uint8_t)(c1 >> 8);
    out[12] = (uint8_t)cbits; out[13] = (uint8_t)(cbits >> 8);
    out[14] = (uint8_t)(cbits >> 16); out[15] = (uint8_t)(cbits >> 24);
}

void dxt5_encode_rows(const uint8_t *bgra, uint32_t pitch, uint32_t width, uint32_t rows, int opaque, uint8_t *out) {
    uint8_t px[64];
    for (uint32_t by = 0; by + 4 <= rows; by += 4)
        for (uint32_t bx = 0; bx + 4 <= width; bx += 4) {
            for (int y = 0; y < 4; y++) {
                const uint8_t *s = bgra + (size_t)(by + y) * pitch + (size_t)bx * 4;
                for (int x = 0; x < 4; x++, s += 4) {
                    uint8_t *p = px + (y * 4 + x) * 4;
                    p[0] = s[2]; p[1] = s[1]; p[2] = s[0]; p[3] = opaque ? 255 : s[3];
                }
            }
            encode_block(px, out);
            out += 16;
        }
}
