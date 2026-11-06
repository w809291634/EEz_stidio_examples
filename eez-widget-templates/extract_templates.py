# -*- coding: utf-8 -*-
"""只读提取：从 EEZ UI 创建并保存的工程读取控件语法，写 templates/defaults/manifest。

不创建、不修改 .eez-project；工程必须由 EEZ Studio 的 UI 新建/拖拽/保存。
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "eez-widget-templates.eez-project")
# 每个 Palette 控件一页；Tab 不是独立页，它由 Tabview 页内的宿主保存。
PAGES = ["Arc", "Bar", "Button", "ButtonMatrix", "Calendar", "Canvas", "Chart",
         "Checkbox", "Container", "Dropdown", "Image", "Imgbutton", "Keyboard",
         "Label", "Led", "Line", "List", "Lottie", "Menu", "MessageBox",
         "Panel", "QRCode", "Roller", "Scale", "Slider", "Spangroup", "Spinbox",
         "Spinner", "Switch", "Table", "Tabview", "Textarea", "TileView",
         "Window", "AnimationImage"]


def ph(prefix, role):
    return "__%s%s__" % ((prefix + "_") if prefix else "", role)


def placeholders(node, prefix=""):
    """按层级给三个身份角色独立占位符，并去掉放置时才赋值的 identifier。"""
    node = copy.deepcopy(node)

    def rec(o, pre):
        if isinstance(o, dict):
            if "objID" in o:
                o["objID"] = ph(pre, "OBJID")
            if isinstance(o.get("style"), dict) and "objID" in o["style"]:
                o["style"]["objID"] = ph(pre, "STYLE_OBJID")
            if isinstance(o.get("localStyles"), dict) and "objID" in o["localStyles"]:
                o["localStyles"]["objID"] = ph(pre, "LOCAL_STYLE_OBJID")
            o.pop("identifier", None)
            for i, c in enumerate(o.get("children", [])):
                rec(c, (pre + "_" if pre else "") + "CHILD%d" % i)
            # 非 children 的对象列表（如 Spangroup 的 spans）也带 objID
            for k, v in o.items():
                if k in ("children", "style", "localStyles") or not isinstance(v, list):
                    continue
                for i, c in enumerate(v):
                    if isinstance(c, dict) and "objID" in c:
                        rec(c, (pre + "_" if pre else "") + "%s%d" % (k.upper(), i))
        elif isinstance(o, list):
            for c in o:
                rec(c, pre)

    rec(node, prefix)
    node["left"] = 0
    node["top"] = 0
    return node


def default_value(tpl):
    d = copy.deepcopy(tpl)

    def strip(o):
        if isinstance(o, dict):
            for k in ("objID", "identifier", "style", "localStyles", "left", "top"):
                o.pop(k, None)
            for v in o.values():
                strip(v)
        elif isinstance(o, list):
            for v in o:
                strip(v)

    strip(d)
    return d


def main():
    proj = json.load(open(PROJ, encoding="utf-8"))
    pages = {p["name"]: p for p in proj["userPages"]}
    os.makedirs(os.path.join(HERE, "templates"), exist_ok=True)
    tpls = {}
    typ2page = {}
    for name in PAGES:
        pg = pages[name]
        w = pg["components"][0]["children"][0]
        tpls[w["type"]] = placeholders(w)
        typ2page[w["type"]] = name

    # Tab 只能作为 Tabview 的子控件存在，从宿主页内提取。
    def find(node, typ):
        if node.get("type") == typ:
            return node
        for c in node.get("children", []):
            hit = find(c, typ)
            if hit:
                return hit

    tab = find(pages["Tabview"]["components"][0], "LVGLTabWidget")
    tpls["LVGLTabWidget"] = placeholders(tab)
    typ2page["LVGLTabWidget"] = "Tabview"

    root = placeholders(pages["Label"]["components"][0])
    root["children"] = []
    tpls["LVGLScreenWidget"] = root
    typ2page["LVGLScreenWidget"] = "Label"

    for typ, t in tpls.items():
        json.dump(t, open(os.path.join(HERE, "templates", typ + ".json"),
                          "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    defaults = {"_meta": {"source": "EEZ Studio UI drag-created project; saved post-drag syntax",
                          "project": os.path.basename(PROJ), "pages": len(proj["userPages"]),
                          "templates": len(tpls)}}
    manifest = {}
    for typ, t in sorted(tpls.items()):
        page = typ2page[typ]
        defaults[typ] = {"page": page, "defaultFlags": t.get("widgetFlags", ""),
                         "defaultValue": default_value(t)}
        manifest[typ] = {"page": page, "file": "templates/%s.json" % typ,
                         "source": "EEZ Studio UI drag-created"}
        palette = {"LVGLTabWidget": "Tab", "LVGLSpanWidget": "Spangroup"}.get(typ, page)
        if typ != "LVGLScreenWidget":
            manifest[typ]["palette"] = palette
    json.dump(defaults, open(os.path.join(HERE, "defaults.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("extracted %d templates from %s" % (len(tpls), os.path.basename(PROJ)))


if __name__ == "__main__":
    main()
