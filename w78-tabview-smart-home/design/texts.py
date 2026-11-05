# -*- coding: utf-8 -*-
"""界面文案索引（单一真值）：可见中文按 key 存放，生成器只引用 key，不写字面量。

为什么要索引（2026-11-04 用户令，PR-0476/0477）：
中文散落在脚本里会反复出问题——命令行参数被引号截断、控制台编码变乱码、
换字库后字形缺失。集中到 key 之后：改文案只改这里一处，生成器与检查器都引用 key。

约定：
  · key 用 `页面.用途` 命名；控件名类文案来自设计源（pages.py），不进本表。
  · 生成器不得再写中文字面量（`design/lint_text.py` 用 AST 检查）。
"""

TEXTS = {
    "home.hello": "晚上好，李然 · 5月18日 周一",
    "home.env": "室内 23.5° · 湿度 48%",
    "home.scene_title": "场景",
    "wifi.title": "Wi-Fi",
    "wifi.status": "点「扫描」发现网络",
    "wifi.hint": "共 0 个网络 · 长按已保存网络可忘记",
    "wifi.back": "‹ 设置",
    "wifi.scan": "扫描",
    "wifi.disconnect": "断开",
    "wifi.connect": "连接",
    "wifi.close": "x",
    "wifi.pwd_placeholder": "输入密码",
    "wifi.forget_title": "忘记此网络？",
    "wifi.forget_hint": "将删除已保存的密码，下次连接需重新输入。",
    "wifi.forget": "忘记",
    "wifi.cancel": "取消",
}


def t(key):
    return TEXTS[key]
