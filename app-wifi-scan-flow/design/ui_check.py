#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui_check.py — 把仿真截图与设计图对照，并做像素级居中/位置校验。

产出（默认 design/check/）：
  shot.png      截图（BMP 转 PNG，便于查看）
  overlay.png   截图 + 设计参考线（框 + 中心十字）
  report.html   设计 SVG ｜ 截图 ｜ 叠加图 三栏并排 + 测量表（浏览器打开）

用法（必须用装了 Pillow 的 managed python）：
  python design/ui_check.py
  python design/ui_check.py --shot design/sim_cmake/shot_fake.bmp --spec design/check_spec.json
  python design/ui_check.py --design design/mockups/mockup_01_list.svg

校验规则（spec 里每一项）：
  rect     [x, y, w, h]   设计位置（屏幕坐标系，与设计图同一套常量）
  probe    "bright"       亮度 > threshold 的像素范围 → 求中心
           "text"         近白像素范围 → 求中心（按钮/标签文字）
           "none"         只画参考线，不测量
  tol      允许偏差（像素，默认 4）

退出码：0 全部 PASS；1 有偏差/缺图。
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("FAIL: 当前 python 没有 Pillow。请用 managed python：")
    print(r"  C:\Users\yjt54\.workbuddy\binaries\python\envs\default\Scripts\python.exe design\ui_check.py")
    sys.exit(1)


def load_shot(path, swap_rb=False):
    im = Image.open(path)
    im = im.convert("RGB")
    if swap_rb:                       # P-0008：ARGB8888 内存序是 B,G,R,A
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
    return im


def probe(im, rect, mode, threshold):
    """在 rect 内找亮像素/白像素的包围盒中心。"""
    x, y, w, h = rect
    px = im.load()
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(im.width, x + w), min(im.height, y + h)
    cols, rows = [], []
    for yy in range(y0 + 1, y1 - 1):
        for xx in range(x0 + 1, x1 - 1):
            r, g, b = px[xx, yy]
            ok = (r > 200 and g > 200 and b > 200) if mode == "text" \
                else max(r, g, b) > threshold
            if ok:
                cols.append(xx)
                rows.append(yy)
    if not cols:
        return None
    return ((min(cols) + max(cols)) / 2.0, (min(rows) + max(rows)) / 2.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default=os.path.join(ROOT, "design", "sim_cmake", "shot_fake.bmp"))
    ap.add_argument("--spec", default=os.path.join(ROOT, "design", "check_spec.json"))
    ap.add_argument("--design", default="", help="设计 SVG，放进报告做并排对照")
    ap.add_argument("--out", default=os.path.join(ROOT, "design", "check"))
    ap.add_argument("--swap-rb", action="store_true", help="颜色反常时交换 R/B（P-0008）")
    args = ap.parse_args()

    if not os.path.exists(args.shot):
        print("FAIL: 找不到截图 %s" % args.shot)
        print("      先在 main.c 里用 lv_snapshot 落盘（见 EEZ_WORKFLOW.md 第 5 节）")
        sys.exit(1)

    im = load_shot(args.shot, args.swap_rb)
    os.makedirs(args.out, exist_ok=True)
    shot_png = os.path.join(args.out, "shot.png")
    im.save(shot_png)

    spec = {"screen": [im.width, im.height], "items": []}
    if os.path.exists(args.spec):
        spec = json.load(open(args.spec, encoding="utf-8"))

    ov = im.copy()
    d = ImageDraw.Draw(ov)
    results, fails = [], 0
    for it in spec.get("items", []):
        name, rect = it.get("name", "?"), it.get("rect")
        if not rect:
            continue
        x, y, w, h = rect
        mode = it.get("probe", "none")
        tol = it.get("tol", 4)
        d.rectangle([x, y, x + w, y + h], outline=(108, 230, 156), width=1)
        cx, cy = x + w / 2.0, y + h / 2.0
        d.line([(cx, y - 2), (cx, y + h + 2)], fill=(229, 86, 106), width=1)
        d.line([(x - 2, cy), (x + w + 2, cy)], fill=(229, 86, 106), width=1)

        if mode == "none":
            results.append((name, "—", "—", "—", "仅标注"))
            continue
        c = probe(im, rect, mode, it.get("threshold", 90))
        if c is None:
            results.append((name, "未检出像素", "—", "—", "FAIL"))
            fails += 1
            continue
        dx, dy = c[0] - cx, c[1] - cy
        ok = abs(dx) <= tol and abs(dy) <= tol
        fails += 0 if ok else 1
        results.append((name, "%d,%d" % (c[0], c[1]), "%+.1f" % dx, "%+.1f" % dy,
                        "PASS" if ok else "FAIL(>%d)" % tol))
        d.ellipse([c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2], fill=(255, 210, 90))

    ov_png = os.path.join(args.out, "overlay.png")
    ov.save(ov_png)

    # ---- HTML 报告：设计图 ｜ 截图 ｜ 叠加 ----
    def rel(p):
        return os.path.relpath(p, args.out).replace("\\", "/")

    rows = "\n".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%s</td></tr>"
        % (n, c, dx, dy, "ok" if s.startswith("PASS") or s == "仅标注" else "bad", s)
        for n, c, dx, dy, s in results)

    design_panel = ("<img src='%s'>" % rel(os.path.abspath(args.design))) if args.design \
        else "<div class='hint'>未指定 --design</div>"

    html = """<!doctype html><meta charset="utf-8">
<title>UI 核对 · 设计 vs 实机</title>
<style>
 body{margin:0;background:#0B0F1A;color:#E8EEF9;font:13px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}
 h1{font-size:16px;font-weight:500;margin:16px 20px 4px}
 .sub{color:#8A99B3;margin:0 20px 14px}
 .cols{display:flex;gap:14px;padding:0 20px;align-items:flex-start}
 .card{flex:1;background:#101A28;border:1px solid #26314A;border-radius:10px;padding:10px;min-width:0}
 .card h2{font-size:11px;color:#8A99B3;font-weight:400;margin:0 0 8px}
 .card img{width:100%%;display:block;border-radius:6px}
 table{border-collapse:collapse;margin:16px 20px;width:calc(100%% - 40px)}
 th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #26314A;font-size:12px}
 th{color:#8A99B3;font-weight:400}
 .ok{color:#3DDC97}.bad{color:#E06A6A}
 .hint{color:#5C6A85;padding:40px 0;text-align:center}
</style>
<h1>UI 核对：设计图 vs 仿真截图</h1>
<p class="sub">绿框=设计位置，红线=设计中心，黄点=实测中心；偏差在 tol 内为 PASS</p>
<div class="cols">
  <div class="card"><h2>设计图（SVG）</h2>%s</div>
  <div class="card"><h2>仿真截图</h2><img src="%s"></div>
  <div class="card"><h2>叠加 + 测量</h2><img src="%s"></div>
</div>
<table><tr><th>元素</th><th>实测中心</th><th>Δx</th><th>Δy</th><th>结果</th></tr>%s</table>
""" % (design_panel, rel(shot_png), rel(ov_png), rows)

    rep = os.path.join(args.out, "report.html")
    open(rep, "w", encoding="utf-8").write(html)

    print("截图   :", shot_png)
    print("叠加   :", ov_png)
    print("报告   :", rep)
    for n, c, dx, dy, s in results:
        print("  %-16s 中心 %-12s Δx %-6s Δy %-6s %s" % (n, c, dx, dy, s))
    if fails:
        print("\nFAIL: %d 项超出容差" % fails)
        sys.exit(1)
    print("\nOK: 全部元素在设计位置（±tol）")


if __name__ == "__main__":
    main()
