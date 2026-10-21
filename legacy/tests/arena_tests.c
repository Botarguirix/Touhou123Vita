#include <stdio.h>
#include "t123/fight.h"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)

int main(void){
    /* Minimal idle/walk data: exercise the real PAT combat path, without
       body collision or AI interfering with the wall/camera assertions. */
    const int ids[]={0,4,5};
    T123Move moves[3]={0};T123Pose poses[3]={0};uint16_t durations[3]={30000,30000,30000};
    for(unsigned i=0;i<3;i++){
        moves[i].action=ids[i];moves[i].poses=&poses[i];
        moves[i].sequence=(T123Sequence){1,1,&durations[i]};
    }
    T123Pattern pat={.moves=moves,.move_count=3};
    Fight g;fight_init(&g);fight_bind_patterns(&g,&pat,&pat);
    CHECK(g.p[0].x==480&&g.p[1].x==800);
    CHECK(g.p[0].face==1&&g.p[1].face==-1);
    CHECK(g.camera.x==640&&g.camera.y==0&&g.camera.zoom==1);
    float start_x,start_y;
    CHECK(t123_stage_camera_project(&g.camera,480,0,0,0,&start_x,&start_y));
    CHECK(start_x==160&&start_y==420);
    CHECK(t123_stage_camera_project(&g.camera,800,0,0,0,&start_x,&start_y));
    CHECK(start_x==480&&start_y==420);
    g.scene=SCENE_FIGHT;g.p[0].x=1000;g.p[0].vy=13;g.p[1].x=40;
    fight_step(&g,IN_RESET);
    CHECK(g.p[0].x==480&&g.p[1].x==800&&g.p[0].vy==0&&g.camera.x==640);
    g.ai=0;g.scene=SCENE_FIGHT;g.p[0].x=600;g.p[1].x=50;
    for(int i=0;i<400;i++)fight_step(&g,IN_RIGHT);
    CHECK(g.p[0].x==1240);
    CHECK(g.camera.x>640.0f); /* the right half of the stage is reachable */
    float x,y;
    CHECK(t123_stage_camera_project(&g.camera,1240,0,0,0,&x,&y));
    CHECK(x>0&&x<640); /* wall stays visible after zooming out */
    g.p[1].x=1200;g.p[0].x=45;
    for(int i=0;i<20;i++)fight_step(&g,IN_LEFT);
    CHECK(g.p[0].x==40);
    puts("PAT arena walls and camera passed");
    return 0;
}
