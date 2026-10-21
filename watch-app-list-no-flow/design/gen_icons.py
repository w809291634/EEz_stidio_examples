# -*- coding: utf-8 -*-
"""gen_icons.py —— 自绘占位应用图标，直接产出 LVGL 9 的 lv_image_dsc_t .c

为什么不走 EEZ 的 bitmaps[] 链：这些图标只被 native 移植件用（EEZ 屏上没有
引用它们），走 EEZ 反而要多一套 data-URI + CLI 不烘图（P-0151）的补烘步骤。
产物形态与 EEZ 生成的 images/*.c 逐字段一致（ARGB8888 / stride=w*4 /
LV_IMAGE_HEADER_MAGIC），可直接被 lv_image_set_src 吃。

尺寸 80x80 = 移植件里的 ICON_OUTER_DIAMETER（ICON_OUTER_RADIUS = 368/9 = 40），
按这个尺寸出图可让 zoom 落在 LV_SCALE_NONE(256) 上，不做无谓重采样。

用法：python design/gen_icons.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "src", "native", "icons")
FONT_PATH = os.path.join(ROOT, "fonts", "simhei.ttf")

SIZE = 80
# 图标画在 80x80 画布中央、留 10px 透明边：蜂窝间距就是 80px，而穹顶变换还会
# 把外圈往屏心**压缩**（radial_factor<1），满幅圆一定糊成一团。真机美术件同样带
# 透明边，这里把它显式画出来。
INSET = 10
CORNER = 22

APPS = [
    ("clock",     (61, 220, 151)), ("activity",  (255, 204,  0)),
    ("alarm",     (255,  99,  99)), ("calendar",  (255, 255, 255)),
    ("camera",    (120, 130, 145)), ("health",    (255,  59,  92)),
    ("mail",      ( 90, 200, 250)), ("maps",      ( 52, 199,  89)),
    ("music",     (255,  45,  85)), ("phone",     ( 52, 199,  89)),
    ("photos",    (255, 214,  10)), ("remote",    (150, 160, 175)),
    ("settings",  (140, 145, 155)), ("stocks",    ( 48, 176, 199)),
    ("stopwatch", (255, 149,   0)), ("workout",   (255,  55,  95)),
]


def render(app_id, rgb):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((INSET, INSET, SIZE - 1 - INSET, SIZE - 1 - INSET),
                        radius=CORNER, fill=rgb + (255,))
    letter = app_id[0].upper()
    f = ImageFont.truetype(FONT_PATH, 34)
    box = d.textbbox((0, 0), letter, font=f)
    d.text(((SIZE - (box[2] - box[0])) / 2 - box[0],
            (SIZE - (box[3] - box[1])) / 2 - box[1]),
           letter, font=f, fill=(20, 24, 32, 255))
    return img


def render(app_id, rgb):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, SIZE - 3, SIZE - 3), fill=rgb + (255,))
    letter = app_id[0].upper()
    f = ImageFont.truetype(FONT_PATH, 44)
    box = d.textbbox((0, 0), letter, font=f)
    d.text(((SIZE - (box[2] - box[0])) / 2 - box[0],
            (SIZE - (box[3] - box[1])) / 2 - box[1]),
           letter, font=f, fill=(20, 24, 32, 255))
    return img


def emit_c(app_id, img):
    px = img.tobytes()                       # RGBA -> 内存序 B,G,R,A（小端 ARGB8888）
    name = "img_app_%s" % app_id
    rows = []
    for i in range(0, len(px), 16):
        rows.append(",".join("0x%02x" % b for b in px[i:i + 16]))
    body = (
        "/* 自动生成：design/gen_icons.py —— 请勿手改，重跑脚本即覆盖 */\n"
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
        % (name, len(px), ",\n  ".join(rows), name, SIZE, SIZE, SIZE * 4,
           name, name)
    )
    with open(os.path.join(OUT_DIR, name + ".c"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(body)
    return len(body)


def main():
    if not os.path.exists(FONT_PATH):
        raise SystemExit("缺字体源：%s（字母要用它画）" % FONT_PATH)
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for app_id, rgb in APPS:
        total += emit_c(app_id, render(app_id, rgb))
    print("written: %d 个图标 -> %s（%d B 源码）"
          % (len(APPS), OUT_DIR, total))


if __name__ == "__main__":
    main()
