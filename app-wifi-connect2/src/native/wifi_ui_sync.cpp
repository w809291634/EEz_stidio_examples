/*
 * wifi_ui_sync.cpp — 把 io 层的扫描结果填进 EEZ 画好的 10 个固定槽。
 *
 * 规则（定稿）：
 *   - 槽位固定 10 个，运行时只改内容，不新建/销毁对象；
 *   - 空槽 hiddenFlag 隐藏，并把可见行 y 重排（不依赖 flex，防止留洞）；
 *   - 顺序由 io 层保证：已连接置顶 → RSSI 降序 → SSID 升序；
 *   - 状态文案/按钮文字也在这里写（避免 label 表达式被 codegen 编成空串）。
 */
#include <stdio.h>
#include <string.h>
#include "lvgl.h"
#include "app_model.h"
#include "wifi_ui_sync.h"
#include "platform/io_iface.h"
#include "../ui/screens.h"

#define SLOT_MAX   10
#define ROW_PITCH  50

#define C_BAR_ON   0x5B8CFF
#define C_BAR_OFF  0x2A3550
#define C_CONN     0x3DDC97
#define C_SAVED    0x9DB8FF
#define C_OPEN     0x5C6A85

static int s_last_gen = -1;
static int s_last_state = -1;

/* 行内子对象顺序（build_example.row_slot）：4 根信号条 + SSID + 副行 + 状态 */
#define CH_BAR0  0
#define CH_SSID  4
#define CH_META  5
#define CH_STATE 6

static int rssi_bars(int rssi)
{
    /* 阈值 -85 / -75 / -65 / -55，对应点亮 1..4 格 */
    if (rssi >= -55) return 4;
    if (rssi >= -65) return 3;
    if (rssi >= -75) return 2;
    if (rssi >= -85) return 1;
    return 0;
}

static void fill_row(lv_obj_t *row, int idx, const wifi_ap_t *ap)
{
    lv_obj_set_pos(row, 0, idx * ROW_PITCH);
    lv_obj_remove_flag(row, LV_OBJ_FLAG_HIDDEN);

    int on = rssi_bars(ap->rssi);
    for (int b = 0; b < 4; b++) {
        lv_obj_t *bar = lv_obj_get_child(row, CH_BAR0 + b);
        if (!bar) continue;
        lv_obj_set_style_bg_color(bar, lv_color_hex(b < on ? C_BAR_ON : C_BAR_OFF), 0);
    }

    lv_obj_t *ssid = lv_obj_get_child(row, CH_SSID);
    lv_obj_t *meta = lv_obj_get_child(row, CH_META);
    lv_obj_t *state = lv_obj_get_child(row, CH_STATE);
    if (ssid) lv_label_set_text(ssid, ap->ssid);

    if (meta) {
        char buf[80];
        snprintf(buf, sizeof(buf), "%s · %d dBm · %s",
                 ap->auth, ap->rssi, ap->band);
        lv_label_set_text(meta, buf);
    }

    if (state) {
        const char *txt = "";
        uint32_t color = C_OPEN;
        if (ap->connected) { txt = "已连接"; color = C_CONN; }
        else if (ap->saved) { txt = "已保存"; color = C_SAVED; }
        else if (!ap->lock) { txt = "无需密码"; color = C_OPEN; }
        lv_label_set_text(state, txt);
        lv_obj_set_style_text_color(state, lv_color_hex(color), 0);
    }
}

static void hide_row(lv_obj_t *row)
{
    lv_obj_add_flag(row, LV_OBJ_FLAG_HIDDEN);
}

void wifi_ui_sync(void)
{
    if (!objects.list_box || !objects.lbl_status || !objects.btn_refresh)
        return;

    int gen = wifi_ap_gen();
    int state = (int)app_get_input_i(APP_IN_SCAN_STATE);
    int n = wifi_ap_count();

    /* 状态文案 + 刷新按钮（状态变化时更新一次即可） */
    if (state != s_last_state) {
        lv_label_set_text(objects.lbl_status, app_get_input_s(APP_IN_SCAN_STATUS));
        lv_obj_t *bl = lv_obj_get_child(objects.btn_refresh, 0);
        if (bl) lv_label_set_text(bl, state == 1 ? "扫描中" : "刷 新");
        if (state == 1)
            lv_obj_remove_flag(objects.btn_refresh, LV_OBJ_FLAG_CLICKABLE);
        else
            lv_obj_add_flag(objects.btn_refresh, LV_OBJ_FLAG_CLICKABLE);
        s_last_state = state;
    }

    /* 扫描中/无结果时只处理显隐，不重排数据 */
    if (gen == s_last_gen) return;

    for (int i = 0; i < SLOT_MAX; i++) {
        lv_obj_t *row = lv_obj_get_child(objects.list_box, i);
        if (!row) continue;
        const wifi_ap_t *ap = (state == 2 && i < n) ? wifi_ap_at(i) : NULL;
        if (ap) fill_row(row, i, ap);
        else hide_row(row);
    }
    s_last_gen = gen;
    printf("[UI] list rebuilt: %d rows visible (gen=%d)\n",
           n > SLOT_MAX ? SLOT_MAX : n, gen);
}
