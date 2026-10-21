#include "t123/pattern.h"
#include <stdlib.h>
#include <string.h>
typedef struct {const unsigned char *p;size_t left;int error;} Reader;
static const unsigned char *take(Reader *r,size_t n){if(n>r->left){r->error=1;return NULL;}const unsigned char *p=r->p;r->p+=n;r->left-=n;return p;}
static uint32_t read_int(Reader *r,unsigned n){const unsigned char *p=take(r,n);if(!p)return 0;uint32_t v=0;for(unsigned i=0;i<n;i++)v|=(uint32_t)p[i]<<(i*8);return v;}
static uint16_t get16(const unsigned char *p){return (uint16_t)(p[0]|((uint16_t)p[1]<<8));}
static int boxes(Reader *r,T123Box *out,unsigned *count,int extra){
 unsigned n=read_int(r,1);if(n>T123_BOX_LIMIT)return -1;if(count)*count=n;
 for(unsigned i=0;i<n;i++){
  T123Box b;b.left=(int32_t)read_int(r,4);b.up=(int32_t)read_int(r,4);b.right=(int32_t)read_int(r,4);b.down=(int32_t)read_int(r,4);
  if(out)out[i]=b;
  if(extra && read_int(r,1)){if(!take(r,16))return -1;}
 }
 return r->error?-1:0;
}
void t123_pattern_free(T123Pattern *p){
 for(uint32_t i=0;i<p->move_count;i++){free(p->moves[i].poses);free((void*)p->moves[i].sequence.durations);}
 free(p->moves);free(p->images);free(p->aliases);memset(p,0,sizeof *p);
}
int t123_pattern_decode(const unsigned char *data,size_t size,T123Pattern *p){
 memset(p,0,sizeof *p);Reader r={data,size,0};if(!data||read_int(&r,1)!=5)return -1;
 uint32_t images=read_int(&r,2);if(!images||images>8192||r.error)return -1;
 p->images=calloc(images,sizeof *p->images);if(!p->images)return -1;p->image_count=images;
 for(uint32_t i=0;i<images;i++){
  const unsigned char *name=take(&r,128);if(!name)goto fail;
  memcpy(p->images[i],name,128);
  p->images[i][128]=0;
 }
 uint32_t declared=read_int(&r,4);if(!declared||declared>16384||r.error)goto fail;
 p->moves=calloc(declared,sizeof *p->moves);p->aliases=calloc(declared,sizeof *p->aliases);if(!p->moves||!p->aliases)goto fail;
 int32_t action=-1;uint16_t index=0;
 while(r.left){
  int32_t id=(int32_t)read_int(&r,4);if(r.error)goto fail;
  if(id==-1){if(p->alias_count>=declared)goto fail;T123Alias *a=&p->aliases[p->alias_count++];a->action=(int32_t)read_int(&r,4);a->target=(int32_t)read_int(&r,4);continue;}
  if(id==-2){if(action<0||index==65535)goto fail;++index;}else{
   if(id<0)goto fail;
   action=id;index=0;
   /* Later definitions replace the entire earlier action, including its sequences. */
   for(uint32_t i=0;i<p->move_count;){
    if(p->moves[i].action==action){free(p->moves[i].poses);free((void*)p->moves[i].sequence.durations);memmove(p->moves+i,p->moves+i+1,(p->move_count-i-1)*sizeof *p->moves);--p->move_count;}
    else ++i;
   }
  }
  if(p->move_count>=declared)goto fail;
  T123Move *m=&p->moves[p->move_count++];m->action=action;m->index=index;
  m->move_lock=(uint16_t)read_int(&r,2);m->action_lock=(uint16_t)read_int(&r,2);m->sequence.loop=(uint16_t)read_int(&r,1);
  uint32_t frames=read_int(&r,4);if(!frames||frames>4096||r.error)goto fail;
  m->sequence.count=(uint16_t)frames;m->poses=calloc(frames,sizeof *m->poses);uint16_t *durations=calloc(frames,2);m->sequence.durations=durations;
  if(!m->poses||!durations)goto fail;
  for(uint32_t j=0;j<frames;j++){
   T123Pose *f=&m->poses[j];const unsigned char *v=take(&r,19);if(!v)goto fail;
   f->image=get16(v);f->tx=(int16_t)get16(v+4);f->ty=(int16_t)get16(v+6);f->tw=(int16_t)get16(v+8);f->th=(int16_t)get16(v+10);f->ox=(int16_t)get16(v+12);f->oy=(int16_t)get16(v+14);f->duration=get16(v+16);durations[j]=f->duration;
   if(f->image>=images||v[18]>2)goto fail;
   if(v[18]==2 && !take(&r,16))goto fail;
   v=take(&r,40);if(!v)goto fail;
   f->damage=get16(v);f->chip=get16(v+4);f->hit_stop=get16(v+14);f->enemy_stun=get16(v+16);f->block_stun=get16(v+20);
   read_int(&r,1);f->flags=read_int(&r,4);f->attack_flags=read_int(&r,4);
   if(boxes(&r,f->collision,&f->collision_count,0)||boxes(&r,f->hurt,&f->hurt_count,0)||boxes(&r,f->attack,&f->attack_count,1))goto fail;
   v=take(&r,T123_POSE_EFFECT_BYTES);if(!v)goto fail;memcpy(f->effect_data,v,T123_POSE_EFFECT_BYTES);
  }
 }
 if(r.error||!p->move_count)goto fail;
 return 0;
fail:t123_pattern_free(p);return -1;
}
const T123Move *t123_pattern_move(const T123Pattern *p,int action,unsigned index){
 for(unsigned depth=0;depth<32;depth++){
  for(uint32_t i=p->move_count;i>0;i--)if(p->moves[i-1].action==action&&p->moves[i-1].index==index)return &p->moves[i-1];
  int found=0;for(uint32_t i=0;i<p->alias_count;i++)if(p->aliases[i].action==action){action=p->aliases[i].target;found=1;break;}
  if(!found)return NULL;
 }
 return NULL;
}
static unsigned variant_count(const T123Pattern *p,int action,unsigned depth){
 if(depth>=32)return 0;
 unsigned count=0;
 for(uint32_t i=0;i<p->move_count;i++)if(p->moves[i].action==action)++count;
 if(!count)for(uint32_t i=0;i<p->alias_count;i++)if(p->aliases[i].action==action)return variant_count(p,p->aliases[i].target,depth+1);
 return count;
}
unsigned t123_pattern_variant_count(const T123Pattern *p,int action){return variant_count(p,action,0);}
int t123_pattern_sequences(const T123Pattern *p,int action,T123Sequence *out,unsigned capacity){
 unsigned count=variant_count(p,action,0);if(!count)return 0;if(!out||count>capacity)return -1;
 for(unsigned i=0;i<count;i++){const T123Move *m=t123_pattern_move(p,action,i);if(!m)return -1;out[i]=m->sequence;}
 return (int)count;
}
static uint64_t attack_score(const T123Move *m){
 uint64_t score=0;
 for(unsigned frame=0;frame<m->sequence.count;frame++){
  const T123Pose *pose=&m->poses[frame];
  if(!pose->damage||!pose->attack_count)continue;
  uint64_t candidate=(uint64_t)pose->damage*pose->attack_count;
  score+=candidate;
 }
 return score;
}
static const T123Move *best_attack(const T123Pattern *p,int action,unsigned *variant_index,unsigned depth){
 if(depth>=32)return NULL;
 const T123Move *best=NULL;uint64_t best_score=0;unsigned best_index=0;
 for(uint32_t i=0;i<p->move_count;i++){
  const T123Move *m=&p->moves[i];if(m->action!=action)continue;
  uint64_t score=attack_score(m);
  if(score>best_score){best=m;best_score=score;best_index=m->index;}
  else if(score&&score==best_score&&m->index<best_index){best=m;best_index=m->index;}
 }
 if(variant_index)*variant_index=best?best_index:0;
 if(!best)for(uint32_t i=0;i<p->alias_count;i++)if(p->aliases[i].action==action){
  unsigned nested=0;best=best_attack(p,p->aliases[i].target,&nested,depth+1);
  if(best&&variant_index)*variant_index=nested;
  return best;
 }
 return best;
}
const T123Move *t123_pattern_best_attack(const T123Pattern *p,int action,unsigned *variant_index){return best_attack(p,action,variant_index,0);}
int t123_resource_pattern(T123Resources *b,const char *name,T123Pattern *p){
 unsigned char *bytes=NULL;size_t size=0;if(t123_resource_read(b,name,&bytes,&size))return -1;
 int result=t123_pattern_decode(bytes,size,p);free(bytes);return result;
}
