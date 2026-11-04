# -*- coding: utf-8 -*-
"""预览长图：22 屏真实设计帧 + 屏内序号 + 右侧控件表 + 左侧跳转总线。

帧与控件框坐标来自 simple_control / pages，不手抄。
"""
import io
import os

import simple_control as sc
import pages as pg

OUT = sc.OUT
S = 0.5
FX = 150
FRAME_W, FRAME_H = int(800 * S), int(480 * S)
BLOCK_H = FRAME_H + 78
TX = FX + FRAME_W + 44
COLS = [("序", 28), ("控件", 120), ("分类", 62), ("点击后", 214), ("行为层", 92)]
TABLE_W = sum(c[1] for c in COLS)
W = TX + TABLE_W + 40
RAIL_IN, RAIL_BACK = 64, 104
ROOM_FIRST, ROOM_LAST = 1, len(sc.ROOM_ORDER)

CAT_LABEL = {"nav": "跳转", "back": "返回", "scene": "场景",
             "toggle": "开关", "slider": "滑条", "read": "只读"}
BEHAV_LABEL = {"换页": sc.CAT_COLORS["nav"],
               "下发硬件": sc.CAT_COLORS["toggle"],
               "只刷新": sc.CAT_COLORS["read"]}


def badge(px, py, num, color, small=False):
    r = 7.5 if small else 10
    fs = 7.5 if small else 10
    return (f'<circle cx="{px}" cy="{py}" r="{r}" fill="{color}" stroke="{sc.BG}" '
            f'stroke-width="1.5"/>'
            f'<text x="{px}" y="{py + fs * 0.36}" font-size="{fs}" fill="{sc.BG}" '
            f'font-weight="700" text-anchor="middle">{num}</text>')


def legend(y):
    out = [sc.t(40, y, "分类色", 11, sc.T1, "700")]
    x = 100
    for k in ("nav", "back", "scene", "toggle", "slider", "read"):
        out.append(sc.r(x, y - 9, 10, 10, sc.CAT_COLORS[k], "none", 3))
        out.append(sc.t(x + 15, y, CAT_LABEL[k], 10, sc.T2))
        x += 72
    for k, c in BEHAV_LABEL.items():
        out.append(sc.r(x, y - 9, 10, 10, "none", c, 3))
        out.append(sc.t(x + 15, y, k, 10, sc.T2))
        x += 88
    return "".join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = pg.PAGES
    top = 160
    H = top + len(pages) * BLOCK_H + 60

    assert len(pages) >= 20, f"页面数 {len(pages)} 少于 20"
    for pi, (name, _f, _ei, _eo, rows) in enumerate(pages):
        assert 1 <= len(rows) <= 14, f"{name} 控件行 {len(rows)} 超出表格高度"
        assert all(r[1] in sc.CAT_COLORS for r in rows), f"{name} 分类色缺项"
        assert all(r[3] in BEHAV_LABEL for r in rows), f"{name} 行为层缺项"
        assert all(r[4] and r[4][2] > 0 and r[4][3] > 0 for r in rows), \
            f"{name} 控件框缺坐标"
        back = [r for r in rows if r[1] == "back"]
        assert len(back) == (0 if pi == 0 else 1), f"{name} 返回按钮数量不对"
        if pi:
            assert back[0][3] == "换页", f"{name} 返回未接换页"
        assert name in {p[0] for p in pages}, f"{name} 未登记"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="Microsoft YaHei,Noto Sans SC,'
        f'PingFang SC,sans-serif">',
        sc.r(0, 0, W, H, sc.BG, "none", 0),
        sc.t(40, 44, f"Haven Home · {len(pages)} 屏设计图预览（真实帧 + 控件标注 + 跳转）",
             24, sc.T1, "700"),
        sc.t(40, 70, "1 主控 + 4 房间页 + 17 个二级页；每屏序号 = 右侧表格行号 = "
                     "屏内彩色框；块底标注该页入口/出口",
             11, sc.T2),
        legend(98),
    ]

    rail_top = top + 26
    rail_bot = top + ROOM_LAST * BLOCK_H + 26
    out.append(sc.line(RAIL_IN, rail_top, RAIL_IN, rail_bot,
                       sc.CAT_COLORS["nav"], 1.6))
    out.append(f'<path d="M{RAIL_BACK},{rail_bot} V{rail_top}" fill="none" '
               f'stroke="{sc.CAT_COLORS["back"]}" stroke-width="1.5" '
               f'stroke-dasharray="6 5"/>')
    out.append(sc.t(RAIL_IN, top - 12, "房间", 9.5, sc.CAT_COLORS["nav"], "600",
                    "middle"))
    out.append(sc.t(RAIL_BACK, top - 12, "返回", 9.5, sc.CAT_COLORS["back"], "600",
                    "middle"))

    for pi, (name, frame_svg, entry, exit_, rows) in enumerate(pages):
        y0 = top + pi * BLOCK_H
        out.append(sc.r(FX - 12, y0 - 20, FRAME_W + 24, FRAME_H + 42, "#0A0F18",
                        sc.EDGE, 10))
        out.append(sc.t(FX - 12, y0 - 28, f"{pi + 1}. {name}页"
                                             f"（800x480 × {S}）", 11, sc.ACCENT,
                        "600"))
        out.append(sc.t(FX - 12, y0 + FRAME_H + 14, entry, 8.5, sc.TEAL))
        out.append(sc.t(FX + FRAME_W + 12, y0 + FRAME_H + 14, exit_, 8.5, sc.T3,
                        "400", "end"))
        out.append(f'<g transform="translate({FX},{y0}) scale({S})">{frame_svg}</g>')
        out.append(sc.r(FX, y0, FRAME_W, FRAME_H, "none", sc.EDGE, 4))

        for ni, (_n, cat, _a, _b, box) in enumerate(rows, start=1):
            bx, by, bw, bh = box
            px, py = FX + bx * S, y0 + by * S
            pw, ph = bw * S, bh * S
            c = sc.CAT_COLORS[cat]
            out.append(sc.r(px, py, pw, ph, "none", c, 6))
            out.append(badge(px + 1, py + 1, ni, c, small=(ph < 22 or pw < 22)))

        if ROOM_FIRST <= pi <= ROOM_LAST:
            out.append(f'<path d="M{RAIL_IN},{y0 + 28} H{FX - 14}" fill="none" '
                       f'stroke="{sc.CAT_COLORS["nav"]}" stroke-width="1.6" '
                       f'marker-end="url(#ain)"/>')
            out.append(f'<path d="M{FX - 14},{y0 + 44} H{RAIL_BACK}" fill="none" '
                       f'stroke="{sc.CAT_COLORS["back"]}" stroke-width="1.5" '
                       f'stroke-dasharray="6 5"/>')
        elif pi == 0:
            out.append(f'<path d="M{FX - 14},{y0 + 28} H{RAIL_IN}" fill="none" '
                       f'stroke="{sc.CAT_COLORS["nav"]}" stroke-width="1.6"/>')
            out.append(f'<path d="M{RAIL_BACK},{y0 + 44} H{FX - 14}" fill="none" '
                       f'stroke="{sc.CAT_COLORS["back"]}" stroke-width="1.5" '
                       f'stroke-dasharray="6 5" marker-end="url(#aback)"/>')

        ty = y0 - 8
        x = TX
        for (h, cw) in COLS:
            out.append(sc.t(x, ty + 10, h, 9.5, sc.T3, "600"))
            x += cw
        out.append(sc.line(TX, ty + 16, TX + TABLE_W, ty + 16, sc.EDGE, 1))
        row_h = min(30, (FRAME_H - 6) / max(len(rows), 1))
        for ri, (cn, cat, act, behav, _box) in enumerate(rows, start=1):
            yy = ty + 28 + (ri - 1) * row_h
            c = sc.CAT_COLORS[cat]
            out.append(f'<circle cx="{TX + 12}" cy="{yy - 3.5}" r="8.5" fill="{c}"/>'
                       f'<text x="{TX + 12}" y="{yy - 0.5}" font-size="9" '
                       f'fill="{sc.BG}" font-weight="700" text-anchor="middle">'
                       f'{ri}</text>')
            x = TX + COLS[0][1]
            out.append(sc.t(x, yy, cn, 9.5, sc.T1, "600"))
            x += COLS[1][1]
            out.append(sc.t(x, yy, CAT_LABEL[cat], 9, c))
            x += COLS[2][1]
            out.append(sc.t(x, yy, act, 9, sc.T2))
            x += COLS[3][1]
            out.append(sc.t(x, yy, behav, 9, BEHAV_LABEL[behav]))

    out.append(
        '<defs>'
        '<marker id="ain" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
        'fill="#F2B45C"/></marker>'
        '<marker id="aback" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
        'fill="#5FD3C6"/></marker>'
        '</defs>')
    out.append("</svg>")

    svg = os.path.join(OUT, "01_preview_pages.svg")
    io.open(svg, "w", encoding="utf-8", newline="\n").write("".join(out))
    print("written", svg, "size", W, H,
          f"[GATE] 屏 {len(pages)} 控件行 {sum(len(p[4]) for p in pages)}")
    try:
        import cairosvg
        png = os.path.join(OUT, "01_preview_pages.png")
        cairosvg.svg2png(url=svg, write_to=png, output_width=W, output_height=H)
        print("written", png)
    except Exception as e:
        print("png skip", e)


if __name__ == "__main__":
    main()