# -*- coding: utf-8 -*-
"""EEZ 工程 A 层对账（第④步门禁）：工程 JSON ↔ 设计源逐项对齐。

查九件（任何 FAIL 退出码非 0）：
  A1 页面尺寸与工程设置一致（800×480）
  A2 已生成的页，设计源控件数 == 工程控件数，且每个控件按 identifier 能对上
  A3 每个控件的框（left/top/width/height）与设计源 box 完全一致
  A4 按钮/标签的显示文本非空
  A5 字体条目存在、TTF 文件存在且能打开
  A6 所有控件引用的 text_font 都能解析，且**控件文本里的每个字符都在字体覆盖范围内**
     （这条专治"打开没字"）
  A7 identifier 在页内唯一；objID 全工程唯一
  A8 颜色值只允许 0xRRGGBB（防 invalid color）
  A9 identifier 类别码 == io_of() 的六类，且按类连续编号、无未分类命名

用法：python design/eez_check.py
"""
import glob
import io
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pages as pg                  # noqa: E402
import overview_pro as ov           # noqa: E402
from eez_gen import PAGE_IDS, widget_kind, compound_kind   # noqa: E402

KIND_TYPE = {"button": "LVGLButtonWidget", "switch": "LVGLSwitchWidget",
             "slider": "LVGLSliderWidget", "textarea": "LVGLTextareaWidget",
             "bar": "LVGLBarWidget", "chart": "LVGLChartWidget",
             "label": "LVGLLabelWidget", "container": "LVGLContainerWidget"}

PROJ = os.path.join(ROOT, "w78-smart-home.eez-project")
TPL_DIR = os.path.join(os.path.dirname(ROOT), "eez-widget-templates", "templates")
W, H = 800, 480

# EEZ 样式编辑器里的 LVGL 样式属性（拼错的键 EEZ 不报错、只会静默失效）
STYLE_KEYS = {
    "align", "text_align", "text_color", "text_font",
    "line_width", "line_color", "line_opa",
    "bg_color", "bg_opa", "border_color", "border_width", "outline_width", "radius",
    "pad_top", "pad_bottom", "pad_left", "pad_right", "pad_row", "pad_column",
    "arc_width", "arc_rounded", "width", "height",
}


def templates():
    """标准模板（只读缓存）：控件类型 → 模板节点。"""
    if not hasattr(templates, "_cache"):
        d = {}
        for f in glob.glob(os.path.join(TPL_DIR, "*.json")):
            t = json.load(io.open(f, encoding="utf-8"))
            d[t["type"]] = t
        templates._cache = d
    return templates._cache

# 类别码：长码在前，避免 hw01 被当成 w01
CODE_RE = re.compile(r"_(hw|hr|go|w|r)(\d{2})$")
STATIC_RE = re.compile(r"_st\d{2}$")
DECO_RE = re.compile(r"_deco\d{2}$")
LB_RE = re.compile(r"_(?:hw|hr|go|w|r)\d{2}_lb$")
SW_RE = re.compile(r"_(?:sw|sl)$")


def _font_has_cjk(f):
    txt = str(f.get("lvglRanges") or "")
    for part in txt.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            if int(a) <= 0x9FFF and int(b) >= 0x4E00:
                return True
        else:
            if 0x4E00 <= int(part) <= 0x9FFF:
                return True
    return False


def check_font_policy(fonts, storage):
    """镜像：≤3 档、仅 1 档带汉字且该档是最小字号；SD：不限档位但镜像留 1 档兜底。"""
    errs = []
    sizes = [f["source"]["size"] for f in fonts]
    cjk = [f for f in fonts if _font_has_cjk(f)]
    if storage == "image":
        if len(fonts) > 3:
            errs.append("A11 镜像字库 %d 档 > 3" % len(fonts))
        if len(cjk) != 1:
            errs.append("A11 镜像字库带汉字的档 %d 个（必须恰好 1）" % len(cjk))
        elif cjk[0]["source"]["size"] != min(sizes):
            errs.append("A11 汉字档 %dpx 不是最小字号 %dpx"
                        % (cjk[0]["source"]["size"], min(sizes)))
    elif storage == "sd":
        if not cjk:
            errs.append("A11 SD 模式镜像内也必须有 1 档汉字兜底")
    else:
        errs.append("A11 font_storage 未知：%s" % storage)
    return errs


def is_control(identifier):
    return bool(CODE_RE.search(str(identifier or "")))


def main():
    proj = json.load(io.open(PROJ, encoding="utf-8"))
    design = {t: rows for t, _f, _entry, _exit, rows in pg.PAGES}
    fails = []

    g = proj["settings"]["general"]
    if (g["displayWidth"], g["displayHeight"]) != (W, H):
        fails.append("A1 工程分辨率 %dx%d ≠ %dx%d" % (g["displayWidth"], g["displayHeight"], W, H))

    # 字体：条目、文件、覆盖范围
    fonts = {f["name"]: f for f in proj.get("fonts", [])}
    covered = set()
    for name, f in fonts.items():
        path = os.path.join(ROOT, f["source"]["filePath"].replace("/", os.sep))
        if not os.path.isfile(path):
            fails.append("A5 字体 %s 的 TTF 不存在：%s" % (name, f["source"]["filePath"]))
            continue
        try:
            from fontTools.ttLib import TTFont
            tt = TTFont(path)
            cmap = set(tt.getBestCmap().keys())
            tt.close()
        except Exception as e:
            fails.append("A5 字体 %s 打不开：%s" % (name, e))
            continue
        ranges = set()
        for part in (f.get("lvglRanges") or "").split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                ranges |= set(range(int(a), int(b) + 1))
            else:
                ranges.add(int(part))
        covered |= (ranges & cmap)
        if ranges - cmap:
            fails.append("A5 字体 %s 声明了 TTF 里没有的码点 %d 个（例 %s）"
                         % (name, len(ranges - cmap), sorted(ranges - cmap)[:5]))

    def walk(comps, page_name):
        for c in comps:
            yield c
            for k in walk(c.get("children") or [], page_name):
                yield k

    total = 0
    rev = {v: k for k, v in PAGE_IDS.items()}      # 工程用 ASCII 标识，对账时换回中文页名
    for page in proj["userPages"]:
        name = rev.get(page["name"], page["name"])
        if (page["width"], page["height"]) != (W, H):
            fails.append("A1 页 %s 尺寸 %dx%d" % (name, page["width"], page["height"]))
        widgets = list(walk(page["components"], name))
        total += len(widgets)
        ids = [w.get("identifier") for w in widgets if w.get("identifier")]
        if len(ids) != len(set(ids)):
            fails.append("A7 页 %s 的 identifier 有重复" % name)
        if name not in design:
            fails.append("A2 工程里有设计源没有的页：%s" % name)
            continue
        if name == "Wi-Fi 设置":
            # 该页按示例工程结构生成（list/textarea/keyboard + 弹层），
            # identifier 是示例命名，不走类别码；这里改核「必需对象存在」。
            need = {"list_box", "overlay_root", "dlg_root", "pwd_ta", "kb_main",
                    "btn_refresh", "btn_connect", "scrim", "sheet"}
            have = {w.get("identifier") for w in widgets}
            miss = sorted(need - have)
            if miss:
                fails.append("A2 页 %s 缺必需对象：%s" % (name, miss))
            need_types = {"list_box": "LVGLListWidget", "pwd_ta": "LVGLTextareaWidget",
                          "kb_main": "LVGLKeyboardWidget", "overlay_root": "LVGLContainerWidget",
                          "dlg_root": "LVGLContainerWidget", "btn_connect": "LVGLButtonWidget",
                          "btn_refresh": "LVGLButtonWidget"}
            for ident, want in need_types.items():
                node = next((w for w in widgets if w.get("identifier") == ident), None)
                if node is not None and node["type"] != want:
                    fails.append("A12 页 %s 控件 %s 应为 %s，实际 %s"
                                 % (name, ident, want, node["type"]))
            continue
        rows = design[name]
        # 设计源控件 → 工程控件（按下标 + 框对账；标签类控件设计源里没有单独条目）
        boxes = {(r[4][0], r[4][1], r[4][2], r[4][3]) for r in rows}
        for w in widgets:
            if w["type"] == "LVGLScreenWidget":
                continue
            is_ctl = is_control(w.get("identifier"))   # <页>_<类别码>NN 是设计控件
            key = (w["left"], w["top"], w["width"], w["height"])
            if is_ctl and key not in boxes:
                fails.append("A3 页 %s 控件 %s 的框 %s 在设计源里找不到"
                             % (name, w.get("identifier"), key))
            if w["type"] == "LVGLButtonWidget":
                kids = w.get("children") or []
                txt = (kids[0].get("text") if kids else "") or ""
                if not txt.strip():
                    fails.append("A4 页 %s 按钮 %s 缺少承载文字的子标签" % (name, w.get("identifier")))
                if "text" in w:
                    fails.append("A4 页 %s 按钮 %s 不该有 text 字段" % (name, w.get("identifier")))
            elif w["type"] == "LVGLLabelWidget":
                if not (w.get("text") or "").strip():
                    fails.append("A4 页 %s 标签 %s 文本为空" % (name, w.get("identifier")))
                fname = (w.get("localStyles", {}).get("definition", {})
                          .get("MAIN", {}).get("DEFAULT", {}).get("text_font"))
                if fname and fname not in fonts:
                    fails.append("A6 页 %s 控件 %s 引用了不存在的字体 %s"
                                 % (name, w.get("identifier"), fname))
                if fname and covered:
                    miss = {c for c in (w.get("text") or "") if c.strip() and ord(c) not in covered}
                    if miss:
                        fails.append("A6 页 %s 控件 %s 有 %d 个字不在字体里（例 %s）"
                                     % (name, w.get("identifier"), len(miss), "".join(sorted(miss))[:6]))
        # 设计源里有、工程里没有的控件（按框反查）
        wboxes = {(w["left"], w["top"], w["width"], w["height"])
                  for w in widgets if is_control(w.get("identifier"))}
        missing = [r[0] for r in rows if (r[4][0], r[4][1], r[4][2], r[4][3]) not in wboxes]
        if missing:
            fails.append("A2 页 %s 缺控件 %d 个（例 %s）" % (name, len(missing), missing[:3]))

        # A9 类别码对账：每页控件 identifier 的码必须等于 io_of() 判出的类，
        # 且按「页内每类 01..N」连续编号；出现未知命名也报错（防漏改）。
        slug = PAGE_IDS.get(name, page["name"])
        expect, cnt = [], {}
        for r in rows:
            io_k = ov.io_of(name, {"name": r[0], "behav": r[3], "cat": r[1]})
            code = pg.IO_CODE[io_k]
            cnt[code] = cnt.get(code, 0) + 1
            expect.append("%s_%s%02d" % (slug, code, cnt[code]))
        got = [str(w.get("identifier", "")) for w in widgets if is_control(w.get("identifier"))]
        if sorted(got) != sorted(expect):
            fails.append("A9 页 %s 类别码对不上：期望 %s ｜ 实际 %s"
                         % (name, sorted(expect)[:4], sorted(got)[:4]))
        # A12 设计标注的类型必须是真实控件：开关→Switch、滑条→Slider、
        # 动作/跳转按钮→Button、输入→Textarea、进度→Bar、图表→Chart。
        by_id = {w.get("identifier"): w for w in widgets}
        for r, ident in zip(rows, expect):
            node = by_id.get(ident)
            if compound_kind(r[1], r[4]):
                if node is not None and node["type"] != "LVGLContainerWidget":
                    fails.append("A12 页 %s 控件 %s 是整卡交互区，应为容器，实际 %s"
                                 % (name, ident, node["type"]))
                suffix = "_sw" if r[1] == "toggle" else "_sl"
                want_child = "LVGLSwitchWidget" if r[1] == "toggle" else "LVGLSliderWidget"
                child = next((c for c in (node.get("children") or [])
                              if c.get("identifier") == ident + suffix), None) if node else None
                if node is not None and (child is None or child["type"] != want_child):
                    fails.append("A12 页 %s 控件 %s 卡内缺真实 %s"
                                 % (name, ident, want_child))
                continue
            want = KIND_TYPE[widget_kind(r[0], r[1], r[4])]
            if node is not None and node["type"] != want:
                fails.append("A12 页 %s 控件 %s 标注为 %s，应为 %s，实际 %s"
                             % (name, ident, r[1], want, node["type"]))
        known = CODE_RE.search
        for w in widgets:
            ident = str(w.get("identifier") or "")
            if w["type"] == "LVGLScreenWidget":
                continue
            if not ident:
                fails.append("A9 页 %s 有控件无 identifier（%s）" % (name, w["type"]))
            elif not (known(ident) or STATIC_RE.search(ident) or DECO_RE.search(ident)
                      or LB_RE.search(ident) or SW_RE.search(ident)):
                fails.append("A9 页 %s 出现未分类命名：%s" % (name, ident))

    ids_all = []

    def collect(o):
        if isinstance(o, dict):
            if "objID" in o:
                ids_all.append(o["objID"])
            for v in o.values():
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(proj)
    if len(ids_all) != len(set(ids_all)):
        fails.append("A7 objID 重复 %d 个" % (len(ids_all) - len(set(ids_all))))

    # A8 颜色值合法（EEZ Checks 会把 0XNONE / 0XURL(...) 报 invalid color）
    bad_color = []

    def walk_color(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if k in ("bg_color", "text_color", "border_color") and isinstance(v, str):
                    if not re.fullmatch(r"0x[0-9A-Fa-f]{6}", v):
                        bad_color.append((k, v))
                walk_color(v)
        elif isinstance(n, list):
            for x in n:
                walk_color(x)
    walk_color(proj)
    if bad_color:
        fails.append("A8 非法颜色值 %d 处（例 %s）" % (len(bad_color), bad_color[:3]))

    # A10 控件样式只能写 EEZ 的 LVGL 样式属性（字段集本身由 A14 卡模板库）
    for pgx in proj["userPages"]:
        for w in walk(pgx["components"], ""):
            defn = w.get("localStyles", {}).get("definition") or {}
            bad = set()
            for part in defn.values():
                for state in (part or {}).values():
                    bad |= set(state.keys()) - STYLE_KEYS
            if bad:
                fails.append("A10 %s 控件 %s 样式出现非 LVGL 属性：%s"
                             % (w.get("type"), w.get("identifier"), sorted(bad)))

    # A13 开关必须可切换：EEZ 生成的 Switch 样板缺 CHECKABLE 时点击不会变状态
    for pgx in proj["userPages"]:
        for w in walk(pgx["components"], ""):
            if w.get("type") == "LVGLSwitchWidget":
                if "CHECKABLE" not in str(w.get("widgetFlags", "")).split("|"):
                    fails.append("A13 开关 %s 缺 CHECKABLE 标志"
                                 % w.get("identifier"))

    # A14 每个控件的字段集必须等于标准模板库（只允许改值，不允许增删字段）
    std = {t: set(node.keys()) for t, node in templates().items()}
    a14_ok = a14_bad = 0
    for pgx in proj["userPages"]:
        for w in walk(pgx["components"], ""):
            typ = w.get("type")
            if typ not in std:
                fails.append("A14 %s 没有标准模板" % typ)
                a14_bad += 1
                continue
            extra = set(w.keys()) - std[typ]
            missing = std[typ] - set(w.keys())
            # 放置期才有的字段：identifier；hiddenFlag 只允许真正隐藏的遮罩（=True）；
            # Keyboard 绑定 textarea 后才出现该字段。
            extra -= {"identifier"}
            if w.get("hiddenFlag") is True:
                extra -= {"hiddenFlag"}
            if typ == "LVGLKeyboardWidget":
                extra -= {"textarea"}
            if extra or missing:
                fails.append("A14 %s 控件 %s 字段集不符（多 %s / 少 %s）"
                             % (typ, w.get("identifier"), sorted(extra),
                                sorted(missing)))
                a14_bad += 1
            else:
                a14_ok += 1
    print("[A14] 标准模板字段集 %d/%d" % (a14_ok, a14_ok + a14_bad))

    fs_path = os.path.join(HERE, "font_storage.json")
    storage = "image"
    if os.path.isfile(fs_path):
        storage = json.load(io.open(fs_path, encoding="utf-8")).get("storage", "image")
    fails += check_font_policy(proj.get("fonts", []), storage)

    print("工程页 %d ｜ 控件 %d ｜ 字体 %d（覆盖 %d 字符）"
          % (len(proj["userPages"]), total, len(fonts), len(covered)))
    print("[EEZ_CHECK] " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  !! " + f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
