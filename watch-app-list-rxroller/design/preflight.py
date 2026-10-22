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

    # ---- 表盘外形：必须完全由 EEZ 属性面生成，native/仿真器不许插手 ----
    # （settings.general.circularDisplay 只是编辑器预览的 CSS，不进代码生成器，
    #   所以圆形靠控件级 radius + clip_corner，见 build_example.py 的 SCREEN_RADIUS）
    sc = read(os.path.join(UI, "screens.c"))
    main_blk = sc.split("objects.main = obj;")[-1].split("parent_obj")[0]
    check("主屏 radius 由 EEZ 生成（LV_RADIUS_CIRCLE=32767）",
          "lv_obj_set_style_radius(obj, 32767," in main_blk,
          "EEZ 没生成圆角 ⇒ 表盘又是方的")
    check("主屏 clip_corner 由 EEZ 生成",
          "lv_obj_set_style_clip_corner(obj, true," in main_blk,
          "只有 radius 不裁子对象 ⇒ 看着还是方的")
    check("native 侧没有偷偷补 radius/clip_corner",
          "clip_corner" not in read(os.path.join(NATIVE, "watch_list_native.c")),
          "遮罩被挪到 native 了，违反 EEZ 单一口径")

    # 外壳元素（标题/状态行）必须落在胶囊安全区内，否则会被圆角整个裁掉——实测踩过
    g = json.loads(read(PROJ))["settings"]["general"]
    W, H = int(g["displayWidth"]), int(g["displayHeight"])
    R = min(W, H) // 2

    def inside(x, y):
        if y <= R:      return (x - W / 2) ** 2 + (y - R) ** 2 <= R ** 2
        if y >= H - R:  return (x - W / 2) ** 2 + (y - (H - R)) ** 2 <= R ** 2
        return True

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "LVGLLabelWidget" and n.get("identifier"):
                yield n
            for v in n.values():
                yield from walk(v)
        elif isinstance(n, list):
            for v in n:
                yield from walk(v)

    labels = [w for w in walk(json.loads(read(PROJ)))
              if w.get("identifier") in ("lbl_title", "lbl_status")]
    for lb in labels:
        x, y = int(lb["left"]), int(lb["top"])
        # 查左上/右上两个角：它们离胶囊弧心最远，是会被裁的那个方向
        check("%s 落在胶囊安全区内 (%d,%d)" % (lb["identifier"], x, y),
              inside(x, y) and inside(x + int(lb["width"]), y),
              "会被圆角裁掉——标题/状态行必须往里挪")


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
def font_covered_codepoints():
    """从**实际烘出来的** ui_font_cn14.c 里解析它到底覆盖了哪些码点。

    ★ 为什么不能只比 build_example.FONT_CHARS：那是"声明值"。
      EEZ Studio 自己也会烘字体（GUI 构建会烘，CLI 不烘 —— 见 P-0140），
      它写出的 --range 列表和我们的 --symbols 列表是两份东西。
      拿声明比声明，字体被换掉时门禁会"因为错的理由通过"（实测踩过）。
    lv_font_conv 会在产物头部原样回显 `Opts: ...`，那就是这份字体的真实配方。
    """
    src = read(os.path.join(UI, "fonts", "ui_font_cn14.c"))
    opts = next((l for l in src.splitlines() if "Opts:" in l), "")
    cov = set()
    m = re.search(r"--(?:range|r)\s+(\S+)", opts)
    if m:
        for part in m.group(1).split(","):
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                cov |= set(range(int(a, 0), int(b, 0) + 1))
            else:
                cov.add(int(part, 0))
    m = re.search(r"--symbols\s+(\S+)", opts)
    if m:
        cov |= {ord(c) for c in m.group(1)}
    return cov, opts


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

    # ★ 关键一条：比的是**字体文件本身**，不是声明
    cov, opts = font_covered_codepoints()
    check("字体产物在位且头部带 Opts 配方", bool(opts),
          "解析不到 `Opts:` 行 ⇒ 无法证明这份 .c 覆盖了哪些码点")
    absent = sorted({ord(c) for c in used} - cov)
    check("实际字体文件覆盖 native 用字 %d 个（解析自 ui_font_cn14.c 的 Opts）" % len(used),
          not absent,
          "字体缺字 %s ⇒ 这份 .c 不是按我们的字符集烘的（EEZ GUI 会自己烘，注意别被覆盖）"
          % "".join(chr(c) for c in absent))
    declared = {ord(c) for c in be.FONT_CHARS}
    check("字体实际覆盖码点数(%d) == 声明字符集数(%d)" % (len(cov), len(declared)),
          cov == declared,
          "只被声明有、字体里没有：%s ｜ 只在字体里：%s" % (
              "".join(chr(c) for c in sorted(declared - cov)),
              "".join(chr(c) for c in sorted(cov - declared))))



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

    # ★ 改动必须"就地可见"：翻到 src/native/rxroller/ 就能看到改了什么，
    #   不用先知道 PORTLOG 在哪。同时防文档腐化——账单数字变了而文档没跟上就 FAIL。
    import difflib
    # n=3 才能和 `diff -u` 的 hunk 数对齐；n=0 会把相邻改动拆成更多块（实测 19 vs 14）
    hunks = sum(1 for l in difflib.unified_diff(
        read(orig).replace("\r\n", "\n").splitlines(True),
        read(ported).replace("\r\n", "\n").splitlines(True),
        n=3) if l.startswith("@@"))
    note = os.path.join(RX_DIR, "README.md")
    check("目录内有就地说明件 src/native/rxroller/README.md",
          os.path.exists(note), "打开目录看不出这里被改过")
    dexport = os.path.join(RX_DIR, "Rxroller_port.diff")
    check("目录内有逐字对照件 Rxroller_port.diff", os.path.exists(dexport),
          "缺导出件（跑 python design/compare_upstream.py --diff 生成）")
    for name, path in (("目录说明件", note),
                       ("PORTLOG", os.path.join(ROOT, "PORTLOG.md"))):
        if not os.path.exists(path):
            continue
        txt = read(path)
        # 取文档里出现的**每一个** "<N> hunks"，全部必须等于实测。
        # 只判"有没有 14 hunks 这个串"是假门禁：文里别处还有一个，改错一处照样绿。
        found = [int(m) for m in re.findall(r"(\d+)\s+hunks", txt)]
        check("%s 记的 hunk 数全等于实测 %d（文中 %d 处）" % (
                  name, hunks, len(found)),
              bool(found) and all(f == hunks for f in found),
              "账单腐化：文档里出现了 %s，实测是 %d" % (sorted(set(found)), hunks))


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
    check("十一条行为断言在夹具里",
          all(k in mainc for k in ("中心行 = 10", "缩放最大", "单调衰减",
                                   "快滑一次跨多行", "钳住不越界",
                                   "横向 1/3", "起步不吸在首行",
                                   "行程不限", "弹回顶部第 n 个",
                                   "弹回底部倒数第 n 个")),
          "断言被删了")
    check("自证模式摘掉真鼠标",
          'WATCH_ALLOWMOUSE' in mainc and 'lv_indev_delete(mouse)' in mainc,
          "人手一滑就把断言量歪（实测污染过一次：10->13 被改成 11->15）")
    # ★ 手势回调必须同时挂行和滚轮根对象。屏外回收把远处行置 HIDDEN，
    #   LVGL 跳过隐藏对象 ⇒ 按在"隐藏行/空白"上时目标是根对象，只挂行会**静默失效**
    #   （2026-10-22 用户报"滑到最上面不返回"就是这个，行级 API 夹具测不到）。
    nativec = read(os.path.join(NATIVE, "watch_list_native.c"))
    check("手势回调也挂在滚轮根对象上（否则隐藏区按下时静默失效）",
          all(("lv_obj_add_event_cb(s_wheel, %s," % fn) in nativec
              for fn in ("row_press_cb", "row_pressing_cb",
                         "row_released_cb", "row_press_lost_cb")),
          "只挂在行上：按在隐藏行/空白处时快滑与松手弹回全不触发")
    check("有走真 indev 的合成拖动夹具 WATCH_DRAGTEST",
          'WATCH_DRAGTEST' in mainc and 'SDL_PushEvent' in mainc
          and 'lv_sdl_window_get_window' in mainc,
          "行级 API 夹具测不到手势链路，必须能合成 SDL 级拖动")


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
