# -*- coding: utf-8 -*-
"""交付门禁 D1–D8（第④步交付前必跑；任何一条 FAIL 都不许交付）。

用法：python design/delivery_gate.py            # 跑全部
      python design/delivery_gate.py --b1-ok    # 人工完成画布比对后打确认标记
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

PROJ = os.path.join(ROOT, "w78-smart-home.eez-project")
B1_MARK = os.path.join(HERE, ".b1_confirmed")


def run(cmd):
    r = subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def d1_struct():
    ok, out = run(["design/eez_check.py"])
    return ok, "eez_check（页尺寸/控件数/框/文本/字体引用/ID 唯一）"


def d2_text():
    sys.path.insert(0, HERE)
    import simple_control as sc
    import eez_gen as g
    sub = {k: v for k, v in g.SUBST.items()}
    fix = lambda t: "".join(sub.get(c, c) for c in t)
    design = [fix(m.group(1)) for m in re.finditer(r"<text[^>]*>([^<]*)</text>", sc.main_frame())
              if m.group(1).strip()]
    proj = json.load(io.open(PROJ, encoding="utf-8"))
    got = []

    def walk(n):
        if n["type"] == "LVGLLabelWidget" and n.get("text"):
            got.append(n["text"])
        for c in n.get("children", []):
            walk(c)
    for c in proj["userPages"][0]["components"][0]["children"]:
        walk(c)
    miss = [t for t in design if t not in got]
    return (not miss), "文本覆盖 设计 %d / 工程 %d ｜ 未覆盖 %d %s" % (
        len(design), len(got), len(miss), miss[:3] if miss else "")


def d3_font():
    proj = json.load(io.open(PROJ, encoding="utf-8"))
    fonts = proj.get("fonts", [])
    files = glob.glob(os.path.join(ROOT, "src", "ui", "fonts", "ui_font_*.c"))
    names = {f["name"] for f in fonts}
    have = {os.path.basename(f)[len("ui_font_"):-2] for f in files}
    sizes = {f["source"]["size"] for f in fonts}
    # 同字号可以有多档（设计子集 + 运行时 GB2312 字库），按「每条都有 .c」核
    ok = bool(fonts) and names <= have and len(files) == len(names)
    return ok, "字体条目 %d（%d 个字号）｜ 烘出的 .c %d 个" % (len(fonts), len(sizes), len(files))


def d4_build():
    ok, out = run(["design/cli_build.py"])
    built = len(re.findall(r'File ".+" built', out))
    good = ok and built >= 12 and "Build successfully finished" in out
    # ★ 构建会清空 src/ui/fonts（headless 不烘字体）→ 必须构建后再烘一次
    baker = os.path.join(os.path.expanduser("~"), "Desktop", "local_knowledge_base",
                         "embedded", "EEZ Studio_ui_debug_kit", "tools", "eez_font_bake.py")
    if good and os.path.isfile(baker):
        run([baker, PROJ, os.path.join(ROOT, "src", "ui", "fonts")])
    # 真编译：生成的 C 必须过 gcc 语法检查（EEZ 生成 ≠ C 编译）
    srcs = [os.path.join(ROOT, "src", "ui", n)
            for n in ("screens.c", "ui.c", "styles.c", "images.c")]
    srcs += glob.glob(os.path.join(ROOT, "src", "ui", "fonts", "*.c"))
    conf = os.path.join(HERE, "lv_conf.h")
    incs = ["-I", HERE, "-I", os.path.join(os.path.dirname(ROOT), "apl_lvgl_v9_4"),
            "-I", os.path.join(ROOT, "src", "ui")]
    errs = []
    for f in srcs:
        if not os.path.isfile(f):
            errs.append("缺少 " + os.path.basename(f))
            continue
        r = subprocess.run(["gcc", "-fsyntax-only", "-DLV_CONF_INCLUDE_SIMPLE", *incs, f],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            errs.append("%s: %s" % (os.path.basename(f), (r.stderr or "").strip().splitlines()[:1]))
    good = good and not errs
    return good, "构建 %d 行 built ｜ C 编译 %d 个文件 %s" % (
        built, len(srcs), "全过" if not errs else "报错：" + str(errs[:2]))


def d5_canvas():
    coef_file = os.path.join(ROOT, "designer_annotated", "d5_相似度.txt")
    coef = ""
    if os.path.isfile(coef_file):
        rows = [l.strip() for l in io.open(coef_file, encoding="utf-8") if l.strip()]
        coef = rows[0] if rows else ""
    if os.path.isfile(B1_MARK):
        stamp = io.open(B1_MARK, encoding="utf-8").read().strip()
        return True, "画布比对已确认（%s）｜ %s" % (stamp, coef or "无相似度记录")
    if coef:
        return False, "%s ｜ 待人工确认后 `--b1-ok`" % coef
    return False, "未做画布比对：跑 `python design/d5_pages.py` 再人工确认"


def d6_nav():
    ok, out = run(["design/nav_audit.py"])
    tail = [l for l in out.splitlines() if l.startswith("[NAV_AUDIT]")]
    return ok, (tail[0] if tail else "nav_audit 输出异常")


def d7_clean():
    """只卡 tmp（交付件不许进）；__pycache__ 是跑脚本的副产物，仅提示。"""
    tmp = os.path.join(ROOT, "tmp")
    junk = os.listdir(tmp) if os.path.isdir(tmp) else []
    cache = os.path.isdir(os.path.join(ROOT, "design", "__pycache__"))
    ok = not junk
    return ok, "tmp：%s ｜ __pycache__：%s" % (
        "空" if ok else "未清 %s" % junk[:3], "有（可忽略）" if cache else "无")


def d8_trace():
    kit = r"C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEz Studio_ui_debug_kit"
    log = os.path.join(kit, "prompts", "PROMPT_LOG.md")
    if not os.path.isfile(log):
        return True, "提示词日志不在本机（跳过）"
    return True, "留痕在 %s 末尾（人工确认本轮已写）" % "PROMPT_LOG.md"


def d9_mem():
    ok, out = run(["design/mem_report.py"])
    m = re.search(r"\[MEM-BIN\] fonts=(\d+)KB ui=(\d+)KB ram=(\d+)KB(?: target=(\w+))?(?: opt=(\S+))?", out)
    if not m:
        return False, "资源账未产出 [MEM-BIN] 行"
    fk, uk, rk = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    tgt = m.group(4) or "pc"
    opt = m.group(5) or "?"
    budget = {"fonts_mb": 0.5, "ui_mb": 1.0}
    bf = os.path.join(HERE, "mem_budget.json")
    if os.path.isfile(bf):
        budget.update(json.load(io.open(bf, encoding="utf-8")))
    good = fk <= budget["fonts_mb"] * 1024 and uk <= budget["ui_mb"] * 1024
    label = "ESP32 工具链估算（只编译，%s）" % opt if tgt.startswith("esp32") else "PC 上限（-O1）"
    return good and ok, "%s Flash %dKB（字体 %d）+ RAM %dKB（预算 %.0f/%.0fKB）" % (
        label, uk, fk, rk, budget["fonts_mb"] * 1024, budget["ui_mb"] * 1024)


def main():
    if "--b1-ok" in sys.argv:
        i = sys.argv.index("--b1-ok")
        note = sys.argv[i + 1] if len(sys.argv) > i + 1 else "已核对"
        io.open(B1_MARK, "w", encoding="utf-8", newline="\n").write(note)
        print("已记录画布比对确认：", note)
        return
    # D4 会重新构建（清空 fonts 目录）并在构建后重烘，所以必须先跑 D4 再统计字体
    r4 = d4_build()
    rows = [("D1 结构对账", d1_struct()), ("D2 文本覆盖", d2_text()),
            ("D3 字体 F1–F7", d3_font()), ("D4 编译", r4),
            ("D5 画布比对", d5_canvas()), ("D6 跳转闭环", d6_nav()),
            ("D7 过程件清理", d7_clean()), ("D8 留痕", d8_trace()),
            ("D9 内存账", d9_mem())]
    print("== 交付门禁 ==")
    bad = 0
    for name, (ok, msg) in rows:
        print("  %-14s %s  %s" % (name, "PASS" if ok else "FAIL", msg))
        bad += 0 if ok else 1
    print("[DELIVERY] " + ("PASS" if not bad else "FAIL（%d 项未过）" % bad))
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
