/*
 * wifi_platform.h — 唯一提及"硬件"的窄接口（platform 层契约）
 *
 * 两份实现，编译期二选一：
 *   platform/pc/wifi_platform_pc.cpp        —— 不定义 WIFI_PLATFORM_DEVICE 时生效；
 *   platform/device/wifi_platform_device.cpp —— 真机构建定义该宏后生效。
 * 因此 app/ 永远只 include 本头，不出现 #ifdef PC 分支，也不会重复链接符号。
 *
 * 本层不得引用 LVGL / objects.*：换后端时 app 与 UI 侧一行不改。
 * PC 专属的假数据裁剪（io_fake_*）不放这里，只存在于 pc 实现内，由夹具自行 extern。
 */
#pragma once
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 扫描结果条目（后端所有，app 层只读） */
typedef struct {
    char ssid[33];
    char auth[8];      /* "WPA2" / "WPA3" / "开放网络" */
    int  rssi;         /* dBm，负值 */
    char band[8];      /* "2.4 GHz" / "5 GHz" */
    bool lock;         /* 需要密码 */
    bool saved;        /* 已保存密码 */
    bool connected;    /* 当前已连接 */
} wifi_ap_t;

void io_init(void);                 /* 一次性初始化 */
void io_sample_inputs(void);        /* 采样外部世界 -> app_set_input_*() */
void io_wifi_scan(int v);           /* v=1 发起一次扫描 */

/* 连接 / 忘记：状态变化由后端负责（改完要 +1 代数，UI 才会重画）。
 * password 仅对"有锁且没存过密码"的网络有意义；已保存或开放网络传空串。
 *
 * ★ 连接是异步的，后端必须走 APP_IN_CONN_STATE 报进度（两份实现同口径）：
 *   io_wifi_connect() 里立即置 1（连接中）并把标题写成「正在连接 X…」；
 *   之后在 io_sample_inputs() 里回查真值，成功置 2 +「已连接 X」，
 *   超时/被拒置 3 +「连接失败 X」。半页由 app/wifi_logic 在收到 2 时才关，
 *   所以点完不关窗、看到"正在连接"是设计口径（mockup_06）。 */
void io_wifi_connect(const char *ssid, const char *password);
void io_wifi_forget(const char *ssid);

const wifi_ap_t *wifi_ap_at(int index);  /* 已按「已连接→RSSI→SSID」排好 */
int  wifi_ap_count(void);           /* 扫描结果总数 */
int  wifi_ap_gen(void);             /* 代数：内容变化 +1，UI 据此重建 */

#ifdef __cplusplus
}
#endif
