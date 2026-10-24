/*
 * wifi_nav.cpp — 模态显隐的实现（只动 objects.* 的可见性与标题文案）
 *
 * 为什么显隐只能在这里：EEZ 的 hiddenFlag 是**逐对象字面量**，且本工程 EEZ 侧
 * 不持有任何变量，所以整块模态必须靠 overlay_root / dlg_root 这一个父容器原子显隐
 * （kit cases/B16）。
 */
#include <stdio.h>
#include "lvgl.h"
#include "wifi_nav.h"
#include "../../ui/screens.h"

/******************** 模块私有状态与常量 ********************/

static bool s_sheet_open = false;    /* 半页是否在前台 */
static bool s_dlg_open = false;      /* 对话框是否在前台 */

/******************** 对外初始化与公开接口 ********************/

// 函数作用：查询半页是否在前台。 参数：无。 返回值：true 表示显示中。
bool wifi_nav_sheet_open(void) { return s_sheet_open; }

// 函数作用：查询对话框是否在前台。 参数：无。 返回值：true 表示显示中。
bool wifi_nav_dialog_open(void) { return s_dlg_open; }

// 函数作用：打开连接半页并填标题，同时关掉对话框（模态互斥）。
//          参数：ssid：目标网络名。 返回值：无。
void wifi_nav_open_sheet(const char *ssid)
{
    if (!objects.overlay_root) return;
    if (ssid && objects.lbl_pwd_ssid) lv_label_set_text(objects.lbl_pwd_ssid, ssid);
    if (objects.pwd_ta) lv_textarea_set_text(objects.pwd_ta, "");
    s_dlg_open = false;
    if (objects.dlg_root) lv_obj_add_flag(objects.dlg_root, LV_OBJ_FLAG_HIDDEN);
    s_sheet_open = true;
    lv_obj_remove_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] sheet open: %s\n", ssid ? ssid : "");
}

// 函数作用：关闭连接半页。 参数：无。 返回值：无（未打开时不动，避免重复日志）。
void wifi_nav_close_sheet(void)
{
    if (!s_sheet_open) return;
    s_sheet_open = false;
    if (objects.overlay_root) lv_obj_add_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] sheet close\n");
}

// 函数作用：打开「忘记此网络」对话框并填 SSID，同时关掉半页。 参数：ssid：目标网络名。 返回值：无。
void wifi_nav_open_dialog(const char *ssid)
{
    if (!objects.dlg_root) return;
    if (ssid && objects.lbl_dlg_ssid) lv_label_set_text(objects.lbl_dlg_ssid, ssid);
    s_sheet_open = false;
    if (objects.overlay_root) lv_obj_add_flag(objects.overlay_root, LV_OBJ_FLAG_HIDDEN);
    s_dlg_open = true;
    lv_obj_remove_flag(objects.dlg_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] dialog open: %s\n", ssid ? ssid : "");
}

// 函数作用：关闭对话框。 参数：无。 返回值：无。
void wifi_nav_close_dialog(void)
{
    if (!s_dlg_open) return;
    s_dlg_open = false;
    if (objects.dlg_root) lv_obj_add_flag(objects.dlg_root, LV_OBJ_FLAG_HIDDEN);
    printf("[UI] dialog close\n");
}
