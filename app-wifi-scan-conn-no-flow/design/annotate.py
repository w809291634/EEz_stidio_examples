# -*- coding: utf-8 -*-
"""annotate.py —— 第②步：控件标注图（单页徽标 + 树状总览）

数据全部来自本文件的 CONTROLS 注册表（唯一真值），图由脚本生成，**禁止手 P 图**。
底图直接内嵌 design/mockups 里同一份设计图（base64），所以设计图改了重跑本脚本即可。

标注口径（kit NO_FLOW §2.1）：
  · 徽标 = **分类序号**：1按钮 2开关 3滑条 4列表 5步进 6chips 7按键网格
  · 连线颜色：绿 = UI 内部切换，红 = 输出硬件/手机
  · 未列入 CONTROLS 的对象 = 纯展示，不接行为
"""
import base64
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOCK = os.path.join(HERE, "mockups")
OUT = os.path.join(ROOT, "designer_annotated")

SCREEN_W, SCREEN_H = 480, 320
FRAME = (40, 40, 1.25)          # 与 mockup_gen.build() 的外框变换一致

CAT = {1: ("按钮", "#5B8CFF"), 2: ("开关", "#8A6BFF"), 3: ("滑条", "#26C6DA"),
       4: ("列表", "#2E9F79"), 5: ("步进", "#FFB300"), 6: ("chips", "#FF8A3D"),
       7: ("按键网格", "#FF5B8D")}

# ---- 控件注册表：screen -> [ (分类, 序号, id, 文案/名称, 框(x,y,w,h), 去向) ] ----
# ★ 框坐标**从设计源取**（mockup_gen 的几何常量），不在这里手抄 ——
#   空态按钮曾抄错成 (190,236,100,30)，标到了文案上，见 FIXLOG。
#   去向: ("ui", 目标) = UI 内部切换（绿）；("hw", 说明) = 输出硬件/手机（红）；None = 纯展示
import mockup_gen as M

_SY = M.SHEET_Y
HEAD = [
    (1, 1, "btn_refresh", "刷新", M.HEAD_BTN, ("hw", "发起 Wi-Fi 扫描")),
]
LIST = [
    (4, 1, "list_box", "网络列表（可滚动）", (16, 64, 448, 242), ("ui", "长按行 → 忘记对话框")),
]
SHEET = [
    (1, 2, "btn_pwd_close", "×", (436, _SY + 15, 28, 20), ("ui", "关闭半页")),
    (1, 3, "btn_connect", "连接",
     (M.SHEET_BTN[0], _SY + M.SHEET_BTN[1], M.SHEET_BTN[2], M.SHEET_BTN[3]),
     ("hw", "下发 SSID+密码给 Wi-Fi")),
    (7, 1, "kb_main", "键盘（LVGL buttonmatrix）",
     (M.SHEET_KB[0], _SY + M.SHEET_KB[1], M.SHEET_KB[2], M.SHEET_KB[3]), None),
]
DIALOG = [
    (1, 4, "btn_forget", "忘记", M.DIALOG_BTN_L, ("hw", "删除已保存密码")),
    (1, 5, "btn_cancel", "取消", M.DIALOG_BTN_R, ("ui", "关闭对话框")),
]
EMPTY = [
    (1, 6, "btn_rescan", "重新扫描", M.EMPTY_BTN, ("hw", "发起 Wi-Fi 扫描")),
]

CONTROLS = {
    "mockup_01_list":       HEAD + LIST,
    "mockup_02_scanning":   HEAD + LIST,
    "mockup_03_empty":      HEAD + EMPTY,   # 空态里「刷新」也在，别漏标
    # 半页那几张不重复标列表：它被遮罩盖住了，01 已标
    "mockup_04_sheet":      HEAD + SHEET,
    "mockup_05_sheet_error": HEAD + SHEET,
    "mockup_06_connecting": HEAD + SHEET,
    "mockup_07_failed":     HEAD + SHEET,
    "mockup_10_connected":  HEAD + LIST,
    "mockup_11_menu":       HEAD + LIST + DIALOG,
}

DESC = {
    "mockup_01_list": "列表主态：三种行状态（已连接/已保存/无需密码），行内无控件，整行可点",
    "mockup_02_scanning": "扫描中：刷新键变「扫描中」，列表骨架占位，状态只在标题栏",
    "mockup_03_empty": "空态：仅一个重新扫描按钮",
    "mockup_04_sheet": "连接半页：密码框 + 连接键 + 键盘；overlay 挂 screen 根",
    "mockup_05_sheet_error": "密码错误：错误就地显示在标题行，键盘不收起",
    "mockup_06_connecting": "连接中：连接键禁用，防重复投递",
    "mockup_07_failed": "连接失败：行状态胶囊 + 红标题",
    "mockup_10_connected": "连接成功：半页收起，行转绿",
    "mockup_11_menu": "忘记确认对话框：左忘记 / 右取消",
}


def _n(v):
    return ("%.1f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def base_image(name):
    raw = io.open(os.path.join(MOCK, name + ".svg"), "rb").read()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def badge(x, y, txt, col, r=9):
    return ('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="#0B0F1A" stroke-width="1.4"/>'
            '<text x="%s" y="%s" fill="#0A1020" font-size="11" font-weight="700" '
            'text-anchor="middle">%s</text>' % (_n(x), _n(y), _n(r), col,
                                                _n(x), _n(y + 4), txt))


def annotate(name, items):
    ox, oy, k = FRAME
    parts = [
        '<svg viewBox="0 0 680 500" width="100%" role="img" '
        'xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Microsoft YaHei, sans-serif">',
        '  <title>%s · 控件标注</title>' % _esc(name),
        # 用嵌套 viewBox 把设计图的"设备区"(40,40,600,400) 裁出来，避免整张画布被二次缩放
        '  <svg x="40" y="24" width="600" height="400" viewBox="40 40 600 400">',
        '    <image x="0" y="0" width="680" height="500" href="%s"/>' % base_image(name),
    ]
    # 徽标 = **屏内统一序号**（1..N，阅读顺序），分类靠颜色区分 —— 每类各自从 1 起会撞号
    for i, (cat, _num, ident, label, (x, y, w, h), dest) in enumerate(items, 1):
        col = "#2E9F79" if (dest and dest[0] == "ui") else "#FF5B5B" if dest else "#7C8AA5"
        bx, by = ox + x * k, oy + y * k
        bw, bh = w * k, h * k
        parts.append('    <rect x="%s" y="%s" width="%s" height="%s" rx="4" fill="none" '
                     'stroke="%s" stroke-width="1.8" stroke-dasharray="%s"/>'
                     % (_n(bx), _n(by), _n(bw), _n(bh), col, "0" if dest else "5 4"))
        parts.append("    " + badge(bx + bw - 4, by + 4, "%d" % i, CAT[cat][1], 10))
    parts.append("  </svg>")
    parts.append('  <text x="40" y="444" fill="#7C8AA5" font-size="12">'
                 '实线框=有行为 · 虚线框=纯展示 · 徽标数字=本屏序号</text>')
    lx = 40
    for k2, (label, col2) in CAT.items():
        parts.append('  <circle cx="%s" cy="460" r="5" fill="%s"/>' % (_n(lx), col2))
        parts.append('  <text x="%s" y="464" fill="#7C8AA5" font-size="12">%s %s</text>'
                     % (_n(lx + 9), k2, label))
        lx += 30 + 13 * len(label)
    parts.append('  <text x="40" y="486" fill="#7C8AA5" font-size="12">'
                 '绿框=UI 内部切换 · 红框=输出硬件/手机</text>')
    parts.append("</svg>")
    path = os.path.join(OUT, name + "_annot.svg")
    io.open(path, "w", encoding="utf-8").write("\n".join(parts) + "\n")
    return path


def base_image_for(name):
    """树节点用**已标注**缩略图（§2.1）；标注图不在就退回原设计图。"""
    p = os.path.join(OUT, name + "_annot.svg")
    if not os.path.exists(p):
        p = os.path.join(MOCK, name + ".svg")
    raw = io.open(p, "rb").read()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def tree():
    """树状总览：根=scr_main；两行四列；节点=已标注缩略图（含框与徽标）；直角连线挂发起控件徽标。"""
    W, H = 1320, 700
    S = 0.56                     # 缩略比例：268.8x179.2（NO_FLOW §2.1 要求节点边长 >=260）
    NW, NH = 480 * S, 320 * S
    ROW1, ROW2 = 110, 400
    COL = [40, 360, 680, 1000]
    nodes = [
        ("mockup_01_list",      COL[0], ROW1, "01 列表主态"),
        ("mockup_04_sheet",     COL[1], ROW1, "04 连接半页"),
        ("mockup_06_connecting", COL[2], ROW1, "06 连接中"),
        ("mockup_10_connected", COL[3], ROW1, "10 连接成功"),
        ("mockup_02_scanning",  COL[0], ROW2, "02 扫描中"),
        ("mockup_03_empty",     COL[1], ROW2, "03 空态"),
        ("mockup_05_sheet_error", COL[2], ROW2, "05 密码错误"),
        ("mockup_11_menu",      COL[3], ROW2, "11 忘记对话框"),
    ]
    pos = {n: (x, y) for n, x, y, _l in nodes}
    parts = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" '
             'xmlns="http://www.w3.org/2000/svg" '
             'font-family="Segoe UI, Microsoft YaHei, sans-serif">' % (W, H),
             '<rect x="0" y="0" width="%d" height="%d" fill="#0B0F1A"/>' % (W, H),
             '<text x="24" y="34" fill="#F0F4FC" font-size="17" font-weight="600">'
             'app-wifi-scan-conn-no-flow · 控件树状总览</text>',
             '<text x="24" y="56" fill="#7C8AA5" font-size="12">'
             '绿线=UI 内部切换 · 红线=输出硬件/手机 · 节点=已标注缩略图 · 徽标=发起控件序号</text>']

    for name, x, y, label in nodes:
        parts.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#111827" '
                     'stroke="#26314A" stroke-width="1"/>'
                     % (_n(x), _n(y), _n(NW), _n(NH)))
        parts.append('<svg x="%s" y="%s" width="%s" height="%s" viewBox="40 40 600 400">'
                     '<image x="0" y="0" width="680" height="500" href="%s"/></svg>'
                     % (_n(x), _n(y), _n(NW), _n(NH),
                        base_image_for(name)))
        parts.append('<text x="%s" y="%s" fill="#9DB8FF" font-size="13">%s</text>'
                     % (_n(x), _n(y - 8), _esc(label)))

    def edge(pts, kind, tag):
        col = "#2E9F79" if kind == "ui" else "#FF5B5B"
        d = "M " + " L ".join("%s %s" % (_n(a), _n(b)) for a, b in pts)
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.8" '
                     'opacity="0.95"/>' % (d, col))
        mx, my = pts[len(pts) // 2]
        parts.append('<circle cx="%s" cy="%s" r="11" fill="%s" stroke="#0B0F1A" '
                     'stroke-width="1.4"/>' % (_n(mx), _n(my), col))
        parts.append('<text x="%s" y="%s" fill="#04101A" font-size="10" font-weight="700" '
                     'text-anchor="middle">%s</text>' % (_n(mx), _n(my + 3.6), _esc(tag)))

    def P(name, side):
        x, y = pos[name]
        return {"l": (x, y + NH / 2), "r": (x + NW, y + NH / 2),
                "t": (x + NW / 2, y), "b": (x + NW / 2, y + NH)}[side]

    parts.append('<circle cx="%s" cy="112" r="7" fill="#5B8CFF"/>' % _n(pos["mockup_01_list"][0] + NW / 2))
    parts.append('<text x="%s" y="96" fill="#9DB8FF" font-size="12" text-anchor="middle">scr_main</text>'
                 % _n(pos["mockup_01_list"][0] + NW / 2))

    # 同行横向
    a, b = P("mockup_01_list", "r"), P("mockup_04_sheet", "l")
    edge([a, b], "ui", "行")
    a, b = P("mockup_04_sheet", "r"), P("mockup_06_connecting", "l")
    edge([a, b], "hw", "连")
    a, b = P("mockup_06_connecting", "r"), P("mockup_10_connected", "l")
    edge([a, b], "hw", "成功")
    # 同列纵向
    a, b = P("mockup_01_list", "b"), P("mockup_02_scanning", "t")
    edge([a, b], "hw", "刷新")
    a, b = P("mockup_02_scanning", "r"), P("mockup_03_empty", "l")
    edge([a, b], "ui", "空")
    a, b = P("mockup_04_sheet", "b"), P("mockup_05_sheet_error", "t")
    edge([a, b], "hw", "失败")
    a, b = P("mockup_05_sheet_error", "r"), P("mockup_06_connecting", "b")
    edge([a, P("mockup_05_sheet_error", "r"), (b[0], a[1]), b], "hw", "重试")
    # 长按（绕到底部，避免穿节点）
    x0, y0 = pos["mockup_01_list"]
    x1, y1 = pos["mockup_11_menu"]
    yb = 600
    edge([(x0 + NW / 2, y0 + NH), (x0 + NW / 2, yb), (x1 + NW / 2, yb),
          (x1 + NW / 2, y1 + NH)], "ui", "长按")

    parts.append("</svg>")
    path = os.path.join(OUT, "_tree.svg")
    io.open(path, "w", encoding="utf-8").write("\n".join(parts) + "\n")
    return path



def table():
    """控件清单表（与图同源生成，别手写）。"""
    rows = ["# 控件清单（由 design/annotate.py 从 CONTROLS 生成）", "",
            "| 屏 | 徽标 | 分类 | identifier | 名称 | 框 (x,y,w,h) | 去向 |",
            "|---|---|---|---|---|---|---|"]
    for name, items in CONTROLS.items():
        for i, (cat, _num, ident, label, (x, y, w, h), dest) in enumerate(items, 1):
            if dest and dest[0] == "ui":
                where = "UI → " + dest[1]
            elif dest:
                where = "硬件/手机 → " + dest[1]
            else:
                where = "纯展示"
            rows.append("| %s | %d | %s | `%s` | %s | (%d,%d,%d,%d) | %s |"
                        % (name, i, CAT[cat][0], ident, label, x, y, w, h, where))
    rows.append("")
    rows.append("> 未列入本表的对象 = 纯展示，不接任何行为（kit NO_FLOW §2.1）。")
    path = os.path.join(OUT, "控件清单.md")
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, items in CONTROLS.items():
        print("annot:", os.path.basename(annotate(name, items)))
    print("tree  :", os.path.basename(tree()))
    print("table :", os.path.basename(table()))


if __name__ == "__main__":
    main()
