# -*- coding: utf-8 -*-
"""compare_shots.py —— ⑤ 双核对的交付图：设计图 vs 仿真出图，逐屏 1:1 并排。

口径：
  * 每屏两格，都是 480×320 的**全分辨率**（缩略网格不算目检，见 memory）；
  * 设计格直接内嵌 design/mockups 的 SVG 源码（矢量，不缩放失真；
    屏幕区 = viewBox "40 40 600 400"，与 annotate.py 同一套取框）；
  * 仿真格内嵌 build/sim_shots 的 PNG（base64，保持单文件自包含）。

用法：python design/compare_shots.py
产物：build/sim_shots/step5_compare.svg
"""
import base64
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOCK = os.path.join(HERE, "mockups")
SHOTS = os.path.join(ROOT, "build", "sim_shots")
OUT = os.path.join(SHOTS, "step5_compare.svg")

try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

CELL_W, CELL_H = 480, 320
GAP_X, GAP_Y = 24, 16
MARGIN, LABEL_H = 20, 30
SCREEN_VIEWBOX = "40 40 600 400"      # mockup 里屏幕区的取框（annotate.py 同源）

# (行标题, 设计图文件, 仿真图文件, 备注)
ROWS = [
    ("列表主态（扫描完成）", "mockup_01_list.svg", "done.png", ""),
    ("扫描中", "mockup_02_scanning.svg", "scanning.png", ""),
    ("空态", "mockup_03_empty.svg", "empty.png",
     "仿真缺「重新扫描」按钮：空态行由 native 画，属 ⑦ 接线范围"),
    ("连接半页（输入密码）", "mockup_04_sheet.svg", "sheet_open.png",
     "由真实点击到达（⑦-1 接线后不再翻 hiddenFlag）"),
    ("长按 -> 忘记确认对话框", "mockup_11_menu.svg", "dialog_open.png",
     "由真实长按到达；「取 消」隐形＝按钮底色与卡片同值（色值漂移，待裁决）"),
]

# 设计图里有、但当前构建到不了的态（依赖 ⑦ 接线 / 真机后端）
NOT_YET = [
    ("mockup_05_sheet_error.svg", "半页错误态", "需要连接失败回显（⑦）"),
    ("mockup_06_connecting.svg", "连接中", "需要连接状态机（⑦）"),
    ("mockup_07_failed.svg", "连接失败", "需要连接状态机（⑦）"),
    ("mockup_09_embedded.svg", "已连接内嵌态", "需要后端上报（⑦）"),
    ("mockup_10_connected.svg", "连接成功", "需要后端上报（⑦）"),
]


def design_svg_text(path):
    """取 mockup 的 <svg> 内层（去掉根标签与 width=100%，由外层统一控框）。"""
    t = io.open(path, encoding="utf-8").read()
    i = t.index(">") + 1
    j = t.rindex("</svg>")
    return t[i:j].strip()


def png_data_uri(path):
    b = io.open(path, "rb").read()
    return "data:image/png;base64," + base64.b64encode(b).decode("ascii")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def main():
    for _t, d, s, _n in ROWS:
        for p in (os.path.join(MOCK, d), os.path.join(SHOTS, s)):
            if not os.path.exists(p):
                sys.stderr.write("缺图：%s\n" % p)
                return 1

    n = len(ROWS)
    W = MARGIN * 2 + CELL_W * 2 + GAP_X
    H = MARGIN * 2 + 46 + n * (LABEL_H + CELL_H + GAP_Y) + 30 + len(NOT_YET) * 22
    out = io.open(OUT, "w", encoding="utf-8", newline="")
    out.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
              'viewBox="0 0 %d %d" font-family="Microsoft YaHei, Segoe UI, sans-serif" '
              'font-size="14">\n' % (W, H, W, H))
    out.write('<rect x="0" y="0" width="%d" height="%d" fill="#F4F5F7"/>\n' % (W, H))
    y = MARGIN
    out.write('<text x="%d" y="%d" font-size="18" font-weight="600" '
              'fill="#15171A">⑤ 双核对 · 仿真出图 vs 设计图（每格 480×320 全分辨率）'
              '</text>\n' % (MARGIN, y + 18))
    y += 46

    for title, dfile, sfile, note in ROWS:
        out.write('<text x="%d" y="%d" font-weight="600" fill="#15171A">%s'
                  '</text>\n' % (MARGIN, y + 16, esc(title)))
        if note:
            out.write('<text x="%d" y="%d" font-size="12" fill="#8A4B00">⚠ %s</text>\n'
                      % (MARGIN + 250, y + 16, esc(note)))
        ty = y + LABEL_H
        x1 = MARGIN
        x2 = MARGIN + CELL_W + GAP_X
        out.write('<text x="%d" y="%d" font-size="12" fill="#5C6A85">设计图 %s</text>\n'
                  % (x1, ty - 4, esc(dfile)))
        out.write('<text x="%d" y="%d" font-size="12" fill="#5C6A85">仿真 %s</text>\n'
                  % (x2, ty - 4, esc(sfile)))
        out.write('<svg x="%d" y="%d" width="%d" height="%d" viewBox="%s" '
                  'preserveAspectRatio="none">%s</svg>\n'
                  % (x1, ty, CELL_W, CELL_H, SCREEN_VIEWBOX,
                     design_svg_text(os.path.join(MOCK, dfile))))
        out.write('<image x="%d" y="%d" width="%d" height="%d" href="%s"/>\n'
                  % (x2, ty, CELL_W, CELL_H,
                     png_data_uri(os.path.join(SHOTS, sfile))))
        out.write('<rect x="%d" y="%d" width="%d" height="%d" fill="none" '
                  'stroke="#C7CEDB"/>\n' % (x2, ty, CELL_W, CELL_H))
        y = ty + CELL_H + GAP_Y

    y += 14
    out.write('<text x="%d" y="%d" font-weight="600" fill="#15171A">'
              '当前构建到不了的态（不猜、不算通过）</text>\n' % (MARGIN, y))
    y += 22
    for dfile, what, why in NOT_YET:
        out.write('<text x="%d" y="%d" font-size="13" fill="#5C6A85">'
                  '%s — %s：%s</text>\n' % (MARGIN + 8, y, esc(what), esc(dfile),
                                            esc(why)))
        y += 22
    out.write("</svg>\n")
    out.close()
    print("written:", OUT, os.path.getsize(OUT), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
