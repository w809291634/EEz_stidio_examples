# -*- coding: utf-8 -*-
"""apps.py —— 22 行应用表的**唯一事实源**

一张表喂三个产物，避免"屏上字与字体子集不一致"这类跨文件漂移：
  1) build_example.py  取所有中文名 → 算 UI_CJK（字体子集）
  2) gen_assets.py     生成 22 个图标 .c + app_rows.c（native 用的表）
  3) design/preflight.py 反查屏上每个字都在子集内

表内容与桌面的 Design Watch 工程 `design/build_watch_ui.py::applist_rows()`
逐行一致（图标名 / 中文名 / 目标页 id），便于两个工程对照观感。
"""

# (icon_id, 中文名, 目标页 id)
APPS = [
    ("ic_sport_mode",   "运动模式",  "SportMode"),
    ("ic_sport_record", "运动记录",  "SportRecord"),
    ("ic_step",         "计步",      "Step"),
    ("ic_physio",       "理疗",      "Physio"),
    ("ic_hr",           "心率",      "HeartRate"),
    ("ic_spo2",         "血氧",      "Spo2"),
    ("ic_bp",           "血压",      "BloodPressure"),
    ("ic_breath",       "呼吸训练",  "Breath"),
    ("ic_sleep",        "睡眠",      "Sleep"),
    ("ic_calendar",     "日历",      "Calendar"),
    ("ic_weather",      "天气",      "Weather"),
    ("ic_camera",       "拍照",      "Camera"),
    ("ic_alarm",        "闹钟",      "Alarm"),
    ("ic_stopwatch",    "秒表",      "Stopwatch"),
    ("ic_calculator",   "计算器",    "Calculator"),
    ("ic_timer",        "定时器",    "Timer"),
    ("ic_raise_hand",   "抬腕亮屏",  "RaiseHand"),
    ("ic_find_phone",   "查找手机",  "FindPhone"),
    ("ic_screen_time",  "亮屏时间",  "ScreenTime"),
    ("ic_language",     "语言",      "Language"),
    ("ic_qrcode",       "二维码",    "QrCode"),
    ("ic_settings",     "设置",      "Settings"),
]

# 本工程自己会往屏上写的其它中文（状态行前缀等），一并进子集
EXTRA_UI_TEXT = "已打开: 应用列表 就绪 中心"


def ui_cjk_chars():
    """屏上会出现的全部汉字（去重后按码位排序，便于 diff 字体子集）"""
    s = set()
    for _icon, name, _target in APPS:
        s |= {c for c in name if ord(c) > 0x7F}
    s |= {c for c in EXTRA_UI_TEXT if ord(c) > 0x7F}
    return "".join(sorted(s))
