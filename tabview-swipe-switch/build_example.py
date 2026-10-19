# -*- coding: utf-8 -*-
"""tabview-swipe-switch —— Tabview 隐藏 tab 栏 + 原生滑动切页示例（生成器）

本文件是示例的唯一设计源：tabview-swipe-switch.eez-project 由它生成，请勿手改产物。

    python build_example.py      # 重新生成 tabview-swipe-switch.eez-project

演示点：
  1. 单 screen + lv_tabview 两页，**tabviewSize=0 隐藏 tab 栏**（lv_tabview_set_tab_bar_size(tv,0)
     直接把 bar 高度置 0，内核 lv_tabview.c:224 实证）——页间切换只靠滑动。
  2. 跟手滑动是 tabview **原生行为**：内容区自带 SCROLL_SNAP_CENTER 横向吸附
     （lv_tabview.c:190）+ LV_EVENT_SCROLL_END 自动吸附最近页（lv_tabview.c:344-373）。
     不画任何 Switch/Action 流组件，零连线 —— 与 gesture-page-switch（GESTURE 离散切屏）
     互补：要"跟手拖一半弹回"用本例，要"整页离散翻页"用手势版。
  3. Tab 控件直接作 Tabview 子控件（配置 1，watch.eez-project 同款实测形态）；
     Tab 自身 bg 着色区分页，tabName 用 ASCII（P-0022：tabName 不进字形收集，中文会豆腐——
     本例 tab 栏隐藏所以 tabName 不可见，但仍取 ASCII 稳妥）。
  4. widgetFlags 与 widgetFlagsUser：tab 栏隐藏后页间滑动只由 tabview 内容区承担，
     Tab 控件去掉内部滚动族 flag（SCROLLABLE/SCROLL_ELASTIC/SCROLL_MOMENTUM/SNAPPABLE），
     防止页内容拖拽与页切换抢手势（watch 工程同款裁剪）。

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（projectVersion=v3）。
验证：CLI 构建 0 错 0 警 + PC_SIM 仿真器编译链接通过（滑动行为在仿真器窗口拖拽验收）。
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "tabview-swipe-switch.eez-project")

SCREEN_W, SCREEN_H = 480, 320

# ---------------------------------------------------------------------------
# 构建模板：与 EEZ Studio 0.29 新建 LVGL 工程的 settings.build.files 逐字一致
# （与 gesture-page-switch 生成器同源拷贝）。
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

# 各控件类型的默认 widgetFlags（LVGL 9 口径，取自 EEZ Studio 0.29 控件定义）
DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE",
    # EEZ Tabview 控件 defaultFlags（asar 挖证 101192667）
    "LVGLTabviewWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
    # Tab 控件：去掉内部滚动族 flag，防页内容拖拽与页切换抢手势（watch 同款裁剪）
    "LVGLTabWidget": "CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
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
        "left": x,
        "top": y,
        "width": w,
        "height": h,
        "customInputs": [],
        "customOutputs": [],
        "style": {"objID": oid(), "useStyle": "default",
                  "conditionalStyles": [], "childStyles": []},
        "timeline": [],
        "eventHandlers": [],
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
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


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None):
    props = dict(ZERO_PAD, text_color=color)
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": props}},
        text=text,
        textType="literal",
        longMode="WRAP",
        recolor=False,
        useStaticText=True,
    )


def tab_page(name, bg_color, title, hint, hint_color="0xCCCCCC"):
    """一个 Tab 页：整页着色 + 居中标题 + 底部滑动提示。

    Tab 几何与 watch.eez-project 同款：(0,0,SCREEN_W,SCREEN_H)，EEZ 会自行
    把它放进 tabview 内容区并布局成整页。
    """
    return widget(
        "LVGLTabWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="tab_%s" % name,
        local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_color=bg_color,
                                        bg_opa=255, radius=0)}},
        children=[
            label(40, 120, 400, 48, title, color="0xFFFFFF",
                  identifier="lbl_title_%s" % name),
            label(40, 200, 400, 40, hint, color=hint_color,
                  identifier="lbl_hint_%s" % name),
        ],
        tabName=name,
        tabNameType="literal",
    )


def build_project():
    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_main",
        local={"MAIN": {"DEFAULT": {
            "bg_color": "0x101828", "bg_opa": 255, "radius": 0,
            "border_width": 0}}},
        children=[
            widget(
                "LVGLTabviewWidget", 0, 0, SCREEN_W, SCREEN_H,
                identifier="tv_pages",
                # ★ tabviewSize=0 -> lv_tabview_set_tab_bar_size(tv,0) 隐藏 tab 栏
                local={"MAIN": {"DEFAULT": dict(ZERO_PAD, bg_opa=0)}},
                children=[
                    tab_page("p1", "0x103A6B", "PAGE 1",
                             "drag / swipe horizontally -> PAGE 2"),
                    tab_page("p2", "0x14532D", "PAGE 2",
                             "drag / swipe horizontally -> PAGE 1"),
                ],
                tabviewPosition="TOP",
                tabviewSize=0,
                selectedTab=0,
                selectedTabType="literal",
            ),
        ],
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
        "variables": {"objID": oid(), "globalVariables": [],
                      "structures": [], "enums": []},
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
