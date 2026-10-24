#include "input_map.h"
#include <limits.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x); return 1; } } while(0)
int main(int argc,char **argv) {
    if (argc==2 && !strcmp(argv[1],"dump")) {
        for (int i=0;i<512;++i) printf("%d %u\n",i,dik_from_sdl_scancode(i));
        return 0;
    }
    const uint8_t letters[]={0x1e,0x30,0x2e,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,0x32,0x31,0x18,0x19,0x10,0x13,0x1f,0x14,0x16,0x2f,0x11,0x2d,0x15,0x2c};
    for (int i=0;i<26;++i) CHECK(dik_from_sdl_scancode(4+i)==letters[i]);
    for (int i=0;i<10;++i) CHECK(dik_from_sdl_scancode(30+i)==i+2);
    CHECK(dik_from_sdl_scancode(40)==0x1c && dik_from_sdl_scancode(41)==1);
    CHECK(dik_from_sdl_scancode(225)==0x2a && dik_from_sdl_scancode(229)==0x36);
    CHECK(dik_from_sdl_scancode(79)==0xcd && dik_from_sdl_scancode(80)==0xcb);
    CHECK(dik_from_sdl_scancode(81)==0xd0 && dik_from_sdl_scancode(82)==0xc8);
    const int unmapped[]={INT_MIN,-1,0,1,2,3,107,176,257,511,512,INT_MAX};
    for (unsigned i=0;i<sizeof unmapped/sizeof unmapped[0];++i) CHECK(!dik_from_sdl_scancode(unmapped[i]));
    const uint32_t buttons[]={0x10,0x40,0x80,0x20,0x4000,0x2000,0x8000,0x1000,0x100,0x200,8};
    const uint8_t keys[]={0xc8,0xd0,0xcb,0xcd,0x2c,0x2d,0x2e,0x1e,0x1f,0x20,0x10};
    for (unsigned mask=0;mask<2048;++mask) {
        uint8_t guarded[258],expected[256]={0};memset(guarded,0xaa,sizeof guarded);
        uint32_t pressed=0;
        for (unsigned i=0;i<11;++i) if (mask&(1u<<i)) { pressed|=buttons[i];expected[keys[i]]=0x80; }
        dik_state_from_vita_buttons(pressed,guarded+1);
        CHECK(guarded[0]==0xaa && guarded[257]==0xaa);
        CHECK(!memcmp(guarded+1,expected,256));
    }
    uint8_t state[256];dik_state_from_vita_buttons(UINT32_MAX,state);
    dik_state_from_vita_buttons(1u<<31,state);
    for (unsigned i=0;i<256;++i) CHECK(!state[i]);
    dik_state_from_vita_buttons(0,NULL);
    puts("PASS input mapping and 2048 Vita button combinations");return 0;
}
