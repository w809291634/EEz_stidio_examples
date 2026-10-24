/*
 * wifi_list.cpp — Wi-Fi 列表行的创建与手势（父 lv_list 由 EEZ 画）
 *
 * 规则（v2 · List 方案，2026-10-21）：
 *   - EEZ 只画一个空 lv_list（objects.list_box），行全部由本文件动态创建——
 *     行数 = wifi_ap_count()，天然可滚动；
 *   - 每行内自绘：4 根信号条 + SSID + 副行(类型·dBm·频段) + 状态文字；
 *   - 顺序由 io 层保证：已连接置顶 → RSSI 降序 → SSID 升序；
 *   - 数据源直接读 io 接口 wifi_ap_at()/wifi_ap_count()（数组变量已移出 EEZ，
 *     不再经 Flow 数组 aps[]，避免 EEZ 无法渲染动态列表的限制 P-0152/P-0165）。
 *
 * 为什么不用"容器 + 固定槽"（v1 已废弃）：
 *   lv_obj_hit_test() 第一行就要求 LV_OBJ_FLAG_CLICKABLE——自建行/容器
 *   都没这个 flag，indev 的 hit test 全线失败，act_obj 恒为 NULL，
 *   滚动链根本起不了头（lv_indev_scroll.c 的 SCROLL_CHAIN 也无从触发）。
 *   lv_list 的子项是 lv_button（CLICKABLE）+ list 自身 SCROLLABLE + 全套
 *   SCROLL_CHAIN——LVGL 官方的滚动链路本来就是通的。
 */
#include <stdio.h>
#include <stdint.h>
#include "lvgl.h"
#include "wifi_list.h"
#include "platform/wifi_platform.h"      /* wifi_ap_at / wifi_ap_count */
#include "navigation/wifi_nav.h"         /* 手势只决定去向 */
#include "../../../ui/screens.h"
#include "../../../ui/fonts.h"

/******************** 模块私有状态与常量 ********************/

#define C_BAR_ON   0x5B8CFF
#define C_BAR_OFF  0x2A3550
#define C_CONN     0x3DDC97
#define C_SAVED    0x9DB8FF
#define C_OPEN     0x5C6A85
#define C_ROW_BG   0x101A28
#define C_ROW_EDGE 0x26314A
#define C_TEXT1    0xF0F4FC
#define C_TEXT2    0x8A99B3

#define ROW_H      44          /* 与设计图一致 */
#define BAR_X0     14          /* 信号条起点（行内） */
#define BAR_W      3
#define BAR_GAP    3           /* 条间距 3（宽 3 → 中心距 6） */
#define TXT_X      44

/* 行的两条通路：单击=需要密码的网络开半页；长按=已保存网络开"忘记"对话框。
 * 索引存在 user_data 里，事件里回查 io（列表重建后索引与数据仍同源）。
 *
 * ★ LVGL 对普通按钮在长按抬手后**仍会补发一次 CLICKED**
 *   （lv_indev.c:1046 只在 short_click 上做了 long_pr_sent 判断，CLICKED 无条件发）。
 *   不吞掉它，长按就会"先开对话框、再被补发的 CLICKED 换成半页"，
 *   模态互斥反而把对话框关掉。用"本次手势的行"来认这条尾巴。 */
static lv_obj_t *s_long_row = NULL;

/******************** 小工具 / 坐标换算 ********************/

// 函数作用：把 RSSI 映射成点亮的信号格数。 参数：rssi：dBm 负值。 返回值：0..4。
static int rssi_bars(int rssi)
{
    /* 阈值 -85 / -75 / -65 / -55，对应点亮 1..4 格 */
    if (rssi >= -55) return 4;
    if (rssi >= -65) return 3;
    if (rssi >= -75) return 2;
    if (rssi >= -85) return 1;
    return 0;
}

// 函数作用：在行内画一个纯色小方块（信号条）。 参数：行列坐标宽高与颜色。 返回值：新建对象。
static lv_obj_t *row_bar(lv_obj_t *row, int x, int y, int w, int h,
                         uint32_t color)
{
    lv_obj_t *o = lv_obj_create(row);
    lv_obj_set_pos(o, x, y);
    lv_obj_set_size(o, w, h);
    lv_obj_set_scrollbar_mode(o, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(o, (lv_obj_flag_t)(LV_OBJ_FLAG_CLICKABLE |
                                      LV_OBJ_FLAG_SCROLLABLE));
    lv_obj_set_style_bg_color(o, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(o, 255, LV_PART_MAIN);
    lv_obj_set_style_radius(o, 2, LV_PART_MAIN);
    lv_obj_set_style_border_width(o, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(o, 0, LV_PART_MAIN);
    return o;
}

// 函数作用：在行内画一个文字标签。 参数：行列坐标宽高文本颜色。 返回值：新建 label。
static lv_obj_t *row_label(lv_obj_t *row, int x, int y, int w, int h,
                           const char *text, uint32_t color)
{
    lv_obj_t *o = lv_label_create(row);
    lv_obj_set_pos(o, x, y);
    lv_obj_set_size(o, w, h);
    lv_obj_set_scrollbar_mode(o, LV_SCROLLBAR_MODE_OFF);
    lv_obj_remove_flag(o, (lv_obj_flag_t)(LV_OBJ_FLAG_CLICKABLE |
                                      LV_OBJ_FLAG_SCROLLABLE));
    lv_obj_set_style_text_color(o, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_text_font(o, &ui_font_cn14, LV_PART_MAIN);
    lv_obj_set_style_border_width(o, 0, LV_PART_MAIN);
    lv_obj_set_style_pad_all(o, 0, LV_PART_MAIN);
    if (text) lv_label_set_text(o, text);
    return o;
}

/******************** 事件回调 ********************/

// 函数作用：行手势分发——单击开半页、长按开忘记对话框、吞掉长按补发的 CLICKED。
//          参数：e：LVGL 事件。 返回值：无。
static void row_event_cb(lv_event_t *e)
{
    lv_obj_t *row = (lv_obj_t *)lv_event_get_target(e);
    int idx = (int)(intptr_t)lv_obj_get_user_data(row);
    const wifi_ap_t *ap = wifi_ap_at(idx);
    if (!ap) return;

    switch (lv_event_get_code(e)) {
    case LV_EVENT_PRESSED:                    /* 新手势开始，清掉上一次的手尾标记 */
        s_long_row = NULL;
        break;
    case LV_EVENT_CLICKED:
        if (s_long_row == row) { s_long_row = NULL; break; }   /* 尾巴，吞掉 */
        /* 已连接的网络点开没有意义；开放网络免密直连属 ⑦-2 后端 */
        if (ap->lock && !ap->connected) wifi_nav_open_sheet(ap->ssid);
        break;
    case LV_EVENT_LONG_PRESSED:
        s_long_row = row;
        if (ap->saved) wifi_nav_open_dialog(ap->ssid);
        break;
    default:
        break;
    }
}

/******************** 行绘制 ********************/

/* 把一个 ap 画成一行：行 = lv_list_add_button 建的 button（CLICKABLE，
 * 滚动链与点选都靠它）。add_button 默认 flex_flow=ROW，要关掉才能摆绝对坐标。 */
// 函数作用：按 ap 数据绘制一行并挂手势。 参数：btn：行对象；ap：数据；index：行号。 返回值：无。
static void build_row(lv_obj_t *btn, const wifi_ap_t *ap, int index)
{
    lv_obj_set_height(btn, ROW_H);
    lv_obj_set_layout(btn, LV_LAYOUT_NONE);   /* 关掉 ROW flex，改用绝对坐标 */
    lv_obj_set_scrollbar_mode(btn, LV_SCROLLBAR_MODE_OFF);
    lv_obj_set_style_bg_color(btn, lv_color_hex(C_ROW_BG), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(btn, 255, LV_PART_MAIN);
    lv_obj_set_style_radius(btn, 10, LV_PART_MAIN);
    lv_obj_set_style_border_color(btn, lv_color_hex(C_ROW_EDGE), LV_PART_MAIN);
    lv_obj_set_style_border_width(btn, 1, LV_PART_MAIN);
    lv_obj_set_style_pad_all(btn, 0, LV_PART_MAIN);
    /* 行间距 6（lv_list 的 pad_row 被 EEZ 清成 0，用行的下内边距补） */
    lv_obj_set_style_pad_bottom(btn, 6, LV_PART_MAIN);

    /* ⑦-1 导航：单击开半页 / 长按开"忘记"对话框（PRESSED 用来分手势） */
    lv_obj_set_user_data(btn, (void *)(intptr_t)index);
    lv_obj_add_event_cb(btn, row_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(btn, row_event_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(btn, row_event_cb, LV_EVENT_LONG_PRESSED, NULL);

    /* SSID：add_button 建的那个 label（第 0 个子对象）复用 */
    lv_obj_t *ssid = lv_obj_get_child(btn, 0);
    if (ssid) {
        lv_obj_set_pos(ssid, TXT_X, 6);
        lv_obj_set_size(ssid, 230, 16);
        /* 坑（LVGL 9.4，lv_list.c/lv_label.c）：lv_list_add_button 的 label
         * 默认 SCROLL_CIRCULAR 跑马灯；且建 label 时它的 coords 还是 0，
         * 文字宽(84) > 盒宽(0) → lv_label_refr_text 当场启动无限滚动动画，
         * 之后再 set_size/布局刷新都不会重跑 refr_text，动画停不下来
         * → 每个 Wi-Fi 名称都在横向滚动。
         * 修法：显式改 long mode——lv_label_set_long_mode() 内部先
         * lv_anim_delete 掉旧动画再置 offset=0；CLIP 是纯绘制期裁剪，
         * 永远不会启动新动画，超长名字在 230px 盒边裁掉。 */
        lv_label_set_long_mode(ssid, LV_LABEL_LONG_MODE_CLIP);
        lv_obj_set_scrollbar_mode(ssid, LV_SCROLLBAR_MODE_OFF);
        lv_obj_set_style_text_color(ssid, lv_color_hex(C_TEXT1), LV_PART_MAIN);
        lv_obj_set_style_text_font(ssid, &ui_font_cn14, LV_PART_MAIN);
        lv_obj_set_style_border_width(ssid, 0, LV_PART_MAIN);
        lv_obj_set_style_pad_all(ssid, 0, LV_PART_MAIN);
    }

    /* 副行：类型 · dBm · 频段 */
    char meta[80];
    snprintf(meta, sizeof(meta), "%s · %d dBm · %s",
             ap->auth, ap->rssi, ap->band);
    row_label(btn, TXT_X, 24, 250, 16, meta, C_TEXT2);

    /* 信号条：4 根，底边对齐 row+34 */
    int on = rssi_bars(ap->rssi);
    static const int BH[4] = {5, 8, 11, 14};
    for (int b = 0; b < 4; b++) {
        row_bar(btn, BAR_X0 + b * (BAR_W + BAR_GAP), 34 - BH[b],
                BAR_W, BH[b], b < on ? C_BAR_ON : C_BAR_OFF);
    }

    /* 状态：已连接 / 已保存 / 无需密码（空 = 普通网络） */
    const char *txt = "";
    uint32_t color = C_OPEN;
    if (ap->connected) { txt = "已连接"; color = C_CONN; }
    else if (ap->saved) { txt = "已保存"; color = C_SAVED; }
    else if (!ap->lock) { txt = "无需密码"; color = C_OPEN; }
    if (txt[0])
        row_label(btn, 310, 14, 120, 16, txt, color);
}

/******************** 对外初始化与公开接口 ********************/

// 函数作用：清空并按 io 快照重建列表行。 参数：state：扫描态，2 才建行。 返回值：无。
void wifi_list_rebuild(int state)
{
    int n = wifi_ap_count();                         /* io 层 AP 总数 */

    /* 清空旧行后按 ap_cnt 重建（lv_list 的行都是它的直接子对象） */
    lv_obj_clean(objects.list_box);

    int shown = 0;
    if (state == 2) {
        for (int i = 0; i < n; i++) {
            const wifi_ap_t *p = wifi_ap_at(i);
            if (!p) break;
            lv_obj_t *btn = lv_list_add_button(objects.list_box, NULL,
                                               p->ssid);
            if (!btn) break;
            build_row(btn, p, i);
            shown++;
        }
    }
    printf("[UI] list rebuilt: %d rows from io (gen=%d, count=%d)\n",
           shown, wifi_ap_gen(), n);
}
