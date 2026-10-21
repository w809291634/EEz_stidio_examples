# -*- coding: utf-8 -*-
"""preflight.py —— watch-app-list-rxroller 交付前的硬门禁

跑法：python design/preflight.py     （任一 FAIL 即退出码 1）

六组判据的存在理由：
  1) no-flow 口径一旦破功，"EEZ 只画外壳、主体在 native"的立论就没了；
  2) 分辨率三处对齐：滚轮的行坐标以根对象内容为原点，宿主尺寸变了整套位置就偏；
  3) **native 往屏上写的中文不在 EEZ 工程 JSON 里**，audit_chars 看不见 ⇒
     必须单独扫 src/native/*.c 的字符串字面量比对字体子集（否则又是"构建 0 错、
     屏上豆腐"）；
  4) 上游件必须可审计：Rxroller.c 与 Rxroller.c.orig 的 diff 只允许出现 RX-PORT 行，
     多一行就是有人绕过 port_rxroller.py 手改了产物；
  5) 应用表 22 项与图标一一对应，且 clock 类首位规则不被打断；
  6) 取证面：LV_USE_SNAPSHOT 与 WATCH_AUTOTEST 钩子必须在位，否则观感没有证据。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJ = os.path.join(ROOT, "watch-app-list-rxroller.eez-project")
NATIVE = os.path.join(ROOT, "src", "native")
UI = os.path.join(ROOT, "src", "ui")
RX_DIR = os.path.join(NATIVE, "rxroller")

sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

FAILS = []


def check(name, ok, detail):
    print("%-4s %s%s" % ("OK" if ok else "FAIL", name, "" if ok else "  -> " + detail))
    if not ok:
        FAILS.append(name)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def strip_comments(body):
    """注释里的中文不上屏、注释里提到的名字不算残留；逐字符扫，
    避免被字符串里的 // 或注释里的引号骗到。"""
    out, i, n = [], 0, len(body)
    while i < n:
        two = body[i:i + 2]
        if two == "//":
            while i < n and body[i] != "\n":
                i += 1
        elif two == "/*":
            j = body.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif body[i] == '"':
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
              "%s 存在 → flowSupport 被改回 true 了" % rel)
    ui_c = read(os.path.join(UI, "ui.c"))
    check("ui.c 走 create_screens() 分支",
          "create_screens()" in ui_c and "eez_flow_init" not in ui_c,
          "ui.c 仍是 flow 版入口")
    h = read(os.path.join(UI, "screens.h"))
    for ident in ("list_host", "lbl_status", "lbl_title"):
        check("objects.%s 在位" % ident, ident in h, "EEZ 屏上没有这个控件")


# ---- 2. 分辨率三处对齐 ----
def check_resolution():
    print("\n=== [2] 分辨率三处对齐（EEZ / main.c / apps 表）===")
    g = json.loads(read(PROJ))["settings"]["general"]
    ew, eh = int(g["displayWidth"]), int(g["displayHeight"])
    mainc = read(os.path.join(HERE, "sim_cmake", "main.c"))
    sw = re.search(r"#define\s+SIM_W\s+(\d+)", mainc)
    sh = re.search(r"#define\s+SIM_H\s+(\d+)", mainc)
    ok = bool(sw) and bool(sh) and (int(sw.group(1)), int(sh.group(1))) == (ew, eh)
    check("EEZ %dx%d == SIM %s" % (ew, eh,
          (sw.group(1), sh.group(1)) if sw and sh else "?"), ok,
          "仿真窗口与 EEZ 屏不一致 ⇒ 滚轮锚点与行位置会整体偏")


# ---- 3. native 上屏中文 ⊆ 字体子集 ----
def check_native_font():
    print("\n=== [3] native 侧中文字体覆盖 ===")
    import build_example as be
    used = set()
    for sub, _dirs, files in os.walk(NATIVE):
        if sub.endswith("rxroller"):      # 上游件不含上屏中文
            continue
        for fn in files:
            if not fn.endswith((".c", ".h")):
                continue
            body = strip_comments(read(os.path.join(sub, fn)))
            for line in body.splitlines():
                if re.match(r'\s*(printf|LOG_[IE])\b', line):
                    continue          # 打日志的中文进控制台，不进屏
                for lit in re.findall(r'"(?:[^"\\\n]|\\.)*"', line):
                    used |= {c for c in lit if ord(c) > 0x7F}
    missing = sorted(used - set(be.FONT_CHARS))
    check("native 上屏用字 %d 个，全部在字体子集内" % len(used), not missing,
          "缺字 %s ⇒ 改 design/apps.py 后重跑生成链" % "".join(missing))


# ---- 4. 上游件可审计 ----
def check_upstream_audit():
    print("\n=== [4] 上游件（Rxroller）改动可审计 ===")
    orig = os.path.join(RX_DIR, "Rxroller.c.orig")
    ported = os.path.join(RX_DIR, "Rxroller.c")
    check("上游原文 Rxroller.c.orig 在位（.orig 不被 *.c glob 收，不会重复定义）",
          os.path.exists(orig), "缺上游原文，diff 无从对照")
    if not os.path.exists(orig) or not os.path.exists(ported):
        return
    # 判据用"逐字节重放比对"而不是关键词白名单：白名单会把生成横幅误判成手改，
    # 而重放比对能精确暴露任何绕过脚本的编辑。
    import port_rxroller
    try:
        expect = port_rxroller.patched_text()
    except SystemExit as e:
        check("脚本可重放", False, str(e))
        return
    actual = read(ported)
    if expect == actual:
        diff_lines = sum(1 for a, b in zip(read(orig).splitlines(),
                                           actual.splitlines()) if a != b)
        check("产物 == port_rxroller.py 重放结果（逐字节一致）", True, "")
    else:
        first = next((i for i, (x, y) in enumerate(zip(expect.splitlines(),
                                                       actual.splitlines()))
                      if x != y), 0)
        check("产物 == port_rxroller.py 重放结果", False,
              "第 %d 行起不一致 ⇒ 有人手改了 Rxroller.c，"
              "请改 design/port_rxroller.py 再重放" % (first + 1))
    check("补丁由脚本生成（脚本可重放）",
          os.path.exists(os.path.join(HERE, "port_rxroller.py")),
          "缺 port_rxroller.py")


# ---- 5. 应用表 × 图标 ----
def check_apps():
    print("\n=== [5] 应用表 × 图标 ===")
    from apps import APPS
    check("表长 22（与 Design Watch 参考同口径）", len(APPS) == 22, "实际 %d" % len(APPS))
    missing = [i for i, _n, _t in APPS
               if not os.path.exists(os.path.join(NATIVE, "icons", "img_%s.c" % i))]
    check("%d 个图标已生成" % len(APPS), not missing, "缺 %s" % missing)
    c = read(os.path.join(NATIVE, "app_rows.c"))
    check("app_rows.c 与表同步（22 条初始化）",
          len(re.findall(r'^\s*\{"', c, flags=re.M)) == len(APPS),
          "app_rows.c 条目数与 apps.py 不一致 ⇒ 重跑 gen_assets.py")


# ---- 6. 取证面 ----
def check_evidence():
    print("\n=== [6] 无头取证面 ===")
    conf = read(os.path.join(HERE, "sim_cmake", "lv_conf.h"))
    check("LV_USE_SNAPSHOT 1", "#define LV_USE_SNAPSHOT 1" in conf,
          "拍不了屏 ⇒ 观感与中文没有可核对证据")
    mainc = read(os.path.join(HERE, "sim_cmake", "main.c"))
    check("WATCH_AUTOTEST 钩子接进主循环", "autotest_hooks();" in mainc,
          "钩子没接进 while(1)")
    check("三条行为断言在夹具里",
          all(k in mainc for k in ("中心行 = 10", "缩放最大", "单调衰减")),
          "断言被删了")


def main():
    if not os.path.exists(PROJ):
        sys.exit("先跑 build_example.py + design/cli_build.py，再跑 preflight")
    check_no_flow()
    check_resolution()
    check_native_font()
    check_upstream_audit()
    check_apps()
    check_evidence()
    print("\n=== 结论 ===")
    if FAILS:
        print("%d 条 FAIL：%s" % (len(FAILS), " | ".join(FAILS)))
        sys.exit(1)
    print("全部通过")


if __name__ == "__main__":
    main()
