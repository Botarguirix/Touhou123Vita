/* English patch (th123e v1.1a, the user's th123e.dat), phase 1: translated resources.
 *
 * The game opens every resource through 0x41C080 (stdcall name, &size, &offset): it
 * looks the name up in the archive index and returns a CreateFileA handle to the DAT,
 * positioned at the entry. Its reader XORs every byte with ((offset >> 1) | 0x23).
 * See docs/TH123E_ANALYSIS.md (T15) for how the original patch DLL serves its ZIP.
 *
 * At start-up th123e.dat (a plain ZIP) is turned into th123e.cache next to it: each
 * entry converted the way the patch DLL does it (PNG -> CV2 32-bit BGRA, cv0/cv1 with
 * the inner text cipher) and then XORed with the key of its own offset in the cache.
 * The intercept answers names found there with a handle to the cache at that offset,
 * opened through the game's own CreateFileA/SetFilePointer imports, so the original
 * reader object works unchanged. Other names go to the original function.
 *
 * Not covered yet (later phases): fonts, the 80 strings inside the EXE, layout tweaks. */
#include "win32.h"

#include <png.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#define IAT_CREATE_FILE_A 0x0085709cu
#define IAT_SET_FILE_POINTER 0x00857094u
#define CACHE_MAGIC "T123E-CACHE-1"

typedef struct { char name[96]; uint32_t offset, size; } Entry;

static Entry *entries;
static unsigned entry_count;
static uint32_t cache_path_guest; /* guest copy of the cache path, for CreateFileA */
static GuestFn factory_original;

static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
static uint32_t le32(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }

/* The patch DLL's lookup key: ".cv2" -> ".png", lower case, '/' (and '\') -> '_'. */
static void normalize(const char *in, char *out, size_t size) {
    size_t n = 0;
    for (; in[n] && n + 1 < size; n++) {
        char ch = in[n];
        if (ch >= 'A' && ch <= 'Z') ch = (char)(ch - 'A' + 'a');
        if (ch == '/' || ch == '\\') ch = '_';
        out[n] = ch;
    }
    out[n] = 0;
    if (n >= 4 && !strcmp(out + n - 4, ".cv2")) memcpy(out + n - 4, ".png", 4);
}

static int entry_cmp(const void *a, const void *b) { return strcmp(((const Entry *)a)->name, ((const Entry *)b)->name); }

static const Entry *lookup(const char *name) {
    Entry key;
    normalize(name, key.name, sizeof key.name);
    return entry_count ? bsearch(&key, entries, entry_count, sizeof *entries, entry_cmp) : NULL;
}

/* -- conversion --------------------------------------------------------------------------- */
typedef struct { const uint8_t *data; size_t size, pos; } PngSource;

static void png_source_read(png_structp png, png_bytep out, png_size_t n) {
    PngSource *s = png_get_io_ptr(png);
    if (s->pos + n > s->size) png_error(png, "truncated");
    memcpy(out, s->data + s->pos, n);
    s->pos += n;
}

/* PNG -> CV2: depth byte 0x20, width, height, width again, 0, then BGRA rows. */
static uint8_t *png_to_cv2(const uint8_t *data, size_t size, size_t *out_size) {
    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info = png ? png_create_info_struct(png) : NULL;
    uint8_t *volatile out = NULL;
    png_bytep *volatile rows = NULL;
    if (!info) { png_destroy_read_struct(&png, NULL, NULL); return NULL; }
    PngSource src = {data, size, 0};
    if (setjmp(png_jmpbuf(png))) {
        free(out); free(rows);
        png_destroy_read_struct(&png, &info, NULL);
        return NULL;
    }
    png_set_read_fn(png, &src, png_source_read);
    png_read_info(png, info);
    png_uint_32 w = png_get_image_width(png, info), h = png_get_image_height(png, info);
    int type = png_get_color_type(png, info), depth = png_get_bit_depth(png, info);
    if (type == PNG_COLOR_TYPE_PALETTE) png_set_expand(png);
    if (type == PNG_COLOR_TYPE_GRAY && depth < 8) png_set_expand(png);
    if (png_get_valid(png, info, PNG_INFO_tRNS)) png_set_expand(png);
    if (depth == 16) png_set_strip_16(png);
    if (type == PNG_COLOR_TYPE_GRAY || type == PNG_COLOR_TYPE_GRAY_ALPHA) png_set_gray_to_rgb(png);
    png_set_filler(png, 0xff, PNG_FILLER_AFTER);
    png_set_bgr(png);
    png_read_update_info(png, info);
    *out_size = 17 + (size_t)w * h * 4;
    out = malloc(*out_size);
    rows = malloc(sizeof *rows * (h ? h : 1));
    if (!out || !rows) png_error(png, "out of memory");
    out[0] = 0x20;
    memcpy(out + 1, &w, 4); memcpy(out + 5, &h, 4); memcpy(out + 9, &w, 4);
    memset(out + 13, 0, 4);
    for (png_uint_32 y = 0; y < h; y++) rows[y] = out + 17 + (size_t)y * w * 4;
    png_read_image(png, rows);
    png_destroy_read_struct(&png, &info, NULL);
    free(rows);
    return out;
}

/* The inner cipher the game's text readers undo (patch DLL 0x65782938). */
static void cv_encrypt(uint8_t *p, size_t n) {
    uint8_t a = 0x8b, b = 0x71;
    for (size_t i = 0; i < n; i++) {
        p[i] ^= a;
        a = (uint8_t)(a + b);
        b = (uint8_t)(b - 0x6b);
    }
}

static uint8_t *inflate_raw(const uint8_t *in, size_t in_size, size_t out_size) {
    uint8_t *out = malloc(out_size ? out_size : 1);
    z_stream z;
    memset(&z, 0, sizeof z);
    if (!out || inflateInit2(&z, -MAX_WBITS) != Z_OK) { free(out); return NULL; }
    z.next_in = (Bytef *)in; z.avail_in = (uInt)in_size;
    z.next_out = out; z.avail_out = (uInt)out_size;
    int r = inflate(&z, Z_FINISH);
    inflateEnd(&z);
    if (r != Z_STREAM_END || z.total_out != out_size) { free(out); return NULL; }
    return out;
}

static uint8_t *read_file(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *data = n > 0 ? malloc((size_t)n) : NULL;
    if (data && fread(data, 1, (size_t)n, f) != (size_t)n) { free(data); data = NULL; }
    fclose(f);
    *size = data ? (size_t)n : 0;
    return data;
}

/* -- cache ---------------------------------------------------------------------------------- */
/* Layout: magic, zip size (u32), entry count (u32), entries (name[96], offset, size),
   then the payloads. Rebuilt when missing or made from a different th123e.dat. */
static int load_cache(const char *path, uint32_t zip_size) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    char magic[sizeof CACHE_MAGIC];
    uint32_t head[2];
    int ok = fread(magic, 1, sizeof magic, f) == sizeof magic && !memcmp(magic, CACHE_MAGIC, sizeof magic) &&
             fread(head, 4, 2, f) == 2 && head[0] == zip_size && head[1] && head[1] < 4096;
    if (ok) {
        entries = calloc(head[1], sizeof *entries);
        ok = entries && fread(entries, sizeof *entries, head[1], f) == head[1];
        if (ok) entry_count = head[1];
    }
    fclose(f);
    return ok;
}

static int build_cache(const char *zip_path, const char *cache_path, const uint8_t *zip, size_t zip_size) {
    /* end of central directory: the last 22+ bytes */
    size_t eocd = zip_size >= 22 ? zip_size - 22 : 0;
    while (eocd > 0 && le32(zip + eocd) != 0x06054b50u) eocd--;
    if (le32(zip + eocd) != 0x06054b50u) { trace("# th123e: %s is not a ZIP", zip_path); return 0; }
    unsigned count = le16(zip + eocd + 10);
    size_t dir = le32(zip + eocd + 16);
    Entry *list = calloc(count ? count : 1, sizeof *list);
    uint8_t **payload = calloc(count ? count : 1, sizeof *payload);
    unsigned n = 0, skipped = 0;
    uint32_t offset = (uint32_t)(sizeof CACHE_MAGIC + 8 + (size_t)count * sizeof *list);
    for (unsigned i = 0; i < count && dir + 46 <= zip_size; i++) {
        const uint8_t *c = zip + dir;
        if (le32(c) != 0x02014b50u) break;
        unsigned method = le16(c + 10), name_len = le16(c + 28), extra = le16(c + 30), comment = le16(c + 32);
        size_t csize = le32(c + 20), usize = le32(c + 24), local = le32(c + 42);
        char name[256] = "";
        memcpy(name, c + 46, name_len < 255 ? name_len : 255);
        dir += 46 + name_len + extra + comment;
        if (local + 30 > zip_size) { skipped++; continue; }
        const uint8_t *data = zip + local + 30 + le16(zip + local + 26) + le16(zip + local + 28);
        if (data + csize > zip + zip_size) { skipped++; continue; }
        size_t len = strlen(name);
        if (len > 4 && !strcmp(name + len - 4, ".ttf")) continue; /* fonts: a later phase */
        uint8_t *raw = method == 0 ? malloc(usize ? usize : 1) : method == 8 ? inflate_raw(data, csize, usize) : NULL;
        if (raw && method == 0) memcpy(raw, data, usize);
        if (!raw) { skipped++; continue; }
        size_t out_size = usize;
        uint8_t *out = raw;
        if (len > 4 && !strcmp(name + len - 4, ".png")) {
            out = png_to_cv2(raw, usize, &out_size);
            free(raw);
            if (!out) { trace("# th123e: cannot decode %s", name); skipped++; continue; }
        } else if (len > 4 && (!strcmp(name + len - 4, ".cv0") || !strcmp(name + len - 4, ".cv1"))) {
            cv_encrypt(out, out_size);
        }
        uint8_t key = (uint8_t)((offset >> 1) | 0x23);
        for (size_t k = 0; k < out_size; k++) out[k] ^= key;
        normalize(name, list[n].name, sizeof list[n].name);
        list[n].offset = offset;
        list[n].size = (uint32_t)out_size;
        payload[n++] = out;
        offset += (uint32_t)out_size;
    }
    /* payload order must match the offsets, so sort a copy of the index only */
    FILE *f = fopen(cache_path, "wb");
    int ok = f != NULL;
    if (f) {
        uint32_t head[2] = {(uint32_t)zip_size, n};
        Entry *sorted = malloc(sizeof *sorted * (n ? n : 1));
        memcpy(sorted, list, sizeof *sorted * n);
        qsort(sorted, n, sizeof *sorted, entry_cmp);
        /* the header reserves room for all ZIP entries; unused slots stay zero */
        Entry *slots = calloc(count ? count : 1, sizeof *slots);
        memcpy(slots, sorted, sizeof *sorted * n);
        ok = fwrite(CACHE_MAGIC, 1, sizeof CACHE_MAGIC, f) == sizeof CACHE_MAGIC &&
             fwrite(head, 4, 2, f) == 2 && fwrite(slots, sizeof *slots, count, f) == count;
        for (unsigned i = 0; ok && i < n; i++)
            ok = fwrite(payload[i], 1, list[i].size, f) == list[i].size;
        ok = fclose(f) == 0 && ok;
        free(slots);
        entries = sorted;
        entry_count = ok ? n : 0;
    }
    for (unsigned i = 0; i < n; i++) free(payload[i]);
    free(payload);
    free(list);
    trace("# th123e: cache %s built: %u resources (%u skipped)%s", cache_path, n, skipped, ok ? "" : " - write FAILED");
    return ok;
}

/* -- intercept ------------------------------------------------------------------------------ */
static uint32_t call_import(Cpu *c, uint32_t slot, unsigned argc, const uint32_t *argv) {
    uint32_t esp = c->esp.d;
    for (unsigned i = argc; i-- > 0;) push32(c, argv[i]);
    push32(c, GUEST_RETURN_SENTINEL);
    guest_call_import(c, slot);
    c->esp.d = esp;
    return c->eax.d;
}

static void factory(Cpu *c) {
    uint32_t name = rd32(c->esp.d + 4), size_out = rd32(c->esp.d + 8), offset_out = rd32(c->esp.d + 12);
    char text[256];
    unsigned n = 0;
    for (; n + 1 < sizeof text && rd8(name + n); n++) text[n] = (char)rd8(name + n);
    text[n] = 0;
    const Entry *e = lookup(text);
    if (!e) { factory_original(c); return; }
    /* CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, NORMAL, NULL) */
    uint32_t open_args[7] = {cache_path_guest, 0x80000000u, 1, 0, 3, 0x80, 0};
    uint32_t handle = call_import(c, IAT_CREATE_FILE_A, 7, open_args);
    if (handle == 0xffffffffu) { factory_original(c); return; }
    uint32_t seek_args[4] = {handle, e->offset, 0, 0};
    call_import(c, IAT_SET_FILE_POINTER, 4, seek_args);
    wr32(size_out, e->size);
    wr32(offset_out, e->offset);
    c->eax.d = handle;
    c->esp.d += 4 + 12;
}

void th123e_init(void) {
    char zip_path[1100], cache_path[1100];
    snprintf(zip_path, sizeof zip_path, "%s/th123e.dat", host_data_dir);
    snprintf(cache_path, sizeof cache_path, "%s/th123e.cache", host_data_dir);
    size_t zip_size = 0;
    uint8_t *zip = read_file(zip_path, &zip_size);
    if (!zip) { trace("# th123e: no %s, game stays in Japanese", zip_path); return; }
    if (!load_cache(cache_path, (uint32_t)zip_size)) build_cache(zip_path, cache_path, zip, zip_size);
    else trace("# th123e: cache %s: %u resources", cache_path, entry_count);
    free(zip);
    factory_original = guest_lifted(0x0041c080u);
    if (!entry_count || !factory_original) return;
    static const char guest_name[] = "th123e.cache";
    cache_path_guest = heap_alloc(sizeof guest_name, 0);
    memcpy(G(cache_path_guest), guest_name, sizeof guest_name);
    guest_intercept(0x0041c080u, factory);
}
