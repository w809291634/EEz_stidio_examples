# -*- coding: utf-8 -*-
"""设计图独立脚本（NO_FLOW 第①步）：读 design_source.py，逐页渲染效果图落 designer/。

与 EEZ 工程生成脚本（build_watch_ui.py）分离但同源。用户确认的即本脚本渲染结果；
不满意改设计源重渲染，禁止在此单独画图。

跑法：python design/design_view.py
产物：designer/<page>.png（每页一张，466x466 圆屏）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_source as ds

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.abspath(os.path.join(HERE, "..", "designer"))

_font_cache = {}


def font(px):
    px = int(px)
    if px in _font_cache:
        return _font_cache[px]
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            _font_cache[px] = ImageFont.truetype(p, px)
            return _font_cache[px]
        except OSError:
            continue
    _font_cache[px] = ImageFont.load_default()
    return _font_cache[px]


def C(hexs):
    h = hexs.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def pt_on_circle(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


# ---- applist 矢量图标（白色线条/形状画在圆角彩底上；s=图标区半宽）----
def _heart(d, x, y, s, col, bg):
    r = s * 0.38
    cy = y - s * 0.4
    d.ellipse([x - s * 0.5 - r, cy - r, x - s * 0.5 + r, cy + r], fill=col)
    d.ellipse([x + s * 0.5 - r, cy - r, x + s * 0.5 + r, cy + r], fill=col)
    d.polygon([(x - s * 0.88, cy + r * 0.35), (x + s * 0.88, cy + r * 0.35),
               (x, y + s * 1.0)], fill=col)


def _moon(d, x, y, s, col, bg):
    d.ellipse([x - s, y - s, x + s, y + s], fill=col)
    d.ellipse([x - s * 0.3, y - s * 1.3, x + s * 1.3, y + s * 0.3], fill=bg)


def _bolt(d, x, y, s, col, bg):
    pts = [(x + .15 * s, y - 1.05 * s), (x - .65 * s, y + .12 * s), (x - .05 * s, y + .12 * s),
           (x - .2 * s, y + 1.05 * s), (x + .7 * s, y - .18 * s), (x + .05 * s, y - .18 * s)]
    d.polygon(pts, fill=col)


def _moon(d, x, y, s, col, bg):
    d.ellipse([x - s, y - s, x + s, y + s], fill=col)
    d.ellipse([x - s * 0.35, y - s * 1.15, x + s * 1.25, y + s * 0.45], fill=bg)


def _sun(d, x, y, s, col, bg):
    r = s * 0.5
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for i in range(8):
        a = i * 45
        x1, y1 = pt_on_circle(x, y, r + s * 0.22, a)
        x2, y2 = pt_on_circle(x, y, r + s * 0.62, a)
        d.line([x1, y1, x2, y2], fill=col, width=max(int(s * 0.14), 2))


def _chat(d, x, y, s, col, bg):
    d.rounded_rectangle([x - s, y - s * 0.85, x + s, y + s * 0.5],
                        radius=s * 0.35, fill=col)
    d.polygon([(x - s * 0.45, y + s * 0.45), (x - s * 0.1, y + s * 0.45),
               (x - s * 0.5, y + s * 0.95)], fill=col)
    ln = max(int(s * 0.12), 2)
    for i, (x1, x2) in enumerate([(-.6, .6), (-.6, .25)]):
        ly = y - s * 0.45 + i * s * 0.45
        d.line([x + x1 * s, ly, x + x2 * s, ly], fill=bg, width=ln)


def _music(d, x, y, s, col, bg):
    wdt = max(int(s * 0.16), 2)
    d.line([x - s * 0.35, y + s * 0.5, x - s * 0.35, y - s * 0.75], fill=col, width=wdt)
    d.line([x + s * 0.65, y + s * 0.25, x + s * 0.65, y - s * 0.95], fill=col, width=wdt)
    d.polygon([(x - s * 0.35, y - s * 0.75), (x + s * 0.65, y - s * 0.95),
               (x + s * 0.65, y - s * 0.55), (x - s * 0.35, y - s * 0.35)], fill=col)
    d.ellipse([x - s * 0.75, y + s * 0.25, x - s * 0.1, y + s * 0.75], fill=col)
    d.ellipse([x + s * 0.25, y + s * 0.0, x + s * 0.9, y + s * 0.5], fill=col)


def _bell(d, x, y, s, col, bg):
    r = s * 0.85
    d.pieslice([x - r, y - r, x + r, y + r], 180, 360, fill=col)
    d.polygon([(x - r, y), (x + r, y), (x + r * 1.15, y + s * 0.6), (x - r * 1.15, y + s * 0.6)],
              fill=col)
    d.ellipse([x - s * 0.12, y - s * 1.15, x + s * 0.12, y - s * 0.85], fill=col)
    d.ellipse([x - s * 0.2, y + s * 0.72, x + s * 0.2, y + s * 1.12], fill=col)


def _watch_g(d, x, y, s, col, bg):
    wdt = max(int(s * 0.13), 2)
    d.ellipse([x - s * 0.85, y - s * 0.75, x + s * 0.85, y + s * 0.95],
              outline=col, width=wdt)
    d.rectangle([x - s * 0.18, y - s * 1.1, x + s * 0.18, y - s * 0.78], fill=col)
    d.line([x, y + s * 0.1, x, y - s * 0.5], fill=col, width=wdt)
    d.line([x, y + s * 0.1, x + s * 0.42, y + s * 0.1], fill=col, width=wdt)


def _hour(d, x, y, s, col, bg):
    wdt = max(int(s * 0.13), 2)
    d.line([x - s * 0.7, y - s * 0.95, x + s * 0.7, y - s * 0.95], fill=col, width=wdt)
    d.line([x - s * 0.7, y + s * 0.95, x + s * 0.7, y + s * 0.95], fill=col, width=wdt)
    d.polygon([(x - s * 0.55, y - s * 0.8), (x + s * 0.55, y - s * 0.8), (x, y + s * 0.05)],
              outline=col, width=wdt)
    d.polygon([(x - s * 0.55, y + s * 0.68), (x + s * 0.55, y + s * 0.68), (x, y - s * 0.08)],
              outline=col, width=wdt)


def _calc(d, x, y, s, col, bg):
    wdt = max(int(s * 0.1), 2)
    d.rounded_rectangle([x - s * 0.8, y - s, x + s * 0.8, y + s], radius=s * 0.2,
                        outline=col, width=wdt)
    d.rectangle([x - s * 0.55, y - s * 0.75, x + s * 0.55, y - s * 0.35], fill=col)
    for r in range(2):
        for c in range(3):
            cx = x - s * 0.45 + c * s * 0.45
            cy = y + s * 0.1 + r * s * 0.45
            d.ellipse([cx - s * 0.09, cy - s * 0.09, cx + s * 0.09, cy + s * 0.09], fill=col)


def _compass(d, x, y, s, col, bg):
    wdt = max(int(s * 0.1), 2)
    d.ellipse([x - s, y - s, x + s, y + s], outline=col, width=wdt)
    d.polygon([(x, y - s * 0.72), (x + s * 0.28, y), (x - s * 0.28, y)], fill=col)
    d.polygon([(x, y + s * 0.72), (x + s * 0.28, y), (x - s * 0.28, y)], outline=col, width=wdt)


def _phone(d, x, y, s, col, bg):
    wdt = max(int(s * 0.11), 2)
    d.rounded_rectangle([x - s * 0.55, y - s * 0.95, x + s * 0.3, y + s * 0.95],
                        radius=s * 0.18, outline=col, width=wdt)
    for i, rr in enumerate((0.45, 0.8)):
        d.arc([x + s * 0.35 - rr * s, y - s * 0.95 - rr * s + s * 0.2,
               x + s * 0.35 + rr * s, y - s * 0.95 + rr * s + s * 0.2],
              0, 90, fill=col, width=wdt)


def _gear(d, x, y, s, col, bg):
    r1, r2 = s * 0.62, s * 0.95
    d.ellipse([x - r1, y - r1, x + r1, y + r1], fill=col)
    for i in range(8):
        a = i * 45
        x1, y1 = pt_on_circle(x, y, r1 * 0.9, a)
        x2, y2 = pt_on_circle(x, y, r2, a)
        d.line([x1, y1, x2, y2], fill=col, width=max(int(s * 0.28), 3))
    d.ellipse([x - s * 0.3, y - s * 0.3, x + s * 0.3, y + s * 0.3], fill=bg)


GLYPHS = {"bolt": _bolt, "heart": _heart, "moon": _moon, "sun": _sun,
          "chat": _chat, "music": _music, "bell": _bell, "watch": _watch_g,
          "hour": _hour, "calc": _calc, "compass": _compass, "phone": _phone,
          "gear": _gear}


def draw_widget(d, w):
    t = w["type"]
    if t == "arc":
        bb = [w["cx"] - w["r"], w["cy"] - w["r"], w["cx"] + w["r"], w["cy"] + w["r"]]
        d.arc(bb, w["start"], w["end"], fill=C(w["color"]), width=w["width"])
    elif t == "ticks":
        for i in range(w["count"]):
            deg = -90 + i * 360.0 / w["count"]
            major = (i % w["major_every"] == 0)
            r_in = w["r_in_major"] if major else w["r_in_minor"]
            col = C(w["major_color"] if major else w["minor_color"])
            wd = w["major_width"] if major else w["minor_width"]
            x1, y1 = pt_on_circle(w["cx"], w["cy"], r_in, deg)
            x2, y2 = pt_on_circle(w["cx"], w["cy"], w["r_out"], deg)
            d.line([x1, y1, x2, y2], fill=col, width=wd)
    elif t == "label":
        d.text((w["x"], w["y"]), w["text"], font=font(w["size"]),
               fill=C(w["color"]), anchor=w.get("anchor", "la"))
    elif t == "statrow":
        for i, (val, lab, col) in enumerate(w["items"]):
            x = w["cx"] + (i - (len(w["items"]) - 1) / 2.0) * w["gap"]
            d.text((x, w["y"] - 8), val, font=font(30), fill=C(col), anchor="mm")
            d.text((x, w["y"] + 22), lab, font=font(18), fill=C(ds.STYLE["sub"]), anchor="mm")
    elif t == "pager_dots":
        for i in range(w["count"]):
            x = w["cx"] + (i - (w["count"] - 1) / 2.0) * w["gap"]
            r = w["r"]
            col = C(ds.STYLE["text"]) if i == w["active"] else C(ds.STYLE["ring"])
            d.ellipse([x - r, w["y"] - r, x + r, w["y"] + r], fill=col)
    elif t == "roller":
        bg = C(ds.STYLE["bg"])
        for row in ds.roller_rows(ds.SCREEN, w["apps"], w["center_idx"]):
            s = row["side"]
            x0, y0 = row["x"] - s / 2.0, row["y"] - s / 2.0
            d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=s * 0.28,
                                fill=C(row["color"]))
            if s > 24:
                g = row["abbr"]
                if g in GLYPHS:
                    GLYPHS[g](d, row["x"], row["y"], s * 0.36, C("#FFFFFF"), bg)
                else:                       # 文字标（如血氧 "97"）
                    d.text((row["x"], row["y"]), g, font=font(int(s * 0.42)),
                           fill=C("#FFFFFF"), anchor="mm")
            if abs(row["d"]) <= 4:
                lx = ds.ROLLER["label_x"] + (row["x"] - ds.ROLLER["icon_cx"])
                d.text((lx, row["y"]), row["name"],
                       font=font(max(int(26 * s / ds.ROLLER["icon_px"]), 12)),
                       fill=C(ds.STYLE["text"]), anchor="lm")
    elif t == "back":
        d.line([w["x"] + 7, w["y"] - 11, w["x"] - 7, w["y"], w["x"] + 7, w["y"] + 11],
               fill=C(ds.STYLE["text"]), width=3, joint="curve")
    elif t == "bars":
        n = len(w["values"])
        total_w = n * w["bw"] + (n - 1) * w["gap"]
        x = w["cx"] - total_w / 2.0
        vmax = max(w["values"])
        for v, lab in zip(w["values"], w.get("labels", [])):
            hgt = max(w["h"] * v / vmax, 4)
            d.rounded_rectangle([x, w["y"] - hgt, x + w["bw"], w["y"]],
                                radius=4, fill=C(w["color"]))
            if lab:
                d.text((x + w["bw"] / 2, w["y"] + 14), lab, font=font(14),
                       fill=C(ds.STYLE["sub"]), anchor="ma")
            x += w["bw"] + w["gap"]
    elif t == "progress":
        x0 = w.get("cx", ds.SCREEN["cx"]) - w["w"] / 2.0
        if w.get("label"):
            d.text((x0, w["y"] - 14), w["label"], font=font(16),
                   fill=C(ds.STYLE["sub"]), anchor="lm")
        if w.get("value"):
            d.text((x0 + w["w"], w["y"] - 14), w["value"],
                   font=font(w.get("value_size", 16)),
                   fill=C(ds.STYLE["sub"]), anchor="rm")
        d.rounded_rectangle([x0, w["y"], x0 + w["w"], w["y"] + 6],
                            radius=3, fill=C(ds.STYLE["ring"]))
        d.rounded_rectangle([x0, w["y"], x0 + w["w"] * w["pct"], w["y"] + 6],
                            radius=3, fill=C(w["color"]))
    elif t == "pill":
        x0, y0 = w["x"] - w["w"] / 2.0, w["y"] - w["h"] / 2.0
        d.rounded_rectangle([x0, y0, x0 + w["w"], y0 + w["h"]],
                            radius=w["h"] / 2.0, fill=C(w["color"]))
        d.text((w["x"], w["y"]), w["text"], font=font(int(w["h"] * w.get("text_size", 42) / 100)),
               fill=C("#0A0A0F"), anchor="mm")
    elif t == "chips":
        n = len(w["cells"])
        total = n * w["cw"] + (n - 1) * w["gap"]
        x = w["cx"] - total / 2.0
        for i, cell in enumerate(w["cells"]):
            on = i in w["on"]
            d.rounded_rectangle([x, w["y"] - w["ch"] / 2, x + w["cw"], w["y"] + w["ch"] / 2],
                                radius=w["ch"] / 2,
                                fill=C(ds.STYLE["accent"] if on else "#1E1E28"))
            d.text((x + w["cw"] / 2, w["y"]), cell, font=font(18),
                   fill=C(ds.STYLE["text"]), anchor="mm")
            x += w["cw"] + w["gap"]
    elif t == "switch":
        on = w["on"]
        x0 = w["cx"] - 30
        d.rounded_rectangle([x0, w["y"] - 16, x0 + 60, w["y"] + 16], radius=16,
                            fill=C(ds.STYLE["green"] if on else ds.STYLE["ring"]))
        kx = x0 + 44 if on else x0 + 16
        d.ellipse([kx - 13, w["y"] - 13, kx + 13, w["y"] + 13], fill=C("#FFFFFF"))
        d.text((w["cx"], w["y"] - 34), w["text"], font=font(20),
               fill=C(ds.STYLE["text"]), anchor="mm")
    elif t == "slider":
        x0 = w.get("cx", ds.SCREEN["cx"]) - w["w"] / 2.0
        d.rounded_rectangle([x0, w["y"] - 4, x0 + w["w"], w["y"] + 4],
                            radius=4, fill=C(ds.STYLE["ring"]))
        kx = x0 + w["w"] * w["pct"]
        d.rounded_rectangle([x0, w["y"] - 4, kx, w["y"] + 4], radius=4, fill=C(w["color"]))
        d.ellipse([kx - 13, w["y"] - 13, kx + 13, w["y"] + 13], fill=C("#FFFFFF"))
    elif t == "stepper":
        s = 11
        for dy, up in ((-52, True), (52, False)):
            ty = w["y"] + dy
            pts = [(w["x"] - s, ty + s * 0.7, ), (w["x"] + s, ty + s * 0.7)] if up else \
                  [(w["x"] - s, ty - s * 0.7), (w["x"] + s, ty - s * 0.7)]
            pts.append((w["x"], ty - s * 0.7 if up else ty + s * 0.7))
            d.polygon(pts, fill=C(w["bg"]))
    elif t == "facepick":
        for i, nm in enumerate(w["names"]):
            x = w["cx"] + (i - (len(w["names"]) - 1) / 2.0) * w["gap"]
            r = w["r"]
            d.ellipse([x - r, w["y"] - r, x + r, w["y"] + r],
                      fill=C("#12121A"),
                      outline=C(ds.STYLE["accent"] if i == w["active"] else ds.STYLE["ring"]),
                      width=3 if i == w["active"] else 2)
            d.text((x, w["y"] - 6), "10:09", font=font(18),
                   fill=C(ds.STYLE["text"]), anchor="mm")
            d.text((x, w["y"] + 18), ["数字", "圆环", "星空"][i], font=font(13),
                   fill=C(ds.STYLE["sub"]), anchor="mm")
            d.text((x, w["y"] + r + 20), nm, font=font(16),
                   fill=C(ds.STYLE["sub"]), anchor="mm")
    elif t == "segbar":
        x = w.get("cx", ds.SCREEN["cx"]) - w["w"] / 2.0
        for _name, frac, col in w["segs"]:
            x2 = x + w["w"] * frac
            d.rectangle([x, w["y"], x2, w["y"] + w["h"]], fill=C(col))
            x = x2
    elif t == "legend":
        f15 = font(15)
        items = w["items"]
        total = (len(items) - 1) * w["gap"] + sum(
            14 + d.textlength(t, font=f15) for t, _ in items)
        x = ds.SCREEN["cx"] - total / 2.0
        for text, col in items:
            d.ellipse([x, w["y"] - 5, x + 10, w["y"] + 5], fill=C(col))
            d.text((x + 14, w["y"]), text, font=f15,
                   fill=C(ds.STYLE["sub"]), anchor="lm")
            x += 14 + d.textlength(text, font=f15) + w["gap"]
    elif t == "ring":
        bb = [w["cx"] - w["r"], w["cy"] - w["r"], w["cx"] + w["r"], w["cy"] + w["r"]]
        d.arc(bb, -90, 270, fill=C(w["bg"]), width=w["width"])
        if w["pct"] < 1.0:
            d.arc(bb, -90, -90 + 360 * w["pct"], fill=C(w["color"]), width=w["width"])
    elif t == "grid":
        for k, cell in enumerate(w["cells"]):
            r, c = divmod(k, w["cols"])
            x0 = w["x0"] + c * (w["cw"] + w["gap"])
            y0 = w["y0"] + r * (w["ch"] + w["gap"])
            col = w["accent_color"] if cell in w.get("accent_cells", []) else w["bg"]
            d.rounded_rectangle([x0, y0, x0 + w["cw"], y0 + w["ch"]],
                                radius=8, fill=C(col))
            d.text((x0 + w["cw"] / 2, y0 + w["ch"] / 2), cell, font=font(w["size"]),
                   fill=C(w["fg"]), anchor="mm")
    elif t == "controls":
        for i, shp in enumerate(w["shapes"]):
            x = w["cx"] + (i - (len(w["shapes"]) - 1) / 2.0) * w["gap"]
            y, s = w["y"], w["size"]
            col = C(w["color"])
            if shp == "play":
                d.polygon([x - s * 0.7, y - s, x - s * 0.7, y + s, x + s * 0.9, y], fill=col)
            elif shp == "prev":
                d.polygon([x + s * 0.5, y - s, x + s * 0.5, y + s, x - s * 0.9, y], fill=col)
                d.rectangle([x - s * 1.2, y - s, x - s * 0.95, y + s], fill=col)
            elif shp == "next":
                d.polygon([x - s * 0.5, y - s, x - s * 0.5, y + s, x + s * 0.9, y], fill=col)
                d.rectangle([x + s * 0.95, y - s, x + s * 1.2, y + s], fill=col)
            else:
                raise ValueError("未知 controls 形状：%s" % shp)
    elif t == "roundrect":
        x0, y0 = w["cx"] - w["w"] / 2.0, w["cy"] - w["h"] / 2.0
        d.rounded_rectangle([x0, y0, x0 + w["w"], y0 + w["h"]],
                            radius=w["radius"], outline=C(w["color"]), width=3)
    elif t == "disc":
        d.ellipse([w["cx"] - w["r"], w["cy"] - w["r"],
                   w["cx"] + w["r"], w["cy"] + w["r"]], fill=C(w["color"]))
        d.ellipse([w["cx"] - 10, w["cy"] - 10, w["cx"] + 10, w["cy"] + 10],
                  fill=C("#101018"))
    elif t == "frame":
        d.rounded_rectangle([w["x"], w["y"], w["x"] + w["w"], w["y"] + w["h"]],
                            radius=10, outline=C(w["color"]), width=2)
    elif t == "shutter":
        d.ellipse([w["cx"] - w["r"], w["cy"] - w["r"],
                   w["cx"] + w["r"], w["cy"] + w["r"]],
                  outline=C(w["color"]), width=4)
        d.ellipse([w["cx"] - w["r"] + 9, w["cy"] - w["r"] + 9,
                   w["cx"] + w["r"] - 9, w["cy"] + w["r"] - 9], fill=C(w["color"]))
    elif t == "rowlist":
        cx = ds.SCREEN["cx"]
        for i, row in enumerate(w["rows"]):
            cy = w["y0"] + i * w["row_h"] + w["row_h"] // 2
            d.text((cx - w["w"] / 2, cy), row[0], font=font(w["size"]),
                   fill=C(ds.STYLE["text"]), anchor="lm")
            if len(row) > 1:
                d.text((cx + w["w"] / 2, cy), row[1], font=font(w["size"]),
                       fill=C(ds.STYLE["sub"]), anchor="rm")
            if i < len(w["rows"]) - 1:
                ly = w["y0"] + (i + 1) * w["row_h"]
                d.line([cx - w["w"] / 2, ly, cx + w["w"] / 2, ly],
                       fill=C(ds.STYLE["ring"]), width=1)
    else:
        raise ValueError("未知控件类型（design_source 与 design_view 必须同步支持）：%s" % t)


def render_page(page):
    w, h = ds.SCREEN["w"], ds.SCREEN["h"]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    face = Image.new("RGBA", (w, h), C(ds.STYLE["bg"]))
    d = ImageDraw.Draw(face)
    for widget in page["widgets"]:
        draw_widget(d, widget)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    face.putalpha(mask)
    img = Image.alpha_composite(img, face)
    dd = ImageDraw.Draw(img)
    dd.ellipse([1, 1, w - 2, h - 2], outline=C(ds.STYLE["ring"]), width=2)
    dd.text((14, 10), page["title"], font=font(16), fill=(150, 150, 170, 255))
    out = os.path.join(OUT_DIR, page["name"] + ".png")
    img.save(out)
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for page in ds.PAGES:
        print("已渲染：", render_page(page))
    print("共 %d 页。不满意改 design_source.py 重渲染（禁止单独画图）。" % len(ds.PAGES))


if __name__ == "__main__":
    main()
