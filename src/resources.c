#include "t123/resources.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
static uint16_t u16(const unsigned char *p){return (uint16_t)(p[0]|((uint16_t)p[1]<<8));}
static uint32_t u32(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
typedef struct{uint32_t word[624];unsigned cursor;} MT;
static void seed(MT *m,uint32_t n){m->word[0]=n;for(unsigned i=1;i<624;i++)m->word[i]=1812433253u*(m->word[i-1]^(m->word[i-1]>>30))+i;m->cursor=624;}
static uint32_t random_word(MT *m){
 if(m->cursor==624){for(unsigned i=0;i<624;i++){uint32_t v=(m->word[i]&0x80000000u)|(m->word[(i+1)%624]&0x7fffffffu);m->word[i]=m->word[(i+397)%624]^(v>>1)^((v&1)?0x9908b0dfu:0);}m->cursor=0;}
 uint32_t v=m->word[m->cursor++];v^=v>>11;v^=(v<<7)&0x9d2c5680u;v^=(v<<15)&0xefc60000u;return v^(v>>18);
}
static int same_name(const char *a,const char *b){
 while(*a&&*b){unsigned x=(unsigned char)*a++,y=(unsigned char)*b++;if(x=='\\')x='/';if(y=='\\')y='/';if(x>='A'&&x<='Z')x+=32;if(y>='A'&&y<='Z')y+=32;if(x!=y)return 0;}return *a==*b;
}
void t123_dat_close(T123Dat *d){if(d->file)fclose(d->file);free(d->entries);memset(d,0,sizeof *d);}
int t123_dat_open(T123Dat *d,const char *path){
 memset(d,0,sizeof *d);d->file=fopen(path,"rb");if(!d->file)return -1;
 unsigned char header[6];if(fread(header,1,6,d->file)!=6)goto fail;
 uint32_t n=u16(header),len=u32(header+2);if(!n || len<n*9u || len>16u*1024*1024)goto fail;
 if(fseek(d->file,0,SEEK_END))goto fail;
 long end=ftell(d->file);if(end<0 || (unsigned long)end>INT32_MAX || (uint32_t)end<len+6u)goto fail;
 d->size=(uint32_t)end;
 unsigned char *table=malloc(len);if(!table)goto fail;
 if(fseek(d->file,6,SEEK_SET) || fread(table,1,len,d->file)!=len){free(table);goto fail;}
 MT m;seed(&m,len+6u);unsigned a=0xc5,b=0x83;
 for(uint32_t i=0;i<len;i++){table[i]^=(unsigned char)(random_word(&m)^a);a=(a+b)&255;b=(b+0x53)&255;}
 d->entries=calloc(n,sizeof *d->entries);if(!d->entries){free(table);goto fail;}
 uint32_t pos=0;
 for(uint32_t i=0;i<n;i++){
  if(len-pos<9){free(table);goto fail;}
  T123DatEntry *e=&d->entries[i];e->offset=u32(table+pos);e->size=u32(table+pos+4);unsigned name_len=table[pos+8];pos+=9;
  if(!name_len || name_len>len-pos || e->offset<len+6u || e->offset>d->size || e->size>d->size-e->offset){free(table);goto fail;}
  memcpy(e->name,table+pos,name_len);e->name[name_len]=0;pos+=name_len;
  if(memchr(e->name,0,name_len)){free(table);goto fail;}
 }
 free(table);d->count=n;return 0;
fail:t123_dat_close(d);return -1;
}
int t123_dat_read(T123Dat *d,const char *name,unsigned char **bytes,size_t *size){
 if(!d||!d->file||!name||!bytes||!size)return -1;
 for(uint32_t i=0;i<d->count;i++)if(same_name(d->entries[i].name,name)){
  const T123DatEntry *e=&d->entries[i];if(e->size>64u*1024*1024)return -1;
  unsigned char *p=malloc(e->size?e->size:1);if(!p)return -1;
  if(fseek(d->file,(long)e->offset,SEEK_SET)||fread(p,1,e->size,d->file)!=e->size){free(p);return -1;}
  unsigned char key=(unsigned char)((e->offset>>1)|0x23u);for(uint32_t j=0;j<e->size;j++)p[j]^=key;
  *bytes=p;*size=e->size;return 0;
 }
 return 1;
}
int t123_resources_open(T123Resources *b,const char *folder){
 memset(b,0,sizeof *b);for(unsigned i=0;i<3;i++){char p[1024];int n=snprintf(p,sizeof p,"%s/th123%c.dat",folder,'a'+i);if(n<0||(size_t)n>=sizeof p)continue;if(t123_dat_open(&b->dat[i],p)==0)b->opened|=1u<<i;}
 return b->opened&1u?0:-1;
}
void t123_resources_close(T123Resources *b){for(unsigned i=0;i<3;i++)t123_dat_close(&b->dat[i]);b->opened=0;}
int t123_resource_read(T123Resources *b,const char *name,unsigned char **bytes,size_t *size){
 for(int i=2;i>=0;i--){if(b->opened&(1u<<i)){int r=t123_dat_read(&b->dat[i],name,bytes,size);if(r!=1)return r;}}
 return 1;
}
static int palette_colors(const unsigned char *p,size_t size,uint32_t out[256]){
 if(!p || size<1)return -1;
 unsigned bpp=p[0];unsigned stride=bpp==16?2:bpp==32?4:0;
 if(!stride || size<1+256u*stride)return -1;
 for(unsigned i=0;i<256;i++){
  if(stride==2){unsigned c=u16(p+1+i*2),b=c&31,g=(c>>5)&31,r=(c>>10)&31;out[i]=((r<<3)|(r>>2))|(((g<<3)|(g>>2))<<8)|(((b<<3)|(b>>2))<<16)|((c&0x8000)?0xff000000u:0);}
  else{const unsigned char *c=p+1+i*4;out[i]=c[2]|((uint32_t)c[1]<<8)|((uint32_t)c[0]<<16)|((uint32_t)c[3]<<24);}
 }
 out[0]&=0xffffffu;return 0;
}
int t123_bitmap_decode(const unsigned char *p,size_t size,const unsigned char *palette,size_t palette_size,T123Bitmap *out){
 memset(out,0,sizeof *out);if(!p || size<17)return -1;
 unsigned bpp=p[0];uint32_t w=u32(p+1),h=u32(p+5),pitch=u32(p+9),alt=u32(p+13),stride=bpp==8?1:(bpp==24||bpp==32)?4:0;
 if(!stride || !w||!h||w>2048||h>2048||pitch<w||pitch>2048||alt)return -1;
 size_t raw=(size_t)pitch*h*stride;if(raw>size-17)return -1;
 uint32_t colors[256];if(bpp==8 && palette_colors(palette,palette_size,colors))return -1;
 uint32_t *pix=malloc((size_t)w*h*4);if(!pix)return -1;
 for(uint32_t y=0;y<h;y++)for(uint32_t x=0;x<w;x++){
  const unsigned char *c=p+17+((size_t)y*pitch+x)*stride;
  pix[y*w+x]=bpp==8?colors[c[0]]:c[2]|((uint32_t)c[1]<<8)|((uint32_t)c[0]<<16)|((uint32_t)c[3]<<24);
 }
 out->width=w;out->height=h;out->pixels=pix;return 0;
}
void t123_bitmap_free(T123Bitmap *b){free(b->pixels);memset(b,0,sizeof *b);}
int t123_resource_bitmap(T123Resources *b,const char *name,const char *pal,T123Bitmap *out){
 unsigned char *bytes=NULL,*palette=NULL;size_t size=0,ps=0;
 if(t123_resource_read(b,name,&bytes,&size))return -1;
 if(size && bytes[0]==8 && (!pal || t123_resource_read(b,pal,&palette,&ps))){free(bytes);return -1;}
 int r=t123_bitmap_decode(bytes,size,palette,ps,out);free(bytes);free(palette);return r;
}
