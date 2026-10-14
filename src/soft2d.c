/* CPU framebuffer renderer for the first prototype. No DirectX or GPU dependency. */
#include "soft2d.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <psp2/display.h>
#include <psp2/kernel/sysmem.h>
static SceUID ids[2];static uint32_t *buffers[2],*fb;static unsigned buffer_index;
int soft2d_init(void){
    for(int i=0;i<2;i++){
        ids[i]=sceKernelAllocMemBlock("T123 framebuffer",SCE_KERNEL_MEMBLOCK_TYPE_USER_RW_UNCACHE,960*544*4,NULL);
        if(ids[i]<0)return -1;
        if(sceKernelGetMemBlockBase(ids[i],(void**)&buffers[i])<0)return -1;
    }
    fb=buffers[0];return 0;
}
void soft2d_fini(void){for(int i=0;i<2;i++)if(ids[i]>=0)sceKernelFreeMemBlock(ids[i]);}
void soft2d_start_drawing(void){fb=buffers[buffer_index];}
void soft2d_clear_screen(void){memset(fb,0,960*544*4);}
void soft2d_end_drawing(void){}
void soft2d_swap_buffers(void){
    SceDisplayFrameBuf frame={sizeof(SceDisplayFrameBuf),fb,960,SCE_DISPLAY_PIXELFORMAT_A8B8G8R8,960,544};
    sceDisplaySetFrameBuf(&frame,SCE_DISPLAY_SETBUF_NEXTFRAME);buffer_index^=1;
}
static void pixel(int x,int y,uint32_t c){
    if(x<0||x>=960||y<0||y>=544)return;
    unsigned a=c>>24;if(!a)return;
    if(a==255){fb[y*960+x]=c;return;}
    uint32_t d=fb[y*960+x];uint32_t v=0xff000000;
    for(int s=0;s<24;s+=8)v|=((((c>>s)&255)*a+((d>>s)&255)*(255-a))/255)<<s;
    fb[y*960+x]=v;
}
void soft2d_draw_rectangle(float x,float y,float w,float h,uint32_t c){
    int l=(int)x,t=(int)y,r=(int)(x+w),b=(int)(y+h);
    if(l<0)l=0;if(t<0)t=0;if(r>960)r=960;if(b>544)b=544;
    for(int py=t;py<b;py++)for(int px=l;px<r;px++)pixel(px,py,c);
}
void soft2d_draw_fill_circle(float x,float y,float r,uint32_t c){
    for(int py=(int)(y-r);py<=(int)(y+r);py++)for(int px=(int)(x-r);px<=(int)(x+r);px++)
        if((px-x)*(px-x)+(py-y)*(py-y)<=r*r)pixel(px,py,c);
}
soft2d_texture *soft2d_load_texture(const char *path){
    FILE *f=fopen(path,"rb");if(!f)return NULL;
    uint32_t header[2];if(fread(header,4,2,f)!=2||!header[0]||!header[1]||header[0]>1920||header[1]>1088){fclose(f);return NULL;}
    soft2d_texture *t=calloc(1,sizeof *t);if(!t){fclose(f);return NULL;}
    t->w=header[0];t->h=header[1];size_t size=(size_t)t->w*t->h*4;t->pixels=malloc(size);
    if(!t->pixels||fread(t->pixels,1,size,f)!=size){free(t->pixels);free(t);fclose(f);return NULL;}
    fclose(f);return t;
}
void soft2d_free_texture(soft2d_texture *t){if(t){free(t->pixels);free(t);}}
unsigned soft2d_texture_get_width(const soft2d_texture *t){return t->w;}
unsigned soft2d_texture_get_height(const soft2d_texture *t){return t->h;}
void soft2d_draw_texture_scale(const soft2d_texture *t,float x,float y,float sx,float sy){
    if(!t||sx==0||sy<=0)return;
    int w=(int)(t->w*(sx<0?-sx:sx)),h=(int)(t->h*sy);
    for(int py=0;py<h;py++)for(int px=0;px<w;px++){
        int u=(int)(px/(sx<0?-sx:sx)),v=(int)(py/sy);
        pixel((int)x+(sx<0?-px:px),(int)y+py,t->pixels[v*t->w+u]);
    }
}
soft2d_pgf *soft2d_load_default_pgf(void){return soft2d_load_texture("app0:assets/font.rgba");}
void soft2d_free_pgf(soft2d_pgf *f){soft2d_free_texture(f);}
void soft2d_pgf_draw_text(const soft2d_pgf *f,float x,float y,uint32_t color,float scale,const char *s){
    if(!f)return;
    for(;*s;s++,x+=9*scale){unsigned ch=(unsigned char)*s;if(ch>=128)ch='?';
        for(int py=0;py<16;py++)for(int px=0;px<12;px++){
            uint32_t c=f->pixels[(ch/16*16+py)*f->w+ch%16*12+px];
            if(c>>24)soft2d_draw_rectangle(x+px*scale,y-16*scale+py*scale,scale+0.5f,scale+0.5f,color);
        }
    }
}
