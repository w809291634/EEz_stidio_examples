#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_images.py —— 补烘 AnimationImage 帧图 .c（EEZ CLI 构建不产图片 .c，与字体
P-0140 同类；GUI Build 才产出。本脚本复算与 build_example.py 完全一致的 spinner 帧，
直接生成 EEZ v9 格式 lv_image_dsc_t 定义，落在 src/ui/images/ 下。

用法：python design/gen_images.py   （在每次 EEZ CLI 构建之后运行）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import build_example as be  # 复用同一套帧绘制与常量

OUT_DIR = os.path.join(ROOT, "src", "ui", "images")

HEADER = """#ifdef __has_include
    #if __has_include("lvgl.h")
        #ifndef LV_LVGL_H_INCLUDE_SIMPLE
            #define LV_LVGL_H_INCLUDE_SIMPLE
        #endif
    #endif
#endif

#if defined(LV_LVGL_H_INCLUDE_SIMPLE)
#include "lvgl.h"
#elif defined(LV_LVGL_H_INCLUDE_SYSTEM)
#include <lvgl.h>
#elif defined(LV_BUILD_TEST)
#include "../lvgl.h"
#else
#include "lvgl/lvgl.h"
#endif

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_ANIM_FRAME_%(idx)d
#define LV_ATTRIBUTE_IMG_ANIM_FRAME_%(idx)d
#endif

static const
LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_ANIM_FRAME_%(idx)d
uint8_t img_anim_frame_%(idx)d_map[] = {
%(rows)s
};

const lv_image_dsc_t img_anim_frame_%(idx)d = {
  .header = {
    .magic = LV_IMAGE_HEADER_MAGIC,
    .cf = LV_COLOR_FORMAT_ARGB8888,
    .flags = 0,
    .w = %(w)d,
    .h = %(h)d,
    .stride = %(stride)d,
    .reserved_2 = 0,
  },
  .data_size = sizeof(img_anim_frame_%(idx)d_map),
  .data = img_anim_frame_%(idx)d_map,
  .reserved = NULL,
};
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for i in range(be.N_FRAMES):
        # 复算帧像素（与 build_example.make_spinner_frame 同源，PNG 内即 RGBA）
        import zlib, struct
        png = be.make_spinner_frame(i, be.N_FRAMES)
        # 直接从 PNG 解码回像素，保证与位图数据 100% 一致
        pos = 8
        idat = b""
        while pos < len(png):
            ln = struct.unpack(">I", png[pos:pos+4])[0]
            tag = png[pos+4:pos+8]
            if tag == b"IDAT":
                idat += png[pos+8:pos+8+ln]
            pos += 12 + ln
        raw = zlib.decompress(idat)
        stride_in = be.FRAME * 4 + 1
        rows = []
        for y in range(be.FRAME):
            line = raw[y*stride_in + 1:(y+1)*stride_in]
            vals = []
            for x in range(be.FRAME):
                r, g, b, a = line[x*4:x*4+4]
                # LVGL ARGB8888 内存字节序：B,G,R,A
                vals.append("0x%02x,0x%02x,0x%02x,0x%02x" % (b, g, r, a))
            rows.append("    " + ",".join(vals) + ",")
        text = HEADER % {
            "idx": i,
            "rows": "\n".join(rows),
            "w": be.FRAME, "h": be.FRAME,
            "stride": be.FRAME * 4,
        }
        out = os.path.join(OUT_DIR, "img_anim_frame_%d.c" % i)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print("written: %s" % out)
    print("done: %d frames -> %s" % (be.N_FRAMES, OUT_DIR))


if __name__ == "__main__":
    main()
