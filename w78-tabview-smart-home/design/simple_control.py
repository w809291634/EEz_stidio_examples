# -*- coding: utf-8 -*-
"""简化主控 + 房间页设计图：主控（场景+房间），房间页（设备方格）。"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "designer_simple")
W, H = 2520, 720

BG, CARD, CARD2, EDGE = "#05080F", "#151B24", "#1C2430", "#273140"
T1, T2, T3 = "#F4F7FB", "#B9C4D4", "#75859C"
ACCENT, GREEN, RED, TEAL = "#F2B45C", "#5FD3A6", "#FF7A6B", "#5FD3C6"
BLUE = "#7FB3FF"
PURPLE = "#C08CFF"

# 控件分类色 = 单一口径（跳转图 / 预览图 / 标注图共用）
CAT_COLORS = {
    "nav": ACCENT,      # 房间卡：跳转
    "back": TEAL,       # 返回按钮
    "scene": PURPLE,    # 场景按钮：执行不跳页
    "toggle": GREEN,    # 开关：接硬件
    "slider": BLUE,     # 滑条：接硬件
    "read": T3,         # 只读传感：不接行为
}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def r(x, y, w, h, fill, stroke="none", rx=8):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}"/>')


def t(x, y, s, size=10, color=T2, weight="400", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')


def line(x1, y1, x2, y2, color=EDGE, w=1):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{w}"/>')


def card(x, y, w, h, rx=12):
    return r(x, y, w, h, CARD, EDGE, rx)


def btn(x, y, w, h, label, fill=ACCENT, fg=BG, size=11, sub=""):
    out = [r(x, y, w, h, fill, "none", h / 2),
           t(x + w / 2, y + h / 2 + size * 0.35, label, size, fg, "600", "middle")]
    if sub:
        out.append(t(x + w / 2, y + h / 2 + size * 0.35 + 13, sub, 8,
                     fg if fg == T1 else "#2A2418", "400", "middle"))
    return "".join(out)


def toggle(x, y, on=True):
    return (r(x, y, 44, 24, ACCENT if on else "#222B38", "none", 12) +
            r(x + (22 if on else 2), y + 2, 20, 20, "#FFFFFF", "none", 10))


def slider(x, y, w, p):
    return (r(x, y, w, 6, "#222B38", "none", 3) +
            r(x, y, w * p, 6, ACCENT, "none", 3) +
            f'<circle cx="{x + w * p}" cy="{y + 3}" r="7" fill="#FFFFFF" '
            f'stroke="{BG}" stroke-width="2"/>')


def tag(x, y, text="只读"):
    return (r(x, y, 34, 16, CARD2, EDGE, 6) +
            t(x + 17, y + 11, text, 8, T3, "400", "middle"))


# 主控顶部 4 个二级页入口（设备 / 能耗 / 通知 / 设置）= 单一真值
HEADER_ENTRIES = [("设备", 540, 26, 56, 28), ("能耗", 600, 26, 56, 28),
                  ("通知", 660, 26, 56, 28), ("设置", 720, 26, 56, 28)]
SECURITY_PILL = (640, 86, 116, 20)


def header_home():
    out = [r(0, 0, 800, 480, BG),
           t(40, 44, "主控", 26, T1, "700"),
           t(40, 66, "晚上好，李然 · 5月18日 周一", 10, T3),
           t(268, 40, "22° 晴", 12, T2, "600"),
           t(268, 58, "室内 23.5° · 48%", 9, T3)]
    for (label, x, y, w, h) in HEADER_ENTRIES:
        out.append(btn(x, y, w, h, label, CARD2, T1, 9))
    out.append(r(700, 20, 14, 14, RED, "none", 7))
    out.append(t(707, 31, "2", 8, "#FFFFFF", "700", "middle"))
    out.append(line(40, 116, 760, 116))
    # status strip
    out.append(r(40, 84, 720, 24, CARD2, "none", 12))
    out.append(r(52, 92, 8, 8, GREEN, "none", 4))
    out.append(t(66, 100, "已布防 · 离家模式", 9, T2))
    out.append(t(250, 100, "12 个设备在线", 9, T3))
    out.append(t(420, 100, "4 个房间", 9, T3))
    out.append(btn(*SECURITY_PILL, "安防 ›", CARD2, TEAL, 8))
    return "".join(out)


def header_room(name, sub):
    out = [r(0, 0, 800, 480, BG),
           btn(*BACK_BOX, "‹ 主控", CARD2, T1, 9),
           t(128, 46, name, 24, T1, "700"),
           t(128, 66, sub, 10, T3),
           line(40, 88, 760, 88)]
    return "".join(out)


# 主控页 2x2 房间卡几何 = 单一真值（标注图 import 这里，不手抄）
ROOM_GRID = {"x0": 40, "dx": 360, "y0": 278, "dy": 98, "w": 340, "h": 86}
SCENE_ROW = {"x": 40, "y": 160, "w": 168, "h": 74, "dx": 180}
SCENES = [("回家", "12 个设备"), ("离家", "全屋关闭"),
          ("晚安", "6 个设备"), ("影院", "4 个设备")]


def room_card_box(i):
    g = ROOM_GRID
    return (g["x0"] + (i % 2) * g["dx"], g["y0"] + (i // 2) * g["dy"],
            g["w"], g["h"])


# 房间页设备方格几何 + 返回按钮几何 = 单一真值
TILE_GRID = {"x0": 40, "dx": 248, "y0": 124, "dy": 168, "w": 224, "h": 150}
BACK_BOX = (40, 28, 72, 28)


def tile_box(i):
    g = TILE_GRID
    return (g["x0"] + (i % 3) * g["dx"], g["y0"] + (i // 3) * g["dy"],
            g["w"], g["h"])


def scene_box(i):
    s = SCENE_ROW
    return (s["x"] + i * s["dx"], s["y"], s["w"], s["h"])


def main_frame():
    out = [header_home(),
           t(40, 148, "场景", 11, T3)]
    for i, (name, sub) in enumerate(SCENES):
        x, y, w, h = scene_box(i)
        out.append(btn(x, y, w, h, name,
                       ACCENT if i == 0 else CARD2, BG if i == 0 else T1,
                       14, sub))
    out.append(t(40, 264, "房间", 11, T3))
    rooms = [("客厅", "23.5°", "5 个设备 · 湿度 48%"),
             ("主卧", "24.0°", "2 个设备 · 湿度 50%"),
             ("厨房", "22.8°", "3 个设备 · 湿度 55%"),
             ("浴室", "23.1°", "1 个设备 · 湿度 62%")]
    for i, (name, temp, sub) in enumerate(rooms):
        x, y, w, h = room_card_box(i)
        out += [card(x, y, w, h),
                t(x + 14, y + 24, name, 13, T1, "600"),
                t(x + 14, y + 54, temp, 22, T1, "700"),
                t(x + 14, y + 72, sub, 8, T3),
                t(x + w - 26, y + 46, "›", 22, ACCENT, "400", "end")]
    return "".join(out)


def tile(x, y, name, sub, value="", control="toggle", on=True, readonly=False,
         scene=False):
    out = [card(x, y, TILE_GRID["w"], TILE_GRID["h"])]
    out.append(r(x + 14, y + 14, 26, 26, CARD2, "none", 8))
    out.append(t(x + 27, y + 32, name[:1], 12, ACCENT if not readonly else T3,
                 "700", "middle"))
    out.append(t(x + 50, y + 24, name, 11, T1, "600"))
    out.append(t(x + 50, y + 40, sub, 8, T3))
    if value:
        out.append(t(x + 14, y + 76, value, 20, T1, "700"))
    dx, dy, dw, dh = TILE_DETAIL_BTN
    out.append(btn(x + dx, y + dy, dw, dh, "详情", CARD2, ACCENT, 8))
    if readonly:
        out.append(tag(x + 104, y + 16))
        out.append(t(x + 14, y + 124, "状态只读", 8, T3))
    elif scene:
        out.append(btn(x + 14, y + 104, 196, 32, "执行", CARD2, ACCENT, 9))
    elif control == "toggle":
        out.append(toggle(x + 166, y + 104, on))
    elif control == "slider":
        out.append(slider(x + 14, y + 112, 196, 0.7))
        out.append(t(x + 14, y + 104, "开合 70%", 8, T3))
    return "".join(out)


def room_frame(name, sub, data):
    """房间页模板：返回主控 + 3x2 设备方格。data 每项 = tile() 的位置参数。"""
    out = [header_room(name, sub),
           t(40, 112, "设备", 11, T3)]
    for i, d in enumerate(data):
        x, y, _w, _h = tile_box(i)
        out.append(tile(x, y, *d))
    return "".join(out)


# 4 个房间的设备方格 = 单一真值（房间页设计图与跳转/预览图共用）
ROOM_TILES = {
    "客厅": [
        ("主灯", "客厅 · 3000K", "80%", "toggle", True, False, False),
        ("落地灯", "客厅 · 暖光", "", "toggle", False, False, False),
        ("窗帘", "客厅", "", "slider", True, False, False),
        ("空调", "制冷 · 自动", "23.5°", "toggle", True, False, False),
        ("温湿度", "客厅", "23.5° / 48%", None, False, True, False),
        ("摄像头", "1080P · 已加密", "实时", None, False, True, False),
    ],
    "主卧": [
        ("床头灯", "主卧 · 暖光", "20%", "toggle", True, False, False),
        ("主灯", "主卧", "", "toggle", False, False, False),
        ("窗帘", "主卧", "", "slider", False, False, False),
        ("空调", "制冷 · 静音", "24.0°", "toggle", True, False, False),
        ("温湿度", "主卧", "24.0° / 50%", None, False, True, False),
        ("晚安模式", "全屋灯关 · 布防", "", None, False, False, True),
    ],
    "厨房": [
        ("主灯", "厨房", "", "toggle", False, False, False),
        ("插座", "厨房", "", "toggle", True, False, False),
        ("燃气传感", "厨房 · 待命", "正常", None, False, True, False),
    ],
    "浴室": [
        ("暖灯", "浴室", "", "toggle", False, False, False),
        ("排风", "浴室", "", "toggle", True, False, False),
        ("漏水传感", "浴室 · 待命", "正常", None, False, True, False),
    ],
}

# 表头副标题沿用已核对过的文案（客厅/主卧的“N 个设备”待用户确认后再改）
ROOM_SUBS = {
    "客厅": "5 个设备 · 23.5°C · 湿度 48%",
    "主卧": "2 个设备 · 24.0°C · 湿度 50%",
    "厨房": "3 个设备 · 22.8°C · 湿度 55%",
    "浴室": "3 个设备 · 23.1°C · 湿度 62%",
}

ROOM_ORDER = ["客厅", "主卧", "厨房", "浴室"]

# ---- 二级页几何（标注图 import，不手抄）----
TILE_DETAIL_BTN = (158, 12, 52, 24)     # 设备格内「详情」按钮（相对格子原点）
SUB_BACK_BOX = (40, 28, 96, 28)
DETAIL_BOXES = {
    "power": (296, 126, 60, 32),
    "bright": (52, 205, 316, 26),
    "cct": (52, 260, 316, 26),
    "timer1": (696, 130, 60, 32),
    "timer2": (696, 180, 60, 32),
    "timer_add": (420, 232, 120, 32),
    "info": (40, 300, 720, 140),
}
NOTIFY_BOXES = {
    "read_all": (620, 28, 140, 28),
    "rows": [(660, 126, 80, 28), (660, 210, 80, 28), (660, 294, 80, 28)],
    "clear": (40, 372, 120, 32),
}
ENERGY_BOXES = {
    "today": (500, 28, 72, 28),
    "week": (580, 28, 72, 28),
    "chart": (40, 104, 440, 300),
    "share": (500, 104, 260, 300),
}
SETTINGS_BOXES = {
    "dark": (696, 118, 60, 32),
    "notify": (696, 178, 60, 32),
    "lock": (500, 244, 240, 22),
    "net": (40, 276, 720, 52),
    "about": (40, 336, 720, 52),
    "reset": (40, 400, 140, 32),
}
SETTINGS_ROWS = [("深色模式", "界面配色"), ("通知提醒", "主控铃铛角标"),
                 ("自动锁屏", "无操作后 60 秒")]


def sub_header(title, sub, back_label):
    return [r(0, 0, 800, 480, BG),
            btn(*SUB_BACK_BOX, back_label, CARD2, T1, 9),
            t(152, 46, title, 24, T1, "700"),
            t(152, 66, sub, 10, T3),
            line(40, 88, 760, 88)]


def detail_frame():
    b = DETAIL_BOXES
    out = sub_header("主灯", "客厅 · 3000K · 在线", "‹ 客厅")
    out += [card(40, 104, 340, 180),
            t(60, 140, "电源", 12, T2, "600"),
            toggle(*b["power"][:2], True),
            t(60, 200, "亮度", 12, T2, "600"),
            slider(60, 218, 300, 0.8), t(300, 200, "80%", 10, T3),
            t(60, 258, "色温", 12, T2, "600"),
            slider(60, 276, 300, 0.45), t(300, 258, "3000K", 10, T3),
            card(400, 104, 360, 180),
            t(420, 130, "定时", 12, T2, "600"),
            t(420, 152, "22:30 自动关灯", 10, T1),
            toggle(*b["timer1"][:2], True),
            t(420, 202, "07:00 缓慢亮起", 10, T1),
            toggle(*b["timer2"][:2], False),
            btn(*b["timer_add"], "添加定时", CARD2, ACCENT, 9),
            card(40, 300, 720, 140),
            t(60, 328, "设备信息（只读）", 12, T2, "600"),
            t(60, 356, "信号强度", 9, T3), t(60, 376, "强", 16, T1, "600"),
            t(240, 356, "固件版本", 9, T3), t(240, 376, "1.4.2", 16, T1, "600"),
            t(420, 356, "累计用电", 9, T3), t(420, 376, "36.8 kWh", 16, T1, "600"),
            t(620, 356, "最近上报", 9, T3), t(620, 376, "2 分钟前", 16, T1, "600"),
            tag(690, 320)]
    return "".join(out)


def notify_frame():
    b = NOTIFY_BOXES
    out = sub_header("通知", "3 条 · 2 条未读", "‹ 主控")
    out.append(btn(*b["read_all"], "全部已读", CARD2, ACCENT, 9))
    rows = [("客厅主灯已开启", "刚才 · 来自 回家场景", True),
            ("浴室漏水传感离线", "12 分钟前 · 需检查", True),
            ("昨晚用电量 8.2 kWh", "昨天 23:00", False)]
    for i, (title, sub, unread) in enumerate(rows):
        y = 104 + i * 84
        out += [card(40, y, 720, 72),
                r(56, y + 20, 8, 8, ACCENT if unread else EDGE, "none", 4),
                t(74, y + 30, title, 12, T1, "600"),
                t(74, y + 50, sub, 9, T3)]
        rx, ry, rw, rh = b["rows"][i]
        out.append(btn(rx, ry, rw, rh, "查看", CARD2, ACCENT, 9))
    out.append(btn(*b["clear"], "清空列表", CARD2, T1, 9))
    return "".join(out)


def energy_frame():
    b = ENERGY_BOXES
    out = sub_header("能源", "今日 12.4 kWh · 本月 268 kWh", "‹ 主控")
    out += [btn(*b["today"], "今日", ACCENT, BG, 9),
            btn(*b["week"], "本周", CARD2, T1, 9),
            card(40, 104, 440, 300),
            t(60, 132, "近 7 日用电（只读）", 12, T2, "600")]
    vals = [0.45, 0.62, 0.38, 0.78, 0.55, 0.9, 0.66]
    for i, v in enumerate(vals):
        h = 180 * v
        out.append(r(70 + i * 56, 360 - h, 36, h, ACCENT if i == 5 else CARD2,
                     "none", 4))
        out.append(t(88 + i * 56, 378, f"{18 + i}日", 8, T3, "400", "middle"))
    out += [card(500, 104, 260, 300),
            t(520, 132, "房间占比（只读）", 12, T2, "600")]
    for i, (room, pct) in enumerate([("客厅", "38%"), ("主卧", "27%"),
                                     ("厨房", "22%"), ("浴室", "13%")]):
        y = 156 + i * 56
        out += [t(520, y, room, 10, T1, "600"),
                t(740, y, pct, 10, T2, "600", "end"),
                r(520, y + 8, 220, 6, "#222B38", "none", 3),
                r(520, y + 8, 220 * int(pct[:-1]) / 100.0, 6, ACCENT, "none", 3)]
    return "".join(out)


def settings_frame():
    b = SETTINGS_BOXES
    out = sub_header("设置", "Haven Home · 网关在线", "‹ 主控")
    for i, (name, sub) in enumerate(SETTINGS_ROWS):
        y = 104 + i * 60
        out += [card(40, y, 720, 52),
                t(60, y + 24, name, 12, T1, "600"),
                t(60, y + 40, sub, 8.5, T3)]
    out.append(toggle(*b["dark"][:2], True))
    out.append(toggle(*b["notify"][:2], True))
    out += [slider(520, 252, 200, 0.5)]
    for i, (name, val) in enumerate([("网络", "Wi-Fi · 已连接 5G · 信号强"),
                                     ("关于", "版本 1.0.0 · 构建 2026-05-18")]):
        y = 276 + i * 60
        out += [card(40, y, 720, 52),
                t(60, y + 24, name, 12, T1, "600"),
                t(60, y + 40, val, 8.5, T3), tag(700, y + 18)]
    out.append(btn(*b["reset"], "恢复默认", CARD2, RED, 9))
    return "".join(out)


def living_frame():
    return room_frame("客厅", ROOM_SUBS["客厅"], ROOM_TILES["客厅"])


def bedroom_frame():
    return room_frame("主卧", ROOM_SUBS["主卧"], ROOM_TILES["主卧"])


def main():
    os.makedirs(OUT, exist_ok=True)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="Microsoft YaHei,Noto Sans SC,'
        f'PingFang SC,sans-serif">',
        r(0, 0, W, H, BG, "none", 0),
        t(40, 46, "Haven Home · 主控 + 房间页设计", 28, T1, "700"),
        t(40, 70, "主控 = 场景 + 房间；房间页 = 设备小方格；先不做侧栏和复杂跳转",
          12, T2),
        t(40, 96, "主控", 10, ACCENT),
        t(860, 96, "客厅（房间模板）", 10, ACCENT),
        t(1680, 96, "主卧（同一模板，换设备）", 10, ACCENT),
    ]
    out.append(f'<g transform="translate(40,110)">{main_frame()}</g>')
    out.append(f'<g transform="translate(860,110)">{living_frame()}</g>')
    out.append(f'<g transform="translate(1680,110)">{bedroom_frame()}</g>')
    out += [t(40, 636, "规则", 14, T1, "700"),
            t(40, 660, "主控只放场景和房间；房间卡整块可点，进入后用左上角“‹ 主控”返回。",
              10, T2),
            t(40, 680, "房间内每格一个设备：灯/窗帘/空调可操作，温湿度/摄像头只读；"
                       "不做每格透明跳转。", 10, T2),
            t(40, 700, "动态先不做；确认布局后再决定是否保留回家/晚安等 3 个场景动效。",
              10, T3)]
    out.append("</svg>")
    svg = os.path.join(OUT, "_control_concept.svg")
    io.open(svg, "w", encoding="utf-8", newline="\n").write("".join(out))
    print("written", svg)
    try:
        import cairosvg
        png = os.path.join(OUT, "_control_concept.png")
        cairosvg.svg2png(url=svg, write_to=png, output_width=2000,
                         output_height=571)
        print("written", png)
    except Exception as e:
        print("png skip", e)


if __name__ == "__main__":
    main()
