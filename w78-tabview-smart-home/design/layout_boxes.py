# -*- coding: utf-8 -*-
"""导出设计源里的卡片布局框（L6 等距检查的输入）。

卡片由 simple_control.card() 画，带 data-card="1" 标记；本脚本只解析设计帧，
不从 EEZ 工程猜（装饰 rect 在 EEZ 里没有对应控件）。
用法：python design/layout_boxes.py   # 产物：design/layout_boxes.json
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pages as pg                  # noqa: E402

OUT = os.path.join(HERE, "layout_boxes.json")
BOX_RE = re.compile(r'<rect[^>]*data-card="1"[^>]*>')


def attr(tag, name):
    m = re.search(name + r'="([^"]*)"', tag)
    return float(m.group(1)) if m else 0.0


def main():
    out = {}
    for name, frame, _entry, _exit, _rows in pg.PAGES:
        out[name] = [{"x": int(round(attr(t, "x"))), "y": int(round(attr(t, "y"))),
                      "w": int(round(attr(t, "width"))), "h": int(round(attr(t, "height")))}
                     for t in BOX_RE.findall(frame or "")]
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("written %s ｜ 页 %d ｜ 卡片框 %d"
          % (OUT, len(out), sum(len(v) for v in out.values())))


if __name__ == "__main__":
    main()
