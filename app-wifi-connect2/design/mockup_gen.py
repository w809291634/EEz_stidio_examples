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
KEY_BG = "#1A2338"
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


def header(s, sub, btn="刷新", busy=False):
    s.text(PAD, 26, "WiFi", 17, T1, weight="500")
    s.text(PAD, 42, sub, 11.5, T2)
    bx = W - PAD - 64
    s.rect(bx, 13, 64, 26, PILL_BG, rx=13, stroke=LINE, sw=0.5)
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
    spinner(s, 190, 300, 8, PRI)
    s.text(206, 304, "正在读取扫描结果", 10.5, T3)


def sc_empty(s):
    header(s, "已发现 0 个网络")
    wifi_glyph(s, W / 2, 168, T3)
    s.text(W / 2, 218, "未发现网络", 15, T1, anchor="middle")
    s.text(W / 2, 240, "请确认 WiFi 已开启，然后重新扫描", 11, T2, anchor="middle")
    s.rect(170, 256, 140, 34, PRI, rx=17)
    s.text(W / 2, 278, "重新扫描", 12, "#FFFFFF", anchor="middle")


def sc_password(s):
    back_bar(s)
    s.text(PAD, 64, "1号楼6层WiFi", 18, T1)
    s.text(PAD, 84, "WPA3 · 5 GHz · -63 dBm", 11, T2)
    s.text(PAD, 110, "密码", 11, T3)
    s.rect(PAD, 118, ROW_W, 42, FIELD_BG, rx=10, stroke=PRI, sw=1)
    s.text(PAD + 16, 145, "请输入密码", 13, T3)
    eye(s, W - PAD - 18, 139)
    s.text(PAD, 188, "记住密码", 13, T1)
    s.text(PAD, 204, "保存后下次自动连接", 10, T3)
    toggle(s, W - PAD - 48, 178, on=False)
    s.rect(PAD, 218, ROW_W, 42, PRI, rx=10)
    s.text(W / 2, 245, "连 接", 14, "#FFFFFF", anchor="middle", weight="600")
    s.text(W / 2, 280, "忘记此网络", 11.5, FAIL, anchor="middle")
    s.text(W / 2, 304, "点按密码框弹出键盘", 10, T3, anchor="middle")


def sc_password_kb(s):
    back_bar(s, 26)
    s.text(PAD, 56, "1号楼6层WiFi", 15, T1)
    s.text(PAD, 73, "WPA3 · 5 GHz · -63 dBm", 10.5, T2)
    s.rect(PAD, 82, ROW_W, 36, FIELD_BG, rx=9, stroke=PRI, sw=1)
    s.text(PAD + 16, 106, "••••••••", 15, T1, ls="1.5")
    eye(s, W - PAD - 18, 100)
    keyboard(s, 126)


def sc_connecting(s):
    header(s, "正在连接 1号楼6层WiFi…")
    group_label(s, GRP1_LABEL_Y, "已连接 · 已保存")
    row(s, GRP1_TOP, "1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4,
        status=("ing", "连接中"), accent="ing")
    row(s, GRP1_TOP + PITCH, "yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4,
        status=("saved", "已保存"))
    group_label(s, GRP2_LABEL_Y, "可用网络", "共 6 个")
    row(s, GRP2_TOP, "YJT-1号楼办公", "WPA2 · -66 dBm · 2.4 GHz", 3)
    row(s, GRP2_TOP + PITCH, "Office-2G", "开放网络 · -74 dBm · 2.4 GHz", 2,
        lock=False, status=("open", "无需密码"))
    spinner(s, PAD + 8, 300, 6, PRI)
    s.text(PAD + 22, 304, "正在认证并获取 IP，请稍候", 10.5, PRI_TXT)


def sc_failed(s):
    header(s, "已发现 6 个网络")
    group_label(s, GRP1_LABEL_Y, "已连接 · 已保存")
    row(s, GRP1_TOP, "1号楼6层WiFi", "WPA3 · -63 dBm · 5 GHz", 4,
        status=("fail", "连接失败"), accent="fail")
    row(s, GRP1_TOP + PITCH, "yjt_dev_2.4G", "WPA2 · -58 dBm · 5 GHz", 4,
        status=("saved", "已保存"))
    group_label(s, GRP2_LABEL_Y, "可用网络", "共 6 个")
    row(s, GRP2_TOP, "YJT-1号楼办公", "WPA2 · -66 dBm · 2.4 GHz", 3)
    row(s, GRP2_TOP + PITCH, "Office-2G", "开放网络 · -74 dBm · 2.4 GHz", 2,
        lock=False, status=("open", "无需密码"))
    s.rect(PAD, 292, ROW_W, 20, FAIL_BG, rx=6, stroke=FAIL_EDGE, sw=0.5)
    s.text(PAD + 10, 306, "密码错误，点按该网络重新输入", 10.5, FAIL)


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


def sc_layers(s):
    """页面层级关系：密码页 = 独立整页，覆盖在列表（扫描结果）之上。"""
    s.text(PAD, 28, "页面结构：两页覆盖", 13, T1, weight="500")
    s.text(PAD, 44, "密码页是独立页面，整页盖在列表（扫描结果）之上；返回即回到列表",
           9.5, T2)

    # 后层：列表页（被覆盖，实例保留）
    s.rect(16, 56, 264, 192, "#0D1420", rx=10, stroke=LINE, sw=0.6)
    s.text(30, 74, "页面 1 · 列表（扫描结果）", 9.5, T3)
    rows = [("yjt_dev_2.4G", "WPA2", 4, SUC), ("1号楼6层WiFi", "WPA3", 4, PRI),
            ("YJT-1号楼办公", "WPA2", 3, PRI), ("Office-2G", "开放", 2, PRI)]
    y = 82
    for ssid, auth, nb, col in rows:
        s.rect(28, y, 240, 24, ROW_BG, rx=6, stroke=LINE, sw=0.4)
        for b in range(4):
            h = [3, 5, 7, 9][b]
            on = b < nb
            s.rect(36 + b * 4.5, y + 20 - h, 2.6, h, col if on else DIM)
        s.text(60, y + 15, ssid, 9, T1)
        s.text(232, y + 15, auth, 7.5, T3, anchor="end")
        y += 28
    s.text(30, 226, "实例保留：扫描结果 / 分组 / 滚动位置", 8, T3)
    s.text(30, 240, "切页不重新扫描、不丢数据", 8, T3)

    # 前层：密码页（整页覆盖）
    s.rect(196, 88, 268, 204, "#101A28", rx=10, stroke=PRI, sw=1)
    s.text(210, 106, "页面 2 · 密码", 9.5, PRI_TXT)
    s.text(452, 106, "整页 480×320", 8, T3, anchor="end")
    s.text(210, 130, "1号楼6层WiFi", 11.5, T1)
    s.text(210, 144, "WPA3 · 5 GHz · -63 dBm", 8, T2)
    s.rect(208, 152, 244, 24, FIELD_BG, rx=6, stroke=PRI, sw=0.8)
    s.text(216, 168, "••••••••", 10, T1, ls="1.2")
    s.text(210, 190, "记住密码", 9, T1)
    s.rect(428, 181, 24, 14, "#16203A", rx=7, stroke=LINE, sw=0.4)
    s.circle(435, 188, 5, T2)
    s.rect(208, 200, 244, 26, PRI, rx=7)
    s.text(330, 217, "连 接", 10, "#FFFFFF", anchor="middle", weight="600")
    s.text(330, 240, "忘记此网络", 8.5, FAIL, anchor="middle")
    s.rect(208, 250, 244, 34, "#141A2E", rx=7, stroke=LINE, sw=0.4, dash="2 2")
    s.text(330, 264, "键盘（点密码框才弹出）", 8, T3, anchor="middle")
    s.text(330, 276, "完成 / 返回 → 收起并回列表", 8, T3, anchor="middle")

    # 编号徽标
    s.circle(16, 56, 7, PRI)
    s.text(16, 59, "1", 8.5, "#FFFFFF", anchor="middle", weight="600")
    s.circle(196, 88, 7, PRI)
    s.text(196, 91, "2", 8.5, "#FFFFFF", anchor="middle", weight="600")

    s.text(PAD, 310, "① 点网络行 → ② 覆盖；② 返回 / 完成 → 回 ①，① 的状态与滚动位置不变",
           8.5, T3)


def sc_explain(s):
    """解释图（独立画布 680x528）：场景 → 键盘宽度对比 → 结论。"""
    s.text(28, 40, "键盘为什么要整页", 20, T1, weight="500")
    s.text(28, 66, "列表可以放进任意子容器；点密码输入时整页覆盖 → 键盘始终按屏幕宽度排版",
           12.5, T2)

    # ---------- ① 场景 ----------
    s.text(28, 100, "① 场景：列表在子容器里，输入密码时升格为整页", 10.5, T3)

    # 左：设置页 + 卡片 + 子容器 + 3 行
    s.rect(28, 110, 202, 134, "#0D1420", rx=8, stroke=LINE, sw=0.6)
    s.text(40, 124, "设置", 8, T3)
    s.rect(38, 130, 182, 104, "#0E1420", rx=6, stroke=LINE, sw=0.5)
    s.text(46, 144, "WiFi", 7, T3)
    s.rect(44, 150, 170, 76, "none", rx=5, stroke="#3A4867", sw=0.5, dash="2 2")
    for i in range(3):
        y = 156 + i * 24
        s.rect(50, y, 158, 20, ROW_BG, rx=4, stroke=LINE, sw=0.3)
        for b in range(4):
            hh = [2.5, 4, 5.5, 7][b]
            s.rect(56 + b * 3.6, y + 15 - hh, 2.2, hh,
                   (PRI if b < 3 else DIM))
        s.rect(72, y + 4, 58, 5, "#1B2438", rx=2)
        s.rect(72, y + 12, 78, 4, "#18202F", rx=2)
        s.rect(176, y + 6, 26, 9, "#16203A", rx=4.5, stroke=LINE, sw=0.3)
    s.text(28, 258, "设置页：WiFi 列表被放进卡片里的子容器（尺寸可任意）", 9, T3)

    # 箭头
    s.path("M240 176 h50", stroke=PRI_TXT, sw=1.4)
    s.path("M286 172 l6 4 -6 4", stroke=PRI_TXT, sw=1.4)
    s.text(265, 166, "点网络", 8.5, PRI_TXT, anchor="middle")

    # 右：密码整页
    s.rect(306, 110, 202, 134, "#101A28", rx=8, stroke=PRI, sw=0.8)
    s.text(318, 124, "\u2039 返回", 7.5, T3)
    s.text(318, 138, "1号楼6层WiFi", 8, T1)
    s.rect(316, 144, 182, 18, FIELD_BG, rx=4, stroke=PRI, sw=0.6)
    s.text(322, 157, "\u2022\u2022\u2022\u2022\u2022\u2022", 7.5, T1, ls="1")
    s.rect(316, 168, 182, 16, PRI, rx=4)
    s.text(407, 180, "连 接", 7, "#FFFFFF", anchor="middle")
    kwid = (182 - 9 * 2) / 10.0
    for ri in range(3):
        y = 190 + ri * 16
        cx = 316
        for _ in range(10):
            s.rect(cx, y, kwid, 13, KEY_BG, rx=2.5, stroke="#212B42", sw=0.3)
            cx += kwid + 2
    s.text(306, 258, "密码页：整页 480×320（键盘按屏宽排版）", 9, T2)

    # ---------- ② 宽度对比 ----------
    s.text(28, 282, "② 键盘宽度：同一套键盘，容器越窄键越窄", 10.5, T3)
    rows = [
        (320, "① 塞进 320 容器", FAIL, "#2A1620", FAIL_EDGE, "#5A2A34",
         "可用 320 · 键宽 28.4"),
        (408, "② 塞进 408 卡片（本设计）", T2, "#16203A", LINE, "#243456",
         "可用 408 · 键宽 34.8"),
        (464, "③ 密码页整页（推荐）", PRI_TXT, "#5B8CFF", "#7FA3FF", "#4A6EE0",
         "可用 464 · 键宽 42.8"),
    ]
    k = 300 / 464.0   # 条形长度：保证右侧数值不溢出画布
    for i, (avail, label, tcol, fill, edge, tick, val) in enumerate(rows):
        y = 292 + i * 38
        s.text(28, y + 17, label, 9.5, tcol)
        w = avail * k
        s.rect(186, y, w, 26, fill, rx=6, stroke=edge, sw=0.6)
        for j in range(1, 10):
            x = 186 + w * j / 10.0
            s.rect(x - 0.6, y + 4, 1.2, 18, tick)
        s.text(186 + w + 10, y + 17, val, 10, tcol)
    s.text(28, 404, "键宽 =（可用宽 \u2212 9 × 4）\u00f7 10；建议 \u2265 40（手指可辨），320 容器只有 28.4",
           9, T3)

    # ---------- ③ 结论 ----------
    s.rect(28, 420, 624, 34, "#16203A", rx=8, stroke=PRI, sw=0.6)
    s.text(44, 442, "结论：把「输入密码」升格为整页 \u2014\u2014 键盘宽度由屏幕决定，永不因子容器变窄",
           11.5, PRI_TXT)
    s.text(28, 476, "① 键宽 42.8：比 320 容器 +51%、比 408 卡片 +23%，误触显著减少", 9.5, T2)
    s.text(28, 494, "② 组件可放进任意容器（设置卡片 / 侧栏 / 弹窗），输入时统一升格为整页", 9.5, T2)
    s.text(28, 512, "③ 容器的紧凑阈值、裁剪、滚动都不会影响键盘排版", 9.5, T2)


def sc_popup_forms(s):
    """解释图：列表在子容器 → 点连接 → 弹层（半页 / 整页）两种形态 + 对比。"""
    s.text(28, 40, "连接页弹出：半页 or 整页", 20, T1, weight="500")
    s.text(28, 66, "WiFi 扫描结果放在宿主页的子容器里；点连接后弹出「连接 WiFi 页」，高度可以半页也可以整页",
           12.5, T2)

    SC = 0.42          # 480x320 → 202x134
    PW, PH = 202, 134
    XS = [28, 240, 452]

    def host(x, y, rows=3, dim=False):
        s.rect(x, y, PW, PH, "#0D1420", rx=6, stroke=LINE, sw=0.6)
        s.rect(x + 8, y + 6, 54, 6, "#1B2438", rx=2)
        s.rect(x + 8, y + 16, PW - 16, PH - 26, "#0E1420", rx=4, stroke=LINE, sw=0.4)
        s.rect(x + 14, y + 26, PW - 28, PH - 42, "none", rx=4, stroke="#3A4867",
               sw=0.5, dash="2 2")
        for i in range(rows):
            ry = y + 30 + i * 26
            s.rect(x + 18, ry, PW - 36, 22, ROW_BG, rx=3, stroke=LINE, sw=0.3)
            for b in range(4):
                hh = [2.5, 4, 5.5, 7][b]
                s.rect(x + 23 + b * 3.4, ry + 17 - hh, 2, hh, PRI if b < 3 else DIM)
            s.rect(x + 38, ry + 4, 52, 5, "#1B2438", rx=2)
            s.rect(x + 38, ry + 12, 66, 4, "#18202F", rx=2)
            s.rect(x + 150, ry + 6, 24, 8, "#16203A", rx=4, stroke=LINE, sw=0.3)
        if dim:
            s.rect(x, y, PW, PH, "#05070D", rx=6, opacity="0.55")

    def kb_rows(x, y, w, n=3, kh=10, gap=2):
        kw = (w - 9 * gap) / 10.0
        for ri in range(n):
            cy = y + ri * (kh + gap)
            cx = x
            for _ in range(10):
                s.rect(cx, cy, kw, kh, KEY_BG, rx=2, stroke="#212B42", sw=0.25)
                cx += kw + gap

    # ① 宿主页 + 子容器（扫描结果）
    host(XS[0], 96)
    s.text(XS[0], 246, "① 扫描结果在子容器里", 10, T1)
    s.text(XS[0], 262, "组件 408 宽，宿主页怎么变都跟着变", 9, T3)

    # ② 半页弹出
    x = XS[1]
    host(x, 96, rows=3, dim=True)
    sy = 96 + PH - 84                       # 高 200 → 84
    s.rect(x, sy, PW, 84, "#101A28", rx=8, stroke=SUC, sw=0.8)
    s.rect(x + 91, sy + 5, 20, 3, "#2C3852", rx=1.5)
    s.rect(x + 12, sy + 12, 66, 5, "#1B2438", rx=2)
    s.rect(x + 12, sy + 21, PW - 24, 15, FIELD_BG, rx=3, stroke=PRI, sw=0.6)
    s.rect(x + 12, sy + 40, PW - 24, 13, PRI, rx=3)
    kb_rows(x + 12, sy + 57, PW - 24, n=2, kh=10, gap=2.5)
    s.text(x, 246, "② 半页弹出（高 200 · 62%）", 10, T1)
    s.text(x, 262, "上半仍见列表；全宽键盘，只放密码 + 连接", 9, T3)

    # ③ 整页弹出
    x = XS[2]
    s.rect(x, 96, PW, PH, "#101A28", rx=6, stroke=PRI, sw=0.9)
    s.path("M%d %d l-4 4 4 4" % (x + 12, 111), stroke=T2, sw=1)
    s.rect(x + 20, 105, 44, 5, "#1B2438", rx=2)
    s.rect(x + 12, 118, 80, 6, "#1B2438", rx=2)
    s.rect(x + 12, 129, PW - 24, 16, FIELD_BG, rx=3, stroke=PRI, sw=0.6)
    s.rect(x + 12, 150, 40, 5, "#1B2438", rx=2)
    s.rect(x + 168, 147, 22, 11, "#16203A", rx=5.5, stroke=LINE, sw=0.3)
    s.rect(x + 12, 162, PW - 24, 15, PRI, rx=3)
    s.rect(x + 78, 184, 44, 5, "#5A2A34", rx=2)
    kb_rows(x + 12, 194, PW - 24, n=3, kh=9, gap=2)
    s.text(x, 246, "③ 整页弹出（320 · 全覆盖）", 10, T1)
    s.text(x, 262, "内容 + 键盘都宽松；记住 / 忘记 / 错误提示放得下", 9, T3)

    # 对比表
    s.rect(20, 282, 640, 190, "#0D1420", rx=8, stroke=LINE, sw=0.6)
    s.text(36, 304, "同一个「连接 WiFi 页」，两种高度", 10.5, T3)
    s.text(300, 304, "半页 200", 9.5, SUC)
    s.text(470, 304, "整页 320", 9.5, PRI_TXT)
    rows = [
        ("覆盖屏高", "62%（上半仍可见列表）", "100%（完全覆盖，返回还原）"),
        ("键盘", "全宽 464 · 2~3 行紧凑（键高 30）", "全宽 464 · 4 行（键高 36）"),
        ("能放的内容", "密码框 + 连接（最多再加一行提示）", "密码 + 记住密码 + 忘记 + 错误提示"),
        ("交互负担", "需管把手、遮罩、下滑关闭、焦点避让", "切页即可：无遮罩、无 z-order"),
        ("适合", "宿主页要保留上下文 / 快捷重连", "主流程：输密码、忘记、重试"),
    ]
    y = 322
    for i, (a, b, c) in enumerate(rows):
        s.text(36, y + 15, a, 9.5, T3)
        s.text(300, y + 15, b, 9.5, T1 if i < 3 else T2)
        s.text(470, y + 15, c, 9.5, T1 if i < 3 else T2)
        if i < len(rows) - 1:
            s.rect(32, y + 26, 616, 0.6, LINE)
        y += 30

    s.text(28, 496, "建议：主流程用整页（简单、键盘最大化）；若 WiFi 只是设置页里的一个小卡片，可给「半页」快捷形态",
           9.5, PRI_TXT)


def sc_arch(s):
    """架构数据流图：EEZ → 变量表 → app_model → io 后端 → 硬件，含状态回写。"""
    s.text(28, 40, "EEZ 里建什么 · 怎么和硬件交互", 20, T1, weight="500")
    s.text(28, 66, "四层单向数据流：UI 只读写变量，硬件只在 io 层；命令向下、状态向上",
           12.5, T2)

    def band(y, h, title):
        s.rect(24, y, 616, h, "#0D1420", rx=10, stroke=LINE, sw=0.6)
        s.text(36, y + 20, title, 10.5, T3)

    def card(x, y, w, h, lines, tcol=T1, edge=LINE):
        s.rect(x, y, w, h, "#101A28", rx=8, stroke=edge, sw=0.6)
        s.text(x + 10, y + 17, lines[0], 9, tcol, weight="500")
        for i, ln in enumerate(lines[1:]):
            s.text(x + 10, y + 33 + i * 14, ln, 8.5, T2)

    # ① EEZ 层
    band(84, 116, "① EEZ 里创建：页面 / 组件 / 控件 / 事件绑定")
    cw, gap, cx = 138, 12, 36
    items = [
        ("scr_list 列表页", "5 个固定行槽", "刷新 + 点行 + 长按"),
        ("wifi_panel 组件", "同一套控件", "整页或进子容器"),
        ("scr_pwd 连接页", "整页 320", "或半页 200"),
        ("Keyboard 键盘", "默认隐藏", "点密码框才弹出"),
    ]
    for i, it in enumerate(items):
        card(cx + i * (cw + gap), 112, cw, 76, it)

    # 箭头 1
    s.path("M340 200 V222", stroke=PRI_TXT, sw=1.3)
    s.path("M336 216 l4 7 4 -7", stroke=PRI_TXT, sw=1.3)
    s.text(352, 216, "事件 → action → app_set_output", 8.5, PRI_TXT)

    # ② 变量表
    band(224, 118, "② 变量表（EEZ 生成 vars.h，两层唯一接口）")
    s.rect(36, 252, 290, 78, "#101A28", rx=8, stroke=SUC, sw=0.6)
    s.text(46, 269, "inputs（io 写 → UI 读）", 9, SUC, weight="500")
    s.text(46, 285, "scan_state · wifi_state · ap_count", 8.5, T2)
    s.text(46, 299, "ssid_N · auth_N · rssi_N · band_N", 8.5, T2)
    s.text(46, 313, "lock_N · saved_N · conn_N（N=1..5）", 8.5, T2)
    s.rect(340, 252, 284, 78, "#101A28", rx=8, stroke=PRI, sw=0.6)
    s.text(350, 269, "outputs（UI 写 → io 读）", 9, PRI_TXT, weight="500")
    s.text(350, 285, "cmd_scan · cmd_pick · cmd_connect", 8.5, T2)
    s.text(350, 299, "cmd_forget · cmd_back", 8.5, T2)
    s.text(350, 313, "pwd · remember · pwd_open", 8.5, T2)

    # 箭头 2
    s.path("M340 342 V364", stroke=PRI_TXT, sw=1.3)
    s.path("M336 358 l4 7 4 -7", stroke=PRI_TXT, sw=1.3)
    s.text(352, 358, "命令环：command", 8.5, PRI_TXT)

    # ③ app_model
    band(366, 106, "③ app_model：每拍跑一次（lv_tick_get 驱动，PC / 真机同一来源）")
    steps = [("排空命令环", "每拍读 outputs"),
             ("调 io_*() 执行", "扫描 / 连接 / 忘记"),
             ("回写 inputs", "app_set_input_*"),
             ("计时", "lv_tick_get()")]
    for i, it in enumerate(steps):
        card(36 + i * 150, 394, 138, 62, it, T1, "#2A3550")

    # 箭头 3
    s.path("M340 472 V494", stroke=PRI_TXT, sw=1.3)
    s.path("M336 488 l4 7 4 -7", stroke=PRI_TXT, sw=1.3)
    s.text(352, 488, "io_*() 实现（同一组签名）", 8.5, PRI_TXT)

    # ④ io 后端
    band(496, 120, "④ io 后端：硬件唯一出口（UI 层零 WiFi 代码）")
    ios = [("io_pc.cpp", "假数据（PC 仿真）", "无需硬件跑通流程"),
           ("io_win.cpp", "Windows WLAN API", "PC 真 WiFi（已验证）"),
           ("io_esp.cpp", "esp_wifi + NVS", "真机（骨架待接）")]
    for i, it in enumerate(ios):
        card(36 + i * 204, 524, 196, 76, it, T1, "#2A3550")

    # 状态回写（右侧上升箭头）
    s.path("M660 556 V108", stroke=SUC, sw=1.3)
    s.path("M656 116 l4 -8 4 8", stroke=SUC, sw=1.3)
    s.o.append('    <g transform="rotate(-90 674 332)"><text x="674" y="332" '
               'fill="#3DDC97" font-size="9" text-anchor="middle">'
               '状态回写：app_set_input_* → 变量变化 → 控件自动刷新</text></g>')

    s.text(28, 640, "三后端同一组 io_* 签名：换硬件只换一个文件，UI 与 app_model 一行不改",
           9.5, PRI_TXT)


SCREENS = [
    ("mockup_01_list.svg", "01 · 列表主态（分组）",
     "已连接/已保存置顶分组 + 可用网络；行内含信号图示、名称、类型·强度·频段、锁、状态位",
     "01 列表主态：分组置顶（已连接 · 已保存 / 可用网络），行高 46、行距 6、状态位右缘统一", sc_list),
    ("mockup_02_scanning.svg", "02 · 扫描中",
     "骨架行占位 + 刷新按钮转圈 + 底部读取提示",
     "02 扫描中：4 行骨架占位，刷新按钮呈扫描态，底部提示正在读取结果", sc_scanning),
    ("mockup_03_empty.svg", "03 · 无网络（空态）",
     "WiFi 图标 + 文案 + 重新扫描主按钮",
     "03 空态：WiFi 图标 + 「未发现网络」+ 引导文案 + 重新扫描按钮", sc_empty),
    ("mockup_04_password.svg", "04 · 密码页（未聚焦）",
     "返回 + SSID + 密码框 + 记住密码开关 + 连接 + 忘记此网络",
     "04 密码页（键盘未弹出）：密码框聚焦描边、记住密码开关（默认关）、整宽连接按钮", sc_password),
    ("mockup_05_password_keyboard.svg", "05 · 密码页（键盘弹出）",
     "点密码框后键盘自底部弹出，内容区上压，完成键收起",
     "05 键盘弹出态：点按密码框弹出，四行键盘 + 右下「完成」收起", sc_password_kb),
    ("mockup_06_connecting.svg", "06 · 连接中",
     "目标行蓝色强调 + 连接中胶囊 + 底部进度提示",
     "06 连接中：目标行蓝描边、状态位「连接中」、底部转圈提示", sc_connecting),
    ("mockup_07_failed.svg", "07 · 连接失败",
     "目标行红描边 + 失败胶囊 + 底部红色错误条",
     "07 连接失败：目标行红描边、状态位「连接失败」、底部「密码错误」错误条", sc_failed),
    ("mockup_08_forget_confirm.svg", "08 · 忘记网络确认",
     "长按行触发：遮罩 + 确认卡（取消 / 忘记）",
     "08 忘记确认：长按已保存网络 → 遮罩 + 确认弹层，忘记为危险色按钮", sc_forget),
    ("mockup_09_embedded.svg", "09 · 组件内嵌容器",
     "同一组件放进设置页卡片，尺寸随容器自适应",
     "09 组件内嵌：同一组件放进设置页卡片，行宽/字号随容器自适应（容器 408×176）", sc_embedded),
    ("mockup_10_page_layers.svg", "10 · 页面层级（密码页覆盖列表）",
     "密码页 = 独立整页，覆盖在列表之上；返回即回列表且状态保留",
     "10 页面层级：① 列表（实例保留）→ 点行 → ② 密码整页覆盖；返回/完成 → 回 ①，扫描结果与滚动位置不变",
     sc_layers),
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
    p = build_wide("mockup_12_explain_keyboard.svg", "解释图 · 键盘为什么要整页",
                   "场景（列表在子容器）→ 键盘宽度对比（28.4/34.8/42.8）→ 结论",
                   528, sc_explain)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    p = build_wide("mockup_14_arch_flow.svg", "架构图 · EEZ 与硬件的数据流",
                   "EEZ 层 → 变量表 → app_model → io 后端；命令向下、状态向上",
                   660, sc_arch)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    p = build_wide("mockup_13_popup_forms.svg", "解释图 · 连接页两种弹出形态",
                   "列表在子容器 → 点连接 → 半页（200）或整页（320）弹出 + 对比表",
                   524, sc_popup_forms)
    total += os.path.getsize(p)
    print("written:", os.path.basename(p), os.path.getsize(p), "bytes")
    print("total:", total, "bytes")
