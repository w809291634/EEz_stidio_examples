#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时：打印 watch 工程位图条目的完整字段（除 image 数据）。"""
import json
PROJ = r"C:\Users\yjt54\Desktop\Design Watch\watch\watch.eez-project"
proj = json.load(open(PROJ, encoding='utf-8'))
b = proj['bitmaps'][0]
print('keys:', list(b.keys()))
print({k: v for k, v in b.items() if k != 'image'})
