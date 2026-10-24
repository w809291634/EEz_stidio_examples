/*
 * wifi_model.cpp — 输入槽 + 输出命令环的存储实现（平台无关，不碰 LVGL/驱动）
 */
#include "wifi_model.h"
#include <string.h>

/******************** 模块私有状态与常量 ********************/

static int32_t g_in_i[APP_IN_COUNT];
static char    g_in_str[APP_IN_COUNT][APP_IN_STR_MAX];

#define OUT_Q 16
static struct { app_output_id_t id; int32_t v; } g_out_q[OUT_Q];
static int g_out_head = 0, g_out_tail = 0;

/******************** 对外读写接口 ********************/

// 函数作用：写入整型输入槽（越界静默丢弃）。 参数：id：输入编号；v：值。 返回值：无。
void app_set_input_i(app_input_id_t id, int32_t v)
{
    if ((int)id >= 0 && id < APP_IN_COUNT) g_in_i[id] = v;
}

// 函数作用：写入字符串输入槽，定长拷贝并补尾零。 参数：id：输入编号；v：文本。 返回值：无。
void app_set_input_s(app_input_id_t id, const char *v)
{
    if ((int)id < 0 || id >= APP_IN_COUNT) return;
    strncpy(g_in_str[id], v ? v : "", APP_IN_STR_MAX - 1);
    g_in_str[id][APP_IN_STR_MAX - 1] = '\0';
}

// 函数作用：读取整型输入槽。 参数：id：输入编号。 返回值：槽值；越界返回 0。
int32_t app_get_input_i(app_input_id_t id)
{
    return ((int)id >= 0 && id < APP_IN_COUNT) ? g_in_i[id] : 0;
}

// 函数作用：读取字符串输入槽。 参数：id：输入编号。 返回值：槽内文本；越界返回空串。
const char *app_get_input_s(app_input_id_t id)
{
    return ((int)id >= 0 && id < APP_IN_COUNT) ? g_in_str[id] : "";
}

// 函数作用：把一次性命令压进输出环。 参数：id：命令编号；v：携带值。 返回值：无。
void app_set_output(app_output_id_t id, app_value_t v)
{
    if ((int)id >= APP_OUT_COUNT) return;
    int next = (g_out_head + 1) % OUT_Q;
    if (next == g_out_tail) return;   /* 队列满：丢弃（命令都是幂等触发，丢一次可重试） */
    g_out_q[g_out_head].id = id;
    g_out_q[g_out_head].v  = v.i;
    g_out_head = next;
}

// 函数作用：弹出一条待处理命令。 参数：id/v：输出参数。 返回值：true 有命令；false 环空。
bool app_pop_output(app_output_id_t *id, app_value_t *v)
{
    if (g_out_tail == g_out_head) return false;
    *id = g_out_q[g_out_tail].id;
    v->i = g_out_q[g_out_tail].v;
    g_out_tail = (g_out_tail + 1) % OUT_Q;
    return true;
}
