# -*- coding: utf-8 -*-
"""校验控件模板：字段结构 + EEZ 新建控件标准默认值。

用法：
  python validate_templates.py
  python validate_templates.py --templates <dir> --defaults <defaults.json>
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


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


def check_canonical(t, typ, defaults, errs):
    """模板必须等于 EEZ classInfo.defaultValue/defaultFlags（新建控件标准值）。"""
    d = defaults.get(typ)
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
        child, cdv = kids[0], defaults["LVGLLabelWidget"]["defaultValue"]
        for k, v in cdv.items():
            if k in ("children", "localStyles", "clickableFlag", "text"):
                continue
            if child.get(k) != v:
                errs.append("Button 子 Label.%s=%r，标准值 %r" % (k, child.get(k), v))
        if child.get("text") != "Button":
            errs.append("Button 子 Label 文本应为 Button")
        exp_child_ls = {"MAIN": {"DEFAULT": {"align": "CENTER"}}}
        got_child_ls = (child.get("localStyles") or {}).get("definition", {})
        if got_child_ls != exp_child_ls:
            errs.append("Button 子 Label.localStyles 应仅 align CENTER")
        if child.get("widgetFlags") != defaults["LVGLLabelWidget"]["defaultFlags"]:
            errs.append("Button 子 Label.widgetFlags 与标准值不一致")
        if child.get("children"):
            errs.append("Button 子 Label 不应再有子控件")
    elif t.get("children"):
        errs.append("%s 不应带子控件（新建控件无子控件）" % typ)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates", default=os.path.join(HERE, "templates"))
    ap.add_argument("--defaults", default=os.path.join(HERE, "defaults.json"))
    a = ap.parse_args()
    defaults = json.load(open(a.defaults, encoding="utf-8"))
    files = sorted(glob.glob(os.path.join(a.templates, "*.json")))

    errs = []
    for f in files:
        t = json.load(open(f, encoding="utf-8"))
        typ = t.get("type")
        if not isinstance(t.get("identifier"), str) or not t["identifier"].startswith("tpl_"):
            errs.append("%s identifier 应以 tpl_ 开头" % typ)
        if t.get("states", "") != "":
            errs.append("%s states 应为空（标准初始态）" % typ)
        if "visibleRowCount" in t:
            errs.append("%s 残留旧字段 visibleRowCount" % typ)
        for k, want in (("checkedState", False), ("disabledState", False), ("hiddenFlag", False)):
            if k in t and t[k] is not want:
                errs.append("%s.%s 应为 %r" % (typ, k, want))
        for k in ("customInputs", "customOutputs"):
            if t.get(k) not in (None, []):
                errs.append("%s.%s 应为空" % (typ, k))
        style = t.get("style") or {}
        if style and (style.get("useStyle") != "default" or style.get("conditionalStyles")
                      or style.get("childStyles")):
            errs.append("%s.style 应为 default 且无条件样式" % typ)
        for n in walk(t):
            oid = n.get("objID")
            if oid is not None and not str(oid).startswith("__"):
                errs.append("%s 有真实 objID（应为占位符）" % typ)
            for k, v in n.items():
                if k.endswith("Type") and v == "expression":
                    errs.append("%s 残留表达式字段 %s" % (typ, k))
            for k in ("eventHandlers", "timeline"):
                if n.get(k) not in (None, []):
                    errs.append("%s.%s 应为空" % (typ, k))
        if typ == "LVGLSwitchWidget" and "CHECKABLE" not in t.get("widgetFlags", "").split("|"):
            errs.append("Switch 缺 CHECKABLE")
        if typ == "LVGLButtonWidget":
            kids = t.get("children") or []
            if len(kids) != 1 or kids[0].get("type") != "LVGLLabelWidget":
                errs.append("Button 必须恰一个子 Label")
        if typ == "LVGLKeyboardWidget" and not isinstance(t.get("textarea"), str):
            errs.append("Keyboard.textarea 必须是字符串")
        check_canonical(t, typ, defaults, errs)

    if errs:
        print("[TPL_CHECK] FAIL")
        for e in errs:
            print("  !!", e)
        sys.exit(1)
    print("[TPL_CHECK] PASS（%d 个模板：%s）" % (len(files), a.templates))


if __name__ == "__main__":
    main()
