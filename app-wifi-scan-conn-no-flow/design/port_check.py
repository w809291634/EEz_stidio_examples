# -*- coding: utf-8 -*-
"""port_check.py —— 把"这模块能不能插进新工程"变成一条命令。

用法：
    python design/port_check.py [--ui <含 screens.h/actions.h 的目录>]
默认检查本工程的 src/ui；给新工程时传它的 src/ui。

判据（缺任何一项都 FAIL，退出码非 0）：
  1. screens.h 的 objects_t 里有本模块引用的全部对象名；
  2. actions.h 声明了本模块实现的全部动作；
  3. platform/wifi_platform.h 的接口齐全（防止拿半份模块）；
  4. lv_conf.h 打开了模块依赖的 LVGL 组件（arc/spinner、Montserrat 14/16）。
第 3/4 项只在本工程目录下检查（新工程未必有同名文件时跳过并说明）。
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---- 模块对 EEZ 的契约（改这里之前先想清楚：新工程都要跟着改）----
OBJECTS = ["main", "list_box", "lbl_status", "btn_refresh",
           "overlay_root", "scrim", "sheet", "lbl_pwd_ssid", "pwd_ta",
           "dlg_root", "lbl_dlg_ssid"]
ACTIONS = ["scan_start", "wifi_connect", "pwd_cancel",
           "dlg_forget", "wifi_disconnect", "dlg_cancel"]
PLATFORM = ["io_init", "io_sample_inputs", "io_wifi_scan", "io_wifi_connect",
            "io_wifi_forget", "io_wifi_disconnect",
            "wifi_ap_at", "wifi_ap_count", "wifi_ap_gen"]
LV_DEFS = ["LV_USE_ARC", "LV_USE_SPINNER", "LV_FONT_MONTSERRAT_14",
           "LV_FONT_MONTSERRAT_16"]


def read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def check_struct_members(ui_dir):
    p = os.path.join(ui_dir, "screens.h")
    if not os.path.isfile(p):
        print("FAIL 找不到 %s" % p)
        return False
    src = read(p)
    m = re.search(r"typedef struct _objects_t \{(.*?)\} objects_t;", src, re.S)
    if not m:
        print("FAIL screens.h 里没有 objects_t 结构体")
        return False
    have = set(re.findall(r"lv_obj_t\s*\*\s*(\w+)\s*;", m.group(1)))
    miss = [x for x in OBJECTS if x not in have]
    print("%s screens.h 对象齐（%d/%d）%s"
          % ("OK  " if not miss else "FAIL", len(OBJECTS) - len(miss),
             len(OBJECTS), "" if not miss else "：缺 " + ", ".join(miss)))
    return not miss


def check_actions(ui_dir):
    p = os.path.join(ui_dir, "actions.h")
    if not os.path.isfile(p):
        print("FAIL 找不到 %s" % p)
        return False
    src = read(p)
    have = set(re.findall(r"void\s+(action_\w+)\s*\(", src))
    miss = ["action_" + x for x in ACTIONS if "action_" + x not in have]
    print("%s actions.h 动作齐（%d/%d）%s"
          % ("OK  " if not miss else "FAIL", len(ACTIONS) - len(miss),
             len(ACTIONS), "" if not miss else "：缺 " + ", ".join(miss)))
    return not miss


def check_platform():
    p = os.path.join(ROOT, "src", "native", "platform", "wifi_platform.h")
    if not os.path.isfile(p):
        print("SKIP 没有 platform/wifi_platform.h（模块不完整？）")
        return False
    src = read(p)
    miss = [x for x in PLATFORM if not re.search(r"\b%s\s*\(" % x, src)]
    print("%s 平台接口齐（%d/%d）%s"
          % ("OK  " if not miss else "FAIL", len(PLATFORM) - len(miss),
             len(PLATFORM), "" if not miss else "：缺 " + ", ".join(miss)))
    return not miss


def check_lv_conf():
    p = os.path.join(ROOT, "design", "sim_cmake", "lv_conf.h")
    if not os.path.isfile(p):
        print("SKIP 没有 lv_conf.h（真机构建请在目标工程里自查这 4 个开关）")
        return True
    src = read(p)
    bad = []
    for d in LV_DEFS:
        m = re.search(r"^#define\s+%s\s+(\d+)" % d, src, re.M)
        if not m or m.group(1) == "0":
            bad.append(d)
    print("%s lv_conf 组件齐（%s）%s"
          % ("OK  " if not bad else "FAIL", ", ".join(LV_DEFS),
             "" if not bad else "：未开 " + ", ".join(bad)))
    return not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ui", default=os.path.join(ROOT, "src", "ui"),
                    help="目标工程的 src/ui 目录（含 screens.h / actions.h）")
    a = ap.parse_args()
    ui = os.path.abspath(a.ui)
    print("=== [移植] 模块 ↔ EEZ 契约检查：%s" % ui)
    ok = check_struct_members(ui)
    ok = check_actions(ui) and ok
    ok = check_platform() and ok
    ok = check_lv_conf() and ok
    print("==== PORT CHECK %s ====" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
