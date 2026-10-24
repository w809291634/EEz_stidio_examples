#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 WiFi 连接模板的全部过程设计图（单一网格常量驱动）。

输出目录：design/mockups/
  01 列表主态（分组）  02 扫描中   03 空态      04 密码页
  05 密码页+键盘       06 连接中   07 连接失败  08 忘记确认
  09 组件内嵌容器

对齐约束（每次生成断言）：
  - 行高/行距统一，列表不溢出
  - 两行文本基线统一（row+19 / row+34）
  - 右侧状态槽：所有胶囊右缘 = RIGHT_EDGE，垂直中心 = row+23
  - 锁列 x 统一且垂直居中
"""
import os

# ---------------- 网格常量（实现时照抄这些数字） ----------------
W, H = 480, 320
PAD = 16
ROW_X, ROW_W = PAD, W - PAD * 2      # 16 / 448
ROW_H, ROW_GAP = 46, 6
PITCH = ROW_H + ROW_GAP              # 52
BAR_X = ROW_X + 14                   # 30
TEXT_X = ROW_X + 42                  # 58
RIGHT_EDGE = ROW_X + ROW_W - 14      # 450：状态槽统一右缘
LOCK_X = RIGHT_EDGE - 82             # 368：锁列
SSID_BASE, META_BASE = 19, 34        # 相对行顶
STATUS_CY = 23                       # 相对行顶的状态中心
GRP1_LABEL_Y, GRP1_TOP = 62, 68
GRP2_LABEL_Y, GRP2_TOP = 184, 190
BOTTOM_Y = 306

# ---------------- 配色 ----------------
BG = "#0B0F1A"
ROW_BG = "#101A28"
LINE = "#26314A"
LINE_CONN = "#2E9F79"
PRI = "#5B8CFF"
PRI_TXT = "#9DB8FF"
SUC = "#3DDC97"
FAIL = "#E06A6A"
FAIL_EDGE = "#7A3B46"
FAIL_BG = "#2A1620"
T1, T2, T3 = "#F0F4FC", "#8A99B3", "#5C6A85"
DIM = "#26314A"
FIELD_BG = "#0E1524"
KEY_BG = "#282B30"   # = LVGL 暗色主题 DARK_COLOR_CARD（EEZ 的 localStyles 只出
                     #   LV_PART_MAIN，键帽色改不动，设计图按渲染真值对齐）
PILL_BG = "#161E30"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mockups")
EDGES = []          # 断言用：所有状态胶囊右缘


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self):
        self.o = []

    def rect(self, x, y, w, h, fill, rx=0, stroke=None, sw=0.5,
             dash=None, opacity=None):
        a = '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"' % (
            _n(x), _n(y), _n(w), _n(h), fill)
        if rx:
            a += ' rx="%s"' % _n(rx)
        if stroke:
            a += ' stroke="%s" stroke-width="%s"' % (stroke, _n(sw))
        if dash:
            a += ' stroke-dasharray="%s"' % dash
        if opacity:
            a += ' opacity="%s"' % opacity
        self.o.append("    " + a + "/>")

    def text(self, x, y, s, size=12, fill=T2, anchor=None, weight=None, ls=None):
        a = '<text x="%s" y="%s" fill="%s" font-size="%s"' % (
            _n(x), _n(y), fill, _n(size))
        if weight:
            a += ' font-weight="%s"' % weight
        if anchor:
            a += ' text-anchor="%s"' % anchor
        if ls:
            a += ' letter-spacing="%s"' % ls
        self.o.append("    " + a + ">%s</text>" % esc(s))

    def path(self, d, fill="none", stroke=None, sw=1.2, cap="round", opacity=None):
        a = '<path d="%s" fill="%s"' % (d, fill)
        if stroke:
            a += ' stroke="%s" stroke-width="%s"' % (stroke, _n(sw))
        if cap:
            a += ' stroke-linecap="%s" stroke-linejoin="round"' % cap
        if opacity:
            a += ' opacity="%s"' % opacity
        self.o.append("    " + a + "/>")

    def circle(self, cx, cy, r, fill, stroke=None, sw=1):
        a = '<circle cx="%s" cy="%s" r="%s" fill="%s"' % (_n(cx), _n(cy), _n(r), fill)
        if stroke:
            a += ' stroke="%s" stroke-width="%s"' % (stroke, _n(sw))
        self.o.append("    " + a + "/>")


def _n(v):
    if isinstance(v, float):
        return ("%.1f" % v).rstrip("0").rstrip(".")
    return str(v)


# ---------------- 组件 ----------------
def spinner(s, cx, cy, r, col=PRI):
    s.circle(cx, cy, r, "none", stroke="#2A3550", sw=2)
    s.path("M%s %s a%s %s 0 0 1 %s %s" % (_n(cx), _n(cy - r), _n(r), _n(r),
                                          _n(r), _n(r)), stroke=col, sw=2)


def bars(s, y, n, conn=False):
    heights = [5, 8, 11, 14]
    base = y + 34
    for b in range(4):
        on = b < n
        col = (SUC if conn else PRI) if on else DIM
        h = heights[b]
        s.rect(BAR_X + b * 6, base - h, 3.6, h, col)


def lock_icon(s, y, col=T2):
    s.rect(LOCK_X, y + 20, 10, 8, col, rx=1.6)
    s.path("M%d %d v-2.6 a2.6 2.6 0 0 1 5.2 0 v2.6" % (LOCK_X + 2, y + 20),
           stroke=col, sw=1.3)


def status_slot(s, y, status):
    """status = None | (kind, label)；kind: conn/saved/ing/fail/open"""
    if not status:
        return
    kind, label = status
    EDGES.append(RIGHT_EDGE)
    if kind == "open":
        s.text(RIGHT_EDGE, y + STATUS_CY + 3, label, 10, T3, anchor="end")
        return
    pw = {"conn": 52, "saved": 46, "ing": 50, "fail": 58}[kind]
    px = RIGHT_EDGE - pw
    fill, edge, col = {
        "conn": ("#0E2A22", LINE_CONN, SUC),
        "saved": ("#16203A", PRI, PRI_TXT),
        "ing": ("#16203A", PRI, PRI_TXT),
        "fail": (FAIL_BG, FAIL_EDGE, FAIL),
    }[kind]
    s.rect(px, y + STATUS_CY - 8, pw, 17, fill, rx=8.5, stroke=edge, sw=0.5)
    if kind == "saved":
        s.text(px + pw / 2, y + STATUS_CY + 3, label, 10, col, anchor="middle")
    else:
        s.circle(px + 10, y + STATUS_CY - 0.5, 2.5, col)
        s.text(px + 17, y + STATUS_CY + 3, label, 10, col)


def row(s, y, ssid, meta, nbars, lock=True, status=None, accent=None):
    """accent: None | 'conn' | 'fail' | 'ing'（描边强调）"""
    edge = {"conn": LINE_CONN, "fail": FAIL_EDGE, "ing": PRI}.get(accent, LINE)
    s.rect(ROW_X, y, ROW_W, ROW_H, ROW_BG, rx=10, stroke=edge,
           sw=1 if accent else 0.5)
    bars(s, y, nbars, conn=(accent == "conn"))
    s.text(TEXT_X, y + SSID_BASE, ssid, 14.5, T1)
    s.text(TEXT_X, y + META_BASE, meta, 11, T2)
    if lock:
        lock_icon(s, y)
    status_slot(s, y, status)


def group_label(s, y, label, trailing=None):
    s.text(PAD, y, label, 10.5, T3)
    if trailing:
        s.text(W - PAD, y, trailing, 10, T3, anchor="end")


# 控件的真实几何（标注脚本从这里取数，避免手抄漂移）
HEAD_BTN = (W - PAD - 64, 14, 64, 26)   # 与 build_example.HEAD_BTN 同值
EMPTY_BTN = (170, 256, 140, 34)
DIALOG_BOX = (70, 90, 340, 140)
DIALOG_BTN_L = (90, 182, 92, 32)
DIALOG_BTN_M = (186, 182, 92, 32)
DIALOG_BTN_R = (282, 182, 92, 32)


def header(s, sub, btn="刷新", busy=False):
    s.text(PAD, 26, "WiFi", 17, T1, weight="500")
    s.text(PAD, 42, sub, 11.5, T2)
    bx = W - PAD - 64
    s.rect(*HEAD_BTN, PILL_BG, rx=13, stroke=LINE, sw=0.5)
    if busy:
        spinner(s, bx + 15, 26, 5.5)
        s.text(bx + 40, 30, btn, 10.5, PRI_TXT, anchor="middle")
    else:
        s.text(bx + 32, 30, btn, 11, "#B9C6DC", anchor="middle")


def bottom_hint(s, text, color=T3):
    s.text(W / 2, BOTTOM_Y, text, 10.5, color, anchor="middle")


def back_bar(s, baseline=28):
    s.path("M25 17 l-6 6 6 6", stroke=T2, sw=1.6)
    s.text(33, baseline, "返回", 11.5, T2)


def eye(s, cx, cy, col=T2):
    s.path("M%s %s q7 -7 14 0 q-7 7 -14 0z" % (_n(cx - 7), _n(cy)),
           stroke=col, sw=1.2)
    s.circle(cx, cy, 2.2, col)


def toggle(s, x, y, on=False):
    fill = "#123A2E" if on else "#16203A"
    edge = LINE_CONN if on else LINE
    s.rect(x, y, 48, 26, fill, rx=13, stroke=edge, sw=0.5)
    s.circle(x + (34 if on else 14), y + 13, 9, SUC if on else T2)


def keyboard(s, top, key_h=36, gap=5, area=(8, W - 8)):
    x0, x1 = area
    avail = x1 - x0
    rows = [
        (["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"], 3),
        (["a", "s", "d", "f", "g", "h", "j", "k", "l"], 3),
        (["shift", "z", "x", "c", "v", "b", "n", "m", "del"], 3),
        (["123", "space", "完成"], 6),
    ]
    for ri, (keys, kg) in enumerate(rows):
        y = top + ri * (key_h + gap)
        if ri == 3:
            ws = [64, avail - 64 - 88 - 2 * kg, 88]
        elif ri == 2:
            mid = (avail - 2 * 54 - 2 * kg - 6 * kg) / 7.0
            ws = [54] + [mid] * 7 + [54]
        else:
            ws = [(avail - (len(keys) - 1) * kg) / float(len(keys))] * len(keys)
        total = sum(ws) + (len(ws) - 1) * kg
        cx = x0 + (avail - total) / 2.0
        for k, kw in zip(keys, ws):
            done = (k == "完成")
            s.rect(cx, y, kw, key_h, PRI if done else KEY_BG, rx=6,
                   stroke=None if done else "#212B42", sw=0.5)
            label = {"shift": "shift", "del": "del", "space": ""}.get(k, k)
            if label:
                s.text(cx + kw / 2, y + key_h / 2 + 4, label,
                       10 if len(label) > 1 else 11,
                       "#FFFFFF" if done else T1, anchor="middle")
            else:
                s.rect(cx + 24, y + key_h / 2 - 2.5,
                       kw - 48, 5, "#2C3852", rx=2.5)
            cx += kw + kg


def wifi_glyph(s, cx, cy, col=T3, dot=True):
    for rr in (48, 33, 18):
        s.path("M%d %d a%d %d 0 0 1 %d 0" % (cx - rr, cy, rr, rr, 2 * rr),
               stroke=col, sw=3)
    if dot:
        s.circle(cx, cy, 3.6, col)


# ---------------- 各屏内容 ----------------
def sc_list(s):
    header(s, "已发现 6 个网络")
    group_label(s, GRP1_LABEL_Y, "已连接 · 已保存")
    row(s, GRP1_TOP, "yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4,
        status=("conn", "已连接"), accent="conn")
    row(s, GRP1_TOP + PITCH, "1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4,
        status=("saved", "已保存"))
    group_label(s, GRP2_LABEL_Y, "可用网络", "共 6 个")
    row(s, GRP2_TOP, "YJT-1号楼办公", "WPA2 · -66 dBm · 2.4 GHz", 3)
    row(s, GRP2_TOP + PITCH, "Office-2G", "开放网络 · -74 dBm · 2.4 GHz", 2,
        lock=False, status=("open", "无需密码"))
    bottom_hint(s, "长按网络行可忘记已保存的密码")


def sc_scanning(s):
    header(s, "正在扫描附近网络…", "扫描中", busy=True)
    y = 62
    for i in range(4):
        s.rect(ROW_X, y, ROW_W, ROW_H, ROW_BG, rx=10, stroke=LINE, sw=0.5)
        for b in range(4):
            s.rect(BAR_X + b * 6, y + 34 - [5, 8, 11, 14][b],
                   3.6, [5, 8, 11, 14][b], DIM)
        s.rect(TEXT_X, y + 11, 118, 9, "#1B2438", rx=4)
        s.rect(TEXT_X, y + 26, 168, 7, "#18202F", rx=3.5)
        s.rect(RIGHT_EDGE - 46, y + STATUS_CY - 8, 46, 17, "#161E30", rx=8.5)
        y += PITCH
    # 状态只留标题栏一处（与 06 同一口径）；底部提示在实现里不存在。


def sc_empty(s):
    header(s, "已发现 0 个网络")
    wifi_glyph(s, W / 2, 168, T3)
    s.text(W / 2, 218, "未发现网络", 15, T1, anchor="middle")
    s.text(W / 2, 240, "请确认 WiFi 已开启，然后重新扫描", 11, T2, anchor="middle")
    s.rect(*EMPTY_BTN, PRI, rx=17)
    s.text(W / 2, 278, "重新扫描", 12, "#FFFFFF", anchor="middle")


def sc_connecting(s):
    _list_base(s, sub="正在连接 1号楼6层WiFi…",
               target_status=("ing", "连接中"), target_accent="ing")
    # 状态只留一处：标题栏副标题「正在连接 …」。
    # 旧版底部那行 spinner + 文案和键盘重叠（半页占到 320），已删。
    sheet(s, "connecting", ssid="1号楼6层WiFi", pwd="12345678")


def sc_failed(s):
    _list_base(s, target_status=("fail", "连接失败"), target_accent="fail")
    sheet(s, "failed", ssid="1号楼6层WiFi", pwd="12345678")


def sc_forget(s):
    header(s, "已发现 6 个网络")
    group_label(s, GRP1_LABEL_Y, "已连接 · 已保存")
    row(s, GRP1_TOP, "yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4,
        status=("conn", "已连接"), accent="conn")
    row(s, GRP1_TOP + PITCH, "1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4,
        status=("saved", "已保存"))
    group_label(s, GRP2_LABEL_Y, "可用网络", "共 6 个")
    row(s, GRP2_TOP, "YJT-1号楼办公", "WPA2 · -66 dBm · 2.4 GHz", 3)
    row(s, GRP2_TOP + PITCH, "Office-2G", "开放网络 · -74 dBm · 2.4 GHz", 2,
        lock=False, status=("open", "无需密码"))
    # 遮罩 + 确认卡
    s.rect(0, 0, W, H, "#05070D", rx=14, opacity="0.66")
    s.rect(60, 96, 360, 132, "#161E30", rx=14, stroke=LINE, sw=0.6)
    s.text(84, 130, "忘记此网络？", 14.5, T1, weight="500")
    s.text(84, 154, "将删除「yjt_dev_2.4G」已保存的密码，", 11, T2)
    s.text(84, 172, "下次连接需要重新输入。", 11, T2)
    s.rect(84, 190, 150, 32, "#1B2438", rx=8, stroke=LINE, sw=0.5)
    s.text(159, 211, "取 消", 11.5, T2, anchor="middle")
    s.rect(246, 190, 150, 32, FAIL_BG, rx=8, stroke=FAIL_EDGE, sw=0.6)
    s.text(321, 211, "忘 记", 11.5, FAIL, anchor="middle")


def sc_embedded(s):
    # 宿主页面：设置页里嵌一个卡片，卡片内放 WiFi 组件
    s.text(20, 30, "设置", 17, T1, weight="500")
    s.text(20, 48, "网络与连接", 10.5, T3)
    s.rect(20, 58, 440, 236, "#0D1420", rx=12, stroke=LINE, sw=0.6)
    s.text(36, 78, "WiFi", 11, T3)
    s.text(444, 78, "管理", 10, T2, anchor="end")
    # 组件区域（虚线示意容器边界）
    s.rect(28, 86, 424, 176, "none", rx=10, stroke="#3A4867", sw=0.6, dash="3 3")
    # 组件内部：头 + 3 行（尺寸随容器，字号/行高按比例缩小）
    s.text(40, 108, "WiFi", 13, T1, weight="500")
    s.text(40, 122, "已发现 6 个网络", 9, T2)
    s.rect(376, 98, 56, 20, PILL_BG, rx=10, stroke=LINE, sw=0.5)
    s.text(404, 112, "刷新", 9, "#B9C6DC", anchor="middle")
    mini = [
        ("yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4, ("conn", "已连接"), "conn"),
        ("1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4, ("saved", "已保存"), None),
        ("Office-2G", "开放网络 · -74 dBm", 2, ("open", "无需密码"), None),
    ]
    y = 130
    for ssid, meta, nb, st, accent in mini:
        s.rect(40, y, 400, 38, ROW_BG, rx=8,
               stroke={"conn": LINE_CONN}.get(accent, LINE),
               sw=1 if accent else 0.5)
        for b in range(4):
            h = [4, 6.5, 9, 11.5][b]
            on = b < nb
            col = (SUC if accent == "conn" else PRI) if on else DIM
            s.rect(52 + b * 5, y + 29 - h, 3, h, col)
        s.text(76, y + 16, ssid, 12, T1)
        s.text(76, y + 29, meta, 9, T2)
        kind = st[0]
        if kind != "open":
            s.rect(364, y + 15, 8, 6.5, T2, rx=1.3)
            s.path("M366 %d v-2 a2 2 0 0 1 4 0 v2" % (y + 15), stroke=T2, sw=1.1)
        if kind == "open":
            s.text(428, y + 22, st[1], 8.5, T3, anchor="end")
        else:
            pw = 42 if kind == "conn" else 38
            px = 428 - pw
            fill, edge, col = (("#0E2A22", LINE_CONN, SUC) if kind == "conn"
                               else ("#16203A", PRI, PRI_TXT))
            s.rect(px, y + 11, pw, 15, fill, rx=7.5, stroke=edge, sw=0.5)
            s.text(px + pw / 2, y + 22, st[1], 8.5, col, anchor="middle")
        y += 45
    s.text(40, 274, "组件根 = LVGL 容器：整页用铺满，内嵌时行宽随容器变化", 8.5, T3)


def sc_sheet(s):
    """方案 C 效果图：列表在子容器 → 点行 → 遮罩 + 半页（键盘式）上滑。"""
    s.text(28, 36, "列表在子容器 · 连接用半页（键盘式）", 20, T1, weight="500")
    s.text(28, 62, "点行后 scrim 淡入、sheet 从底部上滑；半页里只有密码框 + 连接 + 全宽键盘",
           12.5, T2)

    S = 0.62
    PW, PH = 480 * S, 320 * S          # 297.6 x 198.4

    def draw_page(x0, y0, open_sheet):
        def X(v):
            return round(x0 + v * S, 1)

        def Y(v):
            return round(y0 + v * S, 1)

        def W(v):
            return round(v * S, 1)

        s.rect(X(0), Y(0), W(480), W(320), "#0B0F1A", rx=8, stroke=LINE, sw=0.6)
        s.rect(X(20), Y(22), W(90), W(9), "#1B2438", rx=2)
        s.rect(X(20), Y(38), W(56), W(5), "#18202F", rx=2)
        s.rect(X(20), Y(56), W(440), W(238), "#0D1420", rx=10, stroke=LINE, sw=0.5)
        s.rect(X(36), Y(74), W(40), W(6), "#1B2438", rx=2)
        s.rect(X(28), Y(86), W(424), W(192), "none", rx=8, stroke="#3A4867",
               sw=0.5, dash="3 3")
        for i in range(4):
            y = 94 + i * 50
            if y >= 278:              # 完全出界
                continue
            hrow = min(44, 278 - y)   # 第 4 行只露一截 = 容器裁剪（示意可滚动）
            s.rect(X(40), Y(y), W(400), W(hrow), ROW_BG, rx=8, stroke=LINE, sw=0.4)
            for b in range(4):
                hh = [5, 8, 11, 14][b]
                s.rect(X(50 + b * 5), Y(y + 34 - hh), W(3), W(hh),
                       SUC if i == 0 else PRI)
            s.rect(X(66), Y(y + 11), W(118), W(7), "#1B2438", rx=2)
            s.rect(X(66), Y(y + 26), W(150), W(5), "#18202F", rx=2)
            s.rect(X(382), Y(y + 15), W(44), W(13), "#16203A", rx=6,
                   stroke=LINE, sw=0.3)
        # 滚动条
        s.rect(X(444), Y(94), W(4), W(70), "#2C3852", rx=1.5)

        if not open_sheet:
            return
        # 遮罩
        s.rect(X(0), Y(0), W(480), W(320), "#05070D", rx=8, opacity="0.55")
        # 半页 224
        s.rect(X(0), Y(96), W(480), W(224), "#101A28", rx=8, stroke=SUC, sw=0.9)
        s.rect(X(224), Y(102), W(32), W(3), "#2C3852", rx=1.5)
        s.rect(X(16), Y(112), W(150), W(8), "#1B2438", rx=2)
        s.path("M%s %s l%s %s" % (X(450), Y(110), W(8), W(8)), stroke=T2, sw=1)
        s.path("M%s %s l%s %s" % (X(458), Y(110), W(-8), W(8)), stroke=T2, sw=1)
        s.rect(X(16), Y(126), W(364), W(36), FIELD_BG, rx=8, stroke=PRI, sw=0.7)
        s.rect(X(24), Y(140), W(60), W(7), "#1B2438", rx=2)
        s.rect(X(388), Y(126), W(76), W(36), PRI, rx=8)
        # 键盘 4 行
        kw = (464 - 9 * 4) / 10.0
        for ri in range(4):
            ky = 172 + ri * 34
            for ci in range(10):
                s.rect(X(8 + ci * (kw + 4)), Y(ky), W(kw), W(30), KEY_BG, rx=4,
                       stroke="#212B42", sw=0.3)

    draw_page(28, 96, False)
    draw_page(350, 96, True)

    s.text(28, 312, "① 宿主页：列表在子容器里（424×192）", 10, T1)
    s.text(28, 328, "行 400×44 · 可见约 3.5 行 · 容器内滚动（scroll_dir=VER）", 9, T3)
    s.text(350, 312, "② 点行 → 遮罩 + 半页 224 上滑", 10, T1)
    s.text(350, 328, "半页只放：密码框 + 连接 + 全宽键盘（键 42.8）", 9, T3)

    # 下方两块
    s.rect(20, 348, 310, 152, "#0D1420", rx=8, stroke=LINE, sw=0.6)
    s.text(36, 368, "半页 224 的高度预算", 10.5, T3)
    for i, ln in enumerate([
            "把手 6 · 标题行 20（SSID + ×）",
            "输入行 36（密码框 364 + 连接 76）",
            "键盘 132（4 行 × 30 · 键宽 42.8）",
            "间距 30 → 合计 224（< 210 会挤）"]):
        s.text(36, 392 + i * 22, ln, 9, T2)

    s.rect(342, 348, 310, 152, "#0D1420", rx=8, stroke=LINE, sw=0.6)
    s.text(358, 368, "三条 z 序规则（别改）", 10.5, T3)
    for i, ln in enumerate([
            "① overlay 挂 screen 根，不进子容器",
            "② 遮罩 45% + sheet 都置最上层",
            "③ 关闭只改 pwd_open，不动 wifi_state"]):
        s.text(358, 392 + i * 22, ln, 9, T2)
    s.text(358, 480, "（放进容器会被裁剪 + 坐标二次偏移，P-0007）", 8.5, T3)


def sc_noflow_arch(s):
    """no-flow 变体架构图：EEZ 只画静态外壳，执行模型回到纯 LVGL，没有 Flow 这一层。"""
    s.text(28, 38, "no-flow 架构：代码在哪、边界在哪", 20, T1, weight="500")
    s.text(28, 64, "flowSupport=false ⇒ EEZ 只出静态控件树；执行模型回到纯 LVGL，动态逻辑全在 native",
           12.5, T2)
    s.path("M28 78 H652", stroke=LINE, sw=0.6)

    def band(y, h, no, title, note=""):
        s.rect(24, y, 632, h, "#0D1420", rx=10, stroke=LINE, sw=0.6)
        s.text(36, y + 20, no, 9, T3)
        s.text(58, y + 20, title, 10.5, T1, weight="500")
        if note:
            s.text(644, y + 20, note, 8.5, T3, anchor="end")

    def card(x, y, w, h, title, lines, edge=LINE, tcol=T1):
        s.rect(x, y, w, h, "#101A28", rx=8, stroke=edge, sw=0.6)
        s.text(x + 10, y + 18, title, 9.5, tcol, weight="500")
        for i, ln in enumerate(lines):
            s.text(x + 10, y + 36 + i * 15, ln, 8.5, T2)

    # ---------- ① EEZ 工程（无 Flow） ----------
    band(88, 130, "①", "EEZ 工程 .eez-project（唯一设计源）", "flowSupport=false")
    cw, gap = 144, 12          # 36 + 3×156 + 144 = 648 ≤ 带右缘 656（母工程同排是 658，越界 2px）
    cards = [
        ("页面 / 控件树", ["main 单屏 480×320", "标题 + 状态行 + 刷新", "list_box（空 lv_list）"], PRI),
        ("变量：无", ["gvs = []", "structures = []", "vars.h 是空枚举"], FAIL),
        ("动作：1 个 native", ["scan_start", "implementationType", "= native（非 flow）"], PRI),
        ("样式 / 字体", ["主题令牌内联", "cn14 · GB2312", "行样式由 native 复用"], LINE),
    ]
    for i, (t, ls, e) in enumerate(cards):
        card(36 + i * (cw + gap), 112, cw, 88, t, ls, e)
    s.text(36, 210, "★ 与母工程唯一差异：build_example.py 里 flowSupport / generateSourceCodeForEezFramework = False",
           8.5, PRI_TXT)

    # 箭头
    s.path("M340 218 V230", stroke=PRI_TXT, sw=1.3)
    s.path("M335.5 225 l4.5 7 4.5 -7", stroke=PRI_TXT, sw=1.3)
    s.text(354, 230, "cli_build", 8.5, PRI_TXT)

    # ---------- ② 生成源码 ----------
    band(236, 112, "②", "生成源码 src/ui/（12 个模板文件 · 勿手改）", "无 eez-flow.cpp/h")
    chips = [
        ("screens.c", ["控件树 + 样式", "★ 直挂动作回调"]),
        ("actions.h", ["extern void", "action_scan_start"]),
        ("vars.h", ["空枚举", "（无 Flow 全局变量）"]),
        ("ui.c", ["create_screens()", "+ loadScreen()"]),
        ("structs.h", ["空壳", "（无 Value 容器）"]),
    ]
    chw = (608 - 4 * 8) / 5.0
    for i, (n, ls) in enumerate(chips):
        x = 36 + i * (chw + 8)
        s.rect(x, 266, chw, 62, "#101A28", rx=7, stroke="#2A3550", sw=0.6)
        s.text(x + 9, 283, n, 9.5, PRI_TXT, weight="500")
        s.text(x + 9, 301, ls[0], 8.2, T2)
        s.text(x + 9, 315, ls[1], 8.2, T3)
    s.text(36, 342, "★ 红线：src/ui/ 由 EEZ 覆盖生成；改动只发生在 native/ 与 build_example.py",
           8.5, T3)

    # ---------- ③ 没有 Flow 这一层（对照） ----------
    band(360, 124, "③", "执行模型：Flow 版 ↔ 本变体", "同一条结论两种真假")
    bw = (608 - 10) / 2.0
    card(36, 392, bw, 74, "Flow 版（母工程）",
         ["ui_init → eez_flow_init(assets[588])", "ui_tick → eez_flow_tick + tick_screen",
          "事件经 flowState 中转 · 二进制 501 符号"], LINE, T1)
    card(36 + bw + 10, 392, bw, 74, "本变体（no-flow）",
         ["ui_init → create_screens + loadScreen", "ui_tick → tick_screen(currentScreen)",
          "lv_obj_add_event_cb 直连 · 二进制 0 符号"], SUC, SUC)
    s.text(36, 476, "→ 摘掉的是运行时，不是功能：表达式绑定 / flow 组件 / SetVariable 才是 Flow 的收益",
           8.5, PRI_TXT)

    # ---------- ④ native ----------
    band(496, 152, "④", "native 层（app 平铺四组 + navigation/widgets/platform）", "零 Flow 引用")
    nw = (608 - 20) / 3.0
    nb = [
        ("platform/wifi_platform.h", ["契约面：wifi_ap_t 7 字段", "纯头文件，零实现"], LINE),
        ("widgets/wifi_list/wifi_list.cpp", ["native 直读 wifi_ap_at", "★ 唯一画列表处"], SUC),
        ("platform/pc/wifi_platform_pc.cpp", ["假数据 + RSSI 排序", "io_win / io_esp 未落地"], LINE),
    ]
    for i, (t, ls, e) in enumerate(nb):
        card(36 + i * (nw + 10), 528, nw, 62, t, ls, e)
    s.rect(36, 598, 608, 26, "#16203A", rx=6, stroke=LINE, sw=0.5)
    s.text(48, 615, "另有 app/wifi_model·view·events·logic 四组平铺业务文件 · navigation/wifi_nav.cpp（模态显隐）",
           8.8, T2)
    s.text(36, 640, "扫描态/文案/列表行都由 native 每拍比对后直写 LVGL 控件（objects.*）", 8.5, T3)

    # ---------- ⑤ 账单 ----------
    band(664, 122, "⑤", "摘掉 Flow 的账单（实测 2026-10-21）", "可复现")
    gw = (608 - 20) / 3.0
    gb = [
        ("生成码（不含字体）", ["548,573 B → 13,950 B", "少 eez-flow.cpp 9,923 行", "+ eez-flow.h 4,384 行"], PRI_TXT),
        ("二进制符号", ["eez::flow：501 → 0", "nm main.exe | grep -i eez", "仅误命中 focus_freeze"], SUC),
        ("门禁（反向判据）", ["eez-flow.* 出现 = FAIL", "preflight.check_no_flow", "动作断链同样 FAIL"], "#F0D48F"),
    ]
    for i, (t, ls, c) in enumerate(gb):
        x = 36 + i * (gw + 10)
        s.rect(x, 694, gw, 74, "#101A28", rx=8, stroke=LINE, sw=0.6)
        s.text(x + 10, 712, t, 9.5, c, weight="500")
        for j, ln in enumerate(ls):
            s.text(x + 10, 732 + j * 15, ln, 8.5, T2)

    # ---------- 占比条 ----------
    s.text(28, 802, "实现量分布", 8.5, T3)
    s.rect(28, 810, 430, 16, PRI, rx=4)
    s.rect(458, 810, 194, 16, FAIL, rx=4)
    s.text(243, 822, "EEZ 静态外壳（画界面）", 8.8, "#0B0F1A", anchor="middle", weight="500")
    s.text(555, 822, "native 全部动态逻辑", 8.2, "#0B0F1A", anchor="middle", weight="500")


def sc_scan_to_ui(s):
    """点击刷新后，硬件数据如何回流到 UI：9 步 + 归属标签。"""
    s.text(28, 38, "点「刷新」之后：硬件数据怎么回到 UI", 20, T1, weight="500")
    s.text(28, 64, "9 步单向回流；颜色 = 这段代码归谁（EEZ 生成 / native / 硬件）", 12.5, T2)
    s.path("M28 78 H652", stroke=LINE, sw=0.6)

    # 图例
    lx = 28
    for name, col, w in (("EEZ 生成（src/ui）", PRI, 132),
                         ("native（你写）", SUC, 96),
                         ("硬件 / 驱动", "#E8A25C", 88)):
        s.rect(lx, 90, 9, 9, col, rx=2)
        s.text(lx + 14, 99, name, 8.5, T2)
        lx += w

    rows = [
        ("1", "点「刷 新」→ LV_EVENT_CLICKED",
         "EEZ 生成 screens.c：lv_obj_add_event_cb(btn_refresh, ...)", "EEZ 生成", PRI, 72),
        ("2", "actions[] 表按 id 分发 → 你的 C 函数",
         "actions.h 声明 + ui.c 里 ActionExecFunc actions[]", "EEZ + 你", PRI, 66),
        ("3", "C 函数写命令：cmd_scan = 1",
         "native var 的 set 指针（INTEGER）或 setGlobalVariable()", "native", SUC, 56),
        ("4", "主循环每拍排空命令：ui_tick() → user_io_tick() 排空命令环",
         "main.c 调 ui_tick()；poll 读到 cmd_scan 才调 io_scan()", "native", SUC, 56),
        ("5", "发起扫描：esp_wifi_scan_start(WIFI_SCAN_ACTIVE)",
         "io_esp.cpp：异步，立即返回，不阻塞 UI", "native", SUC, 56),
        ("6", "WIFI_EVENT_SCAN_DONE（driver task）→ s_aps[16]",
         "esp_wifi_scan_get_ap_records()；此处【禁止】碰 LVGL / Flow", "硬件", "#E8A25C", 52),
        ("7", "数据已在 io 静态数组（s_aps[16]），只需置 scan_state=2",
         "无 Flow 数组桥；EEZ 不持有列表，native 直读", "native", SUC, 56),
        ("8", "ui_tick() → wifi_list 重建列表",
         "lv_obj_clean + 按 wifi_ap_count 循环 lv_list_add_button", "native", SUC, 80),
        ("9", "LVGL 列表行 / 标量状态文案 → 屏幕",
         "行由 native 自绘；连接中 / 空态文案走 EEZ 标量状态", "native + EEZ", PRI, 72),
    ]

    y = 116
    for i, (no, title, sub, tag, col, tw) in enumerate(rows):
        s.rect(28, y, 624, 62, "#101A28", rx=8, stroke=col, sw=0.55)
        s.rect(40, y + 9, 18, 18, col, rx=9, opacity="0.16")
        s.text(49, y + 22, no, 9, col, anchor="middle", weight="500")
        s.text(68, y + 26, title, 10.2, T1, weight="500")
        s.text(68, y + 45, sub, 8.2, T2)
        # 归属标签（右下角）
        s.rect(640 - tw, y + 36, tw, 15, "#0B1220", rx=7, stroke=col, sw=0.5)
        s.text(640 - tw / 2, y + 46.5, tag, 7.8, col, anchor="middle")
        # 行间箭头
        if i < len(rows) - 1:
            s.path("M49 %d V%d" % (y + 58, y + 68), stroke="#33405E", sw=1)
            s.path("M46 %d l3 4 3 -4" % (y + 64), stroke="#33405E", sw=1)
        y += 70

    # 关键提示
    base = 116 + 9 * 70 - 8
    s.rect(28, base + 10, 624, 78, "#0D1420", rx=8, stroke=LINE, sw=0.6)
    s.text(40, base + 30, "三条铁律（这一段最容易出事）", 9.5, T3)
    notes = [
        "① 线程：第 6 步在 WiFi driver task，绝不能直接调 LVGL/Flow —— 投递到 UI 任务（队列/信号量）",
        "② 顺序：先填 s_aps → 再置 scan_state=2；UI 只在 =2 时读，避免半成品",
        "③ 单一真值源：数据只存在 io 静态数组；换后端只换 io_*.cpp，列表渲染不变",
    ]
    for i, ln in enumerate(notes):
        s.text(40, base + 48 + i * 15, ln, 8.2, T2)

    s.text(28, base + 108, "EEZ 里真正的代码：screens.c（控件树+事件）· actions.h（动作声明）"
                           "· vars.h（标量枚举）· ui.c（assets+init）；列表行由 widgets/wifi_list.cpp 自绘",
           8.5, PRI_TXT)


def sc_password_flow(s):
    """密码怎么到硬件、结果怎么回 UI：下行 5 步 + 上行 5 步 + reason 表。"""
    s.text(28, 38, "密码怎么下去、结果怎么上来", 20, T1, weight="500")
    s.text(28, 64, "密码只在「输入框 → 一次调用」之间存在；结果只通过变量回来", 12.5, T2)
    s.path("M28 78 H652", stroke=LINE, sw=0.6)

    BW, GAP, X0 = 116, 10, 30

    def arrow(x, y):
        s.path("M%d %d h6" % (x, y), stroke="#33405E", sw=1.1)
        s.path("M%d %d l4 3.2 l-4 3.2" % (x + 6, y - 3.2), stroke="#33405E", sw=1.1)

    def box(i, y, no, title, l1, l2, col):
        x = X0 + i * (BW + GAP)
        s.rect(x, y, BW, 74, "#101A28", rx=8, stroke=col, sw=0.55)
        s.rect(x + 9, y + 9, 15, 15, col, rx=7.5, opacity="0.16")
        s.text(x + 16.5, y + 20, no, 8, col, anchor="middle", weight="500")
        s.text(x + 9, y + 40, title, 8.8, T1, weight="500")
        s.text(x + 9, y + 56, l1, 7.8, T2)
        s.text(x + 9, y + 68, l2, 7.8, T3)

    s.text(30, 100, "① 下行：密码 → WiFi 驱动（同一拍内完成，不阻塞 UI）", 9.5, T3)
    a_boxes = [
        ("ta_pwd 输入", "密码模式 · 最多 63", "点框才弹键盘", PRI),
        ("点「连接」", "action_connect()", "生成事件→你的函数", PRI),
        ("命令槽单份拷贝", "≤64B，只存一份", "排空后立即清零", SUC),
        ("本地校验", "长度 8–63", "不合规→reason=5", SUC),
        ("io_wifi_join()", "set_config + connect", "异步，立即返回", SUC),
    ]
    for i, (t, l1, l2, col) in enumerate(a_boxes):
        box(i, 112, str(i + 1), t, l1, l2, col)
        if i < 4:
            arrow(X0 + i * (BW + GAP) + BW + 1, 149)
    s.text(30, 204, "★ 密码不写进 Flow 变量、不进日志、不落 NVS；只在命令槽里存在到同拍 drain 完成（≤1 帧）",
           8.5, PRI_TXT)

    s.text(30, 232, "② 上行：结果 → UI（全部在 UI 任务里发布，驱动任务只写标志）", 9.5, T3)
    b_boxes = [
        ("CONNECTED", "DISCONNECTED(reason)", "驱动任务只写标志", "#E8A25C"),
        ("结果结构 g_res", "{state, reason, ip}", "单写者，不加锁", "#E8A25C"),
        ("pump 读结果", "UI 任务发布变量", "成功才清空输入", SUC),
        ("eez_flow_tick", "按钮「连接中…」", "收起 / 标题红字", PRI),
        ("LVGL 呈现", "失败保留半页+键盘", "可直接重试", PRI),
    ]
    for i, (t, l1, l2, col) in enumerate(b_boxes):
        box(i, 244, str(i + 1), t, l1, l2, col)
        if i < 4:
            arrow(X0 + i * (BW + GAP) + BW + 1, 281)
    s.text(30, 336, "★ 成功 → 半页自动收起、该行变「已连接」；失败 → 半页不关、按钮恢复可点，密码框保留供重试",
           8.5, PRI_TXT)

    s.rect(28, 352, 624, 136, "#0D1420", rx=8, stroke=LINE, sw=0.6)
    s.text(40, 372, "③ 结果不是一个「失败」，而是可解释的 reason（否则用户只会看到「没用」）", 9.5, T3)
    for x, t in ((40, "reason"), (120, "含义"), (300, "UI 文案"), (470, "动作")):
        s.text(x, 394, t, 8, T3)
    rows = [
        ("15", "四次握手超时（密码不对）", "密码错误，请重新输入", "保留半页，输入框聚焦"),
        ("201", "扫描不到该 AP", "网络已消失，请重新扫描", "回列表并触发扫描"),
        ("205 / 2 / 3", "连接失败 / 认证过期", "连接超时，可重试", "按钮恢复，允许重试"),
        ("本地 5", "长度不在 8–63", "密码需 8–63 位", "不发命令，就地提示"),
    ]
    for i, (a1, b1, c1, d1) in enumerate(rows):
        y = 414 + i * 17
        s.text(40, y, a1, 8.2, FAIL)
        s.text(120, y, b1, 8.2, T1)
        s.text(300, y, c1, 8.2, T2)
        s.text(470, y, d1, 8.2, T2)

    s.text(28, 512, "四条纪律：① 密码只在 ta_pwd 与一次调用的栈上 ② 日志只打长度 ③ 失败路径也要清零临时缓冲 ④ 只有 remember=1 才落盘",
           8.5, T2)
    s.text(28, 532, "平台差异：PC（Windows）temporary profile 不稳，remember=0 也需先建 profile；真机（esp_wifi）可直接不落 NVS",
           8.5, T3)



# ---------------- 连接半页（方案 C，几何与实现逐像素一致）----------------
SHEET_Y, SHEET_H = 96, 224
SHEET_TA = (8, 43, 364, 35)          # x,y,w,h（相对 sheet）
SHEET_BTN = (393, 42, 76, 36)
SHEET_KB = (8, 86, 464, 132)
SHEET_KB_GAP = 4                     # 键间距（与 build_example.py 同值）


def sheet(s, state="input", ssid="1号楼6层WiFi", pwd="", remember=False):
    """scrim + sheet。state: input / connecting / failed。

    ★ 这里的坐标就是 build_example.py 里写进 EEZ 的那组数 —— 设计图与实现同源。"""
    s.rect(0, 0, W, H, "#05070D", rx=14, opacity="0.55")
    s.rect(0, SHEET_Y, W, SHEET_H, "#1C2440", rx=0)
    s.rect((W - 32) / 2.0, SHEET_Y + 6, 32, 3, LINE, rx=1.5)
    if state == "failed":
        s.text(16, SHEET_Y + 15 + 14, "密码错误，请重试", 13, FAIL, weight="500")
    else:
        s.text(16, SHEET_Y + 15 + 14, ssid, 13, T1, weight="500")
    s.text(W - 30, SHEET_Y + 15 + 14, "×", 15, T2, anchor="middle")
    x, y, w, h = SHEET_TA
    s.rect(x, SHEET_Y + y, w, h, ROW_BG, rx=8,
           stroke=(FAIL_EDGE if state == "failed" else LINE), sw=0.8)
    if pwd:
        s.text(x + 12, SHEET_Y + y + 23, "•" * len(pwd), 13, T1)
    else:
        s.text(x + 12, SHEET_Y + y + 23, "输入密码", 12, T3)
    bx, by, bw, bh = SHEET_BTN
    busy = (state == "connecting")
    s.rect(bx, SHEET_Y + by, bw, bh, ("#2A3550" if busy else PRI), rx=8)
    s.text(bx + bw / 2.0, SHEET_Y + by + 23,
           ("连接中…" if busy else "连 接"), 11,
           (T3 if busy else "#0A1020"), anchor="middle")
    lvgl_keyboard(s, SHEET_Y + SHEET_KB[1], key_h=30, gap=SHEET_KB_GAP,
                  x0=SHEET_KB[0], width=SHEET_KB[2])


def _list_base(s, sub="已发现 6 个网络", target_status=None, target_accent=None):
    header(s, sub)
    group_label(s, GRP1_LABEL_Y, "已连接 · 已保存")
    row(s, GRP1_TOP, "yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4,
        status=("conn", "已连接"), accent="conn")
    row(s, GRP1_TOP + PITCH, "1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4,
        status=target_status, accent=target_accent)
    group_label(s, GRP2_LABEL_Y, "可用网络", "共 6 个")
    row(s, GRP2_TOP, "YJT-1号楼办公", "WPA2 · -66 dBm · 2.4 GHz", 3)
    row(s, GRP2_TOP + PITCH, "Office-2G", "开放网络 · -74 dBm · 2.4 GHz", 2,
        lock=False, status=("open", "无需密码"))


def sc_sheet_open(s):
    _list_base(s, target_status=("saved", "已保存"))
    sheet(s, "input", ssid="1号楼6层WiFi")


def sc_sheet_error(s):
    _list_base(s, target_status=("fail", "连接失败"), target_accent="fail")
    sheet(s, "failed", ssid="1号楼6层WiFi", pwd="12345678")


def sc_connected(s):
    # 成功态：目标网络升到"已连接"这一行，原已连接的那条退回"已保存"
    header(s, "已连接 1号楼6层WiFi")
    group_label(s, GRP1_LABEL_Y, "已连接 · 已保存")
    row(s, GRP1_TOP, "1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4,
        status=("conn", "已连接"), accent="conn")
    row(s, GRP1_TOP + PITCH, "yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4,
        status=("saved", "已保存"))
    group_label(s, GRP2_LABEL_Y, "可用网络", "共 6 个")
    row(s, GRP2_TOP, "YJT-1号楼办公", "WPA2 · -66 dBm · 2.4 GHz", 3)
    row(s, GRP2_TOP + PITCH, "Office-2G", "开放网络 · -74 dBm · 2.4 GHz", 2,
        lock=False, status=("open", "无需密码"))


def sc_menu(s):
    """长按已保存网络 -> 忘记确认对话框（左取消 / 右忘记）。

    不放「记住密码」开关：既然这个对话框的目的就是忘记，再给个“记住”开关是自相矛盾的选项。"""
    _list_base(s, target_status=("saved", "已保存"))
    s.rect(0, 0, W, H, "#05070D", rx=14, opacity="0.45")
    DX, DY, DW, DH = DIALOG_BOX
    s.rect(DX, DY, DW, DH, "#161E30", rx=14, stroke=LINE, sw=0.6)
    s.text(DX + 20, DY + 32, "忘记此网络？", 14, T1, weight="500")
    s.text(DX + 20, DY + 54, "1号楼6层WiFi · WPA3 · -63 dBm", 11, T2)
    s.text(DX + 20, DY + 74, "将删除已保存的密码，下次连接需重新输入。", 10.5, T3)
    # 三个按钮：左忘记（危险）/ 中断开 / 右取消（用户定的顺序，别＜顺手＞调回去）
    s.rect(*DIALOG_BTN_L, FAIL_BG, rx=8, stroke=FAIL_EDGE, sw=0.6)
    s.text(DIALOG_BTN_L[0] + DIALOG_BTN_L[2] / 2, DY + 113, "忘记", 11.5, FAIL,
           anchor="middle")
    s.rect(*DIALOG_BTN_M, "#1B2438", rx=8, stroke=LINE, sw=0.5)
    s.text(DIALOG_BTN_M[0] + DIALOG_BTN_M[2] / 2, DY + 113, "断 开", 11.5, T2,
           anchor="middle")
    s.rect(*DIALOG_BTN_R, "#1B2438", rx=8, stroke=LINE, sw=0.5)
    s.text(DIALOG_BTN_R[0] + DIALOG_BTN_R[2] / 2, DY + 113, "取 消", 11.5, T2,
           anchor="middle")


def lvgl_keyboard(s, top, key_h=29, gap=4, x0=8, width=464, ok_text="OK"):
    """按 LVGL TEXT_LOWER 的真实键位画键盘（12/12/12/5）。

    符号键用 ASCII 代替（设计图字体没有 LV_SYMBOL）：⌫→del、↵→ret、键盘→abc、
    ←→<、→→>、OK 保留字母；真机由 LVGL 画成对应图标。"""
    rows = [
        [("1#", 1.4)] + [(k, 1.0) for k in "qwertyuiop"] + [("del", 1.4)],
        [("ABC", 1.4)] + [(k, 1.0) for k in "asdfghjkl"] + [("ret", 1.4)],
        [("_", 1.0), ("-", 1.0)] + [(k, 1.0) for k in "zxcvbnm"] +
        [(".", 1.0), (",", 1.0), (":", 1.0)],
        [("键盘", 1.6), ("<", 1.0), ("", 6.0), (">", 1.0), (ok_text, 1.6)],
    ]
    for ri, keys in enumerate(rows):
        y = top + ri * (key_h + gap)
        total_w = sum(w for _k, w in keys)
        unit = (width - (len(keys) - 1) * gap) / total_w
        cx = x0
        for k, wgt in keys:
            kw = unit * wgt
            done = (k == ok_text)
            s.rect(cx, y, kw, key_h, PRI if done else KEY_BG, rx=5,
                   stroke=None if done else "#212B42", sw=0.5)
            if k == "":
                s.rect(cx + kw * 0.3, y + key_h / 2 - 2, kw * 0.4, 4, "#2C3852", rx=2)
            elif k:
                s.text(cx + kw / 2, y + key_h / 2 + 4, k,
                       10 if len(k) > 1 else 11,
                       "#0A1020" if done else T1, anchor="middle")
            cx += kw + gap


SCREENS = [
    ("mockup_01_list.svg", "01 · 列表主态（分组）",
     "已连接/已保存置顶分组 + 可用网络；行内含信号图示、名称、类型·强度·频段、锁、状态位",
     "01 列表主态：分组置顶（已连接 · 已保存 / 可用网络），行高 46、行距 6、状态位右缘统一", sc_list),
    ("mockup_02_scanning.svg", "02 · 扫描中",
     "骨架行占位 + 刷新按钮转圈；状态只在标题栏一行",
     "02 扫描中：4 行骨架占位，刷新按钮呈扫描态，状态统一在标题栏", sc_scanning),
    ("mockup_03_empty.svg", "03 · 无网络（空态）",
     "WiFi 图标 + 文案 + 重新扫描主按钮",
     "03 空态：WiFi 图标 + 「未发现网络」+ 引导文案 + 重新扫描按钮", sc_empty),
    ("mockup_04_sheet.svg", "04 · 连接半页（输入密码）",
     "点带锁网络行：遮罩淡入 + 半页自底部上滑；密码框 + 连接 + 全宽键盘",
     "04 连接半页：sheet 480×224（把手6+标题20+输入行36+间距30+键盘132），overlay 挂 screen 根",
     sc_sheet_open),
    ("mockup_05_sheet_error.svg", "05 · 半页 · 密码错误",
     "标题行就地变红字（不额外占高度），密码框红描边并保持焦点",
     "05 密码错误：错误提示就地显示在标题行，键盘不收起", sc_sheet_error),
    ("mockup_06_connecting.svg", "06 · 连接中",
     "状态只在标题栏一行；半页内密码框保持、连接键变灰「连接中…」",
     "06 连接中：状态统一在标题栏（底部不再另起一行），连接键禁用防重复投递", sc_connecting),
    ("mockup_07_failed.svg", "07 · 连接失败",
     "目标行红描边 + 失败胶囊；半页标题行红字「密码错误」",
     "07 连接失败：目标行红描边 + 状态胶囊；错误就地显示在半页标题行（不额外占高度）", sc_failed),
    ("mockup_08_forget_confirm.svg", "08 · 忘记网络确认",
     "长按行触发：遮罩 + 确认卡（取消 / 忘记）",
     "08 忘记确认：长按已保存网络 → 遮罩 + 确认弹层，忘记为危险色按钮", sc_forget),
    ("mockup_10_connected.svg", "10 · 连接成功",
     "半页自动收起，目标行转绿「已连接」；标题栏回显当前连接",
     "10 连接成功：sheet 收起（不打断列表），行状态就地变绿", sc_connected),
    ("mockup_11_menu.svg", "11 · 长按菜单",
     "对话框形式：标题/网络信息 + 左右两个按钮（左「忘记」/ 右「取消」）",
     "11 忘记确认对话框：左忘记、右取消（用户定序）；不放『记住密码』开关",
     sc_menu),
    ("mockup_09_embedded.svg", "09 · 组件内嵌容器",
     "同一组件放进设置页卡片，尺寸随容器自适应",
     "09 组件内嵌：同一组件放进设置页卡片，行宽/字号随容器自适应（容器 408×176）", sc_embedded),
]


def build(name, title, desc, caption, fn):
    s = SVG()
    fn(s)
    assert len(set(EDGES)) <= 1, "状态胶囊右缘不一致: %s" % set(EDGES)
    svg = "\n".join([
        '<svg viewBox="0 0 680 500" width="100%" role="img" '
        'xmlns="http://www.w3.org/2000/svg" '
        'font-family="Segoe UI, Microsoft YaHei, sans-serif">',
        '  <title>%s</title>' % esc(title),
        '  <desc>%s</desc>' % esc(desc),
        '  <g transform="translate(40,40) scale(1.25)">',
        '    <rect x="0" y="0" width="480" height="320" rx="14" fill="%s" '
        'stroke="%s" stroke-width="1"/>' % (BG, LINE),
    ] + s.o + [
        '  </g>',
        '  <text x="40" y="472" fill="#7C8AA5" font-size="12">%s</text>' % esc(caption),
        '</svg>',
        '',
    ])
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


def build_wide(name, title, desc, height, fn):
    """独立画布解释图（680 宽，无设备外框）。"""
    s = SVG()
    fn(s)
    head = ('<svg viewBox="0 0 680 ' + str(height) + '" width="100%" role="img" '
            'xmlns="http://www.w3.org/2000/svg" '
            'font-family="Segoe UI, Microsoft YaHei, sans-serif">')
    bg = ('  <rect x="0" y="0" width="680" height="' + str(height) +
          '" rx="14" fill="' + BG + '" stroke="' + LINE + '" stroke-width="1"/>')
    svg = "\n".join([head, '  <title>' + esc(title) + '</title>',
                      '  <desc>' + esc(desc) + '</desc>', bg] + s.o +
                     ['</svg>', ''])
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    # 网格自检
    assert GRP1_LABEL_Y + 4 <= GRP1_TOP
    assert GRP1_TOP + PITCH + ROW_H <= GRP2_LABEL_Y, "组1与组2重叠"
    assert GRP2_TOP + PITCH + ROW_H <= BOTTOM_Y - 12, "列表溢出"
    total = 0
    for name, title, desc, cap, fn in SCREENS:
        EDGES.clear()
        p = build(name, title, desc, cap, fn)
        total += os.path.getsize(p)
        print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    p = build_wide("mockup_19_password_flow.svg", "框图 · 密码下行 / 结果上行",
                   "下行 5 步（输入→action→直传→校验→join）+ 上行 5 步（事件→结果→pump→Flow→UI）+ reason 映射",
                   556, sc_password_flow)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    p = build_wide("mockup_18_scan_to_ui.svg", "框图 · 扫描数据如何回流到 UI",
                   "9 步：点击 → action → 命令 → native 泵 → 扫描 → driver task 回调 → 置状态 → native 直读 io 画列表 → LVGL",
                   900, sc_scan_to_ui)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    p = build_wide("mockup_20_noflow_arch.svg",
                   "架构图 · no-flow 变体（EEZ 静态外壳 + native 全动态，无 Flow 运行时）",
                   "五层：EEZ 工程(flowSupport=false) → 生成源码(无 eez-flow) → 执行模型对照 → native 层 → 账单",
                   836, sc_noflow_arch)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    p = build_wide("mockup_15_subcontainer_sheet.svg", "方案图 · 子容器列表 + 半页连接",
                   "宿主页子容器内列表 → 点行 → 遮罩 + 半页上滑（含全宽键盘）",
                   512, sc_sheet)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    print("total:", total, "bytes")
