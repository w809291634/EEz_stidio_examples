/* boot_anim.c — 开机动画（MP4 离线转帧后的顺序播放）
 *
 * 帧由 design/boot_from_mp4.py 从 MP4 转出，路径模板见 boot_frames.h。
 * 播放层挂在 lv_layer_top()，不干扰页面；播完自动删除，主界面自然露出。
 * 每帧切换后丢弃上一帧的解码缓存，避免 36 帧把内存吃满。
 * 设备端只要文件系统就绪（A: 下存在同样路径）即可复用同一模块。
 */
#include "boot_anim.h"

#include <stdio.h>

#include "lvgl.h"
#include "boot_frames.h"

static lv_obj_t *s_root;
static lv_obj_t *s_img;
static lv_timer_t *s_timer;
static int s_idx;
static int s_played;
static char s_prev[80];

static void close_boot(void)
{
    if (s_timer) {
        lv_timer_delete(s_timer);
        s_timer = NULL;
    }
    if (s_root) {
        lv_obj_delete(s_root);
        s_root = NULL;
        s_img = NULL;
    }
}

static void tick_cb(lv_timer_t *t)
{
    char path[80];
    LV_UNUSED(t);
    if (!s_img || s_idx >= BOOT_FRAME_COUNT) {
        close_boot();
        return;
    }
    snprintf(path, sizeof(path), BOOT_FRAME_FMT, s_idx);
    lv_image_set_src(s_img, path);
    if (s_prev[0]) lv_image_cache_drop(s_prev);
    snprintf(s_prev, sizeof(s_prev), "%s", path);
    s_idx++;
    s_played++;
}

static bool first_frame_ok(void)
{
    lv_fs_file_t f;
    char path[80];
    snprintf(path, sizeof(path), BOOT_FRAME_FMT, 0);
    if (lv_fs_open(&f, path, LV_FS_MODE_RD) != LV_FS_RES_OK)
        return false;
    lv_fs_close(&f);
    return true;
}

void boot_anim_play(void)
{
    char path[80];
    if (s_root) return;
    if (BOOT_FRAME_COUNT <= 0 || !first_frame_ok()) return;

    s_root = lv_obj_create(lv_layer_top());
    lv_obj_remove_style_all(s_root);
    lv_obj_set_size(s_root, lv_pct(100), lv_pct(100));
    lv_obj_set_style_bg_color(s_root, lv_color_hex(0x05080F), 0);
    lv_obj_set_style_bg_opa(s_root, LV_OPA_COVER, 0);
    lv_obj_clear_flag(s_root, LV_OBJ_FLAG_SCROLLABLE);

    s_img = lv_image_create(s_root);
    lv_obj_center(s_img);

    s_idx = 0;
    s_played = 0;
    s_prev[0] = '\0';
    snprintf(path, sizeof(path), BOOT_FRAME_FMT, 0);
    lv_image_set_src(s_img, path);
    snprintf(s_prev, sizeof(s_prev), "%s", path);
    s_idx = 1;
    s_played = 1;
    s_timer = lv_timer_create(tick_cb, BOOT_FRAME_MS, NULL);
}

bool boot_anim_active(void)
{
    return s_root != NULL;
}

int boot_anim_frames_played(void)
{
    return s_played;
}
