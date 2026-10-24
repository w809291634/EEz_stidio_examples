# -*- coding: utf-8 -*-
"""shot_states.py —— ⑤/⑦ 的仿真出图：逐状态截到 build/sim_shots/。

全部走**真实运行路径**，不再翻 hiddenFlag：
  * 主屏状态（idle / scanning / done / empty）——钩子 WIFI_SHOT_AT 到达；
  * 模态（半页 / 对话框）——钩子 WIFI_REACH 用注入鼠标点击列表行走完
    "点带锁行 → 半页"、"长按已保存行 → 对话框"这条真通路（⑦-1 接线）。
所以这些图既证明"长这样"，也证明"进得去"。

顺序是硬约束：build_example（写 .eez-project）→ cli_build（覆盖 src/ui，含 fonts/）
→ gen_font（重烘字体，否则链接报 undefined ui_font_cn14）→ 仿真编译 → 跑图。

用法：python design/shot_states.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = os.path.join(ROOT, "build", "sim_shots")
SIM = os.path.join(HERE, "sim_cmake")
EXE_DIR = os.path.join(SIM, "build_rel", "bin")
SDL_BIN = r"D:\Program_Files\SDL2-2.32.4\x86_64-w64-mingw32\bin"

try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

BE_PY = os.path.join(ROOT, "build_example.py")

# (产物 tag, 钩子环境)
SHOOTS = [
    ("idle",       {"WIFI_SHOT_AT": "idle"}),
    ("scanning",   {"WIFI_SHOT_AT": "scanning"}),
    ("done",       {"WIFI_SHOT_AT": "done"}),
    ("empty",      {"WIFI_SHOT_AT": "done", "WIFI_FAKE_STATE": "empty"}),
    ("sheet_open", {"WIFI_AUTOSCAN": "1", "WIFI_REACH": "sheet",
                   "WIFI_KBPROBE": "1"}),
    ("dialog_open", {"WIFI_AUTOSCAN": "1", "WIFI_REACH": "dialog"}),
]


def regen():
    for cmd in ([sys.executable, BE_PY],
                [sys.executable, os.path.join(HERE, "cli_build.py")],
                [sys.executable, os.path.join(HERE, "gen_font.py")]):
        subprocess.check_call(cmd, cwd=ROOT, stdout=subprocess.DEVNULL)
    r = subprocess.run(["cmd.exe", "/c", "run_sim.bat", "build"], cwd=SIM,
                       capture_output=True, text=True, errors="replace")
    if "build succeeded" not in (r.stdout or ""):
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
        raise SystemExit("仿真编译失败")


def run_exe(extra_env):
    env = dict(os.environ)
    env["PATH"] = env["PATH"] + ";" + SDL_BIN
    env.update(WIFI_AUTOEXIT="1")
    env.update(extra_env)
    r = subprocess.run([os.path.join(EXE_DIR, "main.exe")], cwd=EXE_DIR, env=env,
                       timeout=180, capture_output=True, text=True, errors="replace")
    out = r.stdout or ""
    tag = "[REACH] shot" if "WIFI_REACH" in extra_env else "[SHOT] saved"
    if tag not in out:
        raise SystemExit("没截到图：%s\n%s" % (extra_env, out[-600:]))
    return out


def save(tag):
    from PIL import Image
    os.makedirs(SHOTS, exist_ok=True)
    src = os.path.join(EXE_DIR, "shot_fake.bmp")
    Image.open(src).convert("RGB").save(os.path.join(SHOTS, tag + ".png"))
    print("shot:", tag)


def main():
    regen()
    for tag, env in SHOOTS:
        run_exe(env)
        save(tag)
    print("done ->", SHOTS)


if __name__ == "__main__":
    main()
