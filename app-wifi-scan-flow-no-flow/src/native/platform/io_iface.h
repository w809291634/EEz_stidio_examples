/*
 * io_iface.h — 唯一提及"硬件"的薄接口。
 * 两份实现：io_pc.cpp（假数据）/ io_esp.cpp（真机，TODO）。
 * PC_SIM 的 CMake 自动排除 io_esp.cpp。
 */
#pragma once
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 扫描结果条目（io 层所有，UI 同步只读） */
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

const wifi_ap_t *wifi_ap_at(int index);  /* 已按 RSSI 降序排好 */
int  wifi_ap_count(void);           /* 扫描结果总数 */
int  wifi_ap_gen(void);             /* 代数：内容变化 +1，UI 据此重建 */

#ifdef __cplusplus
}
#endif
