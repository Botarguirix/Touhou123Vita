#ifndef SOFT2D_H
#define SOFT2D_H
#include <stdint.h>
#define RGBA8(r,g,b,a) ((uint32_t)(r)|((uint32_t)(g)<<8)|((uint32_t)(b)<<16)|((uint32_t)(a)<<24))
typedef struct {unsigned w,h;uint32_t *pixels;} soft2d_texture;
typedef soft2d_texture soft2d_pgf;
int soft2d_init(void);
void soft2d_fini(void);
void soft2d_start_drawing(void);
void soft2d_clear_screen(void);
void soft2d_end_drawing(void);
void soft2d_swap_buffers(void);
void soft2d_draw_rectangle(float x,float y,float w,float h,uint32_t color);
void soft2d_draw_fill_circle(float x,float y,float r,uint32_t color);
soft2d_texture *soft2d_load_texture(const char *path);
void soft2d_free_texture(soft2d_texture *t);
unsigned soft2d_texture_get_width(const soft2d_texture *t);
unsigned soft2d_texture_get_height(const soft2d_texture *t);
void soft2d_draw_texture_scale(const soft2d_texture *t,float x,float y,float sx,float sy);
soft2d_pgf *soft2d_load_default_pgf(void);
void soft2d_free_pgf(soft2d_pgf *f);
void soft2d_pgf_draw_text(const soft2d_pgf *f,float x,float y,uint32_t color,float scale,const char *s);
#endif
