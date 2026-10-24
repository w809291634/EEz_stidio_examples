/*
 * wifi_platform_win.h — PC 真接口后端（Windows wlanapi）的内部契约
 *
 * 不是 platform/wifi_platform.h 那份对外契约：app/ 与 UI 侧永远看不到这些符号。
 * 只有 platform/pc/wifi_platform_pc.cpp 在运行时判定该走真接口（默认就是真，
 * 除非设了 WIFI_PC_FAKE=1）才把命令转给这里；门禁与出图必须显式设那个变量
 * 退回假世界，否则跑一次分就真连一次网。
 */
#pragma once
#include "platform/wifi_platform.h"

#ifdef __cplusplus
extern "C" {
#endif

int  win_io_open(void);                 /* 1=可用；0=没有无线接口或服务没起 */
void win_io_close(void);
void win_io_scan(void);                 /* 发起真扫描（WlanScan）并置扫描态 */
void win_io_sample(void);               /* 推进扫描/连接计时，到点就重新查询 */
void win_io_connect(const char *ssid, const char *password);
void win_io_forget(const char *ssid);
void win_io_disconnect(const char *ssid);

const wifi_ap_t *win_io_ap_at(int index);
int  win_io_ap_count(void);
int  win_io_ap_gen(void);

#ifdef __cplusplus
}
#endif
