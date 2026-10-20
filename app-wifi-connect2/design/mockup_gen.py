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
    print("total:", total, "bytes")
