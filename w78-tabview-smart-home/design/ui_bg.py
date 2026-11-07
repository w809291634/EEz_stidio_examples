# -*- coding: utf-8 -*-
"""固定背景图（运行期 400×240，拉伸到 800×480）。

视觉：深色网格渐变（mesh gradient）+ 一条很淡的光带 + 细颗粒，避免纯色单调和色带。
为什么先画 800×480 再缩到 400×240：
  - 高分辨率下做模糊/颗粒更自然，缩小后自带抗锯齿；
  - 运行时解码 400×240 只需约 384KB，避免 1.5MB 整屏缓冲。

用法：python design/ui_bg.py
输出：assets/ui_bg.png（400×240）
"""
import math
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "ui_bg.png")

W, H = 800, 480          # 内部渲染尺寸
OW, OH = 400, 240        # 最终输出（运行期拉伸 2x）

TOP = (5, 7, 13)
BOTTOM = (10, 16, 28)


def base_gradient():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / float(H - 1)
        c = tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    return img


def blob(img, cx, cy, radius, color, strength):
    """柔和色块（additive），模拟 mesh gradient 的一个节点。"""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 70
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = strength * (1 - i / steps) ** 1.9
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=tuple(int(c * a) for c in color))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.22))
    return ImageChops.add(img, layer)


def ribbon(img):
    """一条斜穿画面的极淡光带，增加层次但不过分抢眼。"""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = []
    for i in range(81):
        t = i / 80.0
        x = -80 + (W + 160) * t
        y = H * 0.72 - H * 0.42 * math.sin(t * math.pi * 0.85)
        pts.append((x, y))
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=(22, 58, 104), width=54)
    layer = layer.filter(ImageFilter.GaussianBlur(70))
    return ImageChops.add(img, layer)


def grain(img, amp=3):
    """细颗粒：压住渐变色带，放大后更有质感。"""
    arr = np.asarray(img).astype(np.int16)
    rng = np.random.default_rng(20261107)
    noise = rng.integers(-amp, amp + 1, arr.shape[:2], endpoint=True)[..., None]
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def vignette(img, edge=0.78):
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    steps = 48
    for i in range(steps):
        t = i / float(steps - 1)
        box = [-W * 0.08 + (W * 0.58) * t, -H * 0.08 + (H * 0.58) * t,
               W * 1.08 - (W * 0.58) * t, H * 1.08 - (H * 0.58) * t]
        d.ellipse(box, fill=int(255 * (edge + (1 - edge) * t)))
    mask = mask.filter(ImageFilter.GaussianBlur(80))
    return Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), mask)


def main():
    img = base_gradient()
    # 四个 mesh 节点：右上青 / 左上靛 / 右下蓝绿 / 左下暖
    img = blob(img, 700, 40, 360, (24, 110, 180), 0.50)
    img = blob(img, 110, 90, 300, (78, 58, 160), 0.34)
    img = blob(img, 660, 430, 320, (18, 150, 140), 0.24)
    img = blob(img, 60, 420, 280, (150, 92, 38), 0.26)
    img = ribbon(img)
    img = vignette(img)
    img = grain(img, 3)
    img = img.resize((OW, OH), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("[UI_BG] %s (%dx%d, %.1f KB)" % (OUT, OW, OH, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
