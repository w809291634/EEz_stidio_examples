#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""gen_font.py —— 烘中文字体 .c（P-0140：EEZ CLI 不烘字体，GUI Build 才烘；
纯 CLI 工作流在每次 CLI 构建之后跑本脚本补齐）。

产物：src/ui/fonts/ui_font_cn14.c（lv_font_conv，bpp4，14px，
字符集 = build_example.py 的 FONT_CHARS + ASCII 可打印区）。

用法：python design/gen_font.py    （在每次 EEZ CLI 构建之后运行）
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import build_example as be  # 复用 FONT_CHARS / FONT_NAME

OUT_DIR = os.path.join(ROOT, "src", "ui", "fonts")
FONT_SRC = os.path.join(ROOT, be.FONT_FILE)   # 全量黑体（含全部所需字形）
# symbols 只传非 ASCII 字符：ASCII 已由 -r 0x20-0x7E 覆盖，且 <>&| 等若进
# --symbols 会被批处理解释器的元字符解析炸掉（.cmd 经解释器 /c 执行）
SYMBOLS = "".join(c for c in be.FONT_CHARS if ord(c) > 0x7E)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "ui_font_%s.c" % be.FONT_NAME)
    cmd = [
        "npx", "--yes", "lv_font_conv",
        "--no-compress", "--bpp", "4", "--size", "14",
        "--font", FONT_SRC,
        "-r", "0x20-0x7E",
        "--symbols", SYMBOLS,
        "--format", "lvgl",
        "--lv-font-name", "ui_font_%s" % be.FONT_NAME,
        "-o", out,
    ]
    print("baking:", " ".join(cmd[:8]), "...")
    cmd[0] = shutil.which("npx") or cmd[0]   # 解析 npx 批处理全路径
    r = subprocess.call(cmd, shell=False)    # 禁 shell：防元字符注入
    if r != 0 or not os.path.exists(out):
        print("FAILED (exit %d)" % r)
        sys.exit(1)
    print("written: %s (%d bytes)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
