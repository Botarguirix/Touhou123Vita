#include <stdio.h>
#include "t123/fight.h"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static void enter(Fight *g) {fight_init(g);g->ai=0;fight_step(g,IN_CONFIRM);fight_step(g,0);fight_step(g,IN_CONFIRM);fight_step(g,0);}
int main(void) {
    Fight g; enter(&g); CHECK(g.scene==SCENE_FIGHT);
    for(int i=0;i<20;i++) fight_step(&g,IN_RIGHT);
    CHECK(g.p[0].x==250);
    fight_step(&g,IN_JUMP); CHECK(g.p[0].y>0);
    for(int i=0;i<40;i++) fight_step(&g,0);
    CHECK(g.p[0].y==0 && g.p[0].vy==0);
    for(int i=0;i<400;i++) fight_step(&g,IN_LEFT);
    CHECK(g.p[0].x==35);
    fight_reset(&g);g.p[1].x=250;fight_step(&g,IN_MELEE);
    for(int i=0;i<5;i++) fight_step(&g,0);
    CHECK(g.p[1].hp==910 && g.p[0].hits==1);
    for(int i=0;i<20;i++) fight_step(&g,IN_MELEE);
    CHECK(g.p[0].hits==1); /* holding attack cannot retrigger */
    fight_reset(&g);fight_step(&g,0);fight_step(&g,IN_SHOT);
    for(int i=0;i<40;i++) fight_step(&g,0);
    CHECK(g.p[1].hp==945);
    fight_step(&g,IN_RESET);CHECK(g.p[0].hp==1000 && g.p[1].hp==1000);
    Fight a,b;enter(&a);enter(&b);a.ai=b.ai=1;
    for(int i=0;i<3600;i++){unsigned in=i%80<35?IN_RIGHT:IN_LEFT;if(i%47==0)in|=IN_SHOT;fight_step(&a,in);fight_step(&b,in);}
    CHECK(fight_digest(&a)==fight_digest(&b));
    CHECK(a.p[0].hp>=0 && a.p[1].hp>=0);
    fight_step(&g,IN_BACK);CHECK(g.scene==SCENE_PRACTICE);
    return 0;
}
