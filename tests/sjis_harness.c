#include "sjis.h"
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x); return 1; } } while(0)
int main(int argc, char **argv) {
    if (argc==3 && !strcmp(argv[1],"dump")) {
        FILE *dump=fopen(argv[2],"wb"); if (!dump) return 2;
        /* Registro de ancho fijo: longitud, dos unidades UTF-16 para 1/2 bytes;
         * despues longitud, bytes empaquetados y used_default para cada BMP. */
        for (unsigned n=0;n<65792;++n) {
            uint8_t in[2]; uint16_t out[2]={0,0};
            int len=n<256 ? 1:2; unsigned x=n<256 ? n:n-256;
            in[0]=(uint8_t)(len==1 ? x:x>>8); in[1]=(uint8_t)x;
            uint16_t row[3]; row[0]=(uint16_t)sjis_to_utf16(in,len,out,2);
            row[1]=out[0];row[2]=out[1];
            if (fwrite(row,sizeof row,1,dump)!=1) return 2;
        }
        for (unsigned n=0;n<65536;++n) {
            uint16_t in=(uint16_t)n;uint8_t out[2]={0,0};int used=0;
            uint16_t row[3];row[0]=(uint16_t)utf16_to_sjis(&in,1,out,2,&used);
            row[1]=(uint16_t)(out[0]|out[1]<<8);row[2]=(uint16_t)used;
            if (fwrite(row,sizeof row,1,dump)!=1) return 2;
        }
        return fclose(dump)!=0;
    }
    const uint8_t s[]={0x82,0xa0,0,0x41}; uint16_t w[6]={0}; uint8_t b[6]={0}; int used;
    CHECK(sjis_to_utf16(s,-1,NULL,0)==2);
    CHECK(sjis_to_utf16(s,-1,w,6)==2 && w[0]==0x3042 && w[1]==0);
    CHECK(utf16_to_sjis(w,-1,NULL,0,&used)==3 && !used);
    CHECK(utf16_to_sjis(w,-1,b,6,&used)==3 && !memcmp(b,s,3));
    CHECK(sjis_to_utf16(s,4,w,6)==3 && w[2]=='A');
    w[0]=0xbeef;CHECK(sjis_to_utf16(s,4,w,1)==0 && w[0]==0xbeef);
    CHECK(sjis_to_utf16(NULL,1,w,6)==0 && sjis_to_utf16(s,0,w,6)==0);
    CHECK(utf16_to_sjis(NULL,1,b,6,&used)==0);
    uint16_t surrogate[]={0xd800,0xdc00,0x2016,0};
    CHECK(utf16_to_sjis(surrogate,-1,b,6,&used)==4 && used && !memcmp(b,"???",4));
    puts("PASS sjis contracts");return 0;
}
