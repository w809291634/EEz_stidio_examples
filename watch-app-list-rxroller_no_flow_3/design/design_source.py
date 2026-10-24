# -*- coding: utf-8 -*-
"""唯一设计源（NO_FLOW 三条铁律③：界面只在这里定义一次）。

design_view.py（渲染 designer/ 效果图）与 build_watch_ui.py（直出 EEZ 工程）
都只读本文件，两者同源派生。

口径（2026-10-22 用户需求）：主页=表盘；第2页=applist（主流 14 个 APP，遥控相机已删）；每 APP ≥1 功能页。
页面关系候选：左右滑动切页（主页 ↔ 应用列表）；**未标注前所有控件＝纯展示、不接行为**（第②步用户序号标注后才接跳转）。
坐标口径：绝对坐标（左上角原点），屏幕 466x466 圆形。

圆形屏注意（记忆 reference-eez-circulardisplay-is-editor-only）：
矩形控件在圆屏上是"胶囊"，边距太深的元素会被表圈裁掉 ⇒ 内容保持在安全区内。
"""

import math

SCREEN = {"w": 466, "h": 466, "shape": "circular", "cx": 233, "cy": 233, "r": 233}

STYLE = {
    "bg": "#0A0A0F",
    "ring": "#2A2A35",
    "tick": "#55556A",
    "tick_major": "#8A8AA8",
    "text": "#FFFFFF",
    "sub": "#9A9AB5",
    "accent": "#FF6B35",
    "green": "#2BD97C",
    "blue": "#3DA5FF",
    "yellow": "#FFC531",
    "pink": "#FF5B8D",
    "purple": "#9A6BFF",
    "teal": "#2BD9C8",
}

# applist 集合（主流 14 个，遥控相机按用户令删除；图标=圆角彩底+白色矢量图形，
# glyph 键对应 design_view.py 的 GLYPHS 绘制器或文字标；第②步标注控件类型时再定导出形态）
APPS = [
    ("运动", "#FF6B35", "bolt"),
    ("心率", "#FF5B8D", "heart"),
    ("睡眠", "#9A6BFF", "moon"),
    ("血氧", "#3DA5FF", "97"),
    ("天气", "#2BD9C8", "sun"),
    ("消息", "#FFC531", "chat"),
    ("音乐", "#2BD97C", "music"),
    ("闹钟", "#FF8A3D", "bell"),
    ("秒表", "#8A8AA8", "watch"),
    ("计时", "#6B7BFF", "hour"),
    ("计算器", "#B5B5C8", "calc"),
    ("指南针", "#31C48A", "compass"),
    ("找手机", "#FF5B5B", "phone"),
    ("设置", "#7A7A8A", "gear"),
]

STATS = [  # 主页三宫格数据位（演示值；真值来源第②步口径里定）
    ("8523", "步数", STYLE["green"]),
    ("72", "心率", STYLE["pink"]),
    ("80%", "电量", STYLE["yellow"]),
]

# ---------------------------------------------------------------------------
# applist 纵向滚轮布局（参考示例 EEz_stidio_examples\watch-app-list-rxroller，
# 上游 rxwind7/Rxroller；参数口径逐字来自其唯一出处 watch_list_config.h，
# 按本工程 466 圆屏换算）：
#   缩放曲线 = 选中最大、未选中最小、中间线性插值：
#     SCALE_SPAN_PITCHES=3（0/33/66/100）、SCALE_CENTER_PCT=150（中心=ICON_PX*1.5）、
#     SCALE_EDGE_PCT=59（最小档占满档的 59%）
#   弧形排布 = CURVE_ENABLE=1、CURVE_RADIUS=700：x=R*(1-cos(d/R)) 偶函数 ⇒ C 形
#     侧视滚轮（上下都朝同一侧鼓）；y=R*sin(d/R) 纵向略压缩
#   几何     = ROW_PITCH=92（466 屏收小，原 120 为 502 高屏）；ICON_PX=60 ⇒
#     中心档 90px ≤ 行距（示例 preflight 同款几何门禁：中心图标不得顶到上下行）；
#     圆角方块底+单字（示例 shot 观感），名称在图标右侧
#   交互（甩动/吸附/scale 轴）EEZ 属性面没有 ⇒ 第⑦步按铁律0全功能阶段走
#     native（可直接复用该示例移植件）；设计图只定静态剖面。
# ---------------------------------------------------------------------------

ROLLER = {
    "icon_px": 60,
    "pitch": 92,
    "center_pct": 150,
    "edge_pct": 59,
    "span": 3,
    "curve_r": 700,
    "icon_cx": 175,
    "label_x": 240,
    "cy": 195,               # 焦点行略高于屏心：上留返回钮位、下留提示位
}


def roller_rows(screen, apps, center_idx):
    """返回 [{name,color,abbr,x,y,side}] —— 弧形滚轮的逐行剖面（d=行距差）。"""
    R = ROLLER
    cy = R["cy"]
    scale_c = R["icon_px"] * R["center_pct"] / 100.0
    scale_e = scale_c * R["edge_pct"] / 100.0
    rows = []
    for i, (name, color, abbr) in enumerate(apps):
        d = i - center_idx
        t = min(abs(d), R["span"]) / float(R["span"])
        side = scale_c + (scale_e - scale_c) * t          # 线性插值
        cr = R["curve_r"]
        dx = abs(d) * R["pitch"]
        x = R["icon_cx"] + cr * (1 - math.cos(dx / cr))   # 偶函数：上下同侧鼓（C 形）
        y = cy + cr * math.sin(dx / cr) * (1 if d > 0 else -1)
        rows.append({"name": name, "color": color, "abbr": abbr,
                     "x": x, "y": y, "side": side, "d": d})
    return rows


# ---------------------------------------------------------------------------
# 页面清单（16 页 = 主页表盘 + applist + 14 个 APP 功能页，每 APP ≥1 页；遥控相机已按用户令删除）
# 每页通用外壳：back=返回钮（跳转候选，第②步标注确认）、title=页面标题。
# 数值全部为演示占位（真值口径第②步控件清单表里逐项定）。
# ---------------------------------------------------------------------------

def _chrome(title, goto="applist"):
    return [
        {"type": "back", "id": "back", "x": 120, "y": 105, "goto": goto},
        {"type": "label", "id": "title", "text": title,
         "x": 233, "y": 100, "anchor": "mm", "size": 26, "color": STYLE["sub"]},
    ]


def _page(name, title, extra, back_to="applist"):
    return {"name": name, "title": title, "widgets": _chrome(title, back_to) + extra}


def _txt(i, text, x, y, size, color, anchor="mm"):
    return {"type": "label", "id": "t%d" % i, "text": text,
            "x": x, "y": y, "anchor": anchor, "size": size, "color": color}


PAGES = [
    {
        "name": "watchface",
        "title": "主页·表盘",
        "widgets": [
            {"type": "arc", "id": "dial_ring", "cx": 233, "cy": 233, "r": 214,
             "start": -90, "end": 270, "width": 2, "color": STYLE["ring"]},
            # 时刻刻度：12 大刻度 + 48 小刻度（纯装饰）
            {"type": "ticks", "id": "hour_ticks", "cx": 233, "cy": 233,
             "r_out": 214, "r_in_major": 198, "r_in_minor": 206,
             "count": 60, "major_every": 5,
             "major_color": STYLE["tick_major"], "minor_color": STYLE["tick"],
             "major_width": 3, "minor_width": 1},
            _txt(0, "10:09", 233, 172, 76, STYLE["text"]),
            _txt(1, "AM", 233, 224, 20, STYLE["sub"]),
            _txt(2, "10-22 周四", 233, 252, 22, STYLE["sub"]),
            {"type": "statrow", "id": "wf_stats", "items": STATS,
             "cx": 233, "y": 316, "gap": 106},
            {"type": "pager_dots", "id": "wf_pager", "count": 2, "active": 0,
             "cx": 233, "y": 388, "gap": 18, "r": 5},
        ],
    },
    {
        "name": "applist",
        "title": "应用列表",
        "widgets": [
            # 无返回钮（2026-10-22 用户定）：回表盘靠 tabview 左右滑动，不用控件
            # 首屏焦点=第 1 项（向下滚还有 13 项）；剖面 90/78/65/53…（中心 150%、跨 3 行线性到底 59%）
            # 不放操作提示文字：目检翻案——任何底部提示都会压住弧形第 3 行图标
            {"type": "roller", "id": "al_roller", "apps": APPS, "center_idx": 0},
        ],
    },

    # ---- 15 个 APP 功能页 ----
    _page("app_sport", "运动", [
        _txt(0, "320", 233, 185, 66, STYLE["accent"]),
        _txt(1, "千卡", 233, 232, 20, STYLE["sub"]),
        {"type": "progress", "id": "sp_steps", "label": "步数", "value": "8523",
         "pct": 0.68, "y": 278, "w": 250, "color": STYLE["green"]},
        {"type": "progress", "id": "sp_dist", "label": "距离", "value": "5.2km",
         "pct": 0.45, "y": 322, "w": 250, "color": STYLE["blue"]},
        {"type": "pill", "id": "sp_start", "text": "开始运动",
         "x": 233, "y": 375, "w": 168, "h": 46, "color": STYLE["accent"]},
    ]),
    _page("app_hr", "心率", [
        _txt(0, "72", 233, 180, 72, STYLE["pink"]),
        _txt(1, "BPM · 静息", 233, 228, 20, STYLE["sub"]),
        {"type": "bars", "id": "hr_week", "values": [40, 60, 48, 75, 55, 82, 62],
         "labels": ["一", "二", "三", "四", "五", "六", "日"],
         "cx": 233, "y": 345, "h": 110, "bw": 20, "gap": 12, "color": STYLE["pink"]},
        _txt(2, "最高 98   最低 54", 233, 395, 18, STYLE["sub"]),
    ]),
    _page("app_sleep", "睡眠", [
        _txt(0, "7h 24m", 233, 170, 52, STYLE["purple"]),
        _txt(1, "23:40 - 07:04", 233, 212, 20, STYLE["sub"]),
        {"type": "segbar", "id": "sl_stages", "y": 262, "w": 270, "h": 18,
         "segs": [("深睡", 0.22, "#5B3FD6"), ("浅睡", 0.52, STYLE["purple"]),
                  ("REM", 0.18, "#C8A2FF"), ("清醒", 0.08, "#8A8AA8")]},
        {"type": "legend", "id": "sl_legend", "y": 306, "gap": 40,
         "items": [("深睡 1h38", "#5B3FD6"), ("浅睡 3h52", STYLE["purple"]),
                   ("REM 1h19", "#C8A2FF")]},
        _txt(2, "评分 86 · 规律良好", 233, 352, 18, STYLE["sub"]),
    ]),
    _page("app_spo2", "血氧", [
        {"type": "ring", "id": "so_ring", "cx": 233, "cy": 215, "r": 82,
         "width": 12, "pct": 0.97, "color": STYLE["blue"], "bg": STYLE["ring"]},
        _txt(0, "97%", 233, 215, 46, STYLE["blue"]),
        _txt(1, "正常", 233, 258, 18, STYLE["sub"]),
        _txt(2, "范围 95-99 · 昨最低 94", 233, 330, 18, STYLE["sub"]),
        {"type": "pill", "id": "so_measure", "text": "测量",
         "x": 233, "y": 378, "w": 150, "h": 46, "color": STYLE["blue"]},
    ]),
    _page("app_weather", "天气", [
        _txt(0, "22°", 233, 165, 70, STYLE["teal"]),
        _txt(1, "多云  18°/25°", 233, 216, 20, STYLE["sub"]),
        {"type": "rowlist", "id": "wt_hours",
         "rows": [["11时", "23°"], ["12时", "24°"], ["13时", "25°"], ["14时", "24°"]],
         "y0": 258, "row_h": 38, "w": 210, "size": 20},
        _txt(2, "明日 19°/27° · 后日 雨", 233, 420, 16, STYLE["sub"]),
    ]),
    _page("app_msg", "消息", [
        _txt(0, "3 条未读", 233, 140, 22, STYLE["text"]),
        {"type": "rowlist", "id": "ms_list",
         "rows": [["微信", "10:02  张：方案今晚发我"],
                  ["短信", "09:47  10086：套餐余量"],
                  ["钉钉", "09:15  早会改 10:30"]],
         "y0": 195, "row_h": 68, "w": 300, "size": 18},
        {"type": "pill", "id": "ms_clear", "text": "全部清除",
         "x": 233, "y": 402, "w": 150, "h": 42, "color": STYLE["ring"]},
    ]),
    _page("app_music", "音乐", [
        {"type": "disc", "id": "mu_disc", "cx": 233, "cy": 185, "r": 62,
         "color": STYLE["green"]},
        _txt(0, "夜曲", 233, 272, 26, STYLE["text"]),
        _txt(1, "周杰伦 · 十一月的萧邦", 233, 300, 16, STYLE["sub"]),
        {"type": "progress", "id": "mu_prog", "label": None, "value": "1:23 / 3:45",
         "pct": 0.37, "y": 332, "w": 270, "color": STYLE["green"], "value_size": 14},
        {"type": "controls", "id": "mu_ctrl", "shapes": ["prev", "play", "next"],
         "cx": 233, "y": 382, "gap": 84, "size": 15, "color": STYLE["text"]},
    ]),
    _page("app_alarm", "闹钟", [
        _txt(0, "07:00", 233, 165, 60, STYLE["text"]),
        _txt(1, "下次闹钟 · 工作日", 233, 212, 18, STYLE["sub"]),
        {"type": "rowlist", "id": "al_list",
         "rows": [["06:30 起床", "开"], ["08:00 会议", "关"], ["12:30 午休", "开"]],
         "y0": 252, "row_h": 46, "w": 270, "size": 20},
        {"type": "pill", "id": "al_add", "text": "+ 添加闹钟",
         "x": 233, "y": 405, "w": 176, "h": 42, "color": STYLE["accent"]},
    ]),
    _page("app_stopwatch", "秒表", [
        _txt(0, "00:23.46", 233, 205, 48, STYLE["text"]),
        {"type": "pill", "id": "sw_start", "text": "开始",
         "x": 233, "y": 290, "w": 150, "h": 48, "color": STYLE["green"]},
        {"type": "pill", "id": "sw_reset", "text": "复位",
         "x": 233, "y": 352, "w": 150, "h": 48, "color": STYLE["ring"]},
    ]),
    _page("app_timer", "计时", [
        {"type": "ring", "id": "tm_ring", "cx": 233, "cy": 210, "r": 92,
         "width": 10, "pct": 0.65, "color": STYLE["yellow"], "bg": STYLE["ring"]},
        _txt(0, "05:00", 233, 210, 44, STYLE["text"]),
        {"type": "pill", "id": "tm_pause", "text": "暂停",
         "x": 185, "y": 350, "w": 110, "h": 44, "color": STYLE["yellow"]},
        {"type": "pill", "id": "tm_cancel", "text": "取消",
         "x": 300, "y": 350, "w": 110, "h": 44, "color": STYLE["ring"]},
    ]),
    _page("app_calc", "计算器", [
        _txt(0, "128", 330, 150, 40, STYLE["text"], anchor="rm"),
        {"type": "grid", "id": "ca_keys",
         "cells": ["C", "±", "%", "÷",
                   "7", "8", "9", "×",
                   "4", "5", "6", "-",
                   "1", "2", "3", "+",
                   "0", ".", "="],
         "cols": 4, "x0": 118, "y0": 195, "cw": 56, "ch": 44, "gap": 6,
         "size": 22, "bg": "#1E1E28", "fg": STYLE["text"],
         "accent_cells": ["="], "accent_color": STYLE["accent"]},
    ]),
    _page("app_compass", "指南针", [
        {"type": "ring", "id": "cp_ring", "cx": 233, "cy": 248, "r": 105,
         "width": 3, "pct": 1.0, "color": STYLE["tick"], "bg": STYLE["tick"]},
        _txt(0, "N", 233, 128, 24, STYLE["accent"]),
        _txt(1, "E", 353, 248, 22, STYLE["sub"]),
        _txt(2, "S", 233, 372, 22, STYLE["sub"]),
        _txt(3, "W", 113, 248, 22, STYLE["sub"]),
        _txt(4, "NE", 318, 163, 16, STYLE["sub"]),
        _txt(5, "SE", 318, 333, 16, STYLE["sub"]),
        _txt(6, "SW", 148, 333, 16, STYLE["sub"]),
        _txt(7, "NW", 148, 163, 16, STYLE["sub"]),
        _txt(8, "135°", 233, 248, 40, STYLE["text"]),
        _txt(9, "东南", 233, 283, 18, STYLE["sub"]),
    ]),
    _page("app_findphone", "找手机", [
        {"type": "roundrect", "id": "fp_phone", "cx": 233, "cy": 172,
         "w": 44, "h": 66, "radius": 9, "color": STYLE["sub"]},
        _txt(1, "已连接手机 · 信号强", 233, 235, 20, STYLE["sub"]),
        {"type": "pill", "id": "fp_ring", "text": "让手机响铃",
         "x": 233, "y": 305, "w": 190, "h": 48, "color": STYLE["blue"]},
        _txt(2, "断连超过 5 分钟提醒（开关候选）", 233, 362, 15, STYLE["sub"]),
    ]),
    _page("app_settings", "设置", [
        {"type": "rowlist", "id": "se_list",
         "rows": [["亮度", ">"], ["声音与振动", ">"], ["表盘样式", ">"],
                  ["蓝牙连接", "已连"], ["勿扰模式", "关"], ["系统关于", ">"]],
         "y0": 150, "row_h": 46, "w": 290, "size": 20},
    ]),

    # ---- 子页（2026-10-22 用户拍板"补子页设计"，回第①步追加）----
    _page("alarm_editor", "编辑闹钟", [
        {"type": "stepper", "id": "ae_hour", "x": 175, "y": 190, "dir": "both",
         "bg": STYLE["ring"]},
        {"type": "stepper", "id": "ae_min", "x": 291, "y": 190, "dir": "both",
         "bg": STYLE["ring"]},
        _txt(0, "07", 175, 190, 64, STYLE["text"]),
        _txt(1, ":", 233, 183, 44, STYLE["sub"]),
        _txt(2, "00", 291, 190, 64, STYLE["text"]),
        {"type": "chips", "id": "ae_days",
         "cells": ["一", "二", "三", "四", "五", "六", "日"], "on": [0, 1, 2, 3, 4],
         "cx": 233, "y": 296, "cw": 40, "ch": 40, "gap": 8},
        {"type": "rowlist", "id": "ae_opts",
         "rows": [["标签", "工作"], ["重复", "工作日"]],
         "y0": 326, "row_h": 40, "w": 240, "size": 18},
        {"type": "pill", "id": "ae_save", "text": "保存",
         "x": 233, "y": 424, "w": 150, "h": 44, "color": STYLE["green"]},
    ], back_to="app_alarm"),
    _page("set_brightness", "亮度", [
        {"type": "slider", "id": "br_slider", "y": 210, "w": 250,
         "pct": 0.7, "color": STYLE["yellow"]},
        _txt(0, "70%", 233, 262, 22, STYLE["sub"]),
        {"type": "switch", "id": "br_auto", "text": "自动亮度",
         "cx": 233, "y": 322, "on": True},
    ], back_to="app_settings"),
    _page("set_sound", "声音与振动", [
        {"type": "slider", "id": "sd_vol", "y": 180, "w": 250,
         "pct": 0.5, "color": STYLE["blue"]},
        _txt(0, "提示音量 50%", 233, 230, 20, STYLE["sub"]),
        {"type": "switch", "id": "sd_cue", "text": "触摸提示音",
         "cx": 233, "y": 290, "on": True},
        {"type": "switch", "id": "sd_vib", "text": "振动提醒",
         "cx": 233, "y": 348, "on": False},
    ], back_to="app_settings"),
    _page("set_facestyle", "表盘样式", [
        {"type": "facepick", "id": "fs_items", "names": ["简约数字", "运动圆环", "星空"],
         "active": 0, "cx": 233, "y": 230, "r": 56, "gap": 130},
        {"type": "pill", "id": "fs_apply", "text": "应用",
         "x": 233, "y": 360, "w": 150, "h": 44, "color": STYLE["accent"]},
    ], back_to="app_settings"),
    _page("set_bt", "蓝牙连接", [
        _txt(0, "已连接", 233, 140, 24, STYLE["green"]),
        _txt(1, "yjt-Watch · Xiaomi 14", 233, 174, 17, STYLE["sub"]),
        {"type": "rowlist", "id": "bt_others",
         "rows": [["HUAWEI FreeBuds", "配对"], ["MacBook-Pro", "配对"]],
         "y0": 210, "row_h": 44, "w": 280, "size": 18},
        {"type": "pill", "id": "bt_disc", "text": "断开连接",
         "x": 233, "y": 360, "w": 160, "h": 44, "color": STYLE["ring"]},
    ], back_to="app_settings"),
    _page("set_dnd", "勿扰模式", [
        {"type": "switch", "id": "dn_on", "text": "勿扰",
         "cx": 233, "y": 165, "on": False},
        {"type": "rowlist", "id": "dn_sched",
         "rows": [["定时开启", "关"], ["时间段", "23:00-07:00"]],
         "y0": 215, "row_h": 48, "w": 270, "size": 19},
        _txt(0, "开启后静默通知与触感", 233, 350, 16, STYLE["sub"]),
    ], back_to="app_settings"),
    _page("set_about", "系统关于", [
        {"type": "rowlist", "id": "ab_list",
         "rows": [["固件版本", "v1.0.0"], ["型号", "WT-466C"], ["序列号", "A2486…"],
                  ["存储", "34% 已用"], ["电池", "80%"]],
         "y0": 140, "row_h": 46, "w": 290, "size": 19},
        {"type": "pill", "id": "ab_update", "text": "检查更新",
         "x": 233, "y": 400, "w": 160, "h": 44, "color": STYLE["blue"]},
    ], back_to="app_settings"),
]

# ---------------------------------------------------------------------------
# 控件注册表（第②步口径同源数据）：(页内号, ids, 描述, 跳转, 类型, 输出去向)
# 跳转=""＝无跳页（本页状态/硬件动作）。类型→徽标前缀：
#   1=按钮 2=开关 3=滑条 4=滚轮 5=步进 6=chips 7=按键网格（每类独立连续编号）
# 输出去向：硬件=驱动传感器/背光/蜂鸣/马达/BLE 手机等外部 ⇒ 红；UI=界面内部切换 ⇒ 绿。
# design_annotate.py 按此画框+分类序号徽标（红/绿），跳转关系另出树状图 _tree.svg。
# ids 支持 "a+" 前缀=同组多控件共用一个序号。
# ---------------------------------------------------------------------------

CATS = {"按钮": 1, "开关": 2, "滑条": 3, "滚轮": 4, "步进": 5, "chips": 6, "按键网格": 7}

H = "硬件"
U = "UI"

CONTROLS = {
    "applist": [(3, ["al_roller"], "滚轮·整行可点", "14 个 app_* 页", "滚轮", U)],
    "app_sport": [(4, ["back"], "返回", "applist", "按钮", U), (5, ["sp_start"], "开始运动钮", "", "按钮", U)],
    "app_hr": [(6, ["back"], "返回", "applist", "按钮", U)],
    "app_sleep": [(7, ["back"], "返回", "applist", "按钮", U)],
    "app_spo2": [(8, ["back"], "返回", "applist", "按钮", U),
                 (9, ["so_measure"], "测量钮", "", "按钮", H)],
    "app_weather": [(10, ["back"], "返回", "applist", "按钮", U)],
    "app_msg": [(11, ["back"], "返回", "applist", "按钮", U), (12, ["ms_clear"], "全部清除钮", "", "按钮", U)],
    "app_music": [(13, ["back"], "返回", "applist", "按钮", U),
                  (14, ["mu_ctrl"], "播控三钮", "", "按钮", H)],
    "app_alarm": [(15, ["back"], "返回", "applist", "按钮", U), (16, ["al_list"], "行开关×3", "", "开关", U),
                  (17, ["al_add"], "添加钮", "alarm_editor", "按钮", U)],
    "alarm_editor": [(31, ["back"], "返回", "app_alarm", "按钮", U),
                     (32, ["ae_hour+", "ae_min+"], "时分步进", "", "步进", U),
                     (33, ["ae_days"], "星期 chips×7", "", "chips", U),
                     (34, ["ae_save"], "保存钮", "app_alarm", "按钮", U)],
    "app_stopwatch": [(18, ["back"], "返回", "applist", "按钮", U), (19, ["sw_start"], "开始/暂停", "", "按钮", U),
                      (20, ["sw_reset"], "复位", "", "按钮", U)],
    "app_timer": [(21, ["back"], "返回", "applist", "按钮", U), (22, ["tm_pause"], "暂停", "", "按钮", U),
                  (23, ["tm_cancel"], "取消", "", "按钮", U)],
    "app_calc": [(24, ["back"], "返回", "applist", "按钮", U), (25, ["ca_keys"], "19 键网格", "", "按键网格", U)],
    "app_compass": [(26, ["back"], "返回", "applist", "按钮", U)],
    "app_findphone": [(27, ["back"], "返回", "applist", "按钮", U),
                      (28, ["fp_ring"], "响铃钮", "BLE→手机", "按钮", H)],
    "app_settings": [(29, ["back"], "返回", "applist", "按钮", U),
                     (30, ["se_list"], "6 行入口", "set_brightness/sound/facestyle/bt/dnd/about", "按钮", U)],
    "set_brightness": [(35, ["back"], "返回", "app_settings", "按钮", U),
                       (36, ["br_slider"], "亮度滑条", "", "滑条", H),
                       (37, ["br_auto"], "自动亮度开关", "", "开关", H)],
    "set_sound": [(38, ["back"], "返回", "app_settings", "按钮", U),
                  (39, ["sd_vol"], "音量滑条", "", "滑条", H),
                  (40, ["sd_cue+", "sd_vib"], "开关×2", "", "开关", H)],
    "set_facestyle": [(41, ["back"], "返回", "app_settings", "按钮", U),
                      (42, ["fs_items"], "表盘缩选×3", "", "按钮", U),
                      (43, ["fs_apply"], "应用钮", "tab_main.tab0(换表盘)", "按钮", U)],
    "set_bt": [(44, ["back+", "bt_disc"], "返回 / 断开连接", "app_settings / BLE 断开", "按钮", H)],
    "set_dnd": [(45, ["back+", "dn_on"], "返回 / 勿扰开关", "app_settings", "开关", U)],
    "set_about": [(46, ["back+", "ab_update"], "返回 / 检查更新", "app_settings / 手机通道", "按钮", H)],
}


def widget_bbox(page, w):
    """控件外接框（设计图坐标系）；返回 None=无法定位（不出框）。"""
    t, i = w["type"], w.get("id", "?")
    if t == "back":
        return (w["x"] - 20, w["y"] - 22, w["x"] + 20, w["y"] + 22)
    if t == "label":
        return None
    if t == "roller":
        return (118, 132, 368, 424)
    if t == "pill":
        return (w["x"] - w["w"] / 2 - 3, w["y"] - w["h"] / 2 - 3,
                w["x"] + w["w"] / 2 + 3, w["y"] + w["h"] / 2 + 3)
    if t == "rowlist":
        cx = SCREEN["cx"]
        return (cx - w["w"] / 2 - 6, w["y0"] - 4,
                cx + w["w"] / 2 + 6, w["y0"] + len(w["rows"]) * w["row_h"] + 4)
    if t == "grid":
        nr = (len(w["cells"]) + w["cols"] - 1) // w["cols"]
        return (w["x0"] - 4, w["y0"] - 4,
                w["x0"] + w["cols"] * (w["cw"] + w["gap"]) - w["gap"] + 4,
                w["y0"] + nr * (w["ch"] + w["gap"]) - w["gap"] + 4)
    if t == "controls":
        n = len(w["shapes"])
        return (w["cx"] - (n - 1) / 2.0 * w["gap"] - 34, w["y"] - 24,
                w["cx"] + (n - 1) / 2.0 * w["gap"] + 34, w["y"] + 24)
    if t in ("slider", "progress"):
        x0 = w.get("cx", SCREEN["cx"]) - w["w"] / 2.0
        return (x0 - 6, w["y"] - 20, x0 + w["w"] + 6, w["y"] + 20)
    if t == "switch":
        return (w["cx"] - 60, w["y"] - 48, w["cx"] + 60, w["y"] + 20)
    if t == "chips":
        n = len(w["cells"])
        total = n * w["cw"] + (n - 1) * w["gap"]
        return (w["cx"] - total / 2 - 5, w["y"] - w["ch"] / 2 - 5,
                w["cx"] + total / 2 + 5, w["y"] + w["ch"] / 2 + 5)
    if t == "facepick":
        n = len(w["names"])
        total = (n - 1) * w["gap"] + 2 * w["r"]
        return (w["cx"] - total / 2 - 5, w["y"] - w["r"] - 5,
                w["cx"] + total / 2 + 5, w["y"] + w["r"] + 28)
    if t == "stepper":
        return (w["x"] - 26, w["y"] - 66, w["x"] + 26, w["y"] + 66)
    if t in ("bars", "segbar", "legend"):
        return None
    return (w.get("x", w.get("cx", 0)) - 30, w.get("y", w.get("cy", 0)) - 30,
            w.get("x", w.get("cx", 0)) + 30, w.get("y", w.get("cy", 0)) + 30)


# 字体条目（第④步预生成前按 P-0125 原生形态填：renderingEngine=LVGL + lvglRanges 数字表）
FONTS = {}

# 下次跑仿真前需同步清单：（当前为空；跳过仿真时在此登记 L4 期望值、夹具坐标等）
