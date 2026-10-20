/*
 * io_iface.h — 唯一提及"硬件"的薄接口（lvgl_demo_ai 同款）。
 * 两份实现：io_pc.cpp（假数据+打印命令）/ io_esp.cpp（真机 esp_wifi+NV，TODO）。
 * 构建各取一份：PC_SIM 的 CMake 自动排除 io_esp（NATIVE_SOURCES 过滤器）。
 *
 * ★ 动态列表（链表）归 io 层所有：扫描结果以链表表达（用户需求），
 *   io_wifi_scan 后填充；UI 渲染由 wifi_ui_sync.cpp 读取遍历入口完成。
 */
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

/* 扫描结果节点（链表）—— io 层所有，UI 同步只读 */
typedef struct wifi_ap {
    char ssid[33];
    int  rssi;
    bool lock;        /* true = 需要密码 */
    bool connected;   /* 当前已连接此网络 */
    int  auth;        /* DOT11 认证算法（io_win 用：1=open 7=WPA2PSK 8=WPA3SAE）*/
    struct wifi_ap *next;
} wifi_ap_t;

void io_init(void);                 /* 一次性初始化（真机：NV/WIFI 外设）      */
void io_sample_inputs(void);        /* 采样外部世界 → app_set_input_*()        */
void io_wifi_scan(int v);           /* v=1 发起一次扫描                        */
void io_wifi_join(int v);           /* v=1 连接 APP_IN_PICK_SSID（密码在 APP_IN_PWD）*/
void io_pwd_cancel(int v);          /* v=1 取消（只收面板，状态不变）          */
void io_remember_toggle(int v);     /* v=1 翻转记住密码                        */

/* 链表遍历入口（wifi_ui_sync 渲染用） */
const wifi_ap_t *wifi_ap_first(void);
int               wifi_ap_count(void);
int               wifi_ap_gen(void);  /* 链表代数：内容变化 +1，UI 据此重建 */

#ifdef __cplusplus
}
#endif
