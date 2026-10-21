#include "t123/stage.h"
#include <math.h>

int t123_stage_camera_pair_target(float player0_x, float player0_y,
                                  float player1_x, float player1_y,
                                  T123StageCameraTarget *out) {
    if (!out || !isfinite(player0_x) || !isfinite(player0_y) ||
        !isfinite(player1_x) || !isfinite(player1_y)) return 0;
    float horizontal = fabsf(player0_x - player1_x) + 80.0f;
    if (horizontal < 640.0f) horizontal = 640.0f;
    float vertical = fabsf(player0_y - player1_y) * 1.5f;
    out->distance = sqrtf(horizontal * horizontal + vertical * vertical);
    out->zoom = 640.0f / out->distance;
    if (out->zoom < 0.5f) out->zoom = 0.5f;
    float center_x = (player0_x + player1_x) * 0.5f;
    float minimum_x = 320.0f / out->zoom;
    if (center_x < minimum_x) center_x = minimum_x;
    if (center_x > 960.0f) center_x = 960.0f;
    out->center_x = center_x;
    return 1;
}

int t123_stage_camera_y_target(float player0_y, float player1_y,
                               float current_zoom, float *out_y) {
    if (!out_y || !isfinite(player0_y) || !isfinite(player1_y) ||
        !isfinite(current_zoom) || current_zoom < 0.5f) return 0;
    float minimum_y = player0_y < player1_y ? player0_y : player1_y;
    float target_y;
    if (minimum_y > 270.0f) {
        target_y = -minimum_y;
        if (target_y < -420.0f) target_y = -420.0f;
    } else {
        target_y = -fabsf(player0_y - player1_y) * 0.2f *
                   (2.0f * current_zoom - 1.0f);
        if (target_y < -420.0f) target_y = -420.0f;
    }
    *out_y = target_y;
    return 1;
}

int t123_stage_camera_y_step(float current_y, float target_y,
                             float player0_y, float player1_y,
                             float current_zoom, float *out_y) {
    if (!out_y || !isfinite(current_y) || !isfinite(target_y) ||
        !isfinite(player0_y) || !isfinite(player1_y) ||
        !isfinite(current_zoom) || current_zoom < 0.5f) return 0;
    float difference = target_y - current_y;
    float next = current_y;
    float divisor = (player0_y < player1_y ? player0_y : player1_y) > 270.0f
                        ? 10.0f : 20.0f;
    if (difference > 0.0f) {
        next += difference / divisor + 1.0f;
        if (next > target_y) next = target_y;
    } else if (difference < 0.0f) {
        next += difference / divisor - 1.0f;
        if (next < target_y) next = target_y;
    }
    float zoom_factor = 2.0f * current_zoom - 1.0f;
    float minimum = -420.0f * zoom_factor;
    if (next < minimum) next = minimum;
    if (next > 0.0f) next = 0.0f;
    *out_y = next;
    return 1;
}

int t123_stage_camera_zoom_step(float current_zoom, float target_zoom,
                                float *out_zoom) {
    if (!out_zoom || !isfinite(current_zoom) || !isfinite(target_zoom) ||
        current_zoom < 0.5f || target_zoom < 0.5f) return 0;
    float next;
    if (current_zoom > target_zoom) {
        next = current_zoom + (target_zoom - current_zoom) / 5.0f - 0.002f;
        if (next < target_zoom) next = target_zoom;
    } else if (current_zoom < target_zoom) {
        next = current_zoom + (target_zoom - current_zoom) / 80.0f + 0.002f;
        if (next > target_zoom) next = target_zoom;
    } else {
        next = target_zoom;
    }
    if (next < 0.5f) next = 0.5f;
    *out_zoom = next;
    return 1;
}

int t123_stage_camera_x_step(float current_x, float target_x,
                             float current_zoom, float *out_x) {
    if (!out_x || !isfinite(current_x) || !isfinite(target_x) ||
        !isfinite(current_zoom) || current_zoom < 0.5f) return 0;
    float difference = target_x - current_x;
    float next = current_x;
    if (difference > 0.0f) {
        next += difference / 30.0f + 5.0f;
        if (next > target_x) next = target_x;
    } else if (difference < 0.0f) {
        next += difference / 30.0f - 5.0f;
        if (next < target_x) next = target_x;
    }
    float half_view = 320.0f / current_zoom;
    float minimum = half_view;
    float maximum = 1280.0f - half_view;
    if (next < minimum) next = minimum;
    if (next > maximum) next = maximum;
    *out_x = next;
    return 1;
}

int t123_stage_camera_step(T123StageCamera *camera,
                           float player0_x, float player0_y,
                           float player1_x, float player1_y) {
    if (!camera || !isfinite(camera->x) || !isfinite(camera->y) ||
        !isfinite(camera->zoom) || !isfinite(camera->target_x) ||
        !isfinite(camera->target_y) || !isfinite(camera->target_zoom) ||
        camera->zoom < 0.5f || camera->target_zoom < 0.5f) return 0;
    T123StageCameraTarget target;
    float target_y, zoom, x, y;
    if (!t123_stage_camera_pair_target(player0_x, player0_y,
                                       player1_x, player1_y, &target) ||
        !t123_stage_camera_y_target(player0_y, player1_y,
                                    camera->zoom, &target_y) ||
        !t123_stage_camera_zoom_step(camera->zoom, target.zoom, &zoom) ||
        !t123_stage_camera_x_step(camera->x, target.center_x, zoom, &x) ||
        !t123_stage_camera_y_step(camera->y, target_y, player0_y, player1_y,
                                  zoom, &y)) return 0;
    camera->target_x = target.center_x;
    camera->target_y = target_y;
    camera->target_zoom = target.zoom;
    camera->x = x;
    camera->y = y;
    camera->zoom = zoom;
    return 1;
}

int t123_stage_camera_project(const T123StageCamera *camera,
                              float world_x, float world_y,
                              float viewport_x, float viewport_y,
                              float *screen_x, float *screen_y) {
    if (!camera || !screen_x || !screen_y || !isfinite(world_x) ||
        !isfinite(world_y) || !isfinite(viewport_x) ||
        !isfinite(viewport_y) || !isfinite(camera->x) ||
        !isfinite(camera->y) || !isfinite(camera->zoom) ||
        camera->zoom < 0.5f) return 0;
    *screen_x = (world_x - camera->x - viewport_x) * camera->zoom + 320.0f;
    *screen_y = (world_y - camera->y - viewport_y) * camera->zoom + 420.0f;
    return 1;
}

void t123_bg36_scroll_init(T123Bg36Scroll *scroll) {
    if (!scroll) return;
    scroll->clowd_l_x = -400.0f;
    scroll->clowd_s_x = -300.0f;
}

void t123_bg36_scroll_update(T123Bg36Scroll *scroll) {
    if (!scroll) return;
    scroll->clowd_l_x -= 1.5f;
    if (scroll->clowd_l_x < -1200.0f) scroll->clowd_l_x = 800.0f;
    scroll->clowd_s_x -= 1.0f;
    if (scroll->clowd_s_x < -800.0f) scroll->clowd_s_x = 800.0f;
}

int t123_bg36_tile_anchor(uint32_t slot, float *stage_x, float *stage_y) {
    if (slot >= 30u || !stage_x || !stage_y) return 0;
    *stage_x = 700.0f - (float)(slot % 6u) * 256.0f;
    *stage_y = 946.0f - (float)(slot / 6u) * 256.0f;
    return 1;
}

int t123_bg36_project_tile_quad(uint32_t slot, const T123StageCamera *camera,
                                T123StageQuad *out) {
    if (!camera || !out || slot >= 30u || !isfinite(camera->x) ||
        !isfinite(camera->y) || !isfinite(camera->zoom) || camera->zoom < 0.5f)
        return 0;
    float anchor_x, anchor_y;
    T123StageMatrixTranslation translation;
    if (!t123_bg36_tile_anchor(slot, &anchor_x, &anchor_y) ||
        !t123_stage_viewport_translation(camera->zoom, camera->x, camera->y,
                                         0.0f, 0.0f, 1.0f, 1.0f,
                                         &translation)) return 0;
    static const float corner_x[4] = {0.0f, 256.0f, 0.0f, 256.0f};
    static const float corner_y[4] = {0.0f, 0.0f, 256.0f, 256.0f};
    for (unsigned i = 0; i < 4; ++i) {
        out->x[i] = (corner_x[i] - anchor_x + translation.x) * camera->zoom;
        out->y[i] = (corner_y[i] - anchor_y + translation.y) * camera->zoom;
    }
    return 1;
}

int t123_bg36_project_aux_quad(uint32_t aux_slot, float width, float height,
                               float stage_x, float stage_y, float zoom,
                               float camera_x, float camera_y,
                               float viewport_x, float viewport_y,
                               float factor_x, float factor_y,
                               T123StageQuad *out) {
    if (!out || aux_slot >= 4u || width < 0.0f ||
        height < 0.0f || zoom <= 0.0f) return 0;
    T123StageMatrixTranslation translation;
    if (!t123_stage_viewport_translation(zoom, camera_x, camera_y,
                                         viewport_x, viewport_y,
                                         factor_x, factor_y, &translation)) return 0;
    float pivot_x = (aux_slot == 0u || aux_slot == 1u || aux_slot == 3u) ? width * 0.5f : 0.0f;
    float pivot_y = (aux_slot == 0u || aux_slot == 1u || aux_slot == 3u) ? height : 0.0f;
    static const float corner_x[4] = {0.0f, 1.0f, 0.0f, 1.0f};
    static const float corner_y[4] = {0.0f, 0.0f, 1.0f, 1.0f};
    for (unsigned i = 0; i < 4; ++i) {
        float local_x = corner_x[i] * width - pivot_x + stage_x;
        float local_y = corner_y[i] * height - pivot_y + stage_y;
        out->x[i] = (local_x + translation.x) * zoom;
        out->y[i] = (local_y + translation.y) * zoom;
    }
    return 1;
}

int t123_bg36_project_cloud_quad(uint32_t aux_slot, float width, float height,
                                 float stage_x, float stage_y, float zoom,
                                 float camera_x, float camera_y,
                                 float viewport_x, float viewport_y,
                                 float factor_x, float factor_y,
                                 T123StageQuad *out) {
    if (aux_slot != 2u && aux_slot != 3u) return 0;
    return t123_bg36_project_aux_quad(aux_slot, width, height, stage_x, stage_y,
                                      zoom, camera_x, camera_y, viewport_x,
                                      viewport_y, factor_x, factor_y, out);
}

void t123_bg37_scroll_init(T123Bg37Scroll *scroll) {
    if (!scroll) return;
    scroll->counter = 0;
    scroll->tori1_x = -400.0f;
    scroll->clowd_l_x = -300.0f;
}

void t123_bg37_scroll_update(T123Bg37Scroll *scroll) {
    if (!scroll) return;
    scroll->counter += 1u;
    scroll->tori1_x -= 1.5f;
    if (scroll->tori1_x < -1200.0f) scroll->tori1_x = 800.0f;
    scroll->clowd_l_x -= 1.0f;
    if (scroll->clowd_l_x < -800.0f) scroll->clowd_l_x = 800.0f;
}

void t123_bg38_scroll_init(T123Bg38Scroll *scroll) {
    if (!scroll) return;
    scroll->clowd_l_x = -400.0f;
    scroll->clowd_s_x = -300.0f;
}

void t123_bg38_scroll_update(T123Bg38Scroll *scroll) {
    if (!scroll) return;
    scroll->clowd_l_x -= 1.5f;
    if (scroll->clowd_l_x < -1200.0f) scroll->clowd_l_x = 800.0f;
    scroll->clowd_s_x -= 1.0f;
    if (scroll->clowd_s_x < -800.0f) scroll->clowd_s_x = 800.0f;
}

void t123_stage_animation_update(uint32_t stage_id, uint32_t *counter) {
    if (!counter || stage_id == 14u) return;
    if (stage_id == 33u) {
        *counter = (*counter + 1u) & 0x3ffu;
        return;
    }
    *counter += 1u;
    if (stage_id == 10u || stage_id == 11u) *counter += 3u;
    if (stage_id == 13u) *counter += 10u;
}

void t123_bg12_render_time_args(uint32_t counter, uint32_t *first, uint32_t *second) {
    if (first) *first = 2u * counter;
    if (second) *second = 2u * (counter + 45u);
}

void t123_bg12_torii_base_translation(float *x, float *y) {
    if (x) *x = 492.0f;
    if (y) *y = -401.0f;
}

uint32_t t123_bg02_frame(uint32_t counter) {
    return (counter / 3u) % 16u;
}

uint32_t t123_bg02_sprite_index(uint32_t counter, uint32_t segment) {
    if (segment >= 3u) return UINT32_MAX;
    return t123_bg02_frame(counter) * 3u + segment;
}

int t123_bg02_sprite_offset(uint32_t segment, float *x, float *y) {
    static const float offsets[3][2] = {
        {-332.0f, -472.0f},
        {0.0f, 0.0f},
        {312.0f, -472.0f},
    };
    if (segment >= 3u) return 0;
    if (x) *x = offsets[segment][0];
    if (y) *y = offsets[segment][1];
    return 1;
}

int t123_bg33_render_slot(uint32_t counter, uint32_t slot, T123Bg33RenderSlot *out) {
    if (!out || slot >= 30u) return 0;
    counter &= 0x3ffu;
    uint32_t phase = counter >> 8;
    uint32_t requested = slot + phase * 6u;
    uint32_t index = requested % 24u;
    int32_t scroll_y = -(int32_t)counter + (requested >= 24u ? 1024 : 0);
    out->sprite_index = index;
    out->x = 0;
    out->y = scroll_y;
    return 1;
}

int t123_stage_viewport_translation(float zoom, float camera_x, float camera_y,
                                    float viewport_x, float viewport_y,
                                    float factor_x, float factor_y,
                                    T123StageMatrixTranslation *out) {
    if (!out || zoom == 0.0f) return 0;
    out->x = 320.0f / zoom + (640.0f - (viewport_x + camera_x)) * factor_x;
    out->y = 420.0f / zoom - (viewport_y + camera_y) * factor_y;
    return 1;
}

int t123_bg33_project_slot_quad(const T123Bg33RenderSlot *slot,
                                float stage_x, float stage_y, float zoom,
                                float camera_x, float camera_y,
                                float viewport_x, float viewport_y,
                                float factor_x, float factor_y,
                                T123StageQuad *out) {
    if (!slot || !out || slot->sprite_index >= 24u || zoom == 0.0f) return 0;
    T123StageMatrixTranslation translation;
    if (!t123_stage_viewport_translation(zoom, camera_x, camera_y,
                                         viewport_x, viewport_y,
                                         factor_x, factor_y, &translation)) return 0;
    float anchor_x = 700.0f - (float)(slot->sprite_index % 6u) * 256.0f;
    float anchor_y = 860.0f - (float)(slot->sprite_index / 6u) * 256.0f;
    static const float corner_x[4] = {0.0f, 256.0f, 0.0f, 256.0f};
    static const float corner_y[4] = {0.0f, 0.0f, 256.0f, 256.0f};
    for (unsigned i = 0; i < 4; ++i) {
        float local_x = corner_x[i] - anchor_x + stage_x + (float)slot->x;
        float local_y = corner_y[i] - anchor_y + stage_y + (float)slot->y;
        out->x[i] = (local_x + translation.x) * zoom;
        out->y[i] = (local_y + translation.y) * zoom;
    }
    return 1;
}
