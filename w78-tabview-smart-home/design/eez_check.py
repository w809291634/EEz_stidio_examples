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
from eez_gen import PAGE_IDS        # noqa: E402

PROJ = os.path.join(ROOT, "w78-smart-home.eez-project")
W, H = 800, 480

# 类别码：长码在前，避免 hw01 被当成 w01
CODE_RE = re.compile(r"_(hw|hr|go|w|r)(\d{2})$")
STATIC_RE = re.compile(r"_st\d{2}$")
DECO_RE = re.compile(r"_deco\d{2}$")
LB_RE = re.compile(r"_(?:hw|hr|go|w|r)\d{2}_lb$")


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
        known = CODE_RE.search
        for w in widgets:
            ident = str(w.get("identifier") or "")
            if w["type"] == "LVGLScreenWidget":
                continue
            if not ident:
                fails.append("A9 页 %s 有控件无 identifier（%s）" % (name, w["type"]))
            elif not (known(ident) or STATIC_RE.search(ident) or DECO_RE.search(ident)
                      or LB_RE.search(ident)):
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

    print("工程页 %d ｜ 控件 %d ｜ 字体 %d（覆盖 %d 字符）"
          % (len(proj["userPages"]), total, len(fonts), len(covered)))
    print("[EEZ_CHECK] " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  !! " + f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
