#include <stdio.h>
#include "t123/fight.h"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static void enter(Fight *g) {fight_init(g);g->ai=0;fight_step(g,IN_CONFIRM);fight_step(g,0);fight_step(g,IN_CONFIRM);fight_step(g,0);}
static void test_moves(T123Pattern *p,T123Move *moves,T123Pose *poses,uint16_t *durations,const int *ids,unsigned count,int attacks){
    p->moves=moves;p->move_count=count;
    for(unsigned i=0;i<count;i++){
        unsigned sequence=0;for(unsigned j=0;j<i;j++)if(ids[j]==ids[i])++sequence;
        moves[i].action=ids[i];moves[i].index=sequence;moves[i].move_lock=100;moves[i].poses=&poses[i];durations[i]=30000;moves[i].sequence=(T123Sequence){1,1,&durations[i]};
        poses[i].hurt_count=1;poses[i].hurt[0]=(T123Box){-20,-100,20,0};
        if(attacks&&ids[i]>=300&&ids[i]<419){poses[i].damage=100;poses[i].enemy_stun=12;poses[i].attack_count=1;poses[i].attack[0]=(T123Box){0,-100,100,0};}
    }
}
static int patterned_states(void){
    static const int ids[]={0,1,2,3,4,5,6,7,8,9,10,150,158,200,300,301,302,303,304,306,307,308,309,330,400,401,402,403,404,405,406,407,409,410,411,412,414,415,416,417,418,560};
    T123Move moves[sizeof ids/sizeof ids[0]]={0};T123Pose poses[sizeof ids/sizeof ids[0]]={0};uint16_t durations[sizeof ids/sizeof ids[0]];
    T123Pattern pat={0};pat.moves=moves;pat.move_count=(uint32_t)(sizeof ids/sizeof ids[0]);
    for(unsigned i=0;i<pat.move_count;i++){durations[i]=30000;moves[i].action=ids[i];moves[i].poses=&poses[i];moves[i].sequence=(T123Sequence){1,1,&durations[i]};}
    Fight g;fight_init(&g);g.ai=0;fight_bind_patterns(&g,&pat,&pat);g.ai=0;g.scene=SCENE_FIGHT;
    fight_step(&g,IN_RIGHT);CHECK(g.p[0].action==4);
    fight_step(&g,0);fight_step(&g,IN_LEFT);CHECK(g.p[0].action==5);
    fight_step(&g,IN_DOWN);CHECK(g.p[0].action==1);fight_step(&g,IN_DOWN);CHECK(g.p[0].action==2);
    fight_step(&g,0);CHECK(g.p[0].action==3);
    fight_reset(&g);g.previous=0;fight_step(&g,IN_RIGHT|IN_JUMP);CHECK(g.p[0].action==7&&g.p[0].y>0);
    for(int i=0;i<18;i++){fight_step(&g,0);}CHECK(g.p[0].action==9);
    for(int i=0;i<20&&g.p[0].y>0;i++){fight_step(&g,0);}CHECK(g.p[0].y==0&&g.p[0].action==10);
    fight_reset(&g);g.previous=0;fight_step(&g,IN_MELEE);CHECK(g.p[0].action==300);
    fight_reset(&g);g.previous=0;fight_step(&g,IN_RIGHT|IN_MELEE);CHECK(g.p[0].action==302);
    fight_reset(&g);g.previous=0;fight_step(&g,IN_DOWN|IN_MELEE);CHECK(g.p[0].action==303);
    fight_reset(&g);g.previous=0;fight_step(&g,IN_DOWN|IN_RIGHT|IN_MELEE);CHECK(g.p[0].action==304);
    fight_reset(&g);g.previous=0;fight_step(&g,IN_JUMP);fight_step(&g,0);fight_step(&g,IN_MELEE);CHECK(g.p[0].action==306);
    fight_reset(&g);g.ai=1;g.previous=0;fight_step(&g,0);CHECK(g.p[1].x<450);
    {
        Fight skill;fight_init(&skill);fight_bind_character_patterns(&skill,&pat,0,&pat,16);skill.ai=0;skill.scene=SCENE_FIGHT;skill.p[1].x=220;
        T123Move *move=NULL;for(unsigned i=0;i<pat.move_count;i++)if(moves[i].action==560)move=&moves[i];
        CHECK(move!=NULL);T123Pose *pose=move->poses;pose->damage=130;pose->enemy_stun=12;pose->attack_count=1;pose->attack[0]=(T123Box){0,-100,100,0};
        fight_step(&skill,IN_SPELLCARD);
        CHECK(skill.p[0].action==560&&skill.p[0].skill_uses==1);
        CHECK(skill.p[0].hits==1&&skill.p[1].hp==skill.max_hp-130);
    }
    {
        uint16_t idle_duration=30000,prepare_durations[4]={3,3,3,3},attack_durations[7]={3,3,3,3,3,3,3},loop_durations[2]={3,3};
        T123Pose idle_pose={0},prepare_poses[4]={0},attack_poses[7]={0},loop_poses[2]={0};
        T123Move sequence_moves[5]={0};T123Pattern sequence_pattern={0};
        idle_pose.hurt_count=1;idle_pose.hurt[0]=(T123Box){-20,-100,20,0};
        sequence_moves[0]=(T123Move){0,0,100,100,{1,1,&idle_duration},&idle_pose};
        sequence_moves[1]=(T123Move){560,0,100,100,{4,0,prepare_durations},prepare_poses};
        sequence_moves[2]=(T123Move){560,1,100,100,{7,0,attack_durations},attack_poses};
        sequence_moves[3]=(T123Move){560,2,100,100,{2,1,loop_durations},loop_poses};
        uint16_t recovery_durations[3]={5,5,5};T123Pose recovery_poses[3]={0};
        sequence_moves[4]=(T123Move){560,3,100,100,{3,0,recovery_durations},recovery_poses};
        attack_poses[0].image=21;attack_poses[0].damage=130;attack_poses[0].enemy_stun=12;attack_poses[0].attack_count=1;attack_poses[0].attack[0]=(T123Box){0,-100,100,0};
        sequence_pattern.moves=sequence_moves;sequence_pattern.move_count=5;
        Fight skill;fight_init(&skill);fight_bind_character_patterns(&skill,&sequence_pattern,0,&sequence_pattern,16);skill.ai=0;skill.scene=SCENE_FIGHT;skill.p[1].x=220;
        fight_step(&skill,IN_SPELLCARD);
        CHECK(skill.p[0].action==560&&skill.p[0].animation.sequence==0&&skill.p[0].hits==0);
        for(int i=0;i<10;i++)fight_step(&skill,0);
        CHECK(skill.p[0].animation.sequence==0&&skill.p[0].hits==0);
        fight_step(&skill,0);
        CHECK(skill.p[0].animation.sequence==1&&skill.p[0].action_index==1&&fight_pose(&skill,0)->image==21);
        CHECK(skill.p[0].hits==1&&skill.p[1].hp==skill.max_hp-130);
        CHECK(skill.p[0].skill_air_active&&skill.p[0].skill_air_vy_q==56);
        CHECK(skill.p[0].animation.sequence==1);
        /* Continue the actual sequence and x86-derived vertical arc through
           takeoff, loop, descent and floor contact. */
        int skill_start_x=skill.p[0].x,air_ticks=0;skill.p[1].x=590;
        for(;air_ticks<60&&skill.p[0].animation.sequence!=3;air_ticks++)fight_step(&skill,0);
        CHECK(skill.p[0].y==0&&skill.p[0].vy==0&&!skill.p[0].skill_air_active);
        CHECK(skill.p[0].action==560&&skill.p[0].animation.sequence==3&&skill.p[0].action_index==3);
        CHECK(skill.p[0].x==(skill_start_x*4+18*air_ticks)/4);

        Fight reverse;fight_init(&reverse);fight_bind_character_patterns(&reverse,&sequence_pattern,0,&sequence_pattern,16);
        reverse.ai=0;reverse.scene=SCENE_FIGHT;reverse.p[0].x=400;reverse.p[1].x=0;
        fight_step(&reverse,IN_SPELLCARD);
        for(int tick=0;tick<10;tick++)fight_step(&reverse,0);
        fight_step(&reverse,0);
        CHECK(reverse.p[0].skill_air_active&&reverse.p[0].skill_air_vx_q==18);
        int reverse_start_x=reverse.p[0].x,reverse_ticks=0;
        for(;reverse_ticks<60&&reverse.p[0].animation.sequence!=3;reverse_ticks++)fight_step(&reverse,0);
        CHECK(reverse.p[0].animation.sequence==3);
        CHECK(reverse.p[0].x==(reverse_start_x*4-18*reverse_ticks)/4);
    }
    {
        /* Reimu grounded card 102 dispatches action 540 in the original
           handleInputs switch; PAT sequence data is required before use. */
        uint16_t startup_duration=4,attack_duration=3;
        T123Pose startup_pose={0},attack_pose={0};
        T123Move skill_moves[2]={
            {540,0,100,100,{1,1,&startup_duration},&startup_pose},
            {540,1,100,100,{1,0,&attack_duration},&attack_pose},
        };
        T123Pattern skill_pattern={.moves=skill_moves,.move_count=2};
        Fight card;fight_init(&card);fight_bind_character_patterns(&card,&skill_pattern,0,&skill_pattern,16);
        card.ai=0;card.scene=SCENE_FIGHT;card.p[0].skill_card_id=102;
        fight_step(&card,IN_SPELLCARD);
        CHECK(card.p[0].action==540&&card.p[0].animation.sequence==0&&card.p[0].skill_uses==1);
    }
    {
        /* Grounded card 107 dispatches action 565; its PAT data is required. */
        uint16_t startup_duration=4,attack_duration=4;
        T123Pose startup_pose={0},attack_pose={0};
        T123Move skill_moves[2]={
            {565,0,100,100,{1,0,&startup_duration},&startup_pose},
            {565,1,100,100,{1,1,&attack_duration},&attack_pose},
        };
        T123Pattern skill_pattern={.moves=skill_moves,.move_count=2};
        Fight card;fight_init(&card);fight_bind_character_patterns(&card,&skill_pattern,0,&skill_pattern,16);
        card.ai=0;card.scene=SCENE_FIGHT;card.p[0].skill_card_id=107;
        fight_step(&card,IN_SPELLCARD);
        CHECK(card.p[0].action==565&&card.p[0].animation.sequence==0&&card.p[0].skill_uses==1);
    }
    {
        /* Reimu 104/505 emits the original four-object PAT-811 spread at
           sequence 2, pose 2. The exact spawn tuple comes from the x86 oracle. */
        uint16_t idle_duration=30000,skill_durations[5]={3,3,3,3,3},bullet_duration=120;
        T123Pose idle_pose={0},skill_poses[5]={0},bullet_pose={0};
        T123Move moves[7]={0};T123Pattern pattern={0};
        idle_pose.hurt_count=1;idle_pose.hurt[0]=(T123Box){-20,-100,20,0};
        moves[0]=(T123Move){0,0,100,100,{1,1,&idle_duration},&idle_pose};
        for(unsigned n=0;n<5;n++)moves[n+1]=(T123Move){505,(uint16_t)n,100,100,{1,0,&skill_durations[n]},&skill_poses[n]};
        bullet_pose.damage=550;bullet_pose.enemy_stun=10;bullet_pose.attack_count=1;
        bullet_pose.attack[0]=(T123Box){-65,-25,50,25};
        moves[6]=(T123Move){811,0,10,0,{1,1,&bullet_duration},&bullet_pose};
        pattern.moves=moves;pattern.move_count=7;
        Fight volley;fight_init(&volley);fight_bind_character_patterns(&volley,&pattern,0,&pattern,16);
        volley.ai=0;volley.scene=SCENE_FIGHT;volley.p[0].skill_card_id=104;volley.p[1].x=286;
        fight_step(&volley,IN_SPELLCARD);
        CHECK(volley.p[0].action==505&&volley.p[0].action_sequence_count==5);
        volley.p[0].animation.sequence=2;volley.p[0].animation.pose=2;
        volley.p[0].animation.pose_frame=0;volley.p[0].animation.current_frame=0;
        volley.p[0].animation.duration=3;volley.p[0].object_counter=0;
        fight_step(&volley,0);
        CHECK(volley.object_spawns==4&&volley.p[0].object_counter==1);
        static const int expected_vx[]={15,5,-5,-15},expected_vy[]={24,26,26,24};
        for(unsigned n=0;n<4;n++){
            const T123Object *o=&volley.objects[n];
            CHECK(o->active&&o->owner==0&&o->action==811&&o->sequence==0);
            CHECK(o->x==304&&o->y==96&&o->vx==expected_vx[n]&&o->vy==expected_vy[n]&&o->life==120);
        }
        fight_step(&volley,0);CHECK(volley.object_spawns==4&&volley.p[1].hp==volley.max_hp);
        fight_step(&volley,0);CHECK(volley.p[1].hp==volley.max_hp-550&&volley.p[0].hits==1);
        CHECK(volley.object_spawns==4);

        Fight reverse;fight_init(&reverse);fight_bind_character_patterns(&reverse,&pattern,0,&pattern,16);
        reverse.ai=0;reverse.scene=SCENE_FIGHT;reverse.p[0].x=400;reverse.p[1].x=0;reverse.p[0].skill_card_id=104;
        fight_step(&reverse,IN_SPELLCARD);
        reverse.p[0].animation.sequence=2;reverse.p[0].animation.pose=2;
        reverse.p[0].animation.pose_frame=0;reverse.p[0].animation.duration=3;reverse.p[0].object_counter=0;
        fight_step(&reverse,0);
        CHECK(reverse.object_spawns==4&&reverse.objects[0].x==286&&reverse.objects[0].vx==-15);

        static const int counts[]={3,4,5},route_vx[3][5]={{10,0,-10,0,0},{15,5,-5,-15,0},{20,10,0,-10,-20}},route_vy[3][5]={{22,24,22,0,0},{24,26,26,24,0},{25,26,28,26,25}};
        for(unsigned route=0;route<3;route++){
            Fight phase;fight_init(&phase);fight_bind_character_patterns(&phase,&pattern,0,&pattern,16);
            phase.ai=0;phase.scene=SCENE_FIGHT;phase.p[0].skill_card_id=104;
            fight_step(&phase,IN_SPELLCARD);CHECK(phase.p[0].action==505);
            phase.p[0].animation.sequence=2;phase.p[0].animation.pose=2;phase.p[0].animation.pose_frame=0;
            phase.p[0].animation.current_frame=0;phase.p[0].animation.duration=3;phase.p[0].action_ticks=(int)(route*30);
            fight_step(&phase,0);CHECK(phase.object_spawns==(unsigned)counts[route]);
            for(int n=0;n<counts[route];n++)CHECK(phase.objects[n].vx==route_vx[route][n]&&phase.objects[n].vy==route_vy[route][n]);
        }
    }
    {
        static const int aid[]={0,50,300,320,321,322,400,410,401,401,408,408,418},vid[]={0,50};
        T123Move am[13]={0},vm[2]={0};T123Pose ap[13]={0},vp[2]={0};uint16_t ad[13],vd[2];T123Pattern a={0},v={0};
        test_moves(&a,am,ap,ad,aid,13,1);test_moves(&v,vm,vp,vd,vid,2,0);
        ap[10].damage=0;ap[10].attack_count=0; /* Reimu/Cirno 66B base variant is a non-hit placeholder. */
        fight_init(&g);g.ai=0;fight_bind_patterns(&g,&a,&v);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_MELEE);CHECK(g.p[0].action==300&&g.p[0].hits==1&&g.p[1].hp==9900);
        fight_step(&g,0);fight_step(&g,IN_MELEE);CHECK(g.p[0].action==320&&g.p[0].hits==2&&g.p[1].hp==9800);
        fight_step(&g,0);fight_step(&g,IN_MELEE);CHECK(g.p[0].action==321&&g.p[0].hits==3);
        fight_step(&g,0);fight_step(&g,IN_MELEE);CHECK(g.p[0].action==322&&g.p[0].hits==4);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_SHOT);CHECK(g.p[0].action==400&&g.p[0].hits==1&&fight_pose(&g,0)->damage==100);
        fight_step(&g,0);fight_step(&g,IN_C_ATTACK);CHECK(g.p[0].action==410&&g.p[0].hits==2&&fight_pose(&g,0)->damage==100);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT|IN_SHOT);CHECK(g.p[0].action==401&&g.p[0].b_hits==0); /* 66B cannot bypass dash state 200. */
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT);fight_step(&g,0);fight_step(&g,IN_RIGHT);CHECK(g.p[0].action==200&&g.p[0].dashes==1);
        fight_step(&g,IN_RIGHT|IN_SHOT);CHECK(g.p[0].action==408&&g.p[0].action_index==1&&g.p[0].b_hits==1&&g.p[1].hp==9900);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT|IN_C_ATTACK);CHECK(g.p[0].action==411&&g.p[0].c_hits==0); /* 66C also requires the dash. */
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT);fight_step(&g,0);fight_step(&g,IN_RIGHT);CHECK(g.p[0].action==200&&g.p[0].dashes==1);
        fight_step(&g,IN_RIGHT|IN_C_ATTACK);CHECK(g.p[0].action==418&&g.p[0].action_index==0&&g.p[0].c_hits==1&&g.p[1].hp==9900);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT);for(int i=0;i<12;i++)fight_step(&g,0);fight_step(&g,IN_RIGHT);CHECK(g.p[0].action==200&&g.p[0].dashes==1); /* Exact NRNR matcher: 12 neutral samples fit in the 15-sample search suffix. */
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT);for(int i=0;i<13;i++)fight_step(&g,0);fight_step(&g,IN_RIGHT);CHECK(g.p[0].dashes==0&&g.p[0].action!=200);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[0].x=400;g.p[1].x=220;
        fight_step(&g,IN_LEFT);fight_step(&g,0);fight_step(&g,IN_LEFT);CHECK(g.p[0].face==-1&&g.p[0].action==200&&g.p[0].dashes==1);
        fight_step(&g,IN_LEFT|IN_SHOT);CHECK(g.p[0].action==408&&g.p[0].action_index==1);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        ad[8]=30000;ap[8].damage=0;ad[9]=30000;ap[9].damage=100;
        am[8].sequence=(T123Sequence){1,1,&ad[8]};am[9].sequence=(T123Sequence){1,1,&ad[9]};
        ap[9].enemy_stun=12;ap[9].attack_count=1;ap[9].attack[0]=(T123Box){0,-100,100,0};
        fight_step(&g,IN_RIGHT|IN_SHOT);CHECK(g.p[0].action==401&&g.p[0].hits==0&&fight_pose(&g,0)->damage==0);
    }
    {
        static const int aid[]={0,50,200,408,408,408},vid[]={0,50};
        T123Move am[6]={0},vm[2]={0};T123Pose ap[6]={0},vp[2]={0};uint16_t ad[6],vd[2];T123Pattern a={0},v={0};
        test_moves(&a,am,ap,ad,aid,6,1);test_moves(&v,vm,vp,vd,vid,2,0);
        ap[3].damage=0;ap[3].attack_count=0;
        ap[4].damage=100;ap[5].damage=250;
        am[3].move_lock=1;am[4].move_lock=3;am[5].move_lock=6;
        fight_init(&g);fight_bind_patterns(&g,&a,&v);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT);fight_step(&g,0);fight_step(&g,IN_RIGHT);
        CHECK(g.p[0].action==200);
        g.p[0].animation.current_frame=6; /* The target move lock is inclusive in the x86 handler. */
        fight_step(&g,IN_RIGHT|IN_SHOT);
        CHECK(g.p[0].action==408&&g.p[0].action_index==2&&g.p[0].b_hits==1&&g.p[1].hp==9750);
        fight_reset(&g);g.ai=0;g.scene=SCENE_FIGHT;g.p[1].x=220;
        fight_step(&g,IN_RIGHT);fight_step(&g,0);fight_step(&g,IN_RIGHT);CHECK(g.p[0].action==200);
        g.p[0].animation.current_frame=7;
        fight_step(&g,IN_RIGHT|IN_SHOT);
        CHECK(g.p[0].action==200&&g.p[0].b_hits==0&&g.p[1].hp==10000);
    }
    return 0;
}
static int suwako_418_burst(void){
    uint16_t action_durations[23]={2,2,2,2,2,2,2,2,4,3,3,4,4,4,4,4,4,4,12,6,4,3,3};
    uint16_t object_duration=100;
    T123Pose action_poses[23]={0},object_pose={0};
    T123Move moves[2]={0};
    moves[0].action=418;moves[0].index=0;moves[0].move_lock=100;moves[0].poses=action_poses;
    moves[0].sequence=(T123Sequence){23,0,action_durations};
    moves[1].action=808;moves[1].index=0;moves[1].poses=&object_pose;
    moves[1].sequence=(T123Sequence){1,1,&object_duration};
    T123Pattern pattern={0};pattern.moves=moves;pattern.move_count=2;
    Fight g;fight_init(&g);fight_bind_character_patterns(&g,&pattern,19,&pattern,19);g.ai=0;g.scene=SCENE_FIGHT;
    g.p[0].action=418;g.p[0].action_index=0;
    CHECK(t123_animation_set(&g.p[0].animation,&moves[0].sequence,1,0)==0);
    g.p[0].animation.pose=9;g.p[0].animation.pose_frame=2;g.p[0].animation.duration=3;
    fight_step(&g,0);
    CHECK(g.p[0].animation.pose==10&&g.p[0].animation.pose_frame==0&&g.p[0].object_counter==1);
    CHECK(g.objects[0].active&&g.objects[0].x==g.p[0].x&&g.objects[0].y==g.p[0].y);
    for(int i=0;i<19;i++)fight_step(&g,0);
    CHECK(g.object_spawns==10&&g.p[0].object_counter==20);
    for(int i=0;i<8;i++)fight_step(&g,0);
    CHECK(g.object_spawns==10&&g.p[0].object_counter==20);
    return 0;
}
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
    fight_reset(&g);g.ai=1;g.frame=55;g.p[1].x=250;
    for(int i=0;i<6;i++)fight_step(&g,IN_GUARD);
    CHECK(g.p[0].hp==982 && g.p[1].hits==1);
    fight_reset(&g);g.ai=0;g.p[1].hp=10;g.p[1].x=250;fight_step(&g,IN_MELEE);
    for(int i=0;i<5;i++)fight_step(&g,0);
    CHECK(g.p[1].hp==0);
    Fight a,b;enter(&a);enter(&b);a.ai=b.ai=1;
    for(int i=0;i<3600;i++){unsigned in=i%80<35?IN_RIGHT:IN_LEFT;if(i%47==0)in|=IN_SHOT;fight_step(&a,in);fight_step(&b,in);}
    CHECK(fight_digest(&a)==fight_digest(&b));
    CHECK(a.p[0].hp>=0 && a.p[1].hp>=0);
    fight_step(&g,IN_BACK);CHECK(g.scene==SCENE_PRACTICE);
    CHECK(patterned_states()==0);
    CHECK(suwako_418_burst()==0);
    return 0;
}
