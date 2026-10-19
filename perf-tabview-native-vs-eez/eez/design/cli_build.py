#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EEZ Studio 无头构建（perf-eez-tabview，无字体/图片条目）。"""
import os, subprocess, sys, time, tempfile

EXE = r'C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(os.path.dirname(HERE), 'perf-eez-tabview.eez-project')

env = dict(os.environ)
env.pop('ELECTRON_RUN_AS_NODE', None)
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
        # 必须等这一句（EEZ Flow engine 在其之前发射，提前退出会掐掉）
        hit = 'ok'
        break
p.terminate()
try:
    p.wait(timeout=10)
except Exception:
    subprocess.call(['taskkill', '/F', '/IM', 'EEZ Studio.exe'], shell=False)

print('==== BUILD RESULT:', hit or 'TIMEOUT/FAIL', '====')
print('\n'.join(l for l in txt.splitlines()
                if 'MMKV' not in l and 'MemoryFile' not in l)[-1200:])
sys.exit(0 if hit else 1)
