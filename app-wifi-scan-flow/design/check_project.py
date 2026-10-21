#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_project.py — 项目静态自检（交付前必跑；P-0164 防再犯清单的机器落地）。

检查项（每项都对应一次真实事故，见 KB P-0164）：
  1 变量引用审计   EEZ 表达式里引用的标识符必须 ∈ 全局变量/控件 identifier
                   （抓"变量改名漏改表达式"→ is neither input or global）
  2 字符集 ⊆ 字体  UI 文案（JSON + C 渲染源）字符 vs 字体字符集逐字比对
                   （抓"方框/豆腐"——含 placeholder、表达式字面量、C 渲染字符串）
  3 字体条目形态   renderingEngine/lvglRanges/lvglGlyphs/glyphs[] 四要点
                   （P-0125：形态错 = 画布永远豆腐）
  4 字符集 ⊆ TTF   字符集必须被字体源 TTF 的 cmap 覆盖
                   （抓"extraction failed: doesn't have any characters in range"）
  5 native_vars 桥 extern "C"（漏了 → C 侧链接 undefined reference）
  6 C 头注释提前闭合（注释里写 xxx_*/ 的 `*/` 序列）
  7 demo 无守卫退出（main.c 的 exit(0) 必须在 WIFI_AUTOEXIT 条件保护下）

用法（managed python，需 fontTools）：
  C:\\Users\\yjt54\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe design/check_project.py
全部通过打印 OK；任何 FAIL 退出码 1。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import build_example as be            # FONT_CHARS / PROJECT_FILE

PROJ = os.path.join(ROOT, os.path.basename(be.PROJECT_FILE))
fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL:", msg)


# ---------- 载入工程 ----------
proj = json.load(open(PROJ, encoding="utf-8"))
var_names = {v["name"] for v in proj["variables"]["globalVariables"]}
action_names = {a["name"] for a in proj.get("actions", [])}

# 控件 identifier（表达式可引用 objects.xxx，但表达式里不允许直接引用）
obj_ids = set()
def walk_ids(o):
    if isinstance(o, dict):
        if "identifier" in o and "type" in o:
            obj_ids.add(o["identifier"])
        for v in o.values(): walk_ids(v)
    elif isinstance(o, list):
        for v in o: walk_ids(v)
walk_ids(proj["userPages"])

# EEZ flow 表达式的合法标识符白名单（按需扩充）
KNOWN = var_names | action_names | {
    "true", "false", "null", "Event",
}

# ---------- 1 变量引用审计 ----------
exprs = []
def walk_expr(o):
    if isinstance(o, dict):
        if o.get("textType") == "expression" and isinstance(o.get("text"), str):
            exprs.append(("text", o.get("identifier", "?"), o["text"]))
        if o.get("hiddenFlagType") == "expression" and isinstance(o.get("hiddenFlag"), str):
            exprs.append(("hiddenFlag", o.get("identifier", "?"), o["hiddenFlag"]))
        for v in o.values(): walk_expr(v)
    elif isinstance(o, list):
        for v in o: walk_expr(v)
walk_expr(proj["userPages"])

tok_re = re.compile(r"(?<![\w.])()([A-Za-z_]\w*)")
unknown = {}
for kind, ident, expr in exprs:
    body = re.sub(r'"[^"]*"', '""', expr)          # 字符串字面量剔除
    for m in re.finditer(r"(?<![\w.])\s*([A-Za-z_]\w*)", body):
        tok = m.group(1)
        if tok in ("", ) or tok in KNOWN:
            continue
        # 剥掉字面量后剩下的裸标识符
        stripped = re.sub(r'"[^"]*"', '', expr)
        if not re.search(r"(?<![\w.])%s(?!\w)" % re.escape(tok), stripped):
            continue
        if tok not in KNOWN:
            unknown.setdefault(tok, []).append("%s(%s)" % (kind, ident))
if unknown:
    for tok, where in unknown.items():
        fail("表达式引用未知标识符 '%s' @ %s（变量改名漏改？）"
             % (tok, ", ".join(where[:3])))

# ---------- 2/4 字符集审计（JSON 文案 + C 渲染字符串）----------
ui_chars = set()
def walk_chars(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("text", "placeholder") and isinstance(v, str):
                ui_chars.update(v)
            if k == "hiddenFlag" and isinstance(v, str) and \
                    o.get("hiddenFlagType") == "expression":
                for lit in re.findall(r'"([^"]*)"', v):
                    ui_chars.update(lit)
            walk_chars(v)
    elif isinstance(o, list):
        for v in o: walk_chars(v)
walk_chars(proj["userPages"])

# C 渲染字符串（wifi_ui_sync / native_actions 等写死的显示文案）
c_render = ""
for fn in ("wifi_ui_sync.cpp", "native_actions.cpp", "main.c"):
    p = os.path.join(ROOT, "src", "native", fn)
    if fn == "main.c":
        p = os.path.join(ROOT, "design", "sim_cmake", "main.c")
    if not os.path.exists(p):
        continue
    src = open(p, encoding="utf-8", errors="replace").read()
    for lit in re.findall(r'lv_label_set_text\(\w+,\s*"([^"]*)"', src):
        c_render += lit
    for lit in re.findall(r'lv_label_set_text_fmt\(\w+,\s*"([^"]*)"', src):
        c_render += lit
for c in c_render:
    if ord(c) > 0x7E:
        ui_chars.add(c)

covered = set(be.FONT_CHARS) | {chr(c) for c in range(0x20, 0x7F)}
missing = sorted(c for c in ui_chars if ord(c) > 0x7E and c not in covered)
priv = sorted(c for c in ui_chars if 0xE000 <= ord(c) <= 0xF8FF)
if missing:
    fail("字体未覆盖字符: %s (%s)"
         % ("".join(missing), " ".join("U+%04X" % ord(c) for c in missing)))
if priv:
    fail("私有区字符（需图标字体）: %s"
         % " ".join("U+%04X" % ord(c) for c in priv))

# ---------- 3 字体条目形态 ----------
fentry = proj["fonts"][0]
for k, want in [("renderingEngine", "LVGL"), ("lvglSymbols", ""),
                ("glyphs", [])]:
    if fentry.get(k) != want:
        fail("字体条目形态: %s 应为 %r（P-0125 四要点）" % (k, want))
if not fentry.get("lvglRanges") or not fentry.get("lvglGlyphs", {}).get("encodings"):
    fail("字体条目形态: lvglRanges/lvglGlyphs.encodings 缺失")

# ---------- 4 字符集 ⊆ TTF cmap ----------
try:
    from fontTools.ttLib import TTFont
    tf = TTFont(os.path.join(ROOT, fentry["source"]["filePath"]), lazy=True)
    cmap = set(tf.getBestCmap().keys())
    tf.close()
    out = sorted(c for c in ui_chars if ord(c) > 0x7E and ord(c) not in cmap)
    if out:
        fail("字符集含 TTF 没有的字（GUI extraction failed 必现）: %s" % "".join(out))
except ImportError:
    print("SKIP: fontTools 不可用（检查 4 跳过）——请用 managed python")

# ---------- 5 native_vars.h extern "C" ----------
nv = os.path.join(ROOT, "src", "native", "native_vars.h")
if os.path.exists(nv) and 'extern "C"' not in open(nv, encoding="utf-8").read():
    fail("native_vars.h 缺 extern \"C\"（C 侧链接必炸）")

# ---------- 6 C 头注释提前闭合（xxx_*/ 模式）----------
for fn in ("app_model.h", "app_model.cpp", "native_vars.h", "wifi_ui_sync.h",
           "platform/io_iface.h"):
    p = os.path.join(ROOT, "src", "native", fn)
    if not os.path.exists(p):
        continue
    src = open(p, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"\w\*/", src):
        line = src[:m.start()].count("\n") + 1
        fail("注释提前闭合风险: %s:%d 含 `_*/` 序列（改为 xxx_yyy 无星号写法）"
             % (fn, line))
        break

# ---------- 7 demo 无守卫退出 ----------
mc = os.path.join(ROOT, "design", "sim_cmake", "main.c")
src = open(mc, encoding="utf-8", errors="replace").read()
lines = src.splitlines()
for i, line in enumerate(lines):
    if "exit(0)" in line or "exit(1)" in line:
        ctx = "\n".join(lines[max(0, i - 6):i + 1])
        if "WIFI_AUTOEXIT" not in ctx and "WIFI_AUTOEXIT" not in line:
            fail("main.c:%d 有无守卫的 exit()（真模式会'一点就退出'）" % (i + 1))

# ---------- 汇总 ----------
if fails:
    print("\n==== 自检 FAIL: %d 项 ====" % len(fails))
    sys.exit(1)
print("OK: 全部静态自检通过（变量引用/字符集/字体条目/extern C/注释/退出守卫）")
