#include <stdio.h>
#include <psp2/ctrl.h>
#include <psp2/display.h>
#include <psp2/kernel/processmgr.h>
#include "soft2d.h"
#include "t123/fight.h"
static soft2d_pgf *font;
static soft2d_texture *sprites[2],*background;
static const float scale=544.0f/480.0f;
static float sx(float x){return 117.33f+x*scale;}
static void rect(float x,float y,float w,float h,unsigned c){soft2d_draw_rectangle(sx(x),y*scale,w*scale,h*scale,c);}
static void text(int x,int y,const char *s,unsigned c){soft2d_pgf_draw_text(font,sx(x),y*scale,c,0.85f,s);}
#define WHITE RGBA8(235,240,250,255)
#define GOLD RGBA8(255,215,125,255)
static uint32_t controls(unsigned b){
    uint32_t in=0;
    if(b&SCE_CTRL_LEFT)in|=IN_LEFT;
    if(b&SCE_CTRL_RIGHT)in|=IN_RIGHT;
    if(b&SCE_CTRL_UP)in|=IN_JUMP;
    if(b&SCE_CTRL_SQUARE)in|=IN_MELEE;
    if(b&SCE_CTRL_TRIANGLE)in|=IN_SHOT;
    if(b&SCE_CTRL_RTRIGGER)in|=IN_GUARD;
    if(b&SCE_CTRL_SELECT)in|=IN_RESET;
    if(b&SCE_CTRL_CROSS)in|=IN_CONFIRM;
    if(b&SCE_CTRL_CIRCLE)in|=IN_BACK;
    if(b&SCE_CTRL_LTRIGGER)in|=IN_AI;
    return in;
}
static uint32_t scenario(int f){
    if(f==10 || f==30)return IN_CONFIRM;
    if(f<40)return 0;
    unsigned in=0;
    if(f>=40 && f<100)in|=IN_RIGHT;
    if(f==70)in|=IN_JUMP;
    if(f%37==0)in|=IN_SHOT;
    if(f%29==0)in|=IN_MELEE;
    if(f>=220 && f<245)in|=IN_GUARD;
    return in;
}
static void fighter(const Fighter *p,int i){
    int ground=395-p->y;unsigned c=i?RGBA8(110,190,255,255):RGBA8(245,105,145,255);
    soft2d_draw_fill_circle(sx(p->x),398*scale,21*scale,RGBA8(20,22,40,200));
    if(sprites[i]){
        float size=1.5f*scale,w=soft2d_texture_get_width(sprites[i])*size,h=soft2d_texture_get_height(sprites[i])*size;
        soft2d_draw_texture_scale(sprites[i],sx(p->x)+(p->face<0?w/2:-w/2),ground*scale-h,p->face*size,size);
    }else{
        rect(p->x-18,ground-65,36,46,c);
        soft2d_draw_fill_circle(sx(p->x),(ground-78)*scale,14*scale,c);
        rect(p->x-15,ground-22,10,22,c);rect(p->x+5,ground-22,10,22,c);
    }
    if(p->attack)rect(p->x+p->face*22-(p->face<0?35:0),ground-55,35,12,GOLD);
    if(p->guard)rect(p->x+p->face*28,ground-94,5,94,RGBA8(100,255,230,200));
    if(p->stun)soft2d_draw_fill_circle(sx(p->x),(ground-50)*scale,8*scale,GOLD);
}
static void draw(const Fight *g,int automated){
    rect(0,0,640,480,RGBA8(20,23,43,255));
    if(g->scene!=SCENE_FIGHT){
        rect(0,0,640,7,RGBA8(218,79,121,255));
        text(48,78,"TOUHOU123VITA",GOLD);
        text(48,112,"Prototype 0.1 - native Vita practice arena",WHITE);
        text(48,149,"Own engine; original gameplay not recovered yet",WHITE);
        if(g->scene==SCENE_MENU){
            rect(40,204,560,70,RGBA8(57,46,78,255));
            text(60,247,"> PRACTICE    [X / keyboard X]",GOLD);
            text(48,331,"Prototype controls: arrows, Z, V, Q, E",WHITE);
        }else{
            text(48,214,"PRACTICE SETUP",GOLD);
            text(48,250,"Player 1 vs training CPU | 1000 HP",WHITE);
            text(48,285,"X: enter arena     Circle/C: back",GOLD);
            text(48,335,"L/Q: toggle CPU   SELECT/right Shift: reset",WHITE);
        }
    }else{
        if(background)soft2d_draw_texture_scale(background,sx(0),0,640*scale/soft2d_texture_get_width(background),400*scale/soft2d_texture_get_height(background));
        else{rect(0,0,640,400,RGBA8(35,49,72,255));for(int i=0;i<12;i++)rect(i*60,200+(i%3)*20,28,180,RGBA8(24,39,58,255));}
        rect(0,395,640,85,RGBA8(48,37,60,255));
        rect(30,30,240,15,RGBA8(40,20,30,255));rect(370,30,240,15,RGBA8(20,25,40,255));
        rect(30,30,g->p[0].hp*240.0f/1000,15,RGBA8(245,105,145,255));rect(370,30,g->p[1].hp*240.0f/1000,15,RGBA8(110,190,255,255));
        char line[96];snprintf(line,sizeof line,"P1 %d HP",g->p[0].hp);text(30,24,line,WHITE);
        snprintf(line,sizeof line,"CPU %d HP",g->p[1].hp);text(370,24,line,WHITE);text(280,40,"PRACTICE",GOLD);
        fighter(&g->p[0],0);fighter(&g->p[1],1);
        for(int i=0;i<16;i++)if(g->shots[i].active)soft2d_draw_fill_circle(sx(g->shots[i].x),(395-g->shots[i].y)*scale,8*scale,g->shots[i].owner?RGBA8(90,200,255,255):RGBA8(255,110,170,255));
        if(!g->p[0].hp || !g->p[1].hp)text(210,170,"K.O. - SELECT to restart",GOLD);
        snprintf(line,sizeof line,"Hits: %u / %u    CPU: %s",g->p[0].hits,g->p[1].hits,g->ai?"ON":"OFF");text(30,428,line,WHITE);
        text(30,453,"Arrows move/jump | Z melee | V shot | E guard | C back",WHITE);
        text(30,475,"Prototype rules - original moves/cards/weather pending",GOLD);
    }
    if(automated)text(430,110,"AUTOMATED TEST",GOLD);
}
int main(void){
    Fight g;fight_init(&g);sceCtrlSetSamplingMode(SCE_CTRL_MODE_ANALOG);
    if(soft2d_init()<0)return 1;
    font=soft2d_load_default_pgf();if(!font){soft2d_fini();return 2;}
    sprites[0]=soft2d_load_texture("app0:assets/player.rgba");sprites[1]=soft2d_load_texture("app0:assets/cpu.rgba");background=soft2d_load_texture("app0:assets/stage.rgba");
    FILE *flag=fopen("app0:auto-test.txt","r");int automated=flag!=NULL;if(flag)fclose(flag);
    int f=0,menu_seen=0,practice_seen=0,fight_seen=0,jump_seen=0;
    for(;;){
        SceCtrlData pad={0};sceCtrlPeekBufferPositive(0,&pad,1);fight_step(&g,automated?scenario(f):controls(pad.buttons));
        if(g.scene==SCENE_MENU)menu_seen=1;
        if(g.scene==SCENE_PRACTICE)practice_seen=1;
        if(g.scene==SCENE_FIGHT)fight_seen=1;
        if(g.p[0].y>0)jump_seen=1;
        soft2d_start_drawing();soft2d_clear_screen();draw(&g,automated);soft2d_end_drawing();soft2d_swap_buffers();sceDisplayWaitVblankStart();
        if(automated && ++f==600){
            int pass=menu_seen&&practice_seen&&fight_seen&&jump_seen&&g.p[0].hits>0&&g.p[1].hp<1000;
            FILE *r=fopen("ux0:data/touhou123vita-smoke.json","w");
            if(r){fprintf(r,"{\"schema\":2,\"status\":\"%s\",\"frames\":600,\"menu\":%d,\"practice\":%d,\"fight\":%d,\"jump\":%d,\"hits\":%u,\"cpu_hp\":%d,\"digest\":%u,\"sprites\":%d}\n",pass?"passed":"failed",menu_seen,practice_seen,fight_seen,jump_seen,g.p[0].hits,g.p[1].hp,(unsigned)fight_digest(&g),sprites[0]!=NULL&&sprites[1]!=NULL);fclose(r);}
            break;
        }
    }
    for(int i=0;i<2;i++)if(sprites[i])soft2d_free_texture(sprites[i]);
    if(background)soft2d_free_texture(background);
    soft2d_free_pgf(font);soft2d_fini();sceKernelExitProcess(0);return 0;
}
