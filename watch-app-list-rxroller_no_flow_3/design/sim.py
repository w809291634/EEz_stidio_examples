# -*- coding: utf-8 -*-
"""仿真器编译 + 逐屏截图（NO_FLOW 第⑤步双核对用；动态效果主验收面）。

现状：骨架占位。启用前必须：
① 向用户核对 ui_debug_kit.config.json 的 sim 段（template_dir=EEz_stidio_examples\\PC_SIM
   是否可直接用、mingw/cmake/sdl2 路径）——禁止猜；
② 参考 kit skills.md §5.6 快照流水线与 watch-app-list-no-flow 的 sim_cmake 做法。
"""
import sys

sys.exit("sim.py 尚未实现：第⑤步前先核对 PC_SIM 工具链路径（config.sim 段），再按 kit §5.6 接入。")
