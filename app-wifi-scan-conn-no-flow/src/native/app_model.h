/*
 * app_model.h — WiFi 扫描契约头（app-wifi-scan-flow）
 *
 * 职责分界：
 *   UI（EEZ 生成码）只认对象名 + 动作名，不持有变量；
 *   wifi_ui_sync.cpp 每帧经本契约读状态、直写 LVGL 对象；
 *   native_actions.cpp 的 action_* 只投递命令；
 *   platform/io_*.cpp 只认 io_* 端口函数。
 *
 * 数据通道：
 *   A 动作（一次性命令）  -> APP_OUT_*，动作函数体只投递
 *   C 输入（状态回显）    -> APP_IN_*，io_sample_inputs 发布（扫描态/文案）
 *   扫描结果列表          -> io 接口 wifi_ap_at()/wifi_ap_count()/wifi_ap_gen()
 *                            native 直接读，数组变量不进 EEZ
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
    APP_IN_SCAN_STATUS,      /* string: 标题下状态文案 */
    APP_IN_COUNT
} app_input_id_t;

typedef enum {
    APP_OUT_WIFI_SCAN = 0,   /* v=1 发起一次扫描 */
    APP_OUT_WIFI_CONNECT,    /* 半页点「连接」（密码由 UI 层读 pwd_ta）*/
    APP_OUT_PWD_CANCEL,      /* 关闭半页 */
    APP_OUT_DLG_FORGET,      /* 忘记已保存网络 */
    APP_OUT_DLG_CANCEL,      /* 关闭对话框 */
    APP_OUT_COUNT
} app_output_id_t;

typedef union {
    int32_t i;
    bool b;
} app_value_t;

/* ---- inputs ---- */
void app_set_input_i(app_input_id_t id, int32_t v);
void app_set_input_s(app_input_id_t id, const char *v);
int32_t     app_get_input_i(app_input_id_t id);
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
