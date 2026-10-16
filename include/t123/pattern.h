#ifndef T123_PATTERN_H
#define T123_PATTERN_H
#include "t123/resources.h"
#include "t123/animation.h"
#define T123_BOX_LIMIT 16
typedef struct {int32_t left,up,right,down;} T123Box;
typedef struct {
 uint16_t image,tx,ty,tw,th,duration,damage,chip,hit_stop,enemy_stun,block_stun;
 int16_t ox,oy;
 uint32_t flags,attack_flags;
 unsigned collision_count,hurt_count,attack_count;
 T123Box collision[T123_BOX_LIMIT];
 T123Box hurt[T123_BOX_LIMIT],attack[T123_BOX_LIMIT];
} T123Pose;
typedef struct {int32_t action;uint16_t index,move_lock,action_lock;T123Sequence sequence;T123Pose *poses;} T123Move;
typedef struct {int32_t action,target;} T123Alias;
typedef struct {
 uint32_t image_count,move_count,alias_count;char (*images)[129];T123Move *moves;T123Alias *aliases;
} T123Pattern;
int t123_pattern_decode(const unsigned char *bytes,size_t size,T123Pattern *out);
void t123_pattern_free(T123Pattern *pattern);
int t123_resource_pattern(T123Resources *bank,const char *name,T123Pattern *out);
const T123Move *t123_pattern_move(const T123Pattern *pattern,int action,unsigned sequence);
#endif
