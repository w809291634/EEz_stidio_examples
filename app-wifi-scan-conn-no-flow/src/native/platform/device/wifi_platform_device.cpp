/*
 * wifi_platform_device.cpp — 真机（嵌入式）后端接入点
 *
 * 编译选择（kit reference/12）：PC 构建**不**定义 WIFI_PLATFORM_DEVICE，本文件整体
 * 编译为空；真机构建定义该宏后，pc/ 那份实现不再提供符号，由这里补齐同名接口。
 * 这样 app/ 只 include platform/wifi_platform.h，既没有 #ifdef 分支也不会重复定义。
 *
 * 参考实现：platform/pc/wifi_platform_win.cpp 已经把 Windows 宿主侧的真接口跑通
 * （WlanScan / WlanGetAvailableNetworkList / WlanConnect / WlanDeleteProfile），
 * 端口到嵌入式栈时照它的**时序与状态口径**抄，别照注释里的名字猜：
 *   io_init          → 打开无线客户端 + 选接口；失败要有可读文案
 *   io_wifi_scan     → 发起扫描 + 置扫描态
 *   io_sample_inputs → 到点拉结果 → 排序 → 发布（扫描态最后才置 2）
 *   io_wifi_connect  → 有密码先写凭据再连；连上/失败都由回查真值定结论
 *   io_wifi_forget   → 删已存凭据；不断已建立的连接
 */
#ifdef WIFI_PLATFORM_DEVICE

#include <stdio.h>
#include "app/wifi_model.h"
#include "app/wifi_text.h"
#include "platform/wifi_platform.h"

/******************** 模块私有状态与常量 ********************/

#define AP_MAX 16

static wifi_ap_t s_aps[AP_MAX];
static int s_cnt = 0;
static int s_gen = 0;

/******************** 对外初始化与公开接口 ********************/

// 函数作用：初始化宿主无线客户端。 参数：无。 返回值：无。
void io_init(void)
{
    /* TODO(⑦-2): WlanOpenClient + WlanEnumInterfaces，失败时把文案置成"无线不可用" */
    app_set_input_i(APP_IN_SCAN_STATE, 0);
    app_set_input_s(APP_IN_SCAN_STATUS, WIFI_TXT_SCAN_HINT);
    printf("[IO] io_init (device, 未实现)\n");
}

// 函数作用：发起一次扫描。 参数：v：1 才生效。 返回值：无。
void io_wifi_scan(int v)
{
    (void)v;
    /* TODO(⑦-2): WlanScan()；置 APP_IN_SCAN_STATE=1 与WIFI_TXT_SCANNING */
    printf("[IO] io_wifi_scan 未实现（⑦-2）\n");
}

// 函数作用：连接指定网络。 参数：ssid / password。 返回值：无。
void io_wifi_connect(const char *ssid, const char *password)
{
    (void)ssid; (void)password;
    /* TODO(⑦-2): WlanConnect()；有密码时先 WlanSetProfile()
     * ★ 必须按 platform/wifi_platform.h 的口径报进度：这里立即置
     *   APP_IN_CONN_STATE=1 +「正在连接 X…」，之后在 io_sample_inputs 里
     *   回查真值置 2/3。置不了 2，app/wifi_logic 就永远不关半页。 */
    printf("[IO] io_wifi_connect 未实现（⑦-2）\n");
}

// 函数作用：忘记指定网络。 参数：ssid。 返回值：无。
void io_wifi_forget(const char *ssid)
{
    (void)ssid;
    /* TODO(⑦-2): WlanDeleteProfile()；成功后 saved 置假、代数 +1 */
    printf("[IO] io_wifi_forget 未实现（⑦-2）\n");
}

// 函数作用：断开指定网络。 参数：ssid。 返回值：无。
void io_wifi_disconnect(const char *ssid)
{
    (void)ssid;
    /* TODO(⑦-2): 断开当前连接；注意整口断开不认 SSID，先比对当前 SSID */
}

// 函数作用：拉取扫描结果并回写 model。 参数：无。 返回值：无。
void io_sample_inputs(void)
{
    /* TODO(⑦-2): WlanGetNetworkBssList() → 排序 → 发布 + APP_IN_SCAN_STATE=2 */
}

// 函数作用：取第 index 条结果。 参数：index：下标。 返回值：只读指针；越界 NULL。
const wifi_ap_t *wifi_ap_at(int index)
{
    if (index < 0 || index >= s_cnt) return NULL;
    return &s_aps[index];
}

// 函数作用：结果总数。 参数：无。 返回值：条数。
int wifi_ap_count(void) { return s_cnt; }

// 函数作用：结果代数。 参数：无。 返回值：代数。
int wifi_ap_gen(void)   { return s_gen; }

#endif /* WIFI_PLATFORM_DEVICE */
