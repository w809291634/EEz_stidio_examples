# -*- coding: utf-8 -*-
"""icons_art.py —— 应用图标的矢量画法（只画图标，不碰任何其它东西）

把图标从"圆角方 + 汉字首字"换成"正圆 + 白色矢量符号"。
为了让"图标"是唯一变量，画布与留白保持与旧版逐像素一致：

  旧版画的是 rounded_rectangle((inset, inset, size-1-inset, size-1-inset))，
  半边长 = (size-1-2*inset)/2，留 4px 透明边（避免相邻行糊在一起）。
  这里把圆塞进同一个方框，其余不动。

符号一律"先量包围盒、再搬正到圆心"：绘制器里的坐标是按手感写的相对值，
包围盒中心不在原点（音符偏右、月牙偏左上），不搬正就会看着歪。
"""
import math

from PIL import Image, ImageDraw

# ---- 符号占比 ----
FILL_RATIO = 0.36               # 符号半宽基准（相对内容边长）
LIMIT_RATIO = 0.74              # 符号最远角最多占半径的 74%


def _hex(c):
    return c if c.startswith("#") else "#" + c


def _pt(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


# ===========================================================================
# 符号绘制器：画在 (x, y)、半宽 s，col=符号色，bg=底色（挖洞用）
# ===========================================================================
def g_bolt(d, x, y, s, col, bg):
    d.polygon([(x + .15 * s, y - 1.05 * s), (x - .65 * s, y + .12 * s),
               (x - .05 * s, y + .12 * s), (x - .2 * s, y + 1.05 * s),
               (x + .7 * s, y - .18 * s), (x + .05 * s, y - .18 * s)], fill=col)


def g_heart(d, x, y, s, col, bg):
    r = s * 0.38
    cy = y - s * 0.4
    d.ellipse([x - s * 0.5 - r, cy - r, x - s * 0.5 + r, cy + r], fill=col)
    d.ellipse([x + s * 0.5 - r, cy - r, x + s * 0.5 + r, cy + r], fill=col)
    d.polygon([(x - s * 0.88, cy + r * 0.35), (x + s * 0.88, cy + r * 0.35),
               (x, y + s * 1.0)], fill=col)


def g_moon(d, x, y, s, col, bg):
    d.ellipse([x - s, y - s, x + s, y + s], fill=col)
    d.ellipse([x - s * 0.35, y - s * 1.15, x + s * 1.25, y + s * 0.45], fill=bg)


def g_sun(d, x, y, s, col, bg):
    r = s * 0.5
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for i in range(8):
        a = i * 45
        x1, y1 = _pt(x, y, r + s * 0.22, a)
        x2, y2 = _pt(x, y, r + s * 0.62, a)
        d.line([x1, y1, x2, y2], fill=col, width=max(int(s * 0.14), 2))


def g_suncloud(d, x, y, s, col, bg):
    r = s * 0.52
    d.ellipse([x - s * 0.95 - r, y - s * 0.75 - r, x - s * 0.95 + r,
               y - s * 0.75 + r], fill="#FFD510")
    d.ellipse([x - s * 0.62, y - s * 0.18, x + s * 0.06, y + s * 0.5], fill=col)
    d.ellipse([x - s * 0.12, y - s * 0.42, x + s * 0.62, y + s * 0.34], fill=col)
    d.rounded_rectangle([x - s * 0.62, y + s * 0.06, x + s * 0.62, y + s * 0.5],
                        radius=s * 0.22, fill=col)


def g_chat(d, x, y, s, col, bg):
    d.rounded_rectangle([x - s, y - s * 0.85, x + s, y + s * 0.55],
                        radius=s * 0.5, fill=col)
    d.polygon([(x - s * 0.55, y + s * 0.35), (x - s * 0.15, y + s * 0.45),
               (x - s * 0.62, y + s * 1.0)], fill=col)


def g_music(d, x, y, s, col, bg):
    w = max(int(s * 0.16), 2)
    d.line([x - s * 0.35, y + s * 0.5, x - s * 0.35, y - s * 0.75], fill=col, width=w)
    d.line([x + s * 0.65, y + s * 0.25, x + s * 0.65, y - s * 0.95], fill=col, width=w)
    d.polygon([(x - s * 0.35, y - s * 0.75), (x + s * 0.65, y - s * 0.95),
               (x + s * 0.65, y - s * 0.55), (x - s * 0.35, y - s * 0.35)], fill=col)
    d.ellipse([x - s * 0.75, y + s * 0.25, x - s * 0.1, y + s * 0.75], fill=col)
    d.ellipse([x + s * 0.25, y, x + s * 0.9, y + s * 0.5], fill=col)


def g_bell(d, x, y, s, col, bg):
    r = s * 0.85
    d.pieslice([x - r, y - r, x + r, y + r], 180, 360, fill=col)
    d.polygon([(x - r, y), (x + r, y), (x + r * 1.15, y + s * 0.6),
               (x - r * 1.15, y + s * 0.6)], fill=col)
    d.ellipse([x - s * 0.12, y - s * 1.15, x + s * 0.12, y - s * 0.85], fill=col)
    d.ellipse([x - s * 0.2, y + s * 0.72, x + s * 0.2, y + s * 1.12], fill=col)


def g_stopwatch(d, x, y, s, col, bg):
    w = max(int(s * 0.13), 2)
    d.ellipse([x - s * 0.85, y - s * 0.75, x + s * 0.85, y + s * 0.95],
              outline=col, width=w)
    d.rectangle([x - s * 0.18, y - s * 1.1, x + s * 0.18, y - s * 0.78], fill=col)
    d.line([x, y + s * 0.1, x, y - s * 0.5], fill=col, width=w)
    d.line([x, y + s * 0.1, x + s * 0.42, y + s * 0.1], fill=col, width=w)


def g_hourglass(d, x, y, s, col, bg):
    w = max(int(s * 0.13), 2)
    d.line([x - s * 0.7, y - s * 0.95, x + s * 0.7, y - s * 0.95], fill=col, width=w)
    d.line([x - s * 0.7, y + s * 0.95, x + s * 0.7, y + s * 0.95], fill=col, width=w)
    d.polygon([(x - s * 0.55, y - s * 0.8), (x + s * 0.55, y - s * 0.8),
               (x, y + s * 0.05)], outline=col, width=w)
    d.polygon([(x - s * 0.55, y + s * 0.68), (x + s * 0.55, y + s * 0.68),
               (x, y - s * 0.08)], outline=col, width=w)


def g_calc(d, x, y, s, col, bg):
    w = max(int(s * 0.1), 2)
    d.rounded_rectangle([x - s * 0.8, y - s, x + s * 0.8, y + s], radius=s * 0.2,
                        outline=col, width=w)
    d.rectangle([x - s * 0.55, y - s * 0.75, x + s * 0.55, y - s * 0.35], fill=col)
    for r in range(2):
        for c in range(3):
            cx = x - s * 0.45 + c * s * 0.45
            cy = y + s * 0.1 + r * s * 0.45
            d.ellipse([cx - s * 0.09, cy - s * 0.09, cx + s * 0.09, cy + s * 0.09],
                      fill=col)


def g_compass(d, x, y, s, col, bg):
    w = max(int(s * 0.1), 2)
    d.ellipse([x - s, y - s, x + s, y + s], outline=col, width=w)
    d.polygon([(x, y - s * 0.72), (x + s * 0.28, y), (x - s * 0.28, y)], fill=col)
    d.polygon([(x, y + s * 0.72), (x + s * 0.28, y), (x - s * 0.28, y)],
              outline=col, width=w)


def g_phone(d, x, y, s, col, bg):
    w = max(int(s * 0.11), 2)
    d.rounded_rectangle([x - s * 0.55, y - s * 0.95, x + s * 0.3, y + s * 0.95],
                        radius=s * 0.18, outline=col, width=w)
    for rr in (0.45, 0.8):
        d.arc([x + s * 0.35 - rr * s, y - s * 0.95 - rr * s + s * 0.2,
               x + s * 0.35 + rr * s, y - s * 0.95 + rr * s + s * 0.2],
              0, 90, fill=col, width=w)


def g_gear(d, x, y, s, col, bg):
    r1, r2 = s * 0.62, s * 0.95
    d.ellipse([x - r1, y - r1, x + r1, y + r1], fill=col)
    for i in range(8):
        a = i * 45
        x1, y1 = _pt(x, y, r1 * 0.9, a)
        x2, y2 = _pt(x, y, r2, a)
        d.line([x1, y1, x2, y2], fill=col, width=max(int(s * 0.28), 3))
    d.ellipse([x - s * 0.3, y - s * 0.3, x + s * 0.3, y + s * 0.3], fill=bg)


def g_runner(d, x, y, s, col, bg):
    w, a = max(s * 0.26, 3), max(s * 0.19, 2)
    d.ellipse([x + s * 0.05, y - s * 1.1, x + s * 0.55, y - s * 0.6], fill=col)
    d.line([x + s * 0.28, y - s * 0.52, x - s * 0.02, y + s * 0.08], fill=col, width=w)
    d.line([x + s * 0.18, y - s * 0.38, x - s * 0.42, y - s * 0.55], fill=col, width=a)
    d.line([x + s * 0.22, y - s * 0.44, x + s * 0.68, y - s * 0.16], fill=col, width=a)
    d.line([x - s * 0.02, y + s * 0.08, x - s * 0.45, y + s * 0.42], fill=col, width=w)
    d.line([x - s * 0.45, y + s * 0.42, x - s * 0.55, y + s * 0.98], fill=col, width=a)
    d.line([x - s * 0.02, y + s * 0.08, x + s * 0.45, y + s * 0.34], fill=col, width=w)
    d.line([x + s * 0.45, y + s * 0.34, x + s * 0.62, y + s * 0.9], fill=col, width=a)


# ---- 22 行表里"已确认那版没有"的应用：先给最近似的形状，标了临时 ----
def g_calendar(d, x, y, s, col, bg):
    w = max(int(s * 0.12), 2)
    d.rounded_rectangle([x - s * 0.85, y - s * 0.8, x + s * 0.85, y + s * 0.9],
                        radius=s * 0.16, outline=col, width=w)
    d.rectangle([x - s * 0.85, y - s * 0.8, x + s * 0.85, y - s * 0.3], fill=col)
    for r in range(2):
        for c in range(3):
            cx = x - s * 0.5 + c * s * 0.5
            cy = y + s * 0.05 + r * s * 0.42
            d.ellipse([cx - s * 0.09, cy - s * 0.09, cx + s * 0.09, cy + s * 0.09],
                      fill=col)


def g_camera(d, x, y, s, col, bg):
    w = max(int(s * 0.12), 2)
    d.rounded_rectangle([x - s, y - s * 0.55, x + s, y + s * 0.85],
                        radius=s * 0.22, outline=col, width=w)
    d.polygon([(x - s * 0.4, y - s * 0.55), (x - s * 0.25, y - s * 0.9),
               (x + s * 0.25, y - s * 0.9), (x + s * 0.4, y - s * 0.55)], fill=col)
    d.ellipse([x - s * 0.38, y - s * 0.18, x + s * 0.38, y + s * 0.58],
              outline=col, width=w)


def g_footprint(d, x, y, s, col, bg):
    d.ellipse([x - s * 0.55, y - s * 0.9, x + s * 0.05, y + s * 0.35], fill=col)
    d.ellipse([x - s * 0.62, y + s * 0.45, x - s * 0.02, y + s * 1.0], fill=col)
    d.ellipse([x + s * 0.15, y - s * 0.35, x + s * 0.7, y + s * 0.9], fill=col)


def g_wave(d, x, y, s, col, bg):
    w = max(int(s * 0.16), 2)
    d.line([x - s, y, x - s * 0.55, y], fill=col, width=w)
    d.line([x - s * 0.55, y, x - s * 0.3, y - s * 0.8], fill=col, width=w)
    d.line([x - s * 0.3, y - s * 0.8, x - s * 0.05, y + s * 0.7], fill=col, width=w)
    d.line([x - s * 0.05, y + s * 0.7, x + s * 0.2, y - s * 0.35], fill=col, width=w)
    d.line([x + s * 0.2, y - s * 0.35, x + s * 0.45, y], fill=col, width=w)
    d.line([x + s * 0.45, y, x + s, y], fill=col, width=w)


def g_drop(d, x, y, s, col, bg):
    d.polygon([(x, y - s), (x + s * 0.72, y + s * 0.15), (x - s * 0.72, y + s * 0.15)],
              fill=col)
    d.ellipse([x - s * 0.72, y + s * 0.15 - s * 0.72, x + s * 0.72,
               y + s * 0.15 + s * 0.72], fill=col)


def g_rings(d, x, y, s, col, bg):
    for rr in (0.95, 0.62, 0.3):
        d.ellipse([x - s * rr, y - s * rr, x + s * rr, y + s * rr],
                  outline=col, width=max(int(s * 0.24), 2))


def g_gauge(d, x, y, s, col, bg):
    w = max(int(s * 0.14), 2)
    d.arc([x - s * 0.9, y - s * 0.9, x + s * 0.9, y + s * 0.9], 150, 30,
          fill=col, width=w)
    d.line([x, y, x + s * 0.55, y - s * 0.5], fill=col, width=w)
    d.ellipse([x - s * 0.14, y - s * 0.14, x + s * 0.14, y + s * 0.14], fill=col)


def g_hand(d, x, y, s, col, bg):
    w = max(int(s * 0.14), 2)
    d.rounded_rectangle([x - s * 0.45, y - s * 0.9, x + s * 0.45, y + s * 0.55],
                        radius=s * 0.3, outline=col, width=w)
    d.line([x - s * 0.15, y + s * 0.55, x - s * 0.5, y + s * 1.0], fill=col, width=w)
    d.arc([x - s * 0.2, y - s * 1.4, x + s * 0.8, y - s * 0.4], 270, 360,
          fill=col, width=w)


def g_display(d, x, y, s, col, bg):
    w = max(int(s * 0.13), 2)
    d.rounded_rectangle([x - s, y - s * 0.75, x + s, y + s * 0.55],
                        radius=s * 0.16, outline=col, width=w)
    d.line([x - s * 0.4, y + s * 0.95, x + s * 0.4, y + s * 0.95], fill=col, width=w)
    d.line([x, y + s * 0.55, x, y + s * 0.95], fill=col, width=w)
    d.line([x, y - s * 0.1, x, y - s * 0.5], fill=col, width=w)
    d.line([x, y - s * 0.1, x + s * 0.35, y - s * 0.1], fill=col, width=w)


def g_globe(d, x, y, s, col, bg):
    w = max(int(s * 0.11), 2)
    d.ellipse([x - s, y - s, x + s, y + s], outline=col, width=w)
    d.ellipse([x - s * 0.45, y - s, x + s * 0.45, y + s], outline=col, width=w)
    d.line([x - s, y, x + s, y], fill=col, width=w)


def g_qr(d, x, y, s, col, bg):
    for cx, cy in ((-0.62, -0.62), (0.18, -0.62), (-0.62, 0.18)):
        d.rectangle([x + cx * s, y + cy * s, x + (cx + 0.62) * s, y + (cy + 0.62) * s],
                    outline=col, width=max(int(s * 0.14), 2))
    for cx, cy in ((0.5, 0.2), (0.2, 0.5), (0.75, 0.75), (0.5, 0.75)):
        d.rectangle([x + cx * s, y + cy * s, x + (cx + 0.22) * s, y + (cy + 0.22) * s],
                    fill=col)


def g_chart(d, x, y, s, col, bg):
    w = max(int(s * 0.2), 2)
    for i, h in enumerate((0.35, 0.75, 0.5, 1.0)):
        cx = x - s * 0.72 + i * s * 0.48
        d.line([cx, y + s * 0.95, cx, y + s * 0.95 - h * s * 1.8], fill=col, width=w)


GLYPHS = {
    "bolt": g_bolt, "heart": g_heart, "moon": g_moon, "sun": g_sun,
    "suncloud": g_suncloud, "chat": g_chat, "music": g_music, "bell": g_bell,
    "stopwatch": g_stopwatch, "hourglass": g_hourglass, "calc": g_calc,
    "compass": g_compass, "phone": g_phone, "gear": g_gear, "runner": g_runner,
    "calendar": g_calendar, "camera": g_camera, "footprint": g_footprint,
    "wave": g_wave, "drop": g_drop, "rings": g_rings, "gauge": g_gauge,
    "hand": g_hand, "display": g_display, "globe": g_globe, "qr": g_qr,
    "chart": g_chart,
}

# icon_id → (符号, 底色, 符号色 None=白, 依据)
# 14 个的配色照 watchOS 蜂窝图实测；另外 8 个是临时色，标 [临时]。
ART = {
    "ic_sport_mode":   ("runner",    "#C2ED3C", "#111111", "实测"),
    "ic_sport_record": ("chart",     "#5E5CE6", None,      "临时"),
    "ic_step":         ("footprint", "#FF9F0A", None,      "临时"),
    "ic_physio":       ("wave",      "#30D158", None,      "临时"),
    "ic_hr":           ("heart",     "#FF5B8D", None,      "待核"),
    "ic_spo2":         ("drop",      "#3DA5FF", None,      "待核"),
    "ic_bp":           ("gauge",     "#FF453A", None,      "临时"),
    "ic_breath":       ("rings",     "#64D2FF", None,      "临时"),
    "ic_sleep":        ("moon",      "#9A6BFF", None,      "待核"),
    "ic_calendar":     ("calendar",  "#FF453A", None,      "临时"),
    "ic_weather":      ("suncloud",  "#1BC0FA", None,      "实测"),
    "ic_camera":       ("camera",    "#8E8E93", None,      "临时"),
    "ic_alarm":        ("bell",      "#FF8A3D", None,      "待核"),
    "ic_stopwatch":    ("stopwatch", "#FF9406", None,      "实测"),
    "ic_calculator":   ("calc",      "#B5B5C8", None,      "待核"),
    "ic_timer":        ("hourglass", "#6B7BFF", None,      "待核"),
    "ic_raise_hand":   ("hand",      "#AC8E68", None,      "临时"),
    "ic_find_phone":   ("phone",     "#FF5B5B", None,      "待核"),
    "ic_screen_time":  ("display",   "#40C8E0", None,      "临时"),
    "ic_language":     ("globe",     "#0A84FF", None,      "临时"),
    "ic_qrcode":       ("qr",        "#FFFFFF", "#111111", "临时"),
    "ic_settings":     ("gear",      "#797979", None,      "实测"),
}


# ===========================================================================
# 量包围盒 → 搬正 → 收进圆里
# ===========================================================================
class _BBox(object):
    """只累计坐标范围、不落笔画，用来量符号的**真实**包围盒。"""

    def __init__(self):
        self.x0 = self.y0 = 1e9
        self.x1 = self.y1 = -1e9

    def _add(self, x, y):
        self.x0, self.x1 = min(self.x0, x), max(self.x1, x)
        self.y0, self.y1 = min(self.y0, y), max(self.y1, y)

    def _box(self, b):
        self._add(b[0], b[1])
        self._add(b[2], b[3])

    def ellipse(self, box, **kw):
        self._box(box)

    def rectangle(self, box, **kw):
        self._box(box)

    def rounded_rectangle(self, box, radius=0, **kw):
        self._box(box)

    def polygon(self, points, **kw):
        for x, y in points:
            self._add(x, y)

    def line(self, coords, **kw):
        self._add(coords[0], coords[1])
        self._add(coords[2], coords[3])

    def _arc(self, box, start, end):
        cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
        rx, ry = abs(box[2] - box[0]) / 2.0, abs(box[3] - box[1]) / 2.0
        a = int(min(start, end))
        b = int(max(start, end))
        while a <= b:
            self._add(cx + rx * math.cos(math.radians(a)),
                      cy + ry * math.sin(math.radians(a)))
            a += 5

    def arc(self, box, start, end, **kw):
        self._arc(box, start, end)

    def pieslice(self, box, start, end, **kw):
        self._add((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
        self._arc(box, start, end)

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2.0

    @property
    def rmax(self):
        return max(abs(self.x0 - self.cx), abs(self.x1 - self.cx),
                   abs(self.y0 - self.cy), abs(self.y1 - self.cy))


class _Xform(object):
    """等比缩放 + 平移后转发。一律取整：PIL 的 line 只吃整数。"""

    def __init__(self, t, k, dx, dy):
        self.t, self.k, self.dx, self.dy = t, k, dx, dy

    def _p(self, x, y):
        return int(round(x * self.k + self.dx)), int(round(y * self.k + self.dy))

    def _box(self, b):
        x0, y0 = self._p(b[0], b[1])
        x1, y1 = self._p(b[2], b[3])
        return [x0, y0, x1, y1]

    def _w(self, kw):
        kw = dict(kw)
        if kw.get("width"):
            kw["width"] = max(int(round(kw["width"] * self.k)), 1)
        return kw

    def ellipse(self, box, **kw):
        self.t.ellipse(self._box(box), **kw)

    def rectangle(self, box, **kw):
        self.t.rectangle(self._box(box), **kw)

    def rounded_rectangle(self, box, radius=0, **kw):
        self.t.rounded_rectangle(self._box(box), radius=int(round(radius * self.k)),
                                 **kw)

    def polygon(self, points, **kw):
        self.t.polygon([self._p(x, y) for x, y in points], **kw)

    def line(self, coords, **kw):
        a, b = self._p(coords[0], coords[1]), self._p(coords[2], coords[3])
        self.t.line([a[0], a[1], b[0], b[1]], **self._w(kw))

    def arc(self, box, start, end, **kw):
        self.t.arc(self._box(box), start, end, **self._w(kw))

    def pieslice(self, box, start, end, **kw):
        self.t.pieslice(self._box(box), start, end, **kw)


_METRICS = {}


def metrics(glyph, s):
    key = (glyph, round(s, 3))
    if key not in _METRICS:
        b = _BBox()
        GLYPHS[glyph](b, 0, 0, s, "#FFFFFF", "#000000")
        _METRICS[key] = b
    return _METRICS[key]


def render_icon(size, glyph, bg, fg=None, inset=4, ss=4):
    """画一个图标位图（RGBA）。

    ★ 内容方框与旧版**逐像素同位**：旧版画的是
      `rounded_rectangle((inset, inset, size-1-inset, size-1-inset))`，
      半边长 = (size-1-2*inset)/2。这里把圆塞进同一个方框 ⇒ 换图标是唯一变量。

    ss>1 先按 ss 倍超采样再 LANCZOS 缩回（76px 的圆直接画台阶很明显）；
    超采样只改边缘平滑度，不改方框位置。"""
    big = int(size) * ss
    inset_b = int(inset) * ss
    cx = cy = big / 2.0
    half = (big - 1 - 2 * inset_b) / 2.0
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - half, cy - half, cx + half, cy + half], fill=_hex(bg))

    col = _hex(fg) if fg else "#FFFFFF"
    if glyph in GLYPHS:
        s = half * 2 * FILL_RATIO
        m = metrics(glyph, s)
        limit = half * LIMIT_RATIO
        k = 1.0 if m.rmax <= 0 or m.rmax <= limit else limit / m.rmax
        GLYPHS[glyph](_Xform(d, k, cx - k * m.cx, cy - k * m.cy), 0, 0, s, col,
                      _hex(bg))
    else:                                     # 文字标（如 "97"）
        from PIL import ImageFont
        f = None
        for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
            try:
                f = ImageFont.truetype(p, int(half * 0.9))
                break
            except OSError:
                continue
        if f is not None:
            bb = d.textbbox((0, 0), glyph, font=f)
            d.text((cx - (bb[2] - bb[0]) / 2.0 - bb[0],
                    cy - (bb[3] - bb[1]) / 2.0 - bb[1]), glyph, font=f, fill=col)
    if ss != 1:
        img = img.resize((int(size), int(size)), Image.LANCZOS)
    return img
