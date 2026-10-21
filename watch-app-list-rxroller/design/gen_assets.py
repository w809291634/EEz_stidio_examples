# -*- coding: utf-8 -*-
"""gen_assets.py —— 由 design/apps.py 一张表生成两样东西

  1) src/native/icons/img_<icon_id>.c   22 个占位图标（76x76 ARGB8888）
  2) src/native/app_rows.c/.h           native 侧读的常量表（id/中文名/图标指针）

图标形态与 EEZ 生成的 images/*.c 逐字段一致（ARGB8888 / stride=w*4 /
LV_IMAGE_HEADER_MAGIC），lv_img_set_src 直接吃。
尺寸 76 = Design Watch 参考口径里行的基准图标宽（其注释：峰值 76x1.094x1.078≈88px
仍要避开 100px 行距撞行），留 4px 透明边免得相邻行糊在一起。

用法：python design/gen_assets.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from apps import APPS  # noqa: E402

ICON_DIR = os.path.join(ROOT, "src", "native", "icons")
FONT_PATH = os.path.join(ROOT, "fonts", "simhei.ttf")

SIZE = 76
INSET = 4
CORNER = 20
PALETTE = [
    (61, 220, 151), (255, 204, 0), (255, 99, 99), (90, 200, 250),
    (52, 199, 89), (255, 55, 95), (48, 176, 199), (150, 160, 175),
]


def render(glyph, rgb):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((INSET, INSET, SIZE - 1 - INSET, SIZE - 1 - INSET),
                        radius=CORNER, fill=rgb + (255,))
    f = ImageFont.truetype(FONT_PATH, 30)
    box = d.textbbox((0, 0), glyph, font=f)
    d.text(((SIZE - (box[2] - box[0])) / 2 - box[0],
            (SIZE - (box[3] - box[1])) / 2 - box[1]),
           glyph, font=f, fill=(20, 24, 32, 255))
    return img


def emit_icon(name, img):
    px = img.tobytes()                      # RGBA -> 内存序 B,G,R,A（小端 ARGB8888）
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
    if not os.path.exists(FONT_PATH):
        sys.exit("缺字体源：%s" % FONT_PATH)
    os.makedirs(ICON_DIR, exist_ok=True)
    for i, (icon_id, name, _target) in enumerate(APPS):
        emit_icon("img_" + icon_id, render(name[0], PALETTE[i % len(PALETTE)]))
    emit_table()
    print("written: %d 个图标 -> icons/，外加 app_rows.{c,h}" % len(APPS))


if __name__ == "__main__":
    main()
