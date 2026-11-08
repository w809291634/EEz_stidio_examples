from pathlib import Path
import base64, json, re, sys
from html import escape

# 优先使用项目中的生成产物；原始图稿缺失时，从对应已标注图中提取其内嵌原稿。
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT/'designer_simple'/'overview_pro.html'
items = [
 ('01','列表主态','mockup_01_list','已连接、已保存及可用网络示例'),
 ('02','扫描中','mockup_02_scanning','显示扫描状态'),
 ('03','无网络','mockup_03_empty','空状态与重新扫描'),
 ('04','密码半页','mockup_04_sheet','输入密码与键盘'),
 ('05','密码错误','mockup_05_sheet_error','输入错误状态'),
 ('06','连接中','mockup_06_connecting','连接等待状态'),
 ('07','连接失败','mockup_07_failed','失败提示'),
 ('10','已连接','mockup_10_connected','连接成功状态'),
 ('11','网络操作','mockup_11_menu','已保存网络操作对话框'),
]
rows=[]
for num,title,stem,desc in items:
    a=ROOT/'designer_annotated'/f'{stem}_annot.svg'
    original=ROOT/'design'/'mockups'/f'{stem}.svg'
    marked=a.read_text(encoding='utf-8') if a.exists() else None
    if original.exists(): raw=original.read_text(encoding='utf-8'); source='设计源生成的 SVG'
    elif marked:
        m=re.search(r'href="data:image/svg\+xml;base64,([^"]+)"',marked)
        if not m: raise ValueError('无法从标注图提取原稿: '+stem)
        raw=base64.b64decode(m.group(1)).decode('utf-8'); source='标注图内嵌原稿（原始 SVG 缺失）'
    else: raise FileNotFoundError(stem)
    rows.append(dict(id=num,title=title,desc=desc,raw=raw,marked=marked,source=source))
payload=json.dumps(rows,ensure_ascii=False).replace('</','<\\/')
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wi-Fi 示例 · H5 设计评审</title><style>
*{box-sizing:border-box}body{margin:0;font-family:Microsoft YaHei,Arial,sans-serif;background:#0b1220;color:#edf4ff}header{padding:22px 4vw;background:#111e30;position:sticky;top:0;z-index:3}h1{font-size:22px;margin:0 0 8px}header p,.hint{color:#aabbce;font-size:14px;line-height:1.6;margin:0}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}button{background:#263a53;color:#e6f1ff;border:1px solid #405875;padding:10px 16px;border-radius:8px;cursor:pointer}button.active{background:#5183ea;color:#09172a}.wrap{max-width:1500px;margin:auto;padding:24px 4vw}.hint{background:#18283b;padding:14px;border-radius:10px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr));gap:18px;margin-top:22px}.card{background:#172437;padding:16px;border:1px solid #2b4058;border-radius:12px}.card h2{font-size:18px;margin:0 0 8px}.card p{color:#aabbce;margin:0 0 12px;font-size:14px}.art{background:#0b0f1a;border-radius:8px;overflow:hidden}.art svg{display:block;width:100%;height:auto}.single{max-width:880px;margin:25px auto}.single .card{padding:20px}.list{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.small{font-size:13px;color:#aabbce;line-height:1.6;margin-top:12px}footer{padding:25px 0;color:#aabbce;font-size:13px}
</style></head><body><header><h1>Wi-Fi 连接示例 · 设计评审</h1><p>原工程 480 × 320 · 原图直接内嵌 · 本页用于查看设计状态</p><div class="toolbar"><button id="gallery" class="active">状态总览</button><button id="single">高清设计图</button><button id="marks">标注：开</button></div></header><main class="wrap"><div class="hint">画面来自示例工程已有设计图；网络名称和状态是示意数据。此页仅供设计评审，状态切换不代表真实扫描或连接。个别原稿从现有标注图中提取，标注源来自既有控件清单。</div><div id="content"></div><footer>设计源：design/mockup_gen.py；标注源：design/annotate.py。动态网络列表由应用运行时生成，实际行为和布局以工程与仿真验证为准。</footer></main><script id="data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent);let mode='gallery',marks=true,selected=0;
const content=document.getElementById('content');
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function card(d,i){const art=marks&&d.marked?d.marked:d.raw;return `<section class="card"><h2>${esc(d.id+' · '+d.title)}</h2><p>${esc(d.desc)}</p><div class="art">${art}</div><div class="small">${esc(d.source)}${!d.marked?' · 无现有标注图':''}</div></section>`;}
function render(){document.getElementById('gallery').classList.toggle('active',mode==='gallery');document.getElementById('single').classList.toggle('active',mode==='single');document.getElementById('marks').textContent='标注：'+(marks?'开':'关');if(mode==='gallery'){content.innerHTML='<div class="grid">'+data.map(card).join('')+'</div>'}else{content.innerHTML='<div class="single">'+card(data[selected],selected)+'<div class="list">'+data.map((d,i)=>`<button data-i="${i}" class="${i===selected?'active':''}">${esc(d.title)}</button>`).join('')+'</div></div>';content.querySelectorAll('[data-i]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.i);render()})}}
document.getElementById('gallery').onclick=()=>{mode='gallery';render()};document.getElementById('single').onclick=()=>{mode='single';render()};document.getElementById('marks').onclick=()=>{marks=!marks;render()};render();
</script></body></html>'''.replace('__DATA__',payload)
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(html,encoding='utf-8')
print('frames',len(rows),'annotated',sum(bool(r['marked']) for r in rows),'output',OUT)
