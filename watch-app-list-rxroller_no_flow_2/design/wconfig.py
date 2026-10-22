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


_RAW = {}


def _raw_all():
    """把 config 里所有 `#define NAME 值` 收进字典（值原样保留）。"""
    if not _RAW:
        for n, v in re.findall(r"^#define\s+([A-Z_][A-Z0-9_]*)\s+(\S.*?)\s*$",
                               _text(), re.M):
            _RAW[n] = re.sub(r"/\*.*$", "", v).strip()   # 行尾注释切掉
    return _RAW


def _resolve(name, seen=()):
    """把值里的标识符换成同文件里的其它 #define，最后只剩数字和运算符。
    只认数字与 + - * / ( )，其它字符一律拒绝——不把 config 当代码执行。"""
    if name in seen:
        raise ValueError("config 里 %s 循环引用" % name)
    raw = _raw_all()[name].rstrip("\\").strip()
    def sub(m):
        return str(_resolve(m.group(1), seen + (name,)))
    expr = re.sub(r"\b([A-Z_][A-Z0-9_]*)\b", sub, raw)
    if not re.match(r"^[\d\s\(\)\+\-\*/]+$", expr):
        raise ValueError("%s 的值不是纯整数/纯算术式：%r" % (name, raw))
    return int(eval(expr, {"__builtins__": {}}, {}))


def wcfg(name):
    """取一个整型 #define（允许 (256 * PCT / 100) 这种算式）。
    取不到就抛异常——宁可炸，也不要悄悄用默认值。"""
    if name not in _raw_all():
        raise KeyError("%s 不在 %s 里" % (name, CFG_PATH))
    return _resolve(name)


def names():
    return re.findall(r"^#define\s+([A-Z_][A-Z0-9_]*)\b", _text(), re.M)
