/* Prueba propia: no contiene datos del juego ni imagen/audio externo. */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#include <png.h>
#include <ogg/ogg.h>
#include <vorbis/codec.h>
#include <vorbis/vorbisenc.h>
#include <vorbis/vorbisfile.h>
#ifdef __vita__
#include <psp2/io/stat.h>
#include <psp2/kernel/processmgr.h>
int _newlib_heap_size_user = 16 * 1024 * 1024;
#endif

#define CHECK(condition) do { if (!(condition)) { \
    printf("FAIL linea %d: %s\n", __LINE__, #condition); return 1; \
} } while (0)

typedef struct {
    unsigned char data[65536];
    size_t size, position;
    int closed;
} Memory;

static int append(Memory *memory, const void *bytes, size_t size)
{
    if (size > sizeof(memory->data) - memory->size) return 0;
    memcpy(memory->data + memory->size, bytes, size);
    memory->size += size;
    return 1;
}

static int test_zlib(void)
{
    unsigned char original[4096], encoded[8192], decoded[4096];
    uLongf encoded_size = sizeof(encoded), decoded_size = sizeof(decoded);
    for (size_t i = 0; i < sizeof(original); ++i) original[i] = (unsigned char)(i * 7u);
    CHECK(strcmp(zlibVersion(), "1.2.3") == 0);
    CHECK(compress2(encoded, &encoded_size, original, sizeof(original), 9) == Z_OK);
    CHECK(uncompress(decoded, &decoded_size, encoded, encoded_size) == Z_OK);
    CHECK(decoded_size == sizeof(original));
    CHECK(memcmp(original, decoded, sizeof(original)) == 0);
    encoded[encoded_size - 1] ^= 0x80;
    decoded_size = sizeof(decoded);
    CHECK(uncompress(decoded, &decoded_size, encoded, encoded_size) == Z_DATA_ERROR);
    printf("PASS zlib %s: 4096 bytes, roundtrip y Adler-32 invalido\n", zlibVersion());
    return 0;
}

static void png_memory_write(png_structp png, png_bytep data, png_size_t length)
{
    Memory *memory = (Memory *)png_get_io_ptr(png);
    if (!append(memory, data, length)) png_error(png, "buffer lleno");
}

static void png_memory_flush(png_structp png) { (void)png; }

static void png_memory_read(png_structp png, png_bytep data, png_size_t length)
{
    Memory *memory = (Memory *)png_get_io_ptr(png);
    if (length > memory->size - memory->position) png_error(png, "PNG truncado");
    memcpy(data, memory->data + memory->position, length);
    memory->position += length;
}

static int test_png(void)
{
    static Memory png_bytes;
    static const unsigned char pixels[16] = {
        255, 0, 0, 255, 0, 255, 0, 128,
        0, 0, 255, 64, 255, 255, 255, 0
    };
    unsigned char decoded[16];
    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info;
    CHECK(png != NULL);
    info = png_create_info_struct(png);
    CHECK(info != NULL);
    CHECK(strcmp(png_get_libpng_ver(png), "1.2.5") == 0);
    if (setjmp(png->jmpbuf)) { png_destroy_write_struct(&png, &info); return 1; }
    png_set_write_fn(png, &png_bytes, png_memory_write, png_memory_flush);
    png_set_IHDR(png, info, 2, 2, 8, PNG_COLOR_TYPE_RGBA,
                 PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_write_info(png, info);
    png_write_row(png, (png_bytep)pixels);
    png_write_row(png, (png_bytep)pixels + 8);
    png_write_end(png, info);
    png_destroy_write_struct(&png, &info);
    png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    CHECK(png != NULL);
    info = png_create_info_struct(png);
    CHECK(info != NULL);
    if (setjmp(png->jmpbuf)) { png_destroy_read_struct(&png, &info, NULL); return 1; }
    png_set_read_fn(png, &png_bytes, png_memory_read);
    png_read_info(png, info);
    CHECK(png_get_image_width(png, info) == 2 && png_get_image_height(png, info) == 2);
    CHECK(png_get_color_type(png, info) == PNG_COLOR_TYPE_RGBA);
    CHECK(png_get_rowbytes(png, info) == 8);
    png_read_row(png, decoded, NULL);
    png_read_row(png, decoded + 8, NULL);
    png_read_end(png, info);
    png_destroy_read_struct(&png, &info, NULL);
    CHECK(memcmp(pixels, decoded, sizeof(pixels)) == 0);
    printf("PASS libpng %s: PNG RGBA 2x2 generado y decodificado (%lu bytes)\n",
           PNG_LIBPNG_VER_STRING, (unsigned long)png_bytes.size);
    return 0;
}

static int append_page(Memory *memory, const ogg_page *page)
{
    return append(memory, page->header, (size_t)page->header_len)
        && append(memory, page->body, (size_t)page->body_len);
}

static size_t ogg_memory_read(void *ptr, size_t size, size_t count, void *source)
{
    Memory *memory = (Memory *)source;
    size_t remaining = memory->size - memory->position;
    if (!size) return 0;
    if (count > remaining / size) count = remaining / size;
    memcpy(ptr, memory->data + memory->position, count * size);
    memory->position += count * size;
    return count;
}

static int ogg_memory_no_seek(void *source, ogg_int64_t offset, int origin)
{
    (void)source;
    (void)offset;
    (void)origin;
    /* libvorbisfile 1.1.2 invoca seek_func al abrir incluso un stream no seekable. */
    return -1;
}

static int ogg_memory_close(void *source)
{
    ((Memory *)source)->closed = 1;
    return 0;
}

static long ogg_memory_tell(void *source)
{
    return (long)((Memory *)source)->position;
}

static int test_vorbis(void)
{
    static Memory ogg_bytes;
    ogg_stream_state stream;
    ogg_page page;
    ogg_packet header, comment_header, setup, packet;
    vorbis_info info;
    vorbis_comment comment;
    vorbis_dsp_state dsp;
    vorbis_block block;
    OggVorbis_File file;
    ov_callbacks callbacks = {
        ogg_memory_read, ogg_memory_no_seek, ogg_memory_close, ogg_memory_tell
    };
    float **samples;
    long decoded_count = 0, count;
    double energy = 0;
    int section = 0;
    vorbis_info_init(&info);
    CHECK(vorbis_encode_init_vbr(&info, 1, 8000, 0.1f) == 0);
    vorbis_comment_init(&comment);
    CHECK(vorbis_analysis_init(&dsp, &info) == 0);
    CHECK(vorbis_block_init(&dsp, &block) == 0);
    CHECK(ogg_stream_init(&stream, 123) == 0);
    CHECK(vorbis_analysis_headerout(&dsp, &comment, &header, &comment_header, &setup) == 0);
    CHECK(comment_header.bytes >= 11);
    CHECK(memcmp(comment_header.packet, "\003vorbis", 7) == 0);
    {
        uint32_t size = (uint32_t)comment_header.packet[7]
            | (uint32_t)comment_header.packet[8] << 8
            | (uint32_t)comment_header.packet[9] << 16
            | (uint32_t)comment_header.packet[10] << 24;
        const char *vendor = "Xiph.Org libVorbis I 20050304";
        CHECK(size == strlen(vendor) && size <= (uint32_t)comment_header.bytes - 11);
        CHECK(memcmp(comment_header.packet + 11, vendor, size) == 0);
        printf("PASS vendor real de libvorbis compilada: %.*s\n", (int)size, comment_header.packet + 11);
    }
    CHECK(ogg_stream_packetin(&stream, &header) == 0);
    CHECK(ogg_stream_packetin(&stream, &comment_header) == 0);
    CHECK(ogg_stream_packetin(&stream, &setup) == 0);
    while (ogg_stream_flush(&stream, &page)) CHECK(append_page(&ogg_bytes, &page));
    samples = vorbis_analysis_buffer(&dsp, 1024);
    CHECK(samples != NULL);
    for (int i = 0; i < 1024; ++i) samples[0][i] = 0.2f * sinf(i * 0.3455752f);
    CHECK(vorbis_analysis_wrote(&dsp, 1024) == 0);
    CHECK(vorbis_analysis_wrote(&dsp, 0) == 0);
    while (vorbis_analysis_blockout(&dsp, &block) == 1) {
        CHECK(vorbis_analysis(&block, NULL) == 0);
        CHECK(vorbis_bitrate_addblock(&block) == 0);
        while (vorbis_bitrate_flushpacket(&dsp, &packet)) {
            CHECK(ogg_stream_packetin(&stream, &packet) == 0);
            while (ogg_stream_pageout(&stream, &page)) CHECK(append_page(&ogg_bytes, &page));
        }
    }
    while (ogg_stream_flush(&stream, &page)) CHECK(append_page(&ogg_bytes, &page));
    ogg_stream_clear(&stream);
    vorbis_block_clear(&block);
    vorbis_dsp_clear(&dsp);
    vorbis_comment_clear(&comment);
    vorbis_info_clear(&info);
    CHECK(ov_open_callbacks(&ogg_bytes, &file, NULL, 0, callbacks) == 0);
    CHECK(ov_seekable(&file) == 0);
    CHECK(ov_info(&file, -1)->channels == 1 && ov_info(&file, -1)->rate == 8000);
    while ((count = ov_read_float(&file, &samples, 512, &section)) > 0) {
        CHECK(decoded_count + count <= 1024);
        for (long i = 0; i < count; ++i) {
            CHECK(isfinite(samples[0][i]));
            energy += samples[0][i] * samples[0][i];
        }
        decoded_count += count;
    }
    CHECK(count == 0 && decoded_count == 1024 && energy > 1.0);
    ov_clear(&file);
    CHECK(ogg_bytes.closed == 1);
    printf("PASS libogg/libvorbis/vorbisfile/vorbisenc: Ogg generado, 1024 muestras decodificadas\n");
    return 0;
}

int main(void)
{
#ifdef __vita__
    sceIoMkdir("ux0:data/touhou123vita", 0777);
    if (!freopen("ux0:data/touhou123vita/vita-libs-smoke.txt", "w", stdout))
        sceKernelExitProcess(2);
#endif
    setvbuf(stdout, NULL, _IONBF, 0);
    int result = test_zlib() || test_png() || test_vorbis();
    printf("%s vita-libs smoke\n", result ? "FAIL" : "PASS");
    fflush(stdout);
#ifdef __vita__
    fclose(stdout);
    sceKernelExitProcess(result);
#endif
    return result;
}
