/* Portable reconstruction of the pose/sequence counter contract.
 * Reference addresses and independent x86 comparison are documented in docs/KERNEL.md.
 * Graphics refresh and character-specific update logic are deliberately outside this kernel.
 */
#include "t123/animation.h"
static int refresh(T123Animation *s,const T123Sequence *sequences,uint16_t count){
 if(s->sequence>=count)return -1;
 const T123Sequence *q=&sequences[s->sequence];
 if(!q->count || !q->durations || s->pose>=q->count)return -1;
 s->pose_frame=0;s->duration=q->durations[s->pose];return 0;
}
int t123_animation_set(T123Animation *s,const T123Sequence *q,uint16_t count,uint16_t sequence){
 if(!s || !q || sequence>=count || !q[sequence].count || !q[sequence].durations)return -1;
 s->sequence=sequence;s->pose=0;s->current_frame=0;return refresh(s,q,count);
}
int t123_animation_tick(T123Animation *s,const T123Sequence *q,uint16_t count){
 if(!s || !q || s->sequence>=count || !q[s->sequence].count || s->pose>=q[s->sequence].count)return -1;
 ++s->current_frame;s->pose_frame=(uint16_t)(s->pose_frame+1u);
 if((int16_t)s->pose_frame < (int16_t)s->duration)return 0;
 s->pose=(uint16_t)((s->pose+1u)%q[s->sequence].count);
 if(refresh(s,q,count)<0)return -1;
 if(s->pose || q[s->sequence].loop)return 0;
 s->sequence=(uint16_t)((s->sequence+1u)%count);s->current_frame=0;s->pose=0;
 if(refresh(s,q,count)<0)return -1;
 return s->sequence==0;
}
