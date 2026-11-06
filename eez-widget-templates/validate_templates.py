# -*- coding: utf-8 -*-
"""只读校验：templates/ 是否等于 UI 工程各画布保存下来的控件语法。"""
import copy
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "eez-widget-templates.eez-project")
TPL = os.path.join(HERE, "templates")


def norm(node):
    node = copy.deepcopy(node)

    def rec(o):
        if isinstance(o, dict):
            o.pop("objID", None)
            o.pop("identifier", None)
            o.pop("left", None)
            o.pop("top", None)
            if isinstance(o.get("style"), dict):
                o["style"].pop("objID", None)
            if isinstance(o.get("localStyles"), dict):
                o["localStyles"].pop("objID", None)
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(node)
    return node


def main():
    proj = json.load(open(PROJ, encoding="utf-8"))
    pages = {p["name"]: p for p in proj["userPages"]}
    errs = []
    types = []
    for f in sorted(glob.glob(os.path.join(TPL, "*.json"))):
        t = json.load(open(f, encoding="utf-8"))
        typ = t["type"]
        if typ == "LVGLScreenWidget":
            page = pages["Label"]
            w = page["components"][0]
            w = copy.deepcopy(w)
            w["children"] = []
        else:
            name = t["identifier"][4:] if t["identifier"].startswith("tpl_") else None
            # page names are the control names used during UI drag
            cand = [p for p in pages.values()
                    if p.get("components") and p["components"][0].get("children")
                    and p["components"][0]["children"][0].get("type") == typ]
            if not cand:
                errs.append("%s 找不到对应页面" % typ)
                continue
            w = cand[0]["components"][0]["children"][0]
        # 防止退回旧模板：拖拽保存语法的基础字段/标志约束
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
        a, b = norm(t), norm(w)
        if a != b:
            ka, kb = set(a), set(b)
            if ka - kb:
                errs.append("%s 模板多字段 %s" % (typ, sorted(ka - kb)))
            if kb - ka:
                errs.append("%s 模板少字段 %s" % (typ, sorted(kb - ka)))
            for k in sorted(ka & kb):
                if a[k] != b[k]:
                    errs.append("%s.%s 不一致" % (typ, k))
        types.append(typ)
    print("[TPL_CHECK] %s（%d 个模板）" % ("PASS" if not errs else "FAIL", len(types)))
    for e in errs:
        print("  !!", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
