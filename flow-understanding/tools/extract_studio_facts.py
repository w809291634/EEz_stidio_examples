#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_studio_facts.py —— 从装机版 EEZ Studio 里抽出**权威事实**，并与手册对账（只读，不改任何东西）。

为什么需要它：手册（784 页）在 0.29 上已经**滞后且不全**——
实测它列的 A43 LVGL 子动作是 63 项，装机版注册表里是 **65 项**（多 `objGetDisplayX/Y`）。
判"EEZ 能不能做 X"必须看三层证据，本脚本负责前两层 + 手册对账：

  1) 面板层：`enabledInComponentPalette` 谓词 → LVGL 工程能不能拖出这个件；
  2) 注册表层：`registerAction({...})` → A43 LVGL 动作的子动作全清单（id/分组/属性）；
  3) 运行时层：生成的 C++ 里是否真有实现 → 只能靠实际 CLI 构建验（见 EXAMPLE_PLAN 示例②③）。

用法：
    python flow-understanding/tools/extract_studio_facts.py [app.asar 路径] [手册全文 txt 路径]
    （默认路径均为本机路径 —— ★ 每机不同，换机器请传自己的路径）

输出（写到 flow-understanding/notes/）：
    _lvgl_action_registry_extract.txt   A43 子动作注册表（65 项）
    _lvgl_palette_availability.txt      每个 Flow 件在 LVGL 工程的可用性判定
    _manual_vs_registry_diff.txt        手册 A43 与装机注册表的差集（谁滞后）
"""
import os
import re
import sys

DEFAULT_ASAR = r"C:\Users\yjt54\AppData\Local\Programs\eezstudio\resources\app.asar"
DEFAULT_MANUAL = (r"C:\Users\yjt54\Desktop\local_knowledge_base\embedded"
                  r"\EEZ Studio_ui_debug_kit\reference_guide_raw.txt")
HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(os.path.dirname(HERE), "notes")


# 面板谓词 → 判定文字
RULES = [
    ('"lvgl"!==e', "LVGL 禁用（面板里拖不出来）"),
    ('"lvgl"===e', "LVGL 专属"),
    ('"dashboard"===e', "仅 Dashboard"),
    ("isEezFlowLite", "面板允许（LVGL 不是 FlowLite）→ 运行时需实测"),
    ('"eez-gui-lite"!==e', "面板允许（除 eez-gui-lite）"),
    ("DEFAULT_ALL", "无谓词 = 全工程类型可拖出 → 运行时需实测"),
]


def classify(pred):
    for needle, text in RULES:
        if needle in pred:
            return text
    return "未归类：" + pred[:60]


def load(asar_path):
    if not os.path.exists(asar_path):
        sys.exit("找不到 app.asar：%s\n→ 用 `python 本脚本 <你的 app.asar 路径>` 指定" % asar_path)
    with open(asar_path, "rb") as f:
        return f.read().decode("utf-8", "replace")


def registry(data):
    rows = []
    for m in re.finditer(r'registerAction\)\(\{id:', data):
        blk = data[m.start():m.start() + 1400]
        fid = re.search(r'id:(\d+)', blk)
        nm = re.search(r'name:"([^"]+)"', blk)
        grp = re.search(r'group:"([^"]+)"', blk)
        props = re.search(r'properties:\[([^\]]*)\]', blk)
        names = sorted(set(n for n in re.findall(r'\{name:"([^"]+)"', props.group(1)) if n != "type")) if props else []
        rows.append((int(fid.group(1)) if fid else -1,
                     nm.group(1) if nm else "?",
                     grp.group(1) if grp else "?",
                     " ".join(names)))
    return sorted(set(rows))


def palette(data):
    anchors = [m.end() for m in re.finditer(r'ActionComponent\.classInfo,\{', data)]
    rows = []
    for i, st in enumerate(anchors):
        blk = data[st:min(anchors[i + 1] if i + 1 < len(anchors) else len(data), st + 4000)]
        fid = re.search(r'flowComponentId:component_types_1\.(\w+)', blk)
        pm = re.search(r'enabledInComponentPalette:', blk)
        if pm:
            rest = blk[pm.end():]
            cuts = [rest.find(x) for x in (',properties:', ',label:', ',icon:', ',defaultValue:',
                                           ',beforeLoadHook:', ',onAfterPaste') if rest.find(x) >= 0]
            pred = rest[:min(cuts)] if cuts else rest[:160]
        else:
            pred = "DEFAULT_ALL"
        rows.append((fid.group(1) if fid else "?", pred.strip()))
    out = {}
    for fid, pred in rows:
        out.setdefault(fid, pred)
    return sorted(out.items())


def native_var_types(data):
    m = re.search(r'isLVGL\(\)\{return!0\}.{0,400}?isVariableTypeSupportedAsNative\(e\)\{return([^}]+)\}', data)
    return m.group(1).strip() if m else "（未匹配到）"


def _tokens(s):
    return [w for w in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split() if w not in ("obj", "the", "a")]


def _line_token_sets(text):
    return [set(_tokens(l)) for l in text.split("\n") if l.strip()]


def _prefix_in(tok, tset):
    # 手册爱缩写（property→prop、coordinate→coord…），按前缀≥4 字符匹配
    for t in tset:
        if t == tok:
            return True
        k = min(len(t), len(tok), 5)
        if k >= 4 and (t.startswith(tok[:k]) or tok.startswith(t[:k])):
            return True
    return False


def manual_diff(reg_rows, manual_path):
    """装机注册表 ↔ 手册 A43 小节的差集。

    判读口径（别误报）：
      - 手册 A43 小节里找不到、且**全文也找不到**相关字样 → 手册真缺该子动作；
      - 手册 A43 里找不到但存在动宾倒写/缩写（注册表 `objStyleSetProperty`
        ↔ 手册 "Set Obj Style Prop"）→ 只是**措辞差异**，不是缺失，需人工确认。
    """
    if not os.path.exists(manual_path):
        return None
    lines = open(manual_path, encoding="utf-8").read().split("\n")
    joined = "\n".join(lines)
    # 目录页那行是 "A43. LVGL.....A.107"（带点线），用**整行相等**过滤掉；
    # 正文里 "A43. LVGL" 还会作为页眉重复出现，取**第一次**（后随 Description）。
    starts = [i for i, l in enumerate(lines) if l.strip() == "A43. LVGL"]
    if not starts:
        return None
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines))
               if re.match(r"^A(4[4-9]|[5-9][0-9])\.\s", lines[i]) and "..." not in lines[i]),
               len(lines))
    # 跨度太小 = 抓错区间（比如只抓到页眉），宁可不判也不出错结论
    if end - start < 200:
        return None
    a43_sets = _line_token_sets("\n".join(lines[start:end]))
    missing, wording = [], []
    for _id, name, group, _props in reg_rows:
        toks = _tokens(" ".join(re.findall(r"[A-Z][a-z0-9]*", name)))
        if not toks:
            continue
        if any(all(_prefix_in(t, s) for t in toks) for s in a43_sets):
            continue                                  # 手册有（含措辞差异）
        # 没命中：全文再查一次，区分"真缺"与"措辞差异（写在别处）"
        if any(all(_prefix_in(t, s) for t in toks) for s in _line_token_sets(joined)):
            wording.append((name, " ".join(toks)))
        else:
            missing.append((name, " ".join(toks)))
    return missing, wording, start + 1, end



def main():
    asar = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ASAR
    manual = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MANUAL
    data = load(asar)
    os.makedirs(NOTES, exist_ok=True)

    reg = registry(data)

    p1 = os.path.join(NOTES, "_lvgl_action_registry_extract.txt")
    with open(p1, "w", encoding="utf-8") as f:
        f.write("A43 LVGL 动作的子动作注册表（装机版 EEZ Studio，权威；手册只列到 63 项）\n")
        f.write("来源：%s\n\n" % asar)
        f.write("%-3s | %-30s | %-24s | 属性\n" % ("id", "name", "group"))
        for r in reg:
            f.write("%-3d | %-30s | %-24s | %s\n" % r)
        f.write("\n合计：%d 项（手册 A43 = 63 项，差集见 notes/flow-actions-lvgl.md）\n" % len(reg))
    print("written:", p1, len(reg), "项")

    pal = palette(data)
    p2 = os.path.join(NOTES, "_lvgl_palette_availability.txt")
    with open(p2, "w", encoding="utf-8") as f:
        f.write("每个 Flow 件在 **LVGL 工程**里的可用性（判据：enabledInComponentPalette 谓词）\n")
        f.write("★注意：面板允许 ≠ CLI 生成的 C++ 里有实现；后者要实测。\n\n")
        for fid, pred in pal:
            f.write("%-34s | %-46s | %s\n" % (fid.replace("COMPONENT_TYPE_", ""), classify(pred), pred[:90]))
    print("written:", p2, len(pal), "件")

    print("\nLVGL 的 native 变量可用类型（官方 traits 原话）：\n  ", native_var_types(data))

    d = manual_diff(reg, manual)
    if d:
        missing, wording, ls, le = d
        p3 = os.path.join(NOTES, "_manual_vs_registry_diff.txt")
        with open(p3, "w", encoding="utf-8") as f:
            f.write("手册 A43 小节（raw 行 %d–%d）↔ 装机注册表 %d 项 的对账\n\n" % (ls, le, len(reg)))
            f.write("== 手册真缺（全文都找不到该字样）==\n")
            for n, lab in missing:
                f.write("  %-30s (%s)\n" % (n, lab))
            f.write("\n== 措辞差异（同一动作，手册换了词序/叫法，需人工确认）==\n")
            for n, lab in wording:
                f.write("  %-30s (%s)\n" % (n, lab))
            f.write("\n判读：只有『手册真缺』那组才是产品比手册新的部分；"
                    "『措辞差异』不要当成缺失写进结论。\n")
        print("written:", p3, "→ 真缺 %d 项，措辞差异 %d 项" % (len(missing), len(wording)))
    else:
        print("（未找到手册全文，跳过对账：%s）" % manual)



if __name__ == "__main__":
    main()
