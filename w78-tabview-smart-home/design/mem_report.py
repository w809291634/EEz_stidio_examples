# -*- coding: utf-8 -*-
"""D9 资源账（只报编译后占用）：默认 IDF 工具链只编译估算 + PC 上限。

用法：python design/mem_report.py [--brief]
默认：design/esp32_estimate.py（只编译，Flash 偏高约17%）
点名复核：python design/esp32_size.py（IDF 工程最终链接，精确）
预算：design/mem_budget.json（按编译后 Flash 计）
"""
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

import esp32_estimate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UI = os.path.join(ROOT, "src", "ui")
BUDGET = os.path.join(HERE, "mem_budget.json")
ESP32 = os.path.join(HERE, "esp32_size.json")
OPT_TABLE = os.path.join(HERE, "esp32_opt_table.json")
BRIEF = "--brief" in sys.argv


def ui_hash():
    files = sorted(glob.glob(os.path.join(UI, "**", "*.c"), recursive=True) +
                   glob.glob(os.path.join(UI, "**", "*.h"), recursive=True))
    h = hashlib.sha256()
    for f in files:
        h.update(os.path.relpath(f, ROOT).replace(os.sep, "/").encode())
        h.update(open(f, "rb").read())
    return h.hexdigest()


def kb(v):
    return "%dB" % v if v < 1024 else "%.1fKB" % (v / 1024.0)


def esp32_data():
    """返回 (data, fresh)；json 缺失或 UI 已变动则 fresh=False。"""
    if not os.path.isfile(ESP32):
        return None, False
    d = json.load(io.open(ESP32, encoding="utf-8"))
    return d, d.get("ui_hash") == ui_hash()


def opt_table():
    """各优化等级只编译对比；按 ui_hash 缓存，UI 变了才重算（约20s）。"""
    h = ui_hash()
    if os.path.isfile(OPT_TABLE):
        d = json.load(io.open(OPT_TABLE, encoding="utf-8"))
        if d.get("ui_hash") == h and d.get("rows"):
            return d["rows"]
    rows = esp32_estimate.measure_levels()
    if rows:
        json.dump({"ui_hash": h, "rows": rows,
                   "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                  io.open(OPT_TABLE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return rows



def mb(path):
    return os.path.getsize(path) / 1048576.0
def conf_val(path, key):
    if not os.path.isfile(path):
        return "?"
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"#define\s+" + key + r"\s+\(([^)]+)\)", txt) or \
        re.search(r"#define\s+" + key + r"\s+(\S+)", txt)
    return m.group(1).strip() if m else "?"


def compile_sizes(files):
    """把生成物编成 .o，读 text/data/bss；.o 持久缓存在 tmp/compile_cache/pc。"""
    out = {}
    hdr = hashlib.sha256()
    for h in sorted(glob.glob(os.path.join(UI, "**", "*.h"), recursive=True)):
        hdr.update(os.path.basename(h).encode())
        hdr.update(open(h, "rb").read())
    hdr = hdr.hexdigest()[:12]
    cache = os.path.join(ROOT, "tmp", "compile_cache", "pc", "O1")
    os.makedirs(cache, exist_ok=True)
    for f in files:
        key = hashlib.sha256(open(f, "rb").read() + hdr.encode()).hexdigest()[:10]
        o = os.path.join(cache, os.path.basename(f)[:-2] + "." + key + ".o")
        if not os.path.isfile(o):
            r = subprocess.run(["gcc", "-c", "-O1", "-DLV_CONF_INCLUDE_SIMPLE",
                                "-I", HERE, "-I", UI, "-I", os.path.join(os.path.dirname(ROOT), "apl_lvgl_v9_4"),
                                f, "-o", o],
                               capture_output=True, text=True, errors="replace")
            if r.returncode != 0 or not os.path.isfile(o):
                continue
        s = subprocess.run(["size", o], capture_output=True, text=True, errors="replace")
        m = re.search(r"^\s*(\d+)\s+(\d+)\s+(\d+)", s.stdout, re.M)
        if m:
            out[f] = (int(m.group(1)) + int(m.group(2)), int(m.group(3)))  # (flash, ram)
    return out


def main():
    fonts = sorted(glob.glob(os.path.join(UI, "fonts", "*.c")))
    others = [os.path.join(UI, n) for n in ("screens.c", "styles.c", "images.c")]
    binmap = compile_sizes([p for p in fonts + others if os.path.isfile(p)])
    f_flash = sum(v[0] for p, v in binmap.items() if p in fonts)
    f_ram = sum(v[1] for p, v in binmap.items() if p in fonts)
    o_flash = sum(v[0] for p, v in binmap.items() if p in others)
    o_ram = sum(v[1] for p, v in binmap.items() if p in others)
    flash, ram = f_flash + o_flash, f_ram + o_ram
    budget = {"fonts_mb": 0.5, "ui_mb": 1.0, "tier": "1m"}
    if os.path.isfile(BUDGET):
        budget.update(json.load(io.open(BUDGET, encoding="utf-8")))
    esp, fresh = esp32_data()
    est = esp32_estimate.measure()
    est_ok = "error" not in est
    if est_ok:
        ok = (est["ui_flash"] <= budget["ui_mb"] * 1048576 and
              est["fonts_flash"] <= budget["fonts_mb"] * 1048576)
    else:
        ok = flash <= budget["ui_mb"] * 1048576 and f_flash <= budget["fonts_mb"] * 1048576

    sim_conf = os.path.join(HERE, "sim_cmake", "lv_conf.h")
    depth = conf_val(sim_conf, "LV_COLOR_DEPTH")
    try:
        fb = "%.2fMB" % (800 * 480 * int(depth) / 8 / 1048576.0)
    except Exception:
        fb = "?"
    mem = conf_val(sim_conf, "LV_MEM_SIZE")
    sim_build = os.path.join(ROOT, "tmp", "sim_build_" + os.path.basename(ROOT))
    if not os.path.isdir(sim_build):
        sim_build = os.path.join(ROOT, "tmp", "sim_build")
    exe = os.path.join(sim_build, "bin", "main.exe")
    lib = os.path.join(sim_build, "apl_lvgl_build", "lib", "liblvgl.a")

    if not BRIEF:
        print("[MEM] 资源树（%s；只计编译后占用）" % budget.get("tier", "1m"))
        if est_ok:
            tgt = est["target"].upper().replace("ESP32P", "ESP32-P")
            print("ESP32（%s / IDF %s，工具链只编译估算；优化 %s，默认）"
                  % (tgt, est["idf_version"], est.get("opt", "?")))
            print("|- EEZ UI Flash %.1fKB / RAM %.1fKB" % (est["ui_flash"] / 1024.0, est["ui_ram"] / 1024.0))
            exact = {f["name"]: f for f in esp["files"]} if (esp and fresh) else {}
            for f in est["files"]:
                line = "|  |- %s %s / RAM %s" % (f["name"], kb(f["flash"]), kb(f["ram"]))
                ex = exact.get(f["name"])
                if ex and ex["flash"] != f["flash"]:
                    line += "  <- 精确 %s" % kb(ex["flash"])
                print(line)
            print("`- 未链接：缺 gc/链接脚本，Flash 通常偏高约17%；精确值按需跑 python design/esp32_size.py")
            rows = opt_table()
            if rows:
                print("优化等级对比（IDF 工具链只编译；字库 %.0fKB 不随等级变）" % (est["fonts_flash"] / 1024.0))
                for r in rows:
                    mark = "  <- 当前" if r["opt"] == est.get("opt") else ""
                    print("  %-4s Flash %6.1fKB / RAM %.1fKB%s"
                          % (r["opt"], r["ui_flash"] / 1024.0, r["ui_ram"] / 1024.0, mark))
        else:
            print("ESP32：工具链不可用（%s）" % est["error"])
            print("      先构建一次测量模板；本报告只统计 ESP32 工具链估算")
        if esp and fresh:
            print("精确链接缓存：Flash %.1fKB / RAM %.1fKB（%s，按需复核）"
                  % (esp["ui_flash"] / 1024.0, esp["ui_ram"] / 1024.0, esp["measured_at"]))
        print("字库")
        print("|- 镜像：12px 汉字 + 24/32 ASCII")
        print("`- SD 卡：未启用（启用后不占镜像，镜像保留 1 档兜底）")
    if est_ok:
        print("[MEM-BIN] fonts=%.0fKB ui=%.0fKB ram=%.0fKB target=%s opt=%s source=toolchain-estimate"
              % (est["fonts_flash"] / 1024.0, est["ui_flash"] / 1024.0, est["ui_ram"] / 1024.0,
                 est["target"], est.get("opt", "?")))
    else:
        print("[MEM-BIN] fonts=%.0fKB ui=%.0fKB ram=%.0fKB target=pc" % (f_flash / 1024.0, flash / 1024.0, ram / 1024.0))
    if esp and fresh:
        print("[MEM-EXACT] fonts=%.0fKB ui=%.0fKB ram=%.0fKB target=%s"
              % (esp["fonts_flash"] / 1024.0, esp["ui_flash"] / 1024.0, esp["ui_ram"] / 1024.0, esp["target"]))
    if est_ok:
        print("[MEM] %s 工具链估算（只编译，优化 %s，偏高约17%%）：Flash %.0fKB（字体 %.0fKB）+ RAM %.0fKB；预算 字体 %.0fKB / UI %.0fKB ｜ %s"
              % (est["target"].upper().replace("ESP32P", "ESP32-P"), est.get("opt", "?"),
                 est["ui_flash"] / 1024.0, est["fonts_flash"] / 1024.0, est["ui_ram"] / 1024.0,
                 budget["fonts_mb"] * 1024, budget["ui_mb"] * 1024, "PASS" if ok else "FAIL 超预算"))
    else:
        print("[MEM] PC 上限：Flash %.0fKB（字体 %.0fKB）+ RAM %.0fKB；预算 字体 %.0fKB / UI %.0fKB ｜ %s"
              % (flash / 1024.0, f_flash / 1024.0, ram / 1024.0,
                 budget["fonts_mb"] * 1024, budget["ui_mb"] * 1024, "PASS" if ok else "FAIL 超预算"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
