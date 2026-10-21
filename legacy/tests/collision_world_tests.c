#include <stdio.h>
#include "t123/fight.h"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)

static int damage_at(int x0,int x1,float zoom){
    uint16_t duration=30000;
    T123Pose idle={0},attack={0};
    idle.hurt_count=1;idle.hurt[0]=(T123Box){-10,-120,10,0};
    attack=idle;attack.damage=200;attack.enemy_stun=16;
    attack.attack_count=1;attack.attack[0]=(T123Box){-40,-120,80,0};
    T123Move moves[2]={
        {0,0,100,100,{1,1,&duration},&idle},
        {300,0,100,100,{1,1,&duration},&attack}
    };
    T123Pattern pat={.moves=moves,.move_count=2};
    Fight g;fight_init(&g);fight_bind_patterns(&g,&pat,&pat);
    g.scene=SCENE_FIGHT;g.ai=0;g.p[0].x=x0;g.p[1].x=x1;
    g.camera.zoom=zoom;
    fight_step(&g,IN_MELEE);
    return g.max_hp-g.p[1].hp;
}

static int symmetric_body_separation(void){
    uint16_t duration=30000;T123Pose idle={0};
    idle.collision_count=1;idle.collision[0]=(T123Box){-20,-100,20,0};
    T123Move move={0,0,100,100,{1,1,&duration},&idle};
    T123Pattern pat={.moves=&move,.move_count=1};
    Fight g;fight_init(&g);fight_bind_patterns(&g,&pat,&pat);
    g.scene=SCENE_FIGHT;g.ai=0;g.p[0].x=480;g.p[1].x=510;
    fight_step(&g,0);
    CHECK(g.p[0].x==475&&g.p[1].x==515);
    g.p[0].x=800;g.p[1].x=770;
    fight_step(&g,0);
    CHECK(g.p[0].x==805&&g.p[1].x==765);
    return 0;
}

int main(void){
    /* Original PE attack at x=480 covers [440,560]. Defender at 550
       covers [540,560]; at 580 there is a clear ten-unit gap. */
    CHECK(damage_at(480,550,1)==200);
    CHECK(damage_at(480,580,1)==0);
    CHECK(damage_at(800,730,1)==200);
    CHECK(damage_at(800,700,1)==0);
    CHECK(damage_at(480,550,0.5f)==200);
    CHECK(symmetric_body_separation()==0);
    puts("World-unit PAT contact, mirrored facing and zoom independence passed");
    return 0;
}
