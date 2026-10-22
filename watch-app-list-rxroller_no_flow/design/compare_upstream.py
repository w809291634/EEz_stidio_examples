# -*- coding: utf-8 -*-
"""
compare_upstream.py —— 拿本地克隆的上游仓库，逐字节核对"入库原文 == 上游原文"

对照库是**整个上游工程**（6 个文件 + .git 全历史），不是只挑出来的那 3 个：
    watch-app-list-rxroller_no_flow/upstream_Rxroller/
重新拉取：
    git clone https://github.com/rxwind7/Rxroller.git watch-app-list-rxroller_no_flow/upstream_Rxroller

为什么需要它：入库的 Rxroller.c.orig 是**行尾归一化成 LF** 的（上游仓库里是 CRLF），
所以直接 sha256sum 两边对不上（166b6480… vs 3a364084…），看着像"改过"其实没有。
本脚本把行尾归一化后再比，并顺带核对 commit 身份，避免拿错版本。

用法：
    python design/compare_upstream.py            # 出结论
    python design/compare_upstream.py --diff     # 顺手把两份 diff 写成文件
退出码：0 = 原文未被改动且补丁账单符合预期；1 = 有出入，需要查。
"""
import argparse
import hashlib
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
ROOT = os.path.dirname(PROJ)
VEND = os.path.join(PROJ, "src", "native", "rxroller")

# 上游仓库的**完整**本地克隆（含 .git 全历史），放在工程自己目录下，见 §"本地对照库"
UPSTREAM_CLONE = os.path.join(PROJ, "upstream_Rxroller")

# 上游身份（PORTLOG §1）。换版本时改这里，别改产物。
PINNED_COMMIT = "8928104b2aa7961e2d2d44cd50f01cb3a1747088"
EXPECTED_HUNKS = 14

# 上游仓库内路径 -> 本工程入库文件名（.orig 是原文留底；Rxroller.h/LICENSE 就地用）
PAIRS = [
    ("Rxroller.c", "Rxroller.c.orig"),
    ("Rxroller.h", "Rxroller.h"),
    ("LICENSE",    "LICENSE"),
]

# 上游仓库里我们**没有**取用的文件。列出来是为了"整仓可核对"：
# 脚本会确认这些确实只存在于对照库、没有被偷偷塞进本工程。
NOT_VENDORED = ["README.md", "CMakeLists.txt", ".gitignore"]


def norm(path):
    """读文本并把 CRLF/CR 归一成 LF，返回 bytes。行尾差异不算改动。"""
    data = io.open(path, "rb").read()
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def repo_commit(repo):
    try:
        out = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"],
                                      stderr=subprocess.STDOUT)
        return out.decode().strip()
    except Exception as e:
        return "取不到：%s" % e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=UPSTREAM_CLONE,
                    help="上游仓库本地克隆路径（默认工程内的 upstream_Rxroller/）")
    ap.add_argument("--diff", action="store_true", help="导出两份 diff 文件")
    a = ap.parse_args()

    if not os.path.isdir(os.path.join(a.repo, ".git")):
        sys.exit("没找到上游克隆：%s\n先跑：git clone https://github.com/rxwind7/Rxroller.git %s"
                 % (a.repo, os.path.relpath(UPSTREAM_CLONE, PROJ)))

    print("上游克隆  = %s" % a.repo)
    print("HEAD      = %s" % repo_commit(a.repo))
    print("钉住 commit= %s%s" % (PINNED_COMMIT,
          "" if repo_commit(a.repo) == PINNED_COMMIT else "   ★ 两者不一致，比对结果只代表当前 HEAD"))
    print("")

    ok = True

    # ---- 整仓对账：上游每个文件都必须有归属，不能出现"没记账的文件" ----
    try:
        tree = subprocess.check_output(
            ["git", "-C", a.repo, "ls-tree", "-r", "HEAD", "--name-only"]
        ).decode("utf-8", "replace").split()
    except Exception:
        tree = sorted(f for f in os.listdir(a.repo)
                      if os.path.isfile(os.path.join(a.repo, f)))
    accounted = [u for u, _ in PAIRS] + NOT_VENDORED
    extra = sorted(set(tree) - set(accounted))
    missing = sorted(set(accounted) - set(tree))
    print("上游仓库共 %d 个文件（git ls-tree -r HEAD）" % len(tree))
    tree_ok = not extra and not missing
    ok = ok and tree_ok
    if extra:
        print("DIFF  ★ 上游有 %d 个文件没记账：%s" % (len(extra), ", ".join(extra)))
    if missing:
        print("DIFF  ★ 账上记了但上游没有：%s" % ", ".join(missing))
    for f in NOT_VENDORED:
        print("      未取用 %-16s（只存在于对照库 %s）" % (f, os.path.relpath(a.repo, ROOT)))
    print("")

    for up_name, our_name in PAIRS:
        up = os.path.join(a.repo, up_name)
        our = os.path.join(VEND, our_name)
        if not os.path.exists(up):
            print("MISS  上游没有 %s" % up_name); ok = False; continue
        bu, bo = norm(up), norm(our)
        same = bu == bo
        ok = ok and same
        print("%s  %-12s 上游 %s  vs  入库 %-16s %s" % (
            "OK  " if same else "DIFF",
            up_name, sha(bu)[:12], our_name,
            "逐字节一致（归一化行尾后）" if same
            else "★ 不一致，sha=%s" % sha(bo)[:12]))

    # 补丁账单：入库原文 vs 编译产物
    orig = os.path.join(VEND, "Rxroller.c.orig")
    prod = os.path.join(VEND, "Rxroller.c")
    import difflib
    d = list(difflib.unified_diff(
        norm(orig).decode("utf-8", "replace").splitlines(True),
        norm(prod).decode("utf-8", "replace").splitlines(True),
        fromfile="upstream/Rxroller.c.orig", tofile="src/native/rxroller/Rxroller.c"))
    hunks = sum(1 for l in d if l.startswith("@@"))
    add = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
    dele = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
    bill_ok = hunks == EXPECTED_HUNKS
    ok = ok and bill_ok
    print("%s  %-12s .orig -> Rxroller.c（编译产物）= %d hunks / +%d / -%d%s" % (
        "OK  " if bill_ok else "DIFF", "账单", hunks, add, dele,
        "" if bill_ok else "   ★ 与 PORTLOG §3 记的 %d hunks 不符" % EXPECTED_HUNKS))

    if a.diff:
        out = os.path.join(VEND, "Rxroller_port.diff")
        io.open(out, "w", encoding="utf-8", newline="").write("".join(d))
        print("\n已导出：%s（%d 行）" % (
            os.path.relpath(out, ROOT), len(d)))

    print("\n结论：%s" % ("入库原文与上游一致，补丁账单符合 PORTLOG" if ok
                          else "★ 有出入，见上面 DIFF 行"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
