#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时：解析 ESP-IDF map（GNU ld），按组件归档统计 flash/RAM。"""
import re

MAP = r"D:\esp32_8266_files\esp-idf-v5.5.5_ol\examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_ai\build\lvgl_demo_v9.map"

FLASH_SECS = {".flash.text", ".flash.rodata", ".iram0.text", ".dram0.data"}
RAM_SECS = {".dram0.bss"}

def bucket(archive):
    if archive == "esp-idf/ui":
        return "★ EEZ 自身（ui 组件：生成代码+flow 引擎）"
    if archive == "esp-idf/lvgl__lvgl":
        return "LVGL 内核（两方案共有）"
    if archive == "esp-idf/main":
        return "main 应用层"
    if archive == "esp-idf/native":
        return "应用 native 层"
    if archive.startswith("esp-idf/xiaozhi"):
        return "xiaozhi（与 EEZ 无关）"
    return "ESP-IDF 系统组件"

obj_re = re.compile(r"^\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)\s+(\S+)\s*$")
sec_re = re.compile(r"^(\.\S+)\s+0x")
arch_re = re.compile(r"^(esp-idf/[^/(]+|managed_components/[^/(]+)\(")

stats = {}
cur_sec = None
for line in open(MAP, encoding="utf-8", errors="replace"):
    ms = sec_re.match(line)
    if ms:
        cur_sec = ms.group(1)
        continue
    m = obj_re.match(line)
    if m and cur_sec:
        size = int(m.group(1), 16)
        token = m.group(2)
        ma = arch_re.match(token)
        if not ma:
            continue
        b = bucket(ma.group(1))
        st = stats.setdefault(b, [0, 0])
        if cur_sec in FLASH_SECS:
            st[0] += size
        elif cur_sec in RAM_SECS:
            st[1] += size

print("%-40s %12s %12s" % ("组件", "flash(B)", "ram-bss(B)"))
tf = tr = 0
for b in sorted(stats, key=lambda k: -stats[k][0]):
    fl, rm = stats[b]
    tf += fl; tr += rm
    print("%-40s %12d %12d" % (b, fl, rm))
print("%-40s %12d %12d" % ("合计(已归桶)", tf, tr))
