#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <psp2/ctrl.h>
#include <psp2/display.h>
#include <psp2/kernel/processmgr.h>
#include "soft2d.h"
#include "t123/fight.h"
#include "t123/stage.h"
/* Combat diagnostics use explicit historic positions so their input/timing
   fixtures do not depend on the production round-start layout. */
static void probe_bind_character_patterns(Fight *g,const T123Pattern *a,int ca,const T123Pattern *b,int cb){
    fight_bind_character_patterns(g,a,ca,b,cb);
    g->p[0].x=190;g->p[1].x=450;
    g->camera=(T123StageCamera){320,0,1,320,0,1};
}
static void probe_bind_patterns(Fight *g,const T123Pattern *a,const T123Pattern *b){
    probe_bind_character_patterns(g,a,-1,b,-1);
}
static void probe_reset(Fight *g){
    fight_reset(g);g->p[0].x=190;g->p[1].x=450;
    g->camera=(T123StageCamera){320,0,1,320,0,1};
}
static int arena_spawn_contract_seen;
static int udonge_409_contract_seen;
static soft2d_pgf *font;
static soft2d_texture *sprites[2],*background;
static soft2d_texture *stage_tiles[5][6];
static soft2d_texture *stage_alt_tiles[5][6];
/* BG34's loader also creates four static scene sprites and thirty object
   sprites. Keep them inspectable separately until their update/collision
   routines have been reconstructed from the x86 reference. */
static soft2d_texture *stage_extras[4];
static soft2d_texture *stage_objects[30];
static soft2d_texture *stage_bg02_page[16];
static T123Resources resources;
static T123Pattern patterns[2];
static int data_ready;
static const char *roster[]={"reimu","marisa","sakuya","alice","patchouli","youmu","remilia","yuyuko","yukari","suika","udonge","aya","komachi","iku","tenshi","sanae","chirno","meirin","utsuho","suwako"};
#define ROSTER_COUNT (sizeof roster/sizeof roster[0])
static unsigned roster_index[2]={0,16},roster_card_index[2]={ROSTER_COUNT,ROSTER_COUNT};
static unsigned roster_pat_mask,roster_asset_mask,roster_card_mask,roster_attempt_mask,roster_texture_fail_mask;
static unsigned dash_direct_hit_routes,dash_no_direct_boxes;
static unsigned roster_b_natural_candidates[20],roster_c_natural_candidates[20];
static int roster_b_natural_action[20],roster_c_natural_action[20];
static unsigned roster_b_hit_frame[20],roster_b_hit_damage[20],roster_c_hit_frame[20],roster_c_hit_damage[20];
static int roster_b_hit_gap[20],roster_c_hit_gap[20];
static unsigned roster_b_reached_mask[20],roster_c_reached_mask[20];
static int roster_b_408_variant[20],roster_b_409_variant[20],roster_c_418_variant[20];
static int roster_c_418_overlap_seen[20];
static int roster_c_418_horizontal_overlap_seen[20];
static int roster_c_418_vertical_overlap_seen[20];
static int roster_c_418_min_active_gap[20];
static int roster_c_418_min_signed_gap[20];
static int roster_c_418_min_horizontal_gap[20];
static int roster_c_418_min_vertical_gap[20];
static int roster_b_hit_source[20],roster_c_hit_source[20],roster_b_hit_pose[20],roster_c_hit_pose[20];
static unsigned object_route_probe,object_attack_routes,remilia_object_linger_seen,remilia_trail_lifecycle_seen;
static int object_route_error;
static int remilia_spacing_pair;
static float remilia_spacing_dx,remilia_spacing_dy;
static float remilia_spacing_samples[5][2];
static unsigned suwako_418_burst_spawns;
static unsigned object_anchor_probe;
static int object_sprite_seen;
static int object_render_capture;
static int probe_roster_object_routes(void);
static soft2d_texture *roster_cards[2];
static char roster_first_image[20][64];
static int gallery_mode,gallery_texture_seen,gallery_character_seen,gallery_action_seen,gallery_pose_seen;
static int stage_mode,stage_texture_seen,stage_navigation_seen,stage_layout_seen,stage_bg02_page_captured,stage_bg02_transform_contract_seen,stage_viewport_contract_seen,stage_camera_pair_contract_seen,stage_bg36_aux_projection_contract_seen,stage_bg33_quad_contract_seen,stage_bg12_layout_seen,stage_bg12_layout_captured,stage_bg12_contract_seen,stage_bg33_layout_seen,stage_bg33_layout_captured,stage_bg36_layout_seen,stage_bg36_layout_captured,stage_bg36_scroll_seen,stage_bg34_objects_seen;
static unsigned stage_constructor_asset_mask;
static unsigned gallery_move,gallery_pose;
static uint32_t gallery_previous;
static uint32_t stage_previous;
static unsigned stage_index,stage_layer;
static unsigned stage_tick;
static unsigned stage_bg12_updates;
static uint32_t stage_bg12_counter,stage_bg02_counter;
static uint32_t stage_bg33_counter;
static unsigned stage_bg33_updates;
static unsigned stage_bg02_resource_count;
static unsigned stage_bg36_scroll_ticks,stage_bg36_cloud_quads_projected;
static T123Bg36Scroll stage_bg36_scroll;
static soft2d_texture *battle_bg33_assets[4][6];
static int battle_bg33_ready;
static unsigned battle_bg33_tiles,battle_bg33_draws,battle_bg33_updates;
static uint32_t battle_bg33_counter,battle_bg33_slot_mask;
static soft2d_texture *battle_bg36_assets[4];
static soft2d_texture *battle_bg36_tiles[5][6];
static int battle_bg36_ready;
static unsigned battle_bg36_loaded,battle_bg36_draws,battle_bg36_updates;
static unsigned battle_bg36_base_tiles,battle_bg36_base_draws;
static unsigned battle_bg36_capture_seen;
static float battle_bg36_capture_camera_x,battle_bg36_capture_camera_y,battle_bg36_capture_camera_zoom;
static uint32_t battle_bg36_draw_mask,battle_bg36_base_slot_mask;
static T123Bg36Scroll battle_bg36_scroll;
static unsigned battle_stage_selection;
static unsigned battle_stage_selected_interactively;
static unsigned stage_bg37_scroll_ticks,stage_bg38_scroll_ticks;
static T123Bg37Scroll stage_bg37_scroll;
static T123Bg38Scroll stage_bg38_scroll;
static int stage_bg37_scroll_captured,stage_bg38_scroll_captured;
static int stage_bg33_layout_seen,stage_bg33_layout_captured;
static int suika_623c_action_seen,suika_623c_skill_uses,suika_623c_hit_delta,suika_623c_level5_hit_delta,suika_623c_level9_action_seen,suika_623c_531_hit_delta,suika_623c_531_objects,suika_623c_route_mask;
static int suika_623b_hit_delta,suika_623b_level5_hit_delta,suika_623b_level9_action_seen,suika_623b_level9_hit_delta,suika_623b_level9_objects,suika_623b_route_mask;
static float suika_623b_level9_object_x,suika_623b_level9_object_y;
static int suika_623b_level9_reaction_contract;
static int suika_821_debug_calls,suika_821_debug_damage,suika_821_debug_attacks,suika_821_debug_object_x,suika_821_debug_object_y,suika_821_debug_defender_x,suika_821_debug_defender_y,suika_821_debug_defender_pose,suika_821_debug_hurts,suika_821_debug_overlap;
static int sprite_region_crop_contract_seen;
static int stage_bg33_tiles_loaded;
static int stage_bg33_scroll_seen,stage_bg33_scroll_captured;
static uint32_t stage_bg33_slot_mask;
static unsigned stage_bg33_quad_draws;
static const char *stage_names[]={"bg00","bg01","bg02","bg03","bg04","bg05","bg06","bg10","bg11","bg12","bg13","bg14","bg15","bg16","bg17","bg18","bg30","bg31","bg32","bg33","bg34","bg35","bg36","bg37","bg38"};
#define STAGE_COUNT (sizeof stage_names/sizeof stage_names[0])
static int stage_uses_grid(void){return stage_index>=16;}
static unsigned stage_base_expected(void){return !strcmp(stage_names[stage_index],"bg33")?24u:30u;}
static unsigned stage_base_loaded(void){unsigned loaded=0;for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col])++loaded;return loaded;}
static int probe_bg12_animation_contract(void){
    uint32_t counter=0,first=0,second=0;
    t123_stage_animation_update(12u,&counter);if(counter!=1u)return 0;
    t123_stage_animation_update(12u,&counter);if(counter!=2u)return 0;
    t123_bg12_render_time_args(counter,&first,&second);if(first!=4u||second!=94u)return 0;
    counter=0;t123_stage_animation_update(10u,&counter);if(counter!=4u)return 0;
    counter=0;t123_stage_animation_update(11u,&counter);if(counter!=4u)return 0;
    counter=0;t123_stage_animation_update(13u,&counter);if(counter!=11u)return 0;
    counter=123u;t123_stage_animation_update(14u,&counter);if(counter!=123u)return 0;
    return 1;
}
static int probe_bg02_transform_contract(void){
    static const float expected[3][2]={{-332.0f,-472.0f},{0.0f,0.0f},{312.0f,-472.0f}};
    for(unsigned segment=0;segment<3;segment++){
        float x=0.0f,y=0.0f;
        if(!t123_bg02_sprite_offset(segment,&x,&y)||x!=expected[segment][0]||y!=expected[segment][1])return 0;
    }
    return !t123_bg02_sprite_offset(3,NULL,NULL);
}
static int probe_stage_viewport_contract(void){
    T123StageMatrixTranslation t;
    if(!t123_stage_viewport_translation(1.0f,0,0,0,0,1,1,&t)||t.x!=960.0f||t.y!=420.0f)return 0;
    if(!t123_stage_viewport_translation(2.0f,100,50,20,30,0.5f,2.0f,&t)||t.x!=420.0f||t.y!=50.0f)return 0;
    return !t123_stage_viewport_translation(0.0f,0,0,0,0,1,1,&t);
}
static int probe_stage_camera_pair_contract(void){
    static const float input[4][4]={{200.0f,0.0f,200.0f,0.0f},
                                    {200.0f,0.0f,300.0f,100.0f},
                                    {200.0f,0.0f,900.0f,0.0f},
                                    {200.0f,0.0f,2200.0f,0.0f}};
    static const float distance[4]={640.0f,657.34314f,780.0f,2080.0f};
    static const float zoom[4]={1.0f,0.97361630f,0.82051283f,0.5f};
    static const float center_x[4]={320.0f,328.67157f,550.0f,960.0f};
    T123StageCameraTarget target;
    for(unsigned i=0;i<4;i++){
        if(!t123_stage_camera_pair_target(input[i][0],input[i][1],input[i][2],input[i][3],&target))return 0;
        if(target.distance<distance[i]-0.0001f||target.distance>distance[i]+0.0001f||
           target.zoom<zoom[i]-0.00001f||target.zoom>zoom[i]+0.00001f||
           target.center_x<center_x[i]-0.0001f||target.center_x>center_x[i]+0.0001f)return 0;
    }
    if(!t123_stage_camera_pair_target(300.0f,500.0f,400.0f,500.0f,&target)||
       target.center_x!=350.0f)return 0;
    float zoom_step;
    if(!t123_stage_camera_zoom_step(0.5f,1.0f,&zoom_step)||
       zoom_step<0.50824f||zoom_step>0.50826f)return 0;
    if(!t123_stage_camera_zoom_step(1.0f,0.82051283f,&zoom_step)||
       zoom_step<0.96210f||zoom_step>0.96211f)return 0;
    if(!t123_stage_camera_zoom_step(0.501f,0.5f,&zoom_step)||zoom_step!=0.5f)return 0;
    float camera_x;
    if(!t123_stage_camera_x_step(400.0f,550.0f,1.0f,&camera_x)||camera_x!=410.0f)return 0;
    if(!t123_stage_camera_x_step(200.0f,550.0f,0.96210259f,&camera_x)||
       camera_x<332.60f||camera_x>332.61f)return 0;
    if(!t123_stage_camera_x_step(1000.0f,550.0f,0.96210259f,&camera_x)||
       camera_x<947.39f||camera_x>947.40f)return 0;
    float camera_y;
    if(!t123_stage_camera_y_target(0.0f,-500.0f,1.0f,&camera_y)||camera_y!=-100.0f)return 0;
    if(!t123_stage_camera_y_target(0.0f,-500.0f,0.59145278f,&camera_y)||
       camera_y<-18.292f||camera_y>-18.289f)return 0;
    if(!t123_stage_camera_y_target(500.0f,600.0f,1.0f,&camera_y)||camera_y!=-420.0f)return 0;
    if(!t123_stage_camera_y_step(-100.0f,-18.29056f,0.0f,-500.0f,
                                 0.59145278f,&camera_y)||
       camera_y<-76.821f||camera_y>-76.819f)return 0;
    if(!t123_stage_camera_y_step(-76.820335f,-18.29056f,0.0f,-500.0f,
                                 0.59145278f,&camera_y)||
       camera_y<-72.895f||camera_y>-72.892f)return 0;
    if(!t123_stage_camera_y_step(0.0f,-269.23077f,500.0f,500.0f,
                                 0.82051283f,&camera_y)||
       camera_y<-27.925f||camera_y>-27.921f)return 0;
    T123StageCamera live={550.0f,-18.29056f,0.59145278f,
                          550.0f,-76.820335f,0.59145278f};
    if(!t123_stage_camera_step(&live,200.0f,0.0f,900.0f,-500.0f)||
       live.target_x!=550.0f||live.x!=550.0f||
       live.zoom<0.59145f||live.zoom>0.59146f||
       live.y<-72.895f||live.y>-72.892f)return 0;
    T123StageCamera projection={550.0f,0.0f,0.82051283f,
                                550.0f,0.0f,0.82051283f};
    float screen_x,screen_y;
    if(!t123_stage_camera_project(&projection,200.0f,0.0f,0.0f,0.0f,
                                 &screen_x,&screen_y)||
       screen_x<32.81f||screen_x>32.83f||screen_y!=420.0f)return 0;
    if(!t123_stage_camera_project(&projection,900.0f,0.0f,0.0f,0.0f,
                                 &screen_x,&screen_y)||
       screen_x<607.17f||screen_x>607.19f)return 0;
    Fight fight_probe;fight_init(&fight_probe);fight_probe.ai=0;fight_probe.scene=SCENE_FIGHT;
    fight_step(&fight_probe,IN_RIGHT);
    if(fight_probe.p[0].x!=193||fight_probe.camera.x!=321.5f||
       !t123_stage_camera_project(&fight_probe.camera,(float)fight_probe.p[0].x,
                                  0.0f,0.0f,0.0f,&screen_x,&screen_y)||
       screen_x!=191.5f)return 0;
    fight_step(&fight_probe,0);fight_step(&fight_probe,IN_JUMP);
    if(fight_probe.p[0].y<=0||fight_probe.camera.y>=0.0f)return 0;
    return !t123_stage_camera_pair_target(0.0f,0.0f,0.0f,0.0f,NULL);
}
static void suika_623c_enter(Fight *probe){
    fight_step(probe,IN_RIGHT);
    fight_step(probe,IN_DOWN);
    fight_step(probe,IN_DOWN|IN_RIGHT);
    fight_step(probe,IN_RIGHT|IN_C_ATTACK);
}
static void suika_623b_enter(Fight *probe){
    fight_step(probe,IN_RIGHT);
    fight_step(probe,IN_DOWN);
    fight_step(probe,IN_DOWN|IN_RIGHT);
    fight_step(probe,IN_RIGHT|IN_SHOT);
}
static int suika_float_near(float a,float b,float epsilon){
    float delta=a-b;return delta>=-epsilon&&delta<=epsilon;
}
static int probe_suika_623c(void){
    T123Pattern suika={0};
    if(t123_resource_pattern(&resources,"data/character/suika/suika.pat",&suika))return 0;
    Fight base;fight_init(&base);
    probe_bind_character_patterns(&base,&suika,9,&suika,16);
    base.ai=0;base.scene=SCENE_FIGHT;base.p[1].x=220;
    suika_623c_enter(&base);
    suika_623c_action_seen=base.p[0].action==521;
    suika_623c_skill_uses=(int)base.p[0].skill_uses;
    unsigned initial_hp=(unsigned)base.p[1].hp;
    for(unsigned tick=0;tick<40;tick++){
        fight_step(&base,0);
        if(base.p[0].action==521)suika_623c_action_seen=1;
    }
    suika_623c_hit_delta=(int)(initial_hp-(unsigned)base.p[1].hp);
    if(suika_623c_action_seen&&suika_623c_skill_uses==1&&suika_623c_hit_delta==1000)suika_623c_route_mask|=1;

    Fight level5;fight_init(&level5);
    probe_bind_character_patterns(&level5,&suika,9,&suika,16);
    level5.ai=0;level5.scene=SCENE_FIGHT;level5.p[0].skill_level_5=1;level5.p[1].x=220;
    suika_623c_enter(&level5);
    int level5_action_seen=level5.p[0].action==526;
    initial_hp=(unsigned)level5.p[1].hp;
    for(unsigned tick=0;tick<40;tick++){
        fight_step(&level5,0);
        if(level5.p[0].action==526)level5_action_seen=1;
    }
    suika_623c_level5_hit_delta=(int)(initial_hp-(unsigned)level5.p[1].hp);
    if(level5_action_seen&&level5.p[0].skill_uses==1&&suika_623c_level5_hit_delta==500)suika_623c_route_mask|=2;

    T123Pattern remilia={0};
    if(t123_resource_pattern(&resources,"data/character/remilia/remilia.pat",&remilia)){t123_pattern_free(&suika);return 0;}
    Fight level9;fight_init(&level9);
    probe_bind_character_patterns(&level9,&suika,9,&remilia,6);
    level9.ai=0;level9.scene=SCENE_FIGHT;level9.p[0].skill_level_9=1;
    suika_623c_enter(&level9);
    suika_623c_level9_action_seen=level9.p[0].action==531;
    const T123Move *remilia_defense=t123_pattern_move(&remilia,602,0);
    if(remilia_defense&&t123_animation_set(&level9.p[1].animation,&remilia_defense->sequence,1,0)==0){
        level9.p[1].action=602;level9.p[1].stun=100;
        /* x86 pair oracle fixes Remilia at vulnerable 602/0/frame0; hold
           that authored frame while Suika's 20-tick startup completes. */
        level9.p[1].animation.duration=1000;
    }
    /* Keep fighter bodies separated while aligning Remilia with the 821
       spawn point (Suika x=320 plus the authored +100 object offset). */
    level9.p[0].x=320;level9.p[1].x=420;
    unsigned hp_before_531=(unsigned)level9.p[1].hp;
    int projectile_spawn_seen=0;
    int debug_captured=0,debug_object_x=0,debug_object_y=0,debug_owner_x=0,debug_owner_y=0;
    int debug_defender_x=0,debug_defender_y=0,debug_defender_pose=0,debug_hurt_count=0;
    int debug_damage=0,debug_attack_count=0,debug_left=0,debug_up=0,debug_right=0,debug_down=0;
    int impact_captured=0,impact_hp=-1,impact_action=-1,impact_stun=-1,impact_sequence=-1,impact_pose=-1,impact_pose_frame=-1,impact_action_ticks=-1;
    struct {float x,y;int alpha,active,pose,pose_frame;} motion[27]={0};
    unsigned motion_count=0;int motion_finished=0;
    struct {float x,y;int alpha,active,pose,pose_frame;} visual_motion[27]={0};
    unsigned visual_motion_count=0;int visual_motion_finished=0;
    /* The projectile spawns late in the startup. Leave enough controlled
       ticks to capture its complete 27-update x86 lifecycle. */
    for(unsigned tick=0;tick<50;tick++){
        fight_step(&level9,0);
        if(level9.p[0].action==531)suika_623c_level9_action_seen=1;
        if(!impact_captured&&level9.p[1].hp<(int)hp_before_531){
            const Fighter *victim=&level9.p[1];impact_captured=1;impact_hp=victim->hp;
            impact_action=victim->action;impact_stun=victim->stun;
            impact_sequence=victim->animation.sequence;impact_pose=victim->animation.pose;
            impact_pose_frame=victim->animation.pose_frame;impact_action_ticks=victim->action_ticks;
        }
        if(!motion_finished){
            for(unsigned oi=0;oi<sizeof level9.objects/sizeof level9.objects[0];oi++){
                T123Object *o=&level9.objects[oi];
                if(o->action!=821||o->animation.sequence!=0)continue;
                if(motion_count<27)motion[motion_count++]=(typeof(motion[0])){o->world_x,o->world_y,o->alpha,o->active,(int)o->animation.pose,(int)o->animation.pose_frame};
                if(!o->active)motion_finished=1;
                break;
            }
        }
        if(!visual_motion_finished){
            for(unsigned oi=0;oi<sizeof level9.objects/sizeof level9.objects[0];oi++){
                T123Object *o=&level9.objects[oi];
                if(o->action!=821||o->animation.sequence!=1)continue;
                if(visual_motion_count<27){
                    visual_motion[visual_motion_count].x=o->world_x;
                    visual_motion[visual_motion_count].y=o->world_y;
                    visual_motion[visual_motion_count].alpha=o->alpha;
                    visual_motion[visual_motion_count].active=o->active;
                    visual_motion[visual_motion_count].pose=(int)o->animation.pose;
                    visual_motion[visual_motion_count].pose_frame=(int)o->animation.pose_frame;
                    ++visual_motion_count;
                }
                if(!o->active)visual_motion_finished=1;
                break;
            }
        }
        if(level9.object_spawns>=2){projectile_spawn_seen=1;if(!debug_captured){
            for(unsigned oi=0;oi<sizeof level9.objects/sizeof level9.objects[0];oi++){
                T123Object *o=&level9.objects[oi];if(!o->active||o->action!=821||o->sequence!=0)continue;
                const T123Move *om=t123_pattern_move(&suika,821,0);
                const T123Pose *dp=fight_pose(&level9,1);
                debug_object_x=o->x;debug_object_y=o->y;debug_owner_x=level9.p[0].x;debug_owner_y=level9.p[0].y;
                debug_defender_x=level9.p[1].x;debug_defender_y=level9.p[1].y;
                debug_defender_pose=dp?(int)level9.p[1].animation.pose:-1;debug_hurt_count=dp?(int)dp->hurt_count:0;
                if(om&&om->poses&&om->sequence.count){const T123Pose *op=&om->poses[0];debug_damage=op->damage;debug_attack_count=(int)op->attack_count;
                    if(op->attack_count){debug_left=op->attack[0].left;debug_up=op->attack[0].up;debug_right=op->attack[0].right;debug_down=op->attack[0].down;}}
                debug_captured=1;break;
            }
        }}
    }
    int motion_contract=motion_count==27&&
        suika_float_near(motion[0].x,420.0f,0.001f)&&suika_float_near(motion[0].y,0.0f,0.001f)&&motion[0].alpha==255&&motion[0].active&&motion[0].pose==0&&
        suika_float_near(motion[1].x,387.11075f,0.005f)&&suika_float_near(motion[1].y,11.470705f,0.005f)&&motion[1].alpha==245&&motion[1].active&&motion[1].pose==0&&
        suika_float_near(motion[25].x,-402.23105f,0.005f)&&suika_float_near(motion[25].y,136.76758f,0.005f)&&motion[25].alpha==5&&motion[25].active&&motion[25].pose==3&&motion[25].pose_frame==1&&
        suika_float_near(motion[26].x,motion[25].x,0.001f)&&suika_float_near(motion[26].y,motion[25].y,0.001f)&&motion[26].alpha==5&&!motion[26].active&&motion[26].pose==3&&motion[26].pose_frame==1;
    int visual_motion_contract=visual_motion_count==27&&
        suika_float_near(visual_motion[0].x,420.0f,0.001f)&&suika_float_near(visual_motion[0].y,0.0f,0.001f)&&visual_motion[0].alpha==255&&visual_motion[0].active&&visual_motion[0].pose==0&&
        suika_float_near(visual_motion[1].x,420.0f,0.001f)&&suika_float_near(visual_motion[1].y,-0.5f,0.001f)&&visual_motion[1].alpha==245&&visual_motion[1].active&&visual_motion[1].pose==0&&visual_motion[1].pose_frame==1&&
        suika_float_near(visual_motion[25].x,420.0f,0.001f)&&suika_float_near(visual_motion[25].y,-162.5f,0.001f)&&visual_motion[25].alpha==5&&visual_motion[25].active&&visual_motion[25].pose==0&&visual_motion[25].pose_frame==0&&
        suika_float_near(visual_motion[26].x,visual_motion[25].x,0.001f)&&suika_float_near(visual_motion[26].y,visual_motion[25].y,0.001f)&&visual_motion[26].alpha==5&&!visual_motion[26].active&&visual_motion[26].pose==0&&visual_motion[26].pose_frame==0;
    int impact_contract=impact_captured&&impact_hp==(int)hp_before_531-800&&
        impact_action==50&&impact_stun==20&&impact_sequence==0&&impact_pose==0&&impact_action_ticks==0;
    FILE *motion_file=fopen("ux0:data/touhou123vita-suika821-motion.tsv","w");
    if(motion_file){fprintf(motion_file,"tick\tx\ty\talpha\tactive\tpose\tpose_frame\n");for(unsigned i=0;i<motion_count;i++)fprintf(motion_file,"%u\t%.6f\t%.6f\t%d\t%d\t%d\t%d\n",i+1,motion[i].x,motion[i].y,motion[i].alpha,motion[i].active,motion[i].pose,motion[i].pose_frame);fclose(motion_file);}
    FILE *visual_motion_file=fopen("ux0:data/touhou123vita-suika821-seq1-motion.tsv","w");
    if(visual_motion_file){fprintf(visual_motion_file,"tick\tx\ty\talpha\tactive\tpose\tpose_frame\n");for(unsigned i=0;i<visual_motion_count;i++)fprintf(visual_motion_file,"%u\t%.6f\t%.6f\t%d\t%d\t%d\t%d\n",i+1,visual_motion[i].x,visual_motion[i].y,visual_motion[i].alpha,visual_motion[i].active,visual_motion[i].pose,visual_motion[i].pose_frame);fclose(visual_motion_file);}
    FILE *debug_file=fopen("ux0:data/touhou123vita-suika821-debug.json","w");
    if(debug_file){fprintf(debug_file,"{\"captured\":%d,\"object\":[%d,%d],\"owner\":[%d,%d],\"defender\":[%d,%d],\"defender_pose\":%d,\"hurt_count\":%d,\"damage\":%d,\"attack_count\":%d,\"attack_box\":[%d,%d,%d,%d],\"motion_samples\":%u,\"motion_contract\":%d,\"visual_motion_samples\":%u,\"visual_motion_contract\":%d,\"impact_captured\":%d,\"impact_contract\":%d,\"impact_hp\":%d,\"impact_action\":%d,\"impact_stun\":%d,\"impact_sequence\":%d,\"impact_pose\":%d,\"impact_pose_frame\":%d,\"impact_action_ticks\":%d}\n",debug_captured,debug_object_x,debug_object_y,debug_owner_x,debug_owner_y,debug_defender_x,debug_defender_y,debug_defender_pose,debug_hurt_count,debug_damage,debug_attack_count,debug_left,debug_up,debug_right,debug_down,motion_count,motion_contract,visual_motion_count,visual_motion_contract,impact_captured,impact_contract,impact_hp,impact_action,impact_stun,impact_sequence,impact_pose,impact_pose_frame,impact_action_ticks);fclose(debug_file);}
    suika_623c_531_hit_delta=(int)(hp_before_531-(unsigned)level9.p[1].hp);
    suika_623c_531_objects=(int)level9.object_spawns;
    if(suika_623c_level9_action_seen&&level9.p[0].skill_uses==1)suika_623c_route_mask|=4;
    if(projectile_spawn_seen&&suika_623c_531_objects==2&&suika_623c_531_hit_delta==800)suika_623c_route_mask|=16;
    t123_pattern_free(&remilia);

    Fight locked;fight_init(&locked);
    probe_bind_character_patterns(&locked,&suika,9,&suika,16);
    locked.ai=0;locked.scene=SCENE_FIGHT;locked.p[0].skill_level_5=1;locked.p[0].skill_level_9=1;
    suika_623c_enter(&locked);
    int blocked=locked.p[0].skill_uses==0&&locked.p[0].action!=521&&locked.p[0].action!=526&&locked.p[0].action!=531;
    if(blocked)suika_623c_route_mask|=8;

    int passed=suika_623c_route_mask==31&&motion_contract&&visual_motion_contract&&impact_contract;
    t123_pattern_free(&suika);
    return passed;
}

static int probe_suika_623b(void){
    T123Pattern suika={0};
    if(t123_resource_pattern(&resources,"data/character/suika/suika.pat",&suika))return 0;
    Fight base;fight_init(&base);probe_bind_character_patterns(&base,&suika,9,&suika,16);
    base.ai=0;base.scene=SCENE_FIGHT;base.p[1].x=220;suika_623b_enter(&base);
    int base_action=base.p[0].action==520,uses=(int)base.p[0].skill_uses;unsigned hp=(unsigned)base.p[1].hp;
    for(unsigned tick=0;tick<42;tick++)fight_step(&base,0);
    suika_623b_hit_delta=(int)(hp-(unsigned)base.p[1].hp);
    if(base_action&&uses==1&&base.p[0].skill_uses==1&&suika_623b_hit_delta==1000)suika_623b_route_mask|=1;

    Fight level5;fight_init(&level5);probe_bind_character_patterns(&level5,&suika,9,&suika,16);
    level5.ai=0;level5.scene=SCENE_FIGHT;level5.p[0].skill_level_5=1;level5.p[1].x=220;
    suika_623b_enter(&level5);int level5_action=level5.p[0].action==525;hp=(unsigned)level5.p[1].hp;
    for(unsigned tick=0;tick<42;tick++)fight_step(&level5,0);
    suika_623b_level5_hit_delta=(int)(hp-(unsigned)level5.p[1].hp);
    if(level5_action&&level5.p[0].skill_uses==1&&suika_623b_level5_hit_delta==500)suika_623b_route_mask|=2;

    Fight level9;fight_init(&level9);probe_bind_character_patterns(&level9,&suika,9,&suika,16);
    level9.ai=0;level9.scene=SCENE_FIGHT;level9.p[0].skill_level_9=1;
    /* Isolate the RNG/spawn oracle from body push: full-size collision
       boxes need more than the old 31-unit gap to leave owner x unchanged. */
    level9.p[0].x=320;level9.p[0].y=0;level9.p[1].x=400;level9.p[1].y=0;
    fight_step(&level9,IN_RIGHT);level9.p[1].y=0;level9.p[1].vy=0;
    fight_step(&level9,IN_DOWN);level9.p[1].y=0;level9.p[1].vy=0;
    fight_step(&level9,IN_DOWN|IN_RIGHT);level9.p[1].y=0;level9.p[1].vy=0;
    fight_step(&level9,IN_RIGHT|IN_SHOT);level9.p[1].y=0;level9.p[1].vy=0;
    suika_623b_level9_action_seen=level9.p[0].action==530&&level9.p[0].skill_uses==1;
    hp=(unsigned)level9.p[1].hp;
    int response_checked=0,response_ok=0;
    for(unsigned tick=0;tick<42;tick++){
        level9.p[1].y=0;level9.p[1].vy=0;fight_step(&level9,0);
        if(level9.p[0].action==530)suika_623b_level9_action_seen=1;
        if(!response_checked&&(unsigned)level9.p[1].hp<hp){
            response_checked=1;
            int response_action=level9.p[1].action;
            int response_stun=level9.p[1].stun;
            unsigned hp_after_hit=(unsigned)level9.p[1].hp;
            fight_step(&level9,0);
            response_ok=response_action==50&&response_stun==20&&
                (unsigned)level9.p[1].hp==hp_after_hit&&
                !level9.objects[0].active&&level9.p[0].hits==1;
        }
    }
    suika_623b_level9_reaction_contract=response_checked&&response_ok;
    suika_623b_level9_hit_delta=(int)(hp-(unsigned)level9.p[1].hp);
    suika_623b_level9_objects=(int)level9.object_spawns;
    for(unsigned i=0;i<sizeof level9.objects/sizeof level9.objects[0];i++){
        T123Object *object=&level9.objects[i];
        if(object->action==821&&object->owner_action==530){
            suika_623b_level9_object_x=object->world_x;
            suika_623b_level9_object_y=object->world_y;
            break;
        }
    }
    if(suika_623b_level9_action_seen)suika_623b_route_mask|=4;
    if(suika_623b_level9_hit_delta==800&&suika_623b_level9_objects==1)suika_623b_route_mask|=16;
    if(suika_float_near(suika_623b_level9_object_x,350.62018f,0.01f)&&
       suika_float_near(suika_623b_level9_object_y,81.13174f,0.01f))suika_623b_route_mask|=32;
    if(suika_623b_level9_reaction_contract)suika_623b_route_mask|=64;

    Fight locked;fight_init(&locked);probe_bind_character_patterns(&locked,&suika,9,&suika,16);
    locked.ai=0;locked.scene=SCENE_FIGHT;locked.p[0].skill_level_5=1;locked.p[0].skill_level_9=1;
    suika_623b_enter(&locked);
    if(!locked.p[0].skill_uses&&locked.p[0].action!=520&&locked.p[0].action!=525&&locked.p[0].action!=530)suika_623b_route_mask|=8;
    t123_pattern_free(&suika);return suika_623b_route_mask==127;
}
static int probe_bg36_aux_projection_contract(void){
    static const float expected[4][4]={{510.0f,-380.0f,610.0f,-330.0f},
                                       {610.0f,50.0f,710.0f,100.0f},
                                       {960.0f,420.0f,1060.0f,470.0f},
                                       {910.0f,370.0f,1010.0f,420.0f}};
    static const float x[4]={-400.0f,-300.0f,0.0f,0.0f};
    static const float y[4]={-750.0f,-320.0f,0.0f,0.0f};
    T123StageQuad q;
    for(unsigned slot=0;slot<4;slot++){
        if(!t123_bg36_project_aux_quad(slot,100.0f,50.0f,x[slot],y[slot],
                                       1.0f,0.0f,0.0f,0.0f,0.0f,1.0f,1.0f,&q))return 0;
        if(q.x[0]!=expected[slot][0]||q.y[0]!=expected[slot][1]||
           q.x[3]!=expected[slot][2]||q.y[3]!=expected[slot][3])return 0;
    }
    return 1;
}
static int probe_bg33_quad_contract(void){
    T123Bg33RenderSlot slot;T123StageQuad q;
    if(!t123_bg33_render_slot(0,0,&slot)||!t123_bg33_project_slot_quad(&slot,0,0,1,0,0,0,0,1,1,&q))return 0;
    if(q.x[0]!=260.0f||q.y[0]!=-440.0f||q.x[3]!=516.0f||q.y[3]!=-184.0f)return 0;
    if(!t123_bg33_render_slot(0,24,&slot)||!t123_bg33_project_slot_quad(&slot,0,0,1,0,0,0,0,1,1,&q))return 0;
    return q.y[0]==584.0f&&q.y[3]==840.0f;
}
static const char *stage_extra_paths[5][4]={
    {"data/background/bg12/tori1.cv2","data/background/bg12/tori2.cv2",NULL,NULL},
    {"data/background/bg33/0001.cv2","data/background/bg33/0002.cv2",NULL,NULL},
    {"data/background/bg36/tori1.cv2","data/background/bg36/tori2.cv2","data/background/bg36/clowd_l.cv2","data/background/bg36/clowd_s.cv2"},
    {"data/background/bg37/tori1.cv2","data/background/bg37/clowd_l.cv2","data/background/bg37/clowd_s.cv2",NULL},
    {"data/background/bg38/clowd_l.cv2","data/background/bg38/clowd_s.cv2",NULL,NULL}
};
static const char *stage_extra_stage_names[5]={"bg12","bg33","bg36","bg37","bg38"};
static int stage_extra_set(void){for(int i=0;i<5;i++)if(!strcmp(stage_names[stage_index],stage_extra_stage_names[i]))return i;return -1;}
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
            if(stage_layer&&strcmp(stage_names[stage_index],"bg12")&&strcmp(stage_names[stage_index],"bg02"))continue;
            snprintf(path,sizeof path,"data/background/%s/0000_%02u.cv2",stage_names[stage_index],row*6+col);
        }else{
            unsigned prefix=!strcmp(stage_names[stage_index],"bg34")?0:(stage_layer?1:0);
            if(strcmp(stage_names[stage_index],"bg34"))prefix=0;
            if(!strcmp(stage_names[stage_index],"bg33")&&(row*6+col)>=24)continue;
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
    for(unsigned i=0;i<4;i++){if(stage_extras[i])soft2d_free_texture(stage_extras[i]);stage_extras[i]=NULL;}
    for(unsigned i=0;i<30;i++){if(stage_objects[i])soft2d_free_texture(stage_objects[i]);stage_objects[i]=NULL;}
    for(unsigned i=0;i<16;i++){if(stage_bg02_page[i])soft2d_free_texture(stage_bg02_page[i]);stage_bg02_page[i]=NULL;}
}
static void prepare_battle_bg33(void){
    battle_bg33_tiles=0;
    for(unsigned row=0;row<4;row++)for(unsigned col=0;col<6;col++){
        if(battle_bg33_assets[row][col])soft2d_free_texture(battle_bg33_assets[row][col]);
        battle_bg33_assets[row][col]=NULL;
        char path[128];snprintf(path,sizeof path,"data/background/bg33/0000[%02u][%02u].cv2",row+1,col+1);
        battle_bg33_assets[row][col]=soft2d_load_dat(&resources,path,NULL);
        if(battle_bg33_assets[row][col])battle_bg33_tiles++;
    }
    battle_bg33_ready=battle_bg33_tiles==24u;
    battle_bg33_counter=0;battle_bg33_draws=0;battle_bg33_updates=0;battle_bg33_slot_mask=0;
}
static void draw_battle_bg33(const Fight *g){
    if(!battle_bg33_ready)return;
    const float framebuffer_scale=544.0f/480.0f;
    for(unsigned slot=0;slot<30;slot++){
        T123Bg33RenderSlot draw;T123StageQuad quad;
        if(!t123_bg33_render_slot(battle_bg33_counter,slot,&draw))continue;
        unsigned row=draw.sprite_index/6u,col=draw.sprite_index%6u;
        soft2d_texture *tile=battle_bg33_assets[row][col];if(!tile)continue;
        if(!t123_bg33_project_slot_quad(&draw,0,0,g->camera.zoom,g->camera.x,
                                        g->camera.y,0,0,1,1,&quad))continue;
        float qx[4],qy[4];
        for(unsigned corner=0;corner<4;corner++){
            qx[corner]=117.33f+quad.x[corner]*framebuffer_scale;
            qy[corner]=quad.y[corner]*framebuffer_scale;
        }
        if(soft2d_draw_texture_quad(tile,qx,qy)){
            battle_bg33_draws++;battle_bg33_slot_mask|=1u<<slot;
        }
    }
}
static void prepare_battle_bg36(void){
    static const char *paths[4]={
        "data/background/bg36/tori1.cv2","data/background/bg36/tori2.cv2",
        "data/background/bg36/clowd_l.cv2","data/background/bg36/clowd_s.cv2"
    };
    battle_bg36_loaded=0;
    battle_bg36_base_tiles=0;
    for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){
        if(battle_bg36_tiles[row][col])soft2d_free_texture(battle_bg36_tiles[row][col]);
        char tile_path[128];
        snprintf(tile_path,sizeof tile_path,"data/background/bg36/0000[%02u][%02u].cv2",row+1u,col+1u);
        battle_bg36_tiles[row][col]=soft2d_load_dat(&resources,tile_path,NULL);
        if(battle_bg36_tiles[row][col])battle_bg36_base_tiles++;
    }
    for(unsigned i=0;i<4;i++){
        if(battle_bg36_assets[i])soft2d_free_texture(battle_bg36_assets[i]);
        battle_bg36_assets[i]=soft2d_load_dat(&resources,paths[i],NULL);
        if(battle_bg36_assets[i])battle_bg36_loaded++;
    }
    battle_bg36_ready=battle_bg36_loaded==4u;
    battle_bg36_draws=battle_bg36_updates=0;battle_bg36_draw_mask=0;
    battle_bg36_base_draws=0;battle_bg36_base_slot_mask=0;
    t123_bg36_scroll_init(&battle_bg36_scroll);
}
static void draw_battle_bg36_aux(const Fight *g,unsigned i,float framebuffer_scale){
    if(i>=4u||!battle_bg36_assets[i])return;
    static const float base_x[4]={0.0f,0.0f,-400.0f,-300.0f};
    static const float base_y[4]={0.0f,0.0f,-750.0f,-320.0f};
    soft2d_texture *asset=battle_bg36_assets[i];
    float x=base_x[i],y=base_y[i];
    if(i==2u)x=battle_bg36_scroll.clowd_l_x;
    else if(i==3u)x=battle_bg36_scroll.clowd_s_x;
    T123StageQuad quad;
    if(!t123_bg36_project_aux_quad(i,(float)soft2d_texture_get_width(asset),
            (float)soft2d_texture_get_height(asset),x,y,g->camera.zoom,
            g->camera.x,g->camera.y,0.0f,0.0f,1.0f,1.0f,&quad))return;
    float qx[4],qy[4];
    for(unsigned corner=0;corner<4;corner++){
        qx[corner]=117.33f+quad.x[corner]*framebuffer_scale;
        qy[corner]=quad.y[corner]*framebuffer_scale;
    }
    if(soft2d_draw_texture_quad(asset,qx,qy)){
        battle_bg36_draws++;battle_bg36_draw_mask|=1u<<i;
    }
}
static void draw_battle_bg36(const Fight *g){
    if(!battle_bg36_ready)return;
    const float framebuffer_scale=544.0f/480.0f;
    /* PE pass 1 draws clowd_l/clowd_s (slots 2/3) before the tile grid. */
    draw_battle_bg36_aux(g,2u,framebuffer_scale);
    draw_battle_bg36_aux(g,3u,framebuffer_scale);
    for(unsigned slot=0;slot<30;slot++){
        unsigned row=slot/6u,col=slot%6u;
        soft2d_texture *tile=battle_bg36_tiles[row][col];if(!tile)continue;
        T123StageQuad quad;
        if(!t123_bg36_project_tile_quad(slot,&g->camera,&quad))continue;
        float qx[4],qy[4];
        for(unsigned corner=0;corner<4;corner++){
            qx[corner]=117.33f+quad.x[corner]*framebuffer_scale;
            qy[corner]=quad.y[corner]*framebuffer_scale;
        }
        if(soft2d_draw_texture_quad(tile,qx,qy)){
            battle_bg36_base_draws++;battle_bg36_base_slot_mask|=1u<<slot;
        }
    }
    /* PE pass 2 draws the two fixed torii (slots 0/1) over the tile grid. */
    draw_battle_bg36_aux(g,0u,framebuffer_scale);
    draw_battle_bg36_aux(g,1u,framebuffer_scale);
}
static void stage_load_extras(void){
    if(!strcmp(stage_names[stage_index],"bg02")){
        static const char *directory[3]={"left/a","center/b","right/c"};
        if(stage_layer<1||stage_layer>3)return;
        unsigned segment=stage_layer-1;
        for(unsigned i=0;i<16;i++){
            char path[128];snprintf(path,sizeof path,"data/background/bg02/%s%02u.cv2",directory[segment],i);
            if(!stage_bg02_page[i])stage_bg02_page[i]=soft2d_load_dat(&resources,path,NULL);
        }
        return;
    }
    int set=stage_extra_set();
    if(set>=0){unsigned expected=0,loaded=0;for(unsigned i=0;i<4;i++){if(stage_extra_paths[set][i]){++expected;if(!stage_extras[i])stage_extras[i]=soft2d_load_dat(&resources,stage_extra_paths[set][i],NULL);if(stage_extras[i])++loaded;}}if(loaded==expected)stage_constructor_asset_mask|=1u<<set;return;}
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
    unsigned loaded=0;for(unsigned i=0;i<30;i++)if(stage_objects[i])++loaded;if(loaded==30)stage_bg34_objects_seen=1;
}
static unsigned probe_bg02_resources(void){
    static const char *directory[3]={"left/a","center/b","right/c"};
    unsigned decoded=0;
    for(unsigned segment=0;segment<3;segment++)for(unsigned i=0;i<16;i++){
        char path[128];snprintf(path,sizeof path,"data/background/bg02/%s%02u.cv2",directory[segment],i);
        soft2d_texture *asset=soft2d_load_dat(&resources,path,NULL);
        if(asset){++decoded;soft2d_free_texture(asset);}
    }
    return decoded;
}
static int stage_step(Fight *g,uint32_t input){
    uint32_t edge=input&~stage_previous;stage_previous=input;
    if(!stage_mode){if(g->scene!=SCENE_MENU||!(edge&IN_AI))return 0;stage_mode=1;stage_index=0;stage_layer=0;stage_tick=0;stage_bg12_updates=0;stage_bg12_counter=0;stage_bg02_counter=0;stage_bg36_scroll_ticks=0;stage_load_tiles();fight_step(g,0);return 1;}
    if(edge&IN_BACK){stage_mode=0;gallery_previous=0;stage_previous=0;fight_step(g,0);return 1;}
    stage_tick++;
    if(!strcmp(stage_names[stage_index],"bg12")){t123_stage_animation_update(12u,&stage_bg12_counter);stage_bg12_updates++;}
    if(!strcmp(stage_names[stage_index],"bg02"))stage_bg02_counter++;
    if(!strcmp(stage_names[stage_index],"bg33")){t123_stage_animation_update(33u,&stage_bg33_counter);stage_bg33_updates++;}
    if(!strcmp(stage_names[stage_index],"bg36")){t123_bg36_scroll_update(&stage_bg36_scroll);stage_bg36_scroll_ticks++;}
    if(!strcmp(stage_names[stage_index],"bg37")){t123_bg37_scroll_update(&stage_bg37_scroll);stage_bg37_scroll_ticks++;}
    if(!strcmp(stage_names[stage_index],"bg38")){t123_bg38_scroll_update(&stage_bg38_scroll);stage_bg38_scroll_ticks++;}
    if(edge&IN_LEFT){stage_index=(stage_index+STAGE_COUNT-1)%STAGE_COUNT;stage_layer=0;stage_navigation_seen=1;stage_load_tiles();if(!strcmp(stage_names[stage_index],"bg12")){stage_bg12_counter=0;stage_bg12_updates=0;}if(!strcmp(stage_names[stage_index],"bg02"))stage_bg02_counter=0;if(!strcmp(stage_names[stage_index],"bg36")){t123_bg36_scroll_init(&stage_bg36_scroll);stage_bg36_scroll_ticks=0;}if(!strcmp(stage_names[stage_index],"bg37")){t123_bg37_scroll_init(&stage_bg37_scroll);stage_bg37_scroll_ticks=0;}if(!strcmp(stage_names[stage_index],"bg38")){t123_bg38_scroll_init(&stage_bg38_scroll);stage_bg38_scroll_ticks=0;}}
    else if(edge&IN_RIGHT){stage_index=(stage_index+1)%STAGE_COUNT;stage_layer=0;stage_navigation_seen=1;stage_load_tiles();if(!strcmp(stage_names[stage_index],"bg12")){stage_bg12_counter=0;stage_bg12_updates=0;}if(!strcmp(stage_names[stage_index],"bg02"))stage_bg02_counter=0;if(!strcmp(stage_names[stage_index],"bg36")){t123_bg36_scroll_init(&stage_bg36_scroll);stage_bg36_scroll_ticks=0;}if(!strcmp(stage_names[stage_index],"bg37")){t123_bg37_scroll_init(&stage_bg37_scroll);stage_bg37_scroll_ticks=0;}if(!strcmp(stage_names[stage_index],"bg38")){t123_bg38_scroll_init(&stage_bg38_scroll);stage_bg38_scroll_ticks=0;}}
    if(edge&(IN_JUMP|IN_DOWN)){
        if(!strcmp(stage_names[stage_index],"bg34"))stage_layer=(stage_layer+1)%4;
        else if(!strcmp(stage_names[stage_index],"bg02"))stage_layer=(stage_layer+1)%4;
        else if(!strcmp(stage_names[stage_index],"bg36"))stage_layer=(stage_layer+1)%3;
        else if(!strcmp(stage_names[stage_index],"bg37")||!strcmp(stage_names[stage_index],"bg38"))stage_layer=(stage_layer+1)%3;
        else if(!strcmp(stage_names[stage_index],"bg12"))stage_layer=(stage_layer+1)%3;
        else if(!strcmp(stage_names[stage_index],"bg33"))stage_layer=(stage_layer+1)%4;
        else stage_layer=stage_layer?0:1;
        stage_navigation_seen=1;stage_load_tiles();if(stage_layer>=1)stage_load_extras();
    }
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
    if(f==173)return IN_BACK;
    if(f==95)return IN_JUMP;
    if(f==183)return IN_AI; /* Keep the target stationary while testing natural approach and A timing. */
    if(f>=500&&f<526)return IN_RIGHT;
    if(f==526)return IN_MELEE;
    if(f>=92&&f<=108&&f%2==0)return IN_RIGHT;
    if(f==112)return IN_RIGHT;
    if(f>=114&&f<=130&&f%2==0)return IN_RIGHT;
    if(f==110||f==131||f==137||f==142||f==147||f==152||f==157||f==167||f==169||f==171)return IN_JUMP;
    if(f==111)return IN_DOWN;
    if(f==134)return 0; /* Release the layer-2 transition key. */
    if(f==135)return IN_JUMP; /* BG33 layer 3: original 30 draw-slot scroll. */
    if(f==136||f==140||f==145||f==150||f==155)return IN_RIGHT;
    if(f==148)return IN_DOWN; /* BG36 constructor layout page. */
    if(f==154)return IN_DOWN; /* BG37 cloud update view. */
    if(f==158)return IN_DOWN; /* BG38 cloud update view. */
    if(f==159||f==161||f==163||f==165)return IN_LEFT;
    if(f==132||f==138||f==139||f==149||f==153||f==156||f==160||f==162||f==164||f==166||f==168||f==170||f==172)return 0;
    if(f==133)return IN_JUMP; /* BG33 layer 2: source grid plus constructor anchors. */
    if(f==143)return IN_DOWN; /* Enter BG36's constructor/scroll schematic layer. */
    if(f>=141&&f<=160)return 0;
    if(f>=141&&f<=177&&f%2==1)return IN_RIGHT;
    if(f<80&&f%4==0)return IN_RIGHT;
    if(f==178||f==180)return IN_CONFIRM;
    if(f==179)return IN_DOWN; /* Exercise the practice stage selector before entering the fight. */
    unsigned in=0;
    if(f>=182 && f<281)in|=IN_RIGHT;
    if(f==182)in|=IN_JUMP;
    if(f==281)in|=IN_MELEE;
    if(f==307||f==339||f==371||f==403)in|=IN_RIGHT;
    if(f==309||f==341||f==373||f==405)in|=IN_RIGHT;
    if(f==311||f==375)in|=IN_RIGHT|IN_SHOT;
    if(f==343||f==407)in|=IN_RIGHT|IN_C_ATTACK;
    if(f==439)in|=IN_LEFT|IN_SHOT;
    if(f==471)in|=IN_LEFT|IN_C_ATTACK;
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
    Fight probe;fight_init(&probe);probe_bind_patterns(&probe,&attacker,&defender);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200)return 0;
    probe.p[0].animation.current_frame=6;
    fight_step(&probe,IN_RIGHT|IN_SHOT);
    if(probe.p[0].action!=408||probe.p[0].action_index!=2||probe.p[0].b_hits!=1||probe.p[1].hp!=9750)return 0;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;
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
static int probe_fighter_boxes_overlap(const T123Box *a,const Fighter *pa,
                                      const T123Box *b,const Fighter *pb){
    int al=pa->x+(pa->face>0?a->left:-a->right);
    int ar=pa->x+(pa->face>0?a->right:-a->left);
    int bl=pb->x+(pb->face>0?b->left:-b->right);
    int br=pb->x+(pb->face>0?b->right:-b->left);
    int at=-pa->y+a->up,ab=-pa->y+a->down;
    int bt=-pb->y+b->up,bb=-pb->y+b->down;
    return al<br&&bl<ar&&at<bb&&bt<ab;
}
static int probe_place_for_attack(Fight *probe,const T123Move *attack,const T123Pattern *defender){
    const T123Move *hurt=t123_pattern_move(defender,0,0);if(!hurt)return -1;
    for(unsigned ap=0;ap<attack->sequence.count;ap++){
        const T123Pose *hit=&attack->poses[ap];if(!hit->damage||!hit->attack_count)continue;
        for(unsigned hp=0;hp<hurt->sequence.count;hp++){
            const T123Pose *body=&hurt->poses[hp];if(!body->hurt_count)continue;
            for(unsigned ai=0;ai<hit->attack_count;ai++)for(unsigned bi=0;bi<body->hurt_count;bi++){
                const T123Box *a=&hit->attack[ai],*b=&body->hurt[bi];int ybase=(b->up+b->down-a->up-a->down)/2;
                for(int dy=-6;dy<=6;dy++){
                    int ax=300,by=ybase+dy;
                    int bx=ax+(a->left+a->right+b->left+b->right)/2;
                    int al=ax+a->left,ar=ax+a->right,bl=bx-b->right,br=bx-b->left;
                    int at=a->up,ab=a->down,bt=-by+b->up,bb=-by+b->down;
                    if(bx<=ax||bx>1240||bx<40||al>=br||bl>=ar||at>=bb||bt>=ab)continue;
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
        probe_bind_character_patterns(&probe,&patterns[0],(int)character,
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
static int probe_character_a_attack_natural(unsigned character){
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
        probe_bind_character_patterns(&probe,&patterns[0],(int)character,
            &patterns[1],(int)roster_index[1]);
        probe.ai=0;probe.scene=SCENE_FIGHT;
        for(unsigned tick=0;tick<130;tick++)fight_step(&probe,IN_RIGHT);
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
static unsigned probe_roster_a_natural_attacks(void){
    unsigned saved0=roster_index[0],saved1=roster_index[1],mask=0;
    for(unsigned character=0;character<ROSTER_COUNT;character++)
        if(load_character(0,character)==0&&probe_character_a_attack_natural(character))mask|=1u<<character;
    load_character(0,saved0);load_character(1,saved1);
    return mask;
}
/* Frame 0 is the command's own simulation update; it can already hit. */
static int probe_record_bc_contact(const Fight *probe,int id,int button,unsigned before,unsigned frame,
                                  unsigned *hit_frame,unsigned *hit_damage,int *hit_source,
                                  unsigned *hit_pose,int *hit_gap){
                if(probe->p[1].hp<before){
                    unsigned damage=before-probe->p[1].hp;int exact=0,source_action=id;unsigned source_pose=0;
                    const T123Pose *hit=fight_pose(probe,0);
                    if(hit&&damage==(unsigned)hit->damage)exact=1;
                    for(unsigned oi=0;!exact&&oi<sizeof probe->objects/sizeof probe->objects[0];oi++){
                        const T123Object *object=&probe->objects[oi];
                        if(object->owner!=0||object->owner_action!=id)continue;
                        const T123Move *source=t123_pattern_move(&patterns[0],object->action,object->sequence);
                        if(source&&object->animation.pose<source->sequence.count&&
                            damage==(unsigned)source->poses[object->animation.pose].damage){exact=1;source_action=object->action;source_pose=object->animation.pose;}
                    }
                    unsigned hits=button==IN_SHOT?probe->p[0].b_hits:probe->p[0].c_hits;
                    if(exact&&hits>0){if(hit_frame)*hit_frame=frame;if(hit_damage)*hit_damage=damage;if(hit_source)*hit_source=source_action;if(hit_pose)*hit_pose=source_pose;if(hit_gap)*hit_gap=probe->p[1].x-probe->p[0].x;return id;}
                }
    return 0;
}
static int probe_character_natural_bc(unsigned character,int button,int required_action,unsigned *candidate_mask,
                                      unsigned *hit_frame,unsigned *hit_damage,
                                       int *hit_source,unsigned *hit_pose,int *hit_gap){
    static const int b_actions[]={400,401,402,403,407,408,404,405,406,409};
    static const uint32_t b_inputs[]={IN_SHOT,IN_RIGHT|IN_SHOT,IN_DOWN|IN_SHOT,
        IN_DOWN|IN_RIGHT|IN_SHOT,IN_LEFT|IN_SHOT,IN_RIGHT|IN_SHOT,IN_SHOT,
        IN_RIGHT|IN_SHOT,IN_DOWN|IN_SHOT,IN_LEFT|IN_SHOT};
    static const int c_actions[]={410,411,412,418,414,415,416,417};
    static const uint32_t c_inputs[]={IN_C_ATTACK,IN_RIGHT|IN_C_ATTACK,
        IN_DOWN|IN_C_ATTACK,IN_RIGHT|IN_C_ATTACK,IN_C_ATTACK,
        IN_RIGHT|IN_C_ATTACK,IN_DOWN|IN_C_ATTACK,IN_LEFT|IN_C_ATTACK};
    const int *actions=button==IN_SHOT?b_actions:c_actions;
    const uint32_t *inputs=button==IN_SHOT?b_inputs:c_inputs;
    unsigned count=button==IN_SHOT?sizeof b_actions/sizeof b_actions[0]:sizeof c_actions/sizeof c_actions[0];
    *candidate_mask=0;if(hit_frame)*hit_frame=0;if(hit_damage)*hit_damage=0;
    if(hit_source)*hit_source=0;if(hit_pose)*hit_pose=0;if(hit_gap)*hit_gap=0;
    unsigned *reached_mask=button==IN_SHOT?&roster_b_reached_mask[character]:&roster_c_reached_mask[character];
    *reached_mask=0;
    if(button==IN_C_ATTACK){roster_c_418_overlap_seen[character]=0;roster_c_418_horizontal_overlap_seen[character]=0;roster_c_418_vertical_overlap_seen[character]=0;roster_c_418_min_active_gap[character]=INT32_MAX;roster_c_418_min_signed_gap[character]=0;roster_c_418_min_horizontal_gap[character]=INT32_MAX;roster_c_418_min_vertical_gap[character]=INT32_MAX;}
    static const int opponent_positions[]={300,320,340,360,380,400,420};
    for(unsigned route=0;route<count;route++){
        int id=actions[route];
        if(required_action&&id!=required_action)continue;
        const T123Move *move=probe_selected_attack(&patterns[0],id);
        int damaging=0;
        if(move)for(unsigned pose=0;pose<move->sequence.count;pose++)
            if(move->poses[pose].damage&&move->poses[pose].attack_count){damaging=1;break;}
        /* Alice's 66B has no direct PAT attack box: the original route emits
           object 849 from its action handler. Include it in the natural
           probe so the object path is tested instead of being mislabeled as
           an absent attack. Alice/Suwako 66C use the same object-backed rule. */
        if((button==IN_SHOT&&id==408&&character==3)||
           (button==IN_C_ATTACK&&id==412&&character==6)||
           (button==IN_C_ATTACK&&id==418&&(character==3||character==19)))damaging=1;
        if(!damaging)continue;
        *candidate_mask|=1u<<route;
        int airborne=(button==IN_SHOT?id>=404&&id!=408:id>=414&&id<=417);
        for(unsigned spacing=0;spacing<sizeof opponent_positions/sizeof opponent_positions[0];spacing++)
        for(unsigned airtime=0;airtime<(airborne?11u:1u);airtime++)
        for(unsigned timing=0;timing<(id==418?9u:1u);timing++){
            Fight probe;fight_init(&probe);
            /* probe_roster_natural_bc temporarily loads every candidate into
               player 0, while the original opponent remains on its saved
               roster slot. Approach the opponent using the actual facing
               direction, then place a neutral opponent at normal combat
               spacing so this diagnostic measures route/PAT behavior rather
               than a fixed-world-coordinate accident. */
            probe_bind_character_patterns(&probe,&patterns[0],(int)character,
                &patterns[1],(int)roster_index[1]);
            probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=opponent_positions[spacing];
            uint32_t forward=probe.p[0].face>0?IN_RIGHT:IN_LEFT;
            uint32_t backward=probe.p[0].face>0?IN_LEFT:IN_RIGHT;
            for(unsigned tick=0;tick<55;tick++)fight_step(&probe,forward);
            if(airborne){
                fight_step(&probe,IN_JUMP|forward);
                for(unsigned tick=0;tick<airtime;tick++)fight_step(&probe,forward);
                if(probe.p[0].y<=0)continue;
            }
            if(id==408||id==418){
                fight_step(&probe,0);fight_step(&probe,forward);fight_step(&probe,0);
                fight_step(&probe,forward);
                if(probe.p[0].action!=200||!probe.p[0].dash_ticks)continue;
            }
            /* Remilia 2C (412) emits the returning object 801. The original
               x86 probe only contacts at close spacing; place this diagnostic
               opponent 20 arena units away instead of measuring it at 80. */
            if(character==6&&id==412)probe.p[1].x=probe.p[0].x+20;
            /* Try several natural dash travel frames before 66C. This varies
               the defender's idle pose against Udonge/Suika/Utsuho's three
               active PAT frames without changing the hit resolver. */
            for(unsigned tick=0;tick<timing;tick++)fight_step(&probe,0);
            uint32_t route_input=inputs[route];
            if(forward==IN_LEFT){
                if(route_input&IN_RIGHT)route_input=(route_input&~IN_RIGHT)|IN_LEFT;
                else if(route_input&IN_LEFT)route_input=(route_input&~IN_LEFT)|IN_RIGHT;
            }
            unsigned command_hp=(unsigned)probe.p[1].hp;
            fight_step(&probe,route_input);
            if(probe.p[0].action!=id)continue;
            *reached_mask|=1u<<route;
            if(button==IN_SHOT&&id==408)roster_b_408_variant[character]=(int)probe.p[0].action_index;
            if(button==IN_SHOT&&id==409)roster_b_409_variant[character]=(int)probe.p[0].action_index;
            if(button==IN_C_ATTACK&&id==418)roster_c_418_variant[character]=(int)probe.p[0].action_index;
            int command_contact=probe_record_bc_contact(&probe,id,button,command_hp,0,
                hit_frame,hit_damage,hit_source,hit_pose,hit_gap);
            if(command_contact)return command_contact;
            for(unsigned tick=0;tick<180;tick++){
                unsigned before=probe.p[1].hp;fight_step(&probe,0);
                if(button==IN_C_ATTACK&&id==418&&probe.p[0].action==418){
                    const T123Pose *attacker=fight_pose(&probe,0),*defender=fight_pose(&probe,1);
                    if(attacker&&attacker->damage&&attacker->attack_count){
                        int gap=abs(probe.p[1].x-probe.p[0].x);
                        if(gap<roster_c_418_min_active_gap[character]){roster_c_418_min_active_gap[character]=gap;roster_c_418_min_signed_gap[character]=probe.p[1].x-probe.p[0].x;}
                        if(defender)for(unsigned a=0;a<attacker->attack_count;a++)
                        for(unsigned b=0;b<defender->hurt_count;b++){
                            const T123Box *ab=&attacker->attack[a],*hb=&defender->hurt[b];
                            int at=-probe.p[0].y+ab->up,ad=-probe.p[0].y+ab->down;
                            int ht=-probe.p[1].y+hb->up,hd=-probe.p[1].y+hb->down;
                            int vertical_overlap=at<hd&&ht<ad;
                            int vertical_gap=at>=hd?at-hd:ht>=ad?ht-ad:0;
                            if(vertical_overlap)roster_c_418_vertical_overlap_seen[character]=1;
                            if(vertical_gap<roster_c_418_min_vertical_gap[character])roster_c_418_min_vertical_gap[character]=vertical_gap;
                            int al=probe.p[0].x+(probe.p[0].face>0?ab->left:-ab->right);
                            int ar=probe.p[0].x+(probe.p[0].face>0?ab->right:-ab->left);
                            int bl=probe.p[1].x+(probe.p[1].face>0?hb->left:-hb->right);
                            int br=probe.p[1].x+(probe.p[1].face>0?hb->right:-hb->left);
                            int horizontal_overlap=al<br&&bl<ar;
                            int horizontal_gap=al>=br?al-br:bl>=ar?bl-ar:0;
                            if(horizontal_overlap)roster_c_418_horizontal_overlap_seen[character]=1;
                            if(vertical_overlap&&horizontal_gap<roster_c_418_min_horizontal_gap[character])
                                roster_c_418_min_horizontal_gap[character]=horizontal_gap;
                            if(horizontal_overlap&&vertical_overlap&&!probe.p[0].hit_done)
                                roster_c_418_overlap_seen[character]=1;
                        }
                    }
                }
                int contact=probe_record_bc_contact(&probe,id,button,before,tick+1,
                    hit_frame,hit_damage,hit_source,hit_pose,hit_gap);
                if(contact)return contact;
            }
        }
    }
    return 0;
}
static void probe_roster_natural_bc(unsigned *bmask,unsigned *cmask){
    unsigned saved0=roster_index[0],saved1=roster_index[1];*bmask=*cmask=0;
    for(unsigned character=0;character<ROSTER_COUNT;character++)if(load_character(0,character)==0){
        roster_b_408_variant[character]=roster_b_409_variant[character]=roster_c_418_variant[character]=-1;
        if(character==10u){
            unsigned candidates=0,frame=0,damage=0,pose=0;int source=0,gap=0;
            int action=probe_character_natural_bc(character,IN_SHOT,409,&candidates,
                &frame,&damage,&source,&pose,&gap);
            udonge_409_contract_seen=action==409&&roster_b_409_variant[character]==1&&
                frame==0&&damage==400&&source==409;
        }
        roster_b_natural_action[character]=probe_character_natural_bc(character,IN_SHOT,0,&roster_b_natural_candidates[character],&roster_b_hit_frame[character],&roster_b_hit_damage[character],&roster_b_hit_source[character],&roster_b_hit_pose[character],&roster_b_hit_gap[character]);
        roster_c_natural_action[character]=probe_character_natural_bc(character,IN_C_ATTACK,0,&roster_c_natural_candidates[character],&roster_c_hit_frame[character],&roster_c_hit_damage[character],&roster_c_hit_source[character],&roster_c_hit_pose[character],&roster_c_hit_gap[character]);
        if(roster_b_natural_action[character])*bmask|=1u<<character;
        if(roster_c_natural_action[character])*cmask|=1u<<character;
    }
    load_character(0,saved0);load_character(1,saved1);
}
static int probe_reimu_505_routes(void){
    static const int counts[3]={3,4,5};
    static const int vx[3][5]={{10,0,-10,0,0},{15,5,-5,-15,0},{20,10,0,-10,-20}};
    static const int vy[3][5]={{22,24,22,0,0},{24,26,26,24,0},{25,26,28,26,25}};
    int mask=0;
    for(int route=0;route<3;route++){
        Fight probe;fight_init(&probe);probe_bind_character_patterns(&probe,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
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
    Fight probe;fight_init(&probe);probe_bind_patterns(&probe,attacker,defender);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=450;
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
        Fight probe;fight_init(&probe);probe_bind_patterns(&probe,attacker,defender);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=220;
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
            Fight probe;fight_init(&probe);probe_bind_patterns(&probe,&patterns[0],&patterns[1]);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[1].x=220;
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
    Fight probe;fight_init(&probe);probe_bind_patterns(&probe,&patterns[0],&patterns[1]);probe.ai=0;
    probe.scene=SCENE_FIGHT;fight_step(&probe,IN_LEFT|IN_DOWN|IN_MELEE);
    if(t123_input_history_get(&probe.input_history[0],89)!=0x19)return 5;
    fight_step(&probe,IN_RIGHT|IN_JUMP|IN_SHOT|IN_C_ATTACK|IN_GUARD|IN_CHANGE_CARD|IN_SPELLCARD);
    if(t123_input_history_get(&probe.input_history[0],89)!=0x3e6)return 6;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT|IN_SHOT);
    if(probe.p[0].action==408||probe.p[0].dashes)return 10;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT|IN_C_ATTACK);
    if(probe.p[0].action==418||probe.p[0].dashes)return 20;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 30;
    fight_step(&probe,IN_RIGHT|IN_SHOT);
    if(probe.p[0].action!=408||probe.p[0].action_index!=1)return 40;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;
    fight_step(&probe,IN_RIGHT);fight_step(&probe,0);fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 50;
    fight_step(&probe,IN_RIGHT|IN_C_ATTACK);
    if(probe.p[0].action!=418||probe.p[0].action_index!=0)return 60;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT);
    for(int i=0;i<12;i++)fight_step(&probe,0);
    fight_step(&probe,IN_RIGHT);
    if(probe.p[0].action!=200||probe.p[0].dashes!=1)return 70;
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[1].x=220;fight_step(&probe,IN_RIGHT);
    for(int i=0;i<13;i++)fight_step(&probe,0);
    fight_step(&probe,IN_RIGHT);
    if(probe.p[0].dashes!=0||probe.p[0].action==200)return 80;
    /* Mirror the motion while the player faces left; forward is relative to
       the opponent rather than a hard-coded screen direction. */
    probe_reset(&probe);probe.scene=SCENE_FIGHT;probe.p[0].x=400;probe.p[1].x=220;
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
    unsigned saved0=roster_index[0],saved1=roster_index[1];object_route_probe=object_attack_routes=object_anchor_probe=0;suwako_418_burst_spawns=0;remilia_object_linger_seen=remilia_trail_lifecycle_seen=0;object_sprite_seen=0;object_route_error=remilia_spacing_pair=0;remilia_spacing_dx=remilia_spacing_dy=0;for(unsigned i=0;i<5;i++)remilia_spacing_samples[i][0]=remilia_spacing_samples[i][1]=0;int error=0;
    for(unsigned i=0;i<sizeof cases/sizeof cases[0];i++){
        const unsigned c=cases[i].character;
        if(load_character(0,c)||load_character(1,c)){error=(int)(300+i);break;}
        const T123Move *player=t123_pattern_move(&patterns[0],cases[i].action,(unsigned)cases[i].variant);
        if(!player){error=(int)(310+i);break;}
        Fight probe;fight_init(&probe);probe_bind_character_patterns(&probe,&patterns[0],(int)c,&patterns[1],(int)c);probe.ai=0;probe.scene=SCENE_FIGHT;
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
    if(!error){
        if(load_character(0,6)||load_character(1,6))error=390;
        else {
            Fight probe;fight_init(&probe);probe_bind_character_patterns(&probe,&patterns[0],6,&patterns[1],6);probe.ai=0;probe.scene=SCENE_FIGHT;probe.p[0].x=200;probe.p[1].x=230;
            fight_step(&probe,IN_DOWN|IN_C_ATTACK);
            for(int tick=1;tick<16;tick++)fight_step(&probe,0);
            if(probe.object_spawns!=2||!probe.objects[0].active||
               !probe.objects[1].active||probe.objects[1].action!=801||
               probe.objects[1].sequence!=1||probe.objects[1].age!=1)error=391;
            else {
                fight_step(&probe,0);
                int hp_after_hit=probe.p[1].hp;
                if(hp_after_hit!=probe.max_hp-120||!probe.objects[0].active||!probe.objects[0].hit_done)error=392;
                else {
                    fight_step(&probe,0);
                    if(probe.p[1].hp!=hp_after_hit||!probe.objects[0].active||probe.objects[0].animation.pose!=2)error=393;
                    else {
                        remilia_object_linger_seen=1;
                        for(int tick=3;tick<73;tick++)fight_step(&probe,0);
                        if(probe.object_spawns!=26||probe.objects[0].active)error=394;
                        else {
                            unsigned ages[6]={0},trails=0,age_mask=0;
                            float trail_x[6]={0},trail_y[6]={0};
                            for(unsigned j=0;j<sizeof probe.objects/sizeof probe.objects[0];j++){
                                const T123Object *o=&probe.objects[j];
                                if(!o->active||o->action!=801||o->sequence!=1)continue;
                                if(o->owner_action!=412||o->life<=0||o->age>=32){error=395;break;}
                                if(trails<6){ages[trails]=(unsigned)o->age;trail_x[trails]=o->world_x;trail_y[trails]=o->world_y;}
                                ++trails;
                            }
                            for(unsigned j=0;j<trails;j++)age_mask|=1u<<ages[j];
                            const unsigned expected_ages=(1u<<1)|(1u<<4)|(1u<<7)|(1u<<10)|(1u<<13)|(1u<<16);
                            if(!error&& (trails!=6||age_mask!=expected_ages))error=396;
                            for(unsigned j=0;j<6&&!error;j++)for(unsigned k=j+1;k<6;k++)if(ages[k]>ages[j]){
                                unsigned age=ages[j];ages[j]=ages[k];ages[k]=age;
                                float x=trail_x[j];trail_x[j]=trail_x[k];trail_x[k]=x;
                                float y=trail_y[j];trail_y[j]=trail_y[k];trail_y[k]=y;
                            }
                            for(unsigned j=1;j<6;j++){
                                float dx=trail_x[j]-trail_x[j-1],dy=trail_y[j]-trail_y[j-1];
                                /* Three full-world PE motion steps between trail emissions. */
                                remilia_spacing_samples[j-1][0]=dx;remilia_spacing_samples[j-1][1]=dy;
                                if((dx>-33.827f||dx<-33.830f||dy<12.311f||dy>12.315f)&&!error){remilia_spacing_pair=(int)j;remilia_spacing_dx=dx;remilia_spacing_dy=dy;error=397;}
                            }
                            if(!error)remilia_trail_lifecycle_seen=1;
                        }
                    }
                }
            }
        }
    }
    if(load_character(0,saved0)||load_character(1,saved1))return 399;
    object_route_error=error;
    if(error)return error;
    return object_route_probe==5&&object_attack_routes==4&&object_anchor_probe==2&&object_sprite_seen&&remilia_object_linger_seen&&remilia_trail_lifecycle_seen?0:400;
}
static void fighter(const Fight *g,int i){
    T123StageCamera camera=g->scene==SCENE_FIGHT?g->camera:
        (T123StageCamera){320.0f,0.0f,1.0f,320.0f,0.0f,1.0f};
    const Fighter *p=&g->p[i];const T123Pose *pose=fight_pose(g,i);
    float world_x=g->scene==SCENE_FIGHT?(float)p->x:(i?450.0f:190.0f);
    float world_y=g->scene==SCENE_FIGHT?-(float)p->y:0.0f;
    float screen_x,screen_y,floor_x,floor_y;
    if(!t123_stage_camera_project(&camera,world_x,world_y,
                                  0.0f,0.0f,&screen_x,&screen_y)||
       !t123_stage_camera_project(&camera,world_x,0.0f,
                                  0.0f,0.0f,&floor_x,&floor_y))return;
    float zoom=camera.zoom;int ground=(int)(screen_y-25.0f);
    unsigned c=i?RGBA8(110,190,255,255):RGBA8(245,105,145,255);
    soft2d_draw_fill_circle(sx(floor_x), (floor_y-22.0f)*scale,
                            21*scale*zoom,RGBA8(20,22,40,200));
    if(pose){
        soft2d_texture *t=pose_texture(i,pose->image);
        if(t){float x=screen_x-p->face*(float)pose->ox*zoom;soft2d_draw_texture_region_scale(t,pose->tx,pose->ty,(int)pose->tx+pose->tw,(int)pose->ty+pose->th,sx(x),(screen_y-(float)pose->oy*zoom)*scale,p->face*scale*zoom,scale*zoom);}
    }else if(sprites[i]){
        float size=1.5f*scale*zoom,w=soft2d_texture_get_width(sprites[i])*size,h=soft2d_texture_get_height(sprites[i])*size;
        soft2d_draw_texture_scale(sprites[i],sx(screen_x)+(p->face<0?w/2:-w/2),ground*scale-h,p->face*size,size);
    }else{
        rect(screen_x-18*zoom,ground-65*zoom,36*zoom,46*zoom,c);
        soft2d_draw_fill_circle(sx(screen_x),(ground-78*zoom)*scale,14*scale*zoom,c);
        rect(screen_x-15*zoom,ground-22*zoom,10*zoom,22*zoom,c);rect(screen_x+5*zoom,ground-22*zoom,10*zoom,22*zoom,c);
    }
    if(p->attack&&!pose)rect(screen_x+(p->face*22-(p->face<0?35:0))*zoom,ground-55*zoom,35*zoom,12*zoom,GOLD);
    if(p->guard)rect(screen_x+p->face*28*zoom,ground-94*zoom,5*zoom,94*zoom,RGBA8(100,255,230,200));
    if(p->stun)soft2d_draw_fill_circle(sx(screen_x),(ground-50*zoom)*scale,8*scale*zoom,GOLD);
}
static void draw_objects(const Fight *g){
    T123StageCamera camera=g->scene==SCENE_FIGHT?g->camera:
        (T123StageCamera){320.0f,0.0f,1.0f,320.0f,0.0f,1.0f};
    for(unsigned i=0;i<sizeof g->objects/sizeof g->objects[0];i++){
        const T123Object *o=&g->objects[i];if(!o->active||o->owner<0||o->owner>1)continue;
        const T123Move *m=t123_pattern_move(g->patterns[o->owner],o->action,(unsigned)o->sequence);
        if(!m||o->animation.pose>=m->sequence.count)continue;
        const T123Pose *pose=&m->poses[o->animation.pose];soft2d_texture *t=pose_texture(o->owner,pose->image);
        float object_x=(o->action==821||o->action==801)?o->world_x:(float)o->x;
        float object_y=(o->action==821||o->action==801)?o->world_y:(float)o->y;
        float screen_x,screen_y;if(!t123_stage_camera_project(&camera,object_x,-object_y,0.0f,0.0f,&screen_x,&screen_y))continue;
        float zoom=camera.zoom;
        if(t){const Fighter *owner=&g->p[o->owner];float x=screen_x-owner->face*(float)pose->ox*zoom;unsigned alpha=o->action==821?(unsigned)(o->alpha<0?0:o->alpha):255u;soft2d_draw_texture_region_scale_alpha(t,pose->tx,pose->ty,(int)pose->tx+pose->tw,(int)pose->ty+pose->th,sx(x),(screen_y-(float)pose->oy*zoom)*scale,owner->face*scale*zoom,scale*zoom,alpha);object_sprite_seen=1;}
        else{rect(screen_x-8*zoom,(screen_y-25.0f)-8*zoom,16*zoom,16*zoom,o->owner?RGBA8(90,200,255,255):RGBA8(255,110,170,255));}
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
        int extra_set=stage_extra_set();
        if(!strcmp(stage_names[stage_index],"bg34"))snprintf(line,sizeof line,"%s",stage_layer==3?"BG34 recovered placement map":stage_layer==2?"BG34 static assets + object sprites":stage_layer==1?"BG34 composite 0000 + 0001":"Layer 0000 tiles");
        else if(!strcmp(stage_names[stage_index],"bg02")&&stage_layer){
            static const char *segment_name[3]={"left","center","right"};float ox=0.0f,oy=0.0f;
            unsigned segment=stage_layer-1;
            if(t123_bg02_sprite_offset(segment,&ox,&oy)){
                if(segment==1)snprintf(line,sizeof line,"BG02 center segment | stage object origin (+44,+48)");
                else snprintf(line,sizeof line,"BG02 %s segment | local offset (%g,%g)",segment_name[segment],(double)ox,(double)oy);
            }else snprintf(line,sizeof line,"BG02 invalid segment");
        }
        else if(!strcmp(stage_names[stage_index],"bg12")&&stage_layer==2)snprintf(line,sizeof line,"BG12 tile anchors + torii base transforms");
        else if(!strcmp(stage_names[stage_index],"bg33")&&stage_layer==2)snprintf(line,sizeof line,"BG33 6x4 source layout + constructor sprite anchors");
        else if(!strcmp(stage_names[stage_index],"bg33")&&stage_layer==3)snprintf(line,sizeof line,"BG33 animated 30-slot local scroll view");
        else if(!strcmp(stage_names[stage_index],"bg36")&&stage_layer==2)snprintf(line,sizeof line,"BG36 grid + constructor anchor schematic");
        else if((!strcmp(stage_names[stage_index],"bg37")||!strcmp(stage_names[stage_index],"bg38"))&&stage_layer==2)snprintf(line,sizeof line,"%s cloud offsets from original update callback",stage_names[stage_index]);
        else snprintf(line,sizeof line,"%s",stage_layer&&extra_set>=0?"Base tiles + constructor-referenced assets":"Base tiles");
        text(30,66,line,WHITE);
        {unsigned loaded=stage_base_loaded();snprintf(line,sizeof line,"Base tiles loaded %u/%u",loaded,stage_base_expected());text(30,91,line,GOLD);}
        if(stage_layer&& !strcmp(stage_names[stage_index],"bg02")){
            static const char *segment_name[3]={"left/a","center/b","right/c"};
            unsigned segment=stage_layer-1,frame=t123_bg02_frame(stage_bg02_counter);
            unsigned page_loaded=0;for(unsigned i=0;i<16;i++)if(stage_bg02_page[i])++page_loaded;
            snprintf(line,sizeof line,"Constructor assets %u/16 | frame %02u/15, advances every 3 updates",page_loaded,frame);text(30,91,line,GOLD);
            for(unsigned i=0;i<16;i++){
                unsigned col=i%4,row=i/4;float x=34.0f+col*145.0f,y=122.0f+row*78.0f;
                rect(x,y,132,70,RGBA8(11,16,30,255));
                if(i==frame){rect(x,y,132,1.5f,GOLD);rect(x,y+68.5f,132,1.5f,GOLD);rect(x,y,1.5f,70,GOLD);rect(x+130.5f,y,1.5f,70,GOLD);}
                if(stage_bg02_page[i]){
                    soft2d_texture *asset=stage_bg02_page[i];float fitw=124.0f*scale/soft2d_texture_get_width(asset),fith=58.0f*scale/soft2d_texture_get_height(asset),fit=fitw<fith?fitw:fith;
                    soft2d_draw_texture_scale(asset,sx(x+4),y+3,fit,fit);
                }
                snprintf(line,sizeof line,"%s%02u",segment_name[segment],i);text((int)x+4,(int)y+57,line,WHITE);
            }
        }
        else if(stage_layer==2&&!strcmp(stage_names[stage_index],"bg33")){
            stage_bg33_layout_seen=1;stage_bg33_tiles_loaded=(int)stage_base_loaded();rect(92,86,358,287,RGBA8(11,16,30,255));
            const float tile_scale=0.16f;
            for(unsigned row=0;row<4;row++)for(unsigned col=0;col<6;col++){
                soft2d_texture *tile=stage_tiles[row][col];if(!tile)continue;
                float wx=700.0f-256.0f*col,wy=860.0f-256.0f*row;
                float px=118.0f+(wx-60.0f)*tile_scale,py=102.0f+(860.0f-wy)*tile_scale;
                float fitw=256.0f*tile_scale*scale/soft2d_texture_get_width(tile);
                float fith=256.0f*tile_scale*scale/soft2d_texture_get_height(tile),fit=fitw<fith?fitw:fith;
                soft2d_draw_texture_scale(tile,sx(px),py*scale,fit,fit);
            }
            const float anchor_x[2]={700.0f,350.0f},anchor_y[2]={228.0f,152.0f};
            for(unsigned i=0;i<2;i++)if(stage_extras[i]){
                soft2d_texture *asset=stage_extras[i];float fitw=132.0f*scale/soft2d_texture_get_width(asset);
                float fith=86.0f*scale/soft2d_texture_get_height(asset),fit=fitw<fith?fitw:fith;
                float draw_w=soft2d_texture_get_width(asset)*fit,draw_h=soft2d_texture_get_height(asset)*fit;
                float px=118.0f+(anchor_x[i]-60.0f)*tile_scale;
                float py=102.0f+(860.0f-anchor_y[i])*tile_scale;
                soft2d_draw_texture_scale(asset,sx(px-draw_w*0.5f),py*scale-draw_h,fit,fit);
                rect(px-4.0f,py-1.0f,9.0f,1.0f,RGBA8(255,212,70,255));
                rect(px-1.0f,py-4.0f,1.0f,9.0f,RGBA8(255,212,70,255));
                snprintf(line,sizeof line,"000%u pivot (%g,%g)",i+1,(double)anchor_x[i],(double)anchor_y[i]);
                text(462,(int)(99+i*22),line,GOLD);
            }
            text(462,151,"Grid: 6 x 4 tiles",WHITE);
            snprintf(line,sizeof line,"update +0x64: %u/1023",stage_bg33_counter);text(462,171,line,GOLD);
            snprintf(line,sizeof line,"render phase: %u/3",stage_bg33_counter>>8);text(462,191,line,WHITE);
            text(30,412,"BG33 local tile-scroll cycle; world-camera projection still pending",GOLD);
        }
        else if(stage_layer==3&&!strcmp(stage_names[stage_index],"bg33")){
            stage_bg33_scroll_seen=1;stage_bg33_tiles_loaded=(int)stage_base_loaded();rect(92,86,358,287,RGBA8(11,16,30,255));
            const float map_scale=0.16f;
            for(unsigned slot=0;slot<30;slot++){
                T123Bg33RenderSlot draw;
                if(!t123_bg33_render_slot(stage_bg33_counter,slot,&draw))continue;
                unsigned row=draw.sprite_index/6u,col=draw.sprite_index%6u;
                soft2d_texture *tile=stage_tiles[row][col];if(!tile)continue;
                T123StageQuad quad;
                /* Camera-zero reference viewport: run the PE-equivalent quad
                   transform, then fit its logical coordinates into this map. */
                if(!t123_bg33_project_slot_quad(&draw,0,0,1,0,0,0,0,1,1,&quad))continue;
                float qx[4],qy[4];
                for(unsigned corner=0;corner<4;corner++){
                    qx[corner]=sx(118.0f+(quad.x[corner]-260.0f)*map_scale);
                    qy[corner]=(102.0f+(quad.y[corner]+440.0f)*map_scale)*scale;
                }
                if(soft2d_draw_texture_quad(tile,qx,qy)){stage_bg33_slot_mask|=1u<<slot;stage_bg33_quad_draws++;}
            }
            snprintf(line,sizeof line,"BG33 renderer slots 30/30 | source phase %u/3",stage_bg33_counter>>8);text(462,115,line,GOLD);
            snprintf(line,sizeof line,"counter %u/1023 | sources %u/24",stage_bg33_counter,(unsigned)stage_base_loaded());text(462,139,line,WHITE);
            text(462,171,"local 256-unit tiles",WHITE);
            text(30,412,"BG33 source matrix + exact local wrap; viewport/camera remains external",GOLD);
        }
        else if(stage_layer==2&&!strcmp(stage_names[stage_index],"bg12")){
            stage_bg12_layout_seen=1;rect(112,83,310,287,RGBA8(11,16,30,255));
            const float map_scale=0.17f;
            for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col]){
                soft2d_texture *tile=stage_tiles[row][col];
                float wx=700.0f-256.0f*col,wy=946.0f-256.0f*row;
                float px=125.0f+(wx+580.0f)*map_scale;
                float py=99.0f+(946.0f-wy)*map_scale;
                float fitw=256.0f*map_scale*scale/soft2d_texture_get_width(tile);
                float fith=256.0f*map_scale*scale/soft2d_texture_get_height(tile);
                float fit=fitw<fith?fitw:fith;
                soft2d_draw_texture_scale(tile,sx(px),py*scale,fit,fit);
            }
            float torii_tx=0.0f,torii_ty=0.0f;t123_bg12_torii_base_translation(&torii_tx,&torii_ty);
            float torii_map_x=125.0f+(torii_tx+580.0f)*map_scale;
            float torii_map_y=99.0f+(946.0f-torii_ty)*map_scale;
            rect(torii_map_x-5.0f,torii_map_y-0.5f,11.0f,1.0f,RGBA8(255,212,70,255));
            rect(torii_map_x-0.5f,torii_map_y-5.0f,1.0f,11.0f,RGBA8(255,212,70,255));
            uint32_t first_phase=0,second_phase=0;t123_bg12_render_time_args(stage_bg12_counter,&first_phase,&second_phase);
            for(unsigned i=0;i<2;i++)if(stage_extras[i]){
                soft2d_texture *asset=stage_extras[i];float fitw=116.0f*scale/soft2d_texture_get_width(asset),fith=66.0f*scale/soft2d_texture_get_height(asset),fit=fitw<fith?fitw:fith;
                float anchor_x=496.0f,anchor_y=(i?276.0f:164.0f)*scale;
                float draw_w=soft2d_texture_get_width(asset)*fit,draw_h=soft2d_texture_get_height(asset)*fit;
                soft2d_draw_texture_scale(asset,sx(anchor_x-draw_w*0.5f),anchor_y-draw_h,fit,fit);
                rect(anchor_x-5.0f,anchor_y-0.5f,11.0f,1.0f,RGBA8(255,212,70,255));
                rect(anchor_x-0.5f,anchor_y-5.0f,1.0f,11.0f,RGBA8(255,212,70,255));
                snprintf(line,sizeof line,"tori%u bottom-center pivot",i+1);text(405,(int)(anchor_y/scale+23.0f),line,GOLD);
            }
            text(425,311,"Base tile anchors:",WHITE);text(425,330,"x=700-256*col",WHITE);text(425,349,"Torii base (492,-401)",GOLD);
            snprintf(line,sizeof line,"counter +0x64 = %u",stage_bg12_counter);text(30,400,line,GOLD);
            snprintf(line,sizeof line,"render args: %u, %u",first_phase,second_phase);text(30,421,line,WHITE);
            text(30,442,"local quad: x[-w/2,+w/2], y[-h,0]",WHITE);
            text(30,463,"Then stage offsets +0x44/+0x48; camera pending",GOLD);
        }
        else if(stage_layer==3&&!strcmp(stage_names[stage_index],"bg34")){
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
        else if(stage_layer==2&&!strcmp(stage_names[stage_index],"bg36")){
            stage_bg36_layout_seen=1;stage_bg36_scroll_seen=1;
            /* FUN_0046fe40 places the grid at x=700-256*col and
               y=0x56+0x35c-256*row. Keep the grid independent of the
               combat camera, which has not yet been recovered. */
            rect(142,78,382,314,RGBA8(11,16,30,255));
            const float map_scale=0.22f;
            for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col]){
                soft2d_texture *tile=stage_tiles[row][col];
                float wx=700.0f-256.0f*col,wy=946.0f-256.0f*row;
                float px=166.0f+(wx+580.0f)*map_scale;
                float py=91.0f+(946.0f-wy)*map_scale;
                float fitw=256.0f*map_scale*scale/soft2d_texture_get_width(tile);
                float fith=256.0f*map_scale*scale/soft2d_texture_get_height(tile);
                float fit=fitw<fith?fitw:fith;
                soft2d_draw_texture_scale(tile,sx(px),py*scale,fit,fit);
            }
            /* Match each auxiliary's callsite into FUN_00429440 with a
               zero-camera reference. Stage-space extents are fitted together
               so the panel preserves their relative position and size. */
            rect(407,176,155,160,RGBA8(11,16,30,255));
            const float anchor_x[4]={0.0f,0.0f,stage_bg36_scroll.clowd_l_x,stage_bg36_scroll.clowd_s_x};
            const float anchor_y[4]={0.0f,0.0f,-750.0f,-320.0f};
            T123StageQuad aux_quad[4];float world_x[4][4],world_y[4][4];
            int projected[4]={0,0,0,0},have_bounds=0;float min_x=0.0f,max_x=0.0f,min_y=0.0f,max_y=0.0f;
            for(unsigned i=0;i<4;i++)if(stage_extras[i]){
                soft2d_texture *asset=stage_extras[i];
                projected[i]=t123_bg36_project_aux_quad(i,
                    (float)soft2d_texture_get_width(asset),(float)soft2d_texture_get_height(asset),
                    anchor_x[i],anchor_y[i],1.0f,0.0f,0.0f,0.0f,0.0f,1.0f,1.0f,&aux_quad[i]);
                if(!projected[i])continue;
                for(unsigned corner=0;corner<4;corner++){
                    world_x[i][corner]=aux_quad[i].x[corner]-960.0f;
                    world_y[i][corner]=aux_quad[i].y[corner]-420.0f;
                    if(!have_bounds){min_x=max_x=world_x[i][corner];min_y=max_y=world_y[i][corner];have_bounds=1;}
                    else{
                        if(world_x[i][corner]<min_x)min_x=world_x[i][corner];
                        if(world_x[i][corner]>max_x)max_x=world_x[i][corner];
                        if(world_y[i][corner]<min_y)min_y=world_y[i][corner];
                        if(world_y[i][corner]>max_y)max_y=world_y[i][corner];
                    }
                }
            }
            float extent_x=max_x-min_x,extent_y=max_y-min_y;
            float fit_x=extent_x>0.0f?139.0f/extent_x:1.0f;
            float fit_y=extent_y>0.0f?140.0f/extent_y:1.0f;
            float diagnostic_fit=fit_x<fit_y?fit_x:fit_y;
            for(unsigned i=0;i<4;i++)if(projected[i]){
                float qx[4],qy[4];
                for(unsigned corner=0;corner<4;corner++){
                    qx[corner]=sx(415.0f+(world_x[i][corner]-min_x)*diagnostic_fit);
                    qy[corner]=(184.0f+(world_y[i][corner]-min_y)*diagnostic_fit)*scale;
                }
                soft2d_draw_texture_quad(stage_extras[i],qx,qy);
                if(i>=2)stage_bg36_cloud_quads_projected++;
            }
            rect(407,176,155,1,RGBA8(145,160,185,255));
            rect(407,335,155,1,RGBA8(145,160,185,255));
            rect(407,176,1,160,RGBA8(145,160,185,255));
            rect(561,176,1,160,RGBA8(145,160,185,255));
            snprintf(line,sizeof line,"BG36 updates %u",stage_bg36_scroll_ticks);text(407,158,line,GOLD);
            text(407,339,"Aux 0/1 torii  |  2/3 clouds",WHITE);
            text(148,409,"BG36 PE transforms, zero-camera fit; live camera pending",GOLD);
        }
        else if(stage_layer==2&&(!strcmp(stage_names[stage_index],"bg37")||!strcmp(stage_names[stage_index],"bg38"))){
            int is_bg37=!strcmp(stage_names[stage_index],"bg37");
            float first_x=is_bg37?stage_bg37_scroll.tori1_x:stage_bg38_scroll.clowd_l_x;
            float second_x=is_bg37?stage_bg37_scroll.clowd_l_x:stage_bg38_scroll.clowd_s_x;
            unsigned updates=is_bg37?stage_bg37_scroll_ticks:stage_bg38_scroll_ticks;
            rect(142,78,382,314,RGBA8(11,16,30,255));
            snprintf(line,sizeof line,"%s renderer sprite-slot transforms",stage_names[stage_index]);text(168,99,line,GOLD);
            unsigned rows=is_bg37?3u:2u;
            for(unsigned i=0;i<rows;i++){
                float x=i==0?first_x:(i==1?second_x:492.0f);
                float y=i==0?-750.0f:(i==1?-320.0f:-401.0f);
                rect(183,146+(int)i*82,290,1,RGBA8(73,83,103,255));
                unsigned asset_index=i;
                if(stage_extras[asset_index]){
                    soft2d_texture *asset=stage_extras[asset_index];
                    float maxw=142.0f*scale,maxh=42.0f*scale;
                    float fitw=maxw/soft2d_texture_get_width(asset),fith=maxh/soft2d_texture_get_height(asset),fit=fitw<fith?fitw:fith;
                    float cx=378.0f+(x+400.0f)*0.08f;
                    soft2d_draw_texture_scale(asset,sx(cx)-soft2d_texture_get_width(asset)*fit*0.5f,151.0f*scale+(float)i*82.0f*scale,fit,fit);
                }
                const char *label=is_bg37?(i==0?"tori1":"clowd_l"):(i==0?"clowd_l":"clowd_s");
                if(is_bg37&&i==2)label="clowd_s";
                snprintf(line,sizeof line,"%s x=%.1f y=%.0f",label,(double)x,(double)y);text(183,126+(int)i*82,line,WHITE);
            }
            snprintf(line,sizeof line,"tick %u | rates -1.5/-1.0 | wraps -1200/-800 -> 800",updates);text(92,373,line,GOLD);
            text(96,393,"Local transforms mapped; camera/alpha composition pending",WHITE);
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
        }else if(stage_layer&&extra_set>=0){
            unsigned loaded=0;
            for(unsigned i=0;i<4;i++)if(stage_extras[i]){
                soft2d_texture *asset=stage_extras[i];float fitw=124.0f*scale/soft2d_texture_get_width(asset),fith=75.0f*scale/soft2d_texture_get_height(asset),fit=fitw<fith?fitw:fith;
                soft2d_draw_texture_scale(asset,sx(34.0f+i*148.0f),80.0f*scale,fit,fit);
                const char *name=strrchr(stage_extra_paths[extra_set][i],'/');text(34+(int)i*148,164,name?name+1:"asset",GOLD);++loaded;
            }
            for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col]){
                soft2d_texture *tile=stage_tiles[row][col];float fitw=42.0f*scale/soft2d_texture_get_width(tile),fith=36.0f*scale/soft2d_texture_get_height(tile),fit=fitw<fith?fitw:fith;
                float x=34.0f+(5-col)*96.0f,y=191.0f*scale+row*45.0f*scale;
                soft2d_draw_texture_scale(tile,sx(x),y,fit,fit);
            }
            snprintf(line,sizeof line,"Constructor assets %u/4; positions/animation not drawn",loaded);text(30,423,line,GOLD);
        }else for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col]){
            soft2d_texture *tile=stage_tiles[row][col];float fit=58.0f*scale/soft2d_texture_get_height(tile);
            soft2d_draw_texture_scale(tile,sx(20.0f+(5-col)*100.0f),82*scale+row*67.0f*scale,fit,fit);
        }
        unsigned stage_base_tiles=0;for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(stage_tiles[row][col])++stage_base_tiles;
        if(!stage_base_tiles)text(205,240,"No base tiles decoded from the local DATs",GOLD);
        text(30,439,"Left/Right: stage   Up/Down: stage view",GOLD);
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
            soft2d_draw_texture_scale(roster_cards[i],sx(i?450.0f:190.0f)-w*0.5f,145*scale,card_scale,card_scale);
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
            snprintf(line,sizeof line,"Setup  %s vs %s  |  %s  |  10000 HP",roster[roster_index[0]],roster[roster_index[1]],battle_stage_selection?"BG36":"BG33");text(30,438,line,GOLD);
            text(30,466,"Left/Right: P2    Up/Down: stage    X: fight    Circle: back",WHITE);
        }
    }else{
        /* BG10 is only a fallback. A loaded stage renderer supplies its own
         * scene background; drawing BG10 beneath it leaks an unrelated stage
         * through transparent tiles and breaks the original composition. */
        if(battle_bg36_ready){
            /* BG36's PE renderer paints the viewport sky before its tiles.
             * The default tint fields are zero, yielding RGB (126,206,244). */
            rect(0.0f,0.0f,640.0f,400.0f,RGBA8(126,206,244,255));
        }else if(!battle_bg33_ready){
            if(background)soft2d_draw_texture_scale(background,sx(0),0,640*scale/soft2d_texture_get_width(background),400*scale/soft2d_texture_get_height(background));
            else{rect(0,0,640,400,RGBA8(35,49,72,255));for(int i=0;i<12;i++)rect(i*60,200+(i%3)*20,28,180,RGBA8(24,39,58,255));}
        }
        float floor_left_x,floor_left_y,floor_right_x,floor_right_y;
        if(battle_bg36_ready)draw_battle_bg36(g);
        else draw_battle_bg33(g);
        if(!battle_bg33_ready&&!battle_bg36_ready&&t123_stage_camera_project(&g->camera,0.0f,0.0f,0.0f,0.0f,
                                     &floor_left_x,&floor_left_y)&&
           t123_stage_camera_project(&g->camera,640.0f,0.0f,0.0f,0.0f,
                                     &floor_right_x,&floor_right_y))
            rect(floor_left_x,floor_left_y-25.0f,floor_right_x-floor_left_x,
                 85.0f*g->camera.zoom,RGBA8(48,37,60,255));
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
    /* The PC canvas is 640x480, fitted uniformly to 544 rows. World-space
       sprites can extend beyond it; keep them out of the Vita side bars.
       Pixel centers 117..842 intersect the fitted [117.333,842.667) canvas. */
    soft2d_draw_rectangle(0,0,117,544,RGBA8(0,0,0,255));
    soft2d_draw_rectangle(843,0,117,544,RGBA8(0,0,0,255));
}
static int capture_object_render_probe(Fight *live){
    unsigned saved0=roster_index[0],saved1=roster_index[1];int previous_gallery=gallery_mode,previous_stage=stage_mode;
    if(load_character(0,3)||load_character(1,19))goto fail;
    Fight preview;fight_init(&preview);probe_bind_character_patterns(&preview,&patterns[0],3,&patterns[1],19);preview.scene=SCENE_FIGHT;preview.p[0].x=190;preview.p[1].x=430;
    const T123Move *move=t123_pattern_move(&patterns[0],849,21);if(!move||!move->sequence.count)goto fail;
    T123Object *o=&preview.objects[0];o->active=1;o->owner=0;o->action=849;o->sequence=21;o->x=280;o->y=30;o->life=30;o->age=1;
    if(t123_animation_set(&o->animation,&move->sequence,1,0))goto fail;
    gallery_mode=stage_mode=0;object_sprite_seen=0;soft2d_start_drawing();soft2d_clear_screen();draw(&preview,1);soft2d_end_drawing();
    if(soft2d_capture("ux0:data/touhou123vita-object-probe.bmp"))goto fail;
    object_render_capture=object_sprite_seen;
    gallery_mode=previous_gallery;stage_mode=previous_stage;
    if(load_character(0,saved0)||load_character(1,saved1))return 0;
    probe_bind_character_patterns(live,&patterns[0],(int)saved0,&patterns[1],(int)saved1);return object_render_capture;
fail:
    gallery_mode=previous_gallery;stage_mode=previous_stage;
    load_character(0,saved0);load_character(1,saved1);
    probe_bind_character_patterns(live,&patterns[0],(int)saved0,&patterns[1],(int)saved1);return 0;
}
int main(void){
    Fight g;fight_init(&g);sceCtrlSetSamplingMode(SCE_CTRL_MODE_ANALOG);
    if(soft2d_init()<0)return 1;
    font=soft2d_load_default_pgf();if(!font){soft2d_fini();return 2;}
    if(t123_resources_open(&resources,"ux0:data/touhou123vita")==0 && (resources.opened&0x1cu)==0x1cu &&
       load_character(0,0)==0 && load_character(1,16)==0){
        data_ready=1;fight_bind_character_patterns(&g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);arena_spawn_contract_seen=g.p[0].x==480&&g.p[1].x==800&&g.p[0].y==0&&g.p[1].y==0&&g.camera.x==640.0f&&g.camera.zoom==1.0f;
        background=soft2d_load_dat(&resources,"data/background/bg10/0000_10.cv2",NULL);
    }
    FILE *flag=fopen("app0:auto-test.txt","r");int automated=flag!=NULL;if(flag)fclose(flag);
    if(automated)sprite_region_crop_contract_seen=soft2d_texture_region_crop_contract();
    if(automated)stage_bg12_contract_seen=probe_bg12_animation_contract();
    if(automated){stage_bg02_transform_contract_seen=probe_bg02_transform_contract();stage_viewport_contract_seen=probe_stage_viewport_contract();stage_camera_pair_contract_seen=probe_stage_camera_pair_contract();stage_bg36_aux_projection_contract_seen=probe_bg36_aux_projection_contract();stage_bg33_quad_contract_seen=probe_bg33_quad_contract();}
    if(automated&&data_ready)stage_bg02_resource_count=probe_bg02_resources();
    int dash_gate_probe=automated&&data_ready?probe_dash_routes():0;
    int suika_623c_probe=automated&&data_ready?probe_suika_623c():0;
    int suika_623b_probe=automated&&data_ready?probe_suika_623b():0;
    if(automated)printf("Suika 623B probe=%d route_mask=%d damage=%d/%d level9=%d\n",suika_623b_probe,suika_623b_route_mask,suika_623b_hit_delta,suika_623b_level5_hit_delta,suika_623b_level9_action_seen);
    if(automated)printf("Suika 623C probe=%d action_seen=%d skill_uses=%d hit_delta=%d\n",suika_623c_probe,suika_623c_action_seen,suika_623c_skill_uses,suika_623c_hit_delta);
    if(automated&&data_ready)object_render_capture=capture_object_render_probe(&g);
    unsigned roster_a_attack_mask=automated&&data_ready?probe_roster_a_attacks():0;
    unsigned roster_a_natural_attack_mask=automated&&data_ready?probe_roster_a_natural_attacks():0;
    unsigned roster_b_natural_attack_mask=0,roster_c_natural_attack_mask=0;
    if(automated&&data_ready)probe_roster_natural_bc(&roster_b_natural_attack_mask,&roster_c_natural_attack_mask);
    int f=0,menu_seen=0,practice_seen=0,fight_seen=0,jump_seen=0,gallery_seen=0,stage_seen=0,skill_probe_inputs=0,skill_probe_success=0,skill_probe_sequence_ok=0,skill_probe_action=-1,skill_probe_image=-1,skill_probe_hit_delta=0,skill_probe_start_sequence=-1,skill_probe_hit_sequence=-1,skill_probe_startup_hit_delta=-1,skill_air_launch_ok=0,skill_landing_sequence=-1,skill_landing_ok=0,skill_x_delta=0,skill_reverse_motion_ok=0;
    Fight skill_probe_game,skill_102_probe_game,skill_107_probe_game,skill_104_probe_game;int skill_probe_ready=0,skill_102_probe_ready=0,skill_107_probe_ready=0,skill_104_probe_ready=0,skill_104_action=-1,skill_104_sequence_ok=0,skill_104_spawn_count=0,skill_104_object_action=-1,skill_104_sprite_seen=0,skill_104_hit_delta=0,skill_104_phase_mask=0,skill_102_action=-1,skill_102_image=-1,skill_102_sequence_ok=0,skill_102_hit_delta=0,skill_102_hit_sequence=-1,skill_102_hit_image=-1,skill_102_followup_ticks=0,skill_107_action=-1,skill_107_image=-1,skill_107_sequence_ok=0,skill_107_hit_delta=0,skill_107_hit_sequence=-1,skill_107_hit_image=-1,skill_107_followup_ticks=0;unsigned skill_hits_baseline=0;
    for(;;){
        SceCtrlData pad={0};sceCtrlPeekBufferPositive(0,&pad,1);uint32_t input=automated?scenario(f):controls(pad.buttons,g.scene==SCENE_FIGHT);
        if(!data_ready)input=0;
        int gallery_handled=data_ready?gallery_step(&g,input):0;
        int stage_handled=data_ready&&!gallery_handled?stage_step(&g,input):0;
        if(data_ready&&!gallery_handled&&!stage_handled&&!automated){uint32_t edge=input&~g.previous;if(g.scene==SCENE_MENU){if(edge&IN_LEFT)select_character(&g,0,-1);else if(edge&IN_RIGHT)select_character(&g,0,1);}else if(g.scene==SCENE_PRACTICE){if(edge&IN_LEFT)select_character(&g,1,-1);else if(edge&IN_RIGHT)select_character(&g,1,1);if(edge&(IN_JUMP|IN_DOWN))battle_stage_selection^=1u;}}
        if(data_ready&&!gallery_handled&&!stage_handled&&automated){uint32_t edge=input&~g.previous;if(g.scene==SCENE_MENU&&(edge&IN_RIGHT))select_character(&g,0,1);else if(g.scene==SCENE_PRACTICE){if(edge&IN_RIGHT)select_character(&g,1,1);if(edge&(IN_JUMP|IN_DOWN))battle_stage_selection^=1u;}}
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
        int scene_before_step=g.scene;
        if(!gallery_handled&&!stage_handled)fight_step(&g,input);else if(gallery_mode)gallery_seen=1;else if(stage_mode)stage_seen=1;
        if(automated&&scene_before_step==SCENE_PRACTICE&&g.scene==SCENE_FIGHT&&battle_stage_selection==1u)battle_stage_selected_interactively=1u;
        if(automated&&g.scene==SCENE_FIGHT&&f==300){battle_bg36_ready=0;prepare_battle_bg36();}
        if(automated&&g.scene==SCENE_FIGHT&&f==301){battle_stage_selection=0u;battle_bg36_ready=0;}
        if(g.scene==SCENE_FIGHT){
            if(!battle_bg33_ready&&!battle_bg36_ready){
                if((automated&&f==300)||( !automated&&battle_stage_selection))prepare_battle_bg36();
                else prepare_battle_bg33();
            }
            if(battle_bg36_ready){t123_bg36_scroll_update(&battle_bg36_scroll);battle_bg36_updates++;}
            else if(battle_bg33_ready){t123_stage_animation_update(33u,&battle_bg33_counter);battle_bg33_updates++;}
        }else{battle_bg33_ready=0;battle_bg36_ready=0;}
        if(automated&&f==180&&g.scene==SCENE_FIGHT&&load_character(0,0)==0){
            probe_bind_character_patterns(&g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            fight_init(&skill_probe_game);probe_bind_character_patterns(&skill_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_probe_game.ai=0;skill_probe_game.scene=SCENE_FIGHT;
            const T123Move *skill=t123_pattern_move(&patterns[0],560,1);
            skill_probe_ready=skill&&probe_place_for_attack(&skill_probe_game,skill,&patterns[1])>=0;
            skill_hits_baseline=skill_probe_game.p[0].hits;
            fight_init(&skill_102_probe_game);probe_bind_character_patterns(&skill_102_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_102_probe_game.ai=0;skill_102_probe_game.scene=SCENE_FIGHT;skill_102_probe_game.p[0].skill_card_id=102;
            const T123Move *card102_attack=probe_selected_attack(&patterns[0],540);
            skill_102_probe_ready=card102_attack&&t123_pattern_variant_count(&patterns[0],540)>0&&t123_pattern_variant_count(&patterns[0],540)<=T123_ACTION_SEQUENCE_LIMIT&&probe_place_for_attack(&skill_102_probe_game,card102_attack,&patterns[1])>=0;
            fight_init(&skill_107_probe_game);probe_bind_character_patterns(&skill_107_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
            skill_107_probe_game.ai=0;skill_107_probe_game.scene=SCENE_FIGHT;skill_107_probe_game.p[0].skill_card_id=107;
            const T123Move *card107_attack=t123_pattern_move(&patterns[0],565,1);
            skill_107_probe_ready=card107_attack&&t123_pattern_variant_count(&patterns[0],565)>0&&t123_pattern_variant_count(&patterns[0],565)<=T123_ACTION_SEQUENCE_LIMIT&&probe_place_for_attack(&skill_107_probe_game,card107_attack,&patterns[1])>=0;
            fight_init(&skill_104_probe_game);probe_bind_character_patterns(&skill_104_probe_game,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
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
            probe_bind_character_patterns(&reverse_skill,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
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
            if(load_character(0,1)==0)probe_bind_character_patterns(&g,&patterns[0],(int)roster_index[0],&patterns[1],(int)roster_index[1]);
        }
        if(g.scene==SCENE_MENU)menu_seen=1;
        if(g.scene==SCENE_PRACTICE)practice_seen=1;
        if(g.scene==SCENE_FIGHT)fight_seen=1;
        if(g.p[0].y>0)jump_seen=1;
        soft2d_start_drawing();soft2d_clear_screen();draw(&g,automated);if(automated&&g.scene==SCENE_FIGHT&&f==300&&battle_bg36_ready&&soft2d_capture("ux0:data/touhou123vita-fight-bg36.bmp")==0){battle_bg36_capture_seen=1;battle_bg36_capture_camera_x=g.camera.x;battle_bg36_capture_camera_y=g.camera.y;battle_bg36_capture_camera_zoom=g.camera.zoom;}soft2d_end_drawing();
        if(automated && f==83)soft2d_capture("ux0:data/touhou123vita-menu.bmp");
        if(automated && gallery_mode && f==85)soft2d_capture("ux0:data/touhou123vita-gallery.bmp");
        if(automated && stage_mode && f==134)soft2d_capture("ux0:data/touhou123vita-stage.bmp");
        if(automated && stage_mode && f==163)soft2d_capture("ux0:data/touhou123vita-stage-assets.bmp");
        if(automated && stage_mode && f==165)soft2d_capture("ux0:data/touhou123vita-stage-layout.bmp");
        if(automated && stage_mode && f==110)soft2d_capture("ux0:data/touhou123vita-stage-bg12-assets.bmp");
        if(automated && stage_mode && stage_index==9 && stage_layer==2 && !stage_bg12_layout_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg12-layout.bmp")==0)stage_bg12_layout_captured=1;
        if(automated && stage_mode && !strcmp(stage_names[stage_index],"bg02") && stage_layer==1 && !stage_bg02_page_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg02-segment.bmp")==0)stage_bg02_page_captured=1;
        if(automated && stage_mode && !strcmp(stage_names[stage_index],"bg36") && stage_layer==2 && !stage_bg36_layout_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg36-layout.bmp")==0)stage_bg36_layout_captured=1;
        if(automated && stage_mode && !strcmp(stage_names[stage_index],"bg37") && stage_layer==2 && !stage_bg37_scroll_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg37-scroll.bmp")==0)stage_bg37_scroll_captured=1;
        if(automated && stage_mode && !strcmp(stage_names[stage_index],"bg38") && stage_layer==2 && !stage_bg38_scroll_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg38-scroll.bmp")==0)stage_bg38_scroll_captured=1;
        if(automated && stage_mode && f==132)soft2d_capture("ux0:data/touhou123vita-stage-bg33-assets.bmp");
        if(automated && stage_mode && !strcmp(stage_names[stage_index],"bg33") && stage_layer==2 && !stage_bg33_layout_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg33-layout.bmp")==0)stage_bg33_layout_captured=1;
        if(automated && stage_mode && !strcmp(stage_names[stage_index],"bg33") && stage_layer==3 && !stage_bg33_scroll_captured && soft2d_capture("ux0:data/touhou123vita-stage-bg33-scroll.bmp")==0)stage_bg33_scroll_captured=1;
        if(automated && stage_mode && stage_layer==1 && !strcmp(stage_names[stage_index],"bg36"))soft2d_capture("ux0:data/touhou123vita-stage-bg36-assets.bmp");
        if(automated && stage_mode && stage_layer==1 && !strcmp(stage_names[stage_index],"bg37"))soft2d_capture("ux0:data/touhou123vita-stage-bg37-assets.bmp");
        if(automated && stage_mode && stage_layer==1 && !strcmp(stage_names[stage_index],"bg38"))soft2d_capture("ux0:data/touhou123vita-stage-bg38-assets.bmp");
        if(automated && f==130)soft2d_capture("ux0:data/touhou123vita-practice.bmp");
        if(automated && f==300)soft2d_capture("ux0:data/touhou123vita-fight.bmp");

        if(automated && f==532)soft2d_capture("ux0:data/touhou123vita-fight-natural-a.bmp");
        soft2d_swap_buffers();sceDisplayWaitVblankStart();
        if(automated && ++f==600){
            int stage_tiles_loaded=0,stage_alt_tiles_loaded=0;for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){if(stage_tiles[row][col])stage_tiles_loaded++;if(stage_alt_tiles[row][col])stage_alt_tiles_loaded++;}
            int stage_static_loaded=0,stage_objects_loaded=0;for(unsigned i=0;i<4;i++)if(stage_extras[i])stage_static_loaded++;for(unsigned i=0;i<30;i++)if(stage_objects[i])stage_objects_loaded++;
            int pat_effect_fixture=probe_pattern_effect_payload();
            int pass=udonge_409_contract_seen&&arena_spawn_contract_seen&&data_ready&&(resources.opened==31u)&&sprite_region_crop_contract_seen&&menu_seen&&gallery_seen&&gallery_texture_seen&&gallery_character_seen&&gallery_action_seen&&gallery_pose_seen&&stage_seen&&stage_index==20&&stage_layer==3&&stage_layout_seen&&stage_bg12_layout_seen&&stage_bg12_layout_captured&&stage_bg02_resource_count==48u&&stage_bg02_page_captured&&stage_bg02_transform_contract_seen&&stage_viewport_contract_seen&&stage_camera_pair_contract_seen&&stage_bg36_aux_projection_contract_seen&&stage_bg33_quad_contract_seen&&stage_bg12_contract_seen&&stage_bg12_updates>=2&&stage_bg33_layout_seen&&stage_bg33_layout_captured&&stage_bg33_scroll_seen&&stage_bg33_scroll_captured&&stage_bg33_slot_mask==0x3fffffffu&&stage_bg33_quad_draws==30u&&stage_bg33_tiles_loaded==24&&stage_bg36_layout_seen&&stage_bg36_layout_captured&&stage_bg36_scroll_seen&&stage_bg36_scroll_ticks>0&&stage_bg36_cloud_quads_projected>=2&&stage_bg37_scroll_captured&&stage_bg37_scroll_ticks>0&&stage_bg38_scroll_captured&&stage_bg38_scroll_ticks>0&&battle_bg33_ready&&battle_bg33_tiles==24u&&battle_bg33_updates>0&&battle_bg33_draws>0&&battle_bg33_slot_mask==0x3fffffffu&&battle_stage_selected_interactively&&stage_texture_seen&&stage_navigation_seen&&stage_constructor_asset_mask==31u&&stage_bg34_objects_seen&&stage_tiles_loaded==30&&stage_alt_tiles_loaded==30&&stage_static_loaded==4&&stage_objects_loaded==30&&practice_seen&&fight_seen&&jump_seen&&dash_gate_probe==1&&object_route_probe==5&&object_attack_routes==4&&suwako_418_burst_spawns==10&&object_anchor_probe==2&&object_sprite_seen&&object_render_capture&&dash_direct_hit_routes>0&&dash_direct_hit_routes+dash_no_direct_boxes==38&&pat_effect_fixture&&roster_card_count()==ROSTER_COUNT&&roster_asset_count()==ROSTER_COUNT&&roster_a_attack_mask==((1u<<ROSTER_COUNT)-1u)&&roster_a_natural_attack_mask==((1u<<ROSTER_COUNT)-1u)&&g.p[0].hits>0&&g.p[0].a_hits>0&&g.p[0].dashes>0&&g.p[0].b_hits>0&&g.p[0].c_hits>0&&skill_probe_success&&skill_probe_sequence_ok&&skill_probe_action==560&&skill_probe_image>=0&&skill_probe_hit_delta>0&&skill_air_launch_ok&&skill_landing_ok&&skill_x_delta>0&&skill_reverse_motion_ok&&skill_102_sequence_ok&&skill_102_image==774&&skill_102_hit_delta==1100&&skill_102_hit_sequence==3&&skill_102_hit_image==39&&skill_102_followup_ticks==47&&skill_107_sequence_ok&&skill_107_action==565&&skill_107_image==12&&skill_107_hit_delta==450&&skill_107_hit_sequence==1&&skill_107_hit_image==47&&skill_107_followup_ticks==63&&skill_104_phase_mask==7&&skill_104_sequence_ok&&skill_104_action==505&&skill_104_spawn_count==4&&skill_104_object_action==811&&skill_104_sprite_seen&&skill_104_hit_delta>0&&g.p[1].hp<g.max_hp&&loaded_textures>2;
            pass=pass&&suika_623c_probe==1&&suika_623b_probe==1&&battle_bg36_base_tiles==25u&&battle_bg36_base_draws==25u&&battle_bg36_base_slot_mask==0x3ffff79cu&&battle_bg36_capture_seen==1u&&battle_bg36_loaded==4u&&battle_bg36_draws>=4u&&battle_bg36_updates>0&&battle_bg36_draw_mask==15u;
            FILE *r=fopen("ux0:data/touhou123vita-smoke.json","w");
            uint32_t bg12_phase0=0,bg12_phase1=0;t123_bg12_render_time_args(stage_bg12_counter,&bg12_phase0,&bg12_phase1);
            if(r){fprintf(r,"{\"schema\":46,\"status\":\"%s\",\"frames\":600,\"regression_gate\":%d,\"arena_spawn_contract\":%d,\"udonge_409_contract\":%d,\"sprite_region_crop_contract\":%d,\"dash_gate_probe\":%d,\"suika_623c_probe\":%d,\"suika_623b_probe\":%d,\"suika_623b_route_mask\":%d,\"suika_623b_hit_delta\":%d,\"suika_623b_level5_hit_delta\":%d,\"suika_623b_level9_action_seen\":%d,\"suika_623b_level9_hit_delta\":%d,\"suika_623b_level9_objects\":%d,\"suika_623b_level9_object_x\":%.5f,\"suika_623b_level9_object_y\":%.5f,\"suika_623c_action_seen\":%d,\"suika_623c_skill_uses\":%d,\"suika_623c_hit_delta\":%d,\"suika_623c_level5_hit_delta\":%d,\"suika_623c_level9_action_seen\":%d,\"suika_623c_531_hit_delta\":%d,\"suika_623c_531_objects\":%d,\"suika_623c_route_mask\":%d,\"object_route_error\":%d,\"object_route_probe\":%u,\"object_attack_routes\":%u,\"object_anchor_probe\":%u,\"suwako_418_burst_spawns\":%u,\"remilia_object_linger_seen\":%u,\"remilia_trail_lifecycle_seen\":%u,\"remilia_spacing_pair\":%d,\"remilia_spacing_dx\":%.7f,\"remilia_spacing_dy\":%.7f,\"remilia_delta_samples\":[",pass?"passed":"failed",pass,arena_spawn_contract_seen,udonge_409_contract_seen,sprite_region_crop_contract_seen,dash_gate_probe,suika_623c_probe,suika_623b_probe,suika_623b_route_mask,suika_623b_hit_delta,suika_623b_level5_hit_delta,suika_623b_level9_action_seen,suika_623b_level9_hit_delta,suika_623b_level9_objects,suika_623b_level9_object_x,suika_623b_level9_object_y,suika_623c_action_seen,suika_623c_skill_uses,suika_623c_hit_delta,suika_623c_level5_hit_delta,suika_623c_level9_action_seen,suika_623c_531_hit_delta,suika_623c_531_objects,suika_623c_route_mask,object_route_error,object_route_probe,object_attack_routes,object_anchor_probe,suwako_418_burst_spawns,remilia_object_linger_seen,remilia_trail_lifecycle_seen,remilia_spacing_pair,remilia_spacing_dx,remilia_spacing_dy);for(unsigned i=0;i<5;i++)fprintf(r,"%s[%.7f,%.7f]",i?",":"",remilia_spacing_samples[i][0],remilia_spacing_samples[i][1]);fprintf(r,"],\"stage_viewport_contract\":%d,\"stage_camera_pair_contract\":%d,\"stage_bg36_aux_projection_contract\":%d,\"stage_bg33_quad_contract\":%d,\"stage_bg33_layout\":%d,\"stage_bg33_layout_capture\":%d,\"stage_bg33_scroll\":%d,\"stage_bg33_scroll_capture\":%d,\"stage_bg33_slots\":%u,\"stage_bg33_quad_draws\":%u,\"stage_bg33_tiles\":%d,\"stage_bg33_updates\":%u,\"stage_bg33_counter\":%u,\"stage_bg36_cloud_quads_projected\":%u,\"stage_bg37_scroll_capture\":%d,\"stage_bg37_scroll_ticks\":%u,\"stage_bg38_scroll_capture\":%d,\"stage_bg38_scroll_ticks\":%u,\"stage_bg37_tori1_x\":%.3f,\"stage_bg37_clowd_l_x\":%.3f,\"stage_bg38_cloud_l_x\":%.3f,\"stage_bg38_cloud_s_x\":%.3f,\"battle_bg33_tiles\":%u,\"battle_bg33_draws\":%u,\"battle_bg33_updates\":%u,\"battle_bg33_slots\":%u,\"battle_bg36_base_tiles\":%u,\"battle_bg36_base_draws\":%u,\"battle_bg36_base_slot_mask\":%u,\"battle_bg36_capture_seen\":%u,\"battle_bg36_loaded\":%u,\"battle_bg36_draws\":%u,\"battle_bg36_updates\":%u,\"battle_bg36_draw_mask\":%u,\"battle_bg36_clowd_l_x\":%.3f,\"battle_bg36_clowd_s_x\":%.3f,\"battle_bg36_capture_camera_x\":%.5f,\"battle_bg36_capture_camera_y\":%.5f,\"battle_bg36_capture_camera_zoom\":%.5f,\"battle_stage_selected_interactively\":%u}\n",stage_viewport_contract_seen,stage_camera_pair_contract_seen,stage_bg36_aux_projection_contract_seen,stage_bg33_quad_contract_seen,stage_bg33_layout_seen,stage_bg33_layout_captured,stage_bg33_scroll_seen,stage_bg33_scroll_captured,stage_bg33_slot_mask,stage_bg33_quad_draws,stage_bg33_tiles_loaded,stage_bg33_updates,stage_bg33_counter,stage_bg36_cloud_quads_projected,stage_bg37_scroll_captured,stage_bg37_scroll_ticks,stage_bg38_scroll_captured,stage_bg38_scroll_ticks,stage_bg37_scroll.tori1_x,stage_bg37_scroll.clowd_l_x,stage_bg38_scroll.clowd_l_x,stage_bg38_scroll.clowd_s_x,battle_bg33_tiles,battle_bg33_draws,battle_bg33_updates,battle_bg33_slot_mask,battle_bg36_base_tiles,battle_bg36_base_draws,battle_bg36_base_slot_mask,battle_bg36_capture_seen,battle_bg36_loaded,battle_bg36_draws,battle_bg36_updates,battle_bg36_draw_mask,battle_bg36_scroll.clowd_l_x,battle_bg36_scroll.clowd_s_x,battle_bg36_capture_camera_x,battle_bg36_capture_camera_y,battle_bg36_capture_camera_zoom,battle_stage_selected_interactively);fclose(r);}
            FILE *rf=fopen("ux0:data/touhou123vita-roster.tsv","w");if(rf){fprintf(rf,"character\tpat_loaded\ttexture_loaded\tfirst_image\n");for(unsigned i=0;i<ROSTER_COUNT;i++)fprintf(rf,"%s\t%d\t%d\t%s\n",roster[i],!!(roster_pat_mask&(1u<<i)),!!(roster_asset_mask&(1u<<i)),roster_first_image[i]);fclose(rf);}
            FILE *bcf=fopen("ux0:data/touhou123vita-bc-natural.tsv","w");
            if(bcf){
                fprintf(bcf,"character\tb_candidates\tb_reached_mask\tb_408_variant\tb_409_variant\tb_hit_action\tb_hit_frame\tb_damage\tb_source\tb_pose\tb_hit_gap\tc_candidates\tc_reached_mask\tc_418_variant\tc_418_overlap_seen\tc_418_horizontal_overlap_seen\tc_418_vertical_overlap_seen\tc_418_min_active_gap\tc_418_min_signed_gap\tc_418_min_horizontal_when_vertical_overlap\tc_418_min_vertical_gap\tc_hit_action\tc_hit_frame\tc_damage\tc_source\tc_pose\tc_hit_gap\tmotion_c_base_action\tmotion_c_base_damage\tmotion_c_level5_action\tmotion_c_level5_damage\tmotion_c_level9_action\tmotion_c_level9_damage\n");
                for(unsigned i=0;i<ROSTER_COUNT;i++){
                    int is_suika=i==9;
                    int min_gap=roster_c_418_min_active_gap[i]==INT32_MAX?-1:roster_c_418_min_active_gap[i];
                    int min_horizontal_gap=roster_c_418_min_horizontal_gap[i]==INT32_MAX?-1:roster_c_418_min_horizontal_gap[i];
                    int min_vertical_gap=roster_c_418_min_vertical_gap[i]==INT32_MAX?-1:roster_c_418_min_vertical_gap[i];
                    fprintf(bcf,"%s\t0x%02X\t0x%02X\t%d\t%d\t%d\t%u\t%u\t%d\t%d\t%d\t0x%02X\t0x%02X\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%u\t%u\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
                        roster[i],roster_b_natural_candidates[i],roster_b_reached_mask[i],roster_b_408_variant[i],roster_b_409_variant[i],roster_b_natural_action[i],roster_b_hit_frame[i],roster_b_hit_damage[i],roster_b_hit_source[i],roster_b_hit_pose[i],roster_b_hit_gap[i],roster_c_natural_candidates[i],roster_c_reached_mask[i],roster_c_418_variant[i],roster_c_418_overlap_seen[i],roster_c_418_horizontal_overlap_seen[i],roster_c_418_vertical_overlap_seen[i],min_gap,roster_c_418_min_signed_gap[i],min_horizontal_gap,min_vertical_gap,roster_c_natural_action[i],roster_c_hit_frame[i],roster_c_hit_damage[i],roster_c_hit_source[i],roster_c_hit_pose[i],roster_c_hit_gap[i],is_suika&&(suika_623c_route_mask&1)?521:0,is_suika?suika_623c_hit_delta:0,is_suika&&(suika_623c_route_mask&2)?526:0,is_suika?suika_623c_level5_hit_delta:0,is_suika&&(suika_623c_route_mask&4)&&(suika_623c_route_mask&16)?531:0,is_suika?suika_623c_531_hit_delta:0);
                }
                fclose(bcf);
            }
            break;
        }
    }
    for(int i=0;i<2;i++)if(sprites[i])soft2d_free_texture(sprites[i]);
    for(int i=0;i<2;i++)if(roster_cards[i])soft2d_free_texture(roster_cards[i]);
    for(unsigned row=0;row<4;row++)for(unsigned col=0;col<6;col++)if(battle_bg33_assets[row][col])soft2d_free_texture(battle_bg33_assets[row][col]);
    for(unsigned i=0;i<4;i++)if(battle_bg36_assets[i])soft2d_free_texture(battle_bg36_assets[i]);
    for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++)if(battle_bg36_tiles[row][col])soft2d_free_texture(battle_bg36_tiles[row][col]);
    if(background)soft2d_free_texture(background);
    for(unsigned row=0;row<5;row++)for(unsigned col=0;col<6;col++){if(stage_tiles[row][col])soft2d_free_texture(stage_tiles[row][col]);if(stage_alt_tiles[row][col])soft2d_free_texture(stage_alt_tiles[row][col]);}
    for(unsigned i=0;i<4;i++)if(stage_extras[i])soft2d_free_texture(stage_extras[i]);
    for(unsigned i=0;i<30;i++)if(stage_objects[i])soft2d_free_texture(stage_objects[i]);
    for(unsigned i=0;i<64;i++)soft2d_free_texture(cache[i].texture);
    t123_pattern_free(&patterns[0]);t123_pattern_free(&patterns[1]);t123_resources_close(&resources);
    soft2d_free_pgf(font);soft2d_fini();sceKernelExitProcess(0);return 0;
}
