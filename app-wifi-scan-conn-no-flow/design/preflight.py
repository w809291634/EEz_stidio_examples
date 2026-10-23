#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preflight.py — EEZ 一键预检：按顺序跑完全链，任一步失败立即停。

对应本地经验：
  P-0005  CLI 报 "Build successfully finished" 但零产出 → 本脚本**校验产物文件**
  P-0013  gcc 不在 PATH 时静默失败             → 编译步单独报错，不吞输出
  P-0164  顺序敏感：gen_font 必须在 cli_build 之后（孤儿清理会删字体）

用法：
  python design/preflight.py            # 生成 + 构建 + 静态自检（不编译仿真）
  python design/preflight.py --with-sim # 再加一步：PC 仿真编译
  python design/preflight.py --skip-cli # 跳过 EEZ CLI（只跑生成与静态检查）

退出码：0 全绿；1 某步失败（并打印该步日志尾部）。
"""
import os
import subprocess
import sys
import time

# Windows 控制台默认 GBK：打印字体丢弃字符（如 U+30FB）或检查名里的符号
# 会 UnicodeEncodeError 把流程本身打断 —— 编不出的字符替换掉，不中断。
try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# 每一步：(名称, 命令, 工作目录, 是否必需)
# 注意顺序：build_example → cli_build → audit → check_project → gen_font
STEPS = [
    ("生成 .eez-project", [PY, "build_example.py"], ROOT, True),
    ("EEZ CLI 构建（含 flow 守卫）", [PY, "design/cli_build.py"], ROOT, True),
    ("逐字审计（文案 ⊆ 字体）", [PY, "design/audit_chars.py"], ROOT, True),
    ("静态自检 7 项", [PY, "design/check_project.py"], ROOT, False),
    ("烘焙字库（必须在 cli_build 之后）", [PY, "design/gen_font.py"], ROOT, False),
]

# P-0005：这些文件必须存在且非空，否则"构建成功"是假的
ARTIFACTS = [
    "src/ui/screens.c",
    "src/ui/ui.c",
    "src/ui/vars.h",
    "src/ui/actions.h",
    "src/ui/structs.h",
]

# ★ no-flow 变体的存在性判据是"反向"的：Flow 运行时**不应**出现。
#   一旦 EEZ 重新发射这些文件，说明 flowSupport 开关被改回去了。
NO_FLOW_ABSENT = [
    "src/ui/eez-flow.cpp",
    "src/ui/eez-flow.h",
]


def check_no_flow():
    print("\n=== [必跑] no-flow 判据：Flow 运行时不得发射 ===")
    bad = [rel for rel in NO_FLOW_ABSENT if os.path.exists(os.path.join(ROOT, rel))]
    if bad:
        print("FAIL: 出现了 Flow 产物 → %s（检查 settings.general.flowSupport）"
              % ", ".join(bad))
        return False
    # 正向：事件动作链要在没有 Flow 的情况下仍然接线
    screens = os.path.join(ROOT, "src/ui/screens.c")
    body = open(screens, encoding="utf-8", errors="replace").read() if os.path.exists(screens) else ""
    if "action_scan_start" not in body or "lv_obj_add_event_cb" not in body:
        print("FAIL: screens.c 里找不到 native 动作接线（按钮点击会静默）")
        return False
    print("OK: 无 eez-flow.*；screens.c 已用 lv_obj_add_event_cb 直连 action_scan_start")
    return True


def run(name, cmd, cwd, required):
    print("\n=== [%s] %s ===" % ("必跑" if required else "可选", name))
    # 脚本不存在：可选步骤直接 SKIP（别打印 Python 的 "can't open file" 噪音）
    for arg in cmd[1:]:
        if arg.endswith(".py") and not os.path.exists(os.path.join(cwd, arg)):
            print("SKIP: 未提供 %s" % arg)
            return None if not required else False
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=600, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print("SKIP: 文件不存在 →", cmd[0])
        return None if not required else False
    out = (p.stdout or "") + (p.stderr or "")
    tail = "\n".join(out.strip().splitlines()[-12:])
    print(tail)
    print("耗时 %.1fs，退出码 %s" % (time.time() - t0, p.returncode))
    if p.returncode != 0:
        if required:
            print("FAIL: %s" % name)
            return False
        print("WARN: %s 未通过（非必需，继续）" % name)
        return None
    return True


def check_artifacts():
    print("\n=== [必跑] 产物存在性（P-0005：别信 'Build successfully finished'）===")
    bad = []
    for rel in ARTIFACTS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append(rel + "（缺失）")
            continue
        size = os.path.getsize(p)
        if size < 50:
            bad.append(rel + "（只有 %d 字节）" % size)
        age = time.time() - os.path.getmtime(p)
        flag = "新" if age < 600 else "%.0f 分钟前" % (age / 60)
        print("  %-24s %8d 字节  %s" % (rel, size, flag))
    if bad:
        print("FAIL: 产物不完整 → %s" % ", ".join(bad))
        print("      常见原因：settings.build.files 被删/被改（P-0005）")
        return False
    print("OK: 产物齐全")
    return True


def check_geometry():
    """④ A 层：EEZ 出码里的控件几何必须等于设计源常量，且设计源与设计图脚本同值。

    这条门禁是为一次真实错误加的：空态「重新扫描」的标注框抄错成 (190,236,100,30)，
    真实按钮是 (170,256,140,34)，标注画到了文案上 —— 三方（生成器/设计图/标注）
    各存一份数字，迟早对不上。"""
    print("\n=== [④A] 出码几何 == 设计源 == 设计图 ===")
    import io
    import re
    sys.path.insert(0, ROOT)          # build_example 在工程根
    import build_example as BE
    import mockup_gen as MG
    ok = True

    # ① 设计源（生成器）与设计图脚本的几何常量必须一致
    pairs = [("SHEET_Y", BE.SHEET_Y, MG.SHEET_Y),
             ("SHEET_H", BE.SHEET_H, MG.SHEET_H),
             ("SHEET_TA", BE.SHEET_TA, MG.SHEET_TA),
             ("SHEET_BTN", BE.SHEET_BTN, MG.SHEET_BTN),
             ("SHEET_KB", BE.SHEET_KB, MG.SHEET_KB),
             ("SHEET_KB_GAP", BE.SHEET_KB_GAP, MG.SHEET_KB_GAP),
             ("DIALOG_BOX", BE.DIALOG_BOX, MG.DIALOG_BOX),
             ("DIALOG_BTN_L", BE.DIALOG_BTN_L, MG.DIALOG_BTN_L),
             ("DIALOG_BTN_R", BE.DIALOG_BTN_R, MG.DIALOG_BTN_R),
             ("HEAD_BTN", BE.HEAD_BTN, MG.HEAD_BTN)]
    # 空态「重新扫描」只存在于设计图/标注（EEZ 里空态由 native 画），不进这份对账
    norm = lambda v: v if isinstance(v, tuple) else (v,)
    bad = ["%s: 生成器=%s 设计图=%s" % (n, a, b)
           for n, a, b in pairs if norm(a) != norm(b)]
    print("%s 设计源与设计图几何一致（%d 组）"
          % ("OK  " if not bad else "FAIL", len(pairs)))
    if bad:
        ok = False
        print("      " + "; ".join(bad))

    # ② 出码几何 == 设计源
    src = io.open(os.path.join(ROOT, "src", "ui", "screens.c"),
                  encoding="utf-8").read()

    def geo(ident):
        i = src.find("objects.%s = obj;" % ident)
        if i < 0:
            return None
        seg = src[i:i + 400]
        m1 = re.search(r"lv_obj_set_pos\(obj, (-?\d+), (-?\d+)\)", seg)
        m2 = re.search(r"lv_obj_set_size\(obj, (-?\d+), (-?\d+)\)", seg)
        if not (m1 and m2):
            return None
        return (int(m1.group(1)), int(m1.group(2)),
                int(m2.group(1)), int(m2.group(2)))

    checks = [
        ("sheet", (0, BE.SHEET_Y, BE.SCREEN_W, BE.SHEET_H)),
        # ★ 半页里的子控件在 EEZ 出码里是**相对 sheet** 的坐标，不要加 SHEET_Y
        ("pwd_ta", BE.SHEET_TA),
        ("btn_connect", BE.SHEET_BTN),
        ("kb_main", BE.SHEET_KB),
        ("sheet_handle", (224, 6, 32, 3)),
        ("dlg_card", BE.DIALOG_BOX),
        ("btn_dlg_forget",
         (BE.DIALOG_BTN_L[0] - BE.DIALOG_BOX[0],
          BE.DIALOG_BTN_L[1] - BE.DIALOG_BOX[1], 140, 32)),
        ("btn_dlg_cancel",
         (BE.DIALOG_BTN_R[0] - BE.DIALOG_BOX[0],
          BE.DIALOG_BTN_R[1] - BE.DIALOG_BOX[1], 140, 32)),
    ]
    for ident, expect in checks:
        got = geo(ident)
        good = got is not None and tuple(got) == tuple(expect)
        print("%s %-14s 出码=%s 设计=%s" % ("OK  " if good else "FAIL", ident, got, expect))
        ok = ok and good

    # ③ 两个模态默认必须是隐藏的
    for ident, expect in (("overlay_root", 1), ("dlg_root", 1)):
        i = src.find("objects.%s = obj;" % ident)
        seg = src[i:i + 300]
        hidden = "LV_OBJ_FLAG_HIDDEN" in seg
        print("%s %-14s 默认隐藏=%s" % ("OK  " if hidden else "FAIL", ident, hidden))
        ok = ok and hidden

    # ④ 出码几何相等 ≠ 渲染位置相等（实测教训：键盘整块下移 92px 出屏）
    #    lv_keyboard 构造函数写死 align=BOTTOM_MID，set_pos 会被当成"相对底边
    #    中点的偏移"；lv_textarea 的 oneLineMode 会把 height 改成 LV_SIZE_CONTENT。
    #    这两处必须有显式覆盖，否则设计坐标全是纸面值。
    def seg_of(ident, n=900):
        i = src.find("objects.%s = obj;" % ident)
        return "" if i < 0 else src[i:i + n]

    guards = [
        ("kb_main", "align 已覆盖为 TOP_LEFT",
         "lv_obj_set_style_align(obj, LV_ALIGN_TOP_LEFT",
         "lv_keyboard 构造函数默认 BOTTOM_MID，不覆盖则 set_pos 语义变成偏移量"),
        ("pwd_ta", "pad_top=%d 撑住 one-line 高度" % BE.SHEET_TA_PAD,
         "lv_obj_set_style_pad_top(obj, %d," % BE.SHEET_TA_PAD,
         "oneLineMode 强制 height=LV_SIZE_CONTENT，只能用上下 pad 撑"),
    ]
    for ident, what, needle, why in guards:
        hit = needle in seg_of(ident)
        print("%s %-14s %s" % ("OK  " if hit else "FAIL", ident,
                               what if hit else "缺 %s（%s）" % (needle, why)))
        ok = ok and hit
    return ok


def main():
    skip_cli = "--skip-cli" in sys.argv
    with_sim = "--with-sim" in sys.argv

    for name, cmd, cwd, required in STEPS:
        if skip_cli and "cli_build" in " ".join(cmd):
            print("\nSKIP: %s（--skip-cli）" % name)
            continue
        r = run(name, cmd, cwd, required)
        if r is False:
            sys.exit(1)
        if "cli_build" in " ".join(cmd):
            # CLI 刚跑完，立刻验产物（最贴近故障点的位置）
            if r and not check_artifacts():
                sys.exit(1)

    # 末尾再验一次（防后续步骤误删，如 gen_font 的孤儿清理）
    if not check_artifacts():
        sys.exit(1)
    if not check_no_flow():
        sys.exit(1)
    if not check_geometry():
        sys.exit(1)

    if with_sim:
        bat = os.path.join("design", "sim_cmake")
        print("\n=== [可选] PC 仿真编译 ===")
        p = subprocess.run(["cmd.exe", "/c", "run_sim.bat", "build"],
                           cwd=os.path.join(ROOT, bat), capture_output=True,
                           text=True, timeout=900, errors="replace")
        lines = (p.stdout or "").strip().splitlines()
        print("\n".join(lines[-8:]))
        if p.returncode != 0 or not any(
                "succeeded" in ln.lower() or "no work to do" in ln.lower()
                for ln in lines):
            print("FAIL: 仿真编译未成功")
            sys.exit(1)
        print("OK: 仿真编译通过")

    print("\n==== PREFLIGHT PASS ====")
    print("下一步：启动仿真截图，再跑 design/ui_check.py 与设计图对照（见 EEZ_WORKFLOW.md 第 5 节）")


if __name__ == "__main__":
    main()
