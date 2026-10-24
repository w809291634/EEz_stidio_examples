# -*- coding: utf-8 -*-
"""控件位置图独立脚本（第②步交付物；口径演进见 PR-0313/0314/0315）。

读 design_source.py 的 CONTROLS 注册表：
- 徽标=分类序号 "c-n"（1按钮/2开关/3滑条/4滚轮/5步进/6chips/7按键网格，每类按页序连续编号）；
- 颜色=输出去向（用户 2026-10-22 令）：红=驱动硬件/手机外部（传感器/背光/蜂鸣/马达/BLE），
  绿=UI 内部切换（跳页与本页状态）；
- 跳转关系用**树状结构**出 `_tree.svg`（tab_main → 14 APP → 子页），
  不再用网格+交叉箭头（用户令"树状方便看"）；SVG 为交付真值，cairosvg 光栅化到
  工程外自证后另存 _tree.png 方便双击看。

产物：designer_annotated/<页名>.png（单页红/绿框+徽标）、_tree.svg、_tree.png、图例.md
跑法：python design/design_annotate.py   （改设计源后与 design_view.py 一起重跑）
"""
import base64
import io
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_source as ds

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(HERE, "..", "designer"))
OUT_DIR = os.path.abspath(os.path.join(HERE, "..", "designer_annotated"))

RED = (255, 60, 60)         # 硬件输出
GREEN = (0, 205, 130)       # UI 内部切换
HEX_RED = "#ff3c3c"
HEX_GREEN = "#00cd82"
_font_cache = {}


def font(px):
    if px not in _font_cache:
        for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
            try:
                _font_cache[px] = ImageFont.truetype(p, px)
                break
            except OSError:
                continue
        else:
            _font_cache[px] = ImageFont.load_default()
    return _font_cache[px]


def global_entries():
    """[(徽标"c-n", page, ids, 描述, 跳转, 去向)]；每类按 PAGES 顺序独立连续编号。"""
    counters, out = {c: 0 for c in ds.CATS.values()}, []
    for page in ds.PAGES:
        for _local, ids, desc, jump, cat, hw in ds.CONTROLS.get(page["name"], []):
            counters[ds.CATS[cat]] += 1
            out.append(("%d-%d" % (ds.CATS[cat], counters[ds.CATS[cat]]),
                        page, ids, desc, jump, hw))
    return out


def find_widget(page, token):
    wid = token.rstrip("+")
    for w in page["widgets"]:
        if w.get("id") == wid:
            return w
    return None


def badge_layout(bb, label, placed, img_w):
    """序号圆徽落点（框右上角、越界收进、防重叠避让）——光栅与 SVG 共用同一判据。"""
    x1, y1, x2, _y2 = bb
    r = 12 + 3 * len(label)
    cx = min(x2 + r - 2, img_w - r - 2)
    cy = y1 - r - 2 if y1 - 2 * r > 0 else y1 + r + 2
    while any((cx - px) ** 2 + (cy - py) ** 2 < (2 * r + 4) ** 2 for px, py in placed):
        cx -= 2 * r + 6
        if cx < r:
            cx, cy = min(x2 + r - 2, img_w - r - 2), cy + 2 * r + 6
    placed.append((cx, cy))
    return cx, cy, r


def widget_boxes(page, ids):
    bbs = []
    for token in ids:
        w = find_widget(page, token)
        if w is None:
            print("警告：%s 页找不到 id=%s（注册表与设计源不同步）" % (page["name"], token))
            continue
        bb = ds.widget_bbox(page, w)
        if bb:
            bbs.append(bb)
    return bbs


# ---- 单页标注（红=硬件 绿=UI） ----

def draw_annotations(base, page, entries):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    placed = []
    for label, _pg, ids, _desc, _jump, hw in entries:
        col = RED if hw == "硬件" else GREEN
        for bb in widget_boxes(page, ids):
            x1, y1, x2, y2 = bb
            d.rectangle([x1, y1, x2, y2], outline=col + (255,), width=3)
            d.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill=col + (28,))
            cx, cy, r = badge_layout(bb, label, placed, base.width)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (255,))
            d.text((cx, cy), label, font=font(int(r * 1.05)),
                   fill=(10, 10, 15, 255), anchor="mm")
    return Image.alpha_composite(base, layer)


# ---- 树状跳转图（SVG 真值 + cairosvg 自证光栅） ----

def png_b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def node_img(name):
    """树节点优先用已标注缩略图（控件框/徽标可见），无控件页回落原设计图。"""
    ann = os.path.join(OUT_DIR, name + ".png")
    return ann if os.path.exists(ann) else os.path.join(SRC_DIR, name + ".png")


def build_tree(ents):
    by_page = {}
    hw_of = {}
    for e in ents:
        by_page.setdefault(e[1]["name"], []).append(e)
        hw_of[e[0]] = e[5]

    TH = 260                                   # 缩略图边长（用户令加大）
    x_root, x_app, x_sub = 40, 540, 1080
    slot, y0 = 340, 110
    apps = [p["name"] for p in ds.PAGES if p["name"].startswith("app_")]
    app_y = {n: y0 + i * slot for i, n in enumerate(apps)}
    subs = {"app_alarm": ["alarm_editor"],
            "app_settings": ["set_brightness", "set_sound", "set_facestyle",
                             "set_bt", "set_dnd", "set_about"]}
    sub_y = {}
    for parent, kids in subs.items():
        base = app_y[parent]
        for j, k in enumerate(kids):
            sub_y[k] = base + (j - (len(kids) - 1) / 2.0) * slot
    H = int(max(max(sub_y.values()), max(app_y.values())) + TH + 120)
    x_ext = x_sub + TH + 170
    W = x_ext + 230 + 60

    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" font-family="Microsoft YaHei, SimHei, sans-serif">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="#141419"/>' % (W, H),
         '<text x="%d" y="34" font-size="22" fill="#fff">watch 跳转树 · 连线圆徽=发起控件'
         '（绿底=UI 内部切换 · 红底=输出硬件/手机）· 虚线=手势/跨树 · 分类序号 '
         '1按钮 2开关 3滑条 4滚轮 5步进 6chips 7按键网格</text>' % (x_root,)]

    def node(x, y, name, title):
        s.append('<image href="data:image/png;base64,%s" x="%d" y="%d" width="%d" height="%d"/>'
                 % (png_b64(node_img(name)), x, y, TH, TH))
        s.append('<text x="%d" y="%d" font-size="14" fill="#e8e8f0">%s</text>'
                 % (x, y + TH + 18, title.replace("&", "&amp;").replace("<", "&lt;")))
        hw = [l for l, _p, _i, _d, _j, h in by_page.get(name, []) if h == "硬件"]
        if hw:
            s.append('<text x="%d" y="%d" font-size="13" fill="%s">硬件:%s</text>'
                     % (x, y + TH + 36, HEX_RED, "/".join(hw)))
        return (x, y, x + TH, y + TH)

    def edge_badge(mx, my, label):
        color = HEX_RED if hw_of.get(label) == "硬件" else HEX_GREEN
        r = 11 + 2 * len(label)
        s.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="%s"/>' % (mx, my, r, color))
        s.append('<text x="%.0f" y="%.0f" font-size="13" fill="#0a0a0f" font-weight="bold" '
                 'text-anchor="middle" dominant-baseline="central">%s</text>'
                 % (mx, my, label))

    def elbow(p_from, p_to, badge, color, dashed=False, text=None, t_badge=0.35):
        x1, y1 = p_from[2], (p_from[1] + p_from[3]) / 2
        x2, y2 = p_to[0], (p_to[1] + p_to[3]) / 2
        mx = x1 + (x2 - x1) * 0.5
        dash = ' stroke-dasharray="8,7"' if dashed else ""
        s.append('<path d="M%.0f %.0f C%.0f %.0f %.0f %.0f %.0f %.0f" fill="none" '
                 'stroke="%s" stroke-width="2.5" stroke-opacity="0.75"%s/>'
                 % (x1, y1, mx, y1, mx, y2, x2, y2, color, dash))
        for da in (2.6, -2.6):
            s.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" '
                     'stroke-width="2.5"/>' % (x2, y2, x2 + 12 * math.cos(da),
                                               y2 + 12 * math.sin(da), color))
        if badge:
            # 三次贝塞尔 t 处取点（发起控件圆徽放连线起点侧，扇出不重叠）
            u = t_badge
            bx = (1 - u) ** 3 * x1 + 3 * (1 - u) ** 2 * u * mx + 3 * (1 - u) * u * u * mx + u ** 3 * x2
            by = (1 - u) ** 3 * y1 + 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u * u * y2 + u ** 3 * y2
            edge_badge(bx, by, badge)
        if text:
            s.append('<text x="%.0f" y="%.0f" font-size="13" fill="%s" '
                     'text-anchor="middle">%s</text>'
                     % ((x1 + x2) / 2, (y1 + y2) / 2 + 4, color, text))

    # 根：tab_main（表盘 tab0 + applist tab1，滑动切换）
    wf = node(x_root, y0, "watchface", "tab_main·表盘(tab0)")
    ap = node(x_root, y0 + 420, "applist", "tab_main·applist(tab1)")
    elbow(wf, ap, "", HEX_GREEN, dashed=True, text="滑动切换（手势，非控件）")
    elbow(ap, wf, "", HEX_GREEN, dashed=True)

    # applist → 14 APP（每条连线挂发起控件圆徽 4-1）
    for n in apps:
        title = next(p["title"] for p in ds.PAGES if p["name"] == n)
        node(x_app, app_y[n], n, title + " (%s)" % n)
        elbow(ap, (x_app, app_y[n], x_app + TH, app_y[n] + TH), "4-1", HEX_GREEN)

    # 子页
    for parent, kids in subs.items():
        for k in kids:
            title = next(p["title"] for p in ds.PAGES if p["name"] == k)
            node(x_sub, sub_y[k], k, title + " (%s)" % k)
        lbl = "1-14" if parent == "app_alarm" else "1-26"
        pnode = (x_app, app_y[parent], x_app + TH, app_y[parent] + TH)
        for k in kids:
            elbow(pnode, (x_sub, sub_y[k], x_sub + TH, sub_y[k] + TH),
                  lbl, HEX_GREEN, t_badge=0.22 if len(kids) > 1 else 0.35)

    # 换表盘：set_facestyle → tab_main（虚线）
    elbow((x_sub, sub_y["set_facestyle"], x_sub + TH, sub_y["set_facestyle"] + TH),
          wf, "1-33", HEX_GREEN, dashed=True, t_badge=0.5)
    # 外部目标：手机(BLE) 与 板级硬件 —— 红底圆徽连线（控件→外部，用户令"体现全一点"）
    phone_y = int((app_y["app_music"] + app_y["app_findphone"]
                   + sub_y["set_bt"] + sub_y["set_about"]) / 4 + TH / 2)
    hw_y = int((app_y["app_spo2"] + sub_y["set_brightness"]
                + sub_y["set_sound"]) / 3 + TH / 2)
    ext_phone = (x_ext, phone_y - 48, x_ext + 230, phone_y + 48)
    hw_rect = (x_ext, hw_y - 48, x_ext + 230, hw_y + 48)
    for rc, txt, sub in ((ext_phone, "外部 · 手机 App (BLE)", "响铃/播控/断开/检查更新"),
                         (hw_rect, "外部 · 板级硬件", "背光/光感/功放/蜂鸣/马达/血氧传感器")):
        s.append('<rect x="%d" y="%d" width="230" height="96" rx="14" fill="none" '
                 'stroke="%s" stroke-width="3"/>' % (rc[0], rc[1], HEX_RED))
        s.append('<text x="%d" y="%d" font-size="17" fill="#fff">%s</text>'
                 % (rc[0] + 16, rc[1] + 34, txt))
        s.append('<text x="%d" y="%d" font-size="13" fill="%s">%s</text>'
                 % (rc[0] + 16, rc[1] + 62, HEX_RED, sub))
    ext_edges = [
        ("app_spo2", hw_rect, "1-7"), ("set_brightness", hw_rect, "3-1/2-2"),
        ("set_sound", hw_rect, "3-2/2-3"),
        ("app_music", ext_phone, "1-12"), ("app_findphone", ext_phone, "1-24"),
        ("set_bt", ext_phone, "1-34"), ("set_about", ext_phone, "1-35"),
    ]
    for src_name, dst, badge in ext_edges:
        in_app = src_name in app_y
        sx = x_app if in_app else x_sub
        sy = app_y.get(src_name, sub_y.get(src_name))
        elbow((sx, sy, sx + TH, sy + TH), dst, badge, HEX_RED, t_badge=0.55)

    s.append('</svg>')
    io.open(os.path.join(OUT_DIR, "_tree.svg"), "w", encoding="utf-8").write("\n".join(s))

    # cairosvg 光栅化自证（工程外临时目录）+ 工程内方便版
    import tempfile
    import cairosvg
    tmp = os.path.join(tempfile.gettempdir(), "_tree_check.png")
    cairosvg.svg2png(url=os.path.join(OUT_DIR, "_tree.svg"), write_to=tmp,
                     output_width=W, output_height=H)
    cairosvg.svg2png(url=os.path.join(OUT_DIR, "_tree.svg"),
                     write_to=os.path.join(OUT_DIR, "_tree.png"),
                     output_width=W, output_height=H)
    print("树图自证渲染：", tmp, os.path.getsize(tmp))
    return W, H


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ents = global_entries()
    by_page = {}
    for e in ents:
        by_page.setdefault(e[1]["name"], []).append(e)

    n = 0
    for page in ds.PAGES:
        entries = by_page.get(page["name"])
        if not entries:
            continue
        base = Image.open(os.path.join(SRC_DIR, page["name"] + ".png")).convert("RGBA")
        draw_annotations(base, page, entries).convert("RGB").save(
            os.path.join(OUT_DIR, page["name"] + ".png"))
        n += 1

    W, H = build_tree(ents)

    lines = ["%s | %s | %s | %s | %s | %s" % (
        label, page["name"], "/".join(i.rstrip("+") for i in ids), desc,
        "→ " + jump if jump else "—", hw)
        for label, page, ids, desc, jump, hw in ents]
    io.open(os.path.join(OUT_DIR, "图例.md"), "w", encoding="utf-8").write(
        "# 控件标注图例（design_annotate.py 自动生成，勿手改）\n\n"
        "分类号：1按钮 2开关 3滑条 4滚轮 5步进 6chips 7按键网格；去向：硬件=红，UI=绿。\n"
        "跳转关系见 _tree.svg（交付真值）/_tree.png（方便看）。\n\n"
        "| 号 | 页面 | id | 描述 | 跳转 | 去向 |\n---|---|---|---|---|---\n"
        + "\n".join(lines) + "\n\n语义全文见 ../designer/控件清单表.md\n")
    print("单页 %d 张 + _tree.svg/png(%dx%d, %d 控件)" % (n, W, H, len(ents)))


if __name__ == "__main__":
    main()
