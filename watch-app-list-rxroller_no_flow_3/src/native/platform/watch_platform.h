/*
 * PC/真机唯一平台接口。app 只能包含本头文件，不能感知当前运行环境。
 * PC 构建默认使用 platform/pc/；真机构建定义 WATCH_PLATFORM_DEVICE，改用 device/。
 */
#ifndef WATCH_PLATFORM_H
#define WATCH_PLATFORM_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 以下函数只发出设备命令；业务状态和 UI 回显由 app/ 管理。 */
void watch_platform_set_brightness(int percent, bool automatic); /* 背光 PWM/自动策略 */
void watch_platform_set_sound(int percent, bool cue, bool vibration); /* 功放/提示音/马达 */
void watch_platform_media_command(int command); /* 0=上一首，1=播放/暂停，2=下一首 */
void watch_platform_start_spo2(void); /* 启动传感器一次测量 */
void watch_platform_find_phone(bool ringing); /* 向手机发送响铃/停止请求 */
void watch_platform_ble_disconnect(void); /* 断开当前手机链路 */
void watch_platform_check_update(void); /* 请求手机/网络检查更新 */

/* PC 返回宿主本地时钟；真机改为 RTC / 手机同步时间。 */
bool watch_platform_get_local_time(int *year, int *month, int *day, int *hour, int *minute);

#ifdef __cplusplus
}
#endif

#endif /* WATCH_PLATFORM_H */
