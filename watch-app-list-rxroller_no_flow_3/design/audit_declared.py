# -*- coding: utf-8 -*-
"""④-A 声明层对账（§2.2 四层两站·第一站，判据=差异 0）。

三方对账：
  1) declared_manifest.json（生成器自认为写了什么）↔ watch.eez-project（工程实际有什么）
     —— identifier/类型/坐标/尺寸/文本/字体/颜色逐项比；
  2) 工程 ↔ 设计源控件清单表（CONTROLS 44 项）：每项须能按 identifier 前缀在工程里找到落点；
  3) 资源闭环：工程引用的每个 text_font 都在 fonts[]，每个 image 都在 bitmaps[]，
     每个 CONTROLS 的跳转目标页都在 userPages。

跑法：python design/audit_declared.py     退出码 0=全绿；非 0=有差异（打印差异表）
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import design_source as ds

PROJ = os.path.join(ROOT, "watch.eez-project")
MANIFEST = os.path.join(ROOT, "build", "declared_manifest.json")

diffs = []


def D(cat, key, want, got):
    diffs.append("%-14s %-52s want=%s got=%s" % (cat, key, want, got))


def walk_widgets(w, out):
    if "identifier" in w:
        out[w["identifier"]] = w
    for c in w.get("children", []):
        walk_widgets(c, out)


def main():
    proj = json.load(io.open(PROJ, encoding="utf-8"))
    man = json.load(io.open(MANIFEST, encoding="utf-8"))

    actual = {}
    page_names = []
    for p in proj["userPages"]:
        page_names.append(p["name"])
        for c in p["components"]:
            walk_widgets(c, actual)

    # 1) manifest ↔ 工程
    for m in man:
        a = actual.get(m["identifier"])
        if a is None:
            D("缺控件", m["identifier"], m["type"], "MISSING")
            continue
        for k in ("type", "left", "top", "width", "height"):
            if a.get(k) != m[k]:
                D("几何/类型", m["identifier"] + "." + k, m[k], a.get(k))
        if m["text"] is not None and a.get("text") != m["text"]:
            D("文本", m["identifier"], m["text"], a.get("text"))
        md = a.get("localStyles", {}).get("definition", {}).get("MAIN", {}).get("DEFAULT", {})
        for k in ("text_font", "text_color", "bg_color"):
            want = m.get({"text_font": "font", "text_color": "text_color",
                          "bg_color": "bg_color"}[k])
            if want is not None and md.get(k) != want:
                D("样式", m["identifier"] + "." + k, want, md.get(k))

    # 2) 清单表 44 项落点（identifier 前缀=页_页_id）
    for page in ds.PAGES:
        for _seq, ids, desc, jump, cat, hw in ds.CONTROLS.get(page["name"], []):
            for token in ids:
                wid = token.rstrip("+")
                tok = ("%s_%s" % (page["name"], wid)).replace(".", "_")
                hits = [k for k in actual if tok in k]
                if not hits:
                    D("清单落点", "%s.%s(%s)" % (page["name"], wid, desc), "≥1 个 identifier", "0")

    # 3) 资源闭环
    font_names = {f["name"] for f in proj["fonts"]}
    bmp_names = {b["name"] for b in proj["bitmaps"]}

    def res_check(w):
        md = w.get("localStyles", {}).get("definition", {}).get("MAIN", {}).get("DEFAULT", {})
        tf = md.get("text_font")
        if tf and tf not in font_names:
            D("缺字体", w.get("identifier", "?"), tf, "不在 fonts[]")
        img = w.get("image")
        if w.get("type") == "LVGLImageWidget" and img not in bmp_names:
            D("缺位图", w.get("identifier", "?"), img, "不在 bitmaps[]")
        for c in w.get("children", []):
            res_check(c)

    for p in proj["userPages"]:
        for c in p["components"]:
            res_check(c)

    want_pages = {"tab_main"} | {p["name"] for p in ds.PAGES
                                 if p["name"] not in ("watchface", "applist")}
    miss_pages = want_pages - set(page_names)
    for mp in sorted(miss_pages):
        D("缺页", mp, "存在", "MISSING")

    if diffs:
        print("④-A 对账 FAIL，差异 %d 条：" % len(diffs))
        for d in diffs[:80]:
            print("  " + d)
        sys.exit(1)
    print("④-A 对账 PASS：声明条目 %d / 工程控件 %d / 页 %d / 字体 %d / 位图 %d，差异=0"
          % (len(man), len(actual), len(page_names), len(font_names), len(bmp_names)))


if __name__ == "__main__":
    main()
