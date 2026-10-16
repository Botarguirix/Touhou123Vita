#include <stdlib.h>
#include <string.h>
#include "t123/fight.h"
void fight_reset(Fight *g) {
    memset(g->p,0,sizeof g->p); memset(g->shots,0,sizeof g->shots);
    for(int i=0;i<2;i++) { g->p[i].x= i ? 450:190; g->p[i].hp=g->max_hp?g->max_hp:1000; g->p[i].face= i ? -1:1; }
    g->frame=0;
}
void fight_init(Fight *g) { memset(g,0,sizeof *g); g->ai=1;g->max_hp=1000;fight_reset(g); }
void fight_bind_patterns(Fight *g,const T123Pattern *a,const T123Pattern *b){g->patterns[0]=a;g->patterns[1]=b;g->max_hp=10000;fight_reset(g);}
static void action(Fight *g,int i,int id){
 Fighter *p=&g->p[i];p->action=id;p->hit_done=0;
 const T123Move *m=t123_pattern_move(g->patterns[i],id,0);
 if(m)t123_animation_set(&p->animation,&m->sequence,1,0);
}
const T123Pose *fight_pose(const Fight *g,int i){
 if(!g->patterns[i])return NULL;
 const T123Move *m=t123_pattern_move(g->patterns[i],g->p[i].action,0);
 if(!m||g->p[i].animation.pose>=m->sequence.count)return NULL;
 return &m->poses[g->p[i].animation.pose];
}
static int overlap(const T123Box *a,const Fighter *pa,const T123Box *b,const Fighter *pb){
 /* PAT coordinates are world units; the provisional arena uses a 0.5 camera scale. */
 int al=pa->x+(pa->face>0?a->left:-a->right)/2,ar=pa->x+(pa->face>0?a->right:-a->left)/2;
 int bl=pb->x+(pb->face>0?b->left:-b->right)/2,br=pb->x+(pb->face>0?b->right:-b->left)/2;
 int at=-pa->y+a->up/2,ab=-pa->y+a->down/2,bt=-pb->y+b->up/2,bb=-pb->y+b->down/2;
 return al<br && bl<ar && at<bb && bt<ab;
}
static void separate(Fight *g){
 const T123Pose *a=fight_pose(g,0),*b=fight_pose(g,1);
 if(!a||!b||!a->collision_count||!b->collision_count)return;
 if(!overlap(&a->collision[0],&g->p[0],&b->collision[0],&g->p[1]))return;
 int width=(a->collision[0].right-a->collision[0].left+b->collision[0].right-b->collision[0].left)/4;
 int difference=g->p[1].x-g->p[0].x,delta=width-abs(difference);if(delta<=0)return;
 int direction=difference>=0?1:-1;g->p[0].x-=direction*((delta+1)/2);g->p[1].x+=direction*(delta/2);
}
static void data_act(Fight *g,int i,uint32_t in,uint32_t edge){
 Fighter *p=&g->p[i];if(p->stun)--p->stun;
 p->guard=(in&IN_GUARD)!=0 && p->y==0;p->face=p->x<=g->p[1-i].x?1:-1;
 if(p->action!=300 && !p->stun && p->hp){
  int desired=p->guard?150:0;
  if(!p->guard){if(in&IN_LEFT){p->x-=2;desired=p->face>0?5:4;}if(in&IN_RIGHT){p->x+=2;desired=p->face>0?4:5;}
   if((edge&IN_JUMP)&&p->y==0){p->vy=13;desired=6;}
   if(p->y>0)desired=9;
   if((edge&IN_MELEE)&&p->y==0)desired=300;
  }
  if(p->action!=desired)action(g,i,desired);
 }
 if(p->y||p->vy){p->y+=p->vy;--p->vy;if(p->y<=0){p->y=p->vy=0;if(p->action!=300)action(g,i,10);}}
 if(p->x<35)p->x=35;
 if(p->x>605)p->x=605;
 const T123Move *m=t123_pattern_move(g->patterns[i],p->action,0);
 if(!m)return;
 if(!p->animation.duration)t123_animation_set(&p->animation,&m->sequence,1,0);
 int finished=t123_animation_tick(&p->animation,&m->sequence,1);
 if(finished==1 && p->action==300){action(g,i,0);return;}
 p->attack=p->action==300;
 const T123Pose *f=fight_pose(g,i),*v=fight_pose(g,1-i);Fighter *victim=&g->p[1-i];
 if(!f||!v||p->hit_done||!f->damage||!victim->hp||victim->stun)return;
 for(unsigned a=0;a<f->attack_count;a++)for(unsigned b=0;b<v->hurt_count;b++)if(overlap(&f->attack[a],p,&v->hurt[b],victim)){
  int damage=victim->guard?f->chip:f->damage;victim->hp-=damage;if(victim->hp<0)victim->hp=0;
  victim->stun=victim->guard?f->block_stun:f->enemy_stun;if(victim->stun<1)victim->stun=1;
  ++p->hits;p->hit_done=1;return;
 }
}
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
        if(abs(distance)>(g->patterns[1]?25:65)) cpu|=distance>0?IN_RIGHT:IN_LEFT;
        if(g->frame%55==0) cpu|=abs(distance)<35||!g->patterns[1]?IN_MELEE:IN_SHOT;
        if(g->frame%180==120) cpu|=IN_JUMP;
        if(g->frame%90>72) cpu|=IN_GUARD;
    }
    if(g->patterns[0]&&g->patterns[1]){data_act(g,0,in,edge);data_act(g,1,cpu,cpu);separate(g);++g->frame;return;}
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
