#include <stdlib.h>
#include <string.h>
#include "t123/fight.h"
void fight_reset(Fight *g) {
    memset(g->p,0,sizeof g->p); memset(g->shots,0,sizeof g->shots);memset(g->objects,0,sizeof g->objects);
    g->object_spawns=0;
    for(int i=0;i<2;i++) { g->p[i].x= i ? 450:190; g->p[i].hp=g->max_hp?g->max_hp:1000; g->p[i].face= i ? -1:1;g->p[i].skill_card_id=g->character[i]==0?103:-1;t123_input_history_reset(&g->input_history[i],0); }
    g->frame=0;g->previous=0;
}
void fight_init(Fight *g) { memset(g,0,sizeof *g); g->ai=1;g->max_hp=1000;fight_reset(g); }
void fight_bind_patterns(Fight *g,const T123Pattern *a,const T123Pattern *b){fight_bind_character_patterns(g,a,-1,b,-1);}
void fight_bind_character_patterns(Fight *g,const T123Pattern *a,int ca,const T123Pattern *b,int cb){g->patterns[0]=a;g->patterns[1]=b;g->character[0]=ca;g->character[1]=cb;g->max_hp=10000;fight_reset(g);}
static int pose_has_attack(const T123Move *m){
 if(!m)return 0;
 for(unsigned i=0;i<m->sequence.count;i++)if(m->poses[i].damage&&m->poses[i].attack_count)return 1;
 return 0;
}
static unsigned attack_variant(const T123Pattern *pattern,int id){
 unsigned index=0;
 /* The PAT's per-action index is a runtime choice; prefer the variant with
    the greatest authored damage/hitbox coverage when no selector is ported. */
 const T123Move *best=t123_pattern_best_attack(pattern,id,&index);
 return best&&pose_has_attack(best)?index:0;
}
static int is_skill_action(int id){return id>=500&&id<600;}
static unsigned current_sequence(const Fighter *p){
 return is_skill_action(p->action)&&p->action_sequence_count?p->animation.sequence:p->action_index;
}
static void action(Fight *g,int i,int id){
 Fighter *p=&g->p[i];p->action=id;p->action_ticks=0;p->hit_done=0;p->object_counter=0;if(id!=200)p->dash_ticks=0;
 if(id!=560){p->skill_air_active=0;p->skill_air_x_q=0;p->skill_air_vx_q=0;p->skill_air_y_q=0;p->skill_air_vy_q=0;}
 /* Dash attacks have authored variants whose offensive sequence must be
    selected from PAT; other B/C variant selectors still need x86 recovery. */
 p->action_index=(id==408||id==418)?attack_variant(g->patterns[i],id):0;
 p->action_sequence_count=0;
 if(is_skill_action(id)&&g->patterns[i]){
  int count=t123_pattern_sequences(g->patterns[i],id,p->action_sequences,T123_ACTION_SEQUENCE_LIMIT);
  if(count>0)p->action_sequence_count=(uint16_t)count;
 }
 const T123Move *m=t123_pattern_move(g->patterns[i],id,p->action_index);
 if(p->action_sequence_count)t123_animation_set(&p->animation,p->action_sequences,p->action_sequence_count,0);
 else if(m)t123_animation_set(&p->animation,&m->sequence,1,0);
}
static int is_attack(int id){return (id>=300&&id<333)||(id>=400&&id<419)||(id>=500&&id<600);}
static int overlap(const T123Box *a,const Fighter *pa,const T123Box *b,const Fighter *pb);
static void spawn_object(Fight *g,int owner,int action_id,int move_action,unsigned sequence,int offset_x,int offset_y,int vx,int vy,int life,int follow_owner){
 const T123Move *m=t123_pattern_move(g->patterns[owner],move_action,sequence);if(!m||!m->sequence.count)return;
 for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++)if(!g->objects[i].active){T123Object *o=&g->objects[i];const Fighter *p=&g->p[owner];memset(o,0,sizeof *o);o->active=1;o->owner=owner;o->action=action_id;o->sequence=(int)sequence;o->owner_action=p->action;o->offset_x=offset_x;o->offset_y=offset_y;o->follow_owner=follow_owner;o->x=p->x+p->face*offset_x;o->y=p->y+offset_y;o->vx=p->face*vx;o->vy=vy;o->life=life;t123_animation_set(&o->animation,&m->sequence,1,0);++g->object_spawns;return;}
}
static void spawn_dash_object(Fight *g,int owner){
 int c=g->character[owner],id=g->p[owner].action;
 if(c==3&&id==408)spawn_object(g,owner,849,849,19,60,100,0,0,12,1);
 else if(c==3&&id==418){unsigned frame=g->p[owner].animation.current_frame;unsigned seq=(frame==3||frame==5)?23u:21u;spawn_object(g,owner,849,849,seq,0,50,0,0,90,1);}
 else if(c==19&&id==408)spawn_object(g,owner,989,989,5,0,0,0,0,90,1);
 else if(c==19&&id==418)spawn_object(g,owner,808,808,0,0,0,4,0,90,0);
}
static void spawn_reimu_505_volley(Fight *g,int owner,unsigned route){
 /* Reimu 00490490's action-505 jump-table case (VA 0049985C) emits object
    0x32B at PAT seq.2/pose.2/frame 0. Player+0x7D6 selects 3/4/5
    projectiles; the handler changes it after action age 20 and 60. */
 static const int vx[3][5]={{10,0,-10,0,0},{15,5,-5,-15,0},{20,10,0,-10,-20}};
 static const int vy[3][5]={{22,24,22,0,0},{24,26,26,24,0},{25,26,28,26,25}};
 static const unsigned count[]={3,4,5};if(route>2)route=2;
 for(unsigned n=0;n<count[route];n++)spawn_object(g,owner,811,811,0,114,96,vx[route][n],vy[route][n],120,0);
}
static void update_objects(Fight *g){
 for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++){T123Object *o=&g->objects[i];if(!o->active)continue;const T123Move *m=t123_pattern_move(g->patterns[o->owner],o->action,o->sequence);if(!m){o->active=0;continue;}if(!o->age){o->age=1;continue;}const Fighter *owner=&g->p[o->owner];if(o->follow_owner&&owner->action==o->owner_action){o->x=owner->x+owner->face*o->offset_x;int anchor_y=o->offset_y;if(o->action==849&&owner->action==418)anchor_y=60;o->y=owner->y+anchor_y;}else{o->follow_owner=0;o->x+=o->vx;o->y+=o->vy;}++o->age;if(o->life>0&&--o->life==0){o->active=0;continue;}int ended=t123_animation_tick(&o->animation,&m->sequence,1);if(ended<0||ended==1){o->active=0;continue;}
  if(!m->poses||o->animation.pose>=m->sequence.count)continue;
  const T123Pose *pose=&m->poses[o->animation.pose];Fighter *victim=&g->p[1-o->owner];if(!pose->damage||!pose->attack_count||!victim->hp)continue;
  for(unsigned a=0;a<pose->attack_count;a++){T123Box box=pose->attack[a];box.left+=o->x-g->p[o->owner].x;box.right+=o->x-g->p[o->owner].x;box.up+=g->p[o->owner].y-o->y;box.down+=g->p[o->owner].y-o->y;
   for(unsigned b=0;b<T123_BOX_LIMIT;b++){const T123Pose *vp=fight_pose(g,1-o->owner);if(!vp||b>=vp->hurt_count)break;if(overlap(&box,&g->p[o->owner],&vp->hurt[b],victim)){victim->hp-=victim->guard?pose->chip:pose->damage;if(victim->hp<0)victim->hp=0;victim->stun=victim->guard?pose->block_stun:pose->enemy_stun;if(victim->stun<1)victim->stun=1;Fighter *attacker=&g->p[o->owner];++attacker->hits;if(o->owner_action>=400&&o->owner_action<410)++attacker->b_hits;else if(o->owner_action>=410&&o->owner_action<420)++attacker->c_hits;o->active=0;break;}}
  }
 }
}
static int next_a_chain(const Fight *g,int i,int id){
 int next=id==300?320:id==320?321:id==321?322:-1;
 return next>=0&&t123_pattern_move(g->patterns[i],next,0)?next:-1;
}
static int choose_attack(const Fight *g,int i,uint32_t in,int airborne){
 const Fighter *p=&g->p[i];int toward=(p->face>0?(in&IN_RIGHT):(in&IN_LEFT))!=0;
 int away=(p->face>0?(in&IN_LEFT):(in&IN_RIGHT))!=0;
 int id;
 if(airborne){id=(in&IN_DOWN)?308:toward?307:away?309:306;}
 else{id=(in&IN_DOWN)?(toward?304:303):toward?302:away?330:300;}
 if(t123_pattern_move(g->patterns[i],id,0))return id;
 return t123_pattern_move(g->patterns[i],300,0)?300:-1;
}
static int choose_b(const Fight *g,int i,uint32_t in,int airborne){
 const Fighter *p=&g->p[i];int toward=(p->face>0?(in&IN_RIGHT):(in&IN_LEFT))!=0;
 int away=(p->face>0?(in&IN_LEFT):(in&IN_RIGHT))!=0;int id;
 if(airborne)id=(in&IN_DOWN)?406:toward?405:away?409:404;
 else id=(in&IN_DOWN)?(toward?403:402):toward?(p->action==200&&p->dash_ticks?408:401):away?407:400;
 if(p->action==200&&p->dash_ticks&&id==408){
  const T123Move *lock=t123_pattern_move(g->patterns[i],408,attack_variant(g->patterns[i],408));
  if(!lock||p->animation.current_frame>lock->move_lock)return -1;
 }
 return t123_pattern_move(g->patterns[i],id,0)?id:-1;
}
static int choose_c(const Fight *g,int i,uint32_t in,int airborne){
 const Fighter *p=&g->p[i];int toward=(p->face>0?(in&IN_RIGHT):(in&IN_LEFT))!=0;
 int away=(p->face>0?(in&IN_LEFT):(in&IN_RIGHT))!=0;int id;
 if(airborne)id=(in&IN_DOWN)?416:toward?415:away?417:414;
 else id=(in&IN_DOWN)?412:toward?(p->action==200&&p->dash_ticks?418:411):410;
 if(p->action==200&&p->dash_ticks&&id==418){
  const T123Move *lock=t123_pattern_move(g->patterns[i],418,attack_variant(g->patterns[i],418));
  if(!lock||p->animation.current_frame>lock->move_lock)return -1;
 }
 if(!t123_pattern_move(g->patterns[i],id,0)&&away&&!airborne)id=410;
 return t123_pattern_move(g->patterns[i],id,0)?id:-1;
}
static int skill_action(const Fight *g,int i){
 /* Grounded routes recovered from Reimu's x86 handler 004ae670. Card-hand
    selection/cost are still represented by the prototype's fixed slot. */
 static const uint16_t card_action[12]={500,520,540,560,505,525,545,565,510,530,550,570};
 int card=g->p[i].skill_card_id;
 if(g->patterns[i]&&g->character[i]==0&&card>=100&&card<=111&&g->p[i].y==0){
  int action_id=card_action[card-100];
  unsigned sequences=t123_pattern_variant_count(g->patterns[i],action_id);
  if(sequences>0&&sequences<=T123_ACTION_SEQUENCE_LIMIT)return action_id;
 }
 return -1;
}
static uint16_t input_sample(uint32_t in){
 uint16_t sample=0;
 /* 0046d5d0 packs horizontal signs at bits 0-1, vertical at 2-3,
    A-D at 4-7, card change at bit 8 and spellcard at bit 9. */
 if(in&IN_LEFT)sample|=0x01;
 if(in&IN_RIGHT)sample|=0x02;
 if(in&IN_JUMP)sample|=0x04;
 if(in&IN_DOWN)sample|=0x08;
 if(in&IN_MELEE)sample|=0x10;
 if(in&IN_SHOT)sample|=0x20;
 if(in&IN_C_ATTACK)sample|=0x40;
 if(in&IN_GUARD)sample|=0x80;
 if(in&IN_CHANGE_CARD)sample|=0x100;
 if(in&IN_SPELLCARD)sample|=0x200;
 return sample;
}
const T123Pose *fight_pose(const Fight *g,int i){
 if(!g->patterns[i])return NULL;
 const T123Move *m=t123_pattern_move(g->patterns[i],g->p[i].action,current_sequence(&g->p[i]));
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
 if(p->dash_ticks>0)--p->dash_ticks;
 p->guard=(in&IN_GUARD)!=0 && p->y==0;p->face=p->x<=g->p[1-i].x?1:-1;
 int attacking=is_attack(p->action);
 if(attacking&&(edge&IN_MELEE)&&p->hit_done){int next=next_a_chain(g,i,p->action);if(next>=0)action(g,i,next);}
 if(attacking&&p->hit_done&&(edge&IN_SHOT)){int id=choose_b(g,i,in,p->y>0);if(id>=0)action(g,i,id);}
 if(attacking&&p->hit_done&&(edge&IN_C_ATTACK)){int id=choose_c(g,i,in,p->y>0);if(id>=0)action(g,i,id);}
 if(!attacking && !p->stun && p->hp){
  int desired=0,started_dash=0,forward_bit=p->face>0?IN_RIGHT:IN_LEFT,forward=(in&forward_bit)!=0;
  int forward_edge=(edge&forward_bit)!=0;
  int backward=(p->face>0?(in&IN_LEFT):(in&IN_RIGHT))!=0;
  if(!p->dash_ticks&&p->y==0&&forward_edge&&!p->guard){
   const char *motion=p->face>0?"NRNR":"NLNL";
   if(t123_input_match(&g->input_history[i],motion,15,(int8_t)p->face)&&
      t123_pattern_move(g->patterns[i],200,0)){
    p->dash_ticks=10;++p->dashes;started_dash=1;
   }
  }
  int in_dash=p->action==200&&p->dash_ticks>0;
  int card_skill=(edge&IN_SPELLCARD)?skill_action(g,i):-1;
  if(card_skill>=0&&!p->guard){desired=card_skill;++p->skill_uses;}
  else if(p->guard)desired=150;
  else if(started_dash)desired=200;
  else if(in_dash){desired=200;p->x+=p->face*5;}
  else if(p->y>0){
   if(p->vy<0)desired=9;
   else if(forward)desired=7;
   else if(backward)desired=8;
   else desired=(p->action==7||p->action==8)?p->action:6;
   if(in&IN_RIGHT)p->x+=2;
   if(in&IN_LEFT)p->x-=2;
  }else if(in&IN_DOWN)desired=(edge&IN_DOWN)?1:2;
  else if(p->action==1||p->action==2)desired=3;
  else if(forward)desired=4;
  else if(backward)desired=5;
  if(p->y==0&&!p->guard&&!in_dash){if(in&IN_RIGHT)p->x+=2;if(in&IN_LEFT)p->x-=2;}
  if((edge&IN_JUMP)&&p->y==0&&!p->guard){p->vy=13;desired=forward?7:backward?8:6;}
  if((edge&IN_MELEE)&&!p->guard){int attack=choose_attack(g,i,in,p->y>0);if(attack>=0)desired=attack;}
  if((edge&IN_SHOT)&&!p->guard){int attack=choose_b(g,i,in,p->y>0);if(attack>=0)desired=attack;}
  if((edge&IN_C_ATTACK)&&!p->guard){int attack=choose_c(g,i,in,p->y>0);if(attack>=0)desired=attack;}
  if(p->action==200&&p->dash_ticks==0)desired=0;
 if(p->action!=desired&&t123_pattern_move(g->patterns[i],desired,0))action(g,i,desired);
 }
 if(p->y||p->vy||p->skill_air_active){
  /* 00487EA0's Reimu action-560 landing gate requires ground contact while
     descending and a clear collision flag. This arena has a flat floor and
     no separate collision flag, so landing at y<=0 while vy<0 is its local
     equivalent. Keep action 560 and enter PAT sequence 3 (dashStop recovery)
     instead of replacing the skill with generic action 10. */
  int descending;
  if(p->skill_air_active){
   /* Physics helper 00463550 integrates vx in the facing direction. The
      action-560 handler sets speed.x=4.5; retain quarter units for the .5. */
   p->skill_air_x_q+=p->skill_air_vx_q*p->face;
   if(p->skill_air_x_q<35*4)p->skill_air_x_q=35*4;
   if(p->skill_air_x_q>605*4)p->skill_air_x_q=605*4;
   p->x=p->skill_air_x_q/4;
   p->skill_air_y_q+=p->skill_air_vy_q;
   p->skill_air_vy_q-=3; /* x86 action 560 subtracts gravity 0.75 per update. */
   p->y=p->skill_air_y_q/4;
   p->vy=p->skill_air_vy_q/4;
   descending=p->skill_air_vy_q<0;
  }else{
   descending=p->vy<0;
   p->y+=p->vy;--p->vy;
  }
  if(p->y<=0){
   int skill_landing=p->action==560&&g->character[i]==0&&descending&&
    p->action_sequence_count>3&&p->animation.sequence<3;
   p->y=p->vy=0;
   if(skill_landing){
    p->skill_air_active=0;p->skill_air_x_q=0;p->skill_air_vx_q=0;p->skill_air_y_q=0;p->skill_air_vy_q=0;
    if(t123_animation_set(&p->animation,p->action_sequences,p->action_sequence_count,3)==0)p->action_index=3;
    else action(g,i,10);
   }else if(p->action!=300)action(g,i,10);
  }
 }
 if(p->x<35)p->x=35;
 if(p->x>605)p->x=605;
 const T123Move *m=t123_pattern_move(g->patterns[i],p->action,current_sequence(p));
 if(!m)return;
 if(!p->animation.duration){
  if(is_skill_action(p->action)&&p->action_sequence_count)t123_animation_set(&p->animation,p->action_sequences,p->action_sequence_count,p->animation.sequence);
  else t123_animation_set(&p->animation,&m->sequence,1,0);
 }
 if(p->action==505&&p->action_ticks<INT32_MAX)++p->action_ticks;
 if(g->character[i]==0&&p->action==505&&!p->object_counter&&
    p->animation.sequence==2&&p->animation.pose==2&&p->animation.pose_frame==0&&
    t123_pattern_move(g->patterns[i],811,0)){
  unsigned route=p->action_ticks>60?2u:p->action_ticks>20?1u:0u;
  spawn_reimu_505_volley(g,i,route);p->object_counter=1;
 }
 if(g->character[i]==19&&p->action==418&&p->animation.sequence==0&&p->object_counter>=1&&p->object_counter<=19){
  if(p->object_counter&1)spawn_dash_object(g,i);
  ++p->object_counter;
 }
 unsigned previous_sequence=p->animation.sequence,previous_pose=p->animation.pose;
 int finished=is_skill_action(p->action)&&p->action_sequence_count?
  t123_animation_tick(&p->animation,p->action_sequences,p->action_sequence_count):
  t123_animation_tick(&p->animation,&m->sequence,1);
 if(is_skill_action(p->action)&&p->action_sequence_count)p->action_index=p->animation.sequence;
 /* Original 004A0772 initializes Reimu 560's air launch when PAT seq. 1
    reaches pose/subframe/frame zero: vx=4.5, vy=14.0 and gravity=0.75.
    Physics helper 00463550 multiplies vx by direction and speedPower. */
 if(p->action==560&&g->character[i]==0&&p->action_sequence_count>1&&
    p->animation.sequence==1&&p->animation.pose==0&&p->animation.pose_frame==0&&
    p->animation.current_frame==0&&!p->skill_air_active){
  p->skill_air_active=1;p->skill_air_x_q=p->x*4;p->skill_air_vx_q=18;
  p->skill_air_y_q=p->y*4;p->skill_air_vy_q=56;p->vy=14;
 }
 if(g->character[i]==19&&p->action==418&&previous_sequence==0&&previous_pose<10&&p->animation.sequence==0&&p->animation.pose==10&&p->animation.pose_frame==0)p->object_counter=1;
 if(finished==1&&(is_attack(p->action)||p->action==3||p->action==10)){action(g,i,0);return;}
 if(finished==1&&p->action==1){action(g,i,2);return;}
 p->attack=is_attack(p->action);
 if(p->attack&&!p->hit_done&&(p->action==408&&p->animation.current_frame==1))spawn_dash_object(g,i);
 if(p->attack&&!p->hit_done&&p->action==418&&g->character[i]==3&&p->animation.current_frame>=2&&p->animation.current_frame<=5)spawn_dash_object(g,i);
 const T123Pose *f=fight_pose(g,i),*v=fight_pose(g,1-i);Fighter *victim=&g->p[1-i];
 if(!f||!v||p->hit_done||!f->damage||!victim->hp)return;
 for(unsigned a=0;a<f->attack_count;a++)for(unsigned b=0;b<v->hurt_count;b++)if(overlap(&f->attack[a],p,&v->hurt[b],victim)){
  int damage=victim->guard?f->chip:f->damage;victim->hp-=damage;if(victim->hp<0)victim->hp=0;
  victim->stun=victim->guard?f->block_stun:f->enemy_stun;if(victim->stun<1)victim->stun=1;
  int reaction=victim->guard?(victim->y?158:150):(victim->y?70:50);
  if(t123_pattern_move(g->patterns[1-i],reaction,0))action(g,1-i,reaction);
  ++p->hits;if(p->action<400)++p->a_hits;else if(p->action<410)++p->b_hits;else if(p->action<420)++p->c_hits;p->hit_done=1;return;
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
    if(g->patterns[0]&&g->patterns[1]){t123_input_history_push(&g->input_history[0],input_sample(in));t123_input_history_push(&g->input_history[1],input_sample(cpu));data_act(g,0,in,edge);data_act(g,1,cpu,cpu);separate(g);update_objects(g);++g->frame;return;}
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
        const int fields[]={p->x,p->y,p->vy,p->hp,p->cooldown,p->stun,p->dash_ticks,p->object_counter,p->skill_card_id,p->action_ticks,p->skill_air_x_q,p->skill_air_vx_q,p->skill_air_y_q,p->skill_air_vy_q,p->skill_air_active,(int)p->hits,(int)p->a_hits,(int)p->b_hits,(int)p->c_hits,(int)p->dashes,(int)p->skill_uses};
        for(unsigned j=0;j<sizeof fields/sizeof fields[0];j++) h=(h^(uint32_t)fields[j])*16777619u;
        const T123InputHistory *history=&g->input_history[i];
        h=(h^history->count)*16777619u;h=(h^history->next)*16777619u;
        for(unsigned j=0;j<T123_INPUT_HISTORY_CAPACITY;j++)h=(h^history->samples[j])*16777619u;
    }
    h=(h^g->object_spawns)*16777619u;
    for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++){const T123Object *o=&g->objects[i];const int fields[]={o->active,o->owner,o->action,o->sequence,o->owner_action,o->x,o->y,o->vx,o->vy,o->age,o->life,o->follow_owner,o->offset_x,o->offset_y,o->animation.pose,o->animation.pose_frame};for(unsigned j=0;j<sizeof fields/sizeof fields[0];j++)h=(h^(uint32_t)fields[j])*16777619u;}
    return h;
}
