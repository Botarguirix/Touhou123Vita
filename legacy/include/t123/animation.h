#ifndef T123_ANIMATION_H
#define T123_ANIMATION_H
#include <stdint.h>
typedef struct {uint16_t count,loop;const uint16_t *durations;} T123Sequence;
typedef struct {
 uint16_t sequence,pose,pose_frame,duration;
 uint32_t current_frame;
} T123Animation;
int t123_animation_set(T123Animation *s,const T123Sequence *sequences,uint16_t count,uint16_t sequence);
int t123_animation_tick(T123Animation *s,const T123Sequence *sequences,uint16_t count);
#endif
