# -*- coding: utf-8 -*-
"""flow-page-timeline-animation —— 页面动画时间线 + Animate 件（EXAMPLE_PLAN ⑮）

本文件是工程唯一设计源：由它生成 .eez-project，请勿手改产物。

    python build_example.py        → flow-page-timeline-animation.eez-project
    python design/cli_build.py     → src/ui/（EEZ CLI 生成，勿手改）

演示点（手册 P3 · P.24–25「EEZ Flow supports animation of page content」+ A2 · P.13）：
  ① 关键帧挂在**控件**上（Widget.timeline 数组），页面只有一个时间线游标；
  ② Animate(from, to, speed) 推的是**页面级**游标：运行时沿 parentFlowState 上溯到页面对象
     （eez-flow.cpp:2650-2672），所以一个 Animate 同时驱动屏上所有带关键帧的控件；
  ③ speed=0 ⇒ **立即跳到 To**（手册原话此时 From 无意义）；
  ④ to < from ⇒ **倒放**（运行时走 `currentTime = start - speed*Δt` 分支）；
  ⑤ seqout **只在到达 To 时**发一次 ⇒ 用 SetVariable 写 g_status 证明"动画放完了"；
  ⑥ start == end 的关键帧 = **"At X s set ..."**（不是动画，是设值）；
  ⑦ Flow.pageTimelinePosition() 可用 Evaluate 读出当前游标（g_pos）。

与 ⑭（A43 `animY/animOpacity` 件级动画）的分工：本例走 GUI 拖关键帧这条**主路**，
   ⑭ 走件级参数化那条路，两者是选型对照，不是重复。

★ 三条从装机包/运行时挖出来、手册没写的事实（写进 flow-understanding/notes）：
  - 关键帧属性缺省由 TimelineKeyframe.beforeLoadHook 补：数字会升成
    {enabled:true, value, easingFunction:"linear"}，缺的 scale/scaleX/scaleY/rotate 补 enabled:false；
  - `controlPoints`（贝塞尔控制点）**只在 left 与 top 同时启用时**才生效
    （controlPointsArray 否则返回 []，退化成线性插值）；
  - 插值是**"从初值重放到当前游标"的纯函数**：每帧从控件创建时的 style 初值算起，
    所以倒放/跳帧都可复现（这也是它能当回归夹具的原因）。
"""
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "flow-page-timeline-animation.eez-project")

SCREEN_W, SCREEN_H = 480, 320

BG = "0x0b0f1a"
CARD = "0x1c2440"
CARD2 = "0x101a28"
EDGE = "0x26314a"
BTN = "0x1c2440"
TEXT1 = "0xf0f4fc"
TEXT2 = "0x8a99b3"
ACC = "0x3ddc97"

# --------------------------------------------------------------------------
# 中文字体：本示例 UI 上出现的中文很少，就按"实际用到的字"烘一个极小子集，
# 不照搬 app-wifi-scan-flow 的 GB2312 全集（那是给任意 SSID 准备的，5MB 源文件）。
# ★ 关键：_check_font_coverage() 会从**生成的工程 JSON** 里扫出所有中文，
#   断言它们都在 FONT_CHARS 里 —— 以后改文案忘了加字，这里直接拒绝生成，
#   而不是等到屏上一片豆腐才发现。
# --------------------------------------------------------------------------
FONT_FILE = "fonts/simhei.ttf"      # 相对工程目录（P-0035）
FONT_NAME = "cn14"

# UI 上真正会显示的汉字（按钮文案 + g_status 的取值）
UI_CJK = "播放跳帧倒放读游标无意义"
FONT_CHARS = "".join(sorted(set(chr(c) for c in range(0x20, 0x7F)) | set(UI_CJK)))
# ★ ASCII 0x20-0x7E 必须并入（P-0125），漏了会让拉丁/数字全豆腐


def _filter_by_font_cmap(chars, ttf_path):
    """按 TTF cmap 过滤：ranges 里任何字体没有的字都会让 EEZ 提取报 extraction failed。
    fontTools 缺失时硬失败，绝不把未过滤字符集写进工程（P-0169 根因）。"""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        sys.stderr.write("FATAL: 需要 fontTools 才能按字体 cmap 过滤字符集："
                         "python -m pip install fontTools" + chr(10))
        sys.exit(2)
    f = TTFont(ttf_path, lazy=True)
    cmap = set(f.getBestCmap().keys())
    f.close()
    kept = [c for c in chars if ord(c) in cmap]
    dropped = [c for c in chars if ord(c) not in cmap]
    if dropped:
        print("font coverage: dropped %d chars not in TTF: %s"
              % (len(dropped), "".join(dropped[:40])))
    if len(kept) != len(chars):
        raise SystemExit("字体缺字：%s —— 换字或换文案，别硬写" % "".join(dropped))
    return "".join(kept)


FONT_CHARS = _filter_by_font_cmap(FONT_CHARS, os.path.join(HERE, FONT_FILE))


def font_entry(name, size, description):
    """EEZ LVGL 字体条目（P-0125 定论：renderingEngine + lvglRanges 数字串 +
    lvglGlyphs.encodings + glyphs 留空，缺一不可）。"""
    cps = sorted({ord(c) for c in FONT_CHARS})
    encodings, ranges = [], []
    start = prev = cps[0]
    for cp in cps[1:]:
        if cp == prev + 1:
            prev = cp
            continue
        encodings.append({"from": start, "to": prev})
        ranges.append(str(start) if start == prev else "%d-%d" % (start, prev))
        start = prev = cp
    encodings.append({"from": start, "to": prev})
    ranges.append(str(start) if start == prev else "%d-%d" % (start, prev))
    return {
        "objID": oid(), "name": name, "description": description,
        "renderingEngine": "LVGL",
        "source": {"objID": oid(), "filePath": FONT_FILE, "size": size},
        "bpp": 4, "threshold": 128, "glyphs": [],
        "screenOrientation": "all", "alwaysBuild": False,
        "lvglRanges": ",".join(ranges),
        "lvglSymbols": "",
        "lvglAdditionalSources": [],
        "lvglGlyphs": {"objID": oid(), "encodings": encodings},
    }


# 缓动函数名白名单：与装机运行时 `float eez_<name>(...)` 的 31 个声明**逐名比对过，
# 差集为空**（2026-10-21）。写错名字不会在构建期报错，只会在链接期炸 `undefined reference
# to eez_easeInTeleport` —— 所以宁可在这里拦住。
EASINGS = {
    "linear",
    "easeInQuad", "easeOutQuad", "easeInOutQuad",
    "easeInCubic", "easeOutCubic", "easeInOutCubic",
    "easeInQuart", "easeOutQuart", "easeInOutQuart",
    "easeInQuint", "easeOutQuint", "easeInOutQuint",
    "easeInSine", "easeOutSine", "easeInOutSine",
    "easeInExpo", "easeOutExpo", "easeInOutExpo",
    "easeInCirc", "easeOutCirc", "easeInOutCirc",
    "easeInBack", "easeOutBack", "easeInOutBack",
    "easeInElastic", "easeOutElastic", "easeInOutElastic",
    "easeInBounce", "easeOutBounce", "easeInOutBounce",
}

# 关键帧可动的属性（TimelineKeyframe 类字段）
KF_PROPS = {"left", "top", "width", "height", "scale", "scaleX", "scaleY",
            "rotate", "opacity"}

TIMELINE_END = 3.0        # 页面时间线总长（秒），= 最后一个关键帧的 end

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}

DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLContainerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SNAPPABLE",
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, eventHandlers=None, timeline=None, **extra):
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": [], "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        # ★ 页面时间线的关键帧就挂在这里（Widget 级），游标在页面级
        "timeline": timeline or [],
        "eventHandlers": eventHandlers or [],
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "children": children if children is not None else [],
        "widgetFlags": flags if flags is not None else DEFAULT_FLAGS[wtype],
        "hiddenFlagType": "literal", "hiddenFlag": False,
        "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF",
        "checkedStateType": "literal", "disabledStateType": "literal",
        "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def keyframe(start, end, **props):
    """一个关键帧：{start,end} 秒 + 若干属性目标值。

    属性写法两种都合法（beforeLoadHook 会把裸数字升成对象）：
      top=120                          → 线性
      opacity={"value":60,"easing":"easeInOutSine"}
    """
    kf = {"objID": oid(), "start": start, "end": end}
    for name, spec in props.items():
        if name not in KF_PROPS:
            raise SystemExit("关键帧属性 %r 不在 TimelineKeyframe 字段集里" % name)
        if isinstance(spec, (int, float)):
            kf[name] = {"enabled": True, "value": spec,
                       "easingFunction": "linear"}
        else:
            easing = spec.get("easing", "linear")
            if easing not in EASINGS:
                raise SystemExit("easing %r 不在装机包 easingFunctions 表里" % easing)
            kf[name] = {"enabled": True, "value": spec["value"],
                        "easingFunction": easing}
    return kf


def label(x, y, w, h, text, color=TEXT1, identifier=None, expr=None):
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, text_color=color,
                                               text_font=FONT_NAME)}},
        text=text if expr is None else expr,
        textType="literal" if expr is None else "expression",
        longMode="WRAP", recolor=False, useStaticText=True,
    )


def button(x, y, w, h, text, identifier):
    lbl = {
        "objID": oid(), "type": "LVGLLabelWidget",
        "left": 0, "top": 0, "width": 80, "height": 32,
        "widthUnit": "content", "heightUnit": "content",
        "text": text, "textType": "literal", "longMode": "WRAP",
        "recolor": False, "useStaticText": True,
        "localStyles": {"objID": oid(), "definition": {"MAIN": {"DEFAULT": {
            "align": "CENTER", "text_color": "0xFFFFFF",
            "text_font": FONT_NAME}}}},
    }
    return widget(
        "LVGLButtonWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BTN, bg_opa=255,
                                        radius=8, border_width=1,
                                        border_color=EDGE)}},
        children=[lbl],
        eventHandlers=[{"objID": oid(), "eventName": "CLICKED",
                        "handlerType": "flow", "userData": 0}],
    )


def action_component(ctype, x, y, w, h, description="", inputs=None,
                     outputs=None, **props):
    return {
        "objID": oid(),
        "type": ctype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": inputs or [],
        "customOutputs": outputs or [],
        "description": description,
        **props,
    }


def animate(to, speed, frm="Flow.pageTimelinePosition()", description="Animate",
            x=0, y=0):
    """A2 Animate：属性键 from / to / speed（都是表达式），端口 @seqin/@seqout。

    默认 from = 当前游标 ⇒ 从"现在的位置"接着播（手册 P.13 明确推荐这种写法）。
    """
    # 注意：JSON 键叫 from，但 from 是 Python 关键字 ⇒ 只能走 **dict 展开
    return action_component("AnimateActionComponent", x, y, 200, 60,
                            description, [], [],
                            **{"from": frm, "to": to, "speed": speed})


def set_var(entries, x, y, description="SetVariable", inputs=None):
    return action_component(
        "SetVariableActionComponent", x, y, 200, 60, description, inputs, [],
        entries=[{"objID": oid(), "variable": k, "value": v} for k, v in entries])


def data_input(name, vtype="any"):
    return {"objID": oid(), "name": name, "type": vtype}


def line(src, output, dst, inp):
    return {"objID": oid(), "source": src, "output": output,
            "target": dst, "input": inp}


def page(children, flow_components, conns):
    screen = widget("LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
                    local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG,
                                                    bg_opa=255, radius=0)}},
                    children=children)
    return {
        "objID": oid(),
        "components": [screen] + flow_components,
        "connectionLines": conns,
        "localVariables": [],
        "componentGroups": [],
        "userProperties": [],
        "name": "Main",
        "left": 0, "top": 0,
        "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False,
        "createAtStart": True,
        "deleteOnScreenUnload": False,
    }


def build_project():
    # ============ 1. 被时间线驱动的控件 ============
    # 主角：一条三段关键帧 —— 斜向上滑 → 边转边淡出 → 末尾"设值不插值"
    card = widget("LVGLContainerWidget", 24, 120, 96, 96, identifier="card",
                  flags="GESTURE_BUBBLE|SCROLL_CHAIN_VER",
                  local={"MAIN": {"DEFAULT": dict(
                      ZERO_PAD, bg_color=CARD, bg_opa=255, radius=12,
                      border_width=2, border_color=EDGE)}},
                  timeline=[
                      keyframe(0.0, 1.0,
                               left={"value": 300, "easing": "easeInOutCubic"},
                               top={"value": 60, "easing": "easeOutBack"}),
                      keyframe(1.0, 2.0,
                               # ★ opacity 用 0..1：codegen 读初值时除以 255、
                               #   写回时再乘 255，所以这里写 70 会被夹成全不透明
                               # ★ rotate 用 0.1°：codegen 把值原样 roundf 后塞进
                               #   LV_STYLE_TRANSFORM_ROTATION（screens.c:487），
                               #   LVGL 该属性单位是 0.1° ⇒ 45 只转 4.5°，450 才是 45°
                               rotate={"value": 450, "easing": "easeInOutSine"},
                               opacity={"value": 0.27, "easing": "linear"}),
                      # start == end ⇒ 手册 Fig.35 语义里的 "At 2.0 s set ..."
                      keyframe(2.0, 2.0,
                               width={"value": 150, "easing": "linear"}),
                      keyframe(2.0, TIMELINE_END,
                               left={"value": 40, "easing": "easeInOutQuad"},
                               top={"value": 150, "easing": "easeInOutQuad"},
                               # 回程把姿态也收回正位（和 left/top 同区间 ⇒ 必须同一帧）
                               rotate={"value": 0, "easing": "easeInOutQuad"}),
                  ])

    # 配角：同一条游标驱动第二个控件（证明"页面一条线、多控件共用"）
    # 底部进度条：创建时 width=40，一条关键帧 0→3s 拉到 424 ⇒ 与卡片共用同一个游标，
    # 天然成为"动画进度条"。★ 同区间的属性必须写在**同一帧**里（见 _check_keyframes 的注释）。
    shadow = widget("LVGLContainerWidget", 24, 232, 40, 8, identifier="shadow",
                    flags="",
                    local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=CARD2,
                                                    bg_opa=255, radius=4)}},
                    timeline=[
                        keyframe(0.0, TIMELINE_END,
                                 width={"value": 424, "easing": "easeInOutQuad"},
                                 top={"value": 246, "easing": "linear"}),
                    ])

    w_play = button(16, 256, 104, 30, "播放", "btn_play")
    w_jump = button(128, 256, 104, 30, "跳帧(speed=0)", "btn_jump")
    w_rew = button(240, 256, 104, 30, "倒放", "btn_rew")
    w_probe = button(352, 256, 112, 30, "读游标", "btn_probe")

    # ★ 顺序 = LVGL 创建顺序 = z 序（后面的在上面）。card 的滑动路径会经过两条读数
    #   标签（lbl_pos y=200 / lbl_hint y=220），所以两个动画控件必须排在标签**前面**，
    #   否则播放到中段时卡片会把读数盖成看不见（0.27 透明度的卡片压在文字上）。
    children = [
        card, shadow,
        label(16, 10, 448, 20, "EEZ Flow - page animation timeline + Animate",
              TEXT1, "lbl_title"),
        label(16, 34, 448, 18, "", ACC, "lbl_status", expr="g_status"),
        label(16, 200, 448, 18, "", TEXT2, "lbl_pos",
              expr="`timeline cursor = ${g_pos} s   (range 0 .. 3 s)`"),
        label(16, 220, 448, 16,
              "slide (0-1s) -> rotate 45deg + fade (1-2s) -> width@2s -> back (2-3s)",
              TEXT2, "lbl_hint"),
        w_play, w_jump, w_rew, w_probe,
    ]

    # ============ 2. 流图 ============
    f_start = action_component("StartActionComponent", 16, 320, 180, 40,
                               description="流启动（无输入 ⇒ 启动即执行，P6.2）")
    f_ready = set_var([('g_status', '"ready (cursor at 0)"')], 240, 320,
                      description="启动：状态复位")
    f_play = animate(str(TIMELINE_END), "1",
                     description="⑤ 放到终点：seqout 到达才发", x=16, y=392)
    f_play_done = set_var([('g_status', '"finished: seqout fired"')], 16, 464,
                          description="⑤ 证明 seqout 只放完才发")
    f_jump = animate(str(TIMELINE_END), "0", frm=str(TIMELINE_END),
                     description="③ speed=0 ⇒ 立即跳帧", x=240, y=392)
    f_jump_done = set_var([('g_status', '"jumped (speed=0, From 无意义)"')],
                          240, 464, description="跳帧后状态")
    f_rew = animate("0", "2",
                    description="④ to < from ⇒ 倒放回 0", x=464, y=392)
    f_rew_done = set_var([('g_status', '"rewound to 0"')], 464, 464,
                          description="倒放完成")
    f_probe = action_component("EvalExprActionComponent", 688, 392, 180, 60,
                               description="⑦ 读页面时间线游标",
                               expression="Flow.pageTimelinePosition()")
    f_probe_store = set_var([("g_pos", "r")], 688, 464,
                            description="⑦ 游标写进 g_pos",
                            inputs=[data_input("r")])

    flow_components = [f_start, f_ready, f_play, f_play_done, f_jump,
                       f_jump_done, f_rew, f_rew_done, f_probe, f_probe_store]

    conns = [
        # 按钮事件进流：CLICKED → @seqin
        line(w_play["objID"], "CLICKED", f_play["objID"], "@seqin"),
        line(w_jump["objID"], "CLICKED", f_jump["objID"], "@seqin"),
        line(w_rew["objID"], "CLICKED", f_rew["objID"], "@seqin"),
        line(w_probe["objID"], "CLICKED", f_probe["objID"], "@seqin"),
        line(f_start["objID"], "@seqout", f_ready["objID"], "@seqin"),
        line(f_play["objID"], "@seqout", f_play_done["objID"], "@seqin"),
        line(f_jump["objID"], "@seqout", f_jump_done["objID"], "@seqin"),
        line(f_rew["objID"], "@seqout", f_rew_done["objID"], "@seqin"),
        line(f_probe["objID"], "@seqout", f_probe_store["objID"], "@seqin"),
        line(f_probe["objID"], "result", f_probe_store["objID"], "r"),
    ]


    # ============ 3. 变量 ============
    gvs = [
        {"objID": oid(), "name": "g_status", "type": "string",
         "defaultValue": '"boot"', "persistent": False, "native": False},
        {"objID": oid(), "name": "g_pos", "type": "float",
         "defaultValue": "0", "persistent": False, "native": False},
    ]

    return {
        "themesVersion": 1, "objID": oid(),
        "settings": {
            "objID": oid(),
            "general": {
                "objID": oid(),
                "projectVersion": "v3",
                "projectType": "lvgl",
                "lvglVersion": "9.4.0",
                "extensions": [],
                "imports": [],
                "flowSupport": True,
                "displayWidth": SCREEN_W,
                "displayHeight": SCREEN_H,
                "circularDisplay": False,
                "displayBorderRadius": 0,
                "darkTheme": True,
                "colorBpp": "16",
                "bitmapColorFormat": "BGR",
                "resourceFiles": [],
                "hiddenWidgetLines": "dimmed",
                "dimmedLinesOpacity": "20",
                "embedBitmaps": True,
                "embedFonts": True,
                "cacheFonts": True,
            },
            "build": {
                "objID": oid(),
                "configurations": [{"objID": oid(), "name": "Default"}],
                "destinationFolder": "src\\ui",
                "separateFolderForImagesAndFonts": True,
                "imageExportMode": "source",
                "fontExportMode": "source",
                "fileSystemPath": "",
                "lvglInclude": "lvgl.h",
                "screensLifetimeSupport": False,
                "useDockerDesktop": True,
                "generateSourceCodeForEezFramework": True,
                "compressFlowDefinition": False,
                "executionQueueSize": 1000,
                "expressionEvaluatorStackSize": 20,
                "files": [
                    {"objID": oid(), "fileName": name, "template": tmpl}
                    for name, tmpl in BUILD_TEMPLATES.items()
                ],
            },
        },
        "variables": {
            "objID": oid(),
            "globalVariables": gvs,
            "structures": [], "enums": [],
        },
        "actions": [],
        "userPages": [page(children, flow_components, conns)],
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [font_entry(FONT_NAME, 14,
                             "UI 实际用字子集：%d 字（ASCII + %s）"
                             % (len(FONT_CHARS), UI_CJK))],
        "bitmaps": [], "colors": [],
        "themes": [{"objID": oid(), "name": "Default", "colors": []}],
    }


# --------------------------------------------------------------------------
# 交付前自检（机器断言，不靠眼睛）
# --------------------------------------------------------------------------
def _check_font_coverage(data):
    """扫生成的工程 JSON：任何出现在 UI 文本里的中文都必须在 FONT_CHARS 内。

    覆盖范围 = 控件 text / 表达式里的字符串字面量 / 变量默认值 / SetVariable 的 value。
    （流件的 description 只是编辑器批注、不进 UI，故排除。）
    """
    blob = json.dumps(data, ensure_ascii=False)
    # 去掉 description 字段值再扫：它不会显示到屏上
    blob = re.sub(r'"description":\s*"[^"]*"', '""', blob)
    need = {c for c in blob if ord(c) > 0x7F}
    missing = sorted(need - set(FONT_CHARS))
    if missing:
        raise SystemExit("字体字符集缺字：%s ⇒ 加进 UI_CJK 重跑，否则屏上是豆腐"
                         % "".join(missing))
    return len(need)


def _check_keyframes(page_obj):
    """关键帧合法性：属性名、缓动名、单控件内时间不倒序、总长不超过 Animate 目标。

    ★ 每个控件各自一条关键帧序列（游标共享），所以 last_end **逐控件重置**——
      跨控件累计会把两个独立时间轴当成一条来判，误报重叠。
    ★ **同区间拆两帧是无效的**：生成的 C 里命中第一个满足 `start <= pos < end` 的帧就
      `break`（装机包 `lvglBuildPageTimeline`），所以同一时刻要一起动的属性**必须写进同一帧**。
      这条不是风格建议，是 codegen 行为——违反它会出现"只有一半属性在动"的诡异现象。
    """
    overall = 0.0
    for w in _walk_widgets(page_obj):
        last_end = 0.0
        for kf in w.get("timeline", []):
            for name in list(kf):
                if name in ("objID", "start", "end", "controlPoints"):
                    continue
                if name not in KF_PROPS:
                    raise SystemExit("非法关键帧属性 %s（%s）" % (name, w["identifier"]))
                if kf[name]["easingFunction"] not in EASINGS:
                    raise SystemExit("非法缓动 %s" % kf[name]["easingFunction"])
            if "opacity" in kf and not (0.0 <= kf["opacity"]["value"] <= 1.0):
                raise SystemExit("opacity 关键帧值 %s 越界：这里是 0..1 域，不是 0..255"
                                 % kf["opacity"]["value"])
            if "rotate" in kf and not (0 <= abs(kf["rotate"]["value"]) <= 3600):
                raise SystemExit("rotate 关键帧值 %s 越界：单位是 0.1°（3600 = 360°），"
                                 "填 45 只会转 4.5°" % kf["rotate"]["value"])
            if kf["end"] < kf["start"]:
                raise SystemExit("%s 关键帧 end < start" % w["identifier"])
            if kf["start"] < last_end - 1e-6:
                raise SystemExit("%s 关键帧倒序/重叠：%s 在 %s 之前"
                                 % (w["identifier"], kf["start"], last_end))
            last_end = kf["end"]
        overall = max(overall, last_end)
    if overall > TIMELINE_END + 1e-6:
        raise SystemExit("关键帧总长 %.2fs 超过 Animate 目标 %.2fs"
                         % (overall, TIMELINE_END))
    return overall


def _walk_widgets(node):
    for c in node.get("components", []):
        yield from _walk_children(c)


def _walk_children(node):
    if str(node.get("type", "")).startswith("LVGL") and node.get("timeline") is not None:
        yield node
    for ch in node.get("children", []):
        yield from _walk_children(ch)


def _check_flow_boxes(flow_components):
    boxes = [(c.get("description") or c["type"], c["left"], c["top"],
              c["width"], c["height"]) for c in flow_components]
    for i, (n, x, y, w, h) in enumerate(boxes):
        for n2, x2, y2, w2, h2 in boxes[i + 1:]:
            if x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h:
                raise SystemExit("流组件画布重叠：%s × %s" % (n, n2))


BUILD_TEMPLATES = {
    'screens.h': '#ifndef EEZ_LVGL_UI_SCREENS_H\r\n#define EEZ_LVGL_UI_SCREENS_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_SCREENS_DECL}\r\n//${eez-studio LVGL_SCREENS_DECL_EXT}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_SCREENS_H*/',
    'screens.c': '#include <string.h>\n\n#include "screens.h"\n#include "images.h"\n#include "fonts.h"\n#include "actions.h"\n#include "vars.h"\n#include "styles.h"\n#include "ui.h"\n\n//${eez-studio LVGL_SCREENS_DEF}\n//${eez-studio LVGL_SCREENS_DEF_EXT}',
    'actions.h': '#ifndef EEZ_LVGL_UI_EVENTS_H\r\n#define EEZ_LVGL_UI_EVENTS_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_ACTIONS_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_EVENTS_H*/',
    'vars.h': '#ifndef EEZ_LVGL_UI_VARS_H\r\n#define EEZ_LVGL_UI_VARS_H\r\n\r\n#include <stdint.h>\r\n#include <stdbool.h>\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n// enum declarations\r\n\r\n//${eez-studio FLOW_ENUMS}\r\n\r\n// Flow global variables\r\n\r\n//${eez-studio FLOW_GLOBAL_VARIABLES_ENUM}\r\n\r\n// Native global variables\r\n\r\n//${eez-studio LVGL_VARS_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_VARS_H*/',
    'structs.h': '#ifndef EEZ_LVGL_UI_STRUCTS_H\n#define EEZ_LVGL_UI_STRUCTS_H\n\n//${eez-studio EEZ_FOR_LVGL_CHECK}\n\n#if defined(EEZ_FOR_LVGL)\n\n#include <eez/flow/flow.h>\n#include <stdint.h>\n#include <stdbool.h>\n\n#include "vars.h"\n\nusing namespace eez;\n\n//${eez-studio FLOW_STRUCTS}\n\n//${eez-studio FLOW_STRUCT_VALUES}\n\n#endif\n\n#endif /*EEZ_LVGL_UI_STRUCTS_H*/\n',
    'images.h': '#ifndef EEZ_LVGL_UI_IMAGES_H\r\n#define EEZ_LVGL_UI_IMAGES_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_IMAGES_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_IMAGES_H*/',
    'images.c': '#include "images.h"\n\n//${eez-studio LVGL_IMAGES_DEF}',
    'fonts.h': '#ifndef EEZ_LVGL_UI_FONTS_H\r\n#define EEZ_LVGL_UI_FONTS_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_FONTS_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_FONTS_H*/',
    'styles.h': '#ifndef EEZ_LVGL_UI_STYLES_H\r\n#define EEZ_LVGL_UI_STYLES_H\r\n\r\n//${eez-studio LVGL_INCLUDE}\r\n\r\n#ifdef __cplusplus\r\nextern "C" {\r\n#endif\r\n\r\n//${eez-studio LVGL_STYLES_DECL}\r\n\r\n#ifdef __cplusplus\r\n}\r\n#endif\r\n\r\n#endif /*EEZ_LVGL_UI_STYLES_H*/',
    'styles.c': '#include "styles.h"\n#include "images.h"\n#include "fonts.h"\n\n//${eez-studio LVGL_STYLES_DEF}\n',
    'ui.h': '#ifndef EEZ_LVGL_UI_GUI_H\n#define EEZ_LVGL_UI_GUI_H\n\n//${eez-studio LVGL_INCLUDE}\n\n//${eez-studio EEZ_FOR_LVGL_CHECK}\n\n#if defined(EEZ_FOR_LVGL)\n#include <eez/flow/lvgl_api.h>\n#endif\n\n#if !defined(EEZ_FOR_LVGL)\n#include "screens.h"\n#endif\n\n#ifdef __cplusplus\nextern "C" {\n#endif\n\n//${eez-studio GUI_ASSETS_DECL}\n\nvoid ui_init();\nvoid ui_tick();\n\n#if !defined(EEZ_FOR_LVGL)\nvoid loadScreen(enum ScreensEnum screenId);\n#endif\n\n#ifdef __cplusplus\n}\n#endif\n\n#endif // EEZ_LVGL_UI_GUI_H',
    'ui.c': '#if defined(EEZ_FOR_LVGL)\n#include <eez/core/vars.h>\n#endif\n\n#include "ui.h"\n#include "screens.h"\n#include "images.h"\n#include "actions.h"\n#include "vars.h"\n\n//${eez-studio GUI_ASSETS_DEF}\n\n//${eez-studio LVGL_NATIVE_VARS_TABLE_DEF}\n\n//${eez-studio LVGL_ACTIONS_ARRAY_DEF}\n\n#if defined(EEZ_FOR_LVGL)\n\nvoid ui_init() {\n    eez_flow_init(assets, sizeof(assets), (lv_obj_t **)&objects, sizeof(objects), images, sizeof(images), actions);\n}\n\nvoid ui_tick() {\n    eez_flow_tick();\n    tick_screen(g_currentScreen);\n}\n\n#else\n\nstatic int16_t currentScreen = -1;\n\nstatic lv_obj_t *getLvglObjectFromIndex(int32_t index) {\n    if (index == -1) {\n        return 0;\n    }\n    return ((lv_obj_t **)&objects)[index];\n}\n\nvoid loadScreen(enum ScreensEnum screenId) {\n    currentScreen = screenId - 1;\n    lv_obj_t *screen = getLvglObjectFromIndex(currentScreen);\n    lv_scr_load_anim(screen, LV_SCR_LOAD_ANIM_FADE_IN, 200, 0, false);\n}\n\nvoid ui_init() {\n    create_screens();\n//${eez-studio LVGL_LOAD_FIRST_SCREEN}\n}\n\nvoid ui_tick() {\n    tick_screen(currentScreen);\n}\n\n#endif\n',
}


def main():
    data = build_project()
    pg = data["userPages"][0]
    total = _check_keyframes(pg)
    _check_flow_boxes(pg["components"][1:])
    shown = _check_font_coverage(data)
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written: %s (%d bytes)"
          % (PROJECT_FILE, os.path.getsize(PROJECT_FILE)))
    print("timeline 长度 %.1fs；控件带关键帧数：%d；UI 非 ASCII 字符 %d 个，"
          "字体子集 %d 字全部覆盖"
          % (total, sum(1 for w in _walk_widgets(pg) if w.get("timeline")),
             shown, len(FONT_CHARS)))


if __name__ == "__main__":
    main()
