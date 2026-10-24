/*
 * wifi_model.h — WiFi 扫描/连接的业务真值（app 层，无 LVGL、无平台依赖）
 *
 * 职责分界（kit reference/12 轻量分层）：
 *   wifi_events  只投递命令（APP_OUT_*）；
 *   wifi_logic   每拍排空命令环，分发给 platform / navigation；
 *   wifi_view    读本层输入槽 + 平台快照，写 objects.*；
 *   platform     只认 io_* 端口函数，不引用 EEZ 对象。
 *
 * 数据通道：
 *   A 动作（一次性命令）-> APP_OUT_*，动作函数体只投递；
 *   C 输入（状态回显）  -> APP_IN_*，由 platform 侧发布；
 *   扫描结果列表        -> 平台接口 wifi_ap_at()/count()/gen()，数组不进 EEZ。
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

#ifdef __cplusplus
}
#endif
