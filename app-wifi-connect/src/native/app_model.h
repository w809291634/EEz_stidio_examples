/*
 * app_model.h — 契约头（迷你版 lvgl_demo_ai/eez-test 同款架构，10 号文档落地）。
 *
 * 职责分界：
 *   - UI 侧（EEZ 生成码）只认「变量名 + 动作名」：native_vars.cpp 里 get_var_xxx
 *     与 set_var_xxx 读写本契约，native_actions.cpp 里 action_xxx 只投递命令。
 *   - 硬件侧（platform/io_pc.cpp 等）只认 io_xxx 端口函数：io_sample_inputs() 发布状态，
 *     io_wifi_xxx() 执行命令。
 *   - 本文件是唯一被两侧同时 include 的头（单边缺实现 = 链接失败，免费架构检查）。
 *
 * 三条通道（KB reference/10 §3）：
 *   A 动作（一次性命令）  → APP_OUT_*，动作函数体只投递
 *   C 输入变量（状态回显）→ APP_IN_*，io_sample_inputs 发布，UI 表达式绑定
 *   动态长度列表          → 不走变量桥：io 层维护链表（wifi_ap），
 *                            wifi_ui_sync.cpp 渲染进 EEZ 的空容器 list_box
 */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define APP_IN_STR_MAX 33   /* SSID 最长 32 + '\0' */

typedef enum {
    APP_IN_SCAN_STATE = 0,   /* int: 0 未扫描 1 扫描中 2 扫描完成           */
    APP_IN_AP_COUNT,         /* int: 扫描到的网络数                          */
    APP_IN_WIFI_STATE,       /* int: 0 未连 1 连接中 2 已连接               */
    APP_IN_CONN_SSID,        /* string: 已连接 SSID（未连接 ""）             */
    APP_IN_PICK_SSID,        /* string: 当前选中行 SSID（"" = 无选中）       */
    APP_IN_REMEMBER,         /* bool: 记住密码                               */
    APP_IN_PWD,              /* string: 连接动作捕获的密码（io 连接时取用）  */
    APP_IN_COUNT
} app_input_id_t;

typedef enum {
    APP_OUT_WIFI_SCAN = 0,   /* v=1 发起一次扫描（刷新按钮）    */
    APP_OUT_WIFI_JOIN,       /* v=1 连接当前选中网络（连接按钮）*/
    APP_OUT_PWD_CANCEL,      /* v=1 取消密码面板                */
    APP_OUT_REMEMBER_TOGGLE, /* v=1 翻转记住密码                */
    APP_OUT_COUNT
} app_output_id_t;

typedef union { int32_t i; bool b; } app_value_t;

/* ---- inputs（io 层 / 动作层发布，native_vars 的 get_* 读取）---- */
void app_set_input_i(app_input_id_t id, int32_t v);
void app_set_input_b(app_input_id_t id, bool v);
void app_set_input_s(app_input_id_t id, const char *v);
int32_t     app_get_input_i(app_input_id_t id);
bool        app_get_input_b(app_input_id_t id);
const char *app_get_input_s(app_input_id_t id);

/* ---- outputs（UI 动作投递，user_io_tick 排空后转 io_*）---- */
void app_set_output(app_output_id_t id, app_value_t v);
bool app_pop_output(app_output_id_t *id, app_value_t *v);

/* ---- lifecycle（main.c 每循环调用；PC/真机共用）---- */
void user_io_init(void);
void user_io_tick(void);

#ifdef __cplusplus
}
#endif
