#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_chars.py —— 逐字审计：UI 全部文案字符 vs 字体字符集（保证一字不少）。

遍历 .eez-project 的控件 text/placeholder + 表达式里的字符串字面量，
收集全部非 ASCII 字符，与 build_example.py 的 FONT_CHARS（+ ASCII 打印区）
比对，列出未覆盖字符。★ 字体新增/修改文案后必跑。

用法：python design/audit_chars.py   （无输出缺字 = 通过）
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import build_example as be

PROJ = os.path.join(ROOT, os.path.basename(be.PROJECT_FILE))
proj = json.load(open(PROJ, encoding="utf-8"))

ui_chars = set()
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("text", "placeholder") and isinstance(v, str):
                ui_chars.update(v)
            if k == "hiddenFlag" and isinstance(v, str) and \
                    o.get("hiddenFlagType") == "expression":
                for lit in re.findall(r'"([^"]*)"', v):
                    ui_chars.update(lit)
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(proj["userPages"])
# textType=expression 的 label 文本里的字面量
def walk2(o):
    if isinstance(o, dict):
        if o.get("type") == "LVGLLabelWidget" and o.get("textType") == "expression":
            for lit in re.findall(r'"([^"]*)"', o.get("text", "")):
                ui_chars.update(lit)
        for v in o.values(): walk2(v)
    elif isinstance(o, list):
        for v in o: walk2(v)
walk2(proj["userPages"])

FONT_CHARS = getattr(be, "FONT_CHARS", None)
non_ascii = [c for c in ui_chars if ord(c) > 0x7E]
if FONT_CHARS is None:
    # 模板工程（还没有字体）：无文案就放行；一旦有中文却说不出字符集，必须报错，
    # 不能"跳过=通过"（P-0012）。
    if non_ascii:
        print("FAIL: 工程有 %d 个非 ASCII 文案，但 build_example 未定义 FONT_CHARS"
              % len(non_ascii))
        print("      先定义 FONT_CHARS（字体字符集），再跑本审计")
        sys.exit(1)
    print("OK: 模板工程无文案（未定义 FONT_CHARS，未做字符比对）")
    sys.exit(0)

covered = set(FONT_CHARS) | {chr(c) for c in range(0x20, 0x7F)}
missing = sorted(c for c in ui_chars if ord(c) > 0x7E and c not in covered)
priv = sorted(c for c in ui_chars if 0xE000 <= ord(c) <= 0xF8FF)
print("UI 非 ASCII 字符数:", len([c for c in ui_chars if ord(c) > 0x7E]))
if missing:
    print("★ 字体未覆盖:", "".join(missing),
          "码位:", " ".join("U+%04X" % ord(c) for c in missing))
    sys.exit(1)
if priv:
    print("★ 私有区字符（需图标字体，否则豆腐）:",
          " ".join("U+%04X" % ord(c) for c in priv))
    sys.exit(2)
print("OK: 每一个文字都在字体字符集内")
