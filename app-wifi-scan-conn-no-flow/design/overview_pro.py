from pathlib import Path
import base64, json, re, sys, importlib.util
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
sys.path.insert(0, str(ROOT/'design'))
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('wifi_annotate', ROOT/'design'/'annotate.py')
ann = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ann)
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
    controls=[dict(n=i, name=x[3], ident=x[2], box=x[4], category=ann.CAT[x[0]][0], action=x[5][1] if x[5] else '展示') for i,x in enumerate(ann.CONTROLS[stem],1)]
    rows.append(dict(id=num,title=title,desc=desc,raw=raw,marked=marked,source=source,controls=controls))
payload=json.dumps(rows,ensure_ascii=False).replace('</','<\\/')
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wi-Fi 示例 · H5 设计评审</title><style>
*{box-sizing:border-box}body{margin:0;font-family:Microsoft YaHei,Arial,sans-serif;background:#0b1220;color:#edf4ff}header{padding:22px 4vw;background:#111e30;position:sticky;top:0;z-index:3}h1{font-size:22px;margin:0 0 8px}header p,.hint{color:#aabbce;font-size:14px;line-height:1.6;margin:0}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}button{background:#263a53;color:#e6f1ff;border:1px solid #405875;padding:10px 16px;border-radius:8px;cursor:pointer}button.active{background:#5183ea;color:#09172a}.wrap{max-width:1500px;margin:auto;padding:24px 4vw}.hint{background:#18283b;padding:14px;border-radius:10px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr));gap:18px;margin-top:22px}.card{background:#172437;padding:16px;border:1px solid #2b4058;border-radius:12px}.card h2{font-size:18px;margin:0 0 8px}.card p{color:#aabbce;margin:0 0 12px;font-size:14px}.art{background:#0b0f1a;border-radius:8px;overflow:hidden}.art svg{display:block;width:100%;height:auto}.single{max-width:880px;margin:25px auto}.single .card{padding:20px}.list{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.small{font-size:13px;color:#aabbce;line-height:1.6;margin-top:12px}footer{padding:25px 0;color:#aabbce;font-size:13px}
</style></head><body><header><h1>Wi-Fi 连接示例 · 设计评审</h1><p>原工程 480 × 320 · 原图直接内嵌 · 本页用于查看设计状态</p><div class="toolbar"><button id="gallery" class="active">状态总览</button><button id="jump">状态演练</button><button id="single">高清设计图</button><button id="marks">标注：开</button><button id="export">导出批注</button></div></header><main class="wrap"><div class="hint">画面来自示例工程已有设计图；网络名称和状态是示意数据。状态演练仅模拟界面切换，不执行真实扫描或连接。右键图像添加位置批注，右键控件清单添加控件批注。个别原稿从现有标注图中提取，标注源来自既有控件清单。</div><div id="content"></div><footer>设计源：design/mockup_gen.py；标注源：design/annotate.py。动态网络列表由应用运行时生成，实际行为和布局以工程与仿真验证为准。</footer></main><script id="data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent);let mode='gallery',marks=true,selected=0,trail=[];
const content=document.getElementById('content'), key='wifi_example_annotations_v1';
let annotations=[];try{annotations=JSON.parse(localStorage.getItem(key)||'[]')}catch(e){}
function save(){try{localStorage.setItem(key,JSON.stringify(annotations))}catch(e){alert('浏览器不允许保存批注，请检查本地存储设置。')}}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function go(id){let n=data.findIndex(x=>x.id===id);if(n<0)return;trail.push(selected);selected=n;render()}
function back(){if(trail.length)selected=trail.pop();render()}
function art(d,interactive){let a=marks&&d.marked?d.marked:d.raw;return `<div class="art" data-page="${esc(d.id)}">${a}</div>`}
function controls(d){return '<div class="small">控件清单（右键可批注）</div><div class="list">'+d.controls.map(c=>`<button data-ctrl="${c.n}" data-page="${d.id}" title="${esc(c.action)}">${c.n} · ${esc(c.name)} · ${esc(c.category)}</button>`).join('')+'</div>'}
function card(d){return `<section class="card"><h2>${esc(d.id+' · '+d.title)}</h2><p>${esc(d.desc)}</p>${art(d)}${controls(d)}<div class="small">${esc(d.source)}</div></section>`}
const steps={
 '01':[['刷新扫描','02'],['选择加密网络','04'],['长按已保存网络','11']],
 '02':[['发现网络','01'],['未发现网络','03']],
 '03':[['重新扫描','02']],
 '04':[['关闭半页','01'],['输入不合法','05'],['连接','06']],
 '05':[['关闭半页','01'],['重新连接','06']],
 '06':[['连接成功','10'],['连接失败','07']],
 '07':[['返回列表','01'],['重试','06']],
 '10':[['刷新扫描','02'],['长按已保存网络','11']],
 '11':[['取消','01'],['忘记网络','01']]
};
function render(){for(const k of ['gallery','jump','single'])document.getElementById(k).classList.toggle('active',mode===k);document.getElementById('marks').textContent='标注：'+(marks?'开':'关');
if(mode==='gallery'){content.innerHTML='<div class="grid">'+data.map(card).join('')+'</div>'}
else if(mode==='single'){content.innerHTML='<div class="single">'+card(data[selected])+'<div class="list">'+data.map((d,i)=>`<button data-i="${i}" class="${i===selected?'active':''}">${esc(d.title)}</button>`).join('')+'</div></div>'}
else{const d=data[selected];content.innerHTML='<div class="single"><div class="small">当前状态：'+esc(d.title)+' ← '+(trail.length?esc(data[trail[trail.length-1]].title):'无来路')+'</div>'+card(d)+'<div class="small">场景演练（选择下一个状态）</div><div class="list">'+steps[d.id].map(([label,id])=>`<button data-go="${id}">${esc(label)}</button>`).join('')+'<button id="back" '+(!trail.length?'disabled':'')+'>返回上一步</button><button id="reset">回列表</button></div></div>';content.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));document.getElementById('back').onclick=back;document.getElementById('reset').onclick=()=>{selected=0;trail=[];render()}}
content.querySelectorAll('[data-i]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.i);render()});}
for(const k of ['gallery','jump','single'])document.getElementById(k).onclick=()=>{mode=k;render()};
document.getElementById('marks').onclick=()=>{marks=!marks;render()};
document.getElementById('export').onclick=()=>{const blob=new Blob([JSON.stringify({version:1,project:'app-wifi-scan-conn-no-flow',annotations},null,2)],{type:'application/json'});const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='wifi_annotations.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
content.addEventListener('contextmenu',e=>{let ctrl=e.target.closest('[data-ctrl]'),area=e.target.closest('.art');if(!ctrl&&!area)return;e.preventDefault();let page=(ctrl||area).dataset.page,record;
if(ctrl){let n=Number(ctrl.dataset.ctrl),d=data.find(x=>x.id===page),c=d.controls.find(x=>x.n===n);record={page,type:'control',n,name:c.name,ident:c.ident,box:c.box}}
else{let svg=area.querySelector('svg'),pt=svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;pt=pt.matrixTransform(svg.getScreenCTM().inverse());record={page,type:'pin',x:Math.round(pt.x),y:Math.round(pt.y),coordinate_space:'SVG viewBox'}}
let note=prompt('输入批注（取消则不保存）');if(note===null||!note.trim())return;record.note=note.trim();annotations.push(record);save();alert('批注已保存，共 '+annotations.length+' 条；可点击“导出批注”。')});
render();
</script></body></html>'''.replace('__DATA__',payload)
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(html,encoding='utf-8')
print('frames',len(rows),'annotated',sum(bool(r['marked']) for r in rows),'output',OUT)
