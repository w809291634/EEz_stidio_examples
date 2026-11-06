# -*- coding: utf-8 -*-
"""EEZ 工程生成器（第④步，分阶段）：先跑通「主控」一屏。

真值来源：design/pages.py 的 _main_rows()（控件名/类型/行为/框）+ design/simple_control.py 的几何常量。
本阶段约束（2026-11-04 用户定，先跑通再加码）：
  · 只出 1 屏；无自定义字体（先用默认字体，中文会显示为默认字形，④-2 再烘子集）
  · 无 action：no flow 的跳转/动作由 native 接，工程里只放界面树
  · 每个控件都带 localStyles（内边距/圆角/底色），保证在 EEZ 里不是裸控件

用法：python design/eez_gen.py        # 产物：w78-smart-home.eez-project
"""
import copy
import io
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# 控件只从根目录 eez-widget-templates 克隆（禁止手拼字段）
sys.path.insert(0, os.path.dirname(ROOT))
from eez_widget_clone import clone, clone_dict   # noqa: E402

import pages as pg                  # noqa: E402
import overview_pro as ov           # noqa: E402  io_of 是六类判定的唯一实现
from texts import TEXTS             # noqa: E402
import re                           # noqa: E402
import simple_control as sc         # noqa: E402

OUT = os.path.join(ROOT, "w78-smart-home.eez-project")
FONT_DIR = os.path.join(ROOT, "fonts")
FONT_FILE = "fonts/cn14.ttf"
FONT_NAME = "cn12"
# EEZ 用页名生成 C 标识符；中文会被消成 "_" 而互相撞车（实测 23 页全变 SCREEN_ID___）
PAGE_IDS = {
    "主控": "main", "客厅": "living", "主卧": "master", "厨房": "kitchen", "浴室": "bath",
    "灯详情": "detail_light", "空调详情": "detail_ac", "窗帘详情": "detail_curtain",
    "传感详情": "detail_sensor", "摄像头详情": "detail_camera", "插座详情": "detail_plug",
    "通知中心": "notify", "能源统计": "energy", "设置": "settings", "全部设备": "devices",
    "安防": "security", "场景详情": "scene_detail", "添加设备·选类型": "add_type",
    "添加设备·配网中": "add_pairing", "添加设备·完成": "add_done", "关于": "about",
    "离线态": "offline", "空房间": "empty_room",
    "Wi-Fi 设置": "wifi",
}


def font_sizes():
    """镜像字库策略：全工程只用 3 档；只有 12px 带汉字，24/32 只放 ASCII。"""
    return [sc.UI_CN, sc.UI_NUM, sc.UI_BIG]

def font_name(size):
    return "cn%d" % int(size)

# 运行时字符集只挂在正文号（12/18）上：同字号共用一条字体条目，不再另建 *f 档
RT_SIZES = {12}
ASCII_SIZES = {24, 32}


def gb2312_level1():
    out = set()
    for hi in range(0xA1, 0xD8):      # 含 A1–A9 符号区（· 、 等）+ 一级汉字
        for lo in range(0xA1, 0xFF):
            try:
                out.add(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    return out


def runtime_chars():
    # U+00B7 中点不在 GB2312 A1 区（那里是 U+30FB），单独补
    return {chr(c) for c in range(32, 127)} | gb2312_level1() | {"·", "×"}
FONT_SIZE = 14
SRC_TTF = os.path.join(os.path.dirname(ROOT), "app-wifi-scan-flow-no-flow", "fonts", "simhei.ttf")
SETTINGS_SRC = os.path.join(os.path.dirname(ROOT), "app-wifi-scan-flow-no-flow",
                            "app-wifi-scan-flow-no-flow.eez-project")
# 黑体里没有的装饰字符 → 用等价 ASCII 顶上（否则界面上是豆腐块）
SUBST = {"‹": "<", "›": ">", "−": "-", "▶": ">", "◀": "<", "✓": "√", "✔": "√"}
W, H = 800, 480


def charset():
    """全工程要显示的字符：23 屏帧内文本 + 控件名 + ASCII。"""
    chars = set(chr(c) for c in range(32, 127))
    for _t, frame, _entry, _exit, _rows in pg.PAGES:
        chars |= set(re.sub(r"<[^>]+>", "", frame or ""))
        for row in (_rows or []):
            chars |= set(str(row[0]))
    chars = {c for c in chars if c.strip() or c == " "}
    # 子集必须按"替换后"的字符集裁（设计里的 ✓ 会显示成 √）
    return {SUBST.get(c, c) for c in chars}


def _src_cmap():
    from fontTools.ttLib import TTFont
    tt = TTFont(SRC_TTF)
    cmap = set(tt.getBestCmap().keys())
    tt.close()
    return cmap


def _fix_text(t):
    return "".join(SUBST.get(c, c) for c in t)


def subset_font(chars):
    """把系统黑体裁成只含需要字形的 TTF（EEZ 打开工程时据此烘焙）。"""
    from fontTools import subset
    os.makedirs(FONT_DIR, exist_ok=True)
    out = os.path.join(ROOT, FONT_FILE.replace("/", os.sep))
    opts = subset.Options()
    opts.layout_features = []
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    cmap = _src_cmap()
    font = subset.load_font(SRC_TTF, opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=[ord(c) for c in chars])
    chars = {c for c in chars if ord(c) in cmap}
    sub.subset(font)
    subset.save_font(font, out, opts)
    return out, len(chars)


def _runs(codes):
    """[码点] → [{from,to}] 连续段（EEZ 的 lvglGlyphs.encodings 格式）。"""
    out = []
    for c in sorted(codes):
        if out and c == out[-1]["to"] + 1:
            out[-1]["to"] = c
        else:
            out.append({"from": c, "to": c})
    return out


def _range_str(runs):
    return ",".join(str(r["from"]) if r["from"] == r["to"]
                    else "%d-%d" % (r["from"], r["to"]) for r in runs)


def _force_font(node):
    """把模板里出现的 text_font 统一改成本工程的字体名。"""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "text_font":
                node[k] = FONT_NAME
            else:
                _force_font(v)
    elif isinstance(node, list):
        for x in node:
            _force_font(x)
    return node


def fresh(spec):
    """克隆标准模板（"A" 或 "A+B"）／深拷贝字典块，换新 objID，并复位"表达式型"属性。

    控件字段集只来自根目录 eez-widget-templates（禁止手拼字段）；
    采来的模板会带别的工程的表达式（如 hiddenFlag: "pick_ssid == ''"），
    不清掉会生成 get_var_pick_ssid…() 这种未声明调用 → C 编译报错。
    """
    node = clone(spec) if isinstance(spec, str) else clone_dict(spec)

    def reset(n):
        if isinstance(n, dict):
            if "hiddenFlag" in n:
                n["hiddenFlagType"] = "literal"
                n["hiddenFlag"] = False
            for k in ("checkedStateType", "disabledStateType", "clickableFlagType"):
                if k in n:
                    n[k] = "literal"
            for v in n.values():
                reset(v)
        elif isinstance(n, list):
            for x in n:
                reset(x)
    reset(node)
    return node


def oid():
    return str(uuid.uuid4())


PAD0 = {"pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
        "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0}

# 各类型的设计基础样式（配色/内边距/圆角属工程设计令牌；模板只提供字段集）
BASE_STYLE = {
    "LVGLScreenWidget": {"MAIN": {"DEFAULT": {"bg_color": "0x101828", "bg_opa": 255,
                                              "radius": 0, "border_width": 0}}},
    "LVGLLabelWidget": {"MAIN": {"DEFAULT": dict(PAD0, text_color="0xFFFFFF",
                                                 text_font="cn12")}},
    "LVGLContainerWidget": {"MAIN": {"DEFAULT": dict(PAD0, bg_color="0x1A2438",
                                                     bg_opa=255, radius=12)}},
    "LVGLButtonWidget": {"MAIN": {"DEFAULT": dict(PAD0, bg_color="0x1c2440",
                                                  bg_opa=255, radius=8)}},
    "LVGLListWidget": {"MAIN": {"DEFAULT": dict(PAD0, bg_color="0x0b0f1a",
                                                bg_opa=0, radius=0)}},
    "LVGLChartWidget": {"MAIN": {"DEFAULT": dict(PAD0, bg_color="0x0C1220", bg_opa=255,
                                                 radius=8, line_width=0,
                                                 line_color="0x000000", line_opa=0)}},
    "LVGLBarWidget": {
        "MAIN": {"DEFAULT": dict(pad_top=4, pad_bottom=8, **{k: 0 for k in
                                                             ("pad_left", "pad_right", "pad_row",
                                                              "pad_column", "border_width", "outline_width")},
                                 bg_color="0x222B38", radius=4)},
        "INDICATOR": {"DEFAULT": {"bg_color": "0xF2B45C", "radius": 4}},
    },
    "LVGLSliderWidget": {
        "MAIN": {"DEFAULT": dict(PAD0, pad_bottom=14, bg_color="0x222B38", radius=3)},
        "INDICATOR": {"DEFAULT": {"bg_color": "0xF2B45C", "radius": 3}},
        "KNOB": {"DEFAULT": {"bg_color": "0xFFFFFF", "radius": 60}},
    },
    "LVGLSwitchWidget": {
        "MAIN": {"DEFAULT": dict(PAD0, bg_color="0x222B38", bg_opa=255, radius=15),
                 "CHECKED": dict(PAD0, bg_color="0xF2B45C", bg_opa=255, radius=15)},
        "INDICATOR": {"DEFAULT": dict(PAD0, bg_color="0xF2B45C", bg_opa=0),
                      "CHECKED": dict(PAD0, bg_color="0xF2B45C", bg_opa=255)},
        "KNOB": {"DEFAULT": dict(PAD0, bg_color="0xFFFFFF", bg_opa=255, radius=15),
                 "CHECKED": dict(PAD0, bg_color="0xFFFFFF", bg_opa=255, radius=15)},
    },
    "LVGLTextareaWidget": {"MAIN": {"DEFAULT": {
        "pad_top": 8, "pad_bottom": 8, "pad_left": 8, "pad_right": 0,
        "pad_row": 0, "pad_column": 0, "border_width": 1, "outline_width": 0,
        "bg_color": "0x101a28", "bg_opa": 255, "radius": 8,
        "border_color": "0x26314a", "text_color": "0xf0f4fc", "text_font": "cn12"}}},
    "LVGLKeyboardWidget": {"MAIN": {"DEFAULT": {
        "align": "TOP_LEFT", "pad_top": 0, "pad_bottom": 0, "pad_left": 0,
        "pad_right": 0, "pad_row": 4, "pad_column": 4, "border_width": 0,
        "outline_width": 0, "bg_color": "0x1c2440", "bg_opa": 255, "radius": 0}}},
}


def _widget(spec):
    """克隆模板（"A"/"A+B"）并套本工程的设计基础样式。"""
    node = fresh(spec)
    if spec in BASE_STYLE:
        node["localStyles"]["definition"] = copy.deepcopy(BASE_STYLE[spec])
    if "flagScrollbarMode" in node:
        node["flagScrollbarMode"] = "OFF"       # 设计不带滚动条（列表在 make_list 里单独设 AUTO）
    return node


def _static(n):
    """纯展示件不吃滚动/焦点：模板默认带 SCROLLABLE|ELASTIC|MOMENTUM，会把拖动变成滑动内容。"""
    keep = {"GESTURE_BUBBLE", "SCROLL_CHAIN_HOR", "SCROLL_CHAIN_VER"}
    n["widgetFlags"] = "|".join(x for x in str(n.get("widgetFlags", "")).split("|")
                                if x in keep)
    return n


def design_texts(frame):
    """从设计帧 SVG 里抽出 <text>：位置/字号/颜色/对齐/内容（文字的唯一真值）。"""
    out = []
    for m in re.finditer(r'<text([^>]*)>([^<]*)</text>', frame or ""):
        attrs, txt = m.group(1), m.group(2)
        if not txt.strip():
            continue
        def a(name, d=None):
            mm = re.search(name + r'="([^"]*)"', attrs)
            return mm.group(1) if mm else d
        out.append({
            "x": float(a("x", 0)), "y": float(a("y", 0)),
            "size": float(a("font-size", 14)),
            "fill": a("fill", "0xF4F7FB").upper().replace("#", "0x"),
            "anchor": a("text-anchor", "start"),
            "text": txt,
        })
    return out


def design_rects(frame):
    """设计帧里的矩形/圆形底板：位置/尺寸/填充/圆角（排除整屏背景）。"""
    out = []
    for m in re.finditer(r'<rect([^>]*?)/?>', frame or ""):
        a = m.group(1)
        def g(n, d=None):
            mm = re.search(n + r'="([^"]*)"', a)
            return mm.group(1) if mm else d
        x, y, w, h = (float(g("x", 0)), float(g("y", 0)),
                      float(g("width", 0)), float(g("height", 0)))
        if w >= 799 and h >= 479:
            continue
        fill = (g("fill", "") or "").strip().upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", fill):
            continue                      # none / url(#..) / 命名色：写进 EEZ 会报 invalid color
        out.append({"box": (int(x), int(y), int(w), int(h)),
                    "fill": fill.replace("#", "0x"),
                    "rx": int(float(g("rx", 0) or 0))})
    for m in re.finditer(r'<circle([^>]*?)/?>', frame or ""):
        a = m.group(1)
        def g(n, d=None):
            mm = re.search(n + r'="([^"]*)"', a)
            return mm.group(1) if mm else d
        cx, cy, rad = float(g("cx", 0)), float(g("cy", 0)), float(g("r", 0))
        fill = (g("fill", "") or "").strip().upper()
        if rad <= 0 or not re.fullmatch(r"#[0-9A-F]{6}", fill):
            continue
        out.append({"box": (int(cx - rad), int(cy - rad), int(rad * 2), int(rad * 2)),
                    "fill": fill.replace("#", "0x"),
                    "rx": int(rad)})
    return out


def _no_scroll(n):
    """卡片不做滚动容器：设计里卡片是静态底板，拖动不该让卡内子件滑动（只保留事件链）。"""
    keep = {"CLICK_FOCUSABLE", "GESTURE_BUBBLE", "PRESS_LOCK",
            "SCROLL_CHAIN_HOR", "SCROLL_CHAIN_VER"}
    n["widgetFlags"] = "|".join(x for x in str(n.get("widgetFlags", "")).split("|")
                                if x in keep)
    return n


def make_label(ident, text, box, color=None, size=None):
    """标签 = 默认 LVGLLabelWidget 克隆，只改几何/文本/字色。"""
    c = _static(_force_font(_widget("LVGLLabelWidget")))
    x, y, w, h = box
    if size:
        c["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_font"] = font_name(size)
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h,
              "widthUnit": "px", "heightUnit": "px",
              "text": _fix_text(text), "textType": "literal", "useStaticText": True})
    if color:
        c["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_color"] = color
    return c


def make_button(ident, text, box, bg=None, radius=None, fg=None):
    """按钮 = 默认 LVGLButtonWidget 克隆 + 一个默认 LVGLLabelWidget 子节点承载文字。

    EEZ 的按钮没有 text 字段；文字必须放在子标签里（align=CENTER）。
    """
    b = _widget("LVGLButtonWidget")
    x, y, w, h = box
    b.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    main = b["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    if bg:
        main["bg_color"] = bg
    if radius is not None:
        main["radius"] = radius
    lb = _static(_widget("LVGLButtonWidget+LVGLLabelWidget"))
    lb.update({"identifier": ident + "_lb",
               "left": 0, "top": 0, "width": w, "height": h,
               "text": _fix_text(text), "textType": "literal", "useStaticText": True})
    lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_font"] = "cn12"
    if fg:
        lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_color"] = fg
    b["children"] = [lb]
    return b


def make_screen():
    """根 = 默认 LVGLScreenWidget 克隆。"""
    c = _widget("LVGLScreenWidget")
    c.update({"left": 0, "top": 0, "width": W, "height": H, "children": []})
    d = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    d.update({"bg_color": "0x05080F", "bg_opa": 255})
    return c


def no_click(n):
    """纯展示/装饰容器不该吃点击：点击由 clickableFlag 表达，否则会盖住下层按钮。"""
    keep = {"GESTURE_BUBBLE", "SCROLL_CHAIN_HOR", "SCROLL_CHAIN_VER"}
    n["widgetFlags"] = "|".join(x for x in str(n.get("widgetFlags", "")).split("|")
                                if x in keep)
    if "clickableFlag" in n:
        n["clickableFlag"] = False
        n["clickableFlagType"] = "literal"


def make_container(ident, box, bg=None, radius=None, text="", color=None):
    """卡片 = 默认 LVGLContainerWidget + 居中子标签（容器本身没有 text 字段）。"""
    c = _no_scroll(_widget("LVGLContainerWidget"))
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    main = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    if bg:
        main["bg_color"] = bg
    if radius is not None:
        main["radius"] = radius
    if text:
        lb = _widget("LVGLContainerWidget+LVGLLabelWidget")
        lb.update({"left": 0, "top": 0, "width": w, "height": h,
                   "text": _fix_text(text), "textType": "literal", "useStaticText": True})
        d = lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]
        d["align"] = "CENTER"
        if color:
            d["text_color"] = color
        c["children"] = [lb]
    return c


def make_switch(ident, box, on=False):
    c = _widget("LVGLSwitchWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    if on:
        c["states"] = "CHECKED"      # EEZ 会生成 LV_STATE_<值>
    return c


def make_slider(ident, box, value=0):
    c = _widget("LVGLSliderWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    if "value" in c:
        c["value"] = value
    return c


def make_list(ident, box):
    c = _widget("LVGLListWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h,
              "flagScrollbarMode": "AUTO"})
    d = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    d["bg_opa"] = 0
    d["radius"] = 0
    return c


def make_textarea(ident, box, placeholder):
    c = _widget("LVGLTextareaWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h,
              "text": "", "textType": "literal", "placeholder": placeholder,
              "oneLineMode": True, "passwordMode": True, "maxTextLength": 64})
    d = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    d["bg_color"] = "0x1C2430"
    d["bg_opa"] = 255
    d["radius"] = 8
    d["border_width"] = 1
    d["border_color"] = "0x27313F"
    d["text_color"] = "0xF4F7FB"
    d["text_font"] = "cn12"
    return c


def make_keyboard(ident, box, ta_ident):
    c = _widget("LVGLKeyboardWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h,
              "textarea": ta_ident, "mode": "TEXT_LOWER"})
    d = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    d["align"] = "TOP_LEFT"          # lv_keyboard 构造会先 BOTTOM_MID，必须覆盖
    d["bg_color"] = "0x101720"
    d["bg_opa"] = 255
    d["radius"] = 0
    d["pad_top"] = 0
    d["pad_bottom"] = 0
    d["pad_left"] = 0
    d["pad_right"] = 0
    d["border_width"] = 0
    return c


def _hide(n):
    n["hiddenFlagType"] = "literal"
    n["hiddenFlag"] = True
    return n


def widget_kind(nm, cat, box):
    """设计标注 → EEZ 真实控件类型；不再用透明容器冒充交互控件。"""
    if cat == "toggle":
        return "switch"
    if cat == "slider":
        return "slider"
    if cat in ("value", "uivalue"):
        return "label"
    if cat in ("nav", "back") and box[2] <= 200:
        return "button"
    if cat == "scene" and box[2] <= 220:
        return "button"
    if cat == "read":
        if nm in ("搜索框", "设备名称"):
            return "textarea"
        if nm == "进度":
            return "bar"
        if "曲线" in nm or "占比" in nm:
            return "chart"
    return "container"


def _inside(inner, outer):
    return (inner[0] >= outer[0] and inner[1] >= outer[1] and
            inner[0] + inner[2] <= outer[0] + outer[2] and
            inner[1] + inner[3] <= outer[1] + outer[3])


def _texts_in(frame, box):
    return [t for t in design_texts(frame)
            if box[0] <= t["x"] <= box[0] + box[2] and
            box[1] <= t["y"] <= box[1] + box[3]]


def _value_ratio(frame, box, default=50):
    """从设计里的轨道/填充矩形宽度估当前值（0–100）。"""
    rs = [r["box"] for r in design_rects(frame) if _inside(r["box"], box)]
    widths = sorted({r[2] for r in rs})
    if len(widths) >= 2 and widths[-1] > 0:
        return int(round(widths[-2] / float(widths[-1]) * 100))
    return default


def _switch_on(frame, box):
    """设计里开关旋钮在右半 → 开。"""
    rs = [r["box"] for r in design_rects(frame) if _inside(r["box"], box)]
    if not rs:
        return False
    knob = min(rs, key=lambda b: b[2] * b[3])
    return knob[0] + knob[2] / 2.0 > box[0] + box[2] / 2.0


def compound_kind(cat, box):
    """房间格等大卡片：交互区是整卡，开关/滑条只是卡内小件。"""
    return cat in ("toggle", "slider") and (box[2] > 120 or box[3] > 60)


def glyph_box(frame, kind, box):
    """从设计帧里找卡内开关轨道/滑条轨道的真实几何；找不到就用右下角兜底。"""
    rs = [r["box"] for r in design_rects(frame) if _inside(r["box"], box)]
    if kind == "switch":
        cand = [b for b in rs if 40 <= b[2] <= 50 and 22 <= b[3] <= 26]
        if cand:
            return cand[0]
        return (box[0] + box[2] - 58, box[1] + box[3] - 32, 44, 24)
    cand = [b for b in rs if b[3] <= 8 and b[2] >= 80]
    if cand:
        b = max(cand, key=lambda x: x[2])
        return (b[0], b[1] - 7, b[2], 20)
    return (box[0] + 14, box[1] + box[3] - 38, box[2] - 28, 20)


def make_bar(ident, box, value=50):
    c = _widget("LVGLBarWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    if "value" in c:
        c["value"] = value
    return c


def make_chart(ident, box):
    c = _widget("LVGLChartWidget")
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    c["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 0
    return c


def _lbl_font(lb, font="cn12"):
    lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_font"] = font
    return lb


def _btn_font(b, font="cn12"):
    lb = b.get("children", [None])[0]
    if lb:
        lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_font"] = font
    return b


def build_wifi_page(name, frame, first=False):
    """Wi-Fi 连接页：完全按 app-wifi-scan-conn-no-flow 的结构——
    一个空 lv_list（行由 native 动态建）+ 密码半页 overlay_root + 忘记对话框 dlg_root。"""
    slug = PAGE_IDS[name]
    page = {
        "objID": oid(), "name": slug, "left": 0, "top": 0, "width": W, "height": H,
        "isUsedAsUserWidget": False, "createAtStart": bool(first),
        "deleteOnScreenUnload": False,
        "connectionLines": [], "localVariables": [], "componentGroups": [],
        "userProperties": [], "components": [],
    }
    bb = sc.WIFI_BOXES
    kids = [
        make_button("%s_go01" % slug, TEXTS["wifi.back"], sc.SUB_BACK_BOX, "0x1C2430", 14, "0xF4F7FB"),
        _btn_font(make_button("btn_refresh", TEXTS["wifi.scan"], bb["scan"], "0x1C2430", 15, "0xF2B45C")),
        make_label("lbl_title", TEXTS["wifi.title"], (152, 22, 200, 36), "0xF4F7FB", 24),
        _lbl_font(make_label("lbl_status", TEXTS["wifi.status"], (152, 54, 620, 20), "0x75859C", 12)),
        make_list("list_box", bb["list"]),
    ]

    scrim = make_container("scrim", bb["scrim"], "0x000000", 0)
    scrim["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 115
    sheet_kids = [
        make_container("sheet_handle", (384, 6, 32, 3), "0x27313F", 2),
        make_label("lbl_pwd_ssid", "", (24, 10, 640, 28), "0xF4F7FB", 12),
        _btn_font(make_button("btn_pwd_close", TEXTS["wifi.close"], (752, 10, 32, 32), "0x1C2430", 16, "0xB9C4D4")),
        make_textarea("pwd_ta", (24, 66, 520, 40), TEXTS["wifi.pwd_placeholder"]),
        make_button("btn_connect", TEXTS["wifi.connect"], (560, 66, 216, 40), "0xF2B45C", 20, "0x05080F"),
        make_keyboard("kb_main", (24, 116, 752, 136), "pwd_ta"),
    ]
    sheet = make_container("sheet", (0, 220, 800, 260), "0x101720", 0)
    sheet["children"] = sheet_kids
    overlay = make_container("overlay_root", (0, 0, 800, 480), None, 0)
    overlay["children"] = [scrim, sheet]
    _hide(overlay)

    dscrim = make_container("dlg_scrim", (0, 0, 800, 480), "0x000000", 0)
    dscrim["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 140
    card_kids = [
        _lbl_font(make_label("lbl_dlg_title", TEXTS["wifi.forget_title"], (20, 20, 320, 24), "0xF4F7FB", 12)),
        _lbl_font(make_label("lbl_dlg_ssid", "", (20, 52, 320, 20), "0xB9C4D4", 12)),
        _lbl_font(make_label("lbl_dlg_hint", TEXTS["wifi.forget_hint"], (20, 78, 320, 40), "0x75859C", 12)),
        _btn_font(make_button("btn_dlg_forget", TEXTS["wifi.forget"], (20, 148, 96, 36), "0x3A1A18", 10, "0xFF7A6B")),
        _btn_font(make_button("btn_dlg_disconnect", TEXTS["wifi.disconnect"], (132, 148, 96, 36), "0x1C2430", 10, "0xF4F7FB")),
        _btn_font(make_button("btn_dlg_cancel", TEXTS["wifi.cancel"], (244, 148, 96, 36), "0x1C2430", 10, "0xF4F7FB")),
    ]
    card = make_container("dlg_card", (220, 140, 360, 200), "0x101720", 14)
    card["children"] = card_kids
    dlg = make_container("dlg_root", (0, 0, 800, 480), None, 0)
    dlg["children"] = [dscrim, card]
    _hide(dlg)
    kids += [overlay, dlg]

    root = make_screen()
    root["children"] = kids
    page["components"].append(root)
    return page


def build_page(name, frame, rows, first=False):
    """通用页：底板(设计矩形) → 控件(控件表) → 文字(设计帧) → 小装饰(最上层)。"""
    page = {
        "objID": oid(), "name": PAGE_IDS.get(name, "page"),
        "left": 0, "top": 0, "width": W, "height": H,
        "isUsedAsUserWidget": False, "createAtStart": bool(first),
        "deleteOnScreenUnload": False,
        "connectionLines": [], "localVariables": [], "componentGroups": [],
        "userProperties": [], "components": [],
    }
    slug = PAGE_IDS.get(name, "page")
    rects = {r["box"]: r for r in design_rects(frame)}
    children, btn_texts, material = [], [], []
    ctl_boxes = [tuple(b) for (_nm, _c, _a, _b, b) in rows]
    code_count = {}

    for n, (nm, cat, act, behav, box) in enumerate(rows, 1):
        io = ov.io_of(name, {"name": nm, "behav": behav, "cat": cat})
        code = pg.IO_CODE[io]
        code_count[code] = code_count.get(code, 0) + 1
        ident = "%s_%s%02d" % (slug, code, code_count[code])
        txt = nm.replace("按钮", "").replace("卡", "").replace(" pill", "")
        if nm == "安防 pill":
            txt = "安防 " + SUBST["›"]
        sty = rects.get(tuple(box), {})
        bg = sty.get("fill", "0x1C2430")
        rx = sty.get("rx", 12)
        kind = widget_kind(nm, cat, box)
        material.append(("container" if compound_kind(cat, box) else kind, box))

        if kind == "button":
            btn = make_button(ident, txt, box, bg, rx)
            lb = btn["children"][0]
            d = lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]
            for t in design_texts(frame):               # 取设计帧里该控件内的文字：文案 + 颜色 + 对齐
                if (box[0] <= t["x"] <= box[0] + box[2] + 40 and
                        box[1] - 6 <= t["y"] <= box[1] + box[3] + 6):
                    lb["text"] = _fix_text(t["text"])   # 按钮显示设计文案（如「详情」），不用控件名
                    d["text_color"] = t["fill"]
                    if t["anchor"] != "middle":         # 行式控件要左对齐，不能居中
                        off = max(0, int(t["x"] - box[0] - 8))
                        lb["left"] = off
                        lb["width"] = max(24, box[2] - off - 12)
                        d["text_align"] = "LEFT"
                        d["align"] = "LEFT_MID"      # 模板自带 CENTER，会覆盖 left/width
                    break
            children.append(btn)
            btn_texts.append(lb["text"])
        elif kind == "switch":
            if compound_kind(cat, box):
                parent = make_container(ident, box, bg, rx)
                parent["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 0
                gb = glyph_box(frame, "switch", box)
                rel = (gb[0] - box[0], gb[1] - box[1], gb[2], gb[3])
                parent["children"] = [make_switch(ident + "_sw", rel,
                                                  _switch_on(frame, gb))]
                material.append(("switch", gb))
                children.append(parent)
            else:
                children.append(make_switch(ident, box, _switch_on(frame, box)))
        elif kind == "slider":
            if compound_kind(cat, box):
                parent = make_container(ident, box, bg, rx)
                parent["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 0
                gb = glyph_box(frame, "slider", box)
                rel = (gb[0] - box[0], gb[1] - box[1], gb[2], gb[3])
                parent["children"] = [make_slider(ident + "_sl", rel,
                                                  _value_ratio(frame, box))]
                material.append(("slider", gb))
                children.append(parent)
            else:
                children.append(make_slider(ident, box, _value_ratio(frame, box)))
        elif kind == "bar":
            node = make_bar(ident, box, _value_ratio(frame, box, 0))
            no_click(node)
            children.append(node)
        elif kind == "chart":
            node = make_chart(ident, box)
            no_click(node)
            children.append(node)
        elif kind == "textarea":
            ts = _texts_in(frame, box)
            shown = _fix_text(ts[0]["text"]) if ts else ""
            node = make_textarea(ident, box, shown if nm == "搜索框" else "设备名称")
            node["passwordMode"] = False
            if nm != "搜索框" and shown:
                node["text"] = shown
            children.append(node)
        elif kind == "label":
            ts = _texts_in(frame, box)
            t = ts[0] if ts else None
            lit = _fix_text(t["text"]) if t else _fix_text(nm)
            node = make_label(ident, lit, box,
                              t["fill"] if t else None,
                              sc.ui_size(lit, t["size"]) if t else None)
            children.append(node)
        else:
            node = make_container(ident, box, bg, rx)
            if tuple(box) in rects:
                # 底板由设计帧的同位矩形当装饰层画；容器透明，别盖住滑条/图表等内部细件
                node["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 0
            if cat == "read":
                no_click(node)      # 只读卡是静态展示；动作类控件要能收点击（⑦ 接 native）
            children.append(node)

    # 按钮只跳过已作为按钮文案的那一条；按钮内其它文字（角标、副标题）仍要保留。
    # 输入框内的设计文字改由控件自身承载，跳过以免叠字。
    skip_boxes = [b for k, b in material if k in ("textarea", "label")]
    for i, t in enumerate(design_texts(frame)):
        lit = _fix_text(t["text"])
        if any(b[0] <= t["x"] <= b[0] + b[2] and b[1] <= t["y"] <= b[1] + b[3]
               for b in skip_boxes):
            continue
        if any(lit == b or lit.startswith(b + " ") for b in btn_texts):
            continue
        size = sc.ui_size(lit, t["size"])
        est_w = int(sum(size if ord(c) > 127 else size * 0.56 for c in lit)) + 4
        left = t["x"]
        if t["anchor"] == "middle":
            left = t["x"] - est_w / 2.0
        elif t["anchor"] == "end":
            left = t["x"] - est_w
        lid = "%s_%s%02d" % (slug, pg.STATIC_CODE, i)
        node = make_label(lid, lit,
                          (int(left), int(t["y"] - size * 0.92), est_w, int(size * 1.5)),
                          t["fill"], size)
        # 运行时字库：Wi-Fi 行/状态文案要显示任意中文 SSID，必须挂 GB2312 档，
        # 12/18 号本身已挂运行时字符集（同字号共用一条目）
        rt12 = {"wifi_st06", "wifi_st07", "wifi_st08", "wifi_st09", "wifi_st10", "wifi_st11",
                "wifi_st12", "wifi_st13", "wifi_st15", "wifi_st16", "wifi_st17", "wifi_st19",
                "wifi_st20", "wifi_st21", "wifi_st23", "wifi_st24", "wifi_st25", "wifi_st02",
                "wifi_connecting_st03"}
        rt24 = {"wifi_pwd_st01", "wifi_connecting_st01"}
        if lid in rt12 or lid in rt24:
            node["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_font"] = "cn12"
        children.append(node)

    allr = design_rects(frame)

    def overlap(r):
        x, y, w, h = r["box"]
        return any(not (x + w <= cx or cx + cw <= x or y + h <= cy or cy + ch <= y)
                   for cx, cy, cw, ch in ctl_boxes)

    under, over = [], []
    # 已物化为真实控件的框：其内部的设计图形（按钮底、开关轨道、滑条轨道、进度条）
    # 不再重复画装饰层，否则会盖住真控件。
    deco_exclude = [tuple(b) for k, b in material
                    if k in ("button", "switch", "slider", "textarea", "bar")]
    deco = [r for r in allr
            if not any(_inside(r["box"], eb) for eb in deco_exclude)]
    for idx, r in enumerate(deco):
        node = make_container("%s_deco%02d" % (slug, idx), r["box"], r["fill"], r["rx"])
        no_click(node)
        if overlap(r) and (r["box"][2] * r["box"][3] < 400
                           or min(r["box"][2], r["box"][3]) <= 10):
            over.append(node)
        else:
            under.append(node)

    root = make_screen()
    root["children"] = under + children + over
    page["components"].append(root)
    return page


def all_pages():
    out = []
    for k, (name, frame, _entry, _exit, rows) in enumerate(pg.PAGES):
        if name == "Wi-Fi 设置":
            out.append(build_wifi_page(name, frame, first=(k == 0)))
        else:
            out.append(build_page(name, frame, rows or [], first=(k == 0)))
    return out


def settings():
    """settings 整体克隆自可正常构建的工程（**files 12 条模板不能少**：
    缺了 EEZ 会报"构建成功"却零产出），只覆盖分辨率 / flow / 输出目录。"""
    src = json.load(io.open(SETTINGS_SRC, encoding="utf-8"))["settings"]
    st = fresh(src)
    g = st["general"]
    g.update({"displayWidth": W, "displayHeight": H, "flowSupport": False,
              "projectVersion": "v3", "projectType": "lvgl", "lvglVersion": "9.4.0",
              "colorBpp": "16", "bitmapColorFormat": "BGR", "darkTheme": True})
    bd = st["build"]
    bd.update({"destinationFolder": os.path.join("src", "ui"), "lvglInclude": "lvgl.h",
               "fontExportMode": "source", "imageExportMode": "source"})
    if "generateSourceCodeForEezFramework" in bd:
        bd["generateSourceCodeForEezFramework"] = False
    return st


def build(chars, rt_chars):
    chars_runs = _runs([ord(c) for c in chars])
    # 12px 是唯一带汉字的档：设计用字也并进来（— 铛 ▼ 这类不在 GB2312 一级区）
    rt_all = set(rt_chars) | set(chars)
    rt_runs = _runs([ord(c) for c in rt_all])
    ascii_chars = {c for c in chars if ord(c) < 128} | {"·", "×", "°"}
    ascii_runs = _runs([ord(c) for c in ascii_chars])
    proj = {
        "themesVersion": 1,
        "objID": oid(),
        "settings": settings(),
        "variables": {"objID": oid(), "globalVariables": [], "structures": [], "enums": []},
        "actions": [],
        "userPages": all_pages(),
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": []},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [{
            "objID": oid(), "name": font_name(sz),
            "description": "Haven Home 子集 %d 字形 %dpx（按设计源全量文本裁）" % (len(chars), sz),
            "renderingEngine": "LVGL",
            "source": {"objID": oid(), "filePath": FONT_FILE, "size": sz},
            # 大字（≥30）用 2bpp：4 级灰度足够，C 数组直接省一半
            "bpp": 2 if (sz >= 30 or sz in RT_SIZES) else 4, "threshold": 128, "glyphs": [], "screenOrientation": "all",
            "alwaysBuild": False,
            "lvglRanges": _range_str(rt_runs if sz in RT_SIZES else ascii_runs),
            "lvglSymbols": "",
            "lvglGlyphs": {"objID": oid(), "encodings": rt_runs if sz in RT_SIZES else ascii_runs},
            "lvglAdditionalSources": [],
        } for sz in font_sizes()],
        "bitmaps": [],
        "colors": [],
        "themes": [{"objID": oid(), "name": "Default", "colors": []}],
    }
    # 门禁：objID 唯一 + 控件树完整
    ids = []

    def walk(n):
        ids.append(n["objID"])
        if "style" in n:
            ids.append(n["style"]["objID"])
        if "localStyles" in n:
            ids.append(n["localStyles"]["objID"])
        for c in n.get("children", []):
            walk(c)

    for p in proj["userPages"]:
        for c in p["components"]:
            walk(c)
        for k in p:
            if k.endswith("objID") or k == "objID":
                pass
        ids.append(p["objID"])
    assert len(ids) == len(set(ids)), "objID 有重复"
    page = proj["userPages"][0]
    n_btn = n_lbl = 0

    def count(n):
        nonlocal n_btn, n_lbl
        if n["type"] == "LVGLButtonWidget":
            n_btn += 1
            kids = n.get("children") or []
            assert len(kids) == 1 and kids[0]["type"] == "LVGLLabelWidget",                 "按钮 %s 必须恰好一个子标签" % n.get("identifier")
            assert (kids[0].get("text") or "").strip(),                 "按钮 %s 的子标签文本为空" % n.get("identifier")
            assert "text" not in n, "按钮 %s 不该有 text（文字在子标签里）" % n.get("identifier")
        elif n["type"] == "LVGLLabelWidget":
            n_lbl += 1
        for c in n.get("children", []):
            count(c)
    for c in page["components"]:
        count(c)
    assert page["width"] == W and page["height"] == H, "页面尺寸不对"
    print("[GATE] 页 %d ｜ 控件 %d（按钮 %d / 标签 %d）｜ objID %d 个唯一"
          % (len(proj["userPages"]), n_btn + n_lbl, n_btn, n_lbl, len(ids)))
    return proj


def main():
    cmap = _src_cmap()
    chars = {c for c in charset() if ord(c) in cmap}   # 源字库没有的已在文本侧替换
    rt = {c for c in runtime_chars() if ord(c) in cmap}
    ttf, n = subset_font(chars | rt)
    print("[FONT] %s ｜ %d 字形（设计 %d + 运行时 %d） ｜ %.0f KB"
          % (FONT_FILE, n, len(chars), len(rt & (chars | rt)), os.path.getsize(ttf) / 1024.0))
    proj = build(chars, rt)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(proj, ensure_ascii=False, indent=2) + "\n")
    print("written", OUT, "%.1f KB" % (os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
