# -*- coding: utf-8 -*-
"""preflight.py —— 本工程交付前的硬门禁（每条都要能反查，不靠口头）

用法：python design/preflight.py        （全跑，任一 FAIL 即退出码 1）

为什么这几条是门禁而不是"建议"：
  1) no-flow 口径一旦破功（flowSupport 被改回 true），本工程"EEZ 只画外壳、
     主体在 native"的立论就没了，而且产物形态会变；
  2) 分辨率三处对齐是移植件的命门——穹顶曲线以屏心为不动点，EEZ 屏、
     compat 宏、仿真窗口任一不一致，中心项就会偏；
  3) native 往屏上写的中文（"已打开: xxx"）**不在 EEZ 工程 JSON 里**，
     audit_chars.py 看不见它 ⇒ 必须单独扫 native 源码比对字体子集，
     否则又是一次"构建 0 错、屏上豆腐"；
  4) 移植件必须可审计：残留的 RT-Thread / GUI 框架符号要能在源码层查干不干净。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJ = os.path.join(ROOT, "watch-app-list-no-flow.eez-project")
NATIVE = os.path.join(ROOT, "src", "native")
UI = os.path.join(ROOT, "src", "ui")

sys.path.insert(0, ROOT)

FAILS = []


def check(name, ok, detail):
    print("%-4s %s%s" % ("OK" if ok else "FAIL", name, "" if ok else "  -> " + detail))
    if not ok:
        FAILS.append(name)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def strip_comments(body):
    """注释里的中文不上屏、注释里提到的框架名也不算残留——扫之前先去注释。
    逐字符扫而不是正则，是为了不被 /* 出现在字符串里 / 字符串里出现 // 骗到。"""
    out, i, n = [], 0, len(body)
    while i < n:
        two = body[i:i + 2]
        if two == "//":
            while i < n and body[i] != "\n":
                i += 1
        elif two == "/*":
            j = body.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif body[i] == '"':                       # 字符串字面量原样保留
            j = i + 1
            while j < n and body[j] != '"':
                j += 2 if body[j] == "\\" else 1
            out.append(body[i:j + 1])
            i = j + 1
        else:
            out.append(body[i])
            i += 1
    return "".join(out)


# ---- 1. no-flow 判据 ----
def check_no_flow():
    print("\n=== [1] no-flow 判据 ===")
    for rel in ("eez-flow.cpp", "eez-flow.h"):
        check("EEZ 不得发射 %s" % rel, not os.path.exists(os.path.join(UI, rel)),
              "%s 存在 → settings.general.flowSupport 被改回 true 了" % rel)
    ui_c = read(os.path.join(UI, "ui.c"))
    check("ui.c 走 create_screens() 分支", "create_screens()" in ui_c
          and "eez_flow_init" not in ui_c, "ui.c 里仍是 flow 版入口")
    h = read(os.path.join(UI, "screens.h"))
    for ident in ("list_host", "lbl_status", "lbl_title"):
        check("objects.%s 在位" % ident, ident in h, "EEZ 屏上没有这个控件")


# ---- 2. 分辨率三处对齐 ----
def check_resolution():
    print("\n=== [2] 分辨率三处对齐（EEZ / compat / 仿真窗口）===")
    data = json.loads(read(PROJ))
    g = data["settings"]["general"]
    ew, eh = int(g["displayWidth"]), int(g["displayHeight"])
    compat = read(os.path.join(NATIVE, "sifli_compat.h"))
    mw = re.search(r"#define\s+WATCH_HOR_RES\s+(\d+)", compat)
    mh = re.search(r"#define\s+WATCH_VER_RES\s+(\d+)", compat)
    mainc = read(os.path.join(HERE, "sim_cmake", "main.c"))
    sw = re.search(r"#define\s+SIM_W\s+(\d+)", mainc)
    sh = re.search(r"#define\s+SIM_H\s+(\d+)", mainc)
    ok = (mw and mh and sw and sh
          and (int(mw.group(1)), int(mh.group(1))) == (ew, eh)
          and (int(sw.group(1)), int(sh.group(1))) == (ew, eh))
    check("EEZ %dx%d == compat %s == SIM %s" % (
        ew, eh,
        (mw.group(1), mh.group(1)) if mw else "?",
        (sw.group(1), sh.group(1)) if sw else "?"),
        ok, "三处不一致：穹顶曲线的屏心与视口中心会错开")


# ---- 3. native 往屏上写的中文必须在字体子集里 ----
def check_native_font():
    print("\n=== [3] native 侧中文字体覆盖 ===")
    import build_example as be
    data = json.loads(read(PROJ))
    used = set()
    for fn in sorted(os.listdir(NATIVE)):
        if not fn.endswith((".c", ".h")):
            continue
        body = strip_comments(read(os.path.join(NATIVE, fn)))
        # 上屏的判定：出现在 lv_label_set_text* 能拿到的字面量里。
        # 逐行筛掉打日志的那几行（printf/rt_kprintf/LOG_x 的中文进控制台，不进屏），
        # 否则 #define WATCH_STATUS_FMT "已打开: %s" 这种真会上屏的也会被漏判。
        for line in body.splitlines():
            if re.match(r'\s*(printf|rt_kprintf|LOG_[IE])\b', line):
                continue
            for lit in re.findall(r'"(?:[^"\\\n]|\\.)*"', line):
                used |= {c for c in lit if ord(c) > 0x7F}
    missing = sorted(used - set(be.FONT_CHARS))
    check("native 字面量用字 %d 个，全部在字体子集内" % len(used), not missing,
          "缺字 %s ⇒ 加进 build_example.py 的 UI_CJK 后重跑生成链" % "".join(missing))


# ---- 4. 移植件可审计：框架残留清零 ----
def check_port_clean():
    print("\n=== [4] 移植件依赖残留 ===")
    body = read(os.path.join(NATIVE, "watch_app_list.c"))
    code = strip_comments(body)          # 注释里提到框架名不算残留
    for pat in ("#include <rtthread.h>", "#include <rtdevice.h>",
                "gui_app_fwk.h", "BUILTIN_APP_EXPORT", "littlevgl2rtt.h",
                "cell_transform.h", "LV_EXT_IMG_GET", "monkey_mode"):
        check("无残留 %s" % pat, pat not in code, "生效代码里还有 " + pat)
    check("PORT: 标记在位（改动可审计）", body.count("PORT:") >= 5,
          "PORT 标记太少，diff 说不清动了什么")
    check("算法主体未被改写（保留原函数名）",
          all(n in body for n in ("layout_get_icon_col_row_by_idx",
                                  "layout_icon_transform",
                                  "mainmainmenu_cell_transform",
                                  "mainmenu_cell_predict_focus_icon")),
          "移植件核心函数缺失")


# ---- 5. 应用表与图标一一对应 ----
def check_icons():
    print("\n=== [5] 应用表 × 图标 ===")
    compat_c = read(os.path.join(NATIVE, "sifli_compat.c"))
    ids = re.findall(r'\{\s*"([a-z_0-9]+)",\s*ICON_PTR\([a-z_0-9]+\)\s*\}', compat_c)
    check("应用表非空", len(ids) >= 8, "只找到 %d 项" % len(ids))
    missing = [i for i in ids
               if not os.path.exists(os.path.join(NATIVE, "icons", "img_app_%s.c" % i))]
    check("%d 个图标全部已生成" % len(ids), not missing, "缺 %s" % missing)
    check("第 0 项是 clock（原文件的固定规则）", ids and ids[0] == "clock",
          "clock 不在第 0 位，蜂窝中心会错位")


# ---- 6. 仿真器取证开关 ----
def check_snapshot():
    print("\n=== [6] 无头自证取证面 ===")
    conf = read(os.path.join(HERE, "sim_cmake", "lv_conf.h"))
    check("LV_USE_SNAPSHOT 1", "#define LV_USE_SNAPSHOT 1" in conf,
          "拍不了屏，中文渲染与观感就没有可核对的证据")
    mainc = read(os.path.join(HERE, "sim_cmake", "main.c"))
    check("WATCH_AUTOTEST 钩子在主循环里被调用",
          "autotest_hooks();" in mainc, "钩子没接进 while(1)")


def main():
    if not os.path.exists(PROJ):
        sys.exit("先跑 build_example.py + design/cli_build.py，再来跑 preflight")
    check_no_flow()
    check_resolution()
    check_native_font()
    check_port_clean()
    check_icons()
    check_snapshot()
    print("\n=== 结论 ===")
    if FAILS:
        print("%d 条 FAIL：%s" % (len(FAILS), " | ".join(FAILS)))
        sys.exit(1)
    print("全部通过")


if __name__ == "__main__":
    main()
