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
        elif isinstance(o, list):
            for c in o:
                rec(c, pre)

    rec(node, prefix)
    node["left"] = 0
    node["top"] = 0
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
        tpls[w["type"]] = placeholders(w)
    root = placeholders(pages["Label"]["components"][0])
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
