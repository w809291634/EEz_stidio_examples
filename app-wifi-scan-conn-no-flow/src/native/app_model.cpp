/*
 * app_model.cpp — 共享状态 + 输出命令环（平台无关，不碰 LVGL / 驱动）。
 * 存储规则：每个输入 id 一个独立槽；get/set 落在同一块内存。
 */
#include "app_model.h"
#include "platform/io_iface.h"
#include "wifi_ui_sync.h"
#include <stdio.h>
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
    if (next == g_out_tail) return;   /* 队列满：丢弃 */
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

/* ---- lifecycle ---- */
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
        case APP_OUT_WIFI_SCAN: io_wifi_scan(v.i); break;
        /* ⑦-1 只做导航闭环：关闭类命令在这里落地；
         * 需要后端的（真连/真忘记）仍留 TODO，但要先让界面退得出去。 */
        case APP_OUT_WIFI_CONNECT:            /* TODO(⑦-4): io_wifi_connect(ssid, pwd) */
            printf("[CMD] wifi_connect（后端未接，⑦-4）\n");
            break;
        case APP_OUT_PWD_CANCEL: wifi_ui_close_sheet(); break;
        case APP_OUT_DLG_FORGET:                      /* TODO(⑦-4): io_wifi_forget(ssid) */
            printf("[CMD] dlg_forget（后端未接，⑦-4）\n");
            wifi_ui_close_dialog();
            break;
        case APP_OUT_DLG_CANCEL: wifi_ui_close_dialog(); break;
        default: break;
        }
    }
    io_sample_inputs();

    /* 10 个固定槽渲染同步（代数或状态变化时重建） */
    wifi_ui_sync();
}
