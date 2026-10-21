/*
 * app_model.h — WiFi 扫描契约头（app-wifi-connect2）
 *
 * 职责分界：
 *   UI（EEZ 生成码）只认变量名 + 动作名；
 *   native_vars.cpp 的 get_var_* 从本契约读状态；
 *   native_actions.cpp 的 action_* 只投递命令；
 *   platform/io_*.cpp 只认 io_* 端口函数。
 *
 * 数据通道（三条）：
 *   A 动作（一次性命令）    -> APP_OUT_*，动作函数体只投递
 *   C 输入变量（状态回显）  -> APP_IN_*，io_sample_inputs 发布
 *   扫描结果列表            -> io 接口 wifi_ap_at()/wifi_ap_count()（native 直接读，
 *                               数组变量已移出 EEZ；标量状态仍走 EEZ native 变量）
 */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define APP_IN_STR_MAX 96

typedef enum {
    APP_IN_SCAN_STATE = 0,   /* int: 0 空闲 1 扫描中 2 完成 */
    APP_IN_AP_GEN,           /* int: aps[] 内容代数（publish +1，UI 据此重建） */
    APP_IN_SCAN_STATUS,      /* string: 标题下状态文案 */
    APP_IN_COUNT
} app_input_id_t;

typedef enum {
    APP_OUT_WIFI_SCAN = 0,   /* v=1 发起一次扫描 */
    APP_OUT_COUNT
} app_output_id_t;

typedef union {
    int32_t i;
    bool b;
} app_value_t;

/* ---- inputs ---- */
void app_set_input_i(app_input_id_t id, int32_t v);
void app_set_input_b(app_input_id_t id, bool v);
void app_set_input_s(app_input_id_t id, const char *v);
int32_t     app_get_input_i(app_input_id_t id);
bool        app_get_input_b(app_input_id_t id);
const char *app_get_input_s(app_input_id_t id);

/* ---- outputs ---- */
void app_set_output(app_output_id_t id, app_value_t v);
bool app_pop_output(app_output_id_t *id, app_value_t *v);

/* ---- lifecycle（main.c 每循环调用）---- */
void user_io_init(void);
void user_io_tick(void);

#ifdef __cplusplus
}
#endif
