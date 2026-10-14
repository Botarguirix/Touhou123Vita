#include <stdlib.h>
#include <string.h>
#include "t123/fight.h"
void fight_reset(Fight *g) {
    memset(g->p,0,sizeof g->p); memset(g->shots,0,sizeof g->shots);
    for(int i=0;i<2;i++) { g->p[i].x= i ? 450:190; g->p[i].hp=1000; g->p[i].face= i ? -1:1; }
    g->frame=0;
}
void fight_init(Fight *g) { memset(g,0,sizeof *g); g->ai=1; fight_reset(g); }
static void hit(Fighter *victim, Fighter *attacker, int damage) {
    if(victim->stun || victim->hp<=0) return;
    victim->hp-=victim->guard ? damage/5 : damage;
    if(victim->hp<0) victim->hp=0;
    victim->stun=victim->guard ? 8:16;
    victim->x+=attacker->face*(victim->guard ? 5:16); ++attacker->hits;
}
static void act(Fight *g,int i,uint32_t in,uint32_t edge) {
    Fighter *p=&g->p[i],*other=&g->p[1-i];
    if(p->cooldown) --p->cooldown;
    if(p->attack) --p->attack;
    if(p->stun) --p->stun;
    p->guard=(in&IN_GUARD)!=0 && p->y==0;
    if(p->hp && !p->stun) {
        p->face=p->x<=other->x ? 1:-1;
        if(!p->guard && !p->attack) {
            if(in&IN_LEFT) p->x-=3;
            if(in&IN_RIGHT) p->x+=3;
            if((edge&IN_JUMP) && p->y==0) p->vy=13;
        }
        if((edge&IN_MELEE) && !p->cooldown && !p->guard) { p->attack=14;p->cooldown=24; }
        if((edge&IN_SHOT) && !p->cooldown && !p->guard) {
            for(int j=0;j<16;j++) if(!g->shots[j].active) {
                g->shots[j]=(Shot){1,p->x+p->face*30,p->y+48,p->face*7,i}; p->cooldown=32; break;
            }
        }
    }
    if(p->y || p->vy) { p->y+=p->vy; --p->vy; if(p->y<=0) {p->y=0;p->vy=0;} }
    if(p->x<35) p->x=35;
    if(p->x>605) p->x=605;
    if(p->attack==10 && abs(p->x-other->x)<85 && abs(p->y-other->y)<65) hit(other,p,90);
}
void fight_step(Fight *g,uint32_t in) {
    uint32_t edge=in&~g->previous; g->previous=in;
    if(g->scene!=SCENE_FIGHT) {
        if(edge&IN_CONFIRM) { ++g->scene; if(g->scene==SCENE_FIGHT) fight_reset(g); }
        if(edge&IN_BACK) g->scene=SCENE_MENU;
        return;
    }
    if(edge&IN_BACK) {g->scene=SCENE_PRACTICE;return;}
    if(edge&IN_AI) g->ai=!g->ai;
    if(edge&IN_RESET) {fight_reset(g);return;}
    uint32_t cpu=0;
    if(g->ai && g->p[1].hp && g->p[0].hp) {
        int distance=g->p[0].x-g->p[1].x;
        if(abs(distance)>65) cpu|=distance>0?IN_RIGHT:IN_LEFT;
        if(g->frame%55==0) cpu|=abs(distance)<90?IN_MELEE:IN_SHOT;
        if(g->frame%180==120) cpu|=IN_JUMP;
        if(g->frame%90>72) cpu|=IN_GUARD;
    }
    act(g,0,in,edge); act(g,1,cpu,cpu);
    for(int j=0;j<16;j++) {
        Shot *s=&g->shots[j]; if(!s->active) continue;
        s->x+=s->vx; Fighter *v=&g->p[1-s->owner];
        if(abs(s->x-v->x)<24 && s->y>=v->y && s->y<=v->y+92) {hit(v,&g->p[s->owner],55);s->active=0;}
        if(s->x<0 || s->x>640) s->active=0;
    }
    ++g->frame;
}
uint32_t fight_digest(const Fight *g) {
    uint32_t h=2166136261u;
    for(int i=0;i<2;i++) {
        const Fighter *p=&g->p[i];
        const int fields[]={p->x,p->y,p->vy,p->hp,p->cooldown,p->stun,(int)p->hits};
        for(unsigned j=0;j<sizeof fields/sizeof fields[0];j++) h=(h^(uint32_t)fields[j])*16777619u;
    }
    return h;
}
