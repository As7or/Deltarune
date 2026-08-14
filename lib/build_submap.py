import json, os, re, html, random, urllib.parse, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_prep import prepare_image

def slugify(name):
    nfkd = unicodedata.normalize('NFKD', name)
    return nfkd.encode('ascii', 'ignore').decode('ascii') or name

NOTES_DIR = None
SPRITES_DIR = None
OUT_DIR = None
NOTE_STEMS = set()

def configure(notes_dir, sprites_dir, out_dir):
    """Llamar antes de generar submapas: fija las rutas reales del vault del usuario."""
    global NOTES_DIR, SPRITES_DIR, OUT_DIR, NOTE_STEMS
    NOTES_DIR = notes_dir
    SPRITES_DIR = sprites_dir
    OUT_DIR = out_dir
    NOTE_STEMS = {os.path.splitext(f)[0] for f in os.listdir(notes_dir) if f.endswith(".md")}

EDGE_COLOR_MAP = {
    "1": "#b23c30", "2": "#c97a3d", "3": "#c9982e",
    "4": "#2e8b46", "5": "#3a9aa6", "6": "#6b3fa0", None: "#8a7a5c",
}
NODE_COLOR_MAP = {
    "1": "#b23c30", "2": "#c97a3d", "3": "#c9982e",
    "4": "#2e8b46", "5": "#3a9aa6", "6": "#6b3fa0",
    "#6b7280": "#6b7280", "6b7280": "#6b7280", None: "#8a7a5c",
}

def note_for_title(title, fallback_stem):
    if title in NOTE_STEMS:
        return slugify(title)
    base = re.sub(r"\s*\(.*?\)\s*", "", title).strip()
    if base in NOTE_STEMS:
        return slugify(base)
    return slugify(fallback_stem) if fallback_stem in NOTE_STEMS else None

def clean_text(t):
    t = t.replace("\\n", "\n")
    parts = t.strip().split("\n", 1)
    title = parts[0].strip()
    title = re.sub(r"^#+\s*", "", title)
    title = re.sub(r"\*\*", "", title).strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    body = re.sub(r"\*\*", "", body)
    body = re.sub(r"\n+", " ", body).strip()
    return title, body

def brightness_of(path):
    try:
        from PIL import Image
        im = Image.open(path)
        if getattr(im, "is_animated", False):
            im.seek(0)
        im = im.convert("RGBA")
        pixels = im.getdata()
        total, count = 0, 0
        for i, (r, g, b, a) in enumerate(pixels):
            if i % 11 != 0 or a < 25:
                continue
            total += 0.299*r + 0.587*g + 0.114*b
            count += 1
        return (total/count) if count else None
    except Exception:
        return None

PAGE_CSS = '''
  :root{ --cork-base:#5c5347; --cork-shadow:rgba(15,12,8,0.55); }
  html,body{ margin:0; padding:0; font-family:'Segoe UI', Tahoma, sans-serif; height:100%; overflow:hidden; }
  #viewport{
    position:relative; width:100%; height:100vh; overflow:hidden; cursor:grab;
    background-color: var(--cork-base);
    background-image:
      radial-gradient(circle at 15% 20%, rgba(255,255,255,0.045) 0, transparent 40%),
      radial-gradient(circle at 80% 10%, rgba(0,0,0,0.12) 0, transparent 35%),
      radial-gradient(circle at 60% 75%, rgba(0,0,0,0.14) 0, transparent 45%),
      radial-gradient(circle at 30% 85%, rgba(255,255,255,0.035) 0, transparent 40%),
      repeating-radial-gradient(circle at 50% 50%, rgba(60,38,12,0.12) 0px, transparent 2px, transparent 6px);
  }
  #viewport.panning{ cursor:grabbing; }
  #board{ position:absolute; top:0; left:0; transform-origin:0 0; will-change:transform; }
  svg#strings{ position:absolute; top:0; left:0; width:100%; height:100%; overflow:visible; }
  .string-hit{ stroke:transparent; stroke-width:16; fill:none; }
  .string-shadow{ stroke:rgba(0,0,0,0.28); stroke-width:3.2; fill:none; }
  .string-visible{ fill:none; stroke-width:2.6; }
  #highlight-svg{ position:absolute; top:0; left:0; width:100%; height:100%; overflow:visible; pointer-events:none; z-index:9999; }
  .highlight-shadow{ stroke:rgba(0,0,0,0.32); stroke-width:5.5; fill:none; }
  .highlight-visible{ stroke-width:4.5; fill:none; }
  .highlight-label-bg{ fill:rgba(35,24,12,0.92); }
  .highlight-label{ font-size:14px; font-weight:bold; fill:#efe6d3; }
  .node{ position:absolute; text-align:center; cursor:pointer; user-select:none; transition:transform .15s ease; z-index:2; }
  .node:hover{ transform:rotate(0deg) scale(1.06) !important; z-index:10; }
  .node.node-center:hover{ transform:rotate(0deg) scale(1.04) !important; }
  .card{ background:#fdfaf3; padding:8px 8px 12px 8px; border-radius:2px; box-shadow:3px 6px 10px var(--cork-shadow); }
  .center-card{ padding:10px 10px 14px 10px; }
  .thumb{ width:100%; display:flex; align-items:center; justify-content:center; overflow:hidden; background-color:#3a3a3a; }
  .thumb-dark{ background-color:#f2f2f2; }
  .thumb img{ width:100%; height:100%; object-fit:contain; display:block; image-rendering:pixelated; }
  .noimg{ color:#999; font-size:11px; padding:20px 0; }
  .title{ font-size:12px; font-weight:bold; color:#2c2416; margin-top:8px; }
  .center-card .title{ font-size:14px; }
  .caption{ font-size:10.5px; margin-top:4px; color:#5a4d38; font-style:italic; line-height:1.3; }
  .pin{ position:absolute; top:-9px; left:50%; transform:translateX(-50%); width:16px; height:16px; z-index:5; }
  .pin svg{ width:100%; height:100%; display:block; filter:drop-shadow(1px 2px 1px rgba(0,0,0,0.4)); }
  #legend{ position:fixed; bottom:14px; left:14px; background:rgba(253,250,243,0.92); border-radius:6px; padding:10px 14px; font-size:12px; color:#3a2f22; box-shadow:2px 3px 8px rgba(0,0,0,0.25); z-index:50; }
  #legend div{ margin:3px 0; display:flex; align-items:center; gap:6px; }
  #legend .swatch{ width:22px; height:3px; display:inline-block; border-radius:2px; }
  #zoomhint{ position:fixed; bottom:14px; right:14px; background:rgba(253,250,243,0.92); border-radius:6px; padding:8px 12px; font-size:11px; color:#3a2f22; box-shadow:2px 3px 8px rgba(0,0,0,0.25); z-index:50; max-width:220px; }
  #back-link{ position:fixed; top:14px; left:14px; background:rgba(253,250,243,0.92); border-radius:6px; padding:8px 14px; font-size:12px; color:#3a2f22; box-shadow:2px 3px 8px rgba(0,0,0,0.25); z-index:50; text-decoration:none; font-weight:bold; }

  #note-panel{ position:fixed; background:#fbf6e9; box-shadow:-4px 0 20px rgba(0,0,0,0.4); z-index:100; }
  #note-panel.mode-side{ top:0; right:-560px; width:540px; height:100%; transition:right .28s ease; }
  #note-panel.mode-side.open{ right:0; }
  #note-panel.mode-center{
    top:50%; left:50%; right:auto; width:min(920px,88vw); height:86vh; border-radius:12px;
    transform:translate(-50%,-50%) scale(0.94); opacity:0; pointer-events:none;
    box-shadow:0 24px 70px rgba(0,0,0,0.55); transition:opacity .2s ease, transform .2s ease;
  }
  #note-panel.mode-center.open{ opacity:1; pointer-events:auto; transform:translate(-50%,-50%) scale(1); }
  #note-panel .note-header{ background:#3a2f22; color:#f3ead6; padding:14px 20px; display:flex; justify-content:space-between; align-items:center; gap:10px; }
  #note-panel .note-header .btns{ display:flex; gap:8px; }
  #note-panel .note-header button{ background:none; border:1px solid #f3ead6; color:#f3ead6; border-radius:4px; padding:4px 10px; cursor:pointer; font-size:13px; white-space:nowrap; }
  #note-panel .note-header button.active{ background:#f3ead6; color:#3a2f22; }
  #note-panel iframe{ width:100%; height:calc(100% - 49px); border:none; }
  #overlay{ position:fixed; inset:0; background:rgba(0,0,0,0.35); opacity:0; pointer-events:none; transition:opacity .28s ease; z-index:90; }
  #overlay.open{ opacity:1; pointer-events:auto; }
'''

def build_submap(canvas_path, title_name):
    d = json.load(open(canvas_path, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    edges = d["edges"]

    text_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "text"}
    file_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "file"}
    used_file_ids = set()

    items = []
    for nid, n in text_nodes.items():
        title, body = clean_text(n.get("text", ""))
        cx = n["x"] + n["width"]/2
        cy = n["y"] + n["height"]/2
        img_node = file_nodes.get(nid + "-img")
        img_name = None
        if img_node:
            img_name = img_node["file"].split("/")[-1]
            used_file_ids.add(nid + "-img")
        node_color = NODE_COLOR_MAP.get(n.get("color"), "#8a7a5c")
        note_stem = note_for_title(title, title_name)
        items.append({
            "id": nid, "title": title, "body": body, "cx": cx, "cy": cy,
            "w": n["width"], "h": n["height"], "color": node_color,
            "img": img_name, "note": note_stem, "is_center": nid == "center",
        })

    for nid, n in file_nodes.items():
        if nid in used_file_ids:
            continue
        cx = n["x"] + n["width"]/2
        cy = n["y"] + n["height"]/2
        items.append({
            "id": nid, "title": "", "body": "", "cx": cx, "cy": cy,
            "w": n["width"], "h": n["height"], "color": "#8a7a5c",
            "img": n["file"].split("/")[-1], "note": None, "is_center": False,
        })

    item_ids = {it["id"] for it in items}
    links = []
    for e in edges:
        fn, tn = e.get("fromNode"), e.get("toNode")
        if fn in item_ids and tn in item_ids:
            links.append({
                "from": fn, "to": tn,
                "color": EDGE_COLOR_MAP.get(e.get("color"), "#8a7a5c"),
                "label": e.get("label", "") or "",
            })

    if not items:
        return None

    SCALE = 0.42
    xs = [it["cx"] for it in items]; ys = [it["cy"] for it in items]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    PAD = 180
    board_w = int((maxx-minx)*SCALE + PAD*2) or 800
    board_h = int((maxy-miny)*SCALE + PAD*2) or 600
    for it in items:
        it["px"] = (it["cx"] - minx) * SCALE + PAD
        it["py"] = (it["cy"] - miny) * SCALE + PAD

    node_html = []
    for it in items:
        nid = it["id"]
        random.seed(canvas_path + nid)
        rot = random.uniform(-4, 4)
        is_center = it["is_center"]
        width = 250 if is_center else 190
        x, y = it["px"], it["py"]

        is_dark = False
        if it["img"]:
            path = os.path.join(SPRITES_DIR, it["img"])
            b = brightness_of(path)
            is_dark = (b is not None and b < 70)
            mime, b64 = prepare_image(path, maxw=(260 if is_center else 200))
            img_tag = f'<img src="data:{mime};base64,{b64}" alt="">' if b64 else '<div class="noimg"><i>sin imagen</i></div>'
        else:
            img_tag = '<div class="noimg"><i>sin imagen</i></div>'

        thumb_class = "thumb thumb-dark" if is_dark else "thumb"
        title_html = html.escape(it["title"]) if it["title"] else ""
        body_html = html.escape(it["body"]) if it["body"] else ""
        note_attr = it["note"] or ""
        cardclass = "card center-card" if is_center else "card"
        thumb_h = 150 if is_center else 100
        node_html.append(f'''
  <div class="node{" node-center" if is_center else ""}" data-id="{nid}" data-note="{note_attr}" style="left:{x-width/2:.0f}px; top:{y-(160 if is_center else 105):.0f}px; width:{width}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    <div class="{cardclass}" style="border-top:5px solid {it['color']};">
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      {f'<div class="title">{title_html}</div>' if title_html else ""}
      {f'<div class="caption">{body_html}</div>' if body_html else ""}
    </div>
  </div>''')

    nodes_str = "\n".join(node_html)
    links_js = ",\n  ".join([
        "[" + ",".join(json.dumps(v, ensure_ascii=False) for v in (l['from'], l['to'], l['color'], l['label'])) + "]"
        for l in links
    ])

    page = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Submapa — {html.escape(title_name)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<a id="back-link" href="../corcho-principal.html">&larr; Corcho principal</a>
<div id="viewport">
  <div id="board" style="width:{board_w}px; height:{board_h}px;">
    <svg id="strings"></svg>
{nodes_str}
    <svg id="highlight-svg"></svg>
  </div>
</div>
<div id="zoomhint">Rueda = zoom &middot; arrastra el fondo para moverte &middot; clic en una nota = abrir su pagina</div>
<div id="overlay"></div>
<div id="note-panel" class="mode-side">
  <div class="note-header">
    <span id="note-title-bar">Nota</span>
    <div class="btns">
      <button id="mode-side-btn" class="active" title="Ver al lado">Lateral</button>
      <button id="mode-center-btn" title="Ver centrado, mas grande">Centrado</button>
      <button id="note-close">Cerrar X</button>
    </div>
  </div>
  <iframe id="note-frame" src=""></iframe>
</div>
<script>
const svg = document.getElementById('strings');
const NS = 'http://www.w3.org/2000/svg';
const links = [
  {links_js}
];
const board = document.getElementById('board');
const viewport = document.getElementById('viewport');
let zoom = 0.85, panX = 60, panY = 60;
const MIN_ZOOM = 0.25, MAX_ZOOM = 2.5;

function applyTransform(){{ board.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{zoom}})`; }}
applyTransform();

viewport.addEventListener('wheel', (e) => {{
  e.preventDefault();
  const rect = viewport.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const boardX = (px - panX) / zoom, boardY = (py - panY) / zoom;
  const delta = -e.deltaY * 0.0015;
  const newZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom + delta * zoom));
  panX = px - boardX * newZoom; panY = py - boardY * newZoom; zoom = newZoom;
  applyTransform();
}}, {{ passive:false }});

function center(el){{
  const pin = el.querySelector('.pin');
  const b = board.getBoundingClientRect();
  const r = (pin || el).getBoundingClientRect();
  return {{ x:(r.left-b.left)/zoom + r.width/zoom/2, y:(r.top-b.top)/zoom + r.height/zoom/2 }};
}}

const highlightSvg = document.getElementById('highlight-svg');
function showHighlight(p1,p2,mx,my,color,label){{
  highlightSvg.innerHTML = '';
  const g = document.createElementNS(NS,'g');
  const shadow = document.createElementNS(NS,'path');
  shadow.setAttribute('class','highlight-shadow');
  shadow.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my+5}} ${{p2.x}} ${{p2.y}}`);
  g.appendChild(shadow);
  const path = document.createElementNS(NS,'path');
  path.setAttribute('class','highlight-visible');
  path.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
  path.setAttribute('stroke', color);
  path.style.filter = `drop-shadow(0 0 5px ${{color}}) drop-shadow(0 0 5px ${{color}})`;
  g.appendChild(path);
  if(label){{
    const textEl = document.createElementNS(NS,'text');
    textEl.setAttribute('x', mx); textEl.setAttribute('y', my);
    textEl.setAttribute('text-anchor','middle'); textEl.setAttribute('class','highlight-label');
    textEl.textContent = label;
    g.appendChild(textEl);
    highlightSvg.appendChild(g);
    const bb = textEl.getBBox();
    const bgRect = document.createElementNS(NS,'rect');
    bgRect.setAttribute('x', bb.x-8); bgRect.setAttribute('y', bb.y-4);
    bgRect.setAttribute('width', bb.width+16); bgRect.setAttribute('height', bb.height+8);
    bgRect.setAttribute('rx', 3); bgRect.setAttribute('class','highlight-label-bg');
    g.insertBefore(bgRect, textEl);
  }} else {{
    highlightSvg.appendChild(g);
  }}
}}
function hideHighlight(){{ highlightSvg.innerHTML=''; }}

function draw(){{
  svg.innerHTML = '';
  highlightSvg.innerHTML = '';
  links.forEach(([a,b,color,label])=>{{
    const elA = document.querySelector(`[data-id="${{a}}"]`);
    const elB = document.querySelector(`[data-id="${{b}}"]`);
    if(!elA||!elB) return;
    const p1 = center(elA), p2 = center(elB);
    const dist = Math.hypot(p2.x-p1.x, p2.y-p1.y);
    const sag = Math.min(50, dist*0.12);
    const mx = (p1.x+p2.x)/2, my = (p1.y+p2.y)/2 + sag;
    const g = document.createElementNS(NS,'g');
    const shadow = document.createElementNS(NS,'path');
    shadow.setAttribute('class','string-shadow');
    shadow.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my+5}} ${{p2.x}} ${{p2.y}}`);
    g.appendChild(shadow);
    const path = document.createElementNS(NS,'path');
    path.setAttribute('class','string-visible');
    path.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
    path.setAttribute('stroke', color);
    g.appendChild(path);
    const hit = document.createElementNS(NS,'path');
    hit.setAttribute('class','string-hit');
    hit.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
    g.appendChild(hit);
    svg.appendChild(g);
    hit.addEventListener('mouseenter', ()=> showHighlight(p1,p2,mx,my,color,label));
    hit.addEventListener('mouseleave', hideHighlight);
  }});
}}
window.addEventListener('resize', draw);
draw();

let mode = null, dragEl=null, offX=0, offY=0, startX=0, startY=0, moved=false;
let panStartX=0, panStartY=0, panOrigX=0, panOrigY=0;

document.querySelectorAll('.node').forEach(n=>{{
  n.addEventListener('mousedown', e=>{{
    e.stopPropagation(); mode='node'; dragEl=n; moved=false;
    startX=e.clientX; startY=e.clientY;
    const r=n.getBoundingClientRect();
    offX=(e.clientX-r.left)/zoom; offY=(e.clientY-r.top)/zoom;
    n.style.transition='none';
  }});
}});
viewport.addEventListener('mousedown', e=>{{
  mode='pan'; panStartX=e.clientX; panStartY=e.clientY; panOrigX=panX; panOrigY=panY;
  viewport.classList.add('panning');
}});
window.addEventListener('mousemove', e=>{{
  if(mode==='node' && dragEl){{
    if(Math.abs(e.clientX-startX)>5 || Math.abs(e.clientY-startY)>5) moved=true;
    const b=board.getBoundingClientRect();
    dragEl.style.left = ((e.clientX-b.left)/zoom-offX)+'px';
    dragEl.style.top = ((e.clientY-b.top)/zoom-offY)+'px';
    draw();
  }} else if(mode==='pan'){{
    panX = panOrigX + (e.clientX-panStartX); panY = panOrigY + (e.clientY-panStartY);
    applyTransform();
  }}
}});
window.addEventListener('mouseup', ()=>{{
  if(mode==='node' && dragEl){{
    dragEl.style.transition='transform .15s ease';
    if(!moved){{
      const note = dragEl.dataset.note;
      const t = dragEl.querySelector('.title');
      const label = t ? t.textContent : '{html.escape(title_name)}';
      if(note){{ openNote(note, label); }} else {{ openNote(null, label); }}
    }}
  }}
  if(mode==='pan') viewport.classList.remove('panning');
  mode=null; dragEl=null;
}});

const panel = document.getElementById('note-panel');
const overlay = document.getElementById('overlay');
const frame = document.getElementById('note-frame');
const noteTitleBar = document.getElementById('note-title-bar');
const modeSideBtn = document.getElementById('mode-side-btn');
const modeCenterBtn = document.getElementById('mode-center-btn');
function setPanelMode(m){{
  panel.classList.remove('mode-side','mode-center'); panel.classList.add(m);
  modeSideBtn.classList.toggle('active', m==='mode-side');
  modeCenterBtn.classList.toggle('active', m==='mode-center');
}}
modeSideBtn.addEventListener('click', ()=>setPanelMode('mode-side'));
modeCenterBtn.addEventListener('click', ()=>setPanelMode('mode-center'));
function openNote(noteStem, label){{
  noteTitleBar.textContent = label;
  if(noteStem){{ frame.src = '../notes/' + encodeURIComponent(noteStem) + '.html'; }}
  else {{ frame.src = 'data:text/html;charset=utf-8,' + encodeURIComponent('<body style="font-family:sans-serif;padding:20px;color:#555">Todavia no hay nota para <b>'+label+'</b>.</body>'); }}
  panel.classList.add('open'); overlay.classList.add('open');
}}
function closeNote(){{ panel.classList.remove('open'); overlay.classList.remove('open'); }}
document.getElementById('note-close').addEventListener('click', closeNote);
overlay.addEventListener('click', closeNote);
</script>
</body>
</html>
'''
    return page

def build_all_submaps(submapas_dir, notes_dir, sprites_dir, out_dir):
    """Genera una pagina html por cada Submapas/*.canvas. Devuelve (ok, fallos)."""
    configure(notes_dir, sprites_dir, out_dir)
    os.makedirs(out_dir, exist_ok=True)
    ok, fail = 0, []
    if not os.path.isdir(submapas_dir):
        return ok, fail
    for fname in sorted(os.listdir(submapas_dir)):
        if not fname.endswith(".canvas"):
            continue
        stem = fname[:-7]
        slug = slugify(stem)
        try:
            page = build_submap(os.path.join(submapas_dir, fname), stem)
            if page is None:
                fail.append((stem, "sin nodos"))
                continue
            with open(os.path.join(out_dir, slug + ".html"), "w", encoding="utf-8") as f:
                f.write(page)
            ok += 1
        except Exception as ex:
            fail.append((stem, str(ex)))
    return ok, fail

