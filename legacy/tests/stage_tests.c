#include <stdio.h>
#include "t123/stage.h"

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"line %d: %s\n",__LINE__,#x); return 1; } } while (0)

int main(void) {
    T123StageCameraTarget camera_target;
    CHECK(t123_stage_camera_pair_target(200.0f,0.0f,200.0f,0.0f,&camera_target));
    CHECK(camera_target.distance == 640.0f && camera_target.zoom == 1.0f);
    CHECK(camera_target.center_x == 320.0f);
    CHECK(t123_stage_camera_pair_target(200.0f,0.0f,300.0f,100.0f,&camera_target));
    CHECK(camera_target.distance > 657.343f && camera_target.distance < 657.344f);
    CHECK(camera_target.zoom > 0.973615f && camera_target.zoom < 0.973617f);
    CHECK(camera_target.center_x > 328.671f && camera_target.center_x < 328.673f);
    CHECK(t123_stage_camera_pair_target(200.0f,0.0f,900.0f,0.0f,&camera_target));
    CHECK(camera_target.distance == 780.0f && camera_target.zoom > 0.820512f && camera_target.zoom < 0.820514f);
    CHECK(t123_stage_camera_pair_target(200.0f,0.0f,2200.0f,0.0f,&camera_target));
    CHECK(camera_target.distance == 2080.0f && camera_target.zoom == 0.5f);
    CHECK(camera_target.center_x == 960.0f);
    CHECK(!t123_stage_camera_pair_target(0.0f,0.0f,0.0f,0.0f,NULL));
    float camera_y_target;
    CHECK(t123_stage_camera_y_target(0.0f,-500.0f,1.0f,&camera_y_target));
    CHECK(camera_y_target==-100.0f);
    CHECK(t123_stage_camera_y_target(0.0f,-500.0f,0.8f,&camera_y_target));
    CHECK(camera_y_target>-60.001f&&camera_y_target<-59.999f);
    CHECK(t123_stage_camera_y_target(0.0f,-500.0f,0.59145278f,&camera_y_target));
    CHECK(camera_y_target>-18.292f&&camera_y_target<-18.289f);
    CHECK(t123_stage_camera_y_target(500.0f,600.0f,1.0f,&camera_y_target));
    CHECK(camera_y_target==-420.0f);
    CHECK(!t123_stage_camera_y_target(0.0f,0.0f,0.4f,&camera_y_target));
    CHECK(t123_stage_camera_y_step(-100.0f,-18.29056f,0.0f,-500.0f,
                                  0.59145278f,&camera_y_target));
    CHECK(camera_y_target>-76.821f&&camera_y_target<-76.819f);
    CHECK(t123_stage_camera_y_step(-76.820335f,-18.29056f,0.0f,-500.0f,
                                  0.59145278f,&camera_y_target));
    CHECK(camera_y_target>-72.895f&&camera_y_target<-72.892f);
    CHECK(t123_stage_camera_y_step(0.0f,-269.23077f,500.0f,500.0f,
                                  0.82051283f,&camera_y_target));
    CHECK(camera_y_target>-27.925f&&camera_y_target<-27.921f);
    T123StageCamera live_camera={550.0f,-18.29056f,0.59145278f,
                                 550.0f,-76.820335f,0.59145278f};
    CHECK(t123_stage_camera_step(&live_camera,200.0f,0.0f,900.0f,-500.0f));
    CHECK(live_camera.target_x==550.0f&&live_camera.target_zoom>0.59145f&&
          live_camera.target_zoom<0.59146f);
    CHECK(live_camera.x==550.0f&&live_camera.zoom>0.59145f&&
          live_camera.zoom<0.59146f&&live_camera.y>-72.895f&&live_camera.y<-72.892f);
    T123StageCamera invalid_camera=live_camera;invalid_camera.zoom=0.4f;
    CHECK(!t123_stage_camera_step(&invalid_camera,200.0f,0.0f,900.0f,-500.0f));
    float screen_x,screen_y;
    T123StageCamera far_camera={550.0f,0.0f,0.82051283f,
                                550.0f,0.0f,0.82051283f};
    CHECK(t123_stage_camera_project(&far_camera,200.0f,0.0f,0.0f,0.0f,
                                    &screen_x,&screen_y));
    CHECK(screen_x>32.81f&&screen_x<32.83f&&screen_y==420.0f);
    CHECK(t123_stage_camera_project(&far_camera,900.0f,0.0f,0.0f,0.0f,
                                    &screen_x,&screen_y));
    CHECK(screen_x>607.17f&&screen_x<607.19f);
    CHECK(!t123_stage_camera_project(&far_camera,0.0f,0.0f,0.0f,0.0f,NULL,&screen_y));
    float zoom_step;
    CHECK(t123_stage_camera_zoom_step(0.5f,1.0f,&zoom_step));
    CHECK(zoom_step>0.50824f&&zoom_step<0.50826f);
    CHECK(t123_stage_camera_zoom_step(1.0f,0.82051283f,&zoom_step));
    CHECK(zoom_step>0.96210f&&zoom_step<0.96211f);
    CHECK(t123_stage_camera_zoom_step(0.501f,0.5f,&zoom_step));
    CHECK(zoom_step==0.5f);
    CHECK(!t123_stage_camera_zoom_step(0.4f,1.0f,&zoom_step));
    CHECK(!t123_stage_camera_zoom_step(1.0f,1.0f,NULL));
    float camera_x_step;
    CHECK(t123_stage_camera_x_step(400.0f,550.0f,1.0f,&camera_x_step));
    CHECK(camera_x_step==410.0f);
    CHECK(t123_stage_camera_x_step(200.0f,550.0f,0.96210259f,&camera_x_step));
    CHECK(camera_x_step>332.60f&&camera_x_step<332.61f);
    CHECK(t123_stage_camera_x_step(1000.0f,550.0f,0.96210259f,&camera_x_step));
    CHECK(camera_x_step>947.39f&&camera_x_step<947.40f);

    T123Bg36Scroll s;
    t123_bg36_scroll_init(&s);
    CHECK(s.clowd_l_x == -400.0f);
    CHECK(s.clowd_s_x == -300.0f);
    float bg36_anchor_x=0.0f,bg36_anchor_y=0.0f;
    CHECK(t123_bg36_tile_anchor(0,&bg36_anchor_x,&bg36_anchor_y));
    CHECK(bg36_anchor_x==700.0f&&bg36_anchor_y==946.0f);
    CHECK(t123_bg36_tile_anchor(29,&bg36_anchor_x,&bg36_anchor_y));
    CHECK(bg36_anchor_x==-580.0f&&bg36_anchor_y==-78.0f);
    CHECK(!t123_bg36_tile_anchor(30,&bg36_anchor_x,&bg36_anchor_y));
    CHECK(!t123_bg36_tile_anchor(0,NULL,&bg36_anchor_y));
    T123StageCamera bg36_camera={0.0f,0.0f,1.0f,0.0f,0.0f,1.0f};
    T123StageQuad bg36_tile_quad;
    CHECK(t123_bg36_project_tile_quad(0,&bg36_camera,&bg36_tile_quad));
    CHECK(bg36_tile_quad.x[0]==260.0f&&bg36_tile_quad.y[0]==-526.0f);
    CHECK(bg36_tile_quad.x[3]==516.0f&&bg36_tile_quad.y[3]==-270.0f);
    CHECK(t123_bg36_project_tile_quad(29,&bg36_camera,&bg36_tile_quad));
    CHECK(bg36_tile_quad.x[0]==1540.0f&&bg36_tile_quad.y[0]==498.0f);
    CHECK(bg36_tile_quad.x[3]==1796.0f&&bg36_tile_quad.y[3]==754.0f);
    CHECK(!t123_bg36_project_tile_quad(30,&bg36_camera,&bg36_tile_quad));
    CHECK(!t123_bg36_project_tile_quad(0,NULL,&bg36_tile_quad));

    T123StageQuad cloud_quad;
    CHECK(t123_bg36_project_aux_quad(0, 100.0f, 50.0f, 0.0f, 0.0f,
                                    1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                                    1.0f, 1.0f, &cloud_quad));
    CHECK(cloud_quad.x[0] == 910.0f && cloud_quad.y[0] == 370.0f);
    CHECK(cloud_quad.x[3] == 1010.0f && cloud_quad.y[3] == 420.0f);
    CHECK(t123_bg36_project_aux_quad(1, 100.0f, 50.0f, 0.0f, 0.0f,
                                    1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                                    1.0f, 1.0f, &cloud_quad));
    CHECK(cloud_quad.x[0] == 910.0f && cloud_quad.y[0] == 370.0f);
    CHECK(cloud_quad.x[3] == 1010.0f && cloud_quad.y[3] == 420.0f);
    CHECK(t123_bg36_project_aux_quad(2, 100.0f, 50.0f, -400.0f, -750.0f,
                                       1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                                       1.0f, 1.0f, &cloud_quad));
    CHECK(cloud_quad.x[0] == 560.0f && cloud_quad.y[0] == -330.0f);
    CHECK(cloud_quad.x[3] == 660.0f && cloud_quad.y[3] == -280.0f);
    CHECK(t123_bg36_project_aux_quad(3, 100.0f, 50.0f, -300.0f, -320.0f,
                                      1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                                      1.0f, 1.0f, &cloud_quad));
    CHECK(cloud_quad.x[0] == 610.0f && cloud_quad.y[0] == 50.0f);
    CHECK(cloud_quad.x[3] == 710.0f && cloud_quad.y[3] == 100.0f);
    CHECK(!t123_bg36_project_cloud_quad(1, 100.0f, 50.0f, 0.0f, 0.0f,
                                       1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                                       1.0f, 1.0f, &cloud_quad));
    CHECK(!t123_bg36_project_cloud_quad(2, 100.0f, 50.0f, 0.0f, 0.0f,
                                       0.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                                       1.0f, 1.0f, &cloud_quad));

    t123_bg36_scroll_update(&s);
    CHECK(s.clowd_l_x == -401.5f);
    CHECK(s.clowd_s_x == -301.0f);
    for (unsigned i = 1; i < 500; ++i) t123_bg36_scroll_update(&s);
    CHECK(s.clowd_l_x == -1150.0f);
    CHECK(s.clowd_s_x == -800.0f);
    t123_bg36_scroll_update(&s);
    CHECK(s.clowd_l_x == -1151.5f);
    CHECK(s.clowd_s_x == 800.0f);
    for (unsigned i = 501; i < 534; ++i) t123_bg36_scroll_update(&s);
    CHECK(s.clowd_l_x == 800.0f);
    CHECK(s.clowd_s_x == 767.0f);
    t123_bg36_scroll_update(&s);
    CHECK(s.clowd_l_x == 798.5f);
    CHECK(s.clowd_s_x == 766.0f);

    t123_bg36_scroll_init(&s);
    CHECK(s.clowd_l_x == -400.0f && s.clowd_s_x == -300.0f);
    t123_bg36_scroll_update(NULL);
    t123_bg36_scroll_init(NULL);

    T123Bg37Scroll bg37;
    t123_bg37_scroll_init(&bg37);
    CHECK(bg37.counter == 0 && bg37.tori1_x == -400.0f && bg37.clowd_l_x == -300.0f);
    for (unsigned i = 0; i < 534; ++i) t123_bg37_scroll_update(&bg37);
    CHECK(bg37.counter == 534 && bg37.tori1_x == 800.0f && bg37.clowd_l_x == 767.0f);
    t123_bg37_scroll_update(NULL);
    t123_bg37_scroll_init(NULL);

    T123Bg38Scroll bg38;
    t123_bg38_scroll_init(&bg38);
    CHECK(bg38.clowd_l_x == -400.0f && bg38.clowd_s_x == -300.0f);
    for (unsigned i = 0; i < 534; ++i) t123_bg38_scroll_update(&bg38);
    CHECK(bg38.clowd_l_x == 800.0f && bg38.clowd_s_x == 767.0f);
    t123_bg38_scroll_update(NULL);
    t123_bg38_scroll_init(NULL);

    uint32_t frame = 0, first = 0, second = 0;
    t123_stage_animation_update(12, &frame);
    CHECK(frame == 1);
    t123_stage_animation_update(12, &frame);
    CHECK(frame == 2);
    t123_bg12_render_time_args(frame, &first, &second);
    CHECK(first == 4 && second == 94);
    float torii_x = 0.0f, torii_y = 0.0f;
    t123_bg12_torii_base_translation(&torii_x, &torii_y);
    CHECK(torii_x == 492.0f && torii_y == -401.0f);
    t123_bg12_torii_base_translation(NULL, &torii_y);
    CHECK(torii_y == -401.0f);

    CHECK(t123_bg02_frame(0) == 0);
    CHECK(t123_bg02_frame(2) == 0);
    CHECK(t123_bg02_frame(3) == 1);
    CHECK(t123_bg02_frame(47) == 15);
    CHECK(t123_bg02_frame(48) == 0);
    CHECK(t123_bg02_sprite_index(3, 0) == 3);
    CHECK(t123_bg02_sprite_index(3, 1) == 4);
    CHECK(t123_bg02_sprite_index(3, 2) == 5);
    CHECK(t123_bg02_sprite_index(3, 3) == UINT32_MAX);
    float bg02_x = 0.0f, bg02_y = 0.0f;
    CHECK(t123_bg02_sprite_offset(0, &bg02_x, &bg02_y));
    CHECK(bg02_x == -332.0f && bg02_y == -472.0f);
    CHECK(t123_bg02_sprite_offset(1, &bg02_x, &bg02_y));
    CHECK(bg02_x == 0.0f && bg02_y == 0.0f);
    CHECK(t123_bg02_sprite_offset(2, &bg02_x, &bg02_y));
    CHECK(bg02_x == 312.0f && bg02_y == -472.0f);
    CHECK(!t123_bg02_sprite_offset(3, &bg02_x, &bg02_y));

    frame = 0;
    t123_stage_animation_update(10, &frame);
    CHECK(frame == 4);
    frame = 0;
    t123_stage_animation_update(11, &frame);
    CHECK(frame == 4);
    frame = 0;
    t123_stage_animation_update(13, &frame);
    CHECK(frame == 11);
    frame = 123;
    t123_stage_animation_update(14, &frame);
    CHECK(frame == 123);
    frame = 0x3feu;
    t123_stage_animation_update(33, &frame);
    CHECK(frame == 0x3ffu);
    t123_stage_animation_update(33, &frame);
    CHECK(frame == 0u);
    frame = 255u;
    t123_stage_animation_update(33, &frame);
    CHECK(frame == 256u);
    T123Bg33RenderSlot bg33_slot;
    CHECK(t123_bg33_render_slot(0, 0, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 0 && bg33_slot.x == 0 && bg33_slot.y == 0);
    CHECK(t123_bg33_render_slot(0, 23, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 23 && bg33_slot.x == 0 && bg33_slot.y == 0);
    CHECK(t123_bg33_render_slot(0, 24, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 0 && bg33_slot.x == 0 && bg33_slot.y == 1024);
    CHECK(t123_bg33_render_slot(256, 0, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 6 && bg33_slot.x == 0 && bg33_slot.y == -256);
    CHECK(t123_bg33_render_slot(256, 18, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 0 && bg33_slot.x == 0 && bg33_slot.y == 768);
    CHECK(t123_bg33_render_slot(1023, 29, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 23 && bg33_slot.x == 0 && bg33_slot.y == 1);
    CHECK(t123_bg33_render_slot(1024, 0, &bg33_slot));
    CHECK(bg33_slot.sprite_index == 0 && bg33_slot.x == 0 && bg33_slot.y == 0);
    /* Exhaust the renderer's 30 draw slots across every 8-bit phase. The PE
       advances the source grid by six sprites per phase and wraps at 24. */
    for (uint32_t counter = 0; counter <= 1023; counter += 64) {
        uint32_t phase = counter >> 8;
        for (uint32_t slot = 0; slot < 30; ++slot) {
            CHECK(t123_bg33_render_slot(counter, slot, &bg33_slot));
            uint32_t requested = slot + phase * 6u;
            uint32_t index = requested % 24u;
            int32_t expected_y = -(int32_t)counter + (requested >= 24u ? 1024 : 0);
            CHECK(bg33_slot.sprite_index == index);
            CHECK(bg33_slot.x == 0);
            CHECK(bg33_slot.y == expected_y);
        }
    }
    CHECK(!t123_bg33_render_slot(0, 30, &bg33_slot));
    CHECK(!t123_bg33_render_slot(0, 0, NULL));
    T123StageMatrixTranslation viewport;
    CHECK(t123_stage_viewport_translation(1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 1.0f, &viewport));
    CHECK(viewport.x == 960.0f && viewport.y == 420.0f);
    CHECK(t123_stage_viewport_translation(2.0f, 100.0f, 50.0f, 20.0f, 30.0f, 0.5f, 2.0f, &viewport));
    CHECK(viewport.x == 420.0f && viewport.y == 50.0f);
    CHECK(!t123_stage_viewport_translation(0.0f, 0, 0, 0, 0, 1, 1, &viewport));
    CHECK(!t123_stage_viewport_translation(1.0f, 0, 0, 0, 0, 1, 1, NULL));
    T123StageQuad bg33_quad;
    bg33_slot.sprite_index=0;bg33_slot.x=0;bg33_slot.y=0;
    CHECK(t123_bg33_project_slot_quad(&bg33_slot,0,0,1,0,0,0,0,1,1,&bg33_quad));
    CHECK(bg33_quad.x[0]==260.0f&&bg33_quad.y[0]==-440.0f);
    CHECK(bg33_quad.x[1]==516.0f&&bg33_quad.y[1]==-440.0f);
    CHECK(bg33_quad.x[2]==260.0f&&bg33_quad.y[2]==-184.0f);
    CHECK(bg33_quad.x[3]==516.0f&&bg33_quad.y[3]==-184.0f);
    bg33_slot.y=1024;
    CHECK(t123_bg33_project_slot_quad(&bg33_slot,0,0,1,0,0,0,0,1,1,&bg33_quad));
    CHECK(bg33_quad.y[0]==584.0f&&bg33_quad.y[3]==840.0f);
    CHECK(!t123_bg33_project_slot_quad(&bg33_slot,0,0,0,0,0,0,0,1,1,&bg33_quad));
    bg33_slot.sprite_index=24;
    CHECK(!t123_bg33_project_slot_quad(&bg33_slot,0,0,1,0,0,0,0,1,1,&bg33_quad));
    frame = UINT32_MAX;
    t123_stage_animation_update(12, &frame);
    CHECK(frame == 0);
    first = second = 0;
    t123_bg12_render_time_args(0, NULL, &second);
    CHECK(first == 0 && second == 90);
    return 0;
}
