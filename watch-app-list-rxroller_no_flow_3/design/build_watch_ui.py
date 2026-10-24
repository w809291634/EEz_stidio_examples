# -*- coding: utf-8 -*-
"""唯一设计源 → EEZ 工程直出（NO_FLOW 第④步预生成）。

读 design_source.py（页面/控件/字体需求）+ design_view.py 的 GLYPHS 矢量图标，
产出 watch.eez-project：
  · 壳（settings/themes/build 等）复制自样板 watch-app-list-no-flow（no flow 已验证），
    仅改 display 466x466 circular；
  · 表盘+applist 合并为 tab_main（LVGLTabviewWidget，tabviewSize=0 隐藏标签条）；
  · 其余 21 页各自一屏；控件 identifier=<page>_<id> 全局唯一（native 挂钩用，显式 id 纪律）；
  · 字体条目按 P-0125 原生形态：renderingEngine LVGL + lvglRanges 数字表 +
    lvglGlyphs.encodings + glyphs:[]，源 fonts/simhei.ttf；
  · 14 个图标 PNG（90px 圆角彩底+白色矢量）入 bitmaps（bpp32 data URI）。

装饰件口径（⑤双核对时豁免）：时刻刻度 ticks、表盘外环 arc 不生成（EEZ 无逐条线原语，
纯装饰）；其余控件与清单表一一对应。

★ EEZ 编辑器校验实测口径（GUI "Pages/…/Arc invalid color / Range min must be an integer" 翻案后定）：
  · arc 的量程字段是 rangeMin/rangeMax（bar/slider 才是 min/max），缺了 GUI 报
    "Range min must be an integer"；
  · 颜色一律 0xRRGGBB（"#00000000" 报 invalid color）；环宽/圆头用 arc_width/arc_rounded，
    轨道色=MAIN bg_color、进度色=INDICATOR bg_color（不用 line_color/KERNEL）。

跑法：python design/build_watch_ui.py    产物：watch.eez-project + design/assets/icons/*.png
"""
import base64
import hashlib
import io
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_source as ds
import design_view as dv

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
TEMPLATE = r"C:\Users\yjt54\Desktop\EEz_stidio_examples\watch-app-list-no-flow\watch-app-list-no-flow.eez-project"
OUT = os.path.join(ROOT, "watch.eez-project")
ICON_DIR = os.path.join(HERE, "assets", "icons")
FONT_FILE = os.path.join(ROOT, "fonts", "simhei.ttf")

W, H = ds.SCREEN["w"], ds.SCREEN["h"]
BG = ds.STYLE["bg"]
MANIFEST = []   # 声明清单（④-A 对账用）：生成器认为写入了什么，audit_declared.py 拿它与工程 JSON 逐项比
_ENT = {}       # id(widget dict) → manifest 条目（set_ident 同步用）


def oid(key):
    return str(uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


def hexcol(c):
    return "0x" + c.lstrip("#").upper()


_fnt = {}


def ttf(px):
    if px not in _fnt:
        _fnt[px] = ImageFont.truetype(FONT_FILE, int(px))
    return _fnt[px]


def measure(text, px):
    f = ttf(px)
    wpx = int(max(f.getlength(t) for t in (text.split("\n") or [""])))
    return max(wpx, 8), int(px * 1.4)


SIZES = (14, 16, 18, 20, 22, 26, 30, 44, 52, 64, 76)


def bucket(px):
    return min(SIZES, key=lambda s: (abs(s - px), s))


def font_name(px):
    return "cn%d" % bucket(px)


def collect_texts():
    texts = []
    for page in ds.PAGES:
        for w in page["widgets"]:
            t = w["type"]
            if t == "label":
                texts.append((w["text"], w["size"]))
            elif t == "pill":
                texts.append((w["text"], max(int(w["h"] * 0.42), 12)))
            elif t == "statrow":
                for v, lab, _c in w["items"]:
                    texts.append((v, 30)); texts.append((lab, 18))
            elif t == "rowlist":
                for row in w["rows"]:
                    for cell in row:
                        texts.append((cell, w["size"]))
            elif t == "legend":
                for txt, _c in w["items"]:
                    texts.append((txt, 15))
            elif t == "chips":
                for c in w["cells"]:
                    texts.append((c, 18))
            elif t == "grid":
                for c in w["cells"]:
                    texts.append((c, w["size"]))
            elif t == "controls":
                texts.append(("<", w["size"]))
            elif t == "bars":
                for lab in w.get("labels", []):
                    texts.append((lab, 14))
            elif t == "progress":
                if w.get("label"):
                    texts.append((w["label"], 16))
                if w.get("value"):
                    texts.append((w["value"], w.get("value_size", 16)))
            elif t == "switch":
                texts.append((w["text"], 20))
            elif t == "facepick":
                for nm in w["names"]:
                    texts.append((nm, 16))
    texts.append(("<", 30)); texts.append((">", 30)); texts.append((">>", 30))
    texts.append(("▲", 22)); texts.append(("▼", 22))
    texts.append(("应用列表", 26)); texts.append(("运动", 26))
    return texts


BASE_FLAGS = "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE"
LBL_FLAGS = "GESTURE_BUBBLE"
CONT_FLAGS = "GESTURE_BUBBLE"


def styles(part_default, parts=None):
    """parts=真部件(INDICATOR/KNOB…)；状态覆盖(PRESSED 等)必须放 MAIN 之下
    （B1 画布翻案：写成 definition.PRESSED.DEFAULT 会被 codegen 发成 LV_PART_PRESSED，
    画布把 PRESSED 色当默认态渲染——reference/07 §3 口径=MAIN.PRESSED）。"""
    d = {"MAIN": {"DEFAULT": {"pad_top": 0, "pad_bottom": 0, "pad_left": 0,
                              "pad_right": 0, "pad_row": 0, "pad_column": 0,
                              "border_width": 0, "outline_width": 0}}}
    d["MAIN"]["DEFAULT"].update(part_default)
    for pname, pval in (parts or {}).items():
        if pname in ("PRESSED", "CHECKED", "FOCUSED", "DISABLED", "SELECTED"):
            d["MAIN"].setdefault(pname, {}).update(pval)
        else:
            d.setdefault(pname, {"DEFAULT": {}})
            d[pname]["DEFAULT"].update(pval)
    return {"objID": oid("st" + json.dumps(d, sort_keys=True, default=str)),
            "definition": d}


def widget(key, wtype, x, y, w_, h_, flags, local, children=None, extra=None):
    o = {"objID": oid(key), "type": wtype,
         "left": int(round(x)), "top": int(round(y)),
         "width": int(round(w_)), "height": int(round(h_)),
         "customInputs": [], "customOutputs": [],
         "style": {"objID": oid("ref" + key), "useStyle": "default",
                   "conditionalStyles": [], "childStyles": []},
         "timeline": [], "eventHandlers": [],
         "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
         "widgetFlags": flags, "hiddenFlagType": "literal",
         "clickableFlagType": "literal", "flagScrollbarMode": "OFF",
         "checkedStateType": "literal", "disabledStateType": "literal",
         "states": "", "groupIndex": 0, "localStyles": local,
         "identifier": key.replace(".", "_").replace("-", "_")}
    if extra:
        o.update(extra)
    o["children"] = children or []
    md = local["definition"]["MAIN"]["DEFAULT"]
    entry = {"identifier": o["identifier"], "type": wtype,
             "left": o["left"], "top": o["top"],
             "width": o["width"], "height": o["height"],
             "text": (extra or {}).get("text"),
             "font": md.get("text_font"),
             "text_color": md.get("text_color"),
             "bg_color": md.get("bg_color")}
    MANIFEST.append(entry)
    _ENT[id(o)] = entry
    return o


def set_ident(o, ident):
    """改 identifier 的唯一入口：同步工程对象与声明清单（④-A 对账翻案：
    直接赋值 o["identifier"] 会让 manifest 与工程脱钩）。"""
    o["identifier"] = ident
    _ENT[id(o)]["identifier"] = ident


def label(key, page, text, px, color, x=None, y=None, cx=None, cy=None,
          anchor="mm", w_=None, h_=None, align=None):
    tw, th = measure(text, bucket(px))
    if x is None:
        x = cx - tw / 2.0
    if y is None:
        y = cy - th / 2.0
    la = {"text_color": hexcol(color), "text_font": font_name(px)}
    if align:
        la["align"] = align
    return widget("%s.%s.l" % (page, key), "LVGLLabelWidget", x, y,
                  w_ or tw + 4, h_ or th, LBL_FLAGS,
                  styles(la),
                  extra={"text": text, "textType": "literal", "longMode": "WRAP",
                         "recolor": False, "useStaticText": True})


def button(key, page, x, y, w_, h_, text, px, bg, fg="#0A0A0F", radius=None,
           flags=BASE_FLAGS):
    r = radius if radius is not None else h_ / 2.0
    # bg_opa:255 必写——缺省时 EEZ 主题灰盖过自定义 bg_color（B1 画布实测翻案）
    btn = widget("%s.%s.b" % (page, key), "LVGLButtonWidget", x, y, w_, h_,
                 flags, styles({"bg_color": hexcol(bg), "bg_opa": 255,
                                "radius": int(r)},
                               parts={"PRESSED": {"bg_color": "0x3A3A48"}}))
    if text:
        btn["children"].append(label(key + ".t", page + ".b", text, px, fg,
                                     cx=w_ / 2.0, cy=h_ / 2.0))
    return btn


def container(key, page, x, y, w_, h_, bg=None, radius=0, border=None,
              flags=CONT_FLAGS):
    la = {"bg_opa": 0}
    if bg:
        la["bg_color"] = hexcol(bg)
        la["bg_opa"] = 255
    if radius:
        la["radius"] = int(radius)
    if border:
        la["border_width"] = border[0]
        la["border_color"] = hexcol(border[1])
    return widget("%s.%s.c" % (page, key), "LVGLContainerWidget", x, y, w_, h_,
                  flags, styles(la))


def convert(page, w, out):
    t = w["type"]
    pid = "%s.%s" % (page, w.get("id", t))
    if t == "label":
        tw, th = measure(w["text"], bucket(w["size"]))
        x, y = w["x"], w["y"]
        a = w.get("anchor", "la")
        lx = x - tw / 2.0 if "m" in a[1] else (x - tw if a[1] == "r" else x)
        ly = y - th / 2.0 if "m" in a[0] else (y - th if a[0] == "s" else y)
        out.append(label(pid, page, w["text"], w["size"], w["color"], x=lx, y=ly))
    elif t == "pill":
        out.append(button(pid, page, w["x"] - w["w"] / 2.0, w["y"] - w["h"] / 2.0,
                          w["w"], w["h"], w["text"], max(int(w["h"] * 0.42), 12),
                          w["color"]))
    elif t == "back":
        b = button(pid, page, w["x"] - 20, w["y"] - 22, 40, 44, "<", 22,
                   BG, fg=ds.STYLE["text"])
        b["localStyles"]["definition"]["MAIN"]["DEFAULT"]["bg_opa"] = 0
        out.append(b)
    elif t == "statrow":
        for i, (val, lab, col) in enumerate(w["items"]):
            cx = w["cx"] + (i - (len(w["items"]) - 1) / 2.0) * w["gap"]
            out.append(label("%s.v%d" % (pid, i), page, val, 30, col, cx=cx,
                             cy=w["y"] - 8 + 10))
            out.append(label("%s.l%d" % (pid, i), page, lab, 18, ds.STYLE["sub"],
                             cx=cx, cy=w["y"] + 22 + 6))
    elif t == "pager_dots":
        for i in range(w["count"]):
            x = w["cx"] + (i - (w["count"] - 1) / 2.0) * w["gap"]
            col = ds.STYLE["text"] if i == w["active"] else ds.STYLE["ring"]
            out.append(container("%s.d%d" % (pid, i), page, x - w["r"],
                                 w["y"] - w["r"], 2 * w["r"], 2 * w["r"],
                                 bg=col, radius=w["r"]))
    elif t == "progress":
        x0 = w.get("cx", ds.SCREEN["cx"]) - w["w"] / 2.0
        if w.get("label"):
            out.append(label(pid + ".lb", page, w["label"], 16, ds.STYLE["sub"],
                             x=x0, y=w["y"] - 26))
        if w.get("value"):
            tw, _ = measure(w["value"], bucket(w.get("value_size", 16)))
            out.append(label(pid + ".vl", page, w["value"], w.get("value_size", 16),
                             ds.STYLE["sub"], x=x0 + w["w"] - tw, y=w["y"] - 26))
        pv = int(w["pct"] * 100)
        out.append(widget(pid + ".bar", "LVGLBarWidget", x0, w["y"], w["w"], 8,
                          "GESTURE_BUBBLE",
                          styles({"bg_color": hexcol(ds.STYLE["ring"]),
                                  "radius": 4},
                                 parts={"INDICATOR": {"bg_color": hexcol(w["color"]),
                                                      "radius": 4}}),
                          extra={"min": 0, "minType": "literal", "max": 100,
                                 "maxType": "literal", "mode": "NORMAL",
                                 "value": str(pv), "valueType": "literal",
                                 "previewValue": str(pv),
                                 "previewValueStart": "0",
                                 "enableAnimation": False}))
    elif t == "ring":
        pv = int(w["pct"] * 100)
        out.append(widget(pid, "LVGLArcWidget", w["cx"] - w["r"], w["cy"] - w["r"],
                          2 * w["r"], 2 * w["r"], "GESTURE_BUBBLE",
                          styles({"bg_color": hexcol(w["bg"]),
                                  "arc_width": w["width"], "arc_rounded": True},
                                 parts={"INDICATOR": {"bg_color": hexcol(w["color"]),
                                                      "arc_width": w["width"],
                                                      "arc_rounded": True}}),
                          extra={"useAngle": False, "mode": "NORMAL",
                                 "startAngle": 0, "startAngleType": "literal",
                                 "endAngle": 360, "endAngleType": "literal",
                                 "bgStartAngle": 0, "bgStartAngleType": "literal",
                                 "bgEndAngle": 360, "bgEndAngleType": "literal",
                                 "rotation": 270, "rotationType": "literal",
                                 "rangeMin": 0, "rangeMinType": "literal",
                                 "rangeMax": 100, "rangeMaxType": "literal",
                                 "value": str(pv), "valueType": "literal",
                                 "previewValue": str(pv),
                                 "previewStartAngle": "0", "previewEndAngle": "360",
                                 "previewBgStartAngle": "0", "previewBgEndAngle": "360",
                                 "previewRotation": "270"}))
    elif t == "switch":
        out.append(label(pid + ".t", page, w["text"], 20, ds.STYLE["text"],
                         cx=w["cx"], cy=w["y"] - 34))
        out.append(widget(pid, "LVGLSwitchWidget", w["cx"] - 30, w["y"] - 16,
                          60, 32, BASE_FLAGS, styles({})))
    elif t == "slider":
        x0 = w.get("cx", ds.SCREEN["cx"]) - w["w"] / 2.0
        pv = int(w["pct"] * 100)
        out.append(widget(pid, "LVGLSliderWidget", x0, w["y"] - 12, w["w"], 24,
                          BASE_FLAGS,
                          styles({"bg_color": hexcol(ds.STYLE["ring"]),
                                  "radius": 6},
                                 parts={"INDICATOR": {"bg_color": hexcol(w["color"]),
                                                      "radius": 6},
                                        "KNOB": {"bg_color": "0xFFFFFF",
                                                 "radius": 60}}),
                          extra={"min": 0, "minType": "literal", "max": 100,
                                 "maxType": "literal", "mode": "NORMAL",
                                 "value": str(pv), "valueType": "literal",
                                 "previewValue": pv, "enableAnimation": False}))
    elif t == "rowlist":
        cx = ds.SCREEN["cx"]
        for i, row in enumerate(w["rows"]):
            cy = w["y0"] + i * w["row_h"] + w["row_h"] // 2
            out.append(label("%s.r%dL" % (pid, i), page, row[0], w["size"],
                             ds.STYLE["text"], x=cx - w["w"] / 2, y=cy - 14))
            if len(row) > 1:
                tw, _ = measure(row[1], bucket(w["size"]))
                out.append(label("%s.r%dR" % (pid, i), page, row[1], w["size"],
                                 ds.STYLE["sub"], x=cx + w["w"] / 2 - tw,
                                 y=cy - 14))
    elif t == "grid":
        for k, cell in enumerate(w["cells"]):
            r, c = divmod(k, w["cols"])
            x0 = w["x0"] + c * (w["cw"] + w["gap"])
            y0 = w["y0"] + r * (w["ch"] + w["gap"])
            bgc = w["accent_color"] if cell in w.get("accent_cells", []) else w["bg"]
            out.append(button("%s.k%d" % (pid, k), page, x0, y0, w["cw"], w["ch"],
                              cell, w["size"], bgc, fg=w["fg"], radius=8))
    elif t == "chips":
        n = len(w["cells"])
        total = n * w["cw"] + (n - 1) * w["gap"]
        x = w["cx"] - total / 2.0
        for i, cell in enumerate(w["cells"]):
            on = i in w["on"]
            out.append(button("%s.c%d" % (pid, i), page, x, w["y"] - w["ch"] / 2,
                              w["cw"], w["ch"], cell, 18,
                              ds.STYLE["accent"] if on else "#1E1E28",
                              fg=ds.STYLE["text"]))
            x += w["cw"] + w["gap"]
    elif t == "controls":
        glyphs = {"prev": "<", "play": ">", "next": ">>"}   # simhei 无 U+25C0/25B6（引擎实测）
        for i, shp in enumerate(w["shapes"]):
            x = w["cx"] + (i - (len(w["shapes"]) - 1) / 2.0) * w["gap"]
            out.append(button("%s.g%d" % (pid, i), page, x - 30, w["y"] - 24,
                              60, 48, glyphs[shp], 22, BG, fg=w["color"],
                              radius=12))
    elif t == "bars":
        n = len(w["values"])
        total = n * w["bw"] + (n - 1) * w["gap"]
        x = w["cx"] - total / 2.0
        vmax = max(w["values"])
        for i, v in enumerate(w["values"]):
            hgt = max(w["h"] * v / vmax, 4)
            out.append(container("%s.b%d" % (pid, i), page, x, w["y"] - hgt,
                                 w["bw"], hgt, bg=w["color"], radius=4))
            x += w["bw"] + w["gap"]
        for i, lab in enumerate(w.get("labels", [])):
            lx = w["cx"] - total / 2.0 + i * (w["bw"] + w["gap"])
            out.append(label("%s.lb%d" % (pid, i), page, lab, 14, ds.STYLE["sub"],
                             cx=lx + w["bw"] / 2, cy=w["y"] + 16))
    elif t == "segbar":
        x = w.get("cx", ds.SCREEN["cx"]) - w["w"] / 2.0
        for i, (nm, frac, col) in enumerate(w["segs"]):
            ww = w["w"] * frac
            out.append(container("%s.s%d" % (pid, i), page, x, w["y"], ww,
                                 w["h"], bg=col))
            x += ww
    elif t == "legend":
        n = len(w["items"])
        total = (n - 1) * w["gap"] + sum(14 + measure(t, bucket(15))[0]
                                         for t, _ in w["items"])
        x = ds.SCREEN["cx"] - total / 2.0
        for i, (txt, col) in enumerate(w["items"]):
            out.append(container("%s.p%d" % (pid, i), page, x, w["y"] - 5, 10, 10,
                                 bg=col, radius=5))
            out.append(label("%s.t%d" % (pid, i), page, txt, 15, ds.STYLE["sub"],
                             x=x + 14, y=w["y"] - 10))
            x += 14 + measure(txt, bucket(15))[0] + w["gap"]
    elif t == "disc":
        out.append(container(pid, page, w["cx"] - w["r"], w["cy"] - w["r"],
                             2 * w["r"], 2 * w["r"], bg=w["color"], radius=w["r"]))
        out.append(container(pid + ".hole", page, w["cx"] - 10, w["cy"] - 10,
                             20, 20, bg="#101018", radius=10))
    elif t == "frame":
        out.append(container(pid, page, w["x"], w["y"], w["w"], w["h"],
                             border=(2, w["color"])))
    elif t == "shutter":
        out.append(container(pid, page, w["cx"] - w["r"], w["cy"] - w["r"],
                             2 * w["r"], 2 * w["r"], border=(4, w["color"]),
                             radius=w["r"]))
        out.append(container(pid + ".in", page, w["cx"] - w["r"] + 9,
                             w["cy"] - w["r"] + 9, 2 * w["r"] - 18,
                             2 * w["r"] - 18, bg=w["color"], radius=w["r"]))
    elif t == "roundrect":
        out.append(container(pid, page, w["cx"] - w["w"] / 2, w["cy"] - w["h"] / 2,
                             w["w"], w["h"], border=(3, w["color"]),
                             radius=w["radius"]))
    elif t == "stepper":
        for dy, g, sfx in ((-64, "▲", "up"), (40, "▼", "dn")):
            out.append(button("%s.%s" % (pid, sfx), page, w["x"] - 32, w["y"] + dy,
                              64, 26, g, 16, BG, fg=ds.STYLE["sub"], radius=6))
    elif t == "facepick":
        for i, nm in enumerate(w["names"]):
            x = w["cx"] + (i - (len(w["names"]) - 1) / 2.0) * w["gap"]
            r = w["r"]
            col = ds.STYLE["accent"] if i == w["active"] else ds.STYLE["ring"]
            out.append(container("%s.f%d" % (pid, i), page, x - r, w["y"] - r,
                                 2 * r, 2 * r, bg="#12121A", radius=r,
                                 border=(3 if i == w["active"] else 2, col)))
            out.append(label("%s.v%d" % (pid, i), page, "10:09", 18,
                             ds.STYLE["text"], cx=x, cy=w["y"] - 6))
            out.append(label("%s.n%d" % (pid, i), page, nm, 16, ds.STYLE["sub"],
                             cx=x, cy=w["y"] + r + 20))
    elif t == "roller":
        # 只出全屏宿主：行全部由 native（Rxroller 移植件）作为子对象创建。
        # ★ 宿主必须铺满整屏——LVGL 9 把子对象裁到父边界，小窗会切掉弧形上下行（FX-004）。
        host = container(pid, page, 0, 0, ds.SCREEN["w"], ds.SCREEN["h"],
                         # 纵向手势留给 native 滚轮；横向沿祖先链交回 tabview，
                         # 让 AppList 右滑跟手而非松手后才切页。
                         flags="GESTURE_BUBBLE|SCROLL_CHAIN_HOR")
        set_ident(host, "al_roller_host")
        out.append(host)
    elif t in ("ticks", "arc"):
        print("豁免装饰件：%s.%s（⑤双核对时注明）" % (page, w.get("id")))
    else:
        raise ValueError("生成器不支持的设计控件类型：%s" % t)


def tab_widget(key, name, children, tabname):
    o = widget(key, "LVGLTabWidget", 0, 0, W, H,
               "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
               styles({}))
    set_ident(o, name)
    o["tabName"] = tabname
    o["tabNameType"] = "literal"
    o["children"] = children
    return o


def screen(key, children):
    scr = widget(key, "LVGLScreenWidget", 0, 0, W, H,
                 "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
                 # circularDisplay 仅影响 EEZ 预览；真机/PC_SIM 要由 LVGL 根对象实际裁圆。
                 styles({"bg_color": hexcol(BG), "radius": 32767, "clip_corner": True}))
    scr["children"] = children
    set_ident(scr, "scr_" + key.split(".")[-1])
    return scr


def page_obj(name, scr, first):
    return {"objID": oid("page." + name), "components": [scr],
            "connectionLines": [], "localVariables": [],
            "componentGroups": [], "userProperties": [],
            "name": name, "left": 0, "top": 0, "width": W, "height": H,
            "isUsedAsUserWidget": False, "createAtStart": first,
            "deleteOnScreenUnload": False}


def build():
    texts = collect_texts()
    sizes = sorted({bucket(px) for _t, px in texts})
    codes = set(range(32, 127))
    for t, _px in texts:
        codes.update(ord(c) for c in t)
    ranges = ["32-126"] + [str(c) for c in sorted(codes) if c > 126]
    encodings = [{"from": 32, "to": 126}] + \
        [{"from": c, "to": c} for c in sorted(codes) if c > 126]

    fonts = []
    for px in sizes:
        fonts.append({"objID": oid("font.cn%d" % px), "name": "cn%d" % px,
                      "description": "设计源 %d px 档（同源生成，勿手改）" % px,
                      "renderingEngine": "LVGL",
                      "source": {"objID": oid("fontsrc.cn%d" % px),
                                 "filePath": "fonts/simhei.ttf", "size": px},
                      "bpp": 4, "threshold": 128, "glyphs": [],
                      "screenOrientation": "all", "alwaysBuild": False,
                      "lvglRanges": ",".join(ranges), "lvglSymbols": "",
                      "lvglAdditionalSources": [],
                      "lvglGlyphs": {"objID": oid("glyphs.cn%d" % px),
                                     "encodings": encodings}})

    os.makedirs(ICON_DIR, exist_ok=True)
    bitmaps = []
    for i, (nm, col, abbr) in enumerate(ds.APPS):
        img = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, 89, 89], radius=25, fill=dv.C(col))
        if abbr in dv.GLYPHS:
            dv.GLYPHS[abbr](d, 45, 45, 32, dv.C("#FFFFFF"), (0, 0, 0, 0))
        else:
            d.text((45, 45), abbr, font=dv.font(38), fill=dv.C("#FFFFFF"),
                   anchor="mm")
        png = os.path.join(ICON_DIR, "ic_%d.png" % i)
        img.save(png)
        bitmaps.append({"objID": oid("bmp.ic_%d" % i), "name": "ic_%d" % i,
                        "description": "applist 图标·%s" % nm,
                        "image": "data:image/png;base64," +
                        base64.b64encode(open(png, "rb").read()).decode(),
                        "bpp": 32, "alwaysBuild": True})

    proj = json.load(io.open(TEMPLATE, encoding="utf-8"))
    g = proj["settings"]["general"]
    g["displayWidth"], g["displayHeight"] = W, H
    g["circularDisplay"] = True
    g["displayBorderRadius"] = 233
    g["flowSupport"] = False
    proj["settings"]["general"] = g
    proj["fonts"] = fonts
    proj["bitmaps"] = bitmaps
    proj["variables"] = {"objID": oid("vars"), "globalVariables": []}
    proj["actions"] = []

    pages = []
    tab_children = {}
    for page in ds.PAGES:
        ch = []
        for w in page["widgets"]:
            convert(page["name"], w, ch)
        if page["name"] in ("watchface", "applist"):
            tab_children[page["name"]] = ch
        else:
            pages.append(page_obj(page["name"], screen("scr." + page["name"], ch),
                                  False))

    tv = widget("tabmain.tv", "LVGLTabviewWidget", 0, 0, W, H,
                "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
                styles({"bg_opa": 0}))
    set_ident(tv, "tv_main")
    tv["tabviewPosition"] = "TOP"
    tv["tabviewSize"] = 0
    tv["selectedTab"] = 0
    tv["selectedTabType"] = "literal"
    tv["children"] = [
        tab_widget("tabmain.t0", "tab_watchface", tab_children["watchface"], "表盘"),
        tab_widget("tabmain.t1", "tab_applist", tab_children["applist"], "应用"),
    ]
    pages.insert(0, page_obj("tab_main", screen("scr.tab_main", [tv]), True))

    proj["userPages"] = pages
    # 工程文件也是人工核对源：保持 UTF-8 与 2 空格缩进，避免单行 JSON 难以审阅/合并。
    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(proj, ensure_ascii=False, indent=2) + "\n")
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    io.open(os.path.join(ROOT, "build", "declared_manifest.json"), "w",
            encoding="utf-8").write(json.dumps(MANIFEST, ensure_ascii=False))
    emit_app_rows()
    print("生成 %s：%d 页 / %d 字体档 / %d 图标 / %d 码位 / %d 声明条目" % (
        OUT, len(pages), len(fonts), len(bitmaps), len(codes), len(MANIFEST)))


def emit_app_rows():
    """app_rows.c = design_source.APPS 的 C 形态（顺序=图标号=app_* 页顺序）。"""
    app_pages = [p["name"] for p in ds.PAGES if p["name"].startswith("app_")]
    if len(app_pages) != len(ds.APPS):
        raise ValueError("APPS %d 项与 app_* 页 %d 个不符" % (len(ds.APPS), len(app_pages)))
    rows = ['    { "%s", "%s", &img_ic_%d, &objects.%s },' % (pid, nm, i, pid)
            for i, ((nm, _c, _g), pid) in enumerate(zip(ds.APPS, app_pages))]
    out = ["/* 生成物，勿手改 —— 出处 design/build_watch_ui.py:emit_app_rows() */",
           '#include "generated/app_rows.h"', '#include "screens.h"', '#include "images.h"', "",
           "const watch_app_row_t WATCH_APP_ROWS[] = {"] + rows + [
           "};", "const int WATCH_APP_ROWS_COUNT = %d;" % len(ds.APPS), ""]
    io.open(os.path.join(ROOT, "src", "native", "generated", "app_rows.c"), "w",
            encoding="utf-8", newline=chr(10)).write(chr(10).join(out))


if __name__ == "__main__":
    build()
