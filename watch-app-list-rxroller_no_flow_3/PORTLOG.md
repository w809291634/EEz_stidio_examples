# PORTLOG —— applist 滚轮移植账单（上游 Rxroller，MIT）
> `Rxroller.c` 是生成物：由 `design/port_rxroller.py` 从 `.orig` 重放，`design/sim.py` 每次构建前会跑它。

## 1. 上游身份
- 仓库 https://github.com/rxwind7/Rxroller ；commit 8928104b2aa7961e2d2d44cd50f01cb3a1747088（无 tag/release）
- 中转自 watch-app-list-rxroller_no_flow（其账单里的 .orig SHA256 与本工程逐字相同）
- 标称 LVGL v8，本工程编到 9.4

## 2. 入库文件 SHA256
```
3a364084ef499629d97185ba800336c836187087c0337026db7af1741f97e146  src/native/third_party/rxroller/Rxroller.c.orig
9ffe79f8de34478791ee57c95921603287e841708765bf75a0f255e809971bd3  src/native/third_party/rxroller/Rxroller.h
5ee83fa2c52beb32c6bd27b3dc01b33be72075b514b1359667a32b16957080c9  src/native/third_party/rxroller/LICENSE
9a8c2681de8f563d6193c3e3d1c63367dc68cd6ddc072343b7496ff1bc14c236  src/native/third_party/rxroller/Rxroller.c
```

## 3. 上游代码改动（全部在 port_rxroller.py 内）
| 项 | 内容 |
| --- | --- |
| 1~12 | user_data 直取 → LVGL 9 访问器 |
| 13 | lv_mem_alloc/free → lv_malloc/free 别名 |
| 14 | RX_SCALE_SPAN_PITCHES / RXROLLER_SCALE_MAX 能力补丁（值取自 watch_list_config.h） |
| 15 | ANIM_OFF 按带符号行差：上游取模只会往前，14 行时 13→5 被算成 +6 再被 clamp 夹住，中心不动 |

## 4. 本工程侧差异（watch_list_native.c）
| 号 | 内容 |
| --- | --- |
| D1 | 行点击=整行直接跳页（参考工程是两段式） |
| D2 | 端点磁吸 1/1（只有 14 个 APP，挡首尾会让运动/设置滚不到中心） |
| D3 | 新增 watch_list_row_obj() + 头文件 extern "C" |
| D4 | 落点标定：先 update_layout；bool 判失败（负坐标是合法的）；去试探按实测斜率 0.5；拖动/动画期跳过；每拍幂等；tab 切换同步 realign |
| D6 | 横向跟手：全屏 native 宿主保留 `SCROLL_CHAIN_HOR`，真实触摸由最近祖先 tabview 原生滚动；`watch_list_swipe_to()` 仅留无头夹具钩子 | 宿主移除横向链会截断输入，旧版只能松手后 `set_active`，无法跟随手指 |
| D5 | 466 圆屏参数：ICON_PX=90（位图原生）、PITCH=92、中心档 100%、CENTER 38%/42%、R=700 |

## 5. 验证
- [NAV] RESULT: PASS 44 / FAIL 0
- 中心行落点 渲染=(176,195)，目标 38%/42%=(177,195)，容差 1px
- 截图 tmp/applist_now.png：穹顶 C 形排布、名称 26px 与设计图一致
- 构建 Ninja + ccache，exe 落工程内 build_rel/bin/main.exe
