#include <stdio.h>
#include <string.h>
#include <psp2/ctrl.h>
#include <psp2/display.h>
#include <psp2/kernel/processmgr.h>
#include "soft2d.h"
#include "t123/fight.h"
static soft2d_pgf *font;
static soft2d_texture *sprites[2],*background;
static soft2d_texture *stage_tiles[5][6];
static soft2d_texture *stage_alt_tiles[5][6];
/* BG34's loader also creates four static scene sprites and thirty object
   sprites. Keep them inspectable separately until their update/collision
   routines have been reconstructed from the x86 reference. */
static soft2d_texture *stage_extras[4];
static soft2d_texture *stage_objects[30];
static T123Resources resources;
static T123Pattern patterns[2];
static int data_ready;
static const char *roster[]={"reimu","marisa","sakuya","alice","patchouli","youmu","remilia","yuyuko","yukari","suika","udonge","aya","komachi","iku","tenshi","sanae","chirno","meirin","utsuho","suwako"};
#define ROSTER_COUNT (sizeof roster/sizeof roster[0])
static unsigned roster_index[2]={0,16},roster_card_index[2]={ROSTER_COUNT,ROSTER_COUNT};
static unsigned roster_pat_mask,roster_asset_mask,roster_card_mask,roster_attempt_mask,roster_texture_fail_mask;
static unsigned dash_direct_hit_routes,dash_no_direct_boxes;
static unsigned object_route_probe,object_attack_routes;
static unsigned suwako_418_burst_spawns;
static unsigned object_anchor_probe;
static int object_sprite_seen;
static int object_render_capture;
static int probe_roster_object_routes(void);
static soft2d_texture *roster_cards[2];
static char roster_first_image[20][64];
static int gallery_mode,gallery_texture_seen,gallery_character_seen,gallery_action_seen,gallery_pose_seen;
static int stage_mode,stage_texture_seen,stage_navigation_seen,stage_layout_seen;
static unsigned gallery_move,gallery_pose;
static uint32_t gallery_previous;
static uint32_t stage_previous;
static unsigned stage_index,stage_layer;
static unsigned stage_tick;
static const char *stage_names[]={"bg00","bg01","bg02","bg03","bg04","bg05","bg06","bg10","bg11","bg12","bg13","bg14","bg15","bg16","bg17","bg18","bg30","bg31","bg32","bg33","bg34","bg36","bg37","bg38"};
#define STAGE_COUNT (sizeof stage_names/sizeof stage_names[0])
static int stage_uses_grid(void){return stage_index>=16;}
typedef struct {unsigned player,image,age;soft2d_texture *texture;} TextureSlot;
static TextureSlot cache[64];static unsigned cache_age,loaded_textures;
static void clear_player_cache(int player){for(unsigned i=0;i<64;i++)if(cache[i].texture&&cache[i].player==(unsigned)player){soft2d_free_texture(cache[i].texture);cache[i]=(TextureSlot){0};}}
static int load_character(int player,unsigned index){
 if(player<0||player>1||index>=ROSTER_COUNT)return -1;
 char path[160];snprintf(path,sizeof path,"data/character/%s/%s.pat",roster[index],roster[index]);
 T123Pattern next={0};if(t123_resource_pattern(&resources,path,&next))return -1;
 t123_pattern_free(&patterns[player]);clear_player_cache(player);patterns[player]=next;roster_index[player]=index;roster_pat_mask|=1u<<index;return 0;
}
static int select_character(Fight *g,int player,int direction){
 int next=(int)roster_index[player]+(direction<0?-1:1);if(next<0)next=(int)ROSTER_COUNT-1;if(next>=(int)ROSTER_COUNT)next=0;
 if(load_character(player,(unsigned)next))return -1;
 fight_bind_character_patterns(g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);return 0;
}
static unsigned roster_asset_count(void){unsigned n=0;for(unsigned i=0;i<ROSTER_COUNT;i++)if(roster_asset_mask&(1u<<i))++n;return n;}
static unsigned roster_card_count(void){unsigned n=0;for(unsigned i=0;i<ROSTER_COUNT;i++)if(roster_card_mask&(1u<<i))++n;return n;}
static void ensure_roster_card(int player){
    unsigned index=roster_index[player];if(roster_card_index[player]==index)return;
    if(roster_cards[player])soft2d_free_texture(roster_cards[player]);
    roster_cards[player]=NULL;roster_card_index[player]=index;
    char path[160];snprintf(path,sizeof path,"data/stand/%s.cv2",roster[index]);
    roster_cards[player]=soft2d_load_dat(&resources,path,NULL);
    if(roster_cards[player])roster_card_mask|=1u<<index;
}
static soft2d_texture *load_image(int player,unsigned image,char *resolved,size_t resolved_size){
    if(image>=patterns[player].image_count)return NULL;
    char filename[160],path[256],palette[256];
    snprintf(filename,sizeof filename,"%s",patterns[player].images[image]);
    char *dot=strrchr(filename,'.');if(!dot)return NULL;strcpy(dot,".cv2");
    snprintf(path,sizeof path,"data/character/%s/%s",roster[roster_index[player]],filename);
    snprintf(palette,sizeof palette,"data/character/%s/palette000.pal",roster[roster_index[player]]);
    soft2d_texture *t=soft2d_load_dat(&resources,path,palette);
    if(t&&resolved&&resolved_size)snprintf(resolved,resolved_size,"%s",filename);
    return t;
}
static const T123Move *roster_idle_move(const T123Pattern *pat){
    const T123Move *idle=t123_pattern_move(pat,0,0);
    if(idle)return idle;
    /* Some PATs alias stand to an internal action instead of defining action 0. */
    for(unsigned i=0;i<pat->move_count;i++)if(pat->moves[i].action==0)return &pat->moves[i];
    return NULL;
}
static soft2d_texture *load_roster_preview(int player,unsigned *source_image,char *resolved,size_t resolved_size){
    const T123Pattern *pat=&patterns[player];
    /* Prefer a sprite actually referenced by the character's idle PAT action. */
    const T123Move *idle=roster_idle_move(pat);
    if(idle)for(unsigned i=0;i<idle->sequence.count;i++){
        unsigned image=idle->poses[i].image;soft2d_texture *t=load_image(player,image,resolved,resolved_size);
        if(t){*source_image=image;return t;}
    }
    /* Some characters' PATs reference an image missing from these DATs. Show
       no fabricated substitute in that case; report the first real pose miss. */
    return NULL;
}
static soft2d_texture *pose_texture(int player,unsigned image){
    unsigned bit=1u<<roster_index[player];
    for(unsigned j=0;j<64;j++)if(cache[j].texture&&cache[j].player==(unsigned)player&&cache[j].image==image){cache[j].age=++cache_age;roster_asset_mask|=bit;return cache[j].texture;}
    if(image>=patterns[player].image_count)return NULL;
    char filename[160],path[256],palette[256];snprintf(filename,sizeof filename,"%s",patterns[player].images[image]);
    if(!(roster_attempt_mask&bit)){roster_attempt_mask|=bit;snprintf(roster_first_image[roster_index[player]],sizeof roster_first_image[0],"%s",filename);}
    soft2d_texture *t=load_image(player,image,NULL,0);if(!t){roster_texture_fail_mask|=bit;return NULL;}roster_asset_mask|=bit;
    unsigned slot=0;for(unsigned j=0;j<64;j++){if(!cache[j].texture){slot=j;break;}if(cache[j].age<cache[slot].age)slot=j;}
    soft2d_free_texture(cache[slot].texture);cache[slot]=(TextureSlot){(unsigned)player,image,++cache_age,t};++loaded_textures;return t;
}
static void gallery_select_idle(void){
    gallery_move=0;gallery_pose=0;
    for(unsigned i=0;i<patterns[0].move_count;i++)if(patterns[0].moves[i].action==0&&patterns[0].moves[i].index==0){gallery_move=i;return;}
}
static void stage_load_tiles(void){
    for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){
        if(stage_tiles[row][col]){soft2d_free_texture(stage_tiles[row][col]);stage_tiles[row][col]=NULL;}
        if(stage_alt_tiles[row][col]){soft2d_free_texture(stage_alt_tiles[row][col]);stage_alt_tiles[row][col]=NULL;}
        char path[128];
        if(!stage_uses_grid()){
            if(stage_layer)continue;
            snprintf(path,sizeof path,"data/background/%s/0000_%02u.cv2",stage_names[stage_index],row*6+col);
        }else{
            if(stage_layer&&strcmp(stage_names[stage_index],"bg34"))continue;
            unsigned prefix=!strcmp(stage_names[stage_index],"bg34")?0:(stage_layer?1:0);
            snprintf(path,sizeof path,"data/background/%s/%04u[%02u][%02u].cv2",stage_names[stage_index],prefix,row+1,col+1);
        }
        stage_tiles[row][col]=soft2d_load_dat(&resources,path,NULL);
        if(stage_tiles[row][col])stage_texture_seen=1;
        if(!strcmp(stage_names[stage_index],"bg34")){
            snprintf(path,sizeof path,"data/background/bg34/0001[%02u][%02u].cv2",row+1,col+1);
            stage_alt_tiles[row][col]=soft2d_load_dat(&resources,path,NULL);
            if(stage_alt_tiles[row][col])stage_texture_seen=1;
        }
    }
    if(strcmp(stage_names[stage_index],"bg34")){
        for(unsigned i=0;i<4;i++){if(stage_extras[i])soft2d_free_texture(stage_extras[i]);stage_extras[i]=NULL;}
        for(unsigned i=0;i<30;i++){if(stage_objects[i])soft2d_free_texture(stage_objects[i]);stage_objects[i]=NULL;}
    }
}
static void stage_load_extras(void){
    if(strcmp(stage_names[stage_index],"bg34"))return;
    char path[160];
    for(unsigned i=0;i<4;i++)if(!stage_extras[i]){
        snprintf(path,sizeof path,"data/background/bg34/%04u.cv2",i+1);
        stage_extras[i]=soft2d_load_dat(&resources,path,NULL);
    }
    for(unsigned i=0;i<30;i++)if(!stage_objects[i]){
        snprintf(path,sizeof path,"data/background/bg34/object/objectFa%03u.cv2",i);
        stage_objects[i]=soft2d_load_dat(&resources,path,NULL);
    }
}
static int stage_step(Fight *g,uint32_t input){
    uint32_t edge=input&~stage_previous;stage_previous=input;
    if(!stage_mode){if(g->scene!=SCENE_MENU||!(edge&IN_AI))return 0;stage_mode=1;stage_index=0;stage_layer=0;stage_tick=0;stage_load_tiles();fight_step(g,0);return 1;}
    if(edge&IN_BACK){stage_mode=0;gallery_previous=0;stage_previous=0;fight_step(g,0);return 1;}
    stage_tick++;
    if(edge&IN_LEFT){stage_index=(stage_index+STAGE_COUNT-1)%STAGE_COUNT;stage_layer=0;stage_navigation_seen=1;stage_load_tiles();}
    else if(edge&IN_RIGHT){stage_index=(stage_index+1)%STAGE_COUNT;stage_layer=0;stage_navigation_seen=1;stage_load_tiles();}
    if(!strcmp(stage_names[stage_index],"bg34")&&(edge&(IN_JUMP|IN_DOWN))){stage_layer=(stage_layer+1)%4;stage_navigation_seen=1;stage_load_tiles();if(stage_layer>=2)stage_load_extras();}
    fight_step(g,0);return 1;
}
static int gallery_step(Fight *g,uint32_t input){
    uint32_t edge=input&~gallery_previous;gallery_previous=input;
    if(!gallery_mode){
        if(g->scene!=SCENE_MENU||!(edge&IN_SHOT))return 0;
        gallery_mode=1;gallery_select_idle();fight_step(g,0);return 1;
    }
    if(edge&IN_BACK){gallery_mode=0;gallery_previous=0;fight_step(g,0);return 1;}
    int character=(int)roster_index[0];
    if(edge&IN_MELEE){if(load_character(0,(unsigned)((character+1)%ROSTER_COUNT))==0){gallery_character_seen=1;fight_bind_character_patterns(g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);gallery_select_idle();}}
    else if(edge&IN_SHOT){if(load_character(0,(unsigned)((character+ROSTER_COUNT-1)%ROSTER_COUNT))==0){gallery_character_seen=1;fight_bind_character_patterns(g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);gallery_select_idle();}}
    else if(patterns[0].move_count){
        if(edge&IN_LEFT){gallery_move=(gallery_move+patterns[0].move_count-1)%patterns[0].move_count;gallery_pose=0;gallery_action_seen=1;}
        else if(edge&IN_RIGHT){gallery_move=(gallery_move+1)%patterns[0].move_count;gallery_pose=0;gallery_action_seen=1;}
        const T123Move *move=&patterns[0].moves[gallery_move];
        if(move->sequence.count){
            if(edge&IN_JUMP){gallery_pose=(gallery_pose+1)%move->sequence.count;gallery_pose_seen=1;}
            else if(edge&IN_DOWN){gallery_pose=(gallery_pose+move->sequence.count-1)%move->sequence.count;gallery_pose_seen=1;}
            else if(edge&IN_RESET)gallery_pose=0;
        }else gallery_pose=0;
    }
    fight_step(g,0);return 1;
}
static const float scale=544.0f/480.0f;
static float sx(float x){return 117.33f+x*scale;}
static void rect(float x,float y,float w,float h,unsigned c){soft2d_draw_rectangle(sx(x),y*scale,w*scale,h*scale,c);}
static void text(int x,int y,const char *s,unsigned c){soft2d_pgf_draw_text(font,sx(x),y*scale,c,1.15f,s);}
#define WHITE RGBA8(235,240,250,255)
#define GOLD RGBA8(255,215,125,255)
static uint32_t controls(unsigned b,int fighting){
    uint32_t in=0;
    if(b&SCE_CTRL_LEFT)in|=IN_LEFT;
    if(b&SCE_CTRL_RIGHT)in|=IN_RIGHT;
    if(b&SCE_CTRL_DOWN)in|=IN_DOWN;
    if(b&SCE_CTRL_UP)in|=IN_JUMP;
    if(b&SCE_CTRL_SQUARE)in|=IN_MELEE;
    if(b&SCE_CTRL_TRIANGLE)in|=IN_SHOT;
    if(b&SCE_CTRL_RTRIGGER)in|=IN_GUARD;
    if(b&SCE_CTRL_SELECT)in|=IN_RESET;
    if(b&SCE_CTRL_CROSS)in|=IN_CONFIRM;
    if(b&SCE_CTRL_CIRCLE)in|=fighting?IN_C_ATTACK:IN_BACK;
    if(fighting&&(b&SCE_CTRL_LTRIGGER)&&(b&SCE_CTRL_CIRCLE))in=(in&~(IN_C_ATTACK|IN_AI))|IN_SPELLCARD;
    if(b&SCE_CTRL_START)in|=IN_BACK;
    if((b&SCE_CTRL_LTRIGGER)&&!(fighting&&(b&SCE_CTRL_CIRCLE)))in|=IN_AI;
    return in;
}
static uint32_t scenario(int f){
    if(f==181)return IN_SPELLCARD;
    if(f==84)return IN_SHOT;
    if(f==86)return IN_MELEE;
    if(f==87)return IN_JUMP;
    if(f==88)return IN_RIGHT;
    if(f==89)return IN_BACK;
    if(f==90)return IN_AI;
    if(f>=92&&f<=130&&f%2==0)return IN_RIGHT;
    if(f==132)return IN_JUMP;
    if(f==135)return IN_JUMP;
    if(f==137)return IN_JUMP;
    if(f==138)return IN_BACK;
    if(f==139)return IN_RIGHT;
    if(f>=141&&f<=177&&f%2==1)return IN_RIGHT;
    if(f<80&&f%4==0)return IN_RIGHT;
    if(f==178||f==180)return IN_CONFIRM;
    unsigned in=0;
    if(f>=182 && f<210)in|=IN_RIGHT;
    if(f==182)in|=IN_JUMP;
    if(f>=212 && f<260)in|=IN_LEFT;
    if(f==215)in|=IN_MELEE;
    if(f==247)in|=IN_RIGHT|IN_MELEE;
    if(f==279)in|=IN_DOWN|IN_MELEE;
    if(f==307||f==339||f==371||f==403)in|=IN_RIGHT;
    if(f==309||f==341||f==373||f==405)in|=IN_RIGHT;
    if(f==311||f==375)in|=IN_RIGHT|IN_SHOT;
    if(f==343||f==407)in|=IN_RIGHT|IN_C_ATTACK;
    if(f==439)in|=IN_LEFT|IN_SHOT;
    if(f==471)in|=IN_LEFT|IN_C_ATTACK;
    if(f==503)in|=IN_JUMP;
    if(f==535)in|=IN_SHOT;
    if(f==567)in|=IN_C_ATTACK;
    if(f>=240 && f<265)in|=IN_GUARD;
    return in;
}
static int probe_attack_variant_selection(void){
    static const int attacker_ids[]={0,50,200,408,408,408},defender_ids[]={0,50};
    T123Move attacker_moves[6]={0},defender_moves[2]={0};
    T123Pose attacker_poses[6]={0},defender_poses[2]={0};
    uint16_t attacker_durations[6],defender_durations[2];
    T123Pattern attacker={0},defender={0};
    attacker.moves=attacker_moves;attacker.move_count=6;defender.moves=defender_moves;defender.move_count=2;
    for(unsigned i=0;i<6;i++){
        unsigned index=0;for(unsigned j=0;j<i;j++)if(attacker_ids[j]==attacker_ids[i])++index;
        attacker_moves[i].action=attacker_ids[i];attacker_moves[i].index=(uint16_t)index;attacker_moves[i].poses=&attacker_poses[i];
        if(attacker_ids[i]==408)attacker_moves[i].move_lock=index==0?1:index==1?3:6;
        attacker_durations[i]=30000;attacker_moves[i].sequence=(T123Sequence){1,1,&attacker_durations[i]};
        attacker_poses[i].hurt_count=1;attacker_poses[i].hurt[0]=(T123Box){-20,-100,20,0};
        if(index){attacker_poses[i].damage=index==1?100:250;attacker_poses[i].enemy_stun=12;attacker_poses[i].attack_count=1;attacker_poses[i].attack[0]=(T123Box){0,-100,100,0};}
    }
    for(unsigned i=0;i<2;i++){
        defender_moves[i].action=defender_ids[i];defender_moves[i].poses=&defender_poses[i];defender_durations[i]=30000;
        defender_moves[i].sequence=(T123Sequence){1,1,&defender_durations[i]};defender_poses[i].hurt_count=1;defender_poses[i].hurt[0]=(T123Box){-20,-100,20,0};
    }
    Fight probe;fight_init(&probe);fight_bind_patterns(&probe,&attacker,&defender);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200)return 0;
    probe.p[0].animation.current_frame=6;
    fight_step(&probe,IN_RIGHT|IN_SHOT);
    if(probe.p[0].action!=408||probe.p[0].action_index!=2||probe.p[0].b_hits!=1||probe.p[1].hp!=9750)return 0;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200)return 0;
    probe.p[0].animation.current_frame=7;fight_step(&probe,IN_RIGHT|IN_SHOT);
    return probe.p[0].action==200&&probe.p[0].b_hits==0&&probe.p[1].hp==10000;
}
static int probe_pattern_effect_payload(void){
    unsigned char bytes[249]={0};bytes[0]=5;bytes[1]=1;memcpy(bytes+3,"blank   .bmp",12);bytes[131]=1;bytes[143]=1;bytes[144]=1;bytes[164]=2;
    for(unsigned i=0;i<T123_POSE_EFFECT_BYTES;i++)bytes[219+i]=(unsigned char)(i+1);
    T123Pattern pattern={0};if(t123_pattern_decode(bytes,sizeof bytes,&pattern))return 0;
    const T123Move *move=t123_pattern_move(&pattern,0,0);int ok=move&&move->sequence.count==1;
    if(ok)for(unsigned i=0;i<T123_POSE_EFFECT_BYTES;i++)if(move->poses[0].effect_data[i]!=(unsigned char)(i+1)){ok=0;break;}
    t123_pattern_free(&pattern);return ok;
}
static const T123Move *probe_selected_attack(const T123Pattern *pattern,int action){
    unsigned index=0;const T123Move *best=t123_pattern_best_attack(pattern,action,&index);
    if(best)for(unsigned pose=0;pose<best->sequence.count;pose++)if(best->poses[pose].damage&&best->poses[pose].attack_count)return best;
    return t123_pattern_move(pattern,action,0);
}
static int probe_place_for_attack(Fight *probe,const T123Move *attack,const T123Pattern *defender){
    const T123Move *hurt=t123_pattern_move(defender,0,0);if(!hurt)return -1;
    for(unsigned ap=0;ap<attack->sequence.count;ap++){
        const T123Pose *hit=&attack->poses[ap];if(!hit->damage||!hit->attack_count)continue;
        for(unsigned hp=0;hp<hurt->sequence.count;hp++){
            const T123Pose *body=&hurt->poses[hp];if(!body->hurt_count)continue;
            for(unsigned ai=0;ai<hit->attack_count;ai++)for(unsigned bi=0;bi<body->hurt_count;bi++){
                const T123Box *a=&hit->attack[ai],*b=&body->hurt[bi];int ybase=(b->up+b->down-a->up-a->down)/4;
                for(int dy=-6;dy<=6;dy++){
                    int ax=300,by=ybase+dy;
                    int bx=ax+(a->left+a->right+b->left+b->right)/4;
                    int al=ax+a->left/2,ar=ax+a->right/2,bl=bx-b->right/2,br=bx-b->left/2;
                    int at=a->up/2,ab=a->down/2,bt=-by+b->up/2,bb=-by+b->down/2;
                    if(bx<=ax||bx>605||bx<35||al>=br||bl>=ar||at>=bb||bt>=ab)continue;
                    probe->p[0].x=ax;probe->p[0].y=0;probe->p[0].face=1;
                    probe->p[1].x=bx;probe->p[1].y=by;probe->p[1].face=-1;
                    return (int)ap;
                }
            }
        }
    }
    return -1;
}
static int probe_character_a_attack(unsigned character){
    static const int actions[]={300,302,303,304,330};
    static const uint32_t inputs[]={IN_MELEE,IN_RIGHT|IN_MELEE,IN_DOWN|IN_MELEE,
        IN_DOWN|IN_RIGHT|IN_MELEE,IN_LEFT|IN_MELEE};
    for(unsigned route=0;route<sizeof actions/sizeof actions[0];route++){
        const T123Move *move=t123_pattern_move(&patterns[0],actions[route],0);
        int damaging=0;
        if(move)for(unsigned pose=0;pose<move->sequence.count;pose++)
            if(move->poses[pose].damage&&move->poses[pose].attack_count){damaging=1;break;}
        if(!damaging)continue;
        Fight probe;fight_init(&probe);
        fight_bind_character_patterns(&probe,&patterns[0],(int)character,
            &patterns[1],(int)roster_index[1]);
        probe.ai=0;probe.scene=SCENE_FIGHT;
        if(probe_place_for_attack(&probe,move,&patterns[1])<0)continue;
        if(inputs[route]&IN_RIGHT){probe.p[0].x-=2;probe.p[1].x-=2;}
        else if(inputs[route]&IN_LEFT){probe.p[0].x+=2;probe.p[1].x+=2;}
        unsigned hp=probe.p[1].hp;
        fight_step(&probe,inputs[route]);
        if(probe.p[0].action!=actions[route])continue;
        for(unsigned tick=0;tick<600&&probe.p[1].hp==hp;tick++)fight_step(&probe,0);
        if(probe.p[1].hp<hp){
            const T123Pose *hit=fight_pose(&probe,0);
            if(probe.p[0].a_hits==1&&hit&&hp-probe.p[1].hp==(unsigned)hit->damage)return 1;
        }
    }
    return 0;
}
static unsigned probe_roster_a_attacks(void){
    unsigned saved0=roster_index[0],saved1=roster_index[1],mask=0;
    for(unsigned character=0;character<ROSTER_COUNT;character++)
        if(load_character(0,character)==0&&probe_character_a_attack(character))mask|=1u<<character;
    load_character(0,saved0);load_character(1,saved1);
    return mask;
}
static int probe_reimu_505_routes(void){
    static const int counts[3]={3,4,5};
    static const int vx[3][5]={{10,0,-10,0,0},{15,5,-5,-15,0},{20,10,0,-10,-20}};
    static const int vy[3][5]={{22,24,22,0,0},{24,26,26,24,0},{25,26,28,26,25}};
    int mask=0;
    for(int route=0;route<3;route++){
        Fight probe;fight_init(&probe);fight_bind_character_patterns(&probe,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
        probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[0].skill_card_id=104;
        fight_step(&probe,IN_SPELLCARD);if(probe.p[0].action!=505)continue;
        probe.p[0].animation.sequence=2;probe.p[0].animation.pose=2;probe.p[0].animation.pose_frame=0;
        probe.p[0].animation.current_frame=0;probe.p[0].animation.duration=3;probe.p[0].action_ticks=route*30;
        fight_step(&probe,0);if(probe.object_spawns!=(unsigned)counts[route])continue;
        int match=1;for(int n=0;n<counts[route];n++)if(probe.objects[n].action!=811||probe.objects[n].vx!=vx[route][n]||probe.objects[n].vy!=vy[route][n])match=0;
        if(match)mask|=1<<route;
    }
    return mask;
}
static int probe_real_dash_hit(const T123Pattern *attacker,const T123Pattern *defender,int action,uint32_t button){
    const T123Move *target=probe_selected_attack(attacker,action);if(!target)return 1;
    int has_direct=0;for(unsigned i=0;i<target->sequence.count;i++)if(target->poses[i].damage&&target->poses[i].attack_count){has_direct=1;break;}
    if(!has_direct){++dash_no_direct_boxes;return 0;} /* PAT selected route has no direct box; object/effect semantics remain. */
    Fight probe;fight_init(&probe);fight_bind_patterns(&probe,attacker,defender);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=450;
    if(probe_place_for_attack(&probe,target,defender)<0)return 3;
    /* The final dash tick advances the attacker 5 units before the action's
       first pose is resolved. Pre-offset both fighters so that pose 0 overlaps. */
    probe.p[0].x-=5;probe.p[1].x-=5;
    int initial_hp=probe.p[1].hp;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);fight_step(&probe,IN_RIGHT|button);
    if(probe.p[0].action!=action||probe.p[0].action_index!=target->index)return 2;
    if(probe.p[1].hp<initial_hp){const T123Pose *pose=fight_pose(&probe,0);int damage=initial_hp-probe.p[1].hp;
        if(!pose||!pose->attack_count||damage!=pose->damage)return 4;
        ++dash_direct_hit_routes;return 0;
    }
    int hp=initial_hp;unsigned ticks=0;for(unsigned i=0;i<target->sequence.count;i++)ticks+=target->sequence.durations[i];
    for(unsigned i=0;i<ticks+2;i++){
        if(probe_place_for_attack(&probe,target,defender)<0)return 3;
        fight_step(&probe,0);
        if(probe.p[1].hp<hp){const T123Pose *pose=fight_pose(&probe,0);int damage=hp-probe.p[1].hp;
            if(!pose||!pose->attack_count||damage!=pose->damage)return 4;
            ++dash_direct_hit_routes;return 0;
        }
    }
    return 5;
}
static int probe_real_dash_move_lock(const T123Pattern *attacker,const T123Pattern *defender,int action,uint32_t button){
    unsigned variant=0;const T123Move *target=t123_pattern_best_attack(attacker,action,&variant);
    int damaging=0;
    if(target)for(unsigned i=0;i<target->sequence.count;i++)if(target->poses[i].damage&&target->poses[i].attack_count){damaging=1;break;}
    if(!damaging)target=t123_pattern_move(attacker,action,0);
    if(!target||!t123_pattern_move(attacker,200,0))return 1;
    for(unsigned boundary=0;boundary<2;boundary++){
        Fight probe;fight_init(&probe);fight_bind_patterns(&probe,attacker,defender);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=220;
        fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
        if(probe.p[0].action!=200)return 2;
        probe.p[0].animation.current_frame=(uint32_t)target->move_lock+boundary;
        fight_step(&probe,IN_RIGHT|button);
        if(boundary==0){if(probe.p[0].action!=action)return 3;}
        else if(probe.p[0].action!=200)return 4;
    }
    return 0;
}
static int probe_roster_dash_routes(void){
    unsigned saved0=roster_index[0],saved1=roster_index[1];
    int error=0;
    for(unsigned character=0;character<ROSTER_COUNT;character++){
        if(load_character(0,character)){error=(int)(200+character*10);break;}
        if(!t123_pattern_move(&patterns[0],200,0)){error=(int)(200+character*10+1);break;}
        if(!strcmp(roster[character],"remilia")){ /* Remilia routes grounded down+C to 2C (412), not 66B/66C. */
            Fight probe;fight_init(&probe);fight_bind_patterns(&probe,&patterns[0],&patterns[1]);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=220;
            if(t123_pattern_move(&patterns[0],408,0)||t123_pattern_move(&patterns[0],418,0)||!t123_pattern_move(&patterns[0],412,0)){error=(int)(200+character*10+2);break;}
            fight_step(&probe,IN_DOWN|IN_C_ATTACK);
            if(probe.p[0].action!=412){error=(int)(200+character*10+3);break;}
            continue;
        }
        for(unsigned move=0;move<2;move++){
            int action=move?418:408;uint32_t button=move?IN_C_ATTACK:IN_SHOT;
            if(!t123_pattern_move(&patterns[0],action,0)){error=(int)(200+character*10+4+(int)move);break;}
            if(probe_real_dash_move_lock(&patterns[0],&patterns[1],action,button)){error=(int)(200+character*10+6+(int)move);break;}
            int hit_probe=probe_real_dash_hit(&patterns[0],&patterns[1],action,button);
            if(hit_probe){error=(int)(2000+character*100+move*10+(unsigned)hit_probe);break;}
        }
        if(error)break;
    }
    if(load_character(0,saved0)||load_character(1,saved1))return 199;
    return error;
}
static int probe_dash_routes(void){
    dash_direct_hit_routes=0;dash_no_direct_boxes=0;
    Fight probe;fight_init(&probe);fight_bind_patterns(&probe,&patterns[0],&patterns[1]);probe.ai=0;
    probe.scene=SCENE_FIGHT;fight_step(&probe,IN_LEFT|IN_DOWN|IN_MELEE);
    if(t123_input_history_get(&probe.input_history[0],89)!=0x19)return 5;
    fight_step(&probe,IN_RIGHT|IN_JUMP|IN_SHOT|IN_C_ATTACK|IN_GUARD|IN_CHANGE_CARD|IN_SPELLCARD);
    if(t123_input_history_get(&probe.input_history[0],89)!=0x3e6)return 6;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT|IN_SHOT);
    if(probe.p[0].action==408||probe.p[0].dashes)return 10;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT|IN_C_ATTACK);
    if(probe.p[0].action==418||probe.p[0].dashes)return 20;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 30;
    fight_step(&probe,IN_RIGHT|IN_SHOT);
    if(probe.p[0].action!=408||probe.p[0].action_index!=1)return 40;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 50;
    fight_step(&probe,IN_RIGHT|IN_C_ATTACK);
    if(probe.p[0].action!=418||probe.p[0].action_index!=0)return 60;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT);
    for(int i=0;i<12;i++)fight_step(&probe,0);
    fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 70;
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT);
    for(int i=0;i<13;i++)fight_step(&probe,0);
    fight_step(&probe,IN_RIGHT);
    if(probe.p[0].dashes!=0||probe.p[0].action==200)return 80;
    /* Mirror the motion while the player faces left; forward is relative to
       the opponent rather than a hard-coded screen direction. */
    fight_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[0].x=400;probe.p[1].x=220;
    fight_step(&probe,IN_LEFT);fight_step(&probe,0);fight_step(&probe,IN_LEFT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 90;
    fight_step(&probe,IN_LEFT|IN_SHOT);
    if(probe.p[0].action!=408||probe.p[0].action_index!=1)return 100;
    if(probe_real_dash_move_lock(&patterns[0],&patterns[1],408,IN_SHOT))return 120;
    if(probe_real_dash_move_lock(&patterns[0],&patterns[1],418,IN_C_ATTACK))return 130;
    if(probe_real_dash_move_lock(&patterns[1],&patterns[0],408,IN_SHOT))return 140;
    if(probe_real_dash_move_lock(&patterns[1],&patterns[0],418,IN_C_ATTACK))return 150;
    int roster_probe=probe_roster_dash_routes();if(roster_probe)return roster_probe;
    int object_probe=probe_roster_object_routes();if(object_probe)return object_probe;
    return probe_attack_variant_selection()?1:110;
}
static int probe_roster_object_routes(void){
    static const struct {unsigned character;int action,variant,action_frame,object,sequence,attacks,offset_x,offset_y;} cases[]={
        {3,408,0,1,849,19,0,60,100},{3,418,0,2,849,21,1,0,50},{3,418,0,3,849,23,1,0,50},
        {19,408,0,1,989,5,1,0,0},{19,418,0,1,808,0,1,0,0}
    };
    unsigned saved0=roster_index[0],saved1=roster_index[1];object_route_probe=object_attack_routes=object_anchor_probe=0;suwako_418_burst_spawns=0;object_sprite_seen=0;int error=0;
    for(unsigned i=0;i<sizeof cases/sizeof cases[0];i++){
        const unsigned c=cases[i].character;
        if(load_character(0,c)||load_character(1,c)){error=(int)(300+i);break;}
        const T123Move *player=t123_pattern_move(&patterns[0],cases[i].action,(unsigned)cases[i].variant);
        if(!player){error=(int)(310+i);break;}
        Fight probe;fight_init(&probe);fight_bind_character_patterns(&probe,&patterns[0],(int)c,&patterns[1],(int)c);probe.ai=0;probe.scene=SCENE_FIGHT;
        probe.p[0].x=130;probe.p[1].x=500;probe.p[0].action=cases[i].action;probe.p[0].action_index=(unsigned)cases[i].variant;
        if(t123_animation_set(&probe.p[0].animation,&player->sequence,1,0)){error=(int)(320+i);break;}
        probe.p[0].animation.current_frame=(uint32_t)(cases[i].action_frame-1);
        if(c==19&&cases[i].action==418){probe.p[0].animation.pose=10;probe.p[0].animation.pose_frame=0;probe.p[0].animation.duration=3;probe.p[0].object_counter=1;}
        fight_step(&probe,0);
        const T123Object *found=NULL;for(unsigned j=0;j<sizeof probe.objects/sizeof probe.objects[0];j++)if(probe.objects[j].active&&probe.objects[j].owner==0){found=&probe.objects[j];break;}
        if(!found||found->action!=cases[i].object||found->sequence!=cases[i].sequence){error=(int)(330+i);break;}
        if(found->x!=probe.p[0].x+probe.p[0].face*cases[i].offset_x||found->y!=probe.p[0].y+cases[i].offset_y){error=(int)(360+i);break;}
        if(i==1||i==3){probe.p[0].x+=10;probe.p[0].y+=5;fight_step(&probe,0);found=NULL;for(unsigned j=0;j<sizeof probe.objects/sizeof probe.objects[0];j++)if(probe.objects[j].active&&probe.objects[j].owner==0){found=&probe.objects[j];break;}int expected_y=probe.p[0].y+(i==1?60:0);if(!found||found->x!=probe.p[0].x||found->y!=expected_y){error=(int)(370+i);break;}++object_anchor_probe;}
        const T123Move *move=t123_pattern_move(&patterns[0],found->action,(unsigned)found->sequence);
        if(!move||!move->sequence.count){error=(int)(340+i);break;}
        int has_attack=0;for(unsigned p=0;p<move->sequence.count;p++)if(move->poses[p].damage&&move->poses[p].attack_count){has_attack=1;break;}
        if(has_attack!=cases[i].attacks){error=(int)(350+i);break;}
        if(move->poses&&move->poses[0].image<patterns[0].image_count&&pose_texture(0,move->poses[0].image))object_sprite_seen=1;
        if(c==19&&cases[i].action==418){for(int tick=1;tick<19;tick++)fight_step(&probe,0);if(probe.object_spawns!=10||probe.p[0].object_counter!=20){error=380;break;}suwako_418_burst_spawns=probe.object_spawns;}
        ++object_route_probe;if(has_attack)++object_attack_routes;
    }
    if(load_character(0,saved0)||load_character(1,saved1))return 399;
    if(error)return error;
    return object_route_probe==5&&object_attack_routes==4&&object_anchor_probe==2&&object_sprite_seen?0:400;
}
static void fighter(const Fight *g,int i){
    const Fighter *p=&g->p[i];const T123Pose *pose=fight_pose(g,i);
    int ground=395-p->y;unsigned c=i?RGBA8(110,190,255,255):RGBA8(245,105,145,255);
    soft2d_draw_fill_circle(sx(p->x),398*scale,21*scale,RGBA8(20,22,40,200));
    if(pose){
        soft2d_texture *t=pose_texture(i,pose->image);
        if(t){float x=p->face>0?sx(p->x-pose->ox*0.5f):sx(p->x+pose->ox*0.5f);soft2d_draw_texture_scale(t,x,(ground-pose->oy*0.5f)*scale,p->face*scale,scale);}
    }else if(sprites[i]){
        float size=1.5f*scale,w=soft2d_texture_get_width(sprites[i])*size,h=soft2d_texture_get_height(sprites[i])*size;
        soft2d_draw_texture_scale(sprites[i],sx(p->x)+(p->face<0?w/2:-w/2),ground*scale-h,p->face*size,size);
    }else{
        rect(p->x-18,ground-65,36,46,c);
        soft2d_draw_fill_circle(sx(p->x),(ground-78)*scale,14*scale,c);
        rect(p->x-15,ground-22,10,22,c);rect(p->x+5,ground-22,10,22,c);
    }
    if(p->attack&&!pose)rect(p->x+p->face*22-(p->face<0?35:0),ground-55,35,12,GOLD);
    if(p->guard)rect(p->x+p->face*28,ground-94,5,94,RGBA8(100,255,230,200));
    if(p->stun)soft2d_draw_fill_circle(sx(p->x),(ground-50)*scale,8*scale,GOLD);
}
static void draw_objects(const Fight *g){
    for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++){
        const T123Object *o=&g->objects[i];if(!o->active||o->owner<0||o->owner>1)continue;
        const T123Move *m=t123_pattern_move(g->patterns[o->owner],o->action,(unsigned)o->sequence);
        if(!m||o->animation.pose>=m->sequence.count)continue;
        const T123Pose *pose=&m->poses[o->animation.pose];soft2d_texture *t=pose_texture(o->owner,pose->image);
        if(t){const Fighter *owner=&g->p[o->owner];float x=owner->face>0?sx(o->x-pose->ox*0.5f):sx(o->x+pose->ox*0.5f);soft2d_draw_texture_scale(t,x,(395.0f-o->y-pose->oy*0.5f)*scale,owner->face*scale,scale);object_sprite_seen=1;}
        else{rect(o->x-8,(395-o->y)-8,16,16,o->owner?RGBA8(90,200,255,255):RGBA8(255,110,170,255));}
    }
}
static void draw(const Fight *g,int automated){
    rect(0,0,640,480,RGBA8(20,23,43,255));
    if(gallery_mode){
        rect(0,0,640,7,RGBA8(108,91,214,255));
        text(30,34,"PAT RESOURCE GALLERY",GOLD);
        char line[144];
        snprintf(line,sizeof line,"Character %u/20: %s  |  image cache %u",roster_index[0]+1,roster[roster_index[0]],loaded_textures);text(30,67,line,WHITE);
        const T123Pattern *pattern=&patterns[0];
        if(pattern->move_count&&gallery_move<pattern->move_count){
            const T123Move *move=&pattern->moves[gallery_move];
            snprintf(line,sizeof line,"Action %d  variant %u  |  action %u/%u",move->action,move->index,gallery_move+1,pattern->move_count);text(30,96,line,GOLD);
            if(move->sequence.count&&gallery_pose<move->sequence.count){
                const T123Pose *pose=&move->poses[gallery_pose];
                const char *image=pose->image<pattern->image_count?pattern->images[pose->image]:"invalid image index";
                snprintf(line,sizeof line,"Pose %u/%u  %s",gallery_pose+1,move->sequence.count,image);text(30,124,line,WHITE);
                snprintf(line,sizeof line,"Duration %u  damage %u  chip %u  hurt %u  attack %u",pose->duration,pose->damage,pose->chip,pose->hurt_count,pose->attack_count);text(30,151,line,WHITE);
                soft2d_texture *sprite=pose_texture(0,pose->image);
                if(sprite){
                    gallery_texture_seen=1;
                    float w=(float)soft2d_texture_get_width(sprite),h=(float)soft2d_texture_get_height(sprite);
                    float fitw=440.0f*scale/w,fith=210.0f*scale/h,fit=fitw<fith?fitw:fith;
                    soft2d_draw_texture_scale(sprite,sx(320)-w*fit*0.5f,174.0f*scale,fit,fit);
                }else{text(180,260,"Image failed to decode",GOLD);}
            }else{text(180,260,"Action contains no poses",GOLD);}
        }
        text(30,439,"Left/Right: action variant  Up/Down: pose",GOLD);
        text(30,467,"Square/Triangle: character  Select: first pose  Circle: menu",WHITE);
    }else if(stage_mode){
        rect(0,0,640,7,RGBA8(75,175,190,255));
        char line[128];snprintf(line,sizeof line,"STAGE RESOURCE VIEWER  %u/%u  %s",stage_index+1,(unsigned)STAGE_COUNT,stage_names[stage_index]);text(30,34,line,GOLD);
        snprintf(line,sizeof line,"%s",stage_layer==3?"BG34 recovered placement map":stage_layer==2?"BG34 static assets + object sprites":stage_layer==1?"BG34 composite 0000 + 0001":"Layer 0000 tiles");text(30,66,line,WHITE);
        if(stage_layer==3&&!strcmp(stage_names[stage_index],"bg34")){
            stage_layout_seen=1;rect(118,78,402,326,RGBA8(11,16,30,255));
            const float map_scale=0.095f,map_x_center=188.0f,map_y_min=92.0f;
            for(unsigned plane=0;plane<2;plane++)for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){
                soft2d_texture *tile=plane?stage_alt_tiles[row][col]:stage_tiles[row][col];if(!tile)continue;
                float wx=700.0f-256.0f*col,wy=(plane?1116.0f:2316.0f)-256.0f*row;
                float px=320.0f+(wx-map_x_center)*map_scale,py=82.0f+(wy-map_y_min)*map_scale;
                float fitw=256.0f*map_scale*scale/soft2d_texture_get_width(tile);
                float fith=256.0f*map_scale*scale/soft2d_texture_get_height(tile);
                float fit=fitw<fith?fitw:fith;
                soft2d_draw_texture_scale(tile,sx(px),py*scale,fit,fit);
            }
            const float aux_x[4]={700.0f,350.0f,350.0f,-1.0f};
            const float aux_y[4]={187.0f,230.0f,480.0f,-1.0f};
            for(unsigned i=0;i<4;i++)if(stage_extras[i]){
                soft2d_texture *asset=stage_extras[i];float wx=i==3?soft2d_texture_get_width(asset)*0.5f:aux_x[i];
                float wy=i==3?soft2d_texture_get_height(asset)*0.5f:aux_y[i];
                float px=320.0f+(wx-map_x_center)*map_scale,py=82.0f+(wy-map_y_min)*map_scale;
                soft2d_draw_texture_scale(asset,sx(px),py*scale,map_scale*scale,map_scale*scale);
            }
            unsigned anim_frame=(stage_tick%60u)/2u;
            if(stage_objects[anim_frame]){
                soft2d_texture *object=stage_objects[anim_frame];float wx=soft2d_texture_get_width(object)*0.5f;
                float wy=soft2d_texture_get_height(object)*0.5f-20.0f;
                float px=320.0f+(wx-map_x_center)*map_scale,py=82.0f+(wy-map_y_min)*map_scale;
                soft2d_draw_texture_scale(object,sx(px),py*scale,map_scale*scale,map_scale*scale);
            }
            text(132,407,"Loader positions; 256-unit tiles; aux x/y recovered",WHITE);
            snprintf(line,sizeof line,"objectFa %02u/29 tick %u/59; projection provisional",anim_frame,stage_tick%60u);text(132,424,line,GOLD);
        }
        else if(stage_layer==2&&!strcmp(stage_names[stage_index],"bg34")){
            for(unsigned i=0;i<4;i++)if(stage_extras[i]){
                soft2d_texture *asset=stage_extras[i];float fitw=124.0f*scale/soft2d_texture_get_width(asset),fith=60.0f*scale/soft2d_texture_get_height(asset),fit=fitw<fith?fitw:fith;
                soft2d_draw_texture_scale(asset,sx(36.0f+i*148.0f),78.0f*scale,fit,fit);
                snprintf(line,sizeof line,"000%u",i+1);text(36+(int)i*148,144,line,GOLD);
            }
            unsigned anim_frame=(stage_tick%60u)/2u;
            for(unsigned i=0;i<30;i++)if(stage_objects[i]){
                soft2d_texture *object=stage_objects[i];unsigned row=i/6,col=i%6;
                float fitw=68.0f*scale/soft2d_texture_get_width(object),fith=38.0f*scale/soft2d_texture_get_height(object),fit=fitw<fith?fitw:fith;
                float x=56.0f+col*91.0f,y=154.0f*scale+row*44.0f*scale;
                if(i==anim_frame){float bx=56.0f+col*91.0f,by=152.0f+row*44.0f;unsigned c=GOLD;rect(bx,by,70,1.4f,c);rect(bx,by+42,70,1.4f,c);rect(bx,by,1.4f,43,c);rect(bx+69,by,1.4f,43,c);}
                soft2d_draw_texture_scale(object,sx(x),y,fit,fit);
                snprintf(line,sizeof line,"%02u",i);text((int)x+4,(int)(y/scale)+36,line,WHITE);
            }
            unsigned static_count=0,object_count=0;for(unsigned i=0;i<4;i++)if(stage_extras[i])static_count++;for(unsigned i=0;i<30;i++)if(stage_objects[i])object_count++;
            snprintf(line,sizeof line,"Static %u/4 | objectFa %u/30 | animation frame %02u/29",static_count,object_count,anim_frame);text(30,402,line,GOLD);
            snprintf(line,sizeof line,"Animation tick %u/59; each frame lasts 2 ticks",stage_tick%60u);text(30,423,line,WHITE);
        }
        else if(stage_layer==1&&!strcmp(stage_names[stage_index],"bg34")){
            soft2d_texture *(*base)[6]=stage_tiles;
            soft2d_texture *(*upper)[6]=stage_alt_tiles;
            float tile_size=35.0f*scale,upper_y=82.0f*scale,base_y=upper_y+(1200.0f/256.0f)*tile_size;
            for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(base[row][col]){
                soft2d_texture *tile=base[row][col];float fit=tile_size/soft2d_texture_get_height(tile);
                soft2d_draw_texture_scale(tile,sx(214.0f+(5-col)*35.0f),base_y+row*tile_size,fit,fit);
            }
            for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(upper[row][col]){
                soft2d_texture *tile=upper[row][col];float fit=tile_size/soft2d_texture_get_height(tile);
                soft2d_draw_texture_scale(tile,sx(214.0f+(5-col)*35.0f),upper_y+row*tile_size,fit,fit);
            }
        }else for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col]){
            soft2d_texture *tile=stage_tiles[row][col];float fit=58.0f*scale/soft2d_texture_get_height(tile);
            soft2d_draw_texture_scale(tile,sx(20.0f+(5-col)*100.0f),82*scale+row*67.0f*scale,fit,fit);
        }
        text(30,439,"Left/Right: stage   Up/Down: BG34 view",GOLD);
        text(30,467,"Circle: menu  |  Object timing, camera and collision pending",WHITE);
    }else if(g->scene!=SCENE_FIGHT){
        rect(0,0,640,7,RGBA8(218,79,121,255));
        text(48,78,"TOUHOU123VITA",GOLD);
        text(48,112,"Roster PAT preview - original DAT resources",WHITE);
        text(48,149,"Select characters and inspect original sprites",WHITE);
        if(!data_ready){text(48,185,"Copy th123a/b/c.dat to ux0:data/touhou123vita/",GOLD);}
        for(int i=0;i<2;i++)if(roster_cards[i]){
            float card_scale=0.34f*scale;
            float w=soft2d_texture_get_width(roster_cards[i])*card_scale;
            float h=soft2d_texture_get_height(roster_cards[i])*card_scale;
            soft2d_draw_texture_scale(roster_cards[i],sx(g->p[i].x)-w*0.5f,145*scale,card_scale,card_scale);
        }
        fighter(g,0);fighter(g,1);draw_objects(g);
        if(g->scene==SCENE_MENU){
            text(30,408,"P1: ",GOLD);text(80,408,roster[roster_index[0]],WHITE);
            text(350,408,"P2: ",GOLD);text(400,408,roster[roster_index[1]],WHITE);
            text(30,438,"Left/Right: choose P1    X: practice setup",GOLD);
            text(30,466,"Triangle: PAT gallery | 20 original characters",WHITE);
            text(30,485,"L: inspect background resources",GOLD);
        }else{
            char line[96];text(30,408,"P1: ",GOLD);text(80,408,roster[roster_index[0]],WHITE);
            text(350,408,"P2: ",GOLD);text(400,408,roster[roster_index[1]],WHITE);
            snprintf(line,sizeof line,"Setup  %s vs %s  |  10000 HP",roster[roster_index[0]],roster[roster_index[1]]);text(30,438,line,GOLD);
            text(30,466,"Left/Right: choose P2    X: enter arena    Circle: back",WHITE);
        }
    }else{
        if(background)soft2d_draw_texture_scale(background,sx(0),0,640*scale/soft2d_texture_get_width(background),400*scale/soft2d_texture_get_height(background));
        else{rect(0,0,640,400,RGBA8(35,49,72,255));for(int i=0;i<12;i++)rect(i*60,200+(i%3)*20,28,180,RGBA8(24,39,58,255));}
        rect(0,395,640,85,RGBA8(48,37,60,255));
        rect(30,30,240,15,RGBA8(40,20,30,255));rect(370,30,240,15,RGBA8(20,25,40,255));
        rect(30,30,g->p[0].hp*240.0f/g->max_hp,15,RGBA8(245,105,145,255));rect(370,30,g->p[1].hp*240.0f/g->max_hp,15,RGBA8(110,190,255,255));
        char line[96];snprintf(line,sizeof line,"P1 %d HP",g->p[0].hp);text(30,24,line,WHITE);
        snprintf(line,sizeof line,"CPU %d HP",g->p[1].hp);text(370,24,line,WHITE);text(280,40,"PRACTICE",GOLD);
        fighter(g,0);fighter(g,1);draw_objects(g);
        for(int i=0;i<16;i++)if(g->shots[i].active)soft2d_draw_fill_circle(sx(g->shots[i].x),(395-g->shots[i].y)*scale,8*scale,g->shots[i].owner?RGBA8(90,200,255,255):RGBA8(255,110,170,255));
        if(!g->p[0].hp || !g->p[1].hp)text(210,170,"K.O. - SELECT to restart",GOLD);
        snprintf(line,sizeof line,"Hits: %u / %u    CPU: %s",g->p[0].hits,g->p[1].hits,g->ai?"ON":"OFF");text(30,428,line,WHITE);
        text(30,453,"Arrows: move/crouch/jump | Z: A | X: B | C: C | E guard",WHITE);
        text(30,475,"L+Circle: Reimu card 103 -> skill 560 test slot; hand/cost pending",GOLD);
    }
    if(automated&&!stage_mode&&!gallery_mode)text(430,190,"AUTOMATED TEST",GOLD);
}
static int capture_object_render_probe(Fight *live){
    unsigned saved0=roster_index[0],saved1=roster_index[1];int previous_gallery=gallery_mode,previous_stage=stage_mode;
    if(load_character(0,3)||load_character(1,19))goto fail;
    Fight preview;fight_init(&preview);fight_bind_character_patterns(&preview,&patterns[0],3,&patterns[1],19);preview.scene=SCENE_FIGHT;preview.p[0].x=190;preview.p[1].x=430;
    const T123Move *move=t123_pattern_move(&patterns[0],849,21);if(!move||!move->sequence.count)goto fail;
    T123Object *o=&preview.objects[0];o->active=1;o->owner=0;o->action=849;o->sequence=21;o->x=280;o->y=30;o->life=30;o->age=1;
    if(t123_animation_set(&o->animation,&move->sequence,1,0))goto fail;
    gallery_mode=stage_mode=0;object_sprite_seen=0;soft2d_start_drawing();soft2d_clear_screen();draw(&preview,1);soft2d_end_drawing();
    if(soft2d_capture("ux0:data/touhou123vita-object-probe.bmp"))goto fail;
    object_render_capture=object_sprite_seen;
    gallery_mode=previous_gallery;stage_mode=previous_stage;
    if(load_character(0,saved0)||load_character(1,saved1))return 0;
    fight_bind_character_patterns(live,&patterns[0],(int)saved0,&patterns[1],(int)saved1);return object_render_capture;
fail:
    gallery_mode=previous_gallery;stage_mode=previous_stage;
    load_character(0,saved0);load_character(1,saved1);
    fight_bind_character_patterns(live,&patterns[0],(int)saved0,&patterns[1],(int)saved1);return 0;
}
int main(void){
    Fight g;fight_init(&g);sceCtrlSetSamplingMode(SCE_CTRL_MODE_ANALOG);
    if(soft2d_init()<0)return 1;
    font=soft2d_load_default_pgf();if(!font){soft2d_fini();return 2;}
    if(t123_resources_open(&resources,"ux0:data/touhou123vita")==0 && (resources.opened&0x1cu)==0x1cu &&
       load_character(0,0)==0 && load_character(1,16)==0){
        data_ready=1;fight_bind_character_patterns(&g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
        background=soft2d_load_dat(&resources,"data/background/bg10/0000_10.cv2",NULL);
    }
    FILE *flag=fopen("app0:auto-test.txt","r");int automated=flag!=NULL;if(flag)fclose(flag);
    int dash_gate_probe=automated&&data_ready?probe_dash_routes():0;
    if(automated&&data_ready)object_render_capture=capture_object_render_probe(&g);
    unsigned roster_a_attack_mask=automated&&data_ready?probe_roster_a_attacks():0;
    int f=0,menu_seen=0,practice_seen=0,fight_seen=0,jump_seen=0,gallery_seen=0,stage_seen=0,skill_probe_inputs=0,skill_probe_success=0,skill_probe_sequence_ok=0,skill_probe_action=-1,skill_probe_image=-1,skill_probe_hit_delta=0,skill_probe_start_sequence=-1,skill_probe_hit_sequence=-1,skill_probe_startup_hit_delta=-1,skill_air_launch_ok=0,skill_landing_sequence=-1,skill_landing_ok=0,skill_x_delta=0,skill_reverse_motion_ok=0;
    Fight skill_probe_game,skill_102_probe_game,skill_107_probe_game,skill_104_probe_game;int skill_probe_ready=0,skill_102_probe_ready=0,skill_107_probe_ready=0,skill_104_probe_ready=0,skill_104_action=-1,skill_104_sequence_ok=0,skill_104_spawn_count=0,skill_104_object_action=-1,skill_104_sprite_seen=0,skill_104_hit_delta=0,skill_104_phase_mask=0,skill_102_action=-1,skill_102_image=-1,skill_102_sequence_ok=0,skill_102_hit_delta=0,skill_102_hit_sequence=-1,skill_102_hit_image=-1,skill_102_followup_ticks=0,skill_107_action=-1,skill_107_image=-1,skill_107_sequence_ok=0,skill_107_hit_delta=0,skill_107_hit_sequence=-1,skill_107_hit_image=-1,skill_107_followup_ticks=0;unsigned skill_hits_baseline=0;
    for(;;){
        SceCtrlData pad={0};sceCtrlPeekBufferPositive(0,&pad,1);uint32_t input=automated?scenario(f):controls(pad.buttons,g.scene==SCENE_FIGHT);
        if(!data_ready)input=0;
        int gallery_handled=data_ready?gallery_step(&g,input):0;
        int stage_handled=data_ready&&!gallery_handled?stage_step(&g,input):0;
        if(data_ready&&!gallery_handled&&!stage_handled&&!automated){uint32_t edge=input&~g.previous;if(g.scene==SCENE_MENU){if(edge&IN_LEFT)select_character(&g,0,-1);else if(edge&IN_RIGHT)select_character(&g,0,1);}else if(g.scene==SCENE_PRACTICE){if(edge&IN_LEFT)select_character(&g,1,-1);else if(edge&IN_RIGHT)select_character(&g,1,1);}}
        if(data_ready&&!gallery_handled&&!stage_handled&&automated){uint32_t edge=input&~g.previous;if(g.scene==SCENE_MENU&&(edge&IN_RIGHT))select_character(&g,0,1);else if(g.scene==SCENE_PRACTICE&&(edge&IN_RIGHT))select_character(&g,1,1);}
        if(data_ready&&g.scene!=SCENE_FIGHT){ensure_roster_card(0);ensure_roster_card(1);}
        if(data_ready&&automated&&g.scene!=SCENE_FIGHT&&f<170){
            soft2d_texture *preview=NULL;unsigned image=0;char filename[64]={0};
            for(int player=0;player<2;player++){
                unsigned idx=roster_index[player],bit=1u<<idx;
                if((roster_attempt_mask&bit)||!(roster_pat_mask&bit))continue;
                preview=load_roster_preview(player,&image,filename,sizeof filename);
                roster_attempt_mask|=bit;
                if(preview){roster_asset_mask|=bit;snprintf(roster_first_image[idx],sizeof roster_first_image[0],"%s",filename);soft2d_free_texture(preview);preview=NULL;}
                else{roster_texture_fail_mask|=bit;if(patterns[player].image_count)snprintf(roster_first_image[idx],sizeof roster_first_image[0],"%s",patterns[player].images[0]);}
            }
        }
        if(automated&&g.scene==SCENE_FIGHT&&(input&IN_SPELLCARD))++skill_probe_inputs;
        if(!gallery_handled&&!stage_handled)fight_step(&g,input);else if(gallery_mode)gallery_seen=1;else if(stage_mode)stage_seen=1;
        if(automated&&f==180&&g.scene==SCENE_FIGHT&&load_character(0,0)==0){
            fight_bind_character_patterns(&g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            fight_init(&skill_probe_game);fight_bind_character_patterns(&skill_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_probe_game.ai=0;skill_probe_game.scene=SCENE_FIGHT;
            const T123Move *skill=t123_pattern_move(&patterns[0],560,1);
            skill_probe_ready=skill&&probe_place_for_attack(&skill_probe_game,skill,&patterns[1])>=0;
            skill_hits_baseline=skill_probe_game.p[0].hits;
            fight_init(&skill_102_probe_game);fight_bind_character_patterns(&skill_102_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_102_probe_game.ai=0;skill_102_probe_game.scene=SCENE_FIGHT;skill_102_probe_game.p[0].skill_card_id=102;
            const T123Move *card102_attack=probe_selected_attack(&patterns[0],540);
            skill_102_probe_ready=card102_attack&&t123_pattern_variant_count(&patterns[0],540)>0&&t123_pattern_variant_count(&patterns[0],540)<=T123_ACTION_SEQUENCE_LIMIT&&probe_place_for_attack(&skill_102_probe_game,card102_attack,&patterns[1])>=0;
            fight_init(&skill_107_probe_game);fight_bind_character_patterns(&skill_107_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_107_probe_game.ai=0;skill_107_probe_game.scene=SCENE_FIGHT;skill_107_probe_game.p[0].skill_card_id=107;
            const T123Move *card107_attack=t123_pattern_move(&patterns[0],565,1);
            skill_107_probe_ready=card107_attack&&t123_pattern_variant_count(&patterns[0],565)>0&&t123_pattern_variant_count(&patterns[0],565)<=T123_ACTION_SEQUENCE_LIMIT&&probe_place_for_attack(&skill_107_probe_game,card107_attack,&patterns[1])>=0;
            fight_init(&skill_104_probe_game);fight_bind_character_patterns(&skill_104_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_104_probe_game.ai=0;skill_104_probe_game.scene=SCENE_FIGHT;skill_104_probe_game.p[0].skill_card_id=104;skill_104_probe_game.p[1].x=286;
            const T123Move *card104_bullet=t123_pattern_move(&patterns[0],811,0);
            skill_104_probe_ready=card104_bullet&&card104_bullet->sequence.count&&card104_bullet->poses[0].damage==550&&card104_bullet->poses[0].attack_count>0&&t123_pattern_variant_count(&patterns[0],505)==5;
        }
        if(automated&&f==181&&g.p[0].skill_uses&&skill_probe_ready){
            fight_step(&skill_probe_game,IN_SPELLCARD);
            const T123Pose *startup=fight_pose(&skill_probe_game,0);
            skill_probe_success=skill_probe_game.p[0].action==560;
            skill_probe_action=skill_probe_game.p[0].action;
            skill_probe_image=startup?startup->image:-1;
            skill_probe_start_sequence=(int)skill_probe_game.p[0].animation.sequence;
            skill_probe_startup_hit_delta=(int)(skill_probe_game.p[0].hits-skill_hits_baseline);
            for(int tick=0;tick<10;tick++)fight_step(&skill_probe_game,0);
            int stayed_in_startup=skill_probe_game.p[0].animation.sequence==0&&skill_probe_game.p[0].hits==skill_hits_baseline;
            fight_step(&skill_probe_game,0);
            skill_probe_hit_sequence=(int)skill_probe_game.p[0].animation.sequence;
            skill_probe_hit_delta=(int)(skill_probe_game.p[0].hits-skill_hits_baseline);
            skill_air_launch_ok=skill_probe_game.p[0].skill_air_active&&skill_probe_game.p[0].skill_air_vy_q==56;
            skill_probe_sequence_ok=stayed_in_startup&&skill_probe_start_sequence==0&&skill_probe_startup_hit_delta==0&&skill_probe_hit_sequence==1&&skill_probe_hit_delta>0;
            /* Keep the target ahead through the probe so auto-facing does not
               reverse the launch direction while testing the 4.5-unit speed. */
            int skill_start_x=skill_probe_game.p[0].x;skill_probe_game.p[1].x=600;
            for(int tick=0;tick<120&&skill_probe_game.p[0].action==560&&
                skill_probe_game.p[0].animation.sequence!=3;tick++)fight_step(&skill_probe_game,0);
            skill_x_delta=skill_probe_game.p[0].x-skill_start_x;
            skill_landing_sequence=(int)skill_probe_game.p[0].animation.sequence;
            skill_landing_ok=skill_probe_game.p[0].action==560&&skill_landing_sequence==3&&
                skill_probe_game.p[0].action_index==3&&skill_probe_game.p[0].y==0&&
                skill_probe_game.p[0].vy==0&&!skill_probe_game.p[0].skill_air_active;
            Fight reverse_skill;fight_init(&reverse_skill);
            fight_bind_character_patterns(&reverse_skill,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            reverse_skill.ai=0;reverse_skill.scene=SCENE_FIGHT;reverse_skill.p[0].x=400;reverse_skill.p[1].x=0;
            fight_step(&reverse_skill,IN_SPELLCARD);
            for(int tick=0;tick<10;tick++)fight_step(&reverse_skill,0);
            fight_step(&reverse_skill,0);
            int reverse_launch_ok=reverse_skill.p[0].skill_air_active&&reverse_skill.p[0].skill_air_vx_q==18;
            int reverse_start_x=reverse_skill.p[0].x;
            for(int tick=0;tick<120&&reverse_skill.p[0].action==560&&
                reverse_skill.p[0].animation.sequence!=3;tick++)fight_step(&reverse_skill,0);
            skill_reverse_motion_ok=reverse_launch_ok&&reverse_skill.p[0].animation.sequence==3&&
                reverse_skill.p[0].x<reverse_start_x;
            if(skill_102_probe_ready){
                fight_step(&skill_102_probe_game,IN_SPELLCARD);
                const T123Pose *card_pose=fight_pose(&skill_102_probe_game,0);
                skill_102_action=skill_102_probe_game.p[0].action;skill_102_image=card_pose?card_pose->image:-1;
                skill_102_sequence_ok=skill_102_action==540&&skill_102_probe_game.p[0].animation.sequence==0&&skill_102_probe_game.p[0].skill_uses==1&&skill_102_image>=0;
                unsigned card102_hp=skill_102_probe_game.p[1].hp;
                for(int tick=0;tick<100&&skill_102_probe_game.p[1].hp==card102_hp;tick++){fight_step(&skill_102_probe_game,0);skill_102_followup_ticks=tick+1;}
                skill_102_hit_delta=(int)(card102_hp-skill_102_probe_game.p[1].hp);
                if(skill_102_hit_delta>0){skill_102_hit_sequence=(int)skill_102_probe_game.p[0].animation.sequence;const T123Pose *hit_pose=fight_pose(&skill_102_probe_game,0);if(hit_pose)skill_102_hit_image=hit_pose->image;}
            }
            if(skill_107_probe_ready){
                fight_step(&skill_107_probe_game,IN_SPELLCARD);
                const T123Pose *card_pose=fight_pose(&skill_107_probe_game,0);
                skill_107_action=skill_107_probe_game.p[0].action;skill_107_image=card_pose?card_pose->image:-1;
                skill_107_sequence_ok=skill_107_action==565&&skill_107_probe_game.p[0].animation.sequence==0&&skill_107_probe_game.p[0].skill_uses==1&&skill_107_image>=0;
                unsigned card107_hp=skill_107_probe_game.p[1].hp;
                for(int tick=0;tick<100&&skill_107_probe_game.p[1].hp==card107_hp;tick++){fight_step(&skill_107_probe_game,0);skill_107_followup_ticks=tick+1;}
                skill_107_hit_delta=(int)(card107_hp-skill_107_probe_game.p[1].hp);
                if(skill_107_hit_delta>0){skill_107_hit_sequence=(int)skill_107_probe_game.p[0].animation.sequence;const T123Pose *hit_pose=fight_pose(&skill_107_probe_game,0);if(hit_pose)skill_107_hit_image=hit_pose->image;}
            }
            if(skill_104_probe_ready){
                skill_104_phase_mask=probe_reimu_505_routes();
                fight_step(&skill_104_probe_game,IN_SPELLCARD);skill_104_action=skill_104_probe_game.p[0].action;
                skill_104_sequence_ok=skill_104_action==505&&skill_104_probe_game.p[0].skill_uses==1&&skill_104_probe_game.p[0].action_sequence_count==5;
                skill_104_probe_game.p[0].animation.sequence=2;skill_104_probe_game.p[0].animation.pose=2;
                skill_104_probe_game.p[0].animation.pose_frame=0;skill_104_probe_game.p[0].animation.current_frame=0;
                skill_104_probe_game.p[0].animation.duration=3;skill_104_probe_game.p[0].object_counter=0;skill_104_probe_game.p[0].action_ticks=20;skill_104_probe_game.p[1].x=286;
                fight_step(&skill_104_probe_game,0);skill_104_spawn_count=(int)skill_104_probe_game.object_spawns;
                for(unsigned n=0;n<16;n++)if(skill_104_probe_game.objects[n].active){skill_104_object_action=skill_104_probe_game.objects[n].action;break;}
                const T123Move *bullet=t123_pattern_move(&patterns[0],811,0);
                if(bullet&&bullet->sequence.count&&bullet->poses[0].image<patterns[0].image_count&&pose_texture(0,bullet->poses[0].image))skill_104_sprite_seen=1;
                unsigned hp=skill_104_probe_game.p[1].hp;
                for(int tick=0;tick<4&&skill_104_probe_game.p[1].hp==hp;tick++)fight_step(&skill_104_probe_game,0);
                skill_104_hit_delta=(int)(hp-skill_104_probe_game.p[1].hp);
            }
            if(load_character(0,1)==0)fight_bind_character_patterns(&g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
        }
        if(g.scene==SCENE_MENU)menu_seen=1;
        if(g.scene==SCENE_PRACTICE)practice_seen=1;
        if(g.scene==SCENE_FIGHT)fight_seen=1;
        if(g.p[0].y>0)jump_seen=1;
        soft2d_start_drawing();soft2d_clear_screen();draw(&g,automated);soft2d_end_drawing();
        if(automated && f==83)soft2d_capture("ux0:data/touhou123vita-menu.bmp");
        if(automated && gallery_mode && f==85)soft2d_capture("ux0:data/touhou123vita-gallery.bmp");
        if(automated && stage_mode && f==134)soft2d_capture("ux0:data/touhou123vita-stage.bmp");
        if(automated && stage_mode && f==136)soft2d_capture("ux0:data/touhou123vita-stage-assets.bmp");
        if(automated && stage_mode && f==137)soft2d_capture("ux0:data/touhou123vita-stage-layout.bmp");
        if(automated && f==130)soft2d_capture("ux0:data/touhou123vita-practice.bmp");
        if(automated && f==300)soft2d_capture("ux0:data/touhou123vita-fight.bmp");
        soft2d_swap_buffers();sceDisplayWaitVblankStart();
        if(automated && ++f==600){
            int stage_tiles_loaded=0,stage_alt_tiles_loaded=0;for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){if(stage_tiles[row][col])stage_tiles_loaded++;if(stage_alt_tiles[row][col])stage_alt_tiles_loaded++;}
            int stage_static_loaded=0,stage_objects_loaded=0;for(unsigned i=0;i<4;i++)if(stage_extras[i])stage_static_loaded++;for(unsigned i=0;i<30;i++)if(stage_objects[i])stage_objects_loaded++;
            int pat_effect_fixture=probe_pattern_effect_payload();
            int pass=data_ready&&(resources.opened==31u)&&menu_seen&&gallery_seen&&gallery_texture_seen&&gallery_character_seen&&gallery_action_seen&&gallery_pose_seen&&stage_seen&&stage_index==20&&stage_layer==3&&stage_layout_seen&&stage_texture_seen&&stage_navigation_seen&&stage_tiles_loaded==30&&stage_alt_tiles_loaded==30&&stage_static_loaded==4&&stage_objects_loaded==30&&practice_seen&&fight_seen&&jump_seen&&dash_gate_probe==1&&object_route_probe==5&&object_attack_routes==4&&suwako_418_burst_spawns==10&&object_anchor_probe==2&&object_sprite_seen&&object_render_capture&&dash_direct_hit_routes>0&&dash_direct_hit_routes+dash_no_direct_boxes==38&&pat_effect_fixture&&roster_card_count()==ROSTER_COUNT&&roster_asset_count()==ROSTER_COUNT&&roster_a_attack_mask==((1u<<ROSTER_COUNT)-1u)&&g.p[0].hits>0&&g.p[0].dashes>0&&g.p[0].b_hits>0&&g.p[0].c_hits>0&&skill_probe_success&&skill_probe_sequence_ok&&skill_probe_action==560&&skill_probe_image>=0&&skill_probe_hit_delta>0&&skill_air_launch_ok&&skill_landing_ok&&skill_x_delta>0&&skill_reverse_motion_ok&&skill_102_sequence_ok&&skill_102_image==774&&skill_102_hit_delta==1100&&skill_102_hit_sequence==3&&skill_102_hit_image==39&&skill_102_followup_ticks==47&&skill_107_sequence_ok&&skill_107_action==565&&skill_107_image==12&&skill_107_hit_delta==450&&skill_107_hit_sequence==1&&skill_107_hit_image==47&&skill_107_followup_ticks==63&&skill_104_phase_mask==7&&skill_104_sequence_ok&&skill_104_action==505&&skill_104_spawn_count==4&&skill_104_object_action==811&&skill_104_sprite_seen&&skill_104_hit_delta>0&&g.p[1].hp<g.max_hp&&loaded_textures>2;
            FILE *r=fopen("ux0:data/touhou123vita-smoke.json","w");
            if(r){fprintf(r,"{\"schema\":29,\"status\":\"%s\",\"frames\":600,\"menu\":%d,\"gallery\":%d,\"gallery_texture\":%d,\"gallery_character\":%d,\"gallery_action\":%d,\"gallery_pose\":%d,\"stage_view\":%d,\"stage\":\"%s\",\"stage_layer\":%u,\"stage_layout\":%d,\"stage_texture\":%d,\"stage_navigation\":%d,\"stage_tiles\":%d,\"stage_alt_tiles\":%d,\"stage_static_assets\":%d,\"stage_object_assets\":%d,\"stage_animation_tick\":%u,\"stage_animation_frame\":%u,\"practice\":%d,\"fight\":%d,\"jump\":%d,\"dash_gate_probe\":%d,\"object_route_probe\":%u,\"object_attack_routes\":%u,\"suwako_418_burst_spawns\":%u,\"object_anchor_probe\":%u,\"object_sprite_seen\":%d,\"object_render_capture\":%d,\"dash_direct_hits\":%u,\"dash_no_direct_boxes\":%u,\"pat_effect_fixture\":%d,\"hits\":%u,\"dashes\":%u,\"a_hits\":%u,\"roster_a_attack_mask\":%u,\"b_hits\":%u,\"c_hits\":%u,\"skill_uses\":%d,\"skill_action\":%d,\"skill_image\":%d,\"skill_sequence_ok\":%d,\"skill_start_sequence\":%d,\"skill_hit_sequence\":%d,\"skill_startup_hit_delta\":%d,\"skill_hit_delta\":%d,\"skill_air_launch_ok\":%d,\"skill_landing_ok\":%d,\"skill_landing_sequence\":%d,\"skill_x_delta\":%d,\"skill_reverse_motion_ok\":%d,\"skill_102_action\":%d,\"skill_102_image\":%d,\"skill_102_sequence_ok\":%d,\"skill_102_hit_delta\":%d,\"skill_102_hit_sequence\":%d,\"skill_102_hit_image\":%d,\"skill_102_followup_ticks\":%d,\"skill_107_action\":%d,\"skill_107_image\":%d,\"skill_107_sequence_ok\":%d,\"skill_107_hit_delta\":%d,\"skill_107_hit_sequence\":%d,\"skill_107_hit_image\":%d,\"skill_107_followup_ticks\":%d,\"skill_104_phase_mask\":%d,\"skill_104_action\":%d,\"skill_104_sequence_ok\":%d,\"skill_104_spawn_count\":%d,\"skill_104_object_action\":%d,\"skill_104_sprite_seen\":%d,\"skill_104_hit_delta\":%d,\"skill_inputs\":%d,\"scene_end\":%d,\"p0_character\":%d,\"p0_skill_card\":%d,\"p0_action\":%d,\"cpu_hp\":%d,\"max_hp\":%d,\"digest\":%u,\"external_dat\":%u,\"textures_decoded\":%u,\"roster_pat_mask\":%u,\"roster_assets\":%u,\"roster_asset_mask\":%u,\"roster_cards\":%u,\"roster_card_mask\":%u,\"roster_attempt_mask\":%u,\"roster_texture_fail_mask\":%u}\n",pass?"passed":"failed",menu_seen,gallery_seen,gallery_texture_seen,gallery_character_seen,gallery_action_seen,gallery_pose_seen,stage_seen,stage_names[stage_index],stage_layer,stage_layout_seen,stage_texture_seen,stage_navigation_seen,stage_tiles_loaded,stage_alt_tiles_loaded,stage_static_loaded,stage_objects_loaded,stage_tick%60u,(stage_tick%60u)/2u,practice_seen,fight_seen,jump_seen,dash_gate_probe,object_route_probe,object_attack_routes,suwako_418_burst_spawns,object_anchor_probe,object_sprite_seen,object_render_capture,dash_direct_hit_routes,dash_no_direct_boxes,pat_effect_fixture,g.p[0].hits,g.p[0].dashes,g.p[0].a_hits,roster_a_attack_mask,g.p[0].b_hits,g.p[0].c_hits,skill_probe_success,skill_probe_action,skill_probe_image,skill_probe_sequence_ok,skill_probe_start_sequence,skill_probe_hit_sequence,skill_probe_startup_hit_delta,skill_probe_hit_delta,skill_air_launch_ok,skill_landing_ok,skill_landing_sequence,skill_x_delta,skill_reverse_motion_ok,skill_102_action,skill_102_image,skill_102_sequence_ok,skill_102_hit_delta,skill_102_hit_sequence,skill_102_hit_image,skill_102_followup_ticks,skill_107_action,skill_107_image,skill_107_sequence_ok,skill_107_hit_delta,skill_107_hit_sequence,skill_107_hit_image,skill_107_followup_ticks,skill_104_phase_mask,skill_104_action,skill_104_sequence_ok,skill_104_spawn_count,skill_104_object_action,skill_104_sprite_seen,skill_104_hit_delta,skill_probe_inputs,g.scene,g.character[0],g.p[0].skill_card_id,g.p[0].action,g.p[1].hp,g.max_hp,(unsigned)fight_digest(&g),resources.opened,loaded_textures,roster_pat_mask,roster_asset_count(),roster_asset_mask,roster_card_count(),roster_card_mask,roster_attempt_mask,roster_texture_fail_mask);fclose(r);}
            FILE *rf=fopen("ux0:data/touhou123vita-roster.tsv","w");if(rf){fprintf(rf,"character\tpat_loaded\ttexture_loaded\tfirst_image\n");for(unsigned i=0;i<ROSTER_COUNT;i++)fprintf(rf,"%s\t%d\t%d\t%s\n",roster[i],!!(roster_pat_mask&(1u<<i)),!!(roster_asset_mask&(1u<<i)),roster_first_image[i]);fclose(rf);}
            break;
        }
    }
    for(int i=0;i<2;i++)if(sprites[i])soft2d_free_texture(sprites[i]);
    for(int i=0;i<2;i++)if(roster_cards[i])soft2d_free_texture(roster_cards[i]);
    if(background)soft2d_free_texture(background);
    for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){if(stage_tiles[row][col])soft2d_free_texture(stage_tiles[row][col]);if(stage_alt_tiles[row][col])soft2d_free_texture(stage_alt_tiles[row][col]);}
    for(unsigned i=0;i<4;i++)if(stage_extras[i])soft2d_free_texture(stage_extras[i]);
    for(unsigned i=0;i<30;i++)if(stage_objects[i])soft2d_free_texture(stage_objects[i]);
    for(unsigned i=0;i<64;i++)soft2d_free_texture(cache[i].texture);
    t123_pattern_free(&patterns[0]);t123_pattern_free(&patterns[1]);t123_resources_close(&resources);
    soft2d_free_pgf(font);soft2d_fini();sceKernelExitProcess(0);return 0;
}
