#ifndef T123_FIGHT_H
#define T123_FIGHT_H
#include <stdint.h>
#include "t123/pattern.h"
#include "t123/input.h"
#include "t123/stage.h"
enum { IN_LEFT=1, IN_RIGHT=2, IN_JUMP=4, IN_MELEE=8, IN_SHOT=16, IN_GUARD=32, IN_RESET=64, IN_CONFIRM=128, IN_BACK=256, IN_AI=512, IN_DOWN=1024, IN_C_ATTACK=2048, IN_CHANGE_CARD=4096, IN_SPELLCARD=8192 };
enum { SCENE_MENU, SCENE_PRACTICE, SCENE_FIGHT };
#define T123_ACTION_SEQUENCE_LIMIT 32
typedef struct {
 int x,y,vy,face,hp,attack,cooldown,stun,guard,action,dash_ticks,object_counter,skill_card_id,action_ticks,skill_level_5,skill_level_9;
 unsigned action_index,hits,hit_done,a_hits,b_hits,c_hits,dashes,skill_uses;
 int skill_air_x_q,skill_air_vx_q,skill_air_y_q,skill_air_vy_q,skill_air_active;
 T123Animation animation;
 T123Sequence action_sequences[T123_ACTION_SEQUENCE_LIMIT];
 uint16_t action_sequence_count;
} Fighter;
typedef struct { int active,x,y,vx,owner; } Shot;
typedef struct { int active,owner,action,sequence,owner_action,x,y,vx,vy,age,life,follow_owner,offset_x,offset_y,x_q,y_q,vx_q,vy_q,fractional_motion,hit_done,persist_after_hit,motion_scale,gravity_q,alpha,alpha_fade; float world_x,world_y; T123Animation animation; } T123Object;
typedef struct { int scene,ai,frame,rounds,max_hp; uint32_t previous; unsigned object_spawns; Fighter p[2]; Shot shots[16]; T123Object objects[16]; T123InputHistory input_history[2]; const T123Pattern *patterns[2]; int character[2]; T123StageCamera camera; uint32_t random_words[624]; unsigned random_index; } Fight;
void fight_init(Fight *g);
void fight_reset(Fight *g);
void fight_step(Fight *g, uint32_t input);
uint32_t fight_digest(const Fight *g);
void fight_bind_patterns(Fight *g,const T123Pattern *a,const T123Pattern *b);
void fight_bind_character_patterns(Fight *g,const T123Pattern *a,int character_a,const T123Pattern *b,int character_b);
const T123Pose *fight_pose(const Fight *g,int player);
#endif
