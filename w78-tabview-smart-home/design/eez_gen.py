# -*- coding: utf-8 -*-
"""EEZ 工程生成器（第④步，分阶段）：先跑通「主控」一屏。

真值来源：design/pages.py 的 _main_rows()（控件名/类型/行为/框）+ design/simple_control.py 的几何常量。
本阶段约束（2026-11-04 用户定，先跑通再加码）：
  · 只出 1 屏；无自定义字体（先用默认字体，中文会显示为默认字形，④-2 再烘子集）
  · 无 action：no flow 的跳转/动作由 native 接，工程里只放界面树
  · 每个控件都带 localStyles（内边距/圆角/底色），保证在 EEZ 里不是裸控件

用法：python design/eez_gen.py        # 产物：w78-smart-home.eez-project
"""
import io
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pages as pg                  # noqa: E402
import overview_pro as ov           # noqa: E402  io_of 是六类判定的唯一实现
from texts import TEXTS             # noqa: E402
import re                           # noqa: E402
import simple_control as sc         # noqa: E402

OUT = os.path.join(ROOT, "w78-smart-home.eez-project")
FONT_DIR = os.path.join(ROOT, "fonts")
FONT_FILE = "fonts/cn14.ttf"
FONT_NAME = "cn14"
# EEZ 用页名生成 C 标识符；中文会被消成 "_" 而互相撞车（实测 23 页全变 SCREEN_ID___）
PAGE_IDS = {
    "主控": "main", "客厅": "living", "主卧": "master", "厨房": "kitchen", "浴室": "bath",
    "灯详情": "detail_light", "空调详情": "detail_ac", "窗帘详情": "detail_curtain",
    "传感详情": "detail_sensor", "摄像头详情": "detail_camera", "插座详情": "detail_plug",
    "通知中心": "notify", "能源统计": "energy", "设置": "settings", "全部设备": "devices",
    "安防": "security", "场景详情": "scene_detail", "添加设备·选类型": "add_type",
    "添加设备·配网中": "add_pairing", "添加设备·完成": "add_done", "关于": "about",
    "离线态": "offline", "空房间": "empty_room",
}


def font_sizes():
    """字号集合从设计帧动态收集（写死会漏页）。"""
    return sorted({int(t["size"]) for _n, f, _e, _x, _r in pg.PAGES
                   for t in design_texts(f)})

def font_name(size):
    return "cn%d" % int(size)
FONT_SIZE = 14
SRC_TTF = os.path.join(os.path.dirname(ROOT), "app-wifi-scan-flow-no-flow", "fonts", "simhei.ttf")
SETTINGS_SRC = os.path.join(os.path.dirname(ROOT), "app-wifi-scan-flow-no-flow",
                            "app-wifi-scan-flow-no-flow.eez-project")
# 黑体里没有的装饰字符 → 用等价 ASCII 顶上（否则界面上是豆腐块）
SUBST = {"‹": "<", "›": ">", "−": "-", "▶": ">", "◀": "<", "✓": "√", "✔": "√"}
W, H = 800, 480
DEFAULTS_PATH = os.path.join(HERE, "eez_defaults.json")
DEFAULTS = json.load(io.open(DEFAULTS_PATH, encoding="utf-8"))


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


def fresh(node):
    """深拷贝默认结构，换新 objID，并把"表达式型"属性复位。

    采来的模板会带别的工程的表达式（如 hiddenFlag: "pick_ssid == ''"），
    不清掉会生成 get_var_pick_ssid…() 这种未声明调用 → C 编译报错。
    """
    if isinstance(node, dict):
        out = {k: (oid() if k == "objID" else fresh(v)) for k, v in node.items()}
        if "hiddenFlag" in out:
            out["hiddenFlagType"] = "literal"
            out["hiddenFlag"] = False
        for k in ("checkedState", "disabledState", "clickableFlag"):
            t = k + "Type"
            if t in out:
                out[t] = "literal"
        return out
    if isinstance(node, list):
        return [fresh(x) for x in node]
    return node


def oid():
    return str(uuid.uuid4())


PAD0 = {"pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
        "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0}


def base(kind, ident, left, top, w, h, style_def):
    return {
        "objID": oid(), "type": kind,
        "left": left, "top": top, "width": w, "height": h,
        "customInputs": [], "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [], "eventHandlers": [],
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "widgetFlags": ("CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|"
                        "SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER" if kind == "LVGLButtonWidget"
                        else "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER"),
        "hiddenFlagType": "literal", "hiddenFlag": False,
        "clickableFlagType": "literal", "flagScrollbarMode": "OFF",
        "checkedStateType": "literal", "disabledStateType": "literal",
        "states": "", "groupIndex": 0, "identifier": ident,
        "localStyles": {"objID": oid(), "definition": {"MAIN": {"DEFAULT": style_def}}},
    }


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


def make_label(ident, text, box, color=None, size=None):
    """标签 = 默认 LVGLLabelWidget 克隆，只改几何/文本/字色。"""
    c = fresh(_force_font(DEFAULTS["LVGLLabelWidget"]))
    x, y, w, h = box
    if size:
        c["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_font"] = font_name(size)
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h,
              "text": _fix_text(text), "textType": "literal", "useStaticText": True})
    if color:
        c["localStyles"]["definition"]["MAIN"]["DEFAULT"]["text_color"] = color
    return c


def make_button(ident, text, box, bg=None, radius=None):
    """按钮 = 默认 LVGLButtonWidget 克隆 + 一个默认 LVGLLabelWidget 子节点承载文字。

    EEZ 的按钮没有 text 字段；文字必须放在子标签里（align=CENTER）。
    """
    b = fresh(DEFAULTS["LVGLButtonWidget"])
    x, y, w, h = box
    b.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    main = b["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    if bg:
        main["bg_color"] = bg
    if radius is not None:
        main["radius"] = radius
    lb = fresh(DEFAULTS["LVGLButtonWidget+LVGLLabelWidget"])
    lb.update({"identifier": ident + "_lb",
               "left": 0, "top": 0, "width": w, "height": h,
               "text": _fix_text(text), "textType": "literal", "useStaticText": True})
    b["children"] = [lb]
    return b


def make_screen():
    """根 = 默认 LVGLScreenWidget 克隆。"""
    c = fresh(DEFAULTS["LVGLScreenWidget"])
    c.update({"left": 0, "top": 0, "width": W, "height": H, "children": []})
    d = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    d.update({"bg_color": "0x05080F", "bg_opa": 255})
    return c


def no_click(n):
    """纯展示/装饰容器不该吃点击：去掉 CLICKABLE 等标记，否则会盖住下层按钮。"""
    keep = {"GESTURE_BUBBLE", "SCROLL_CHAIN_HOR", "SCROLL_CHAIN_VER"}
    n["widgetFlags"] = "|".join(x for x in str(n.get("widgetFlags", "")).split("|")
                                if x in keep)
    n["clickableFlagType"] = "literal"
    n["clickableFlag"] = False


def make_container(ident, box, bg=None, radius=None, text="", color=None):
    """卡片 = 默认 LVGLContainerWidget + 居中子标签（容器本身没有 text 字段）。"""
    c = fresh(DEFAULTS["LVGLContainerWidget"])
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    main = c["localStyles"]["definition"]["MAIN"]["DEFAULT"]
    if bg:
        main["bg_color"] = bg
    if radius is not None:
        main["radius"] = radius
    if text:
        lb = fresh(DEFAULTS["LVGLContainerWidget+LVGLLabelWidget"])
        lb.update({"left": 0, "top": 0, "width": w, "height": h,
                   "text": _fix_text(text), "textType": "literal", "useStaticText": True})
        d = lb["localStyles"]["definition"]["MAIN"]["DEFAULT"]
        d["align"] = "CENTER"
        if color:
            d["text_color"] = color
        c["children"] = [lb]
    return c


def make_switch(ident, box):
    c = fresh(DEFAULTS["LVGLSwitchWidget"])
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    return c


def make_slider(ident, box, value=0):
    c = fresh(DEFAULTS["LVGLSliderWidget"])
    x, y, w, h = box
    c.update({"identifier": ident, "left": x, "top": y, "width": w, "height": h})
    if "value" in c:
        c["value"] = value
    return c


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
    children, btn_texts = [], []
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
        wide = box[2] > 200
        # 只有"窄的跳转控件"做真按钮；卡片/开关/滑条/只读格只做底板，
        # 否则按钮自带的居中文字会和设计帧里的名字/数值/详情叠在一起（实测）。
        if cat not in ("nav", "back") or wide:
            node = make_container(ident, box, bg, rx)
            if tuple(box) in rects:
                # 底板由设计帧的同位矩形当装饰层画；容器透明，别盖住滑条/图表等内部细件
                node["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 0
            if cat not in ("nav", "back"):
                no_click(node)          # 开关/滑条/只读卡目前是静态层，别抢按钮的点击
            children.append(node)
        else:
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

    for i, t in enumerate(design_texts(frame)):
        lit = _fix_text(t["text"])
        if any(lit == b or lit.startswith(b + " ") for b in btn_texts):
            continue
        size = t["size"]
        est_w = int(sum(size if ord(c) > 127 else size * 0.56 for c in lit)) + 4
        left = t["x"]
        if t["anchor"] == "middle":
            left = t["x"] - est_w / 2.0
        elif t["anchor"] == "end":
            left = t["x"] - est_w
        children.append(make_label("%s_%s%02d" % (slug, pg.STATIC_CODE, i), lit,
                                   (int(left), int(t["y"] - size * 0.92), est_w, int(size * 1.5)),
                                   t["fill"], size))

    allr = design_rects(frame)

    def overlap(r):
        x, y, w, h = r["box"]
        return any(not (x + w <= cx or cx + cw <= x or y + h <= cy or cy + ch <= y)
                   for cx, cy, cw, ch in ctl_boxes)

    under, over = [], []
    btn_boxes = {tuple(b) for (nm, c, _a, _b, b) in rows
                 if c in ("nav", "back") and b[2] <= 200}
    for idx, r in enumerate([r for r in allr if r["box"] not in btn_boxes]):
        node = make_container("%s_deco%02d" % (slug, idx), r["box"], r["fill"], r["rx"])
        no_click(node)
        if overlap(r) and (r["box"][2] * r["box"][3] < 2000
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


def build(chars):
    chars_runs = _runs([ord(c) for c in chars])
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
            "bpp": 4, "threshold": 128, "glyphs": [], "screenOrientation": "all",
            "alwaysBuild": False,
            "lvglRanges": _range_str(chars_runs),
            "lvglSymbols": "",
            "lvglGlyphs": {"objID": oid(), "encodings": chars_runs},
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
    ttf, n = subset_font(chars)
    print("[FONT] %s ｜ %d 字形 ｜ %.0f KB" % (FONT_FILE, n, os.path.getsize(ttf) / 1024.0))
    proj = build(chars)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(proj, ensure_ascii=False, indent=2) + "\n")
    print("written", OUT, "%.1f KB" % (os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
