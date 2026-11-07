# -*- coding: utf-8 -*-
"""默认资源口径：用 IDF 工具链按 IDF 同参数只编译 UI，不链接。

统计范围 = EEZ 生成的 src/ui + src/native 下全部 UI 代码（自动发现，新增 UI 模块无需改脚本）：
  - 不含：platform/**（硬件平台与 PC 仿真）、wifi_logic/model/events（硬件业务）

数据来自测量模板的 build/compile_commands.json（模板必须先构建过一次）。
只编译不含 --gc-sections / 链接脚本，Flash 通常偏高约 17%，仅作默认估算；
精确值仍可跑 design/esp32_size.py（点名才做）。
"""
import glob
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UI = os.path.join(ROOT, "src", "ui")
NATIVE = os.path.join(ROOT, "src", "native")
CONF = os.path.join(HERE, "esp32_toolchain.json")

# 与 UI 直接相关的 native 代码：默认收 src/native 下全部 .c/.cpp，
# 只排除硬件平台/仿真目录与硬件业务文件。新增 UI 模块无需再改本脚本。
NATIVE_EXCLUDE_DIRS = ("platform/", "third_party/")
NATIVE_EXCLUDE_FILES = {
    "src/native/app/wifi_logic.cpp",     # Wi-Fi 业务状态机（硬件）
    "src/native/app/wifi_model.cpp",     # Wi-Fi 数据模型（硬件）
    "src/native/app/wifi_events.cpp",    # Wi-Fi 事件队列（硬件）
}


def native_sources():
    out = []
    for ext in ("*.c", "*.cpp"):
        for f in glob.glob(os.path.join(NATIVE, "**", ext), recursive=True):
            rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
            if any(("/" + d) in rel for d in NATIVE_EXCLUDE_DIRS):
                continue
            if rel in NATIVE_EXCLUDE_FILES:
                continue
            out.append(f)
    return sorted(out)


def native_header_hash():
    h = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(NATIVE, "**", "*.h"), recursive=True)):
        h.update(os.path.relpath(f, ROOT).replace(os.sep, "/").encode())
        h.update(open(f, "rb").read())
    return h.hexdigest()


def conf():
    if not os.path.isfile(CONF):
        return None
    return json.load(open(CONF, encoding="utf-8"))


def unq(x):
    if x.startswith('@"') and x.endswith('"'):
        return "@" + x[2:-1]
    return x[1:-1] if len(x) >= 2 and x[0] == '"' and x[-1] == '"' else x


def opt_of(args):
    for a in args:
        if a == "-O" or a in ("-O0", "-O1", "-O2", "-O3", "-O4", "-Og", "-Os", "-Oz", "-Ofast"):
            return a
    return "?"


def ui_hash():
    files = (sorted(glob.glob(os.path.join(UI, "**", "*.c"), recursive=True)) +
             sorted(glob.glob(os.path.join(UI, "**", "*.h"), recursive=True)) +
             native_sources() +
             sorted(glob.glob(os.path.join(NATIVE, "**", "*.h"), recursive=True)))
    h = hashlib.sha256()
    for f in files:
        h.update(os.path.relpath(f, ROOT).replace(os.sep, "/").encode())
        h.update(open(f, "rb").read())
    return h.hexdigest()


def header_hash():
    h = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(UI, "**", "*.h"), recursive=True)):
        h.update(os.path.basename(f).encode())
        h.update(open(f, "rb").read())
    return h.hexdigest()[:12]


def measure(opt=None):
    cfg = conf()
    if not cfg:
        return {"error": "缺少 design/esp32_toolchain.json"}
    build = os.path.join(cfg["template"], "build")
    cc_path = os.path.join(build, "compile_commands.json")
    if not os.path.isfile(cc_path):
        return {"error": "模板尚未构建：%s" % cc_path}
    try:
        cc = json.load(open(cc_path, encoding="utf-8"))
        base = next(e for e in cc
                    if e["file"].replace("\\", "/").endswith("eez-test/src/ui/screens.c"))
    except (StopIteration, ValueError) as e:
        return {"error": "找不到 UI 编译命令：%s" % e}

    args0 = [unq(x) for x in shlex.split(base["command"], posix=False)]
    args0 = [a.replace('\\"', "") if a.startswith("-D") else a for a in args0]
    active = opt_of(args0)
    level = opt or cfg.get("default_opt", "-O2")
    if active != "?":
        args0 = [level if a == active else a for a in args0]
    src0 = base["file"]
    ui_inc = next((a for a in args0
                   if a.startswith("-I") and a.replace("\\", "/").endswith("/eez-test/src/ui")), None)
    if not ui_inc:
        return {"error": "编译命令里没有 UI include 路径"}
    size_exe = cfg["size"]
    sig = []
    skip = False
    for x in args0:
        if skip:
            skip = False
            continue
        if x == "-o":
            skip = True
            continue
        if x == src0:
            sig.append("<SRC>")
        elif x == ui_inc:
            sig.append("-I<UI>")
        else:
            sig.append(x)
    cmd_sig = hashlib.sha1("\0".join(sig).encode()).hexdigest()[:10]
    # 持久缓存：按“单文件内容 + 头文件 + 参数”失效，改一个屏不会重编字库
    hdr = header_hash()
    cache = os.path.join(ROOT, "tmp", "compile_cache", "esp32",
                         level.lstrip("-"), cmd_sig)
    os.makedirs(cache, exist_ok=True)
    files = []
    for f in sorted(glob.glob(os.path.join(UI, "**", "*.c"), recursive=True)):
        key = hashlib.sha256(open(f, "rb").read() + hdr.encode()).hexdigest()[:10]
        obj = os.path.join(cache, os.path.basename(f) + "." + key + ".o")
        if not os.path.isfile(obj):
            a = list(args0)
            a[a.index(ui_inc)] = "-I" + UI
            a[a.index(src0)] = f
            if "-o" in a:
                a[a.index("-o") + 1] = obj
            r = subprocess.run(a, cwd=build, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode != 0 or not os.path.isfile(obj):
                return {"error": "编译失败 %s：%s" % (os.path.basename(f), (r.stderr or r.stdout)[-200:])}
        s = subprocess.run([size_exe, obj], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stdout.split()
        text, data, bss = int(s[-6]), int(s[-5]), int(s[-4])
        files.append({"name": os.path.basename(f), "flash": text + data,
                      "ram": data + bss, "text": text, "data": data, "bss": bss})

    # ---- UI 相关 native 模块（硬件/仿真目录不计）----
    native = []
    nat_inc = next((a for a in args0
                    if a.startswith("-I") and a.replace("\\", "/").endswith("/src/native")), None)
    nhdr = native_header_hash()
    nat_cache = os.path.join(cache, "native")
    os.makedirs(nat_cache, exist_ok=True)
    for f in native_sources():
        ext = os.path.splitext(f)[1].lower()
        key = hashlib.sha256(open(f, "rb").read() + nhdr.encode()).hexdigest()[:10]
        obj = os.path.join(nat_cache, os.path.basename(f) + "." + key + ".o")
        if not os.path.isfile(obj):
            a = list(args0)
            a[a.index(ui_inc)] = "-I" + UI
            if nat_inc:
                a[a.index(nat_inc)] = "-I" + NATIVE
            else:
                a.append("-I" + NATIVE)
            a[a.index(src0)] = f
            if ext == ".cpp":
                if a[0].lower().endswith("-gcc.exe"):
                    a[0] = a[0][:-len("-gcc.exe")] + "-g++.exe"
                a = [("-std=gnu++2b" if x.startswith("-std=") else x) for x in a]
                if "-fexceptions" not in a:
                    a.append("-fexceptions")
            if "-o" in a:
                a[a.index("-o") + 1] = obj
            r = subprocess.run(a, cwd=build, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode != 0 or not os.path.isfile(obj):
                return {"error": "native 编译失败 %s：%s" %
                        (os.path.basename(f), (r.stderr or r.stdout)[-300:])}
        s = subprocess.run([size_exe, obj], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stdout.split()
        text, data, bss = int(s[-6]), int(s[-5]), int(s[-4])
        native.append({"name": os.path.relpath(f, ROOT).replace(os.sep, "/"),
                       "flash": text + data, "ram": data + bss})
    native.sort(key=lambda x: -x["flash"])

    files.sort(key=lambda x: -x["flash"])
    ui_flash = sum(x["flash"] for x in files)
    ui_ram = sum(x["ram"] for x in files)
    nat_flash = sum(x["flash"] for x in native)
    nat_ram = sum(x["ram"] for x in native)
    return {
        "target": cfg.get("target", "esp32p4"),
        "idf_version": cfg.get("idf_version", "?"),
        "opt": level,
        "files": files,
        "native_files": native,
        "ui_flash": ui_flash,
        "ui_ram": ui_ram,
        "native_flash": nat_flash,
        "native_ram": nat_ram,
        "total_flash": ui_flash + nat_flash,
        "total_ram": ui_ram + nat_ram,
        "fonts_flash": sum(x["flash"] for x in files if x["name"].startswith("ui_font_")),
    }


def measure_levels(levels=("-O0", "-O1", "-O2", "-O3", "-Os")):
    out = []
    for lv in levels:
        r = measure(lv)
        if "error" not in r:
            out.append({"opt": lv, "ui_flash": r["total_flash"], "ui_ram": r["total_ram"],
                        "fonts_flash": r["fonts_flash"]})
    return out


if __name__ == "__main__":
    if "--levels" in sys.argv:
        for x in measure_levels():
            print("%-4s Flash %8d  RAM %6d  fonts %8d"
                  % (x["opt"], x["ui_flash"], x["ui_ram"], x["fonts_flash"]))
        raise SystemExit(0)
    r = measure()
    if "error" in r:
        print("[EST] ERROR", r["error"])
    else:
        for x in r["files"]:
            print("%-24s Flash %8d  RAM %6d" % (x["name"], x["flash"], x["ram"]))
        for x in r["native_files"]:
            print("%-40s Flash %8d  RAM %6d" % (x["name"], x["flash"], x["ram"]))
        print("[EST] UI Flash %d (EEZ %d + native %d)  RAM %d  fonts %d (%s, %s)"
              % (r["total_flash"], r["ui_flash"], r["native_flash"],
                 r["total_ram"], r["fonts_flash"], r["target"], r["opt"]))
