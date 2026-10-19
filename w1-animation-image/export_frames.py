#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时：把 .eez-project 内嵌的位图 data-URI 导出为独立 PNG 文件。"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "w1-animation-image.eez-project")
OUT = os.path.join(HERE, "images")

proj = json.load(open(PROJ, encoding="utf-8"))
os.makedirs(OUT, exist_ok=True)
for b in proj["bitmaps"]:
    uri = b["image"]
    assert uri.startswith("data:image/png;base64,")
    png = base64.b64decode(uri.split(",", 1)[1])
    out = os.path.join(OUT, b["name"] + ".png")
    with open(out, "wb") as f:
        f.write(png)
    print("exported: %s (%d bytes)" % (out, len(png)))
