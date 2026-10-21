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
void soft2d_fini(void){
    /* Keep scanout buffers alive until process/session teardown. */
    sceDisplayWaitVblankStart();sceDisplayWaitVblankStart();
    /* Process exit reclaims the two allocations after the display session stops. */
}
void soft2d_start_drawing(void){fb=buffers[buffer_index];}
void soft2d_clear_screen(void){memset(fb,0,960*544*4);}
void soft2d_end_drawing(void){}
static void le32(unsigned char *p,uint32_t v){for(int i=0;i<4;i++)p[i]=(unsigned char)(v>>(i*8));}
int soft2d_capture(const char *path){
    FILE *f=fopen(path,"wb");if(!f)return -1;
    unsigned char header[54]={0};header[0]='B';header[1]='M';le32(header+2,54+960*544*3);le32(header+10,54);le32(header+14,40);
    le32(header+18,960);le32(header+22,(uint32_t)-544);header[26]=1;header[28]=24;le32(header+34,960*544*3);
    if(fwrite(header,1,54,f)!=54){fclose(f);return -1;}
    unsigned char row[960*3];
    for(int y=0;y<544;y++){
        for(int x=0;x<960;x++){uint32_t p=fb[y*960+x];row[x*3]=(p>>16)&255;row[x*3+1]=(p>>8)&255;row[x*3+2]=p&255;}
        if(fwrite(row,1,sizeof row,f)!=sizeof row){fclose(f);return -1;}
    }
    fclose(f);return 0;
}
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
soft2d_texture *soft2d_load_dat(T123Resources *bank,const char *name,const char *palette){
    T123Bitmap image;if(t123_resource_bitmap(bank,name,palette,&image))return NULL;
    soft2d_texture *t=malloc(sizeof *t);if(!t){t123_bitmap_free(&image);return NULL;}
    t->w=image.width;t->h=image.height;t->pixels=image.pixels;return t;
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
void soft2d_draw_texture_region_scale(const soft2d_texture *t,int left,int top,int right,int bottom,float x,float y,float sx,float sy){
    soft2d_draw_texture_region_scale_alpha(t,left,top,right,bottom,x,y,sx,sy,255);
}
void soft2d_draw_texture_region_scale_alpha(const soft2d_texture *t,int left,int top,int right,int bottom,float x,float y,float sx,float sy,unsigned alpha){
    if(!t||!t->pixels||!t->w||!t->h||sx==0.0f||sy<=0.0f)return;
    if(alpha>255)alpha=255;
    int source_w=right-left,source_h=bottom-top;
    if(source_w<=0||source_h<=0)return;
    float abs_sx=sx<0.0f?-sx:sx;
    int w=(int)(source_w*abs_sx),h=(int)(source_h*sy);
    for(int py=0;py<h;py++){
        int v=top+(int)(py/sy);if(v<0||(unsigned)v>=t->h)continue;
        for(int px=0;px<w;px++){
            int u=left+(int)(px/abs_sx);if(u<0||(unsigned)u>=t->w)continue;
            uint32_t color=t->pixels[(unsigned)v*t->w+(unsigned)u];
            unsigned source_alpha=color>>24;
            color=(color&0x00ffffffu)|(((source_alpha*alpha+127u)/255u)<<24);
            pixel((int)x+(sx<0.0f?-px:px),(int)y+py,color);
        }
    }
}
int soft2d_texture_region_crop_contract(void){
    if(!fb)return 0;
    uint32_t pixels[16],saved[16];
    soft2d_texture texture={4,4,pixels};
    for(unsigned i=0;i<16;i++)pixels[i]=0xff000000u|(i+1u);
    for(int y=0;y<4;y++)for(int x=0;x<4;x++)saved[y*4+x]=fb[(20+y)*960+20+x];
    for(int y=0;y<4;y++)for(int x=0;x<4;x++)fb[(20+y)*960+20+x]=0;
    soft2d_draw_texture_region_scale(&texture,1,1,3,3,20,20,1,1);
    int ok=fb[20*960+20]==pixels[5]&&fb[20*960+21]==pixels[6]&&
           fb[21*960+20]==pixels[9]&&fb[21*960+21]==pixels[10]&&
           fb[20*960+19]==0&&fb[20*960+22]==0&&fb[22*960+20]==0;
    for(int y=0;y<4;y++)for(int x=0;x<4;x++)fb[(20+y)*960+20+x]=saved[y*4+x];
    uint32_t saved_alpha=fb[40*960+40];
    fb[40*960+40]=RGBA8(0,0,255,255);pixels[0]=RGBA8(255,0,0,255);
    soft2d_draw_texture_region_scale_alpha(&texture,0,0,1,1,40,40,1,1,128);
    uint32_t blended=fb[40*960+40];
    ok=ok&&((blended&255u)>=127u)&&((blended&255u)<=128u)&&
       (((blended>>16)&255u)>=126u)&&(((blended>>16)&255u)<=127u);
    fb[40*960+40]=saved_alpha;
    return ok;
}
int soft2d_draw_texture_quad(const soft2d_texture *t,const float x[4],const float y[4]){
    if(!t||!t->pixels||!t->w||!t->h||!x||!y)return 0;
    float ux=x[1]-x[0],uy=y[1]-y[0],vx=x[2]-x[0],vy=y[2]-y[0];
    float det=ux*vy-uy*vx;if(det>-0.0001f&&det<0.0001f)return 0;
    float ex=x[1]+x[2]-x[0],ey=y[1]+y[2]-y[0];
    if((x[3]-ex>0.01f||ex-x[3]>0.01f)||(y[3]-ey>0.01f||ey-y[3]>0.01f))return 0;
    float minx=x[0],maxx=x[0],miny=y[0],maxy=y[0];
    for(int i=1;i<4;i++){if(x[i]<minx)minx=x[i];if(x[i]>maxx)maxx=x[i];if(y[i]<miny)miny=y[i];if(y[i]>maxy)maxy=y[i];}
    if(maxx<=0.0f||maxy<=0.0f||minx>=960.0f||miny>=544.0f)return 1;
    int left=minx<=0.0f?0:(int)minx,top=miny<=0.0f?0:(int)miny;
    int right=maxx>=960.0f?960:(int)maxx+1,bottom=maxy>=544.0f?544:(int)maxy+1;
    for(int py=top;py<bottom;py++)for(int px=left;px<right;px++){
        float dx=(float)px+0.5f-x[0],dy=(float)py+0.5f-y[0];
        float u=(dx*vy-dy*vx)/det,v=(ux*dy-uy*dx)/det;
        if(u<0.0f||u>=1.0f||v<0.0f||v>=1.0f)continue;
        unsigned tx=(unsigned)(u*(float)t->w),ty=(unsigned)(v*(float)t->h);
        if(tx>=t->w)tx=t->w-1;
        if(ty>=t->h)ty=t->h-1;
        pixel(px,py,t->pixels[ty*t->w+tx]);
    }
    return 1;
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
