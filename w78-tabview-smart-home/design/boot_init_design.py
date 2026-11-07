# -*- coding: utf-8 -*-
"""开机自检页设计图（800x480 设计，2x 输出 PNG）。

规则（2026-11-07 用户定）：
- 进度条下方只用**一条动态字条**，随当前检测项变化；
- 不允许 "1、2、3、" 这种编号列表；
- 自检项示例：内存 / 显示 / Wi-Fi / 存储 / 完成。

用法：python design/boot_init_design.py
输出：designer_annotated/boot_init_设计图.png
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "designer_annotated", "boot_init_设计图.png")

W, H = 800, 480
S = 2

INK = (238, 244, 252)
SUB = (126, 144, 168)
LINE = (32, 44, 62)
ACCENT = (76, 194, 255)
ACCENT2 = (137, 226, 255)
MUTED = (96, 112, 134)

YH = "C:/Windows/Fonts/msyh.ttc"
YHB = "C:/Windows/Fonts/msyhbd.ttc"


def font(size, bold=False):
    return ImageFont.truetype(YHB if bold else YH, size * S)


def text(d, xy, s, size, color, bold=False, anchor="la", spacing=0):
    f = font(size, bold)
    if spacing:
        x = xy[0] * S
        if anchor[0] == "m":
            total = sum(d.textlength(ch, font=f) for ch in s) + spacing * S * (len(s) - 1)
            x -= total / 2.0
        for ch in s:
            d.text((x, xy[1] * S), ch, font=f, fill=color, anchor="la")
            x += d.textlength(ch, font=f) + spacing * S
    else:
        d.text((xy[0] * S, xy[1] * S), s, font=f, fill=color, anchor=anchor)


def rr(d, box, radius, fill, outline=None, width=0):
    x, y, w, h = [v * S for v in box]
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius * S, fill=fill,
                        outline=outline, width=width * S)


def vgrad(img, top, bottom, y0=0, y1=H):
    d = ImageDraw.Draw(img)
    for yy in range(y0 * S, y1 * S):
        t = (yy - y0 * S) / float((y1 - y0) * S)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, yy), (W * S, yy)], fill=c)


def glow(img, cx, cy, r, color, strength=26):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(10, 0, -1):
        rad = r * i / 10.0
        a = int(strength * (1 - i / 10.0) ** 1.4) + 2
        d.ellipse([(cx * S - rad * S), (cy * S - rad * S),
                   (cx * S + rad * S), (cy * S + rad * S)],
                  fill=color + (a,))
    img.alpha_composite(layer)


def main():
    img = Image.new("RGB", (W * S, H * S + 132 * S), (6, 10, 18)).convert("RGBA")
    vgrad(img, (8, 13, 24), (15, 24, 41))

    d = ImageDraw.Draw(img)
    glow(img, W // 2, 150, 150, (60, 150, 220), 22)
    d = ImageDraw.Draw(img)

    # 顶部：品牌标 + 名称 + 右上版本
    rr(d, (40, 34, 30, 30), 9, ACCENT)
    text(d, (55, 49), "H", 16, (6, 14, 26), True, anchor="mm")
    text(d, (82, 37), "HAVEN HOME", 17, INK, True, spacing=0.6)
    text(d, (82.5, 60), "系统自检", 11, SUB)
    text(d, (W - 40, 40), "v1.0.0", 11, MUTED, anchor="ra")

    # 中央：环形进度（r=88）+ 圆角应用标 + 房子图形
    # 几何与 LVGL/H5 统一：中心 (400,128)，徽标 112×112 @ (344,72)，环 r=88
    ccx, ccy, cr = W // 2, 128, 88
    # 外发光圈（对应 H5 的 stroke-opacity 0.12 / LVGL 的 arc 底）
    ring = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse([(ccx - cr - 2) * S, (ccy - cr - 2) * S,
                (ccx + cr + 2) * S, (ccy + cr + 2) * S],
               outline=(76, 194, 255, 30), width=8 * S)
    img.alpha_composite(ring)
    d = ImageDraw.Draw(img)
    d.ellipse([(ccx - cr) * S, (ccy - cr) * S,
               (ccx + cr) * S, (ccy + cr) * S],
              outline=(42, 59, 82), width=3 * S)
    d.arc([(ccx - cr) * S, (ccy - cr) * S,
           (ccx + cr) * S, (ccy + cr) * S],
          start=-90, end=-90 + int(360 * 0.42), fill=ACCENT, width=3 * S)

    ms = 112
    mx, my = (W - ms) // 2, 72
    rr(d, (mx, my, ms, ms), 28, (22, 38, 62), outline=(58, 104, 146), width=1)
    rr(d, (mx + 1, my + 1, ms - 2, ms // 2), 27, (32, 58, 90))
    cx, cy = mx + ms // 2, my + ms // 2 + 2
    # 屋顶
    d.polygon([((cx) * S, (cy - 26) * S), ((cx - 24) * S, (cy - 4) * S),
               ((cx + 24) * S, (cy - 4) * S)], fill=(240, 247, 255))
    # 墙体
    d.rectangle([(cx - 18) * S, (cy - 4) * S, (cx + 18) * S, (cy + 24) * S],
                fill=(240, 247, 255))
    # 门
    d.rectangle([(cx - 7) * S, (cy + 6) * S, (cx + 7) * S, (cy + 24) * S],
                fill=(30, 52, 82))

    text(d, (W // 2, 222), "系统初始化", 16, INK, True, anchor="ma", spacing=2)
    text(d, (W // 2, 254), "正在检查硬件与网络", 11, SUB, anchor="ma")

    # 进度条（标签 / 条 / 百分比与 LVGL、H5 同坐标）
    bx, by, bw, bh = 140, 300, 520, 8
    text(d, (bx, 284), "自检进度", 10, SUB)
    rr(d, (bx, by, bw, bh), 4, (26, 37, 53))
    fill_w = int(bw * 0.42)
    rr(d, (bx, by, fill_w, bh), 4, ACCENT)
    d.ellipse([(bx + fill_w - 8) * S, (by - 3) * S,
               (bx + fill_w + 2) * S, (by + bh + 3) * S], fill=ACCENT2)
    text(d, (bx + bw, 278), "42%", 12, (176, 197, 220), True, anchor="ra")

    # 状态字条：一个小圆点 + 单行文本（随检测项变化）
    s = "正在检查 Wi-Fi 模块…"
    dx, dy = 304, 338
    d.ellipse([(dx - 4) * S, (dy - 4) * S,
               (dx + 4) * S, (dy + 4) * S], fill=ACCENT)
    text(d, (316, dy), s, 13, (212, 225, 240), anchor="lm")

    # 页脚
    d.line([(40 * S, 432 * S), ((W - 40) * S, 432 * S)], fill=LINE, width=1 * S)
    text(d, (40, 444), "请勿断电", 11, MUTED)
    text(d, (W - 40, 444), "HAVEN HOME", 11, MUTED, anchor="ra")

    # 画布外说明（非 UI）
    y = H + 20
    text(d, (40, y), "动态字条", 12, (150, 170, 192), True)
    text(d, (40, y + 24),
         "正在检查内存…   →   正在检查显示…   →   正在检查 Wi-Fi 模块…   →   正在检查存储…   →   自检完成",
         12, (120, 138, 160))
    text(d, (40, y + 50), "单行显示，只保留当前检测项；禁止编号列表、禁止多项堆叠或换行。",
         11, (92, 108, 128))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.convert("RGB").save(OUT)
    print("[BOOT-DESIGN] %s (%dx%d)" % (OUT, img.width, img.height))


if __name__ == "__main__":
    main()
