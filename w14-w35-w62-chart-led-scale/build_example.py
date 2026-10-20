# -*- coding: utf-8 -*-
"""w14-w35-w62-chart-led-scale —— 数据可视化与状态指示（A 级组合 2/5）

本文件是示例的唯一设计源：由它生成 .eez-project，请勿手改产物。

    python build_example.py

覆盖控件（手册 W14 Chart / W35 Led / W62 Scale）与属性：

  W14 Chart：EEZ 中是**空壳**（零属性，仅 lv_chart_create）——series/数据/样式
    全部在 main.c 的 ui_init() 之后用 C 补（lv_chart_add_series + 定时喂数据）。
    这是 Chart 在 EEZ 的唯一用法（同 List，见 app-list-scroll）。
  W35 Led：color 与 brightness 都是 **integer expression**（手册：亮度 0~255）——
    两个 Led 分别绑定 flow 变量 g_color / g_bright，演示"运行时可变色/可调亮度"。
  W62 Scale：EEZ 9.x 可配（**Meter 仅 LVGL 8.x 可用，9.4 面板里没有**，故用 Scale
    替代仪表）。演示 scaleMode/min/max/angleRange/rotation/totalTickCount/
    majorTickEvery/showLabels 全关键属性。

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（projectVersion=v3）。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "w14-w35-w62-chart-led-scale.eez-project")

SCREEN_W, SCREEN_H = 480, 320

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
    # Chart：EEZ 空壳（零属性），官方默认 flags（含 SCROLLABLE）
    "LVGLChartWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLLedWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    "LVGLScaleWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
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
        "customInputs": [], "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [], "eventHandlers": [],
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "children": children if children is not None else [],
        "widgetFlags": flags if flags is not None else DEFAULT_FLAGS[wtype],
        "hiddenFlagType": "literal", "clickableFlagType": "literal",
        "flagScrollbarMode": "OFF", "checkedStateType": "literal",
        "disabledStateType": "literal", "states": "",
        "localStyles": {"objID": oid(), "definition": local or {}},
        "groupIndex": 0,
    }
    if identifier:
        wd["identifier"] = identifier
    wd.update(extra)
    return wd


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None, expr=None):
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, text_color=color)}},
        text=text if expr is None else expr,
        textType="literal" if expr is None else "expression",
        longMode="WRAP", recolor=False, useStaticText=True,
    )


def build_project():
    # W14 Chart：EEZ 空壳，series 由 main.c 在 ui_init() 后 C 补
    chart = widget(
        "LVGLChartWidget", 16, 40, 300, 180,
        identifier="chart_main",
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color="0x0C1220",
                                        bg_opa=255, radius=8)}},
    )

    # W35 Led：color / brightness 都走 expression（手册：brightness 0~255）
    led_color = widget(
        "LVGLLedWidget", 344, 56, 48, 48,
        identifier="led_color",
        color="g_color", colorType="expression",
        brightness=255, brightnessType="literal",
    )
    led_bright = widget(
        "LVGLLedWidget", 344, 140, 48, 48,
        identifier="led_bright",
        color="0x00FF00", colorType="literal",
        brightness="g_bright", brightnessType="expression",
    )

    # W62 Scale：关键属性全显式（手册：scaleMode/min/max/angleRange/rotation/
    # totalTickCount/majorTickEvery/showLabels）
    scale = widget(
        "LVGLScaleWidget", 16, 240, 448, 48,
        identifier="scale_main",
        scaleMode="HORIZONTAL_BOTTOM",
        minValue=0, minValueType="literal",
        maxValue=100, maxValueType="literal",
        angleRange=270, rotation=135, rotationType="literal",
        totalTickCount=31, majorTickEvery=5,
        postDraw=False, drawTicksOnTop=False, showLabels=True,
        labelTexts="", sections=[],
    )

    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_main",
        local={"MAIN": {"DEFAULT": {
            "bg_color": "0x101828", "bg_opa": 255, "radius": 0,
            "border_width": 0}}},
        children=[
            label(16, 8, 448, 24,
                  "W14 Chart (C-fed) | W35 Led (bound) | W62 Scale",
                  color="0xFFFFFF", identifier="lbl_title"),
            chart,
            label(336, 56, 128, 20, "color = g_color",
                  color="0x8FD3FF", identifier="lbl_led1"),
            label(336, 140, 128, 20, "brightness = g_bright",
                  color="0xFFD38F", identifier="lbl_led2"),
            label(336, 190, 128, 40,
                  "leds follow flow vars g_color / g_bright",
                  color="0x8A94A6", identifier="lbl_hint"),
            scale,
            label(16, 294, 448, 20,
                  "chart series fed by C after ui_init (W14 is an empty shell in EEZ)",
                  color="0x8A94A6", identifier="lbl_note"),
            led_color,
            led_bright,
        ],
    )
    page = {
        "objID": oid(), "components": [screen], "connectionLines": [],
        "localVariables": [], "componentGroups": [], "userProperties": [],
        "name": "Main", "left": 0, "top": 0,
        "width": SCREEN_W, "height": SCREEN_H,
        "isUsedAsUserWidget": False, "createAtStart": True,
        "deleteOnScreenUnload": False,
    }
    return {
        "themesVersion": 1, "objID": oid(),
        "settings": {
            "objID": oid(),
            "general": {
                "objID": oid(), "projectVersion": "v3", "projectType": "lvgl",
                "lvglVersion": "9.4.0", "extensions": [], "imports": [],
                "flowSupport": True, "displayWidth": SCREEN_W,
                "displayHeight": SCREEN_H, "circularDisplay": False,
                "displayBorderRadius": 0, "darkTheme": True, "colorBpp": "16",
                "bitmapColorFormat": "BGR", "resourceFiles": [],
                "hiddenWidgetLines": "dimmed", "dimmedLinesOpacity": "20",
                "embedBitmaps": True, "embedFonts": True, "cacheFonts": True,
            },
            "build": {
                "objID": oid(),
                "configurations": [{"objID": oid(), "name": "Default"}],
                "destinationFolder": "src\\ui",
                "separateFolderForImagesAndFonts": True,
                "imageExportMode": "source", "fontExportMode": "source",
                "fileSystemPath": "", "lvglInclude": "lvgl.h",
                "screensLifetimeSupport": False, "useDockerDesktop": True,
                "generateSourceCodeForEezFramework": True,
                "compressFlowDefinition": False, "executionQueueSize": 1000,
                "expressionEvaluatorStackSize": 20,
                "files": [{"objID": oid(), "fileName": name, "template": tmpl}
                          for name, tmpl in BUILD_TEMPLATES.items()],
            },
        },
        "variables": {
            "objID": oid(),
            "globalVariables": [
                {"objID": oid(), "name": "g_color",
                 "type": "integer", "defaultValue": "65280",   # 0x00FF00
                 "persistent": False, "native": False},
                {"objID": oid(), "name": "g_bright",
                 "type": "integer", "defaultValue": "180",
                 "persistent": False, "native": False},
            ],
            "structures": [], "enums": [],
        },
        "actions": [], "userPages": [page], "userWidgets": [],
        "lvglStyles": {"objID": oid(), "styles": [], "defaultStyles": {}},
        "lvglGroups": {"objID": oid(), "groups": []},
        "fonts": [], "bitmaps": [], "colors": [],
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
