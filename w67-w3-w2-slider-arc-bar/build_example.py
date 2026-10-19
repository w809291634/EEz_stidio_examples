# -*- coding: utf-8 -*-
"""w67-w3-w2-slider-arc-bar（W67 Slider / W3 Bar / W2 Arc）—— 调节与指示：手册全属性覆盖（A 级组合 1/5）

本文件是示例的唯一设计源：w67-w3-w2-slider-arc-bar.eez-project 由它生成，请勿手改产物。

    python build_example.py

演示点（★ 要求：所含控件的手册属性全部覆盖）：

  flow 全局变量：g_val(25) / g_val_left(10)，联动关系：
    拖 slider_range 左 knob → g_val_left → bar_range 的 valueStart 跟随；
    拖 slider_range 右 knob / arc 任意一个 → g_val → 其余全部跟随。

  Slider ×3（4 属性全覆盖：min/max/value/mode/valueLeft/enableAnimation）：
    slider_normal  mode=NORMAL  value=g_val(expr)
    slider_range   mode=RANGE   value=g_val(expr) + valueLeft=g_val_left(expr)
                   + enableAnimation=true（RANGE 专属双 knob 属性）
    slider_sym     mode=SYMMETRICAL  value=60(literal)
  Bar ×3（min/max/value/mode/valueStart/enableAnimation）：
    bar_normal     mode=NORMAL  value=g_val(expr) + enableAnimation=true
    bar_range      mode=RANGE   value=g_val(expr) + valueStart=g_val_left(expr)
    bar_sym        mode=SYMMETRICAL  value=70(literal)
  Arc ×3（useAngle/rangeMin/rangeMax/value/mode/startAngle/endAngle/
          bgStartAngle/bgEndAngle/rotation）：
    arc_normal     mode=NORMAL      useAngle=false  value=g_val(expr)
    arc_sym        mode=SYMMETRICAL useAngle=true   start=180 end=0
                   bg 180..0        rotation=90     value=g_val(expr)
    arc_reverse    mode=REVERSE     useAngle=false  value=g_val(expr)
  （previewValue/preview*Type 为编辑器预览专用，不进生成代码，无需演示）

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（projectVersion=v3）。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "w67-w3-w2-slider-arc-bar.eez-project")

SCREEN_W, SCREEN_H = 480, 320

# ---------------------------------------------------------------------------
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

# flags = 官方默认（P-0150：最终态白名单，勿裁）
DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    # Slider v9（asar 101160719 + lvgl 函数式定义）
    "LVGLSliderWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_ON_FOCUS|SCROLL_WITH_ARROW|SNAPPABLE",
    # Bar（无 SCROLLABLE）
    "LVGLBarWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    # Arc（无 SCROLLABLE、无 CHAIN）
    "LVGLArcWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
}

ZERO_PAD = {
    "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
    "pad_row": 0, "pad_column": 0, "border_width": 0, "outline_width": 0,
}


def oid():
    return str(uuid.uuid4())


def widget(wtype, x, y, w, h, identifier=None, flags=None, local=None,
           children=None, **extra):
    wd = {
        "objID": oid(),
        "type": wtype,
        "left": x, "top": y, "width": w, "height": h,
        "customInputs": [],
        "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [],
        "eventHandlers": [],
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "children": children if children is not None else [],
        "widgetFlags": flags if flags is not None else DEFAULT_FLAGS[wtype],
        "hiddenFlagType": "literal",
        "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF",
        "checkedStateType": "literal",
        "disabledStateType": "literal",
        "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None, expr=None):
    props = dict(ZERO_PAD, text_color=color)
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": props}},
        text=text if expr is None else expr,
        textType="literal" if expr is None else "expression",
        longMode="WRAP", recolor=False, useStaticText=True,
    )


def caption(x, y, w, text, color="0x8A94A6"):
    return label(x, y, w, 16, text, color=color)


def build_project():
    children = []
    children.append(label(
        16, 6, 448, 24,
        "slider-arc-bar: every manual property demonstrated (see captions)",
        color="0xFFFFFF", identifier="lbl_title"))

    # ---------------- Slider 行：NORMAL / RANGE / SYMMETRICAL ----------------
    children.append(caption(24, 36, 200, "Slider NORMAL (value=g_val)"))
    children.append(caption(256, 36, 200,
                            "Slider RANGE (value=g_val, valueLeft=g_val_left)"))
    children.append(caption(24, 128, 200, "Slider SYMMETRICAL (value=60)"))
    children += [
        widget("LVGLSliderWidget", 24, 56, 200, 24,
               identifier="slider_normal",
               min=0, minType="literal", max=100, maxType="literal",
               mode="NORMAL", value="g_val", valueType="expression",
               previewValue=25, enableAnimation=False),
        widget("LVGLSliderWidget", 256, 56, 200, 24,
               identifier="slider_range",
               min=0, minType="literal", max=100, maxType="literal",
               mode="RANGE", value="g_val", valueType="expression",
               valueLeft="g_val_left", valueLeftType="expression",
               previewValue=25, previewValueLeft=10,
               enableAnimation=True),
        widget("LVGLSliderWidget", 24, 148, 200, 24,
               identifier="slider_sym",
               min=0, minType="literal", max=100, maxType="literal",
               mode="SYMMETRICAL", value=60, valueType="literal",
               previewValue=60, enableAnimation=False),
    ]

    # ---------------- Bar 行：NORMAL / RANGE / SYMMETRICAL ----------------
    children.append(caption(256, 128, 200,
                            "Bar RANGE (value=g_val, valueStart=g_val_left)"))
    children += [
        widget("LVGLBarWidget", 256, 148, 200, 22,
               identifier="bar_range",
               min=0, minType="literal", max=100, maxType="literal",
               mode="RANGE", value="g_val", valueType="expression",
               valueStart="g_val_left", valueStartType="expression",
               previewValue="25", previewValueStart="10",
               enableAnimation=True),
    ]

    # ---------------- Bar NORMAL + SYMMETRICAL（放在 Slider 行下方空位）-------
    children.append(caption(24, 180, 200, "Bar NORMAL (value=g_val, anim)"))
    children.append(caption(256, 180, 200, "Bar SYMMETRICAL (value=70)"))
    children += [
        widget("LVGLBarWidget", 24, 200, 200, 22,
               identifier="bar_normal",
               min=0, minType="literal", max=100, maxType="literal",
               mode="NORMAL", value="g_val", valueType="expression",
               previewValue="25", enableAnimation=True),
        widget("LVGLBarWidget", 256, 200, 200, 22,
               identifier="bar_sym",
               min=0, minType="literal", max=100, maxType="literal",
               mode="SYMMETRICAL", value=70, valueType="literal",
               previewValue="70", enableAnimation=False),
    ]

    # ---------------- Arc 列：NORMAL / SYMMETRICAL+useAngle / REVERSE --------
    children.append(caption(30, 236, 100, "Arc NORMAL"))
    children.append(caption(185, 236, 120, "Arc SYMMETRICAL + useAngle + rot90"))
    children.append(caption(345, 236, 110, "Arc REVERSE"))
    arc_common = dict(
        rangeMin=0, rangeMinType="literal",
        rangeMax=100, rangeMaxType="literal",
        value="g_val", valueType="expression", previewValue="25",
    )
    children += [
        widget("LVGLArcWidget", 30, 258, 60, 60,
               identifier="arc_normal",
               useAngle=False, mode="NORMAL",
               startAngle=135, startAngleType="literal", previewStartAngle="135",
               endAngle=45, endAngleType="literal", previewEndAngle="45",
               bgStartAngle=135, bgStartAngleType="literal", previewBgStartAngle="135",
               bgEndAngle=45, bgEndAngleType="literal", previewBgEndAngle="45",
               rotation=0, rotationType="literal", previewRotation="0",
               local={"INDICATOR": {"DEFAULT": dict(ZERO_PAD,
                                                    bg_color="0xE0566A", bg_opa=255)}},
               **arc_common),
        widget("LVGLArcWidget", 195, 258, 60, 60,
               identifier="arc_sym",
               useAngle=True, mode="SYMMETRICAL",
               startAngle=180, startAngleType="literal", previewStartAngle="180",
               endAngle=0, endAngleType="literal", previewEndAngle="0",
               bgStartAngle=180, bgStartAngleType="literal", previewBgStartAngle="180",
               bgEndAngle=0, bgEndAngleType="literal", previewBgEndAngle="0",
               rotation=90, rotationType="literal", previewRotation="90",
               local={"INDICATOR": {"DEFAULT": dict(ZERO_PAD,
                                                    bg_color="0x5B7CFA", bg_opa=255)}},
               **arc_common),
        widget("LVGLArcWidget", 355, 258, 60, 60,
               identifier="arc_reverse",
               useAngle=False, mode="REVERSE",
               startAngle=135, startAngleType="literal", previewStartAngle="135",
               endAngle=45, endAngleType="literal", previewEndAngle="45",
               bgStartAngle=135, bgStartAngleType="literal", previewBgStartAngle="135",
               bgEndAngle=45, bgEndAngleType="literal", previewBgEndAngle="45",
               rotation=0, rotationType="literal", previewRotation="0",
               local={"INDICATOR": {"DEFAULT": dict(ZERO_PAD,
                                                    bg_color="0x4C8C4C", bg_opa=255)}},
               **arc_common),
    ]
    # 底部变量实时值（演示多变量拼接）
    children.append(label(
        16, 302, 448, 16, None, color="0x8FD3FF", identifier="lbl_vars",
        expr='"g_val=" + g_val + "   g_val_left=" + g_val_left'))

    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_main",
        local={"MAIN": {"DEFAULT": {
            "bg_color": "0x101828", "bg_opa": 255, "radius": 0,
            "border_width": 0}}},
        children=children,
    )
    page = {
        "objID": oid(),
        "components": [screen],
        "connectionLines": [],
        "localVariables": [],
        "componentGroups": [],
        "userProperties": [],
        "name": "Main",
        "left": 0, "top": 0, "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False,
        "createAtStart": True,
        "deleteOnScreenUnload": False,
    }
    return {
        "themesVersion": 1,
        "objID": oid(),
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
            "globalVariables": [
                {"objID": oid(), "name": "g_val",
                 "type": "integer", "defaultValue": "25",
                 "persistent": False, "native": False},
                {"objID": oid(), "name": "g_val_left",
                 "type": "integer", "defaultValue": "10",
                 "persistent": False, "native": False},
            ],
            "structures": [], "enums": [],
        },
        "actions": [],
        "userPages": [page],
        "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [],
        "bitmaps": [],
        "colors": [],
        "themes": [{"objID": oid(), "name": "Default", "colors": []}],
    }


def main():
    data = build_project()
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written: %s (%d bytes)"
          % (PROJECT_FILE, os.path.getsize(PROJECT_FILE)))


if __name__ == "__main__":
    main()
