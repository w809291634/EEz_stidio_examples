# -*- coding: utf-8 -*-
"""从真实 EEZ 工程提取控件模板，生成可构建的模板工程。

用法：python build_templates_project.py [--no-build]
产物：templates/<Type>.json + manifest.json + eez-widget-templates.eez-project
原则：每个模板必须来自真实拖拽工程；只归一化表达式/清空事件，不改字段集。
"""
import argparse
import copy
import json
import os
import re
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # EEZ_stidio_examples
TPL_DIR = os.path.join(HERE, "templates")
OUT_PROJ = os.path.join(HERE, "eez-widget-templates.eez-project")
SKELETON = os.path.join(ROOT, "widget-gallery", "widget-gallery.eez-project")
DEFAULTS = json.load(open(os.path.join(HERE, "defaults.json"), encoding="utf-8"))
EEZ_EXE = r"C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe"

# 类型 → (源工程相对 ROOT, 备注)
SOURCES = {
    "LVGLScreenWidget":       ("two-state-styles/two-state-styles.eez-project", "屏幕"),
    "LVGLLabelWidget":        ("two-state-styles/two-state-styles.eez-project", "标签"),
    "LVGLButtonWidget":       ("app-wifi-connect/app-wifi-connect.eez-project", "按钮（含一个子标签）"),
    "LVGLContainerWidget":    ("app-wifi-connect/app-wifi-connect.eez-project", "容器"),
    "LVGLPanelWidget":        ("widget-gallery/widget-gallery.eez-project", "面板"),
    "LVGLSwitchWidget":       ("two-state-styles/two-state-styles.eez-project", "开关（必须 CHECKABLE）"),
    "LVGLSliderWidget":       ("w67-w3-w2-slider-arc-bar/w67-w3-w2-slider-arc-bar.eez-project", "滑条"),
    "LVGLBarWidget":          ("w67-w3-w2-slider-arc-bar/w67-w3-w2-slider-arc-bar.eez-project", "进度条"),
    "LVGLArcWidget":          ("w67-w3-w2-slider-arc-bar/w67-w3-w2-slider-arc-bar.eez-project", "圆弧"),
    "LVGLChartWidget":        ("w14-w35-w62-chart-led-scale/w14-w35-w62-chart-led-scale.eez-project", "图表"),
    "LVGLScaleWidget":        ("w14-w35-w62-chart-led-scale/w14-w35-w62-chart-led-scale.eez-project", "刻度"),
    "LVGLLedWidget":          ("w14-w35-w62-chart-led-scale/w14-w35-w62-chart-led-scale.eez-project", "LED"),
    "LVGLCheckboxWidget":     ("two-state-styles/two-state-styles.eez-project", "复选框"),
    "LVGLDropdownWidget":     ("w23-w59-w73-w16-select-switch/w23-w59-w73-w16-select-switch.eez-project", "下拉框"),
    "LVGLRollerWidget":       ("w23-w59-w73-w16-select-switch/w23-w59-w73-w16-select-switch.eez-project", "滚轮"),
    "LVGLTextareaWidget":     ("app-wifi-connect/app-wifi-connect.eez-project", "输入框"),
    "LVGLKeyboardWidget":     ("app-wifi-connect/app-wifi-connect.eez-project", "键盘"),
    "LVGLListWidget":         ("app-wifi-scan-conn-no-flow/app-wifi-scan-conn-no-flow.eez-project", "列表"),
    "LVGLSpinnerWidget":      ("widget-gallery/widget-gallery.eez-project", "转圈"),
}
# 模板工程里额外出现的页面（Screen 只做模板，不当 gallery 页）
TYPE_ORDER = [t for t in SOURCES if t != "LVGLScreenWidget"]


def find(node, typ):
    if isinstance(node, dict):
        if node.get("type") == typ:
            return node
        for v in node.values():
            r = find(v, typ)
            if r:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find(v, typ)
            if r:
                return r
    return None


def norm(node):
    """清事件、表达式、objID 占位；保留字段集。"""
    if isinstance(node, dict):
        out = copy.deepcopy(node)
        for k in ("objID",):
            if k in out:
                out[k] = "__OBJID__"
        if isinstance(out.get("style"), dict) and "objID" in out["style"]:
            out["style"]["objID"] = "__STYLE_OBJID__"
        if isinstance(out.get("localStyles"), dict) and "objID" in out["localStyles"]:
            out["localStyles"]["objID"] = "__LOCAL_STYLE_OBJID__"
        out["eventHandlers"] = []
        out["timeline"] = []
        if "hiddenFlag" in out:
            out["hiddenFlagType"] = "literal"
            out["hiddenFlag"] = False
        if "checkedState" in out:
            out["checkedStateType"] = "literal"
            out["checkedState"] = False
        if "disabledState" in out:
            out["disabledStateType"] = "literal"
            out["disabledState"] = False
        for k in list(out.keys()):
            if k.endswith("Type") and out[k] == "expression":
                base = k[:-4]
                out[k] = "literal"
                if base in out:
                    if base in ("text", "placeholder", "acceptedCharacters"):
                        out[base] = ""
                    elif base == "options":
                        out[base] = "Option A\nOption B"
                    elif base == "labelTexts":
                        out[base] = "0\n50\n100"
                    elif base == "color":
                        out[base] = "0xFF0000"
                    elif isinstance(out[base], (int, float)):
                        pass
                    else:
                        out[base] = 0
        out["children"] = [norm(c) for c in out.get("children", [])]
        return out
    if isinstance(node, list):
        return [norm(x) for x in node]
    return copy.deepcopy(node)


def _apply_fields(target, dv):
    """按 classInfo.defaultValue 复位字段；children/localStyles 单独处理。"""
    for k, v in dv.items():
        if k in ("children", "localStyles", "clickableFlag"):
            continue
        target[k] = copy.deepcopy(v)
    target["widgetFlags"] = DEFAULTS[target["type"]]["defaultFlags"]
    definition = copy.deepcopy(dv.get("localStyles", {}).get("definition", {}))
    target["localStyles"] = {"objID": "__LOCAL_STYLE_OBJID__", "definition": definition}
    target["states"] = ""
    if "checkedState" in target:
        target["checkedState"] = False
        target["checkedStateType"] = "literal"
    if "disabledState" in target:
        target["disabledState"] = False
        target["disabledStateType"] = "literal"


def apply_defaults(tpl, typ):
    """把真实拖拽控件的字段集复位为 EEZ 新建控件的标准默认值。"""
    src_children = tpl.get("children") or []
    _apply_fields(tpl, DEFAULTS[typ]["defaultValue"])
    tpl["children"] = []
    if typ == "LVGLButtonWidget":
        child = norm(src_children[0])
        child["identifier"] = "tpl_button_label"
        _apply_fields(child, DEFAULTS["LVGLLabelWidget"]["defaultValue"])
        child.update({"text": "Button", "textType": "literal",
                      "localStyles": {"objID": "__LOCAL_STYLE_OBJID__",
                                      "definition": {"MAIN": {"DEFAULT": {"align": "CENTER"}}}}})
        child["children"] = []
        tpl["children"] = [child]
    tpl.pop("visibleRowCount", None)
    return tpl


def slug(typ):
    return re.sub(r"^LVGL|Widget$", "", typ).lower()


def extract():
    os.makedirs(TPL_DIR, exist_ok=True)
    manifest = {}
    for typ, (rel, note) in SOURCES.items():
        p = os.path.join(ROOT, rel)
        proj = json.load(open(p, encoding="utf-8"))
        node = find(proj["userPages"], typ)
        if not node:
            raise SystemExit("找不到 %s 于 %s" % (typ, rel))
        src_ident = node.get("identifier", "")
        tpl = apply_defaults(norm(node), typ)
        tpl["identifier"] = "tpl_" + slug(typ)
        if typ == "LVGLSwitchWidget":
            if "CHECKABLE" not in tpl.get("widgetFlags", "").split("|"):
                raise SystemExit("Switch 样板缺 CHECKABLE：%s" % rel)
        if typ == "LVGLButtonWidget":
            kids = tpl.get("children") or []
            if len(kids) != 1 or kids[0].get("type") != "LVGLLabelWidget":
                raise SystemExit("Button 样板必须恰一个子 Label：%s" % rel)
        if typ == "LVGLKeyboardWidget":
            tpl["textarea"] = ""
        out = os.path.join(TPL_DIR, typ + ".json")
        json.dump(tpl, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        manifest[typ] = {"source": rel, "source_identifier": src_ident,
                         "file": "templates/%s.json" % typ, "note": note,
                         "defaults": "defaults.json"}
        print("[TPL] %-26s <- %s %s" % (typ, rel, src_ident))
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return manifest


def uid():
    return str(uuid.uuid4())


def fill_ids(node):
    if isinstance(node, dict):
        if "objID" in node:
            node["objID"] = uid()
        if isinstance(node.get("style"), dict) and "objID" in node["style"]:
            node["style"]["objID"] = uid()
        if isinstance(node.get("localStyles"), dict) and "objID" in node["localStyles"]:
            node["localStyles"]["objID"] = uid()
        for v in node.values():
            fill_ids(v)
    elif isinstance(node, list):
        for v in node:
            fill_ids(v)
    return node


def make_gallery(manifest):
    sk = json.load(open(SKELETON, encoding="utf-8"))
    g = sk["settings"]["general"]
    g.update({"displayWidth": 800, "displayHeight": 480, "flowSupport": False,
              "projectVersion": "v3", "projectType": "lvgl", "lvglVersion": "9.4.0",
              "colorBpp": "16", "bitmapColorFormat": "BGR", "darkTheme": True})
    bd = sk["settings"]["build"]
    bd.update({"destinationFolder": os.path.join(HERE, "src", "ui"),
               "lvglInclude": "lvgl.h", "fontExportMode": "source",
               "imageExportMode": "source"})
    if "generateSourceCodeForEezFramework" in bd:
        bd["generateSourceCodeForEezFramework"] = False
    sk["actions"] = []
    sk["userWidgets"] = []
    sk["variables"] = {"objID": uid(), "globalVariables": [], "structures": [], "enums": []}
    sk["fonts"] = []
    sk["bitmaps"] = []
    sk["colors"] = []
    sk["lvglStyles"] = {"objID": uid(), "styles": [], "defaultStyles": []}
    sk["lvglGroups"] = {"objID": uid(), "groups": []}
    sk["userPages"] = []

    screen_tpl = json.load(open(os.path.join(TPL_DIR, "LVGLScreenWidget.json"), encoding="utf-8"))
    for i, typ in enumerate(TYPE_ORDER):
        tpl = json.load(open(os.path.join(TPL_DIR, typ + ".json"), encoding="utf-8"))
        name = "tpl_" + slug(typ)
        root = fill_ids(copy.deepcopy(screen_tpl))
        root.update({"left": 0, "top": 0, "width": 800, "height": 480, "children": []})
        w = fill_ids(copy.deepcopy(tpl))
        w["identifier"] = "w_" + slug(typ)
        w["left"], w["top"] = 40, 60
        if "width" in w and isinstance(w["width"], int):
            w["width"] = min(w["width"], 720)
        if "height" in w and isinstance(w["height"], int):
            w["height"] = min(w["height"], 360)
        root["children"] = [w]
        sk["userPages"].append({
            "objID": uid(), "name": name, "left": 0, "top": 0, "width": 800, "height": 480,
            "isUsedAsUserWidget": False, "createAtStart": i == 0,
            "deleteOnScreenUnload": False, "connectionLines": [],
            "localVariables": [], "componentGroups": [], "userProperties": [],
            "components": [root],
        })
    json.dump(sk, open(OUT_PROJ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[PROJ]", OUT_PROJ, "%d 页" % len(sk["userPages"]))
    return sk


def build():
    env = dict(os.environ)
    env.pop("ELECTRON_RUN_AS_NODE", None)
    log = os.path.join(HERE, "build.log")
    with open(log, "w", encoding="utf-8") as f:
        p = subprocess.Popen([EEZ_EXE, "--build-project", OUT_PROJ, "--no-sandbox",
                              "--disable-gpu", "--enable-unsafe-swiftshader",
                              "--disable-dev-shm-usage"],
                             stdout=f, stderr=subprocess.STDOUT, env=env,
                             creationflags=0x08000000)
        deadline = time.time() + 240
        ok = False
        while time.time() < deadline:
            time.sleep(2)
            f.flush()
            txt = open(log, encoding="utf-8", errors="replace").read()
            if "Build successfully finished" in txt:
                ok = True
                break
        p.terminate()
        try:
            p.wait(timeout=10)
        except Exception:
            subprocess.call(["taskkill", "/F", "/IM", "EEZ Studio.exe"], shell=False)
    if not ok:
        print("[BUILD] FAILED，见", log)
        print(open(log, encoding="utf-8", errors="replace").read()[-1200:])
        sys.exit(1)
    print("[BUILD] OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()
    m = extract()
    make_gallery(m)
    if not a.no_build:
        build()
        subprocess.check_call([sys.executable, os.path.join(HERE, "validate_templates.py")])
