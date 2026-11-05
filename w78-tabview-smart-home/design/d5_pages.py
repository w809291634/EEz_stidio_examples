# -*- coding: utf-8 -*-
"""D5 逐页设计比对：每页出「设计 vs EEZ 画布」并排图，并打印相似度百分比。

用法：
  python design/d5_pages.py              # 只跑主控
  python design/d5_pages.py --all        # 23 页逐页（一次启动 EEZ，逐页点树节点）
  python design/d5_pages.py --page 客厅   # 指定页

产物：
  designer_annotated/d5_相似度.txt           # 逐页相似度百分比 + 汇总（门禁读这里）
  designer_annotated/d5/<页名>.png          # 并排图（主控始终留，其余超阈值才留）

要点（都踩过）：EEZ 画布只有点开页节点才挂载；页名是 ASCII id（PAGE_IDS），点树节点要用 id。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pages as pg                       # noqa: E402
from eez_gen import PAGE_IDS             # noqa: E402

KIT = r"C:\Users\yjt54\Desktop\local_knowledge_base\embedded\EEZ Studio_ui_debug_kit"
EEZ_EXE = r"C:\Users\yjt54\AppData\Local\Programs\eezstudio\EEZ Studio.exe"
PROJ = os.path.join(ROOT, "w78-smart-home.eez-project")
OUT_DIR = os.path.join(ROOT, "designer_annotated")
SHOT_DIR = os.path.join(OUT_DIR, "d5")
TMP = os.path.join(ROOT, "tmp")
W, H = 800, 480
COEF_FILE = os.path.join(OUT_DIR, "d5_相似度.txt")
SAVE_ABOVE = 5.0
SUSPECT = 8.0

CLICK_JS = r"""
const target = process.argv[2];
const rootPage = process.argv[3];
const allIds = (process.argv[4] || '').split(',').filter(Boolean);
const idsJson = JSON.stringify(allIds);
const list = await (await fetch('http://127.0.0.1:9222/json/list')).json();
const t = list.find(p => p.type === 'page' && /EEZ Studio/.test(p.title || ''));
const ws = new WebSocket(t.webSocketDebuggerUrl);
let i = 0; const pending = {};
const send = (m, p) => new Promise(r => { const id = ++i; pending[id] = r; ws.send(JSON.stringify({ id, method: m, params: p || {} })); });
ws.onmessage = e => { const d = JSON.parse(e.data); if (d.id && pending[d.id]) { pending[d.id](d); delete pending[d.id]; } };
await new Promise(r => { ws.onopen = r; });
await send('Runtime.enable');

// 目标节点 + 树视口 + 命中自证：只看 window 高度会把被树容器裁掉的节点当可见（实测点到别的页）
const find = `(()=>{
  const hits=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 && e.textContent.trim()===` + JSON.stringify(target) + `);
  if(!hits.length) return 'MISS_HITS';
  // 编辑器里有多个 .EezStudio_Tree（Pages / Widgets Structure / Variables）。
  // Widgets Structure 里也可能出现与页名同名的 label（如「客厅」），点它会开错画布。
  // 只认同时包含 >=3 个已知页 ID 的那棵树（Pages 树）。
  const trees=[...document.querySelectorAll('.EezStudio_Tree')];
  let tree=null, bestScore=0;
  for (const tr of trees){
    const texts=[...tr.querySelectorAll('*')].filter(x=>x.children.length===0).map(x=>x.textContent.trim());
    const sc=__IDS__.filter(id=>texts.includes(id)).length;
    if(sc>bestScore){bestScore=sc;tree=tr;}
  }
  if(!tree || bestScore<3) return 'MISS_TREE:'+bestScore;
  const e=hits.find(x=>tree.contains(x));
  if(!e) return 'MISS_LEAF';
  const row=e.closest('.tree-row') || e;
  // 树是虚拟列表：先把目标行滚到视口中间，避免行贴上下边缘时命中到容器/表头
  row.scrollIntoView({block:'center', inline:'nearest'});
  const b=row.getBoundingClientRect();
  const tr=row.closest('.EezStudio_Tree');
  const tb=tr?tr.getBoundingClientRect():{x:0,y:0,width:innerWidth,height:innerHeight};
  // 只点「行 ∩ 树视口」的交集：行被树容器裁一半时，行中心会落到分隔条上（实测 BLOCKED）
  const y0=Math.max(b.y, tb.y + 2), y1=Math.min(b.y + b.height, tb.y + tb.height - 2);
  const cx=Math.round(tb.x + Math.min(24, tb.width/4));
  const cy=Math.round((y0 + y1) / 2);
  const hit=document.elementFromPoint(cx, cy);
  const self=hit && hit.closest('.tree-row') && hit.closest('.tree-row')===row;
  return JSON.stringify([cx, cy, Math.round(tb.x), Math.round(tb.y), Math.round(tb.width), Math.round(tb.height), self?1:0, Math.round(y1-y0)]);
})()`;
const findExpr = find.replace("__IDS__", idsJson);

async function pos() {
  const r = await send('Runtime.evaluate', { expression: findExpr, returnByValue: true });
  const v = r.result.result.value;
  if (typeof v === 'string' && (v.startsWith('MISS') || v === 'BLOCKED')) {
    console.log(v); process.exit(0);
  }
  return v === 'none' ? null : JSON.parse(v);
}

let p = await pos();
if (!p) { console.log('MISS'); process.exit(0); }
// 虚拟列表：把它滚进树容器视口（max 40 步）
for (let k = 0; k < 40; k++) {
  if (p[7] >= 8 && p[1] > p[3] + 2 && p[1] < p[3] + p[5] - 2) break;
  const dy = p[1] <= p[3] + p[5] / 2 ? -120 : 120;
  await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: p[2] + Math.floor(p[4] / 2), y: p[3] + Math.floor(p[5] / 2), deltaX: 0, deltaY: dy });
  await new Promise(r => setTimeout(r, 180));
  p = await pos();
  if (!p) { console.log('MISS'); process.exit(0); }
}
if (!p[6]) { console.log('BLOCKED'); process.exit(0); }
await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p[0], y: p[1] });
// 双击才真正打开该页（单击只选中）
for (const n of [1, 2]) {
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p[0], y: p[1], button: 'left', clickCount: n, buttons: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p[0], y: p[1], button: 'left', clickCount: n, buttons: 0 });
  await new Promise(r => setTimeout(r, 200));
}
await new Promise(r => setTimeout(r, 800));
// 多标签页时：双击只保证「页签存在」，不一定激活；显式点一下该页签
const tab = await send('Runtime.evaluate', { expression: `(()=>{
  const b=[...document.querySelectorAll('.flexlayout__tab_button')].find(e=>e.textContent.trim()===` + JSON.stringify(target) + `);
  if(!b) return 'none';
  const r=b.getBoundingClientRect();
  return JSON.stringify([Math.round(r.x+r.width/2), Math.round(r.y+r.height/2),
    /selected/.test(b.className) ? 1 : 0]);
})()`, returnByValue: true });
const tv = tab.result.result.value;
if (tv && tv !== 'none') {
  const [tx, ty, sel] = JSON.parse(tv);
  if (!sel) {
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: tx, y: ty, button: 'left', clickCount: 1, buttons: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: tx, y: ty, button: 'left', clickCount: 1, buttons: 0 });
    await new Promise(r => setTimeout(r, 1000));
  }
}
// 只认「目标页签自身带 selected」；整页有多个 tabset，各自都有一个 selected（Pages/属性栏）
const chk = await send('Runtime.evaluate', { expression:
  `(()=>{const b=[...document.querySelectorAll('.flexlayout__tab_button')].find(e=>e.textContent.trim()===` + JSON.stringify(target) + `);return b && /selected/.test(b.className) ? 1 : 0})()`,
  returnByValue: true });
console.log(chk.result.result.value === 1 ? 'OK' : 'NOSEL');
process.exit(0);
"""


SETUP_JS = r"""
const rootPage = process.argv[2];
const list = await (await fetch('http://127.0.0.1:9222/json/list')).json();
const t = list.find(p => p.type === 'page' && /EEZ Studio/.test(p.title || ''));
const ws = new WebSocket(t.webSocketDebuggerUrl);
let i = 0; const pending = {};
const send = (m, p) => new Promise(r => { const id = ++i; pending[id] = r; ws.send(JSON.stringify({ id, method: m, params: p || {} })); });
ws.onmessage = e => { const d = JSON.parse(e.data); if (d.id && pending[d.id]) { pending[d.id](d); delete pending[d.id]; } };
await new Promise(r => { ws.onopen = r; });
await send('Runtime.enable');

// Pages 面板太小（6 行）时，把它的下分隔条往下拖，让整棵页树能滚/能点
const info = await send('Runtime.evaluate', { expression: `(()=>{
  const leaf=[...document.querySelectorAll('*')].find(x=>x.children.length===0 && x.textContent.trim()===` + JSON.stringify(rootPage) + `);
  const tr=leaf && leaf.closest('.EezStudio_Tree');
  if(!tr) return 'none';
  const tb=tr.getBoundingClientRect();
  if(tb.height>=300) return 'skip';
  const sp=[...document.querySelectorAll('.flexlayout__splitter_horz')].find(e=>{
    const b=e.getBoundingClientRect();
    return b.x<=tb.x+2 && b.x+b.width>=tb.x+tb.width-2 && Math.abs(b.y-tb.bottom)<8;
  });
  if(!sp) return 'none';
  const b=sp.getBoundingClientRect();
  return JSON.stringify([Math.round(b.x+b.width/2), Math.round(b.y+2), Math.round(tb.height)]);
})()`, returnByValue: true });
const v = info.result.result.value;
if (v !== 'skip' && v !== 'none') {
  const [x, y] = JSON.parse(v);
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: 1 });
  for (const dy of [40, 80, 120, 160, 200, 240]) {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y: y + dy, button: 'left', buttons: 1 });
    await new Promise(r => setTimeout(r, 60));
  }
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y: y + 240, button: 'left', buttons: 0, clickCount: 1 });
  await new Promise(r => setTimeout(r, 300));
}
console.log('OK');
process.exit(0);
"""


def render_design(frame, out):
    import cairosvg
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
           'font-family="Microsoft YaHei,Noto Sans SC,sans-serif">'
           '<rect width="%d" height="%d" fill="#05080F"/>%s</svg>'
           % (W, H, W, H, W, H, frame or ""))
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=out,
                     output_width=W, output_height=H)


def kill_eez():
    subprocess.call(["taskkill", "/F", "/IM", "EEZ Studio.exe"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_cdp(seconds=60):
    import urllib.request
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            data = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=2))
            if any(p.get("type") == "page" and "EEZ Studio" in (p.get("title") or "")
                   for p in data):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def click_node(page_id, root_id):
    js = os.path.join(TMP, "eez_click_node.js")
    with open(js, "w", encoding="utf-8") as f:
        f.write(CLICK_JS)
    all_ids = ",".join(sorted(set(PAGE_IDS.values())))
    r = subprocess.run(["node", js, page_id, root_id, all_ids], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if not r.stdout.strip().endswith("OK"):
        print("    [click] %s -> %s %s" % (page_id, r.stdout.strip()[:80], (r.stderr or "")[:80]))
    return r.stdout.strip().endswith("OK")


def setup_layout(root_id):
    js = os.path.join(TMP, "eez_setup.js")
    with open(js, "w", encoding="utf-8") as f:
        f.write(SETUP_JS)
    subprocess.run(["node", js, root_id], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")


def grab(out_png):
    grab_js = os.path.join(KIT, "tools", "cdp", "grab.js")
    if os.path.exists(out_png):
        os.remove(out_png)
    for _ in range(2):
        subprocess.run(["node", grab_js, "--port", "9222", "--canvas", "--visible",
                        "--out", out_png],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
        if os.path.isfile(out_png) and os.path.getsize(out_png) > 5000:
            return True
        time.sleep(0.8)
    return False


def coef_of(a_png, b_png):
    from PIL import Image, ImageChops
    a = Image.open(a_png).convert("RGB")
    b = Image.open(b_png).convert("RGB")
    hist = ImageChops.difference(a, b).convert("L").histogram()
    return sum(hist[30:]) / float(sum(hist)) * 100.0


def side_by_side(a_png, b_png, out_png):
    from PIL import Image
    a = Image.open(a_png).convert("RGB")
    b = Image.open(b_png).convert("RGB")
    w, h = a.size
    canvas = Image.new("RGB", (w, h * 2), (10, 12, 18))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (0, h))
    canvas.save(out_png)


def render_design_edge(frame, out):
    """基准图 = H5「高清设计图」那张帧（浏览器渲染，避免 cairosvg 缺中文字体）。"""
    html = os.path.join(TMP, "d_page.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html><body style="margin:0;background:#05080F">'
                '<svg width="%d" height="%d" viewBox="0 0 %d %d" '
                'font-family="Microsoft YaHei,Noto Sans SC,sans-serif">%s</svg></body></html>'
                % (W, H, W, H, frame or ""))
    probe = os.path.join(KIT, "tools", "cdp", "h5_probe.js")
    subprocess.run(["node", probe, "--url", "file:///" + html.replace("\\", "/"),
                    "--out", out, "--clip", "0,0,%d,%d" % (W, H)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
    return os.path.isfile(out) and os.path.getsize(out) > 3000


def start_edge():
    sh = os.path.join(KIT, "tools", "cdp", "h5_edge.sh")
    subprocess.run(["bash", sh, os.path.join("tmp", "edgeprof"), "about:blank"],
                   cwd=ROOT, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
    time.sleep(1)


def stop_edge():
    sh = os.path.join(KIT, "tools", "cdp", "h5_edge.sh")
    subprocess.run(["bash", sh, os.path.join("tmp", "edgeprof"), "--kill"],
                   cwd=ROOT, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")


def launch(profile, settle=15):
    """每次全新起一个 EEZ（同一 profile 复用字体缓存），等 CDP + 首屏渲染。"""
    kill_eez()
    time.sleep(2)
    env = dict(os.environ)
    env.pop("ELECTRON_RUN_AS_NODE", None)
    subprocess.Popen([EEZ_EXE, "--remote-debugging-port=9222", "--user-data-dir=" + profile,
                      "--no-sandbox", "--disable-gpu", "--enable-unsafe-swiftshader", PROJ],
                     env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=0x08000000)
    if not wait_cdp():
        return False
    time.sleep(settle)
    setup_layout(PAGE_IDS.get("主控", "main"))
    return True


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(SHOT_DIR, exist_ok=True)
    only = sys.argv[sys.argv.index("--page") + 1] if "--page" in sys.argv else None
    multi = sys.argv[sys.argv.index("--pages") + 1].split(",") if "--pages" in sys.argv else None
    names = [n for n, _f, _e, _x, _r in pg.PAGES]
    frames = {n: f for n, f, _e, _x, _r in pg.PAGES}
    pages = [only] if only else (multi if multi else names)   # 默认全量（整轮只起一次 EEZ）
    settle = 15

    start_edge()
    rows, fails = [], []
    root_id = PAGE_IDS.get(pg.PAGES[0][0], "main")
    prof = os.path.join(TMP, "eezprof")
    alive = launch(prof)                    # ★ 整轮只起一次 EEZ，逐页切换（不再每页开关窗口）

    for cn in pages:
        pid = PAGE_IDS.get(cn, "page")
        if not render_design_edge(frames[cn], os.path.join(TMP, "d_%s.png" % pid)):
            fails.append((cn, "基准图渲染失败"))
            print("  %-10s —— 基准图渲染失败" % cn, flush=True)
            continue
        best = None
        last_bad = None
        for attempt in range(3):
            if not alive:
                alive = launch(prof)
                if not alive:
                    continue
            ok = False
            for _ in range(3):
                if click_node(pid, root_id):
                    ok = True
                    break
                time.sleep(0.8)
            time.sleep(3.5)                 # 切页后画布要时间重绘
            got = ok and grab(os.path.join(TMP, "c_%s.png" % pid))
            if not got:
                continue
            c = coef_of(os.path.join(TMP, "d_%s.png" % pid), os.path.join(TMP, "c_%s.png" % pid))
            if c > 20.0:                    # 抓到别的页：同实例再切一次
                last_bad = c
                continue
            if best is None or c < best[0]:
                best = (c, os.path.join(TMP, "c_%s.png" % pid))
            if c <= SUSPECT:                # 稳定可信，不必再试
                break
        if best is None:
            # 单页兜底：只在确实抓不到时重启一次 EEZ
            kill_eez()
            time.sleep(1.0)
            alive = launch(prof)
            if alive and click_node(pid, root_id):
                time.sleep(2.5)
                if grab(os.path.join(TMP, "c_%s.png" % pid)):
                    c = coef_of(os.path.join(TMP, "d_%s.png" % pid),
                                os.path.join(TMP, "c_%s.png" % pid))
                    if c <= 20.0:
                        best = (c, os.path.join(TMP, "c_%s.png" % pid))
        if best is None:
            why = ("疑似抓错页（最小差异 %.1f%%）" % last_bad) if last_bad else "画布未取到"
            fails.append((cn, why))
            print("  %-10s —— %s" % (cn, why), flush=True)
            continue
        c, c_png = best
        sim = 100.0 - c
        rows.append((cn, c))
        suspect = c > SUSPECT
        keep = bool(os.environ.get("D5_KEEP_ALL")) or c > SAVE_ABOVE or cn == names[0] or suspect
        if keep:
            side_by_side(os.path.join(TMP, "d_%s.png" % pid), c_png,
                         os.path.join(SHOT_DIR, "%s.png" % cn))
        print("  %-10s 相似度 %5.2f%%（差异 %4.2f%%）  %s"
              % (cn, sim, c, "疑似抓错页" if suspect else ("留图" if keep else "")), flush=True)
        for f in (os.path.join(TMP, "d_%s.png" % pid), c_png):
            try:
                os.remove(f)
            except OSError:
                pass

    stop_edge()
    if rows:
        worst = max(rows, key=lambda x: x[1])
        avg = sum(c for _n, c in rows) / len(rows)
        summary = "%d 页 ｜ 平均相似度 %.2f%% ｜ 最低 %.2f%%（%s）" % (
            len(rows), 100.0 - avg, 100.0 - worst[1], worst[0])
    else:
        summary = "无有效结果"
    stamp = time.strftime("%Y-%m-%d %H:%M")
    lines = ["%s ｜ %s" % (stamp, summary)]
    for cn, c in rows:
        lines.append("  %-10s 相似度 %.2f%%（差异 %.2f%%）%s"
                     % (cn, 100.0 - c, c, "  （差异>8% 疑似抓错页）" if c > 8 else ""))
    for cn, why in fails:
        lines.append("  %-10s 失败：%s" % (cn, why))
    with open(COEF_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("[D5] %s" % summary, flush=True)
    print("[D5] 记录", COEF_FILE)
    if fails:
        print("[D5] %d 页失败：%s" % (len(fails), fails[:4]))
        sys.exit(1)


if __name__ == "__main__":
    main()
