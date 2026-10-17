#include <stdio.h>
#include "t123/animation.h"
#define CHECK(x) do{if(!(x)){fprintf(stderr,"%d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(int argc,char **argv){
 if(argc==2){
  FILE *f=fopen(argv[1],"r");if(!f)return 2;
  unsigned n,a,b,loop,seq,pose,pf,cf,dt,result,es,ep,ef,ec,ed,cases=0;
  while(fscanf(f,"%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u",&n,&a,&b,&loop,&seq,&pose,&pf,&cf,&dt,&result,&es,&ep,&ef,&ec,&ed)==15){
   uint16_t d[2]={(uint16_t)a,(uint16_t)b};T123Sequence q={(uint16_t)n,(uint16_t)loop,d};
   T123Animation s={(uint16_t)seq,(uint16_t)pose,(uint16_t)pf,(uint16_t)dt,cf};
   CHECK(t123_animation_tick(&s,&q,1)==(int)result);
   CHECK(s.sequence==es && s.pose==ep && s.pose_frame==ef && s.current_frame==ec && s.duration==ed);++cases;
  }
  fclose(f);CHECK(cases>=500);printf("x86 oracle cases: %u\n",cases);return 0;
 }
 uint16_t d[]={2,3};T123Sequence q={2,1,d};T123Animation s;
 CHECK(t123_animation_set(&s,&q,1,0)==0);
 for(int i=0;i<5;i++)CHECK(t123_animation_tick(&s,&q,1)==0);
 CHECK(s.pose==0 && s.pose_frame==0 && s.current_frame==5);
 q.loop=0;CHECK(t123_animation_set(&s,&q,1,0)==0);
 for(int i=0;i<4;i++)CHECK(t123_animation_tick(&s,&q,1)==0);
 CHECK(t123_animation_tick(&s,&q,1)==1 && s.current_frame==0);
 T123Sequence invalid={0,0,d};CHECK(t123_animation_set(&s,&invalid,1,0)==-1);
 return 0;
}
