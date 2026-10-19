#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EEZ Studio 无头构建（本工程无字体条目，无需 GUI 补提取链）。"""
import os, subprocess, sys, time, tempfile

EXE = r'C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(os.path.dirname(HERE), 'w1-animation-image.eez-project')

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
        # 必须等这一句——"No error..."在文件列表之前，提前退出会掐死
        # EEZ Flow engine（eez-flow.h/cpp）的发射阶段
        hit = 'ok'
        break
    if 'error' in txt.lower() and 'cache_util' not in txt and \
            'gpu' not in txt.lower() and 'swiftshader' not in txt.lower() and \
            'warning' not in txt.lower():
        # 可能出错，但再等几轮确认（早期日志有噪声）
        if time.time() > deadline - 120:
            pass
p.terminate()
try:
    p.wait(timeout=10)
except Exception:
    subprocess.call(['taskkill', '/F', '/IM', 'EEZ Studio.exe'], shell=False)

print('==== BUILD RESULT:', hit or 'TIMEOUT/FAIL', '====')
print('---- last log lines ----')
print('\n'.join(txt.splitlines()[-25:]))
sys.exit(0 if hit else 1)
