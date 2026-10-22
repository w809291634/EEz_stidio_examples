# -*- coding: utf-8 -*-
"""wconfig.py —— 读 src/native/watch_list_config.h 里的 #define 值。

应用列表的可调参数只有那一份头文件；gen_assets.py / port_rxroller.py / preflight.py
都从这里取值，避免"改了一处忘另一处"。

    from wconfig import wcfg
    size = wcfg("ICON_PX")            # -> 76（int）
    pct  = wcfg("SCALE_EDGE_PCT")     # -> 59
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(os.path.dirname(HERE), "src", "native",
                        "watch_list_config.h")

_CACHE = {}


def _text():
    if "t" not in _CACHE:
        _CACHE["t"] = io.open(CFG_PATH, encoding="utf-8").read()
    return _CACHE["t"]


def wcfg(name):
    """取一个整型 #define。取不到就抛异常——宁可炸，也不要悄悄用默认值。"""
    m = re.search(r"^#define\s+%s\s+(\d+)\b" % re.escape(name),
                  _text(), re.M)
    if not m:
        raise KeyError("%s 不在 %s 里（或不是纯整数）" % (name, CFG_PATH))
    return int(m.group(1))


def names():
    return re.findall(r"^#define\s+([A-Z_][A-Z0-9_]*)\b", _text(), re.M)
