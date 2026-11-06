# -*- coding: utf-8 -*-
"""只读校验：模板 = UI 工程保存对象；并核对 defaults/manifest 与占位符唯一性。"""
import copy
import glob
import json
import os
import sys

from extract_templates import placeholders, default_value

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "eez-widget-templates.eez-project")
TPL = os.path.join(HERE, "templates")


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


def main():
    proj = json.load(open(PROJ, encoding="utf-8"))
    pages = {p["name"]: p for p in proj["userPages"]}
    defaults = json.load(open(os.path.join(HERE, "defaults.json"), encoding="utf-8"))
    manifest = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    errs = []
    types = []
    for f in sorted(glob.glob(os.path.join(TPL, "*.json"))):
        t = json.load(open(f, encoding="utf-8"))
        typ = t["type"]
        if typ == "LVGLScreenWidget":
            page = "Label"
            w = copy.deepcopy(pages[page]["components"][0])
            w["children"] = []
        else:
            cand = [n for n, p in pages.items()
                    if p.get("components") and p["components"][0].get("children")
                    and p["components"][0]["children"][0].get("type") == typ]
            if not cand:
                errs.append("%s 找不到对应页面" % typ)
                continue
            page = cand[0]
            w = pages[page]["components"][0]["children"][0]

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
            if typ in ("LVGLLabelWidget", "LVGLSpinnerWidget"):
                if "clickableFlag" in t:
                    errs.append("%s 不应有 clickableFlag" % typ)
            elif "clickableFlag" not in t:
                errs.append("%s 缺 clickableFlag" % typ)
            ls = (t.get("localStyles") or {})
            if typ == "LVGLKeyboardWidget":
                if set(ls) - {"objID", "definition"}:
                    errs.append("%s localStyles 字段异常" % typ)
            elif set(ls) != {"objID"}:
                errs.append("%s localStyles 应只有 objID" % typ)

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
            if not os.path.isfile(os.path.join(HERE, m.get("file", ""))):
                errs.append("%s manifest.file 不存在" % typ)
            if "UI" not in m.get("source", ""):
                errs.append("%s manifest.source 未标明 UI 创建" % typ)
        types.append(typ)

    print("[TPL_CHECK] %s（%d 个模板）" % ("PASS" if not errs else "FAIL", len(types)))
    for e in errs:
        print("  !!", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
