# -*- coding: utf-8 -*-
"""④-B1 EEZ 画布逐屏截图（§2.2 四层两站·第二站）。

链路（kit NO_FLOW §3.1 实测纪律）：
  起 EEZ Studio --remote-debugging-port=9222 打开本工程 → 等加载+会话内字体提取
  → 逐页点 Pages 树切屏 → cdp.js canvas-shot 取画布原始像素 → 与 designer/*.png 拼并排图。
画布=真实 LVGL wasm 渲染（P-0164 勘误），静态样式在此层主核；跳转不核（归⑤C）。

产物：build/b1/eez_<page>.png、build/b1/_b1_compare.png
跑法：python design/eez_b1_shots.py            （全程自动，结束后自动关 EEZ）
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import design_source as ds

from PIL import Image, ImageDraw, ImageFont

EXE = r"C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe"
CDP = r"C:\Users\yjt54\sim_watch\cdp.js"
PROJ = os.path.join(ROOT, "watch.eez-project")
OUT = os.path.join(ROOT, "tmp", "b1")   # 核对过程件=工程 tmp/（gitignore）；定稿对照图另拷交付位
PORT = "9223"          # 避开 9222（watch 旧会话留档端口），防串台


def sh(args, timeout=60):
    e = dict(os.environ)
    e["CDP_PORT"] = PORT          # 翻案：不传则 cdp.js 回退 9222 连错实例，全页静默失败
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, env=e)


def targets():
    try:
        with urllib.request.urlopen(
                "http://127.0.0.1:%s/json/list" % PORT, timeout=3) as r:
            return json.load(r)
    except Exception:
        return []


def cdp_eval(expr):
    return sh(["node", CDP, "eval", expr], timeout=90)


def main():
    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ)
    env.pop("ELECTRON_RUN_AS_NODE", None)
    env["CDP_PORT"] = PORT
    p = subprocess.Popen([EXE, "--remote-debugging-port=" + PORT, PROJ,
                          "--no-sandbox", "--disable-gpu",
                          "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
                         env=env,
                         creationflags=0x08000000 if os.name == "nt" else 0)
    try:
        print("[B1] 等待 EEZ 加载…")
        for _ in range(60):
            time.sleep(3)
            if any(t.get("type") == "page" for t in targets()):
                break
        else:
            sys.exit("[B1] 9223 无 page target，EEZ 未起来")
        # P-0125：中文依赖会话内字体提取，形态正确≈2 分钟内自愈；先等再核
        print("[B1] 等字体提取…")
        time.sleep(90)

        pages = [pg["name"] for pg in ds.PAGES]
        pages = ["tab_main"] + [n for n in pages if n not in ("watchface", "applist")]
        for name in pages:
            js = ("(()=>{const els=[...document.querySelectorAll('*')]"
                  ".filter(e=>e.children.length===0&&e.textContent.trim()==='%s');"
                  "if(!els.length)return 'NOITEM';const t=els[els.length-1];"
                  "['mousedown','mouseup','click'].forEach(k=>t.dispatchEvent("
                  "new MouseEvent(k,{bubbles:true,cancelable:true,view:window})));"
                  "return 'OK';})()" % name)
            r = cdp_eval(js)
            out = (r.stdout or "").strip()
            if "OK" not in out:
                print("[B1] %s 树项点击失败：%s（回退：手工核对该页）" % (name, out[-120:]))
                continue
            time.sleep(2.5)
            shot = os.path.join(OUT, "eez_%s.png" % name)
            sh(["node", CDP, "canvas-shot", shot], timeout=90)
            print("[B1] %s -> %s %s" % (name, os.path.basename(shot),
                                        "OK" if os.path.exists(shot) else "FAIL"))
    finally:
        sh(["taskkill", "/F", "/T", "/PID", str(p.pid)], timeout=30)
        time.sleep(2)

    # 拼并排对照图（EEZ 画布 vs designer/）
    f = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 16)
    names = [n[:-4][4:] for n in os.listdir(OUT) if n.startswith("eez_") and n.endswith(".png")]
    cell = 240
    cols = 3
    rows = len(names)
    sheet = Image.new("RGB", (cols * (cell + 8) + 8, rows * (cell + 30) + 8), (24, 24, 30))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(sorted(names)):
        r, c = divmod(i, cols)
        x = 8 + c * (cell + 8)
        y = 8 + i * (cell + 30)
        d.text((x, y), name, font=f, fill=(220, 220, 235))
        try:
            a = Image.open(os.path.join(OUT, "eez_%s.png" % name)).convert("RGB")
            sheet.paste(a.resize((cell, cell)), (x, y + 20))
            dname = {"tab_main": "applist"}.get(name, name)
            b = Image.open(os.path.join(ROOT, "designer", dname + ".png")).convert("RGB")
            sheet.paste(b.resize((cell, cell)), (x + cell + 8, y + 20))
        except Exception as e:
            d.text((x, y + 40), "ERR %s" % e, font=f, fill=(255, 90, 90))
    d.text((8, 0), "左=EEZ 画布  右=designer/ 设计图（tab_main 右图用 applist 页对照）", font=f,
           fill=(255, 255, 255))
    sheet.save(os.path.join(OUT, "_b1_compare.png"))
    print("[B1] 对照拼图：%s（%d 页）" % (os.path.join(OUT, "_b1_compare.png"), len(names)))


if __name__ == "__main__":
    main()
