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
