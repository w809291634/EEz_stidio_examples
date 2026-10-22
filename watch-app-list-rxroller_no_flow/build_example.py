# -*- coding: utf-8 -*-
"""watch-app-list-rxroller —— 手表纵向滚轮应用列表（移植 rxwind7/Rxroller）

本文件是工程唯一设计源：由它生成 .eez-project，请勿手改产物。

    python build_example.py        -> watch-app-list-rxroller.eez-project
    python design/cli_build.py     -> src/ui/（EEZ CLI 生成，勿手改）
    python design/port_rxroller.py -> src/native/rxroller/Rxroller.c（上游 v8 -> 9.4）
    python design/gen_assets.py    -> 22 个图标 + app_rows.{c,h}（事实源 design/apps.py）
    python design/gen_font.py      -> src/ui/fonts/ui_font_cn14.c

**no-flow 口径**（与 app-wifi-scan-flow-no-flow 同一族）：
    settings.general.flowSupport = False
    settings.build.generateSourceCodeForEezFramework = False
⇒ EEZ 只画外壳（标题 / 状态行 / 整屏宿主容器），不发射 eez-flow.h/cpp；
⇒ 列表本体是 native C：上游滚轮件 + src/native/watch_list_native.c 的接线，
   在 ui_init() 之后由 design/sim_cmake/main.c 挂到 objects.list_host 上。

★ 为什么主体不在 EEZ 里：scroll snap 轴与"逐子项 transform_scale"不在 EEZ 属性面内
   （asar 实测：scroll_snap 只在 WASM 符号表与 LVGL 常量字符串表里出现）。
★ 变量表是空的（gvs=[]）：no-flow 下 EEZ 变量必须 native，而状态行文本由 native
   直接 lv_label_set_text，不需要 EEZ 变量参与。
★ 屏上中文名的事实源是 design/apps.py（22 行表）——UI_CJK 由它算，
   所以"改了应用名忘了改字体子集"这种漂移在生成期就会被拦下。
"""
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "watch-app-list-rxroller.eez-project")

SCREEN_W, SCREEN_H = 410, 502   # 与 Design Watch 参考工程同口径（滚轮件按此算行距/弧半径）

# 表盘外形：完全在 EEZ 属性面做（主屏 Radius + Clip corner），生成 screens.c 自带，
# native / 仿真器一行都不用加 —— 仿真器照旧只调 ui_init()/ui_tick()。
# LV_RADIUS_CIRCLE = 0x7FFF，LVGL 内部会钳到短边一半 ⇒ 410x502 上是**胶囊**
# （左右两端半圆、上下各留 502-410=92px 直边），不是正圆；正圆要方形分辨率。
# ★ settings.general.circularDisplay 那个总开关只是编辑器预览的 CSS，不进代码生成器，
#   所以这里用控件级 radius/clip_corner，而不是依赖它。
SCREEN_RADIUS = 0x7FFF           # LV_RADIUS_CIRCLE

# 外壳元素（标题 / 状态行）的安全区：胶囊顶端往下，可用宽度随深度增大。
# 半宽 h 处需要的深度 d = R - sqrt(R^2 - h^2)。取 h=140（带宽 280px，够放 4 个 14px 汉字）
# ⇒ 410x502 上 d≈56。**不这么算就会踩坑**：标题原本贴在直角上 (0,8)，加了圆角后被整个裁掉。
DIAL_R = min(SCREEN_W, SCREEN_H) // 2
DIAL_BAND_HALF_W = 140
DIAL_EDGE_DEPTH = DIAL_R - int((DIAL_R ** 2 - DIAL_BAND_HALF_W ** 2) ** 0.5)
DIAL_BAND_W = DIAL_BAND_HALF_W * 2
DIAL_BAND_X = (SCREEN_W - DIAL_BAND_W) // 2

# ---- 设计令牌（深色，与仓库其它示例一致）----
BG = "0x0b0f1a"
PANEL = "0x101a28"
EDGE = "0x26314a"
BTN = "0x1c2440"
TEXT1 = "0xf0f4fc"
TEXT2 = "0x8a99b3"
ACC = "0x3ddc97"

# --------------------------------------------------------------------------
# 中文字体条目：只烘"UI 上真正会出现的字"，不搬 GB2312 全集。
# ★ 变量在屏上显示的**取值**也是文字（g_status 被写成中文时同样要字形），
#   所以字符集不是手写的——_check_font_coverage() 从生成的工程 JSON 里扫出来比对。
# --------------------------------------------------------------------------
FONT_FILE = "fonts/simhei.ttf"      # 相对工程目录（P-0035）
FONT_NAME = "cn14"
import sys as _sys; _sys.path.insert(0, os.path.join(HERE, "design"))
from apps import ui_cjk_chars as _ui_cjk   # 事实源：design/apps.py（22 行表）
UI_CJK = _ui_cjk()


def _filter_by_font_cmap(chars, ttf_path):
    """按 TTF cmap 过滤（P-0125/P-0169）：ranges 里字体没有的字会让 EEZ 提取失败，
    fontTools 缺失时硬失败，绝不把未过滤字符集写进工程。"""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        sys.stderr.write("FATAL: 需要 fontTools 才能按字体 cmap 过滤字符集："
                         "python -m pip install fontTools" + chr(10))
        sys.exit(2)
    f = TTFont(ttf_path, lazy=True)
    cmap = set(f.getBestCmap().keys())
    f.close()
    dropped = [c for c in chars if ord(c) not in cmap]
    if dropped:
        raise SystemExit("字体缺字：%s —— 换字或换文案，别硬写" % "".join(dropped))
    return chars


FONT_CHARS = "".join(sorted(set(chr(c) for c in range(0x20, 0x7F)) | set(UI_CJK)))
# ★ ASCII 0x20-0x7E 必须并入（P-0125），漏了会让拉丁/数字全豆腐
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


def _check_font_coverage(data):
    """工程 JSON 里所有会显示在屏上的非 ASCII 字符必须都在字体子集里。
    description 是编辑器注释、不上屏，排除在外。"""
    blob = json.dumps(data, ensure_ascii=False)
    blob = re.sub(r'"description":\s*"[^"]*"', '""', blob)
    need = {c for c in blob if ord(c) > 0x7F}
    missing = sorted(need - set(FONT_CHARS))
    if missing:
        raise SystemExit("字体字符集缺字：%s ⇒ 加进 UI_CJK 重跑，否则屏上是豆腐"
                         % "".join(missing))
    return len(need)

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}

# flags 是**最终态白名单**，漏写会被反向移除（P-0150）；值取自各控件官方 defaultFlags
DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLButtonWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLContainerWidget": "CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SNAPPABLE",
    "LVGLSliderWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLBarWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, eventHandlers=None, **extra):
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": [], "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [],
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


def label(x, y, w, h, text, color=TEXT1, identifier=None, expr=None):
    """expr 非空 → textType="expression"（读变量）；否则字面量。"""
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
    """按钮：子 label 用 EEZ 原生新建按钮形态（content 尺寸 + align CENTER，
    与官方 defaultValue 逐字段一致——P-0164 坑 20 定论）。
    handlerType="flow"：点击**不是**走 native 动作，而是把 CLICKED 事件送进 Flow。"""
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


# --------------------------------------------------------------------------
# Flow 组件（type 名 = 装机 EEZ Studio 里的类名；属性键名 = classInfo 的 name）
# --------------------------------------------------------------------------
def page(children, flow_components, conns, local_vars):
    screen = widget("LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
                    local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG,
                                                    bg_opa=255,
                                                    radius=SCREEN_RADIUS,
                                                    clip_corner=True)}},
                    children=children)
    return {
        "objID": oid(),
        "components": [screen] + flow_components,
        "connectionLines": conns,
        "localVariables": local_vars,
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
    # ============ 屏外壳：只有三件，全部是 EEZ 能做的部分 ============
    # ★ 列表本体（蜂窝图标 + 穹顶缩放 + 甩动吸附）不在这里，在 src/native/。
    #   EEZ 的 List 是零属性空壳、也做不了逐帧 transform，所以这三件是外壳、
    #   不是界面主体——别指望在 Studio 里看到列表。
    children = [
        # 宿主容器：**整屏**，native 在它内部建可滚动的 pg_obj + 图标。
        # ★ 必须整屏而不是"标题下方的那块"：移植件的穹顶以屏心为不动点
        #   （get_icon_transform_param 用 scr_width/2、scr_height/2），宿主若
        #   被标题挤掉一条，页面中心与曲线中心就错开了。
        # ★ 顺序 = z 序：宿主排第一，标题/状态行浮在上面（列表会滑到它们底下）。
        widget("LVGLContainerWidget", 0, 0, SCREEN_W, SCREEN_H,
               identifier="list_host",
               flags="GESTURE_BUBBLE|SCROLL_CHAIN_VER",
               local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=BG,
                                               bg_opa=0, radius=0)}}),
        label(DIAL_BAND_X, DIAL_EDGE_DEPTH, DIAL_BAND_W, 20,
              "应用列表", TEXT1, "lbl_title"),
        # 状态行：native 在点击图标时写它（"已打开: clock"）
        label(DIAL_BAND_X, SCREEN_H - DIAL_EDGE_DEPTH - 18, DIAL_BAND_W, 18,
              "就绪", ACC, "lbl_status"),
    ]

    # ============ 变量：no-flow 下留空（见模块 docstring） ============
    gvs = []
    local_vars = []

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
                "flowSupport": False,
                "displayWidth": SCREEN_W,
                "displayHeight": SCREEN_H,
                "circularDisplay": True,
                "displayBorderRadius": 232,
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
                "generateSourceCodeForEezFramework": False,
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
        "userPages": [page(children, [], [], [])],
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [font_entry(FONT_NAME, 14,
                             "UI 实际用字子集：%d 字（ASCII + %s）"
                             % (len(FONT_CHARS), UI_CJK))],
        "bitmaps": [], "colors": [],
        "themes": [{"objID": oid(), "name": "Default", "colors": []}],
    }


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
    shown = _check_font_coverage(data)
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written: %s (%d bytes)"
          % (PROJECT_FILE, os.path.getsize(PROJECT_FILE)))
    print("UI 非 ASCII 字符 %d 个，字体子集 %d 字全部覆盖" % (shown, len(FONT_CHARS)))


if __name__ == "__main__":
    main()
