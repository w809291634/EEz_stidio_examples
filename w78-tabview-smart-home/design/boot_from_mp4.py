# -*- coding: utf-8 -*-
"""MP4 → LVGL 开机动画帧序列。

用法：
  python design/boot_from_mp4.py [mp4] [--fps 12] [--max-frames 48] [--width 800]
  python design/boot_from_mp4.py --demo        # 生成演示用 assets/boot.mp4 再转帧

产物：
  assets/boot/boot_000.jpg ...                 （按顺序编号）
  src/native/app/boot_frames.h                 （帧数 / 帧间隔 / 路径模板）

机器上没有 ffmpeg 也能跑：用 cv2 解码；演示 MP4 也用 cv2 生成。
"""
import argparse
import glob
import io
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "assets", "boot")
OUT_MP4 = os.path.join(ROOT, "assets", "boot.mp4")
HEADER = os.path.join(ROOT, "src", "native", "app", "boot_frames.h")
W, H = 800, 480


def _font(size, bold=False):
    for p in ((r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
              r"C:\Windows\Fonts\msyh.ttc"):
        if os.path.isfile(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make_demo(path, fps=12, seconds=3.0):
    """生成一段深色品牌开机动画 MP4（800x480）。"""
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    n = int(fps * seconds)
    f_big, f_small = _font(52, True), _font(18)
    for i in range(n):
        t = i / float(max(n - 1, 1))
        a = min(1.0, t / 0.25) * (1.0 if t < 0.85 else max(0.0, (1.0 - t) / 0.15))
        im = Image.new("RGB", (W, H), (5, 8, 15))
        d = ImageDraw.Draw(im)
        cx, cy = W // 2, 190
        d.ellipse([cx - 46, cy - 46, cx + 46, cy + 46],
                  outline=(int(242 * a), int(180 * a), int(92 * a)), width=3)
        d.text((cx, cy - 2), "H", font=_font(46, True),
               fill=(int(244 * a), int(247 * a), int(251 * a)), anchor="mm")
        d.text((cx, 300), "HAVEN HOME", font=f_big,
               fill=(int(244 * a), int(247 * a), int(251 * a)), anchor="mm")
        d.text((cx, 338), "SMART HOME · BOOTING", font=f_small,
               fill=(int(90 * a), int(106 * a), int(128 * a)), anchor="mm")
        bw, bh, bx, by = 360, 4, (W - 360) // 2, 400
        d.rectangle([bx, by, bx + bw, by + bh], fill=(20, 27, 38))
        d.rectangle([bx, by, bx + int(bw * min(1.0, t / 0.9)), by + bh],
                    fill=(int(242 * a), int(180 * a), int(92 * a)))
        vw.write(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))
    vw.release()
    return n


def extract(mp4, fps_target, max_frames, width):
    os.makedirs(OUT_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(OUT_DIR, "boot_*.jpg")):
        os.remove(f)
    cap = cv2.VideoCapture(mp4)
    if not cap.isOpened():
        raise SystemExit("打不开 MP4：%s" % mp4)
    fps_src = cap.get(cv2.CAP_PROP_FPS) or 24.0
    step = max(1, int(round(fps_src / float(fps_target))))
    files, idx, src_i = [], 0, 0
    while len(files) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if src_i % step == 0:
            h, w = frame.shape[:2]
            scale = min(width / float(w), H / float(h))
            nw, nh = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
            canvas = np.zeros((H, W, 3), np.uint8)
            canvas[:] = (15, 8, 5)               # 与 BG 0x05080F 一致（BGR）
            x, y = (W - nw) // 2, (H - nh) // 2
            canvas[y:y + nh, x:x + nw] = frame
            name = "boot_%03d.jpg" % idx
            cv2.imwrite(os.path.join(OUT_DIR, name), canvas,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            files.append(name)
            idx += 1
        src_i += 1
    cap.release()
    return files, fps_target


def write_header(count, fps):
    frame_ms = int(round(1000.0 / float(fps)))
    os.makedirs(os.path.dirname(HEADER), exist_ok=True)
    txt = (
        "/* 由 design/boot_from_mp4.py 生成，勿手改。 */\n"
        "#ifndef BOOT_FRAMES_H\n#define BOOT_FRAMES_H\n\n"
        "#define BOOT_FRAME_COUNT %d\n"
        "#define BOOT_FRAME_MS    %d\n"
        "#define BOOT_FRAME_FMT   \"A:/assets/boot/boot_%%03d.jpg\"\n\n"
        "#endif\n" % (count, frame_ms))
    io.open(HEADER, "w", encoding="utf-8", newline="\n").write(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4", nargs="?", default=OUT_MP4)
    ap.add_argument("--demo", action="store_true", help="先生成演示 MP4")
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--max-frames", type=int, default=48)
    ap.add_argument("--width", type=int, default=W)
    a = ap.parse_args()

    if a.demo or not os.path.isfile(a.mp4):
        os.makedirs(os.path.dirname(OUT_MP4), exist_ok=True)
        n = make_demo(OUT_MP4, fps=a.fps)
        print("[BOOT] 生成演示 MP4：%s（%d 帧 @%dfps）" % (OUT_MP4, n, a.fps))
        a.mp4 = OUT_MP4
    files, fps = extract(a.mp4, a.fps, a.max_frames, a.width)
    if not files:
        raise SystemExit("没有解出任何帧：%s" % a.mp4)
    write_header(len(files), fps)
    total = sum(os.path.getsize(os.path.join(OUT_DIR, f)) for f in files)
    print("[BOOT] %d 帧 @%dfps（%d ms/帧）｜ %.1f KB ｜ %s"
          % (len(files), fps, int(round(1000.0 / fps)), total / 1024.0, OUT_DIR))
    print("[BOOT] 头文件：%s" % HEADER)


if __name__ == "__main__":
    main()
