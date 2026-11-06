# -*- coding: utf-8 -*-
"""ESP32-P4 专用 EEZ UI 资源账。

默认使用 IDF 工具链同参数只编译估算；需要最终链接数据时，显式运行
design/esp32_size.py。宿主仿真仅用于预览和行为测试，不参与固件资源预算。
"""
import glob
import hashlib
import io
import json
import os
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
    digest = hashlib.sha256()
    for path in files:
        digest.update(os.path.relpath(path, ROOT).replace(os.sep, "/").encode())
        digest.update(open(path, "rb").read())
    return digest.hexdigest()


def kb(value):
    return "%dB" % value if value < 1024 else "%.1fKB" % (value / 1024.0)


def exact_data():
    if not os.path.isfile(ESP32):
        return None, False
    data = json.load(io.open(ESP32, encoding="utf-8"))
    return data, data.get("ui_hash") == ui_hash()


def opt_table():
    current_hash = ui_hash()
    if os.path.isfile(OPT_TABLE):
        data = json.load(io.open(OPT_TABLE, encoding="utf-8"))
        if data.get("ui_hash") == current_hash and data.get("rows"):
            return data["rows"]
    rows = esp32_estimate.measure_levels()
    if rows:
        json.dump({"ui_hash": current_hash, "rows": rows,
                   "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                  io.open(OPT_TABLE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return rows


def main():
    budget = {"fonts_mb": 0.5, "ui_mb": 1.0, "tier": "1m"}
    if os.path.isfile(BUDGET):
        budget.update(json.load(io.open(BUDGET, encoding="utf-8")))

    estimate = esp32_estimate.measure()
    if "error" in estimate:
        print("[MEM] ESP32 工具链估算不可用：%s" % estimate["error"])
        print("      请先构建一次 ESP32-P4 测量模板；不回退到宿主编译统计。")
        return 2

    ok = (estimate["ui_flash"] <= budget["ui_mb"] * 1048576 and
          estimate["fonts_flash"] <= budget["fonts_mb"] * 1048576)
    exact, exact_fresh = exact_data()

    if not BRIEF:
        target = estimate["target"].upper().replace("ESP32P", "ESP32-P")
        print("[MEM] 资源树（%s；只计 ESP32 目标端编译后占用）" % budget.get("tier", "1m"))
        print("ESP32（%s / IDF %s，工具链只编译估算；优化 %s，默认）" %
              (target, estimate["idf_version"], estimate.get("opt", "?")))
        print("|- EEZ UI Flash %.1fKB / RAM %.1fKB" %
              (estimate["ui_flash"] / 1024.0, estimate["ui_ram"] / 1024.0))
        exact_files = {item["name"]: item for item in exact["files"]} if (exact and exact_fresh) else {}
        for item in estimate["files"]:
            line = "|  |- %s %s / RAM %s" % (item["name"], kb(item["flash"]), kb(item["ram"]))
            final = exact_files.get(item["name"])
            if final and final["flash"] != item["flash"]:
                line += "  <- 最终链接 %s" % kb(final["flash"])
            print(line)
        print("`- 未链接：缺 gc/链接脚本，Flash 通常偏高约17%；精确值按需跑 python design/esp32_size.py")

        rows = opt_table()
        if rows:
            print("优化等级对比（IDF 工具链只编译；字库 %.0fKB 不随等级变）" %
                  (estimate["fonts_flash"] / 1024.0))
            for row in rows:
                mark = "  <- 当前" if row["opt"] == estimate.get("opt") else ""
                print("  %-4s Flash %6.1fKB / RAM %.1fKB%s" %
                      (row["opt"], row["ui_flash"] / 1024.0, row["ui_ram"] / 1024.0, mark))
        if exact and exact_fresh:
            print("精确链接缓存：Flash %.1fKB / RAM %.1fKB（%s，按需复核）" %
                  (exact["ui_flash"] / 1024.0, exact["ui_ram"] / 1024.0, exact["measured_at"]))

    print("[MEM-BIN] fonts=%.0fKB ui=%.0fKB ram=%.0fKB target=%s opt=%s source=toolchain-estimate" %
          (estimate["fonts_flash"] / 1024.0, estimate["ui_flash"] / 1024.0,
           estimate["ui_ram"] / 1024.0, estimate["target"], estimate.get("opt", "?")))
    if exact and exact_fresh:
        print("[MEM-EXACT] fonts=%.0fKB ui=%.0fKB ram=%.0fKB target=%s" %
              (exact["fonts_flash"] / 1024.0, exact["ui_flash"] / 1024.0,
               exact["ui_ram"] / 1024.0, exact["target"]))
    print("[MEM] %s 工具链估算（只编译，优化 %s，偏高约17%%）：Flash %.0fKB（字体 %.0fKB）+ RAM %.0fKB；预算 字体 %.0fKB / UI %.0fKB ｜ %s" %
          (estimate["target"].upper().replace("ESP32P", "ESP32-P"), estimate.get("opt", "?"),
           estimate["ui_flash"] / 1024.0, estimate["fonts_flash"] / 1024.0,
           estimate["ui_ram"] / 1024.0, budget["fonts_mb"] * 1024,
           budget["ui_mb"] * 1024, "PASS" if ok else "FAIL 超预算"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
