# -*- coding: utf-8 -*-
"""gen_assets.py —— 由 design/apps.py 一张表生成两样东西

  1) src/native/icons/img_<icon_id>.c   22 个圆形矢量图标（ICON_PX 见方 ARGB8888）
  2) src/native/app_rows.c/.h           native 侧读的常量表（id/中文名/图标指针）

图标形态与 EEZ 生成的 images/*.c 逐字段一致（ARGB8888 / stride=w*4 /
LV_IMAGE_HEADER_MAGIC），lv_img_set_src 直接吃。
尺寸唯一出处是 watch_list_config.h 的 ICON_PX；**画法在 icons_art.py**，
本文件只管接线与落盘 —— 换图标只动 icons_art.py，别在这里画第二套。
内容方框与旧版（圆角方那版）逐像素一致，留 4px 透明边避免相邻行糊在一起。

用法：python design/gen_assets.py
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from apps import APPS  # noqa: E402
from icons_art import ART, render_icon  # noqa: E402
from wconfig import wcfg  # noqa: E402

ICON_DIR = os.path.join(ROOT, "src", "native", "icons")

# ★ 尺寸唯一出处是 src/native/watch_list_config.h，这里只按它等比派生
SIZE = wcfg("ICON_PX")
INSET = max(4, SIZE // 16)     # 与旧版同一个透明边；图标内容仍占 (INSET, SIZE-1-INSET)


def render(icon_id):
    """按 icon_id 画一个圆形矢量图标。画法全在 icons_art.py，这里只管接线。"""
    if icon_id not in ART:
        sys.exit("icons_art.ART 里没有 %s ⇒ 新加的应用行要先补图标" % icon_id)
    glyph, bg, fg, _src = ART[icon_id]
    return render_icon(SIZE, glyph, bg, fg, inset=INSET)


def emit_icon(name, img):
    # ★ LVGL 的 ARGB8888 是小端 uint32 0xAARRGGBB ⇒ 内存字节序 B,G,R,A；
    #   而 PIL 的 tobytes() 给的是 R,G,B,A。原来那行注释写着"已转成 B,G,R,A"，
    #   其实根本没转 —— 实测设计色 #C2ED3C 会发成 #3CEDC2（红蓝互换）。
    #   这是**字节序**修正，与几何无关，不可能影响拖动观感。
    r, g, b, a = img.split()
    px = Image.merge("RGBA", (b, g, r, a)).tobytes()      # 内存序 B,G,R,A
    rows = [",".join("0x%02x" % b for b in px[i:i + 16])
            for i in range(0, len(px), 16)]
    body = (
        "/* 自动生成：design/gen_assets.py —— 勿手改，重跑即覆盖 */\n"
        '#include "lvgl.h"\n\n'
        "static const uint8_t %s_map[%d] = {\n  %s\n};\n\n"
        "const lv_image_dsc_t %s = {\n"
        "  .header = {\n"
        "    .magic = LV_IMAGE_HEADER_MAGIC,\n"
        "    .cf = LV_COLOR_FORMAT_ARGB8888,\n"
        "    .flags = 0,\n"
        "    .w = %d,\n    .h = %d,\n    .stride = %d,\n    .reserved_2 = 0,\n"
        "  },\n"
        "  .data_size = sizeof(%s_map),\n  .data = %s_map,\n  .reserved = NULL,\n};\n"
        % (name, len(px), ",\n  ".join(rows), name, SIZE, SIZE, SIZE * 4, name, name)
    )
    with open(os.path.join(ICON_DIR, name + ".c"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(body)


def emit_table():
    h = (
        "/* 自动生成：design/gen_assets.py（事实源 design/apps.py）——勿手改 */\n"
        "#ifndef WATCH_APP_ROWS_H\n#define WATCH_APP_ROWS_H\n\n"
        "typedef struct {\n"
        "    const char *id;      /* 目标页 id（ASCII，不上屏） */\n"
        "    const char *name;    /* 中文名，上屏 ⇒ 必须在字体子集内 */\n"
        "    const void *icon;    /* lv_image_dsc_t* */\n"
        "} watch_app_row_t;\n\n"
        "extern const watch_app_row_t WATCH_APP_ROWS[];\n"
        "extern const int WATCH_APP_ROWS_COUNT;\n\n"
        "#endif\n"
    )
    c = ['/* 自动生成：design/gen_assets.py（事实源 design/apps.py）——勿手改 */',
         '#include "app_rows.h"',
         '#include "lvgl.h"',
         '']
    for icon_id, _name, _target in APPS:
        c.append("LV_IMG_DECLARE(img_%s);" % icon_id)
    c.append("")
    c.append("const watch_app_row_t WATCH_APP_ROWS[] = {")
    for icon_id, name, target in APPS:
        c.append('    {"%s", "%s", &img_%s},' % (target, name, icon_id))
    c.append("};")
    c.append("const int WATCH_APP_ROWS_COUNT = (int)(sizeof(WATCH_APP_ROWS) / "
             "sizeof(WATCH_APP_ROWS[0]));")
    c.append("")
    for fn, body in (("app_rows.h", h), ("app_rows.c", "\n".join(c))):
        with open(os.path.join(ROOT, "src", "native", fn), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(body)


def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    for icon_id, _name, _target in APPS:
        emit_icon("img_" + icon_id, render(icon_id))
    emit_table()
    print("written: %d 个圆形矢量图标 -> icons/，外加 app_rows.{c,h}" % len(APPS))


if __name__ == "__main__":
    main()
