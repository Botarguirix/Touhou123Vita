#include "t123/resources.h"
#include <string.h>
#include <stdio.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"%d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(void){
 unsigned char cv[21]={32,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,7,19,31,255};T123Bitmap b;
 CHECK(t123_bitmap_decode(cv,sizeof cv,NULL,0,&b)==0);CHECK(b.width==1 && b.height==1 && b.pixels[0]==0xff07131fu);t123_bitmap_free(&b);
 CHECK(t123_bitmap_decode(cv,20,NULL,0,&b)==-1);
 cv[0]=8;CHECK(t123_bitmap_decode(cv,sizeof cv,NULL,0,&b)==-1);
 cv[0]=32;cv[9]=0;CHECK(t123_bitmap_decode(cv,sizeof cv,NULL,0,&b)==-1);
 T123Dat d;CHECK(t123_dat_open(&d,"this-file-does-not-exist.dat")==-1);CHECK(d.file==NULL);
 return 0;
}
