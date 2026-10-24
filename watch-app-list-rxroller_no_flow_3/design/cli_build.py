#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EEZ Studio 无头构建（照抄 EEz_stidio_examples\\watch-app-list-no-flow\\design\\cli_build.py 的已验证链）。

判成败只等 'Build successfully finished'（提前退出会掐死 eez-flow 发射阶段，P-0152）；
flow 检查错误非致命，必须显式拦截。
"""
import os, subprocess, sys, time, tempfile

EXE = r'C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(os.path.dirname(HERE), 'watch.eez-project')

env = dict(os.environ)
env.pop('ELECTRON_RUN_AS_NODE', None)          # 不去掉会报 bad option
args = [EXE, '--build-project', PROJ,
        '--no-sandbox', '--disable-gpu', '--enable-unsafe-swiftshader',
        '--disable-dev-shm-usage']

logf = tempfile.NamedTemporaryFile('w', suffix='.log', delete=False, encoding='utf-8')
p = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT, env=env,
                     creationflags=0x08000000 if os.name == 'nt' else 0)
deadline = time.time() + 180
hit = None
while time.time() < deadline:
    time.sleep(2)
    logf.flush()
    txt = open(logf.name, encoding='utf-8', errors='replace').read()
    if 'Build successfully finished' in txt:
        hit = 'ok'
        break
p.terminate()
try:
    p.wait(timeout=10)
except Exception:
    subprocess.call(['taskkill', '/F', '/IM', 'EEZ Studio.exe'], shell=False)

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
