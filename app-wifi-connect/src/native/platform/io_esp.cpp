/*
 * io_esp.cpp — ESP32 真机实现（TODO 骨架）。
 * PC_SIM 的 CMake 把本文件排除在构建外（NATIVE_SOURCES 过滤 io_esp），
 * 真机侧与 PC 共用 app_model/native_vars/native_actions/UI。
 *
 * 落地清单（照 io_pc.cpp 的语义一一对应）：
 *   io_init          → nvs_flash_init + esp_netif + esp_wifi_init
 *   io_wifi_scan     → esp_wifi_scan_start；WIFI_EVENT_SCAN_DONE 里
 *                      遍历结果 app_set_input_s(APP_IN_WIFI_SLOTn_SSID...)，
 *                      全部填完后 scan_state=2
 *   io_wifi_join     → 密码取 APP_IN_PWD（UI 键盘输入，连接动作已捕获），
 *                      esp_wifi_sta_config + esp_wifi_connect；
 *                      WIFI_EVENT_STA_DISCONNECTED → wifi_state=4 失败（可扩展）
 *   已保存网络       → NVS 读写（g_remember=true 时存 SSID/密码）
 */
#include "../app_model.h"
#include "io_iface.h"
#include <stdio.h>

void io_init(void)                 { printf("[IO:ESP] TODO\n"); }
void io_sample_inputs(void)        { }
void io_wifi_scan(int v)           { (void)v; }
void io_wifi_join(int v)           { (void)v; }
void io_pwd_cancel(int v)          { (void)v; }
void io_remember_toggle(int v)     { (void)v; }
