# -*- coding: utf-8 -*-
"""交互控件行为覆盖审计（⑦）：设计行 vs 已接事件/绑定。

只报“存在/类型”会漏掉“能点但没反应”。本脚本统计：
  - nav/back 是否由 nav_bind 覆盖
  - Wi-Fi 页动作是否由 wifi 层覆盖
  - 滑条是否有数值标签绑定
  - toggle / scene / 其余 slider 是否仍未接行为

用法：python design/behavior_audit.py [--strict]
  --strict：有未接行为的交互控件时退出码 1（供后续交付门禁使用）
"""
import collections
import sys

import overview_pro as ov
import pages as pg

WIFI_HANDLED = {"‹ 设置 按钮", "断开", "扫描", "网络列表", "弹层·密码框",
                "弹层·连接", "弹层·关闭", "弹层·键盘", "对话框·忘记",
                "对话框·断开", "对话框·取消"}
BOUND_SLIDERS = {("客厅", "窗帘"), ("主卧", "窗帘"), ("窗帘详情", "开合度"),
                 ("灯详情", "亮度"), ("设置", "自动锁屏")}
STATIC_SCENES = {("主卧", "晚安模式")}   # 设计标明“不响应点击”，只做展示
BOUND_ACTIONS = {
    ("主控", "回家按钮"), ("主控", "离家按钮"),
    ("主控", "晚安按钮"), ("主控", "影院按钮"),
    ("窗帘详情", "全开"), ("窗帘详情", "半开"), ("窗帘详情", "全关"),
    ("空调详情", "温度 −"), ("空调详情", "温度 ＋"),
    ("空调详情", "制冷"), ("空调详情", "制热"), ("空调详情", "送风"),
    ("空调详情", "风速 低"), ("空调详情", "风速 中"), ("空调详情", "风速 高"),
}


def main():
    cats = collections.Counter()
    unhandled = collections.defaultdict(list)
    bound = collections.Counter()
    for name, *_x, rows in pg.PAGES:
        for nm, cat, act, beh, _box in rows:
            io = ov.io_of(name, {"name": nm, "behav": beh, "cat": cat})
            cats[(cat, io)] += 1
            if io == "nav":
                bound["nav"] += 1
            elif name == "Wi-Fi 设置" and nm in WIFI_HANDLED:
                bound["wifi"] += 1
            elif cat == "slider" and (name, nm) in BOUND_SLIDERS:
                bound["slider-label"] += 1
            elif (name, nm) in BOUND_ACTIONS:
                bound["action"] += 1
            elif (name, nm) in STATIC_SCENES:
                bound["static"] += 1
            elif cat in ("toggle", "slider", "scene"):
                unhandled[cat].append((name, nm, act))

    total = sum(len(v) for v in unhandled.values())
    print("[BEHAVIOR] 已接：导航 %d ｜ Wi-Fi %d ｜ 滑条数值 %d ｜ 本地动作 %d ｜ 静态展示 %d"
          % (bound["nav"], bound["wifi"], bound["slider-label"], bound["action"],
             bound["static"]))
    print("[BEHAVIOR] 未接交互件 %d：开关 %d ｜ 动作按钮/场景 %d ｜ 滑条 %d"
          % (total, len(unhandled["toggle"]), len(unhandled["scene"]),
             len(unhandled["slider"])))
    for cat in ("toggle", "scene", "slider"):
        if not unhandled[cat]:
            continue
        print("-- %s（%d）" % (cat, len(unhandled[cat])))
        for x in unhandled[cat][:6]:
            print("   %s · %s — %s" % x)
        if len(unhandled[cat]) > 6:
            print("   …")
    if "--strict" in sys.argv and total:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("\\", 1)[0])
    main()
