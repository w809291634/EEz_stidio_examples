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
SDL_BIN = r"D:\Program_Files\SDL2-2.32.4\x86_64-w64-mingw32\bin"

# 每一步：(名称, 命令, 工作目录, 是否必需)
# 注意顺序：build_example → cli_build → audit → check_project → gen_font
STEPS = [
    ("生成 .eez-project", [PY, "build_example.py"], ROOT, True),
    ("EEZ CLI 构建（含 flow 守卫）", [PY, "design/cli_build.py"], ROOT, True),
    ("逐字审计（文案 ⊆ 字体）", [PY, "design/audit_chars.py"], ROOT, True),
    ("静态自检 7 项", [PY, "design/check_project.py"], ROOT, True),
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


def check_layers():
    """[分层] native 树 == kit reference/12 轻量版（app 平铺四组 + platform 二选一）。

    只查机械可判的事：目录形态、include 依赖方向、pc/device 的宏互斥。
    分层靠嘴说，下一个改代码的人就会把业务塞进 view。"""
    print("\n=== [分层] native 树 == kit reference/12（轻量版）===")
    import io
    ok = True
    N = os.path.join(ROOT, "src", "native")

    need = ["app/wifi_model.h", "app/wifi_model.cpp",
            "app/wifi_view.h", "app/wifi_view.cpp",
            "app/wifi_events.cpp", "app/wifi_logic.h", "app/wifi_logic.cpp",
            "navigation/wifi_nav.h", "navigation/wifi_nav.cpp",
            "widgets/wifi_list/wifi_list.h", "widgets/wifi_list/wifi_list.cpp",
            "platform/wifi_platform.h",
            "platform/pc/wifi_platform_pc.cpp",
            "platform/pc/wifi_platform_win.cpp",
            "platform/pc/wifi_platform_win.h",
            "platform/device/wifi_platform_device.cpp"]
    miss = [p for p in need if not os.path.isfile(os.path.join(N, p))]
    print("%s native 树 %d 个必备文件齐全" % ("OK  " if not miss else "FAIL", len(need)))
    if miss:
        ok = False
        print("      缺: " + "; ".join(miss))

    # 新规范：app/ 保持平铺，不为功能新建子目录
    sub_dirs = [d for d in os.listdir(os.path.join(N, "app"))
                if os.path.isdir(os.path.join(N, "app", d))] if os.path.isdir(
        os.path.join(N, "app")) else ["<app/ 不存在>"]
    print("%s app/ 平铺（无功能子目录）" % ("OK  " if not sub_dirs else "FAIL"))
    if sub_dirs:
        ok = False
        print("      违例: app/ 下有子目录 %s（要拆分请在 app/ 内平铺加文件）" % sub_dirs)

    def targets(target):
        """目标既可以是目录（platform/、widgets/），也可以是平铺文件前缀（app/wifi_model）。"""
        d = os.path.join(N, target)
        if os.path.isdir(d):
            out = []
            for dirpath, _dirs, files in os.walk(d):
                out += [os.path.join(dirpath, f) for f in sorted(files)
                        if f.endswith((".c", ".cpp", ".h"))]
            return out
        return [d + e for e in (".h", ".cpp") if os.path.isfile(d + e)]

    import re

    def includes(path):
        """把 #include "x" 的目标规范化：既给全路径，也给裸文件名。
        只比前缀会漏掉 `#include "../../ui/screens.h"` 这种相对写法（反向测试抓到）。"""
        t = io.open(path, encoding="utf-8", errors="replace").read()
        out = set()
        for raw in re.findall(r'#\s*include\s*"([^"]+)"', t):
            p = raw.replace("\\", "/")
            while p.startswith("../"):
                p = p[3:]
            out.add(p)
            out.add(os.path.basename(p))
        return out

    # 依赖方向
    rules = [
        ("platform", ("lvgl.h", "screens.h"),
         "platform 只接命令/给快照，不得引用 LVGL 或 EEZ 对象"),
        ("app/wifi_model", ("lvgl.h", "wifi_platform.h"),
         "model 必须无 UI 无平台依赖，才能用无头断言验证"),
        ("app/wifi_logic", ("screens.h",),
         "logic 只做初始化与 tick，不读 objects.*"),
        ("navigation", ("app/wifi_model", "wifi_platform.h"),
         "navigation 只管去向，不读业务真值、不碰硬件接口"),
        ("widgets", ("app/wifi_model",),
         "widgets 读 io 快照、调 navigation，不直接改业务模型"),
    ]
    for target, needles, why in rules:
        bad = []
        for p in targets(target):
            incs = includes(p)
            for nd in needles:
                if any(i == nd or i.startswith(nd) for i in incs):
                    bad.append("%s→%s" % (os.path.relpath(p, N), nd))
        print("%s %-16s 依赖方向合规" % ("OK  " if not bad else "FAIL", target))
        if bad:
            ok = False
            print("      违例: " + ", ".join(bad) + "（%s）" % why)

    # 硬件符号只许出现在 platform/：业务层一旦直接叫 Wlan*/esp_wifi，换后端就没人接了
    hw = ("Wlan", "esp_wifi", "nvs_")
    bad = []
    for root in (N, os.path.join(ROOT, "src", "ui")):
        for dirpath, _dirs, files in os.walk(root):
            for f in sorted(files):
                if not f.endswith((".c", ".cpp", ".h")):
                    continue
                p = os.path.join(dirpath, f)
                if (os.sep + "platform" + os.sep) in p:
                    continue          # 硬件边界层，命中是它的职责
                t = io.open(p, encoding="utf-8", errors="replace").read()
                hit = [nd for nd in hw if nd in t]
                if hit:
                    bad.append("%s:%s" % (os.path.relpath(p, ROOT), ",".join(hit)))
    print("%s 硬件符号不外溢（platform 之外 0 命中）" % ("OK  " if not bad else "FAIL"))
    if bad:
        ok = False
        print("      违例: " + ", ".join(bad) + "（硬件名字只属于 platform/）")

    # pc / device 必须宏互斥，否则真机构建会撞同名符号。
    # ★ 只认行首预处理指令：正文注释里提到过宏名不算守卫（反向测试抓到）。
    guards = [("platform/pc/wifi_platform_pc.cpp", "#ifndef WIFI_PLATFORM_DEVICE"),
              ("platform/device/wifi_platform_device.cpp", "#ifdef WIFI_PLATFORM_DEVICE")]
    for rel, needle in guards:
        p = os.path.join(N, rel)
        hit = os.path.isfile(p) and any(
            ln.strip() == needle
            for ln in io.open(p, encoding="utf-8", errors="replace"))
        print("%s %-34s 宏互斥 %s" % ("OK  " if hit else "FAIL", rel, needle))
        ok = ok and hit
    return ok


def check_nav():
    """[⑦] 导航闭环断言：无窗口跑 main.exe，FAIL 计数直接决定门禁颜色。"""
    print("\n=== [⑦] 导航闭环断言（无窗口）===")
    exe_dir = os.path.join(ROOT, "design", "sim_cmake", "build_rel", "bin")
    env = dict(os.environ)
    env["PATH"] = env.get("PATH", "") + ";" + SDL_BIN
    env["SDL_VIDEODRIVER"] = "dummy"     # 不开桌面窗口；事件链与出图一致（P-0189）
    env["WIFI_NAVTEST"] = "1"
    # 门禁必须跑假世界：真接口（run_sim 双击时的默认）会真连网、真删 profile，
    # 而且"附近有哪些网/谁已连接"每次都变，断言就不可复现。设成假世界这件事要看得见。
    env["WIFI_PC_FAKE"] = "1"
    print("OK   门禁已强制假世界（WIFI_PC_FAKE=1），真接口不会被触发")
    try:
        q = subprocess.run([os.path.join(exe_dir, "main.exe")], cwd=exe_dir,
                           env=env, timeout=300, capture_output=True, text=True,
                           errors="replace")
    except OSError as e:
        print("FAIL: 起不了仿真可执行（先跑 --with-sim 或 run_sim.bat）：%s" % e)
        return False
    except subprocess.TimeoutExpired:
        print("FAIL: 导航断言超时（进程没自己退出）")
        return False
    res = [ln for ln in (q.stdout or "").splitlines() if "[NAV]" in ln]
    print("\n".join(res[-3:]) if res else "FAIL: 没有任何 [NAV] 输出")
    return q.returncode == 0 and any("FAIL 0" in ln for ln in res)


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
    if not check_layers():
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
        if not check_nav():
            print("FAIL: 导航闭环断言未全绿")
            sys.exit(1)
        print("OK: 导航闭环断言全绿")

    print("\n==== PREFLIGHT PASS ====")
    print("下一步：启动仿真截图，再跑 design/ui_check.py 与设计图对照（见 EEZ_WORKFLOW.md 第 5 节）")


if __name__ == "__main__":
    main()
