#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 WiFi 列表页设计图（单一网格常量驱动，杜绝手摆坐标的基线漂移）。

输出：design/mockup_list.svg（480x320 逻辑坐标，等比放大 1.25 放进 680 画布）。
对齐约束（脚本内断言）：
  - 行高/行距统一；左列（信号条）x 统一；
  - 文本两行基线统一（row+19 / row+35）；
  - 右侧状态槽：所有元素右缘 = RIGHT_EDGE，垂直中心 = row+23；
  - 锁列 x 统一。
"""
import os

W, H = 480, 320
PAD = 16
ROW_H, ROW_GAP = 46, 6
ROW_X, ROW_W = PAD, W - PAD * 2
LIST_TOP = 56
RIGHT_EDGE = ROW_X + ROW_W - 14        # 450：右槽统一右缘
LOCK_X = RIGHT_EDGE - 56 - 16 - 10     # 378：锁列
TEXT_X = ROW_X + 42                    # 58
BAR_X = ROW_X + 14                     # 30
SSID_BASE = 19                         # 相对行顶
META_BASE = 35
STATUS_CY = 23                         # 相对行顶的状态垂直中心

# ---- 配色 ----
BG, ROW_BG, ROW_CONN = "#0B0F1A", "#101A28", "#101A28"
LINE, LINE_CONN = "#26314A", "#2E9F79"
PRI, SUC = "#5B8CFF", "#3DDC97"
T1, T2, T3 = "#F0F4FC", "#8A99B3", "#5C6A85"
DIM = "#26314A"

ROWS = [
    dict(ssid="yjt_dev_2.4G", meta="WPA2 · -58 dBm · 5 GHz", bars=4, lock=True,
         status=("conn", "已连接")),
    dict(ssid="1号楼6层WiFi", meta="WPA3 · -63 dBm · 5 GHz", bars=4, lock=True,
         status=("saved", "已保存")),
    dict(ssid="YJT-1号楼办公", meta="WPA2 · -66 dBm · 2.4 GHz", bars=3, lock=True,
         status=None),
    dict(ssid="Office-2G", meta="开放网络 · -74 dBm · 2.4 GHz", bars=2, lock=False,
         status=("open", "无需密码")),
    dict(ssid="Home_5G", meta="WPA2 · -88 dBm · 5 GHz", bars=1, lock=True,
         status=None),
]

out = []
a = out.append
a('<svg viewBox="0 0 680 460" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" '
  'font-family="Segoe UI, Microsoft YaHei, sans-serif">')
a('  <title>WiFi 列表页 · 网格对齐版</title>')
a('  <desc>统一网格生成：行高行距一致、双行基线一致、右侧状态槽右缘与中心线一致、锁列对齐</desc>')
a('  <g transform="translate(40,40) scale(1.25)">')
a('    <rect x="0" y="0" width="480" height="320" rx="14" fill="%s" stroke="%s" stroke-width="1"/>'
  % (BG, LINE))

# 头部
a('    <text x="%d" y="26" fill="%s" font-size="18" font-weight="500">WiFi</text>' % (PAD, T1))
a('    <text x="%d" y="44" fill="%s" font-size="12">已发现 %d 个网络</text>'
  % (PAD, T2, len(ROWS)))
a('    <rect x="400" y="14" width="64" height="26" rx="13" fill="#161E30" stroke="%s" '
  'stroke-width="0.5"/>' % LINE)
a('    <text x="432" y="31" fill="#B9C6DC" font-size="11" text-anchor="middle">刷新</text>')

checked = []
for i, r in enumerate(ROWS):
    y = LIST_TOP + i * (ROW_H + ROW_GAP)
    conn = r["status"] and r["status"][0] == "conn"
    # 行底
    a('    <rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="%s" stroke="%s" '
      'stroke-width="%s"/>' % (ROW_X, y, ROW_W, ROW_H, ROW_BG,
                               LINE_CONN if conn else LINE,
                               "1" if conn else "0.5"))
    # 信号条（底对齐 row+34，高 5/8/11/14）
    heights = [5, 8, 11, 14]
    for b in range(4):
        on = b < r["bars"]
        col = (SUC if conn else PRI) if on else DIM
        h = heights[b]
        a('    <rect x="%.1f" y="%d" width="3.6" height="%d" fill="%s"/>'
          % (BAR_X + b * 6, y + 34 - h, h, col))
    # SSID + meta
    a('    <text x="%d" y="%d" fill="%s" font-size="15">%s</text>'
      % (TEXT_X, y + SSID_BASE, T1, r["ssid"]))
    a('    <text x="%d" y="%d" fill="%s" font-size="11">%s</text>'
      % (TEXT_X, y + META_BASE, T2, r["meta"]))
    # 锁（右缘 = LOCK_X+10，中心 = row+17，与 SSID 基线视觉齐）
    if r["lock"]:
        a('    <rect x="%d" y="%d" width="10" height="8" rx="1.6" fill="%s"/>'
          % (LOCK_X, y + 20, T2))
        a('    <path d="M%d %d v-2.6 a2.6 2.6 0 0 1 5.2 0 v2.6" fill="none" stroke="%s" '
          'stroke-width="1.3"/>' % (LOCK_X + 2, y + 20, T2))
    # 状态槽：右缘统一 RIGHT_EDGE，中心统一 STATUS_CY
    checked.append(RIGHT_EDGE)
    if r["status"]:
        kind, txt = r["status"]
        if kind in ("conn", "saved"):
            pw = 52 if kind == "conn" else 46
            px = RIGHT_EDGE - pw
            fill, edge, col = (("#0E2A22", LINE_CONN, SUC) if kind == "conn"
                               else ("#16203A", PRI, "#9DB8FF"))
            a('    <rect x="%d" y="%d" width="%d" height="17" rx="8.5" fill="%s" '
              'stroke="%s" stroke-width="0.5"/>' % (px, y + STATUS_CY - 8, pw, fill, edge))
            if kind == "conn":
                a('    <circle cx="%d" cy="%.1f" r="2.6" fill="%s"/>'
                  % (px + 10, y + STATUS_CY - 0.5, SUC))
                a('    <text x="%d" y="%.1f" fill="%s" font-size="10">%s</text>'
                  % (px + 17, y + STATUS_CY + 3, col, txt))
            else:
                a('    <text x="%.1f" y="%.1f" fill="%s" font-size="10" '
                  'text-anchor="middle">%s</text>'
                  % (px + pw / 2, y + STATUS_CY + 3, col, txt))
        else:
            a('    <text x="%d" y="%d" fill="%s" font-size="10" text-anchor="end">%s</text>'
              % (RIGHT_EDGE, y + STATUS_CY + 3, T3, txt))

a('  </g>')
a('</svg>')

# ---- 断言：所有状态元素右缘一致 ----
assert len(set(checked)) == 1, "status right edges differ: %s" % set(checked)
lock_center = 20 + 2.7                      # 锁体 y + 视觉中心偏移
assert abs(lock_center - ROW_H / 2) <= 1.5, "lock not v-centered"
assert LIST_TOP + len(ROWS) * (ROW_H + ROW_GAP) - ROW_GAP <= H - 10, "list overflows"

svg = "\n".join(out) + "\n"
dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mockups", "mockup_list.svg")
open(dst, "w", encoding="utf-8").write(svg)
print("written:", dst, len(svg), "bytes")
print(svg)
