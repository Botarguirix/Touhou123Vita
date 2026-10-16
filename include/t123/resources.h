#ifndef T123_RESOURCES_H
#define T123_RESOURCES_H
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
typedef struct {uint32_t offset,size;char name[256];} T123DatEntry;
typedef struct {FILE *file;T123DatEntry *entries;uint32_t count;uint32_t size;} T123Dat;
typedef struct {T123Dat dat[3];unsigned opened;} T123Resources;
typedef struct {uint32_t width,height;uint32_t *pixels;} T123Bitmap;
int t123_dat_open(T123Dat *dat,const char *path);
void t123_dat_close(T123Dat *dat);
int t123_dat_read(T123Dat *dat,const char *name,unsigned char **bytes,size_t *size);
int t123_resources_open(T123Resources *bank,const char *folder);
void t123_resources_close(T123Resources *bank);
int t123_resource_read(T123Resources *bank,const char *name,unsigned char **bytes,size_t *size);
int t123_bitmap_decode(const unsigned char *bytes,size_t size,const unsigned char *palette,size_t palette_size,T123Bitmap *out);
void t123_bitmap_free(T123Bitmap *bitmap);
int t123_resource_bitmap(T123Resources *bank,const char *name,const char *palette,T123Bitmap *out);
#endif
