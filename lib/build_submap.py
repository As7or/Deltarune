import json, os, re, html, random, urllib.parse, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_prep import prepare_image
import mdconvert_linked
from mdconvert_linked import extract_callout_by_title

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

_sprite_index = None
def _build_sprite_index():
    global _sprite_index
    _sprite_index = {}
    if not SPRITES_DIR:
        return
    for dirpath, _, filenames in os.walk(SPRITES_DIR):
        rel_dir = os.path.relpath(dirpath, SPRITES_DIR)
        for fname in filenames:
            rel_path = fname if rel_dir == "." else f"{rel_dir}/{fname}"
            _sprite_index.setdefault(fname, rel_path)

def resolve_sprite_rel(file_field):
    """Los nodos 'file' del canvas guardan la ruta tal cual la escribio Obsidian
    (p.ej. 'Sprites/subcarpeta/archivo.gif'). Si esa ruta relativa a Sprites/
    existe tal cual, se usa; si no, se busca recursivamente por nombre de
    archivo (igual que el resolver de notas), para no perder subcarpetas."""
    rel = file_field.split("Sprites/", 1)[-1] if "Sprites/" in file_field else file_field.split("/")[-1]
    if SPRITES_DIR and os.path.exists(os.path.join(SPRITES_DIR, rel)):
        return rel
    global _sprite_index
    if _sprite_index is None:
        _build_sprite_index()
    basename = file_field.split("/")[-1]
    return _sprite_index.get(basename, basename)

def note_for_title(title, fallback_stem, is_center=False):
    if title in NOTE_STEMS:
        return slugify(title)
    base = re.sub(r"\s*\(.*?\)\s*", "", title).strip()
    if base in NOTE_STEMS:
        return slugify(base)
    # El fallback a la nota del propio personaje SOLO aplica al nodo centro
    # (por si su titulo no calca el nombre exacto de la nota) -- aplicarlo a
    # cualquier burbuja sin match convertiria cualquier teoria/relacion sin
    # nota propia en una falsa "conexion", abriendo la nota del personaje en
    # vez de mostrar el texto real de esa teoria.
    if is_center:
        return slugify(fallback_stem) if fallback_stem in NOTE_STEMS else None
    return None

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

def clean_text_full_html(t):
    """Igual que clean_text pero conservando los saltos de parrafo, para el
    popup tipo postit (a diferencia del pie de foto compacto de la tarjeta,
    que sigue colapsando todo a una linea)."""
    t = t.replace("\\n", "\n")
    parts = t.strip().split("\n", 1)
    body = parts[1].strip() if len(parts) > 1 else ""
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", body) if p.strip()]
    out = []
    for p in paras:
        esc = html.escape(p)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        out.append(f"<p>{esc}</p>")
    return "".join(out)

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

def layout_force_directed(items, edges, min_dist=340, iterations=600):
    """Aparta nodos superpuestos/comprimidos con un layout de fuerzas simple
    (repulsion entre todos los pares + atraccion entre conectados), para que
    los submapas exportados directamente de Obsidian —donde suelen quedar
    muy apelotonados— se vean distribuidos como en el corcho principal.
    Los nodos con 'anchor'=True (el centro) casi no se mueven, para que el
    submapa no rote respecto a su orientacion original."""
    import math, random as _random
    ids = [it["id"] for it in items]
    if len(ids) < 2:
        return
    pos = {it["id"]: [it["cx"], it["cy"]] for it in items}
    anchor = {it["id"]: it.get("anchor", False) for it in items}
    adj = {i: set() for i in ids}
    for e in edges:
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].add(e["to"])
            adj[e["to"]].add(e["from"])

    _random.seed(42)
    k = min_dist
    for step in range(iterations):
        temp = max(4, 40 * (1 - step / iterations))
        disp = {i: [0.0, 0.0] for i in ids}
        for i in range(len(ids)):
            a = ids[i]
            for j in range(i + 1, len(ids)):
                b = ids[j]
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                dist = math.hypot(dx, dy) or 0.01
                if dist < k * 3:
                    force = (k * k) / dist
                    fx, fy = dx / dist * force, dy / dist * force
                    disp[a][0] += fx; disp[a][1] += fy
                    disp[b][0] -= fx; disp[b][1] -= fy
        for a in ids:
            for b in adj[a]:
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                dist = math.hypot(dx, dy) or 0.01
                force = (dist * dist) / k * 0.06
                fx, fy = dx / dist * force, dy / dist * force
                disp[a][0] -= fx; disp[a][1] -= fy
        for a in ids:
            if anchor[a]:
                continue
            dlen = math.hypot(*disp[a]) or 0.01
            capped = min(dlen, temp * k * 0.12)
            pos[a][0] += disp[a][0] / dlen * capped
            pos[a][1] += disp[a][1] / dlen * capped

    for it in items:
        it["cx"], it["cy"] = pos[it["id"]][0], pos[it["id"]][1]

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
  #note-panel .postit-body{
    width:100%; height:calc(100% - 49px); overflow-y:auto; overflow-x:hidden; box-sizing:border-box;
    padding:26px 28px 30px; background:#fdf1b8; font-family:'Segoe UI', Tahoma, sans-serif;
  }
  #note-panel .postit-body p{ font-size:15px; line-height:1.6; color:#3a2f22; margin:0 0 14px; max-width:100%; }
  #note-panel .postit-body strong{ color:#2c2416; }
  #note-panel .postit-body .postit-note-link{
    display:inline-block; margin-top:6px; font-size:13px; color:#8a3a30;
    border-bottom:1px dotted #8a3a30; text-decoration:none;
  }
  /* Callouts anidados (p.ej. Ruta Rara dentro de una teoria) dentro del
     popup: una caja mas suave, sin repetir el marco postit completo. */
  #note-panel .postit-body .callout{
    background:rgba(255,255,255,0.45); border-radius:4px; padding:12px 14px; margin:10px 0 16px;
    box-shadow:none; transform:none !important;
  }
  #note-panel .postit-body .callout-title{ font-weight:bold; margin-bottom:6px; font-size:13px; text-transform:uppercase; letter-spacing:.03em; }
  /* Imagenes dentro del texto de teoria/conexion -- mismas reglas que las
     paginas de nota normales, para que no rompan el ancho del panel. */
  #note-panel .postit-body figure{ margin:12px 0; text-align:center; max-width:100%; }
  #note-panel .postit-body figcaption{ font-size:12px; font-style:italic; color:#6b5c38; margin-top:4px; }
  #note-panel .postit-body img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  #note-panel .postit-body .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:3px; box-shadow:0 2px 6px rgba(0,0,0,0.2); }
  #note-panel .postit-body .inline-img-alpha{ width:auto; max-width:210px; max-height:250px; margin:8px auto; box-shadow:none; background:none; }
  #note-panel .postit-body .inline-img-small{ width:auto; height:100px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  #note-panel .postit-body table.note-table{ width:100%; border-collapse:collapse; margin:10px 0; font-size:12.5px; }
  #note-panel .postit-body table.note-table th, #note-panel .postit-body table.note-table td{ border:1px solid #d8c078; padding:4px; text-align:center; }
  #overlay{ position:fixed; inset:0; background:rgba(0,0,0,0.35); opacity:0; pointer-events:none; transition:opacity .28s ease; z-index:90; }
  #overlay.open{ opacity:1; pointer-events:auto; }

/* ---- Lago: papel mojado ---- */
  .node-wet .wet-card{
    position:relative; overflow:hidden;
    background:
      radial-gradient(ellipse 65% 45% at 22% 20%, transparent 54%, rgba(122,92,52,.4) 58%, rgba(122,92,52,.14) 64%, transparent 70%),
      radial-gradient(ellipse 50% 35% at 82% 78%, transparent 48%, rgba(91,66,35,.35) 53%, transparent 62%),
      #fdfaf3;
    background-blend-mode: multiply, multiply, normal;
    clip-path: url(#deckle-card);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 22px rgba(90,64,32,.3);
  }
  .node-wet .crumple{ position:absolute; inset:-4px; background:#8a8a8a; filter:url(#crumpleTex);
    mix-blend-mode:overlay; opacity:.5; pointer-events:none; z-index:1; }
  .node-wet .creases{ position:absolute; inset:0; mix-blend-mode:overlay; opacity:.8; pointer-events:none; z-index:1;
    background:
      linear-gradient(112deg, transparent 27%, rgba(255,255,255,.4) 28%, rgba(0,0,0,.22) 29%, transparent 30%),
      linear-gradient(64deg, transparent 55%, rgba(255,255,255,.32) 56%, rgba(0,0,0,.18) 57%, transparent 58%),
      linear-gradient(146deg, transparent 74%, rgba(255,255,255,.3) 75%, rgba(0,0,0,.16) 76%, transparent 77%); }
  .node-wet .thumb{ position:relative; z-index:2; filter:sepia(.3) saturate(.8) contrast(.94) brightness(.94); }
  .node-wet .tag, .node-wet .title, .node-wet .summary{ position:relative; z-index:2; }

  /* ---- Shelter: placa de metal oxidada ---- */
  .node-rusted .rusted-card{
    position:relative; overflow:hidden; border-radius:3px;
    background:
      repeating-linear-gradient(90deg, rgba(0,0,0,.22) 0 2px, transparent 2px 26px),
      repeating-linear-gradient(0deg, rgba(0,0,0,.14) 0 2px, transparent 2px 26px),
      radial-gradient(ellipse 70% 40% at 15% 10%, rgba(200,100,40,.32) 0, transparent 55%),
      radial-gradient(ellipse 55% 40% at 85% 90%, rgba(160,70,25,.4) 0, transparent 60%),
      linear-gradient(160deg, #6b6058 0%, #3a332e 100%);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 18px rgba(0,0,0,.4);
  }
  .node-rusted .rust-texture{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:
      radial-gradient(circle 18px at 30% 70%, rgba(140,70,20,.35) 0, transparent 70%),
      radial-gradient(circle 24px at 75% 25%, rgba(120,55,15,.3) 0, transparent 70%); }
  .node-rusted .rivet{ position:absolute; width:7px; height:7px; border-radius:50%; z-index:2;
    background:radial-gradient(circle at 35% 30%, #d8c9a8, #7a6a50 65%); box-shadow:0 1px 2px rgba(0,0,0,.6); }
  .node-rusted .rivet-tl{ top:6px; left:6px; } .node-rusted .rivet-tr{ top:6px; right:6px; }
  .node-rusted .rivet-bl{ bottom:6px; left:6px; } .node-rusted .rivet-br{ bottom:6px; right:6px; }
  .node-rusted .tag{ position:relative; z-index:2; color:#e8c9a0; }
  .node-rusted .title{ position:relative; z-index:2; color:#f3ead6; }
  .node-rusted .summary{ position:relative; z-index:2; color:#d8c9b0; }

  /* ---- Cristal Oscuro: esquirla traslucida con brillo ---- */
  .node-crystal .crystal-card{
    position:relative; overflow:hidden;
    background:
      linear-gradient(135deg, rgba(120,110,220,.22), rgba(40,180,220,.14) 55%, rgba(20,20,40,.55));
    background-color:#1a1c34;
    clip-path:polygon(3% 0%, 97% 0%, 100% 10%, 100% 92%, 97% 100%, 3% 100%, 0% 90%, 0% 8%);
    box-shadow:0 0 14px rgba(110,120,240,.35), 3px 6px 10px rgba(0,0,0,.5);
  }
  .node-crystal .crystal-glow{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:radial-gradient(ellipse 60% 40% at 25% 15%, rgba(180,180,255,.25) 0, transparent 60%); }
  .node-crystal .tag{ position:relative; z-index:2; color:#a8b0e0; }
  .node-crystal .title{ position:relative; z-index:2; color:#e4ecff; text-shadow:0 0 6px rgba(140,160,255,.5); }
  .node-crystal .summary{ position:relative; z-index:2; color:#c8ccf0; }

  /* ---- Conexion Undertale: caja de dialogo clasica ---- */
  .node-undertale .undertale-card{
    background:#000; border-radius:0; box-shadow:3px 6px 10px var(--cork-shadow);
    border:3px solid #fff; padding-bottom:8px;
  }
  .node-undertale .tag{ color:#fff; font-family:'Courier New', monospace; }
  .node-undertale .title{ color:#fff; font-family:'Courier New', monospace; }
  .node-undertale .summary{ color:#e0e0e0; font-family:'Courier New', monospace; }

  /* ---- Fuentes Oscuras: agua ondulante ---- */
  .node-fountain .fountain-card{
    position:relative; overflow:hidden;
    background:
      radial-gradient(ellipse 90% 60% at 50% 0%, rgba(180,220,255,.2) 0, transparent 55%),
      linear-gradient(160deg, rgba(50,120,180,.4), rgba(10,30,55,.6)), #173a5e;
    border-radius:20px 20px 26px 26px/16px 16px 30px 30px;
    box-shadow:0 0 14px rgba(100,180,255,.4), 3px 6px 10px var(--cork-shadow);
  }
  .node-fountain .fountain-glow{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:radial-gradient(ellipse 60% 40% at 50% 20%, rgba(200,230,255,.3) 0, transparent 60%); }
  .node-fountain .tag{ position:relative; z-index:2; color:#a8d4ec; }
  .node-fountain .title{ position:relative; z-index:2; color:#eaf7ff; text-shadow:0 0 6px rgba(150,210,255,.6); }
  .node-fountain .summary{ position:relative; z-index:2; color:#d5ecfb; }

  /* ---- Profecía: pergamino enrollado ---- */
  .node-scroll .scroll{ position:relative; filter:drop-shadow(0 8px 12px rgba(0,0,0,.4)); }
  .node-scroll .roll{ position:relative; height:22px; width:100%; z-index:2;
    background:linear-gradient(180deg,#e8cf9a 0%,#c2a066 30%,#9c7c46 55%,#c2a066 80%,#8a6a3a 100%);
    border-radius:11px; box-shadow:inset 0 -2px 3px rgba(0,0,0,.35), inset 0 2px 2px rgba(255,255,255,.35); }
  .node-scroll .roll::before, .node-scroll .roll::after{
    content:""; position:absolute; top:50%; width:16px; height:16px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #ecdba8, #7a5c30 75%);
    box-shadow:0 2px 3px rgba(0,0,0,.5); transform:translateY(-50%); }
  .node-scroll .roll::before{ left:-8px; }
  .node-scroll .roll::after{ right:-8px; }
  .node-scroll .frizz{ display:none; }
  .node-scroll .sheet{ position:relative; overflow:hidden;
    background:linear-gradient(170deg,#f1e2b8,#dcc38c 55%,#c9ac78);
    margin:-2px 3px; padding:12px 10px 12px; text-align:center; border-radius:2px; }
  .node-scroll .sheet::before{ content:""; position:absolute; inset:0; pointer-events:none;
    background:
      radial-gradient(ellipse 130% 90% at 50% 50%, transparent 45%, rgba(120,88,32,.4) 100%),
      repeating-linear-gradient(90deg, rgba(120,88,32,.05) 0 1px, transparent 1px 7px); }
  .node-scroll .sheet::after{ content:""; position:absolute; inset:0; pointer-events:none;
    box-shadow:inset 0 0 0 1px rgba(120,88,32,.3); }
  .node-scroll .tear{ display:none; }
  .node-scroll .sheet .thumb{ position:relative; z-index:2; margin:0 auto 6px; filter:sepia(.2); background:transparent !important; }
  .node-scroll .sheet .title, .node-scroll .sheet .summary{ position:relative; z-index:2; }
'''

def build_submap(canvas_path, title_name):
    d = json.load(open(canvas_path, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    edges = d["edges"]

    parent_note_text = None
    parent_note_path = os.path.join(NOTES_DIR, title_name + ".md")
    if os.path.exists(parent_note_path):
        parent_note_text = open(parent_note_path, encoding="utf-8").read()

    text_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "text"}
    file_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "file"}
    used_file_ids = set()

    items = []
    for nid, n in text_nodes.items():
        title, body = clean_text(n.get("text", ""))
        full_html = clean_text_full_html(n.get("text", ""))
        cx = n["x"] + n["width"]/2
        cy = n["y"] + n["height"]/2
        img_node = file_nodes.get(nid + "-img")
        img_name = None
        if img_node:
            img_name = resolve_sprite_rel(img_node["file"])
            used_file_ids.add(nid + "-img")
        node_color = NODE_COLOR_MAP.get(n.get("color"), "#8a7a5c")
        note_stem = note_for_title(title, title_name, is_center=(nid == "center"))
        items.append({
            "id": nid, "title": title, "body": body, "full_html": full_html,
            "cx": cx, "cy": cy,
            "w": n["width"], "h": n["height"], "color": node_color,
            "img": img_name, "note": note_stem, "is_center": nid == "center",
            "anchor": nid == "center",
        })

    for nid, n in file_nodes.items():
        if nid in used_file_ids:
            continue
        cx = n["x"] + n["width"]/2
        cy = n["y"] + n["height"]/2
        items.append({
            "id": nid, "title": "", "body": "", "full_html": "", "cx": cx, "cy": cy,
            "w": n["width"], "h": n["height"], "color": "#8a7a5c",
            "img": resolve_sprite_rel(n["file"]), "note": None, "is_center": False,
            "anchor": False,
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

    # Los nodos "-img" (imagen asociada a una burbuja de texto) no participan
    # directamente del layout de fuerzas -- no tienen arista propia, asi que
    # el algoritmo los alejaria de su burbuja al no haber atraccion entre
    # ambos. En su lugar, se guarda su posicion relativa ORIGINAL respecto al
    # nodo de texto al que pertenecen, y tras el layout se les aplica ese
    # mismo offset sobre la posicion ya reordenada del texto -- asi la imagen
    # se mueve pegada a su burbuja, sin enredar hilos con el resto.
    by_id = {it["id"]: it for it in items}
    paired_offset = {}
    for it in items:
        if it["id"] in used_file_ids:
            text_id = it["id"][:-4]  # quita el sufijo "-img"
            parent = by_id.get(text_id)
            if parent:
                paired_offset[it["id"]] = (it["cx"] - parent["cx"], it["cy"] - parent["cy"], text_id)

    layout_items = [it for it in items if it["id"] not in paired_offset]
    layout_force_directed(layout_items, links)

    for it in items:
        if it["id"] in paired_offset:
            dx, dy, text_id = paired_offset[it["id"]]
            parent = by_id[text_id]
            it["cx"] = parent["cx"] + dx
            it["cy"] = parent["cy"] + dy

    SCALE = 0.42
    xs = [it["cx"] for it in items]; ys = [it["cy"] for it in items]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    PAD = 180
    board_w = int((maxx-minx)*SCALE + PAD*2) or 800
    board_h = int((maxy-miny)*SCALE + PAD*2) or 600
    for it in items:
        it["px"] = (it["cx"] - minx) * SCALE + PAD
        it["py"] = (it["cy"] - miny) * SCALE + PAD

    # Nodos con el mismo tema visual especial que sus tarjetas en el corcho
    # principal (Shelter, Lago, Cristal Oscuro, Conexion Undertale, Profecia,
    # Fuentes Oscuras) -- se detectan por titulo exacto de la burbuja/centro.
    SPECIAL_THEMES = {"Shelter", "Lake", "Cristal Oscuro", "Conexión Undertale", "Profecía", "Fuentes Oscuras"}

    node_html = []
    content_map = {}
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
        thumb_h = 150 if is_center else 100
        theme = it["title"] if it["title"] in SPECIAL_THEMES else None

        # Burbuja de CONEXION (su titulo coincide con una nota real, p.ej.
        # "Susie" dentro del submapa de Noelle) -> se comporta igual que el
        # centro: abre la nota completa real, nunca un resumen.
        # Burbuja de TEORIA (sin nota propia) -> se busca su callout exacto
        # dentro de la nota del propio personaje y se muestra COMPLETO (con
        # imagenes incluidas), no el texto abreviado que vive en el .canvas.
        opens_full_note = is_center or bool(it["note"])
        if it["title"] and not opens_full_note:
            extracted = None
            if parent_note_text:
                try:
                    extracted = extract_callout_by_title(parent_note_text, it["title"], sprites_prefix="../Sprites/")
                except Exception:
                    extracted = None
            content_map[nid] = {"title": it["title"],
                                 "html": extracted or it["full_html"] or f"<p>{body_html}</p>",
                                 "note": note_attr}

        opennote_flag = "1" if opens_full_note else "0"
        pin = '<div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>'
        base_attrs = f'data-id="{nid}" data-note="{note_attr}" data-center="{opennote_flag}"'
        pos_style = f'left:{x-width/2:.0f}px; top:{y-(160 if is_center else 105):.0f}px; width:{width}px; transform:rotate({rot:.1f}deg);'

        if theme == "Profecía":
            node_html.append(f'''
  <div class="node node-scroll" {base_attrs} style="{pos_style}">
    {pin}
    <div class="scroll">
      <div class="roll roll-top"></div>
      <div class="sheet">
        <div class="{thumb_class} thumb" style="height:{max(60,thumb_h*0.6):.0f}px;">{img_tag}</div>
        <div class="title">{title_html}</div>
      </div>
      <div class="roll roll-bottom"></div>
    </div>
  </div>''')
        elif theme == "Lake":
            node_html.append(f'''
  <div class="node node-wet" {base_attrs} style="{pos_style}">
    {pin}
    <div class="card wet-card" style="border-top:5px solid {it['color']};">
      <div class="crumple"></div><div class="creases"></div>
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      <div class="title">{title_html}</div>
    </div>
  </div>''')
        elif theme == "Shelter":
            node_html.append(f'''
  <div class="node node-rusted" {base_attrs} style="{pos_style}">
    {pin}
    <div class="card rusted-card" style="border-top:5px solid {it['color']};">
      <div class="rust-texture"></div>
      <div class="rivet rivet-tl"></div><div class="rivet rivet-tr"></div><div class="rivet rivet-bl"></div><div class="rivet rivet-br"></div>
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      <div class="title">{title_html}</div>
    </div>
  </div>''')
        elif theme == "Cristal Oscuro":
            node_html.append(f'''
  <div class="node node-crystal" {base_attrs} style="{pos_style}">
    {pin}
    <div class="card crystal-card" style="border-top:5px solid {it['color']};">
      <div class="crystal-glow"></div>
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      <div class="title">{title_html}</div>
    </div>
  </div>''')
        elif theme == "Conexión Undertale":
            node_html.append(f'''
  <div class="node node-undertale" {base_attrs} style="{pos_style}">
    {pin}
    <div class="card undertale-card" style="border-top:5px solid {it['color']};">
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      <div class="title">{title_html}</div>
    </div>
  </div>''')
        elif theme == "Fuentes Oscuras":
            node_html.append(f'''
  <div class="node node-fountain" {base_attrs} style="{pos_style}">
    {pin}
    <div class="card fountain-card" style="border-top:5px solid {it['color']};">
      <div class="fountain-glow"></div>
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      <div class="title">{title_html}</div>
    </div>
  </div>''')
        else:
            cardclass = "card center-card" if is_center else "card"
            node_html.append(f'''
  <div class="node{" node-center" if is_center else ""}" {base_attrs} style="{pos_style}">
    {pin}
    <div class="{cardclass}" style="border-top:5px solid {it['color']};">
      <div class="{thumb_class}" style="height:{thumb_h}px;">{img_tag}</div>
      {f'<div class="title">{title_html}</div>' if title_html else ""}
      {f'<div class="caption">{body_html}</div>' if body_html else ""}
    </div>
  </div>''')

    nodes_str = "\n".join(node_html)
    links_js = ",\n  ".join([f"['{l['from']}','{l['to']}','{l['color']}','{html.escape(l['label'])}']" for l in links])
    content_json = json.dumps(content_map, ensure_ascii=False)

    page = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Submapa — {html.escape(title_name)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute">
<defs>
<filter id="crumpleTex" x="-20%" y="-20%" width="140%" height="140%">
  <feTurbulence type="turbulence" baseFrequency="0.006 0.03" numOctaves="3" seed="11" result="n"/>
  <feDiffuseLighting in="n" surfaceScale="2.6" diffuseConstant="1.15" lighting-color="#ffffff" result="light">
    <feDistantLight azimuth="235" elevation="52"/>
  </feDiffuseLighting>
</filter>
<clipPath id="deckle-card" clipPathUnits="objectBoundingBox">
  <path d="M0.01,0.05 C0.03,0.01 0.09,0.00 0.15,0.02 C0.23,0.04 0.29,0.00 0.37,0.02
    C0.46,0.04 0.52,0.00 0.60,0.02 C0.69,0.04 0.76,0.00 0.84,0.02
    C0.91,0.04 0.97,0.01 0.99,0.06 C1.01,0.12 0.985,0.18 0.995,0.24
    C1.005,0.31 0.98,0.37 0.995,0.44 C1.01,0.51 0.985,0.57 0.998,0.64
    C1.01,0.71 0.98,0.77 0.995,0.84 C1.005,0.90 0.97,0.95 0.93,0.98
    C0.87,1.02 0.80,0.985 0.72,0.995 C0.64,1.005 0.56,0.98 0.48,0.995
    C0.40,1.01 0.32,0.985 0.24,0.995 C0.16,1.005 0.09,0.98 0.05,0.94
    C0.01,0.90 0.025,0.84 0.01,0.77 C-0.005,0.70 0.02,0.63 0.005,0.56
    C-0.005,0.49 0.02,0.42 0.005,0.35 C-0.005,0.28 0.02,0.21 0.005,0.14
    C-0.005,0.10 0.005,0.08 0.01,0.05 Z" />
</clipPath>
</defs>
</svg>
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
  <div id="postit-body" class="postit-body" style="display:none;"></div>
</div>
<script>
const NODE_CONTENT = {content_json};
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
  applyTransform(); draw();
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
      const nid = dragEl.dataset.id;
      const isCenter = dragEl.dataset.center === '1';
      const note = dragEl.dataset.note;
      const t = dragEl.querySelector('.title');
      const label = t ? t.textContent : '{html.escape(title_name)}';
      if(isCenter){{
        if(note){{ openNote(note, label); }} else {{ openNote(null, label); }}
      }} else if(NODE_CONTENT[nid]){{
        openPostit(NODE_CONTENT[nid]);
      }} else if(note){{
        openNote(note, label);
      }}
    }}
  }}
  if(mode==='pan') viewport.classList.remove('panning');
  mode=null; dragEl=null;
}});

const panel = document.getElementById('note-panel');
const overlay = document.getElementById('overlay');
const frame = document.getElementById('note-frame');
const postitBody = document.getElementById('postit-body');
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
  frame.style.display = 'block';
  postitBody.style.display = 'none';
  if(noteStem){{ frame.src = '../notes/' + encodeURIComponent(noteStem) + '.html'; }}
  else {{ frame.src = 'data:text/html;charset=utf-8,' + encodeURIComponent('<body style="font-family:sans-serif;padding:20px;color:#555">Todavia no hay nota para <b>'+label+'</b>.</body>'); }}
  panel.classList.add('open'); overlay.classList.add('open');
}}
function openPostit(content){{
  noteTitleBar.textContent = content.title;
  frame.style.display = 'none';
  frame.src = 'about:blank';
  postitBody.style.display = 'block';
  let extra = '';
  if(content.note){{
    extra = '<a class="postit-note-link" href="../notes/' + encodeURIComponent(content.note) + '.html" target="_blank">Ver la nota completa de "' + content.title + '" →</a>';
  }}
  postitBody.innerHTML = content.html + extra;
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

