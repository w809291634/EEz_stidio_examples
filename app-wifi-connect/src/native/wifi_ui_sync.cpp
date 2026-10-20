/*
 * wifi_ui_sync.cpp — 动态列表渲染：把 io 层的 AP 链表画进 EEZ 空容器 list_box。
 *
 * 模式照抄 lvgl_demo_ai 的 ui_data_sync（retry-until-success）：
 *   user_io_tick 每拍调用；代数(gen)或行数变了 → lv_obj_clean 重建全部行；
 *   list_box 还没建好（EEZ 屏初始化晚于 user_io_init）就下一拍重试。
 *
 * 每行 = 容器（CLICKABLE，点击回调按 user_data 索引置 PICK_SSID）
 *        + [锁] + SSID + 信号 + [已连接徽标]；文字统一用 ui_font_cn14。
 */
#include <stdio.h>
#include <stdint.h>
#include "lvgl.h"
#include "app_model.h"
#include "platform/io_iface.h"
#include "../ui/screens.h"      /* objects.list_box */
#include "../ui/fonts.h"        /* ui_font_cn14 */

static int s_last_synced_gen = -1;

static void row_click_cb(lv_event_t *e)
{
    int idx = (int)(intptr_t)lv_event_get_user_data(e);
    /* 按索引走链表找节点（io 层数据唯一真值源） */
    const wifi_ap_t *ap = wifi_ap_first();
    for (int i = 0; i < idx && ap; i++) ap = ap->next;
    if (ap) app_set_input_s(APP_IN_PICK_SSID, ap->ssid);
}

static void make_row(lv_obj_t *parent, int idx, const wifi_ap_t *ap)
{
    lv_obj_t *row = lv_obj_create(parent);
    lv_obj_remove_style_all(row);
    lv_obj_set_size(row, 432, 30);
    lv_obj_set_pos(row, 8, idx * 34 + 2);
    lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_style_bg_opa(row, LV_OPA_COVER, 0);
    lv_obj_set_style_bg_color(row, lv_color_hex(0x1A2233), 0);
    lv_obj_set_style_radius(row, 8, 0);
    lv_obj_add_event_cb(row, row_click_cb, LV_EVENT_CLICKED,
                        (void *)(intptr_t)idx);

    lv_obj_t *ssid = lv_label_create(row);
    lv_label_set_text(ssid, ap->ssid);
    lv_obj_set_style_text_color(ssid, lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_style_text_font(ssid, &ui_font_cn14, 0);
    lv_obj_align(ssid, LV_ALIGN_LEFT_MID, 10, 0);

    if (ap->lock) {
        lv_obj_t *lock = lv_label_create(row);
        lv_label_set_text(lock, "锁");
        lv_obj_set_style_text_color(lock, lv_color_hex(0xFFD38F), 0);
        lv_obj_set_style_text_font(lock, &ui_font_cn14, 0);
        lv_obj_align_to(lock, ssid, LV_ALIGN_OUT_RIGHT_MID, 8, 0);
    }

    if (ap->connected) {
        lv_obj_t *ok = lv_label_create(row);
        lv_label_set_text(ok, "已连接");
        lv_obj_set_style_text_color(ok, lv_color_hex(0x6CE69C), 0);
        lv_obj_set_style_text_font(ok, &ui_font_cn14, 0);
        lv_obj_align(ok, LV_ALIGN_RIGHT_MID, -60, 0);
    }

    lv_obj_t *rssi = lv_label_create(row);
    lv_label_set_text_fmt(rssi, "%d dBm", ap->rssi);
    lv_obj_set_style_text_color(rssi, lv_color_hex(0x8A94A6), 0);
    lv_obj_align(rssi, LV_ALIGN_RIGHT_MID, -6, 0);
}

void wifi_ui_sync(void)
{
    lv_obj_t *box = objects.list_box;
    if (!box) return;                       /* 屏还没建好 → 下一拍重试 */

    int gen = wifi_ap_gen();
    int n = wifi_ap_count();
    if (gen == s_last_synced_gen &&
        (uint32_t)n == lv_obj_get_child_count(box))
        return;                             /* 无变化 */

    lv_obj_clean(box);                      /* 删旧行 */
    const wifi_ap_t *ap = wifi_ap_first();
    for (int i = 0; ap; i++, ap = ap->next)
        make_row(box, i, ap);
    s_last_synced_gen = gen;
    printf("[UI] list rebuilt: %d rows (gen=%d)\n", n, gen);
}
