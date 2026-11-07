/* sim_reads.c — PC 仿真专用：让"外部读"随时间变化，并派生开关状态
 *
 * 只做仿真世界的数据源，不碰业务逻辑：
 *   - 外部读（hr）：室温/湿度/功率/电量/码率/告警等按 1s 节拍缓慢抖动；
 *   - 内部派生：色温随滑条、插座开关、布防状态、配网进度按 100ms 刷新。
 * ESP32 目标上编译为空实现（真实数据由驱动/协议栈提供）。
 */
#include "sim_reads.h"

#ifdef ESP_PLATFORM

void sim_reads_init(void) {}
void sim_reads_tick(void) {}

#else

#include "lvgl.h"
#include "screens.h"
#include "value_bind.h"

static int t10[4]   = { 235, 240, 228, 231 };   /* 客厅/主卧/厨房/浴室，0.1°C */
static int hum[4]   = { 48, 50, 55, 62 };
static int cnt[4]   = { 5, 2, 3, 1 };
static int weather10 = 220;
static int online    = 12;
static int plug_w    = 46;
static int plug_today_x100 = 18;                /* 今日 0.18 kWh */
static int plug_month_x10  = 46;                /* 本月 4.6 kWh */
static int light_kwh_x10  = 368;                /* 36.8 kWh */
static int light_min = 2, sensor_min = 2;
static int cam_mbps_x10 = 18, cam_ms = 120;
static int en_today_x10 = 124;                  /* 12.4 kWh */
static int en_month = 268;
static int share[4] = { 38, 27, 22, 13 };
static int bat[3]   = { 92, 76, 58 };
static int alarms   = 0;
static int pair_pct = 0;
static uint32_t rnd_state = 0x12345678u;
static uint32_t t_in, t_ext;

static int rnd(int lo, int hi)
{
    rnd_state = rnd_state * 1664525u + 1013904223u;
    return lo + (int)((rnd_state >> 16) % (uint32_t)(hi - lo + 1));
}

static int clamp(int v, int lo, int hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

static int sw_on(lv_obj_t *o)
{
    return o && lv_obj_has_state(o, LV_STATE_CHECKED);
}

#define SET(field, fmt, ...) \
    do { if (objects.field) lv_label_set_text_fmt(objects.field, fmt, __VA_ARGS__); } while (0)
#define SETS(field, s) \
    do { if (objects.field) lv_label_set_text(objects.field, s); } while (0)

static void ext_apply(void)
{
    SET(main_hr02, "%d° 晴", weather10 / 10);
    SET(main_hr03, "室内 %d.%d° · %d%%", t10[0] / 10, t10[0] % 10, hum[0]);
    SET(main_hr05, "%d 个设备在线", online);
    SET(main_hr07, "%d.%d°", t10[0] / 10, t10[0] % 10);
    SET(main_hr08, "%d 个设备 · 湿度 %d%%", cnt[0], hum[0]);
    SET(main_hr09, "%d.%d°", t10[1] / 10, t10[1] % 10);
    SET(main_hr10, "%d 个设备 · 湿度 %d%%", cnt[1], hum[1]);
    SET(main_hr11, "%d.%d°", t10[2] / 10, t10[2] % 10);
    SET(main_hr12, "%d 个设备 · 湿度 %d%%", cnt[2], hum[2]);
    SET(main_hr13, "%d.%d°", t10[3] / 10, t10[3] % 10);
    SET(main_hr14, "%d 个设备 · 湿度 %d%%", cnt[3], hum[3]);

    SET(living_hr03, "%d 个设备 · %d.%d°C · 湿度 %d%%", cnt[0], t10[0] / 10, t10[0] % 10, hum[0]);
    SET(living_hr06, "%d.%d°", t10[0] / 10, t10[0] % 10);
    SET(living_hr07, "%d.%d° / %d%%", t10[0] / 10, t10[0] % 10, hum[0]);
    SET(master_hr02, "%d 个设备 · %d.%d°C · 湿度 %d%%", cnt[1], t10[1] / 10, t10[1] % 10, hum[1]);
    SET(master_hr04, "%d.%d°", t10[1] / 10, t10[1] % 10);
    SET(master_hr05, "%d.%d° / %d%%", t10[1] / 10, t10[1] % 10, hum[1]);
    SET(kitchen_hr02, "%d 个设备 · %d.%d°C · 湿度 %d%%", cnt[2], t10[2] / 10, t10[2] % 10, hum[2]);
    SET(bath_hr02, "%d 个设备 · %d.%d°C · 湿度 %d%%", cnt[3], t10[3] / 10, t10[3] % 10, hum[3]);

    SET(detail_sensor_hr02, "客厅 · %d 分钟前上报", sensor_min);
    SET(detail_sensor_hr03, "%d.%d°", t10[0] / 10, t10[0] % 10);
    SET(detail_sensor_hr04, "%d%%", hum[0]);

    SET(detail_light_hr04, "%d.%d kWh", light_kwh_x10 / 10, light_kwh_x10 % 10);
    SET(detail_light_hr05, "%d 分钟前", light_min);
    SET(detail_camera_hr05, "码率 %d.%d Mbps · 延迟 %d ms",
        cam_mbps_x10 / 10, cam_mbps_x10 % 10, cam_ms);

    SET(detail_plug_hr07, "今日 %d.%02d kWh", plug_today_x100 / 100, plug_today_x100 % 100);
    SET(detail_plug_hr11, "本月累计用电 %d.%d kWh（只读）",
        plug_month_x10 / 10, plug_month_x10 % 10);

    SET(energy_hr03, "今日 %d.%d kWh · 本月 %d kWh", en_today_x10 / 10, en_today_x10 % 10, en_month);
    SET(energy_hr04, "%d%%", share[0]);
    SET(energy_hr05, "%d%%", share[1]);
    SET(energy_hr06, "%d%%", share[2]);
    SET(energy_hr07, "%d%%", share[3]);

    SET(security_hr07, "今日告警 %d 条", alarms);
    SET(devices_hr01, "示例：共 %d 个设备 · 4 个房间", online);
}

static void ext_jitter(void)
{
    int i;
    weather10 = clamp(weather10 + rnd(-1, 1), 180, 280);
    for (i = 0; i < 4; i++) {
        t10[i] = clamp(t10[i] + rnd(-1, 1), 180, 280);
        hum[i] = clamp(hum[i] + rnd(-1, 1), 35, 70);
    }
    online = 10 + rnd(0, 4);
    plug_w = clamp(plug_w + rnd(-6, 6), 20, 80);
    plug_today_x100 = clamp(plug_today_x100 + rnd(0, 1), 0, 99);
    if (rnd(0, 9) == 0) plug_month_x10 = clamp(plug_month_x10 + 1, 0, 999);
    light_kwh_x10 = clamp(light_kwh_x10 + rnd(0, 1), 0, 9999);
    light_min = (light_min + 1) % 30;
    sensor_min = (sensor_min + 1) % 30;
    cam_mbps_x10 = clamp(cam_mbps_x10 + rnd(-1, 1), 10, 30);
    cam_ms = clamp(cam_ms + rnd(-5, 5), 80, 200);
    en_today_x10 = clamp(en_today_x10 + rnd(0, 2), 0, 400);
    if (en_today_x10 >= 400) { en_today_x10 = 0; en_month++; }
    i = rnd(0, 3);
    if (share[i] > 10) { share[i]--; share[(i + 1) % 4]++; }
    for (i = 0; i < 3; i++) bat[i] = clamp(bat[i] - rnd(0, 1), 20, 100);
    if (rnd(0, 199) == 0) alarms = clamp(alarms + 1, 0, 3);
}

static void int_apply(void)
{
    static const char *SIG[] = { "强", "中", "弱" };
    int armed = sw_on(objects.security_hw01_sw);
    int plug_on = sw_on(objects.detail_plug_hw01_sw);
    int cct = objects.detail_light_hw03_sl
                  ? lv_slider_get_value(objects.detail_light_hw03_sl) : 45;

    cct = value_bind_cct(cct);
    SET(detail_light_hr02, "客厅 · %dK · 在线", cct);
    SET(detail_light_hr03, "%s", SIG[(lv_tick_get() / 5000) % 3]);

    SETS(detail_plug_hr05, plug_on ? "开" : "关");
    SET(detail_plug_hr06, "%d W", plug_on ? plug_w : 0);

    SETS(main_hr04, armed ? "已布防 · 离家模式" : "撤防 · 在家模式");
    SET(security_hr04, "%s · 电量 %d%%", sw_on(objects.security_hw02_sw) ? "已布防" : "已撤防", bat[0]);
    SET(security_hr05, "%s · 电量 %d%%", sw_on(objects.security_hw03_sw) ? "已布防" : "已撤防", bat[1]);
    SET(security_hr06, "%s · 电量 %d%%", sw_on(objects.security_hw04_sw) ? "已布防" : "已撤防", bat[2]);

    if (pair_pct < 100) pair_pct++;
    SET(add_pairing_r01, "%d%%", pair_pct);
}

void sim_reads_init(void)
{
    ext_apply();
    int_apply();
    t_in = t_ext = lv_tick_get();
}

void sim_reads_tick(void)
{
    uint32_t now = lv_tick_get();
    if (now - t_ext >= 1000u) { t_ext = now; ext_jitter(); ext_apply(); }
    if (now - t_in >= 100u)  { t_in = now; int_apply(); }
}

#endif /* !ESP_PLATFORM */
