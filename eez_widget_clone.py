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


def template(wtype):
    """读模板（只读缓存）。"""
    if wtype not in _cache:
        path = os.path.join(TPL_DIR, wtype + ".json")
        if not os.path.isfile(path):
            raise KeyError("没有标准模板：%s（先回 eez-widget-templates 用 UI 拖拽保存）" % wtype)
        _cache[wtype] = json.load(io.open(path, encoding="utf-8"))
    return _cache[wtype]


def _fresh_ids(o):
    """模板里的 __OBJID__ 占位符全部换成新 UUID（含子控件/样式/事件）。"""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "objID":
                o[k] = str(uuid.uuid4())
            else:
                _fresh_ids(v)
    elif isinstance(o, list):
        for v in o:
            _fresh_ids(v)


def new_widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
               children=None, eventHandlers=None, clickable=None, **extra):
    """克隆模板后只改值。

    flags 传旧语法 flags：None=沿用模板默认；显式=按给定值（去掉 CLICKABLE）。
    clickable=None 时按 flags 是否含 CLICKABLE 推导；带事件回调的控件视为可点击。
    """
    wd = copy.deepcopy(template(wtype))
    _fresh_ids(wd)
    wd["left"], wd["top"], wd["width"], wd["height"] = x, y, w, h
    for k in ("leftUnit", "topUnit", "widthUnit", "heightUnit"):
        wd[k] = "px"
    if identifier:
        wd["identifier"] = identifier

    old_flags = flags if flags is not None else OLD_DEFAULT_FLAGS.get(wtype, "")
    if flags is not None:
        wd["widgetFlags"] = "|".join(
            p for p in flags.split("|") if p and p != "CLICKABLE")
    if clickable is None:
        clickable = "CLICKABLE" in old_flags.split("|") or bool(eventHandlers)
    if "clickableFlag" in wd or clickable:
        wd["clickableFlag"] = bool(clickable)

    if local is not None:
        wd["localStyles"]["definition"] = local
    if children is not None:
        wd["children"] = children
    if eventHandlers is not None:
        wd["eventHandlers"] = eventHandlers
        _fresh_ids(wd["eventHandlers"])
    wd.update(extra)
    return wd
