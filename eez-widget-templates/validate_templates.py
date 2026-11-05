# -*- coding: utf-8 -*-
"""校验控件模板语法（不依赖 EEZ 打开）。"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "templates")
DEFAULTS = json.load(open(os.path.join(HERE, "defaults.json"), encoding="utf-8"))


def check_canonical(t, typ, errs):
    """模板必须等于 EEZ classInfo.defaultValue（新建控件标准值）。"""
    d = DEFAULTS.get(typ)
    if not d:
        errs.append("%s 不在 defaults.json" % typ)
        return
    dv = d["defaultValue"]
    for k, v in dv.items():
        if k in ("children", "localStyles", "clickableFlag"):
            continue
        if t.get(k) != v:
            errs.append("%s.%s=%r，标准值 %r" % (typ, k, t.get(k), v))
    if t.get("widgetFlags") != d["defaultFlags"]:
        errs.append("%s.widgetFlags 与标准值不一致" % typ)
    exp = dv.get("localStyles", {}).get("definition", {})
    got = (t.get("localStyles") or {}).get("definition", {})
    if got != exp:
        errs.append("%s.localStyles 残留非标准样式" % typ)
    if typ == "LVGLButtonWidget":
        kids = t.get("children") or []
        if len(kids) != 1 or kids[0].get("type") != "LVGLLabelWidget":
            return
        child, cdv = kids[0], DEFAULTS["LVGLLabelWidget"]["defaultValue"]
        for k, v in cdv.items():
            if k in ("children", "localStyles", "clickableFlag", "text"):
                continue
            if child.get(k) != v:
                errs.append("Button 子 Label.%s=%r，标准值 %r" % (k, child.get(k), v))
        if child.get("text") != "Button":
            errs.append("Button 子 Label 文本应为 Button")
        align = (((child.get("localStyles") or {}).get("definition") or {})
                 .get("MAIN", {}).get("DEFAULT", {}).get("align"))
        if align != "CENTER":
            errs.append("Button 子 Label 应 align CENTER")
        if child.get("widgetFlags") != DEFAULTS["LVGLLabelWidget"]["defaultFlags"]:
            errs.append("Button 子 Label.widgetFlags 与标准值不一致")
    elif t.get("children"):
        errs.append("%s 不应带子控件（新建控件无子控件）" % typ)


def walk(n):
    if isinstance(n, dict):
        yield n
        for v in n.values():
            for x in walk(v):
                yield x
    elif isinstance(n, list):
        for v in n:
            for x in walk(v):
                yield x


def main():
    errs = []
    for f in sorted(glob.glob(os.path.join(TPL, "*.json"))):
        t = json.load(open(f, encoding="utf-8"))
        typ = t.get("type")
        for n in walk(t):
            oid = n.get("objID")
            if oid is not None and not str(oid).startswith("__"):
                errs.append("%s 有真实 objID（应为占位符）" % typ)
            for k, v in n.items():
                if k.endswith("Type") and v == "expression":
                    errs.append("%s 残留表达式字段 %s" % (typ, k))
        if typ == "LVGLSwitchWidget" and "CHECKABLE" not in t.get("widgetFlags", "").split("|"):
            errs.append("Switch 缺 CHECKABLE")
        if typ == "LVGLButtonWidget":
            kids = t.get("children") or []
            if len(kids) != 1 or kids[0].get("type") != "LVGLLabelWidget":
                errs.append("Button 必须恰一个子 Label")
        if typ == "LVGLKeyboardWidget" and not isinstance(t.get("textarea"), str):
            errs.append("Keyboard.textarea 必须是字符串")
        check_canonical(t, typ, errs)
    if errs:
        print("[TPL_CHECK] FAIL")
        for e in errs:
            print("  !!", e)
        sys.exit(1)
    print("[TPL_CHECK] PASS（%d 个模板）" % len(glob.glob(os.path.join(TPL, "*.json"))))


if __name__ == "__main__":
    main()
