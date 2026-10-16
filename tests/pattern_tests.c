#include "t123/pattern.h"
#include <stdio.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"%d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(void){
 unsigned char data[249]={0};data[0]=5;data[1]=1;memcpy(data+3,"blank.bmp",10);data[131]=1;data[143]=1;data[144]=1;data[156]=1;data[158]=1;data[164]=2;
 T123Pattern p;CHECK(t123_pattern_decode(data,sizeof data,&p)==0);
 const T123Move *m=t123_pattern_move(&p,0,0);CHECK(m&&m->sequence.count==1&&m->sequence.durations[0]==2&&m->poses[0].image==0);
 CHECK(t123_pattern_move(&p,1,0)==NULL);t123_pattern_free(&p);
 for(unsigned i=0;i<sizeof data;i++)CHECK(t123_pattern_decode(data,i,&p)==-1);
 data[148]=1;CHECK(t123_pattern_decode(data,sizeof data,&p)==-1);data[148]=0;
 data[216]=255;CHECK(t123_pattern_decode(data,sizeof data,&p)==-1);
 return 0;
}
