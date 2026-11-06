# -*- coding: utf-8 -*-
"""只读提取：从 EEZ UI 创建并保存的工程读取控件语法，写 templates/defaults/manifest。

不创建、不修改 .eez-project；工程必须由 EEZ Studio 的 UI 新建/拖拽/保存。
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "eez-widget-templates.eez-project")
TYPES = ["Arc", "Bar", "Button", "Chart", "Checkbox", "Container", "Dropdown",
         "Keyboard", "Label", "Led", "List", "Panel", "Roller", "Scale",
         "Slider", "Spinner", "Switch", "Textarea"]


def normalize(node, ident):
    node = copy.deepcopy(node)

    def rec(o):
        if isinstance(o, dict):
            if "objID" in o:
                o["objID"] = "__OBJID__"
            if isinstance(o.get("style"), dict) and "objID" in o["style"]:
                o["style"]["objID"] = "__STYLE_OBJID__"
            if isinstance(o.get("localStyles"), dict) and "objID" in o["localStyles"]:
                o["localStyles"]["objID"] = "__LOCAL_STYLE_OBJID__"
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(node)
    node["left"] = 0
    node["top"] = 0
    node["identifier"] = ident
    return node


def default_value(tpl):
    d = copy.deepcopy(tpl)
    for k in ("objID", "identifier", "style", "localStyles", "left", "top"):
        d.pop(k, None)
    for c in d.get("children", []):
        for k in ("objID", "identifier", "style", "localStyles", "left", "top"):
            c.pop(k, None)
    return d


def main():
    proj = json.load(open(PROJ, encoding="utf-8"))
    pages = {p["name"]: p for p in proj["userPages"]}
    os.makedirs(os.path.join(HERE, "templates"), exist_ok=True)
    tpls = {}
    for name in TYPES:
        pg = pages[name]
        w = pg["components"][0]["children"][0]
        typ = w["type"]
        t = normalize(w, "tpl_" + name.lower())
        if typ == "LVGLButtonWidget":
            for c in t.get("children", []):
                c["identifier"] = "tpl_button_label"
        tpls[typ] = t
    root = normalize(pages["Label"]["components"][0], "tpl_screen")
    root["children"] = []
    tpls["LVGLScreenWidget"] = root

    for typ, t in tpls.items():
        json.dump(t, open(os.path.join(HERE, "templates", typ + ".json"),
                          "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    defaults = {"_meta": {"source": "EEZ Studio UI drag-created project; saved post-drag syntax",
                          "project": os.path.basename(PROJ), "pages": len(proj["userPages"]),
                          "templates": len(tpls)}}
    manifest = {}
    for typ, t in sorted(tpls.items()):
        page = "Label" if typ == "LVGLScreenWidget" else next(
            n for n, p in pages.items()
            if p.get("components") and p["components"][0].get("children")
            and p["components"][0]["children"][0].get("type") == typ)
        defaults[typ] = {"page": page, "defaultFlags": t.get("widgetFlags", ""),
                         "defaultValue": default_value(t)}
        manifest[typ] = {"page": page, "file": "templates/%s.json" % typ,
                         "source": "EEZ Studio UI drag-created"}
    json.dump(defaults, open(os.path.join(HERE, "defaults.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("extracted %d templates from %s" % (len(tpls), os.path.basename(PROJ)))


if __name__ == "__main__":
    main()
