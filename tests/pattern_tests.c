#include "t123/pattern.h"
#include <stdio.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"%d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(void){
 unsigned char data[249]={0};data[0]=5;data[1]=1;memset(data+3,0,128);memcpy(data+3,"blank   .bmp",12);data[131]=1;data[143]=1;data[144]=1;data[156]=1;data[158]=1;data[164]=2;
 for(unsigned i=0;i<T123_POSE_EFFECT_BYTES;i++)data[219+i]=(unsigned char)(i+1);
 T123Pattern p;CHECK(t123_pattern_decode(data,sizeof data,&p)==0);
 CHECK(strcmp(p.images[0],"blank   .bmp")==0);
 const T123Move *m=t123_pattern_move(&p,0,0);CHECK(m&&m->sequence.count==1&&m->sequence.durations[0]==2&&m->poses[0].image==0);
 for(unsigned i=0;i<T123_POSE_EFFECT_BYTES;i++)CHECK(m->poses[0].effect_data[i]==i+1);
 CHECK(t123_pattern_move(&p,1,0)==NULL);CHECK(t123_pattern_variant_count(&p,0)==1);CHECK(t123_pattern_best_attack(&p,0,NULL)==NULL);t123_pattern_free(&p);
 {
  T123Pose poses[3]={0};uint16_t durations[3]={3,3,5};T123Move moves[3]={0};T123Pattern attacks={0};
  for(unsigned i=0;i<3;i++){moves[i].action=408;moves[i].index=(uint16_t)i;moves[i].sequence=(T123Sequence){1,1,&durations[i]};moves[i].poses=&poses[i];}
  poses[1].damage=400;poses[1].attack_count=1;poses[1].attack[0]=(T123Box){0,0,10,10};
  poses[2].damage=800;poses[2].attack_count=1;poses[2].attack[0]=(T123Box){0,0,10,10};
  attacks.moves=moves;attacks.move_count=3;unsigned selected=99;
  CHECK(t123_pattern_variant_count(&attacks,408)==3);
  T123Sequence sequences[3];
  CHECK(t123_pattern_sequences(&attacks,408,sequences,3)==3);
  CHECK(sequences[0].durations==&durations[0]&&sequences[1].durations==&durations[1]&&sequences[2].durations==&durations[2]);
  CHECK(t123_pattern_sequences(&attacks,408,sequences,2)==-1);
  CHECK(t123_pattern_sequences(&attacks,404,sequences,3)==0);
  CHECK(t123_pattern_best_attack(&attacks,408,&selected)==&moves[2]&&selected==2);
  poses[1].damage=poses[2].damage=800;
  CHECK(t123_pattern_best_attack(&attacks,408,&selected)==&moves[1]&&selected==1);
  /* Equivalent variants resolve consistently to the earliest index. */
  CHECK(selected==1);
  T123Alias aliases[2]={{500,408},{600,601}};attacks.aliases=aliases;attacks.alias_count=2;
  CHECK(t123_pattern_variant_count(&attacks,500)==3);
  CHECK(t123_pattern_sequences(&attacks,500,sequences,3)==3);
  CHECK(t123_pattern_best_attack(&attacks,500,&selected)==&moves[1]&&selected==1);
  CHECK(t123_pattern_variant_count(&attacks,600)==0);
  CHECK(t123_pattern_best_attack(&attacks,600,&selected)==NULL);
 }
 for(unsigned i=0;i<sizeof data;i++)CHECK(t123_pattern_decode(data,i,&p)==-1);
 data[148]=1;CHECK(t123_pattern_decode(data,sizeof data,&p)==-1);data[148]=0;
 data[216]=255;CHECK(t123_pattern_decode(data,sizeof data,&p)==-1);
 return 0;
}
