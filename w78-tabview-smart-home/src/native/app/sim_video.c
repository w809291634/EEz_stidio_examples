/* sim_video.c — PC 仿真：直接播放真实 MP4（ffmpeg 子进程解码 → LVGL canvas）
 *
 * 为什么用子进程：LVGL 的 FFmpeg 集成需要 libav* 开发库，本机未安装；
 * 环境里有 imageio_ffmpeg 自带的 ffmpeg.exe，run_sim.bat 会把路径写进 FFMPEG_EXE。
 * 解码参数固定为 800x480 BGRA 原始帧，直接对应 LV_COLOR_FORMAT_ARGB8888。
 * 这是"真实 MP4 播放"，不是把 MP4 预转成图片序列。
 * ESP32 目标上编译为空实现。
 */
#include "sim_video.h"

#ifdef ESP_PLATFORM

bool sim_video_play_boot(void) { return false; }
bool sim_video_active(void) { return false; }
int sim_video_frames(void) { return 0; }

#else

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <direct.h>
#endif

#include "lvgl.h"

#define VID_W 800
#define VID_H 480
#define VID_FPS 25

static FILE *s_pipe;
static lv_obj_t *s_root;
static lv_obj_t *s_canvas;
static lv_timer_t *s_timer;
static int s_frames;
static uint8_t s_buf[VID_W * VID_H * 4];

static void close_video(void)
{
    if (s_timer) {
        lv_timer_delete(s_timer);
        s_timer = NULL;
    }
    if (s_pipe) {
        _pclose(s_pipe);
        s_pipe = NULL;
    }
    if (s_root) {
        lv_obj_delete(s_root);
        s_root = NULL;
        s_canvas = NULL;
    }
}

static void tick_cb(lv_timer_t *t)
{
    size_t want = sizeof(s_buf), got;
    LV_UNUSED(t);
    if (!s_pipe) {
        close_video();
        return;
    }
    got = fread(s_buf, 1, want, s_pipe);
    if (got < want) {                 /* EOF / 解码结束 */
        close_video();
        return;
    }
    lv_obj_invalidate(s_canvas);
    s_frames++;
}

static const char *ffmpeg_exe(void)
{
    const char *e = getenv("FFMPEG_EXE");
    if (e && *e) return e;
    return "ffmpeg";                  /* PATH 里有也能用 */
}

bool sim_video_play_boot(void)
{
    const char *root = getenv("SIM_TARGET_PROJ_DIR");
    char mp4[600], cmd[1400];
    char cwd[512];
    if (s_root) return true;
    if (!root || !*root) {
        printf("[VIDEO] SIM_TARGET_PROJ_DIR 未设置\n");
        return false;
    }
    snprintf(mp4, sizeof(mp4), "%s/assets/boot.mp4", root);
    {
        FILE *f = fopen(mp4, "rb");
        if (!f) {
            printf("[VIDEO] 找不到 MP4：%s\n", mp4);
            return false;
        }
        fclose(f);
    }
    /* cmd 的引号规则在“带引号 exe + 多参数”时容易把路径拆坏：
     * 这里 exe 路径不含空格就不加引号，并临时切到工程根用相对路径。 */
    if (strchr(ffmpeg_exe(), ' '))
        snprintf(cmd, sizeof(cmd), "\"%s\"", ffmpeg_exe());
    else
        snprintf(cmd, sizeof(cmd), "%s", ffmpeg_exe());
    {
        size_t n = strlen(cmd);
        snprintf(cmd + n, sizeof(cmd) - n,
                 " -v error -i assets\\boot.mp4 -f rawvideo -pix_fmt bgra "
                 "-vf scale=%d:%d -r %d -", VID_W, VID_H, VID_FPS);
    }
    _getcwd(cwd, sizeof(cwd));
    _chdir(root);
    s_pipe = _popen(cmd, "rb");
    _chdir(cwd);
    if (!s_pipe) {
        printf("[VIDEO] 启动 ffmpeg 失败：%s\n", ffmpeg_exe());
        return false;
    }

    s_root = lv_obj_create(lv_layer_top());
    lv_obj_remove_style_all(s_root);
    lv_obj_set_size(s_root, lv_pct(100), lv_pct(100));
    lv_obj_set_style_bg_color(s_root, lv_color_hex(0x05080F), 0);
    lv_obj_set_style_bg_opa(s_root, LV_OPA_COVER, 0);
    lv_obj_clear_flag(s_root, LV_OBJ_FLAG_SCROLLABLE);

    s_canvas = lv_canvas_create(s_root);
    lv_canvas_set_buffer(s_canvas, s_buf, VID_W, VID_H, LV_COLOR_FORMAT_ARGB8888);
    lv_obj_center(s_canvas);

    s_frames = 0;
    s_timer = lv_timer_create(tick_cb, 1000 / VID_FPS, NULL);
    printf("[VIDEO] playing %s @%dfps\n", mp4, VID_FPS);
    return true;
}

bool sim_video_active(void)
{
    return s_root != NULL;
}

int sim_video_frames(void)
{
    return s_frames;
}

#endif /* !ESP_PLATFORM */
