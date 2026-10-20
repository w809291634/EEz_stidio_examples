/*
 * app_model.cpp — 共享状态 + 输出命令环（平台无关：不碰 LVGL、不碰驱动）。
 * 存储规则照抄 KB reference/10 §4：每个输入 id 一个独立槽（int 数组 + 每 id
 * 定长字符串缓冲），禁止 id-offset 算偏移；get 与 set 落在同一块内存。
 */
#include "app_model.h"
#include "platform/io_iface.h"
#include "wifi_ui_sync.h"
#include <string.h>

static int32_t g_in_i[APP_IN_COUNT];
static char    g_in_str[APP_IN_COUNT][APP_IN_STR_MAX];

#define OUT_Q 16
static struct { app_output_id_t id; int32_t v; } g_out_q[OUT_Q];
static int g_out_head = 0, g_out_tail = 0;
static int32_t g_out_last[APP_OUT_COUNT];

/* ---- inputs ---- */
void app_set_input_i(app_input_id_t id, int32_t v)
{
    if ((int)id >= 0 && id < APP_IN_COUNT) g_in_i[id] = v;
}
void app_set_input_b(app_input_id_t id, bool v)
{
    if ((int)id >= 0 && id < APP_IN_COUNT) g_in_i[id] = v ? 1 : 0;
}
void app_set_input_s(app_input_id_t id, const char *v)
{
    if ((int)id < 0 || id >= APP_IN_COUNT) return;
    strncpy(g_in_str[id], v ? v : "", APP_IN_STR_MAX - 1);
    g_in_str[id][APP_IN_STR_MAX - 1] = '\0';
}
int32_t app_get_input_i(app_input_id_t id)
{
    return ((int)id >= 0 && id < APP_IN_COUNT) ? g_in_i[id] : 0;
}
bool app_get_input_b(app_input_id_t id)
{
    return ((int)id >= 0 && id < APP_IN_COUNT) ? (g_in_i[id] != 0) : false;
}
const char *app_get_input_s(app_input_id_t id)
{
    return ((int)id >= 0 && id < APP_IN_COUNT) ? g_in_str[id] : "";
}

/* ---- outputs ---- */
void app_set_output(app_output_id_t id, app_value_t v)
{
    if ((int)id >= APP_OUT_COUNT) return;
    g_out_last[id] = v.i;
    int next = (g_out_head + 1) % OUT_Q;
    if (next == g_out_tail) return;   /* queue full: drop */
    g_out_q[g_out_head].id = id;
    g_out_q[g_out_head].v  = v.i;
    g_out_head = next;
}
bool app_pop_output(app_output_id_t *id, app_value_t *v)
{
    if (g_out_tail == g_out_head) return false;
    *id = g_out_q[g_out_tail].id;
    v->i = g_out_q[g_out_tail].v;
    g_out_tail = (g_out_tail + 1) % OUT_Q;
    return true;
}

/* ---- lifecycle（main.c 每循环调用；排空命令环 → io_*，再采样外部状态）----
 * 顺序照抄 lvgl_demo_ai：先排空 UI 命令（本拍动作同拍生效），再 io_sample_inputs
 * （硬件最新状态同帧发布，UI 不晚一帧）。动作函数体只投递，业务全在 io 层。 */
void user_io_init(void)
{
    io_init();
}

void user_io_tick(void)
{
    app_output_id_t id;
    app_value_t v;
    while (app_pop_output(&id, &v)) {
        switch (id) {
        case APP_OUT_WIFI_SCAN:        io_wifi_scan(v.i); break;
        case APP_OUT_WIFI_JOIN:        io_wifi_join(v.i); break;
        case APP_OUT_PWD_CANCEL:       io_pwd_cancel(v.i); break;
        case APP_OUT_REMEMBER_TOGGLE:  io_remember_toggle(v.i); break;
        default: break;
        }
    }
    io_sample_inputs();

    /* 动态列表渲染同步（代数变化或首建时重建行） */
    wifi_ui_sync();
}
