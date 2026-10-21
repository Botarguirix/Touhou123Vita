#ifndef T123_STAGE_H
#define T123_STAGE_H
#include <stdint.h>

typedef struct {
    float clowd_l_x;
    float clowd_s_x;
} T123Bg36Scroll;

typedef struct {
    uint32_t counter;
    float tori1_x;
    float clowd_l_x;
} T123Bg37Scroll;

typedef struct {
    float clowd_l_x;
    float clowd_s_x;
} T123Bg38Scroll;

typedef struct {
    uint32_t sprite_index;
    int32_t x;
    int32_t y;
} T123Bg33RenderSlot;

typedef struct {
    float x;
    float y;
} T123StageMatrixTranslation;

typedef struct {
    float x[4];
    float y[4];
} T123StageQuad;

typedef struct {
    float distance;
    float zoom;
    float center_x;
} T123StageCameraTarget;

typedef struct {
    float target_x, target_y, target_zoom;
    float x, y, zoom;
} T123StageCamera;

/* Automatic two-player horizontal target and zoom from PE FUN_00428e20.
   Vertical target requires the initialized per-instance camera state. */
int t123_stage_camera_pair_target(float player0_x, float player0_y,
                                  float player1_x, float player1_y,
                                  T123StageCameraTarget *out);
/* Vertical target from FUN_00428e20; current zoom is part of the state. */
int t123_stage_camera_y_target(float player0_y, float player1_y,
                               float current_zoom, float *out_y);
/* One-frame vertical easing and zoom-dependent viewport bounds. */
int t123_stage_camera_y_step(float current_y, float target_y,
                             float player0_y, float player1_y,
                             float current_zoom, float *out_y);
/* One-frame zoom easing from PE FUN_00429040. */
int t123_stage_camera_zoom_step(float current_zoom, float target_zoom,
                                float *out_zoom);
/* One-frame horizontal camera easing and stage-edge clamp. */
int t123_stage_camera_x_step(float current_x, float target_x,
                             float current_zoom, float *out_x);
/* Refresh automatic targets and advance the original camera by one frame. */
int t123_stage_camera_step(T123StageCamera *camera,
                           float player0_x, float player0_y,
                           float player1_x, float player1_y);
/* Character transform from FUN_004293f0 / FUN_00429370. */
int t123_stage_camera_project(const T123StageCamera *camera,
                              float world_x, float world_y,
                              float viewport_x, float viewport_y,
                              float *screen_x, float *screen_y);

/* BG36's renderer applies +0x68/+0x6c to clowd_l/clowd_s at y=-750/-320.
   The update callback subtracts 1.5/1.0 and wraps below -1200/-800 to 800. */
void t123_bg36_scroll_init(T123Bg36Scroll *scroll);
void t123_bg36_scroll_update(T123Bg36Scroll *scroll);
/* Constructor-authored BG36 base tile anchors from FUN_0046fe40. The original
   constructor requests 30 tiles; missing DAT entries remain null/undrawn. */
int t123_bg36_tile_anchor(uint32_t slot, float *stage_x, float *stage_y);
int t123_bg36_project_tile_quad(uint32_t slot, const T123StageCamera *camera,
                                T123StageQuad *out);
/* Project BG36 constructor auxiliaries through the exact viewport transform.
   Slots 0/1/3 pivot at bottom-center; slot 2 pivots at top-left. */
int t123_bg36_project_aux_quad(uint32_t aux_slot, float width, float height,
                               float stage_x, float stage_y, float zoom,
                               float camera_x, float camera_y,
                               float viewport_x, float viewport_y,
                               float factor_x, float factor_y,
                               T123StageQuad *out);
/* Convenience wrapper for the two BG36 clouds (slots 2 and 3). */
int t123_bg36_project_cloud_quad(uint32_t aux_slot, float width, float height,
                                 float stage_x, float stage_y, float zoom,
                                 float camera_x, float camera_y,
                                 float viewport_x, float viewport_y,
                                 float factor_x, float factor_y,
                                 T123StageQuad *out);

/* BG37 shares BG36's update callback: +0x68 moves tori1, +0x6c moves
   clowd_l. clowd_s uses a fixed renderer translation. */
void t123_bg37_scroll_init(T123Bg37Scroll *scroll);
void t123_bg37_scroll_update(T123Bg37Scroll *scroll);

/* BG38 has its own update callback but uses the same initial offsets and
   cloud rates/wraps as BG36 in the pinned PE. */
void t123_bg38_scroll_init(T123Bg38Scroll *scroll);
void t123_bg38_scroll_update(T123Bg38Scroll *scroll);

/* Base Background::updateAnimation contract at Player/Background+0x64.
   Stage IDs are the original global background IDs used by TH123. */
void t123_stage_animation_update(uint32_t stage_id, uint32_t *counter);

/* BG12's render method passes these time parameters to each of its two
   constructor-created sprites. They are not screen coordinates or frames. */
void t123_bg12_render_time_args(uint32_t counter, uint32_t *first, uint32_t *second);

/* BG12 render applies this shared sprite-local translation before adding the
   stage object's +0x44/+0x48 offsets. It is not final screen/camera position. */
void t123_bg12_torii_base_translation(float *x, float *y);

/* BG02's PE renderer divides +0x64 by three, wraps over 16 groups, then
   addresses three consecutive sprites (left/center/right) for that frame.
   Their local offsets are (-332,-472), the stage object's origin, and
   (312,-472), respectively. Camera projection is applied later by the PE. */
uint32_t t123_bg02_frame(uint32_t counter);
uint32_t t123_bg02_sprite_index(uint32_t counter, uint32_t segment);
int t123_bg02_sprite_offset(uint32_t segment, float *x, float *y);

/* BG33 slot 4 selects one of 24 constructor-created sprites for each of
   30 draw slots. Its per-draw translation is x=0 and y=-counter, with +1024
   for wrapped source indices. Tile anchors are already stored in sprite
   geometry by the constructor. */
int t123_bg33_render_slot(uint32_t counter, uint32_t slot, T123Bg33RenderSlot *out);

/* Shared stage viewport matrix translation from PE FUN_00429440. The
   per-axis factors are supplied by each renderer; these are matrix-space
   translations, not final framebuffer coordinates. */
int t123_stage_viewport_translation(float zoom, float camera_x, float camera_y,
                                    float viewport_x, float viewport_y,
                                    float factor_x, float factor_y,
                                    T123StageMatrixTranslation *out);

/* Rebuild BG33's constructor-authored tile quad and apply the exact local
   stage translation followed by FUN_00429440 viewport translation/scaling.
   Output stays in the game's logical coordinates, before Vita framebuffer fit. */
int t123_bg33_project_slot_quad(const T123Bg33RenderSlot *slot,
                                float stage_x, float stage_y, float zoom,
                                float camera_x, float camera_y,
                                float viewport_x, float viewport_y,
                                float factor_x, float factor_y,
                                T123StageQuad *out);

#endif
