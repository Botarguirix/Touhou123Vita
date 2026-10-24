#include "glyph.h"
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_SYNTHESIS_H
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

enum { CACHE_LIMIT=8*1024*1024, ENTRY_LIMIT=4096 };
typedef struct Entry {
    struct Entry *next;
    int height, weight;
    uint16_t code;
    GlyphMetrics gm;
    uint32_t bytes;
    uint8_t pixels[];
} Entry;
static FT_Library library;
static FT_Face face;
static Entry *cache;
static uint32_t cache_bytes, cache_count;
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER;

static void clear_cache(void) {
    while (cache) { Entry *p=cache;cache=p->next;free(p); }
    cache_bytes=cache_count=0;
}
int glyph_init(const char *font_path) {
    if (!font_path) return -1;
    pthread_mutex_lock(&lock);
    FT_Library new_library=NULL; FT_Face new_face=NULL;
    if (FT_Init_FreeType(&new_library) || FT_New_Face(new_library,font_path,0,&new_face)
        || FT_Select_Charmap(new_face,FT_ENCODING_UNICODE)) {
        if (new_face) FT_Done_Face(new_face);
        if (new_library) FT_Done_FreeType(new_library);
        pthread_mutex_unlock(&lock);return -1;
    }
    clear_cache();
    if (face) FT_Done_Face(face);
    if (library) FT_Done_FreeType(library);
    library=new_library;face=new_face;
    pthread_mutex_unlock(&lock);return 0;
}
static Entry *raster(int height,int weight,uint16_t code) {
    if (height < -4096 || height > 4096 || (code>=0xd800 && code<=0xdfff)) return NULL;
    int h=height ? height:16;
    FT_Size_RequestRec request={h<0 ? FT_SIZE_REQUEST_TYPE_NOMINAL : FT_SIZE_REQUEST_TYPE_REAL_DIM,
                               0,(FT_Long)(h<0 ? -h:h)*64,0,0};
    if (FT_Request_Size(face,&request)
        || FT_Load_Char(face,code,FT_LOAD_NO_BITMAP|FT_LOAD_TARGET_NORMAL)) return NULL;
    if (weight>=600) FT_GlyphSlot_Embolden(face->glyph);
    if (FT_Render_Glyph(face->glyph,FT_RENDER_MODE_NORMAL)) return NULL;
    FT_GlyphSlot slot=face->glyph;FT_Bitmap *bitmap=&slot->bitmap;
    if (bitmap->width>4096 || bitmap->rows>4096) return NULL;
    uint32_t pitch=(bitmap->width+3u)&~3u;
    uint32_t bytes=pitch*bitmap->rows;
    if (bytes>CACHE_LIMIT-sizeof(Entry)) return NULL;
    long advance_x=(slot->advance.x+32)/64,advance_y=(slot->advance.y+32)/64;
    if (advance_x<INT16_MIN || advance_x>INT16_MAX || advance_y<INT16_MIN || advance_y>INT16_MAX)
        return NULL;
    if (bytes && (bitmap->pixel_mode!=FT_PIXEL_MODE_GRAY || bitmap->num_grays!=256)) return NULL;
    Entry *entry=calloc(1,sizeof(Entry)+bytes);
    if (!entry) return NULL;
    entry->height=height;entry->weight=weight;entry->code=code;entry->bytes=bytes;
    entry->gm=(GlyphMetrics){bitmap->width,bitmap->rows,slot->bitmap_left,slot->bitmap_top,
                            (int16_t)advance_x,(int16_t)advance_y};
    int source_pitch=bitmap->pitch;
    for (unsigned y=0;y<bitmap->rows;++y) {
        const uint8_t *row=bitmap->buffer + (source_pitch<0 ? bitmap->rows-1-y:y)
                                              *(size_t)(source_pitch<0 ? -source_pitch:source_pitch);
        for (unsigned x=0;x<bitmap->width;++x)
            entry->pixels[y*pitch+x]=(uint8_t)((row[x]*16u+127u)/255u);
    }
    return entry;
}
uint32_t glyph_gray4(int height,int weight,uint16_t code,GlyphMetrics *gm,uint8_t *buf,uint32_t size) {
    if (!gm) return UINT32_MAX;
    pthread_mutex_lock(&lock);
    if (!face) { pthread_mutex_unlock(&lock);return UINT32_MAX; }
    Entry **link=&cache;
    while (*link && !((*link)->height==height && (*link)->weight==weight && (*link)->code==code))
        link=&(*link)->next;
    Entry *entry=*link;
    if (entry) { *link=entry->next; }
    else {
        entry=raster(height,weight,code);
        if (!entry) { pthread_mutex_unlock(&lock);return UINT32_MAX; }
        /* LRU: el principio es el mas reciente. Incluye metadatos en el limite. */
        while (cache && (cache_bytes+sizeof(Entry)+entry->bytes>CACHE_LIMIT || cache_count>=ENTRY_LIMIT)) {
            Entry **tail=&cache;
            while ((*tail)->next) tail=&(*tail)->next;
            Entry *old=*tail;*tail=NULL;cache_bytes-=(uint32_t)sizeof(Entry)+old->bytes;
            --cache_count;free(old);
        }
        cache_bytes+=(uint32_t)sizeof(Entry)+entry->bytes;++cache_count;
    }
    entry->next=cache;cache=entry;*gm=entry->gm;
    uint32_t result=entry->bytes;
    if (buf && size) {
        if (size<result) result=UINT32_MAX;
        else if (result) memcpy(buf,entry->pixels,result);
    }
    pthread_mutex_unlock(&lock);return result;
}
#ifdef T123_GLYPH_TEST
uint32_t glyph_test_bytes(void) { return cache_bytes; }
uint32_t glyph_test_count(void) { return cache_count; }
uint32_t glyph_test_entry_size(void) { return sizeof(Entry); }
const char *glyph_test_family(void) { return face ? face->family_name:""; }
int glyph_test_units(void) { return face ? face->units_per_EM:0; }
int glyph_test_ascender(void) { return face ? face->ascender:0; }
int glyph_test_descender(void) { return face ? face->descender:0; }
#endif
