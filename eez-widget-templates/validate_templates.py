# -*- coding: utf-8 -*-
"""只读校验：模板 = UI 工程保存对象；并核对 defaults/manifest 与占位符唯一性。"""
import copy
import glob
import json
import os
import re
import sys

from extract_templates import placeholders, default_value

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "eez-widget-templates.eez-project")
TPL = os.path.join(HERE, "templates")
EXPECTED_PAGES = 35
EXPECTED_TEMPLATES = 37
PALETTE_NAME = {"LVGLTabWidget": "Tab", "LVGLSpanWidget": "Spangroup"}
PALETTE = set("""Arc Button ButtonMatrix Container Image Label List Menu MessageBox
QRCode Panel Spangroup Table Tabview Tab Textarea TileView Window Calendar Checkbox
Dropdown Imgbutton Keyboard Roller Spinbox Slider Switch AnimationImage Bar Chart
Canvas Led Line Lottie Scale Spinner""".split())
NO_CLICKABLE = {"LVGLLabelWidget", "LVGLSpinnerWidget", "LVGLImageWidget",
                "LVGLAnimationImageWidget", "LVGLCanvasWidget", "LVGLLineWidget"}
UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def collect_ids(node):
    out = []

    def rec(o):
        if isinstance(o, dict):
            if "objID" in o:
                out.append(o["objID"])
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(node)
    return out


def has_key(node, key):
    if isinstance(node, dict):
        return key in node or any(has_key(v, key) for v in node.values())
    if isinstance(node, list):
        return any(has_key(v, key) for v in node)
    return False


def main():
    proj = json.load(open(PROJ, encoding="utf-8"))
    pages = {p["name"]: p for p in proj["userPages"]}
    defaults = json.load(open(os.path.join(HERE, "defaults.json"), encoding="utf-8"))
    manifest = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    errs = []

    if len(proj.get("userPages", [])) != EXPECTED_PAGES:
        errs.append("工程页数=%d，应为 %d" % (len(proj.get("userPages", [])), EXPECTED_PAGES))
    if len(pages) != len(proj.get("userPages", [])):
        errs.append("工程存在重名页")

    page_types = {}

    def widgets(node):
        """Palette 控件 + Tabview 内嵌的 Tab；Button 子 Label 等不算独立模板。"""
        for c in node.get("children", []):
            yield c
            if c.get("type") == "LVGLTabviewWidget":
                for t in c.get("children", []):
                    if t.get("type") == "LVGLTabWidget":
                        yield t

    for name, p in pages.items():
        comps = p.get("components") or []
        if not comps:
            errs.append("%s 缺 screen 根" % name)
            continue
        ch = comps[0].get("children") or []
        if len(ch) != 1:
            errs.append("%s 子控件数=%d，应为 1" % (name, len(ch)))
            continue
        for w in widgets(comps[0]):
            typ = w.get("type")
            if typ in page_types:
                errs.append("重复控件类型 %s：%s / %s" % (typ, page_types[typ], name))
            page_types[typ] = name

    all_ids = collect_ids(proj)
    if len(all_ids) != len(set(all_ids)):
        errs.append("工程 objID 不唯一：%d 个 / %d 唯一" % (len(all_ids), len(set(all_ids))))

    types = []
    for f in sorted(glob.glob(os.path.join(TPL, "*.json"))):
        t = json.load(open(f, encoding="utf-8"))
        typ = t.get("type")
        if not typ:
            errs.append("%s 缺 type" % os.path.basename(f))
            continue
        if os.path.basename(f) != typ + ".json":
            errs.append("%s 文件名与 type=%s 不一致" % (os.path.basename(f), typ))
        if typ in types:
            errs.append("模板类型重复：%s" % typ)
        if typ == "LVGLScreenWidget":
            page = "Label"
            if page not in pages or not pages[page].get("components"):
                errs.append("Screen 模板找不到页面根 %s" % page)
                continue
            w = copy.deepcopy(pages[page]["components"][0])
            w["children"] = []
        else:
            page = page_types.get(typ)
            if not page:
                errs.append("%s 找不到对应页面" % typ)
                continue
            w = next(x for x in widgets(pages[page]["components"][0])
                     if x.get("type") == typ)

        expected = placeholders(w)
        if t != expected:
            ka, kb = set(t), set(expected)
            if ka - kb:
                errs.append("%s 模板多字段 %s" % (typ, sorted(ka - kb)))
            if kb - ka:
                errs.append("%s 模板少字段 %s" % (typ, sorted(kb - ka)))
            for k in sorted(ka & kb):
                if t[k] != expected[k]:
                    errs.append("%s.%s 不一致" % (typ, k))

        ids = collect_ids(t)
        if len(ids) != len(set(ids)):
            errs.append("%s 占位符撞 ID：%s" % (typ, ids))
        if has_key(t, "identifier"):
            errs.append("%s 不应带 identifier（放置/克隆时赋）" % typ)
        if UUID_RE.search(json.dumps(t, ensure_ascii=False)):
            errs.append("%s 残留真实 UUID" % typ)

        if typ != "LVGLScreenWidget":
            for k in ("hiddenFlag", "checkedState", "textarea"):
                if k in t:
                    errs.append("%s 不应有 %s（拖拽保存语法）" % (typ, k))
            for k in ("flagScrollbarMode", "flagScrollDirection", "scrollSnapX",
                      "scrollSnapY", "group"):
                if k not in t:
                    errs.append("%s 缺 %s（拖拽保存语法）" % (typ, k))
            if t.get("flagScrollbarMode") != "":
                errs.append("%s flagScrollbarMode 应为空" % typ)
            if "CLICKABLE" in t.get("widgetFlags", "").split("|"):
                errs.append("%s widgetFlags 不应含 CLICKABLE" % typ)
            if typ in NO_CLICKABLE:
                if "clickableFlag" in t:
                    errs.append("%s 不应有 clickableFlag" % typ)
            elif "clickableFlag" not in t:
                errs.append("%s 缺 clickableFlag" % typ)
            ls = (t.get("localStyles") or {})
            if "objID" not in ls or set(ls) - {"objID", "definition"}:
                errs.append("%s localStyles 只允许 objID/definition" % typ)

        d = defaults.get(typ)
        if not d:
            errs.append("%s 缺 defaults 条目" % typ)
        else:
            if d.get("page") != page:
                errs.append("%s defaults.page=%r，应为 %r" % (typ, d.get("page"), page))
            if d.get("defaultFlags") != t.get("widgetFlags", ""):
                errs.append("%s defaults.defaultFlags 不一致" % typ)
            if d.get("defaultValue") != default_value(t):
                errs.append("%s defaults.defaultValue 不一致" % typ)

        m = manifest.get(typ)
        if not m:
            errs.append("%s 缺 manifest 条目" % typ)
        else:
            if m.get("page") != page:
                errs.append("%s manifest.page 不一致" % typ)
            if m.get("file") != "templates/%s.json" % typ:
                errs.append("%s manifest.file=%r，应为 templates/%s.json"
                            % (typ, m.get("file"), typ))
            elif not os.path.isfile(os.path.join(HERE, m["file"])):
                errs.append("%s manifest.file 不存在" % typ)
            if "UI" not in m.get("source", ""):
                errs.append("%s manifest.source 未标明 UI 创建" % typ)
            if typ != "LVGLScreenWidget":
                want = PALETTE_NAME.get(typ, page)
                if m.get("palette") != want:
                    errs.append("%s manifest.palette=%r，应为 %r"
                                % (typ, m.get("palette"), want))
        types.append(typ)

    expected_types = set(page_types) | {"LVGLScreenWidget"}
    if set(types) != expected_types:
        extra = sorted(set(types) - expected_types)
        missing = sorted(expected_types - set(types))
        if extra:
            errs.append("多出模板：%s" % extra)
        if missing:
            errs.append("缺模板：%s" % missing)
    if len(types) != EXPECTED_TEMPLATES:
        errs.append("模板数=%d，应为 %d" % (len(types), EXPECTED_TEMPLATES))

    default_types = set(defaults) - {"_meta"}
    if default_types != set(types):
        errs.append("defaults 条目与模板不一致：多 %s 缺 %s"
                    % (sorted(default_types - set(types)),
                       sorted(set(types) - default_types)))
    if set(manifest) != set(types):
        errs.append("manifest 条目与模板不一致：多 %s 缺 %s"
                    % (sorted(set(manifest) - set(types)),
                       sorted(set(types) - set(manifest))))
    covered = {m.get("palette") for typ, m in manifest.items()
               if typ != "LVGLScreenWidget"}
    if covered != PALETTE:
        errs.append("Palette 覆盖不一致：缺 %s 多 %s"
                    % (sorted(PALETTE - covered), sorted(covered - PALETTE)))
    meta = defaults.get("_meta", {})
    if meta.get("pages") != len(pages):
        errs.append("defaults._meta.pages=%r，应为 %d" % (meta.get("pages"), len(pages)))
    if meta.get("templates") != len(types):
        errs.append("defaults._meta.templates=%r，应为 %d"
                    % (meta.get("templates"), len(types)))
    if meta.get("project") != os.path.basename(PROJ):
        errs.append("defaults._meta.project=%r" % (meta.get("project"),))
    if "UI" not in meta.get("source", ""):
        errs.append("defaults._meta.source 未标明 UI 创建")

    print("[TPL_CHECK] %s（%d 个模板）" % ("PASS" if not errs else "FAIL", len(types)))
    for e in errs:
        print("  !!", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
