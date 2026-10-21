#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EEZ Studio 无头构建（本工程无字体/无图片条目，无需 GUI 补提取链）。"""
import os, subprocess, sys, time, tempfile

EXE = r'C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(os.path.dirname(HERE), 'app-wifi-scan-flow-no-flow.eez-project')

env = dict(os.environ)
env.pop('ELECTRON_RUN_AS_NODE', None)          # 坑 3：不去掉会报 bad option
args = [EXE, '--build-project', PROJ,
        '--no-sandbox', '--disable-gpu', '--enable-unsafe-swiftshader',
        '--disable-dev-shm-usage']

logf = tempfile.NamedTemporaryFile('w', suffix='.log', delete=False,
                                   encoding='utf-8')
p = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT, env=env,
                     creationflags=0x08000000 if os.name == 'nt' else 0)
deadline = time.time() + 180
hit = None
while time.time() < deadline:
    time.sleep(2)
    logf.flush()
    txt = open(logf.name, encoding='utf-8', errors='replace').read()
    if 'Build successfully finished' in txt:
        # ★ 必须等这一句——"No error and no warning detected"出现在文件列表之前，
        #   提前退出会掐死 EEZ Flow engine（eez-flow.h/cpp）的发射阶段（P-0152 坑 4 真因）
        hit = 'ok'
        break
p.terminate()
try:
    p.wait(timeout=10)
except Exception:
    subprocess.call(['taskkill', '/F', '/IM', 'EEZ Studio.exe'], shell=False)

# ★ flow 检查错误是非致命的（构建仍会"成功"），必须显式拦截：
#   "identifier ... is neither input or local or global variable" 等
import re
m = re.search(r'(\d+) errors? and no warning', txt)
if m and int(m.group(1)) > 0:
    hit = 'FLOW_ERRORS(%s)' % m.group(1)
    for line in txt.splitlines():
        if 'neither input' in line or 'identifier' in line:
            print('  FLOW-ERR:', line.strip())

print('==== BUILD RESULT:', hit or 'TIMEOUT/FAIL', '====')
print('---- last log lines ----')
print('\n'.join(l for l in txt.splitlines()
                if 'MMKV' not in l and 'MemoryFile' not in l)[-1500:])
sys.exit(0 if hit else 1)
