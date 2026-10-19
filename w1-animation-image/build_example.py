# -*- coding: utf-8 -*-
"""w1-animation-image —— EEZ 手册 W1. AnimationImage 控件示例（生成器）

本文件是示例的唯一设计源：w1-animation-image.eez-project 由它生成，请勿手改产物。

    python build_example.py      # 重新生成 .eez-project（含 8 帧位图）

演示点（手册出处：EEZ Studio 内置文档 help/en-US/components/widgets/AnimationImage.md，
即 EEZ-Studio-reference-guide 的 W1 节；官方 LVGL 文档 docs.lvgl.io/master/widgets/animimg.html）：
  1. AnimationImage = "多帧 Image"：images 列表按顺序逐帧播放，代替单张源图。
  2. 三个属性：Duration（整轮时长 ms）、Repeat infinite（无限循环开关）、
     Repeat count（关闭无限后的次数）。生成代码 = lv_animimg_create →
     lv_animimg_set_src(帧数组) → set_duration → set_repeat_count → lv_animimg_start。
  3. 帧图 = 工程位图（bitmaps 数组，内嵌 data:image/png;base64 data-URI，bpp 32 支持透明），
     本例 8 帧 96x96 旋转 spinner（转圈尾巴渐暗），全部由本脚本纯 stdlib 现算生成。
  4. widgetFlags 用官方默认（含 SNAPPABLE——P-0150 教训：任何页容器/大对象别乱裁 flags）。

屏幕基线：480x320 · LVGL 9.4 · EEZ Studio 0.29（projectVersion=v3）。
"""
import base64
import json
import math
import os
import struct
import uuid
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FILE = os.path.join(HERE, "w1-animation-image.eez-project")

SCREEN_W, SCREEN_H = 480, 320
FRAME = 96          # 帧边长
N_FRAMES = 8        # 帧数
DURATION_MS = 800   # 一整轮时长

# ---------------------------------------------------------------------------
# 纯 stdlib PNG（RGBA）编码
# ---------------------------------------------------------------------------
def png_rgba(width, height, pixels):
    """pixels: list of rows, each row list of (r,g,b,a)"""
    raw = b""
    for row in pixels:
        raw += b"\x00"  # filter: None
        for r, g, b, a in row:
            raw += struct.pack("4B", r, g, b, a)
    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8bit RGBA
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def make_spinner_frame(idx, n):
    """旋转 spinner：240° 渐暗尾巴 + 亮头，绕圈 n 帧。"""
    cx = cy = FRAME / 2.0
    r_in, r_out = FRAME * 0.30, FRAME * 0.46
    a0 = idx * 360.0 / n
    TAIL = 240.0
    px = []
    for y in range(FRAME):
        row = []
        for x in range(FRAME):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            if r_in <= r <= r_out:
                # 屏幕坐标 y 向下，取负使角度逆时针为正
                ang = math.degrees(math.atan2(-(dy), dx)) % 360.0
                d = (a0 - ang) % 360.0          # 距头部的角度差
                if d <= TAIL:
                    t = 1.0 - d / TAIL          # 头=1 尾=0
                    v = int(40 + 215 * t)
                    row.append((v, v, v, 255))
                    px.append(row)
                    continue
            row.append((0, 0, 0, 0))
        px.append(row)
    return png_rgba(FRAME, FRAME, px)


# ---------------------------------------------------------------------------
# EEZ 工程骨架（与 gesture/tabview 生成器同源）
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

# 官方默认 flags（asar 挖证 LVGLAnimationImageWidget.lvgl.defaultFlags；
# P-0150 教训：flags 是最终态白名单，别裁）
DEFAULT_FLAGS = {
    "LVGLScreenWidget": "CLICKABLE|CLICK_FOCUSABLE|SCROLLABLE|SCROLL_MOMENTUM|SCROLL_ELASTIC|SNAPPABLE|SCROLL_CHAIN_VER",
    "LVGLLabelWidget": "GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
    "LVGLAnimationImageWidget": "ADV_HITTEST|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
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


def label(x, y, w, h, text, color="0xFFFFFF", identifier=None):
    props = dict(ZERO_PAD, text_color=color)
    return widget(
        "LVGLLabelWidget", x, y, w, h,
        identifier=identifier,
        local={"MAIN": {"DEFAULT": props}},
        text=text, textType="literal", longMode="WRAP",
        recolor=False, useStaticText=True,
    )


def build_project():
    # ---- 帧位图：8 帧 spinner，data-URI 内嵌 ----
    frames = []
    for i in range(N_FRAMES):
        png = make_spinner_frame(i, N_FRAMES)
        b64 = base64.b64encode(png).decode("ascii")
        frames.append({
            "objID": oid(),
            "name": "anim_frame_%d" % i,
            "description": "spinner frame %d/%d" % (i + 1, N_FRAMES),
            "image": "data:image/png;base64," + b64,
            "bpp": 32,
            "alwaysBuild": False,
        })

    anim = widget(
        "LVGLAnimationImageWidget",
        (SCREEN_W - FRAME) // 2, 90, FRAME, FRAME,
        identifier="anim_spinner",
        children=[],
        images=[{"objID": oid(), "image": f["name"]} for f in frames],
        duration=DURATION_MS,
        repeatInfinite=True,
        repeat=1,
    )

    screen = widget(
        "LVGLScreenWidget", 0, 0, SCREEN_W, SCREEN_H,
        identifier="screen_main",
        local={"MAIN": {"DEFAULT": {
            "bg_color": "0x101828", "bg_opa": 255, "radius": 0,
            "border_width": 0}}},
        children=[
            label(40, 30, 400, 36, "W1. AnimationImage",
                  color="0xFFFFFF", identifier="lbl_title"),
            label(40, 220, 400, 36,
                  "%d frames x %d ms / loop, repeat infinite"
                  % (N_FRAMES, DURATION_MS),
                  color="0xCCCCCC", identifier="lbl_info"),
            anim,
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
        "bitmaps": frames,
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
