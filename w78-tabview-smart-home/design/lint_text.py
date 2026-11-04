# -*- coding: utf-8 -*-
"""界面文案必须走索引：生成器里"造控件的调用"不许出现中文字面量。

判据（2026-11-04 用户令，PR-0476/0477）：
  只看 `make_label / make_button / make_container` 这类构造调用的**文本实参**：
  允许 `TEXTS["key"]` 或来自设计源数据的变量；不允许直接写中文字面量。
  （断言/日志里的中文是开发者信息，不在此列。）

为什么：中文散在脚本里会反复引发命令行截断、控制台乱码、换字库缺字形。
用法：python design/lint_text.py    # 有违规退出码 1
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = ["eez_gen.py", "overview_pro.py", "control_table.py"]
CTORS = {"make_label", "make_button", "make_container"}


def cjk(s):
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def main():
    bad = []
    for name in TARGETS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        tree = ast.parse(io.open(path, encoding="utf-8").read(), filename=name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = getattr(node.func, "id", getattr(node.func, "attr", ""))
            if fn not in CTORS:
                continue
            args = list(node.args[1:]) + [k.value for k in node.keywords]
            for a in args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and cjk(a.value):
                    bad.append((name, a.lineno, a.value[:20]))
    print("[LINT_TEXT] " + ("PASS" if not bad else "FAIL")
          + " ｜ 检查 %d 个生成器的造控件调用" % len(TARGETS))
    for name, line, txt in bad:
        print("  !! %s:%s 中文字面量 %r → 改成 TEXTS[...] 或设计源数据" % (name, line, txt))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
