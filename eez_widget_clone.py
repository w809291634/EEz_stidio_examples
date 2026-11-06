# -*- coding: utf-8 -*-
"""按 eez-widget-templates 标准语法克隆控件（禁止手拼字段）。

模板来自 EEZ Studio UI 拖拽创建并保存后的工程，是控件 JSON 的唯一字段真值：
本模块只做「深拷贝模板 → 换新 objID → 改几何 / identifier / 标志 / 样式 / 子控件 / 事件」，
调用方不得再补模板之外的字段（A14 门禁同口径）。
"""
import copy
import io
import json
import os
import uuid

TPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "eez-widget-templates", "templates")

# 旧语法默认 widgetFlags：只用于把 CLICKABLE 映射到新语法的 clickableFlag
OLD_DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLContainerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SNAPPABLE",
    "LVGLTextareaWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLKeyboardWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLListWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}

_cache = {}


def _child_of(node, wtype):
    """在模板里找第一个指定类型的子控件（深度优先）。"""
    for c in node.get("children") or []:
        if c.get("type") == wtype:
            return c
        found = _child_of(c, wtype)
        if found is not None:
            return found
    return None


def template(name):
    """读模板（只读缓存）。

    name 为 "A"：直接读 `templates/A.json`；
    name 为 "A+B"：取 A 模板里现成的 B 型子控件（如 Button 自带唯一子 Label）；
    A 里没有该子控件时退回 B 的独立模板（如空 Container 里放 Label）。
    """
    if name in _cache:
        return _cache[name]
    if "+" in name:
        parent, child = name.split("+", 1)
        node = _child_of(template(parent), child) or template(child)
    else:
        path = os.path.join(TPL_DIR, name + ".json")
        if not os.path.isfile(path):
            raise KeyError("没有标准模板：%s（先回 eez-widget-templates 用 UI 拖拽保存）" % name)
        node = json.load(io.open(path, encoding="utf-8"))
    _cache[name] = node
    return node


def _fresh_ids(o, id_fn=None):
    """模板里的 __OBJID__ 占位符全部换新：默认随机 UUID；传 id_fn 则按占位符定值。"""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "objID":
                o[k] = id_fn(v) if id_fn else str(uuid.uuid4())
            else:
                _fresh_ids(v, id_fn)
    elif isinstance(o, list):
        for v in o:
            _fresh_ids(v, id_fn)


def clone_dict(obj, id_fn=None):
    """深拷贝任意节点并把 objID 全部换新（模板、设置块通用），不改任何值。"""
    out = copy.deepcopy(obj)
    _fresh_ids(out, id_fn)
    return out


def clone(name, id_fn=None):
    """克隆模板/复合样板（"A" 或 "A+B"），只换 objID，不改值。"""
    return clone_dict(template(name), id_fn)


def new_widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
               children=None, eventHandlers=None, clickable=None, id_fn=None,
               **extra):
    """克隆模板后只改值。

    flags 传旧语法 flags：None=沿用模板默认；显式=按给定值（去掉 CLICKABLE）。
    clickable=None 时按 flags 是否含 CLICKABLE 推导；带事件回调的控件视为可点击。
    """
    wd = clone(wtype, id_fn)
    wd["left"], wd["top"], wd["width"], wd["height"] = x, y, w, h
    for k in ("leftUnit", "topUnit", "widthUnit", "heightUnit"):
        wd[k] = "px"
    if identifier:
        wd["identifier"] = identifier

    if flags is not None:
        wd["widgetFlags"] = "|".join(
            p for p in flags.split("|") if p and p != "CLICKABLE")
    if clickable is None and (flags is not None or wtype in OLD_DEFAULT_FLAGS
                              or eventHandlers):
        if eventHandlers:
            clickable = True
        else:
            src = flags if flags is not None else OLD_DEFAULT_FLAGS[wtype]
            clickable = "CLICKABLE" in src.split("|")
    if clickable is not None and ("clickableFlag" in wd or clickable):
        wd["clickableFlag"] = bool(clickable)

    if local is not None:
        wd["localStyles"]["definition"] = local
    if children is not None:
        wd["children"] = children
    if eventHandlers is not None:
        wd["eventHandlers"] = eventHandlers
        _fresh_ids(wd["eventHandlers"], id_fn)
    wd.update(extra)
    return wd
