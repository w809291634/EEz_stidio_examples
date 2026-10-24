/*
 * PC 平台实现：宿主时间 + 可观测日志。
 * PC 构建不定义 WATCH_PLATFORM_DEVICE；device 构建定义它后，本文件不产生任何接口符号。
 */
#if !defined(WATCH_PLATFORM_DEVICE)

#include <stdio.h>
#include <time.h>

#include "platform/watch_platform.h"

/* ===== 1. 模拟设备命令 =====
 * 业务状态始终在 app/watch_model，PC 端只记录已发出的外设命令。 */
void watch_platform_set_brightness(int percent, bool automatic)
{
    printf("[PLATFORM-PC] brightness=%d auto=%d\n", percent, (int)automatic);
}

void watch_platform_set_sound(int percent, bool cue, bool vibration)
{
    printf("[PLATFORM-PC] sound=%d cue=%d vibration=%d\n", percent, (int)cue, (int)vibration);
}

void watch_platform_media_command(int command)
{
    printf("[PLATFORM-PC] media command=%d\n", command);
}

void watch_platform_start_spo2(void) { printf("[PLATFORM-PC] spo2 start\n"); }
void watch_platform_find_phone(bool ringing) { printf("[PLATFORM-PC] find-phone ringing=%d\n", (int)ringing); }
void watch_platform_ble_disconnect(void) { printf("[PLATFORM-PC] BLE disconnect\n"); }
void watch_platform_check_update(void) { printf("[PLATFORM-PC] update check\n"); }

/* ===== 2. 宿主时间快照 ===== */
bool watch_platform_get_local_time(int *year, int *month, int *day, int *hour, int *minute)
{
    time_t now = time(NULL);
    struct tm *local = localtime(&now);

    if (!local || !year || !month || !day || !hour || !minute) return false;
    *year = local->tm_year + 1900;
    *month = local->tm_mon + 1;
    *day = local->tm_mday;
    *hour = local->tm_hour;
    *minute = local->tm_min;
    return true;
}

#endif /* !WATCH_PLATFORM_DEVICE */
