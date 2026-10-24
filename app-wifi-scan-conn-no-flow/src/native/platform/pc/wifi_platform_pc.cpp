/*
 * wifi_platform_pc.cpp — PC 仿真后端：假 WiFi 世界（12 个 AP）+ 2s 扫描状态机。
 *
 * 结果按「已连接置顶 → RSSI 降序 → SSID 升序」排序后发布。
 * 本层不依赖 LVGL，计时用 clock()。
 *
 * 编译选择：本文件整体包在 #ifndef WIFI_PLATFORM_DEVICE 里，与
 * platform/device/wifi_platform_device.cpp 互斥——真机定义该宏后 PC 实现不产生符号。
 */
#ifndef WIFI_PLATFORM_DEVICE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "app/wifi_model.h"
#include "platform/wifi_platform.h"

/******************** 模块私有状态与常量 ********************/

#define AP_MAX 16

static wifi_ap_t s_aps[AP_MAX];
static int  s_cnt = 0;
static int  s_gen = 0;
static int  s_scan_state = 0;      /* 0 空闲 1 扫描中 2 完成 */
static int  s_fake_n = -1;         /* -1 = 用全表；>=0 = 只报前 n 个（⑤ 逐状态出图） */
static clock_t s_t0 = 0;

typedef struct {
    const char *ssid;
    const char *auth;
    int rssi;
    const char *band;
    bool lock;
    bool saved;
    bool connected;
} fake_ap_t;

static const fake_ap_t FAKE[] = {
    { "yjt_dev_2.4G",     "WPA2",     -41, "2.4 GHz", true,  true,  true  },
    { "YJT-1号楼办公",     "WPA2",     -55, "2.4 GHz", true,  true,  false },
    { "1号楼6层WiFi",      "WPA3",     -58, "5 GHz",   true,  false, false },
    { "Office-2G",        "开放网络", -63, "2.4 GHz", false, false, false },
    { "Coffee_Shop",      "WPA2",     -68, "5 GHz",   true,  false, false },
    { "Home_5G",          "WPA3",     -72, "5 GHz",   true,  true,  false },
    { "会议室-客用",       "WPA2",     -76, "2.4 GHz", true,  false, false },
    { "Guest",            "开放网络", -80, "2.4 GHz", false, false, false },
    { "TP-LINK_8A2C",     "WPA2",     -84, "2.4 GHz", true,  false, false },
    { "ChinaNet-5G",      "WPA2",     -87, "5 GHz",   true,  false, false },
    { "IoT_Device",       "WPA2",     -90, "2.4 GHz", true,  false, false },
    { "邻居的WiFi",        "WPA2",     -93, "2.4 GHz", true,  false, false },
};

/******************** 小工具 / 坐标换算 ********************/

// 函数作用：列表排序比较键（已连接→RSSI 降序→SSID 升序）。 参数：a/b：待比元素。 返回值：符号差。
static int cmp_ap(const void *a, const void *b)
{
    const wifi_ap_t *x = (const wifi_ap_t *)a;
    const wifi_ap_t *y = (const wifi_ap_t *)b;

    /* 已连接置顶 */
    if (x->connected != y->connected) return x->connected ? -1 : 1;
    /* RSSI 降序（-40 在 -80 前） */
    if (x->rssi != y->rssi) return y->rssi - x->rssi;
    /* SSID 升序兜底，保证顺序稳定 */
    return strcmp(x->ssid, y->ssid);
}

// 函数作用：把假世界裁剪并发布结果（置文案 + 扫描态=2 + 代数 +1）。 参数：无。 返回值：无。
static void publish(void)
{
    s_cnt = (int)(sizeof(FAKE) / sizeof(FAKE[0]));
    if (s_fake_n >= 0) s_cnt = s_fake_n;      /* ⑤ 逐状态出图的裁剪 */
    if (s_cnt > AP_MAX) s_cnt = AP_MAX;

    for (int i = 0; i < s_cnt; i++) {
        memset(&s_aps[i], 0, sizeof(s_aps[i]));
        strncpy(s_aps[i].ssid, FAKE[i].ssid, sizeof(s_aps[i].ssid) - 1);
        strncpy(s_aps[i].auth, FAKE[i].auth, sizeof(s_aps[i].auth) - 1);
        strncpy(s_aps[i].band, FAKE[i].band, sizeof(s_aps[i].band) - 1);
        s_aps[i].rssi      = FAKE[i].rssi;
        s_aps[i].lock      = FAKE[i].lock;
        s_aps[i].saved     = FAKE[i].saved;
        s_aps[i].connected = FAKE[i].connected;
    }
    qsort(s_aps, (size_t)s_cnt, sizeof(s_aps[0]), cmp_ap);
    s_gen++;

    char buf[APP_IN_STR_MAX];
    if (s_cnt > 0)
        snprintf(buf, sizeof(buf), "已发现 %d 个网络", s_cnt);
    else
        snprintf(buf, sizeof(buf), "未发现网络，请重新扫描");

    /* 数据保留在 s_aps（本文件静态数组），app 经 wifi_ap_at()/count() 直接读；
     * 不经 Flow 数组变量（aps[] 已移出 EEZ）。 */
    app_set_input_s(APP_IN_SCAN_STATUS, buf);
    app_set_input_i(APP_IN_SCAN_STATE, 2);     /* 最后置完成 */
    printf("[IO] scan done: %d APs (sorted by RSSI)\n", s_cnt);
}

/******************** PC 专属夹具钩子 ********************/

/* 裁剪假世界规模，只用于 ⑤ 逐状态出图（例如"扫到 0 个 AP"的空态）。
 * 刻意不进 wifi_platform.h：真机没有这个概念，声明在共享头上就是骗人。
 * 但必须 extern "C"——调用方是无头仿真入口 main.c（C 编译），否则符号被 C++ 改名链不上。 */
// 函数作用：设定 PC 假世界返回的 AP 条数。 参数：n：<0 用全表。 返回值：无。
extern "C" void io_fake_set_ap_count(int n) { s_fake_n = n; }

// 函数作用：按 SSID 找假世界里的条目（可变指针，后端要改它）。
//          参数：ssid：网络名。 返回值：命中指针；空名或未扫到返回 NULL。
static wifi_ap_t *find_ap(const char *ssid)
{
    if (!ssid || !ssid[0]) return NULL;
    for (int i = 0; i < s_cnt; i++)
        if (strcmp(s_aps[i].ssid, ssid) == 0) return &s_aps[i];
    return NULL;
}

// 函数作用：状态变更后重排序并 +1 代数（UI 靠代数触发重建）。 参数：无。 返回值：无。
static void resort_and_publish(void)
{
    qsort(s_aps, (size_t)s_cnt, sizeof(s_aps[0]), cmp_ap);
    s_gen++;
}

/******************** 对外初始化与公开接口 ********************/

// 函数作用：初始化后端并发布初始文案。 参数：无。 返回值：无。
void io_init(void)
{
    s_scan_state = 0;
    app_set_input_i(APP_IN_SCAN_STATE, 0);
    app_set_input_s(APP_IN_SCAN_STATUS, "点击刷新开始扫描");
    printf("[IO] io_init (pc fake wifi)\n");
}

// 函数作用：发起一次扫描（2s 后 publish）。 参数：v：1 才生效；扫描中重复调用被忽略。 返回值：无。
void io_wifi_scan(int v)
{
    if (v != 1 || s_scan_state == 1) return;
    s_scan_state = 1;
    s_t0 = clock();
    app_set_input_i(APP_IN_SCAN_STATE, 1);
    app_set_input_s(APP_IN_SCAN_STATUS, "正在扫描…");
    printf("[IO] scan start\n");
}

// 函数作用：连接指定网络；有锁且给了密码就顺带存成"已保存"。
//          参数：ssid：目标网络；password：可为空。 返回值：无。
void io_wifi_connect(const char *ssid, const char *password)
{
    wifi_ap_t *ap = find_ap(ssid);
    if (!ap) {
        printf("[IO] connect 跳过：找不到 %s\n", ssid ? ssid : "(空)");
        return;
    }
    /* ★ ap 是指向 s_aps 槽位的指针，而 resort 会 qsort 整个数组——
     *   重排后同一槽位住的是别的网络。所以文案/日志要用的 SSID 和 saved
     *   必须在重排前抄进局部变量，否则「已连接 X」会报成另一个网络。 */
    char target[sizeof(ap->ssid)];
    memcpy(target, ap->ssid, sizeof(target));
    int now_saved;

    for (int i = 0; i < s_cnt; i++) s_aps[i].connected = false;
    ap->connected = true;
    if (ap->lock && password && password[0]) ap->saved = true;
    now_saved = (int)ap->saved;
    resort_and_publish();

    char buf[APP_IN_STR_MAX];
    snprintf(buf, sizeof(buf), "已连接 %s", target);
    app_set_input_s(APP_IN_SCAN_STATUS, buf);
    printf("[IO] connected: %s (saved=%d)\n", target, now_saved);
}

// 函数作用：忘记指定网络（清掉"已保存"）。 参数：ssid：目标网络。 返回值：无。
void io_wifi_forget(const char *ssid)
{
    wifi_ap_t *ap = find_ap(ssid);
    if (!ap) {
        printf("[IO] forget 跳过：找不到 %s\n", ssid ? ssid : "(空)");
        return;
    }
    /* 只清"已保存"，不动 connected：与 Windows 删 profile 的行为一致
     * （已建立的连接不会因此断开）。 */
    char target[sizeof(ap->ssid)];
    memcpy(target, ap->ssid, sizeof(target));   /* 同上：重排前抄走 */
    ap->saved = false;
    resort_and_publish();
    printf("[IO] forgotten: %s\n", target);
}

// 函数作用：推进扫描计时并把状态回写 model。 参数：无。 返回值：无。
void io_sample_inputs(void)
{
    if (s_scan_state == 1 && s_t0 != 0) {
        double elapsed = (double)(clock() - s_t0) / CLOCKS_PER_SEC;
        if (elapsed >= 2.0) {
            publish();
            s_scan_state = 2;
        }
    }
}

// 函数作用：取第 index 条扫描结果。 参数：index：排序后下标。 返回值：只读指针；越界返回 NULL。
const wifi_ap_t *wifi_ap_at(int index)
{
    if (index < 0 || index >= s_cnt) return NULL;
    return &s_aps[index];
}

// 函数作用：结果总数。 参数：无。 返回值：AP 条数。
int wifi_ap_count(void) { return s_cnt; }

// 函数作用：结果代数（内容变化 +1，UI 据此重建）。 参数：无。 返回值：代数。
int wifi_ap_gen(void)   { return s_gen; }

#endif /* !WIFI_PLATFORM_DEVICE */
