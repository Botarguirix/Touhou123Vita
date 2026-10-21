#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "t123/fight.h"
/* PE 004635fc/00463619: locked flat-arena walls, in world coordinates.
   The viewport is 640 wide; it is not the arena's movement range. */
enum { ARENA_LEFT = 40, ARENA_RIGHT = 1240 };
static void fight_random_seed(Fight *g,uint32_t seed){
 g->random_words[0]=seed;
 for(unsigned i=1;i<624;i++)g->random_words[i]=1812433253u*(g->random_words[i-1]^(g->random_words[i-1]>>30))+i;
 g->random_index=624;
}
static uint32_t fight_random_word(Fight *g){
 if(g->random_index==624){
  for(unsigned i=0;i<624;i++){
   uint32_t value=(g->random_words[i]&0x80000000u)|(g->random_words[(i+1)%624]&0x7fffffffu);
   g->random_words[i]=g->random_words[(i+397)%624]^(value>>1)^((value&1u)?0x9908b0dfu:0u);
  }
  g->random_index=0;
 }
 uint32_t value=g->random_words[g->random_index++];
 value^=value>>11;value^=(value<<7)&0x9d2c5680u;value^=(value<<15)&0xefc60000u;
 return value^(value>>18);
}
static unsigned fight_random_range(Fight *g,unsigned range){
 if(!range)return 0;
 uint32_t divisor=0xffffffffu/range;
 return divisor?fight_random_word(g)/divisor:0;
}
void fight_reset(Fight *g) {
    memset(g->p,0,sizeof g->p); memset(g->shots,0,sizeof g->shots);memset(g->objects,0,sizeof g->objects);
    g->object_spawns=0;
    int patterned=g->patterns[0]&&g->patterns[1];
    /* Common Player reset 0046ba2e: x=480+320*(side==1), y=0. */
    for(int i=0;i<2;i++) { g->p[i].x= patterned ? 480+320*i : (i ? 450:190); g->p[i].hp=g->max_hp?g->max_hp:1000; g->p[i].face= i ? -1:1;g->p[i].skill_card_id=g->character[i]==0?103:-1;t123_input_history_reset(&g->input_history[i],0); }
    float center=patterned?640.0f:320.0f;
    g->camera=(T123StageCamera){center,0.0f,1.0f,center,0.0f,1.0f};
    g->frame=0;g->previous=0;
}
static void update_camera(Fight *g) {
    (void)t123_stage_camera_step(&g->camera,(float)g->p[0].x,-(float)g->p[0].y,
                                 (float)g->p[1].x,-(float)g->p[1].y);
}
void fight_init(Fight *g) { memset(g,0,sizeof *g);fight_random_seed(g,5489u);g->ai=1;g->max_hp=1000;fight_reset(g); }
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
  /* Dash and air-B attacks have authored variants. Until their complete
     per-character selector is ported, choose the PAT variant with a real
     attack box; the roster probe records which selection connects. */
  p->action_index=(id==408||id==409||id==418)?attack_variant(g->patterns[i],id):0;
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
static void resolve_object_hit(Fight *g,T123Object *o,const T123Pose *pose);
static unsigned object_sequence_table(const T123Pattern *pattern,int action_id,
                                      T123Sequence sequences[T123_ACTION_SEQUENCE_LIMIT]){
 unsigned count=0;
 while(count<T123_ACTION_SEQUENCE_LIMIT){
  const T123Move *move=t123_pattern_move(pattern,action_id,(int)count);
  if(!move)break;
  sequences[count++]=move->sequence;
 }
 return count;
}
static T123Object *spawn_object(Fight *g,int owner,int action_id,int move_action,unsigned sequence,int offset_x,int offset_y,int vx,int vy,int life,int follow_owner){
 const T123Move *m=t123_pattern_move(g->patterns[owner],move_action,sequence);if(!m||!m->sequence.count)return NULL;
 T123Sequence sequences[T123_ACTION_SEQUENCE_LIMIT];unsigned count=object_sequence_table(g->patterns[owner],move_action,sequences);
 if(sequence>=count)return NULL;
 for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++)if(!g->objects[i].active){T123Object *o=&g->objects[i];const Fighter *p=&g->p[owner];memset(o,0,sizeof *o);o->active=1;o->owner=owner;o->action=action_id;o->sequence=(int)sequence;o->owner_action=p->action;o->offset_x=offset_x;o->offset_y=offset_y;o->follow_owner=follow_owner;o->x=p->x+p->face*offset_x;o->y=p->y+offset_y;o->world_x=(float)o->x;o->world_y=(float)o->y;o->vx=p->face*vx;o->vy=vy;o->life=life;t123_animation_set(&o->animation,sequences,(uint16_t)count,(uint16_t)sequence);++g->object_spawns;return o;}
 return NULL;
}
static int spawn_remilia_412_object(Fight *g,int owner){
 /* PE probe: action 412 requests object 801 at parent update 16. The x86
    spawn is (+83,+180), then (-11.2763,+4.10425) per tick facing right.
    Use full world units and Q16 precision, as for the Suika objects. */
 /* The first update is deferred by the manager after creation, so 72
    countdown steps reproduce the original +0x34c retirement at tick 73. */
 T123Object *o=spawn_object(g,owner,801,801,0,83,180,0,0,72,0);if(!o)return 0;
 const Fighter *p=&g->p[owner];o->fractional_motion=1;o->motion_scale=65536;
 o->persist_after_hit=1;
 o->x_q=(p->x+p->face*83)*65536;o->y_q=(p->y+180)*65536;
 /* Executed PE first step: (403,360) -> (391.72369384765625,
    364.104248046875), exactly representable at this precision. */
 o->vx_q=-p->face*739004;o->vy_q=268976;
 return 1;
}
static int spawn_remilia_801_trail(Fight *g,const T123Object *source){
 /* The original 801 seq.0 update requests seq.1 at its current position on
    update 1 and every third update after that. Seq.1 has no attack boxes. */
 T123Object *trail=spawn_object(g,source->owner,801,801,1,0,0,0,0,17,0);
 if(!trail)return 0;
 trail->owner_action=412;
 if(source->fractional_motion){
  trail->fractional_motion=1;
  trail->motion_scale=source->motion_scale;
  trail->x_q=source->x_q;trail->y_q=source->y_q;
  trail->x=source->x;trail->y=source->y;
  trail->world_x=source->world_x;trail->world_y=source->world_y;
 }else{trail->x=(float)source->x;trail->y=(float)source->y;}
 const T123Move *move=t123_pattern_move(g->patterns[source->owner],801,1);
 if(move&&move->sequence.count>1&&move->sequence.durations){
  trail->animation.pose=1;
  trail->animation.duration=move->sequence.durations[1];
 }
 return 1;
}
static void spawn_dash_object(Fight *g,int owner){
 int c=g->character[owner],id=g->p[owner].action;
 if(c==3&&id==408)spawn_object(g,owner,849,849,19,60,100,0,0,90,1);
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
static T123Object *spawn_suika_531_projectile(Fight *g,int owner){
 const Fighter *p=&g->p[owner];
 T123Object *projectile=spawn_object(g,owner,821,821,0,100,0,0,0,26,0);
 if(!projectile)return NULL;
 projectile->fractional_motion=1;projectile->motion_scale=65536;
 projectile->x_q=(p->x+p->face*100)*65536;projectile->y_q=p->y*65536;
 projectile->vx_q=-p->face*2155429;projectile->vy_q=784512;projectile->gravity_q=-32768;
 projectile->world_x=(float)projectile->x_q/65536.0f;projectile->world_y=(float)projectile->y_q/65536.0f;
 projectile->persist_after_hit=1;projectile->alpha=255;projectile->alpha_fade=10;
 T123Object *effect=spawn_object(g,owner,821,821,1,100,0,0,0,26,0);
 if(effect){effect->fractional_motion=1;effect->motion_scale=65536;effect->x_q=projectile->x_q;effect->y_q=projectile->y_q;effect->vy_q=0;effect->gravity_q=-32768;effect->world_x=projectile->world_x;effect->world_y=projectile->world_y;effect->alpha=255;effect->alpha_fade=10;}
 return projectile;
}
static T123Object *spawn_suika_530_burst(Fight *g,int owner){
 const Fighter *p=&g->p[owner];
 const T123Move *move=t123_pattern_move(g->patterns[owner],821,0);
 if(!move||!move->sequence.count)return NULL;
 int free_slot=0;
 for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++)if(!g->objects[i].active){free_slot=1;break;}
 if(!free_slot)return NULL;
 /* The x86 0x79aef3 branch draws 0..60, 0..5, 0..5 and 0..360
    from the global MT19937 stream. The first draw offsets the vertical
    spawn; the other three initialize the object's authored motion state. */
 unsigned vertical_random=fight_random_range(g,60);
 (void)fight_random_range(g,5);
 (void)fight_random_range(g,5);
 (void)fight_random_range(g,360);
 const float radians=0.01745329251994329577f;
 float x=(float)p->x+(float)p->face*sinf(80.0f*radians)*25.0f;
 float y=(float)p->y+100.0f+sinf(-10.0f*radians)*25.0f*0.2f+(30.0f-(float)vertical_random);
 T123Object *object=spawn_object(g,owner,821,821,0,0,0,0,0,1,0);
 if(!object)return NULL;
 object->world_x=x;object->world_y=y;object->x=(int)x;object->y=(int)y;
 /* The original sequence-0 burst has alpha 0 and retires before its next
    active update; its authored PAT box remains live for the creation frame. */
 object->alpha=0;
 return object;
}
static void update_objects(Fight *g){
 for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++){T123Object *o=&g->objects[i];if(!o->active)continue;T123Sequence sequences[T123_ACTION_SEQUENCE_LIMIT];unsigned count=object_sequence_table(g->patterns[o->owner],o->action,sequences);if(o->animation.sequence>=count){o->active=0;continue;}o->sequence=o->animation.sequence;const T123Move *m=t123_pattern_move(g->patterns[o->owner],o->action,o->sequence);if(!m){o->active=0;continue;}
  if(o->action==801&&o->sequence==0&&o->owner_action==412&&g->character[o->owner]==6&&
     (o->age==0||(o->age%3u)==0))spawn_remilia_801_trail(g,o);
   /* The Suika 623B burst has life=1: the PE tests its authored box in the
      factory/creation frame, then removes it at the start of the next object
      update, before another collision or animation tick. */
   if(o->action==821&&o->owner_action==530&&o->age>0){o->active=0;continue;}
   if(!o->age){o->age=1;if(o->action==821&&m->poses&&o->animation.pose<m->sequence.count)resolve_object_hit(g,o,&m->poses[o->animation.pose]);continue;}
   /* Other Suika 821 projectiles expire before movement on manager update 27. */
  if(o->action==821&&o->life<=1){o->active=0;continue;}
  const Fighter *owner=&g->p[o->owner];
  if(o->follow_owner&&owner->action==o->owner_action){o->x=owner->x+owner->face*o->offset_x;int anchor_y=o->offset_y;if(o->action==849&&owner->action==418)anchor_y=60;o->y=owner->y+anchor_y;o->world_x=(float)o->x;o->world_y=(float)o->y;}
  else if(o->fractional_motion){int qscale=o->motion_scale?o->motion_scale:16;o->follow_owner=0;o->x_q+=o->vx_q;if(o->action==821)o->vy_q+=o->gravity_q;o->y_q+=o->vy_q;if(o->action!=821)o->vy_q+=o->gravity_q;o->world_x=(float)o->x_q/(float)qscale;o->world_y=(float)o->y_q/(float)qscale;o->x=o->x_q/qscale;o->y=o->y_q/qscale;}
  else{o->follow_owner=0;o->x+=o->vx;o->y+=o->vy;o->world_x=(float)o->x;o->world_y=(float)o->y;}
  if(o->alpha_fade>0){o->alpha-=o->alpha_fade;if(o->alpha<0)o->alpha=0;}
  ++o->age;if(o->life>0&&--o->life==0){o->active=0;continue;}
  int ended=t123_animation_tick(&o->animation,sequences,(uint16_t)count);if(ended<0||ended==1){o->active=0;continue;}
  o->sequence=o->animation.sequence;m=t123_pattern_move(g->patterns[o->owner],o->action,o->sequence);if(!m){o->active=0;continue;}
  if(!m->poses||o->animation.pose>=m->sequence.count)continue;
  resolve_object_hit(g,o,&m->poses[o->animation.pose]);
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
static int motion_skill_action(const Fight *g,int i){
 /* The pinned x86 Suika dispatcher implements both motion skills with the
    same level gates. C selects 521/526/531; B selects 520/525/530. */
 if(g->character[i]!=9)return -1;
 const Fighter *p=&g->p[i];
 int command_c=t123_input_match(&g->input_history[i],"623C",15,(int8_t)p->face)>0;
 int command_b=t123_input_match(&g->input_history[i],"623B",15,(int8_t)p->face)>0;
 if(command_c||command_b){
  if(p->skill_level_5>0&&p->skill_level_9>0)return -1;
  int action_id=command_c?
      (p->skill_level_9>0?531:p->skill_level_5>0?526:521):
      (p->skill_level_9>0?530:p->skill_level_5>0?525:520);
  if(t123_pattern_move(g->patterns[i],action_id,0))return action_id;
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
 /* PE 004640b0 transforms local PAT rectangles in full world units.
    Camera zoom belongs only to rendering, never to contact resolution. */
 int al=pa->x+(pa->face>0?a->left:-a->right),ar=pa->x+(pa->face>0?a->right:-a->left);
 int bl=pb->x+(pb->face>0?b->left:-b->right),br=pb->x+(pb->face>0?b->right:-b->left);
 int at=-pa->y+a->up,ab=-pa->y+a->down,bt=-pb->y+b->up,bb=-pb->y+b->down;
 return al<br && bl<ar && at<bb && bt<ab;
}
static int overlap_world(const T123Box *a,float ax,float ay,int aface,
                         const T123Box *b,const Fighter *pb){
 ax=ceilf(ax);ay=ceilf(ay);
 float al=ax+(aface>0?a->left:-a->right);
 float ar=ax+(aface>0?a->right:-a->left);
 float bl=(float)pb->x+(pb->face>0?b->left:-b->right);
 float br=(float)pb->x+(pb->face>0?b->right:-b->left);
 float at=-ay+a->up,ab=-ay+a->down;
 float bt=-(float)pb->y+b->up,bb=-(float)pb->y+b->down;
 return al<br&&bl<ar&&at<bb&&bt<ab;
}
static void resolve_object_hit(Fight *g,T123Object *o,const T123Pose *pose){
 if(o->hit_done||!pose||!pose->damage||!pose->attack_count||!g->p[1-o->owner].hp)return;
 Fighter *victim=&g->p[1-o->owner];
 for(unsigned a=0;a<pose->attack_count;a++){
  T123Box box=pose->attack[a];Fighter object_anchor=g->p[o->owner];
  if(o->action!=821&&o->action!=801){
   int dx=(o->x-g->p[o->owner].x)*g->p[o->owner].face;
   box.left+=dx;box.right+=dx;
   box.up+=g->p[o->owner].y-o->y;box.down+=g->p[o->owner].y-o->y;
  }
  const T123Pose *defender=fight_pose(g,1-o->owner);if(!defender)break;
  for(unsigned b=0;b<defender->hurt_count;b++)if((o->action==821||o->action==801)?
      overlap_world(&box,o->world_x,o->world_y,g->p[o->owner].face,&defender->hurt[b],victim):
      overlap(&box,&object_anchor,&defender->hurt[b],victim)){
   victim->hp-=victim->guard?pose->chip:pose->damage;if(victim->hp<0)victim->hp=0;
   victim->stun=victim->guard?pose->block_stun:(o->action==821?20:pose->enemy_stun);if(victim->stun<1)victim->stun=1;
   int reaction=victim->guard?(victim->y?158:150):(victim->y?70:50);
   if(t123_pattern_move(g->patterns[1-o->owner],reaction,0)){
    if(o->action==821&&o->owner_action==530){
     /* PE hit-response selects the authored action but preserves the 20
        frame reaction timer written by the object pair resolver. */
     victim->action=reaction;victim->action_ticks=0;victim->hit_done=0;
     victim->object_counter=0;victim->dash_ticks=0;
    }else action(g,1-o->owner,reaction);
   }
   ++g->p[o->owner].hits;
   if(o->owner_action>=400&&o->owner_action<410)++g->p[o->owner].b_hits;
   else if(o->owner_action>=410&&o->owner_action<420)++g->p[o->owner].c_hits;
   if(o->persist_after_hit)o->hit_done=1;else o->active=0;
   return;
  }
 }
}
static void separate(Fight *g){
 const T123Pose *a=fight_pose(g,0),*b=fight_pose(g,1);
 if(!a||!b||!a->collision_count||!b->collision_count)return;
 if(!overlap(&a->collision[0],&g->p[0],&b->collision[0],&g->p[1]))return;
 int width=(a->collision[0].right-a->collision[0].left+b->collision[0].right-b->collision[0].left)/2;
 int difference=g->p[1].x-g->p[0].x,delta=width-abs(difference);if(delta<=0)return;
 int direction=difference>=0?1:-1;g->p[0].x-=direction*((delta+1)/2);g->p[1].x+=direction*(delta/2);
}
static void data_act(Fight *g,int i,uint32_t in,uint32_t edge){
 Fighter *p=&g->p[i];
 /* Object collision is resolved after this player's update. Preserve the
    newly-written hitstop until the next simulation tick. */
 if(p->stun&&!(p->stun==20&&(p->action==50||p->action==70))&&
    !(p->stun==20&&(p->action==158||p->action==150)))--p->stun;
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
  int command_skill=motion_skill_action(g,i);
  if(command_skill>=0&&!p->guard){
   desired=command_skill;++p->skill_uses;
   /* Original useSkill reseeds the input ring after dispatch. This prevents
      the same buffered 623C from triggering again after the action ends. */
   t123_input_history_reset(&g->input_history[i],input_sample(in));
  }
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
   if(p->skill_air_x_q<ARENA_LEFT*4)p->skill_air_x_q=ARENA_LEFT*4;
   if(p->skill_air_x_q>ARENA_RIGHT*4)p->skill_air_x_q=ARENA_RIGHT*4;
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
 if(p->x<ARENA_LEFT)p->x=ARENA_LEFT;
 if(p->x>ARENA_RIGHT)p->x=ARENA_RIGHT;
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
 if(g->character[i]==6&&p->action==412&&!p->object_counter&&previous_sequence==0&&previous_pose<4&&p->animation.sequence==0&&p->animation.pose==4&&p->animation.pose_frame==0){if(spawn_remilia_412_object(g,i))p->object_counter=1;}
 if(g->character[i]==9&&p->action==530&&!p->object_counter&&previous_sequence==0&&previous_pose<7&&p->animation.sequence==0&&p->animation.pose==7&&p->animation.pose_frame==0){if(spawn_suika_530_burst(g,i))p->object_counter=1;}
 if(g->character[i]==9&&p->action==531&&!p->object_counter&&previous_sequence==0&&previous_pose<7&&p->animation.sequence==0&&p->animation.pose==7&&p->animation.pose_frame==0){if(spawn_suika_531_projectile(g,i))p->object_counter=1;}
 if(g->character[i]==19&&p->action==418&&previous_sequence==0&&previous_pose<10&&p->animation.sequence==0&&p->animation.pose==10&&p->animation.pose_frame==0)p->object_counter=1;
 if(finished==1&&(is_attack(p->action)||p->action==3||p->action==10)){action(g,i,0);return;}
 if(finished==1&&p->action==1){action(g,i,2);return;}
 p->attack=is_attack(p->action);
 if(p->attack&&!p->hit_done&&(p->action==408&&p->animation.current_frame==1))spawn_dash_object(g,i);
 if(p->attack&&!p->hit_done&&p->action==418&&g->character[i]==3&&p->animation.current_frame>=2&&p->animation.current_frame<=5)spawn_dash_object(g,i);
 const T123Pose *f=fight_pose(g,i),*v=fight_pose(g,1-i);Fighter *victim=&g->p[1-i];
 if(!f||!v||!victim->hp)return;
 /* Multi-hit skills can author separate active windows in different PAT
    sequences. Rearm only after leaving a damaging pose so a held hitbox does
    not repeat damage every frame, while later authored windows can connect. */
 if(is_skill_action(p->action)&&p->hit_done&&(!f->damage||!f->attack_count))p->hit_done=0;
 if(p->hit_done||!f->damage)return;
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
    if(g->patterns[0]&&g->patterns[1]){t123_input_history_push(&g->input_history[0],input_sample(in));t123_input_history_push(&g->input_history[1],input_sample(cpu));data_act(g,0,in,edge);data_act(g,1,cpu,cpu);separate(g);update_objects(g);update_camera(g);++g->frame;return;}
    act(g,0,in,edge); act(g,1,cpu,cpu);
    for(int j=0;j<16;j++) {
        Shot *s=&g->shots[j]; if(!s->active) continue;
        s->x+=s->vx; Fighter *v=&g->p[1-s->owner];
        if(abs(s->x-v->x)<24 && s->y>=v->y && s->y<=v->y+92) {hit(v,&g->p[s->owner],55);s->active=0;}
        if(s->x<0 || s->x>640) s->active=0;
    }
    update_camera(g);++g->frame;
}
uint32_t fight_digest(const Fight *g) {
    uint32_t h=2166136261u;
    for(int i=0;i<2;i++) {
        const Fighter *p=&g->p[i];
        const int fields[]={p->x,p->y,p->vy,p->hp,p->cooldown,p->stun,p->dash_ticks,p->object_counter,p->skill_card_id,p->action_ticks,p->skill_level_5,p->skill_level_9,p->skill_air_x_q,p->skill_air_vx_q,p->skill_air_y_q,p->skill_air_vy_q,p->skill_air_active,(int)p->hits,(int)p->a_hits,(int)p->b_hits,(int)p->c_hits,(int)p->dashes,(int)p->skill_uses};
        for(unsigned j=0;j<sizeof fields/sizeof fields[0];j++) h=(h^(uint32_t)fields[j])*16777619u;
        const T123InputHistory *history=&g->input_history[i];
        h=(h^history->count)*16777619u;h=(h^history->next)*16777619u;
        for(unsigned j=0;j<T123_INPUT_HISTORY_CAPACITY;j++)h=(h^history->samples[j])*16777619u;
    }
    h=(h^g->object_spawns)*16777619u;
    h=(h^g->random_index)*16777619u;
    for(unsigned i=0;i<624;i++)h=(h^g->random_words[i])*16777619u;
    for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++){const T123Object *o=&g->objects[i];const int fields[]={o->active,o->owner,o->action,o->sequence,o->owner_action,o->x,o->y,o->vx,o->vy,o->age,o->life,o->follow_owner,o->offset_x,o->offset_y,o->x_q,o->y_q,o->vx_q,o->vy_q,o->fractional_motion,o->hit_done,o->persist_after_hit,o->motion_scale,o->gravity_q,o->alpha,o->alpha_fade,o->animation.pose,o->animation.pose_frame};for(unsigned j=0;j<sizeof fields/sizeof fields[0];j++)h=(h^(uint32_t)fields[j])*16777619u;}
    return h;
}
