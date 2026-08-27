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
      linear-gradient(rgba(15,12,8,0.4), rgba(15,12,8,0.4)),
      radial-gradient(circle at 15% 20%, rgba(255,255,255,0.045) 0, transparent 40%),
      radial-gradient(circle at 80% 10%, rgba(0,0,0,0.12) 0, transparent 35%),
      radial-gradient(circle at 60% 75%, rgba(0,0,0,0.14) 0, transparent 45%),
      radial-gradient(circle at 30% 85%, rgba(255,255,255,0.035) 0, transparent 40%),
      url("data:image/jpeg;base64,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");
    background-size: auto, auto, auto, auto, auto, 300px 300px;
  }
  #viewport.panning{ cursor:grabbing; }
  /* --- fondos tematicos para el submapa cuyo nodo central es una de las
     6 notas con diseno especial, a juego con la pagina de esa nota --- */
  #viewport.viewport-rusted{
    background-color:#2b1f16;
    background-image:
      radial-gradient(ellipse at 12% 15%, rgba(200,90,30,0.28) 0, transparent 38%),
      radial-gradient(ellipse at 88% 10%, rgba(160,55,15,0.26) 0, transparent 36%),
      radial-gradient(ellipse at 65% 40%, rgba(120,40,10,0.2) 0, transparent 40%),
      radial-gradient(ellipse at 20% 70%, rgba(190,80,25,0.22) 0, transparent 40%),
      radial-gradient(ellipse at 80% 85%, rgba(150,50,15,0.24) 0, transparent 42%);
  }
  #viewport.viewport-wet{
    background-color:#e8e0c4;
    background-image:
      linear-gradient(112deg, transparent 30%, rgba(255,255,255,0.4) 31%, rgba(90,75,30,0.16) 32%, transparent 34%),
      linear-gradient(75deg, transparent 48%, rgba(255,255,255,0.35) 49%, rgba(90,75,30,0.14) 50%, transparent 52%),
      radial-gradient(circle at 15% 20%, transparent 55%, rgba(196,168,90,0.3) 58%, transparent 66%),
      radial-gradient(circle at 85% 15%, transparent 50%, rgba(196,168,90,0.26) 53%, transparent 60%),
      radial-gradient(circle at 75% 68%, transparent 52%, rgba(196,168,90,0.3) 55%, transparent 64%),
      radial-gradient(circle at 25% 78%, rgba(255,255,255,0.4) 0%, transparent 40%);
  }
  #viewport.viewport-crystal{
    background-color:#140e26;
    background-image:
      radial-gradient(ellipse at 15% 15%, rgba(120,90,220,0.22) 0, transparent 42%),
      radial-gradient(ellipse at 85% 25%, rgba(70,180,220,0.2) 0, transparent 40%),
      radial-gradient(ellipse at 50% 90%, rgba(120,90,220,0.18) 0, transparent 45%);
  }
  #viewport.viewport-undertale{ background-color:#000000; background-image:none; }
  #viewport.viewport-fountain{
    background-color:#16303d;
    background-image:
      radial-gradient(ellipse at 20% 10%, rgba(90,150,190,0.32) 0, transparent 40%),
      radial-gradient(ellipse at 80% 20%, rgba(60,120,160,0.28) 0, transparent 38%),
      radial-gradient(ellipse at 30% 55%, rgba(70,130,170,0.26) 0, transparent 42%),
      radial-gradient(ellipse at 75% 65%, rgba(50,100,140,0.28) 0, transparent 40%),
      radial-gradient(ellipse at 45% 90%, rgba(80,140,180,0.24) 0, transparent 42%);
  }
  #viewport.viewport-parchment{
    background-color:#c9ad74;
    background-image:
      radial-gradient(ellipse at 18% 12%, rgba(120,90,40,0.18) 0, transparent 45%),
      radial-gradient(ellipse at 82% 28%, rgba(90,60,20,0.15) 0, transparent 42%),
      radial-gradient(ellipse at 55% 92%, rgba(70,45,15,0.2) 0, transparent 50%);
  }
  #viewport.viewport-gaster{
    background-color:#141412;
    background-image:
      radial-gradient(ellipse at 20% 10%, rgba(255,255,255,0.03) 0, transparent 40%),
      radial-gradient(ellipse at 80% 15%, rgba(0,0,0,0.35) 0, transparent 40%),
      radial-gradient(ellipse at 50% 90%, rgba(0,0,0,0.4) 0, transparent 50%);
  }
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
    position:relative;
    width:100%; height:calc(100% - 49px); overflow-y:auto; overflow-x:hidden; box-sizing:border-box;
    padding:30px 30px 34px;
    background:
      radial-gradient(ellipse at 25% 15%, rgba(255,255,255,0.25) 0, transparent 40%),
      linear-gradient(135deg, #fdf1b8 0%, #fbe89a 100%);
    font-family:'Segoe UI', Tahoma, sans-serif;
    box-shadow:inset 0 -18px 26px -20px rgba(80,60,10,0.18);
  }
  #note-panel .postit-body::before{
    content:""; position:absolute; top:0; right:0; width:0; height:0;
    border-style:solid; border-width:0 22px 22px 0;
    border-color:transparent rgba(120,90,10,0.18) transparent transparent;
  }
  #note-panel .postit-ref-img{
    margin:0 0 18px; text-align:center;
  }
  #note-panel .postit-ref-img img{
    max-width:100%; max-height:220px; border-radius:2px;
    box-shadow:2px 6px 14px rgba(60,45,10,0.35);
    border:4px solid #fffdf6;
    transform:rotate(-1.1deg);
  }
  #note-panel .postit-body p{ font-size:15px; line-height:1.6; color:#3a2f22; margin:0 0 14px; max-width:100%; }
  #note-panel .postit-body strong{ color:#2c2416; }
  #note-panel .postit-body .postit-note-link{
    display:inline-block; margin-top:6px; font-size:13px; color:#8a3a30;
    border-bottom:1px dotted #8a3a30; text-decoration:none;
  }
  /* Callouts anidados (p.ej. Ruta Rara dentro de una teoria) dentro del
     popup: otra notita mas pequena encima, con su propia sombra de papel. */
  #note-panel .postit-body .callout{
    position:relative; background:#fffdf3; border-radius:2px; padding:12px 14px; margin:14px 4px 18px;
    box-shadow:1px 4px 10px rgba(60,45,10,0.28); transform:rotate(0.6deg) !important;
  }
  #note-panel .postit-body .callout-title{ font-weight:bold; margin-bottom:6px; font-size:13px; text-transform:uppercase; letter-spacing:.03em; color:#5a4520; }
  /* Callout especial "[!prophecy]" dentro del popup del submapa: mismo
     pergamino abierto que usa la nota completa (note_page_template.py,
     bloque .callout.prophecy-scroll) -- sin este bloque, el popup del
     submapa mostraba la version generica de callout (notita amarilla
     simple) en vez del pergamino, aunque la nota real si lo tuviera. */
  #note-panel .postit-body .callout.prophecy-scroll{
    position:relative;
    background:
      radial-gradient(ellipse at 50% 45%, #f3e3b2 0%, #ecd89e 30%, #d8b678 58%, #a97b46 82%, #6e4526 100%),
      radial-gradient(ellipse at 30% 35%, rgba(255,240,200,0.25) 0, transparent 45%),
      linear-gradient(124deg, transparent 30%, rgba(90,60,20,0.08) 31%, transparent 34%),
      linear-gradient(38deg, transparent 55%, rgba(90,60,20,0.07) 56%, transparent 60%),
      linear-gradient(160deg, transparent 15%, rgba(120,85,35,0.06) 16%, transparent 20%),
      repeating-linear-gradient(91deg, rgba(90,60,20,0.05) 0px, transparent 2px, transparent 5px),
      repeating-linear-gradient(4deg, rgba(90,60,20,0.04) 0px, transparent 3px, transparent 7px);
    padding:28px 20px 30px;
    margin:22px 6px 28px;
    border-left:8px solid #8a6a3a;
    box-shadow:0 6px 18px rgba(40,25,5,0.4), inset 0 0 60px rgba(90,55,25,0.4);
    font-family:'Palatino Linotype', Georgia, serif;
    transform:none !important;
    clip-path: polygon(
      0% 2%, 7% 0%, 15% 1.5%, 23% 0.5%, 31% 2%, 39% 0%, 47% 1.5%, 55% 0.5%, 63% 2%, 71% 0%, 79% 1.5%, 87% 0.5%, 94% 1.5%, 100% 0.5%,
      99% 8%, 100% 15%, 98.5% 23%, 100% 31%, 99% 39%, 100% 47%, 98.5% 55%, 100% 63%, 99% 71%, 100% 79%, 98.5% 87%, 100% 94%, 99.5% 100%,
      92% 99%, 84% 100%, 76% 98.5%, 68% 100%, 60% 99%, 52% 100%, 44% 98.5%, 36% 100%, 28% 99%, 20% 100%, 12% 98.5%, 4% 100%, 0% 99%,
      1% 92%, 0% 84%, 1.5% 76%, 0% 68%, 1% 60%, 0% 52%, 1.5% 44%, 0% 36%, 1% 28%, 0% 20%, 1.5% 12%, 0% 6%
    );
  }
  #note-panel .postit-body .callout.prophecy-scroll::before, #note-panel .postit-body .callout.prophecy-scroll::after{
    content:""; position:absolute; left:-2px; right:-2px; height:22px; z-index:1;
    background:
      repeating-linear-gradient(135deg, transparent 0 7px, #5a3416 7px 8.5px),
      repeating-linear-gradient(45deg, transparent 0 7px, #5a3416 7px 8.5px),
      linear-gradient(180deg, #caa267, #8a6236 45%, #6e4a26 55%, #a37e46);
    box-shadow:0 3px 8px rgba(30,18,6,0.5);
  }
  #note-panel .postit-body .callout.prophecy-scroll::before{ top:-11px; }
  #note-panel .postit-body .callout.prophecy-scroll::after{ bottom:-11px; transform:scaleY(-1); }
  #note-panel .postit-body .prophecy-scroll .callout-title{
    font-weight:bold; margin-bottom:8px; font-size:13.5px; color:#4a3418 !important;
    text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid rgba(90,60,20,.35); padding-bottom:5px;
    position:relative; z-index:2; font-family:'Palatino Linotype', Georgia, serif;
  }
  #note-panel .postit-body .prophecy-scroll p{ margin:6px 0; font-size:14.5px; line-height:1.55; color:#3f3120 !important; position:relative; z-index:2; }
  #note-panel .postit-body .prophecy-scroll img{
    width:auto; max-width:85%; height:auto; display:block; margin:10px auto;
    border-radius:2px; box-shadow:0 2px 8px rgba(40,25,5,0.35); border:none; position:relative; z-index:2;
  }
  #note-panel .postit-body .prophecy-scroll .wikilink, #note-panel .postit-body .prophecy-scroll .postit-note-link{
    color:#7a2e22 !important; border-bottom:1px dotted #7a2e22 !important;
  }
  /* Imagenes dentro del texto de teoria/conexion -- mismas reglas que las
     paginas de nota normales, para que no rompan el ancho del panel. */
  #note-panel .postit-body figure{ margin:12px 0; text-align:center; max-width:100%; }
  #note-panel .postit-body figcaption{ font-size:12px; font-style:italic; color:#6b5c38; margin-top:4px; }
  #note-panel .postit-body img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  #note-panel .postit-body .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:3px; box-shadow:1px 4px 10px rgba(60,45,10,0.25); }
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

  /* ---- Shelter: placa de metal oxidada y rasgada ---- */
  .node-rusted .rusted-card{
    position:relative; overflow:hidden; border-radius:3px; border:2px solid #7a6a52;
    background:
      repeating-linear-gradient(90deg, rgba(0,0,0,.22) 0 2px, transparent 2px 26px),
      repeating-linear-gradient(0deg, rgba(0,0,0,.14) 0 2px, transparent 2px 26px),
      radial-gradient(ellipse 70% 40% at 15% 10%, rgba(200,100,40,.32) 0, transparent 55%),
      radial-gradient(ellipse 55% 40% at 85% 90%, rgba(160,70,25,.4) 0, transparent 60%),
      linear-gradient(160deg, #6b6058 0%, #3a332e 100%);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 18px rgba(0,0,0,.4), inset 0 0 0 1px rgba(0,0,0,.4);
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

  /* ---- Cristal Oscuro: esquirla traslucida con brillo, imagen completa sin recortes ---- */
  .node-crystal .crystal-card{
    position:relative; overflow:hidden;
    background:
      linear-gradient(135deg, rgba(120,110,220,.22), rgba(40,180,220,.14) 55%, rgba(20,20,40,.55));
    background-color:#1a1c34;
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

  /* ---- Gaster: posit viejo, gris y polvoriento, con el borde medio rasgado ---- */
  .node-gaster .gaster-card{
    position:relative; overflow:hidden; border-radius:2px;
    background:linear-gradient(155deg, #cfcfc6 0%, #adada2 55%, #949488 100%);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 16px rgba(0,0,0,.18);
    clip-path: polygon(
      0% 3%, 5% 0%, 13% 2%, 20% 0%, 29% 2.5%, 37% 0%, 46% 2%, 55% 0%, 64% 2.5%, 73% 0%, 82% 2%, 91% 0%, 97% 2%, 100% 0.5%,
      98% 16%, 100% 28%, 97% 40%, 100% 54%, 98% 66%, 100% 80%, 96% 92%, 100% 100%,
      86% 97%, 72% 100%, 58% 97%, 44% 100%, 30% 97%, 16% 100%, 4% 96%,
      2% 82%, 0% 68%, 2.5% 54%, 0% 40%, 2% 26%, 0% 13%
    );
  }
  .node-gaster .gaster-dust{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:
      radial-gradient(circle 1px at 20% 25%, rgba(0,0,0,.4) 0, transparent 100%),
      radial-gradient(circle 1px at 65% 60%, rgba(0,0,0,.35) 0, transparent 100%),
      radial-gradient(circle 1.2px at 40% 80%, rgba(0,0,0,.3) 0, transparent 100%),
      radial-gradient(circle 1px at 85% 20%, rgba(0,0,0,.35) 0, transparent 100%),
      radial-gradient(ellipse 40% 30% at 80% 85%, rgba(60,55,55,.14) 0%, transparent 70%); }
  .node-gaster .thumb{ position:relative; z-index:2; filter:grayscale(1) contrast(1.05); }
  .node-gaster .title{ position:relative; z-index:2; color:#2c2c24; }

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

SUBMAP_UI = {
    "es": {
        "submap_title_prefix": "Submapa",
        "back_link": "← Corcho principal",
        "zoomhint": "Rueda = zoom &middot; arrastra el fondo para moverte &middot; clic en una nota = abrir su pagina",
        "note_title_default": "Nota",
        "mode_side_title": "Ver al lado",
        "mode_side_label": "Lateral",
        "mode_center_title": "Ver centrado, mas grande",
        "mode_center_label": "Centrado",
        "note_close_label": "Cerrar X",
        "no_note_prefix": "Todavia no hay nota para",
        "view_full_note_prefix": "Ver la nota completa de",
        "no_image": "sin imagen",
    },
    "en": {
        "submap_title_prefix": "Submap",
        "back_link": "← Main Corkboard",
        "zoomhint": "Wheel = zoom &middot; drag the background to move &middot; click a note to open its page",
        "note_title_default": "Note",
        "mode_side_title": "View beside",
        "mode_side_label": "Side",
        "mode_center_title": "View centered, larger",
        "mode_center_label": "Center",
        "note_close_label": "Close X",
        # OJO: este valor se inyecta crudo dentro de un string JS delimitado
        # con comillas simples (ver mas abajo, linea del "no_note_prefix").
        # Un apostrofo aqui ("There's") rompe esa comilla simple y tira
        # abajo TODO el <script> de la pagina -- mismo bug que ya paso una
        # vez en board_template.py. Nunca usar apostrofos en este valor.
        "no_note_prefix": "There is no note yet for",
        "view_full_note_prefix": "View the full note for",
        "no_image": "no image",
    },
}


def build_submap(canvas_path, title_name, lang="es"):
    ui = SUBMAP_UI.get(lang, SUBMAP_UI["es"])
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
    SPECIAL_THEMES = {"Shelter", "Lake", "Cristal Oscuro", "Conexión Undertale", "Profecía", "Fuentes Oscuras", "Gaster"}
    THEME_VIEWPORT_CLASS = {
        "Shelter": "viewport-rusted", "Lake": "viewport-wet", "Cristal Oscuro": "viewport-crystal",
        "Conexión Undertale": "viewport-undertale", "Fuentes Oscuras": "viewport-fountain",
        "Profecía": "viewport-parchment", "Gaster": "viewport-gaster",
    }
    # Si el propio centro del submapa es una de esas 6 notas especiales, todo
    # el fondo del sub-corcho cambia a juego (no solo la tarjeta central).
    center_title_raw = next((it["title"] for it in items if it["is_center"]), "")
    # El titulo del centro suele venir como "Nombre — subtitulo poetico"; para
    # detectar el tema especial hace falta comparar solo la parte "Nombre",
    # sin tocar el titulo completo que se sigue mostrando tal cual en la tarjeta.
    center_title = re.split(r"\s+[—–-]\s+", center_title_raw)[0].strip()
    viewport_extra_class = THEME_VIEWPORT_CLASS.get(center_title, "")

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
            img_tag = f'<img src="data:{mime};base64,{b64}" alt="">' if b64 else f'<div class="noimg"><i>{ui["no_image"]}</i></div>'
        else:
            img_tag = f'<div class="noimg"><i>{ui["no_image"]}</i></div>'

        thumb_class = "thumb thumb-dark" if is_dark else "thumb"
        title_html = html.escape(it["title"]) if it["title"] else ""
        body_html = html.escape(it["body"]) if it["body"] else ""
        note_attr = it["note"] or ""
        thumb_h = 150 if is_center else 100
        title_base = re.split(r"\s+[—–-]\s+", it["title"])[0].strip() if it["title"] else ""
        theme = title_base if title_base in SPECIAL_THEMES else None

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
            ref_img_html = ""
            if it["img"]:
                popup_path = os.path.join(SPRITES_DIR, it["img"])
                pmime, pb64 = prepare_image(popup_path, maxw=340)
                if pb64:
                    ref_img_html = f'<div class="postit-ref-img"><img src="data:{pmime};base64,{pb64}" alt=""></div>'
            content_map[nid] = {"title": it["title"],
                                 "html": ref_img_html + (extracted or it["full_html"] or f"<p>{body_html}</p>"),
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
        elif theme == "Gaster":
            node_html.append(f'''
  <div class="node node-gaster" {base_attrs} style="{pos_style}">
    {pin}
    <div class="card gaster-card" style="border-top:5px solid {it['color']};">
      <div class="gaster-dust"></div>
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
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{ui["submap_title_prefix"]} — {html.escape(title_name)}</title>
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
<a id="back-link" href="../corcho-principal.html">&larr; {ui["back_link"].lstrip("← ")}</a>
<div id="viewport" class="{viewport_extra_class}">
  <div id="board" style="width:{board_w}px; height:{board_h}px;">
    <svg id="strings"></svg>
{nodes_str}
    <svg id="highlight-svg"></svg>
  </div>
</div>
<div id="zoomhint">{ui["zoomhint"]}</div>
<div id="overlay"></div>
<div id="note-panel" class="mode-side">
  <div class="note-header">
    <span id="note-title-bar">{ui["note_title_default"]}</span>
    <div class="btns">
      <button id="mode-side-btn" class="active" title="{ui["mode_side_title"]}">{ui["mode_side_label"]}</button>
      <button id="mode-center-btn" title="{ui["mode_center_title"]}">{ui["mode_center_label"]}</button>
      <button id="note-close">{ui["note_close_label"]}</button>
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

function applyTransform(){{ board.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{zoom}})`; viewport.style.backgroundPosition = `${{panX}}px ${{panY}}px`; }}
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
  else {{ frame.src = 'data:text/html;charset=utf-8,' + encodeURIComponent('<body style="font-family:sans-serif;padding:20px;color:#555">{ui["no_note_prefix"]} <b>'+label+'</b>.</body>'); }}
  panel.classList.add('open'); overlay.classList.add('open');
}}
function openPostit(content){{
  noteTitleBar.textContent = content.title;
  frame.style.display = 'none';
  frame.src = 'about:blank';
  postitBody.style.display = 'block';
  let extra = '';
  if(content.note){{
    extra = '<a class="postit-note-link" href="../notes/' + encodeURIComponent(content.note) + '.html" target="_blank">{ui["view_full_note_prefix"]} "' + content.title + '" →</a>';
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

def build_all_submaps(submapas_dir, notes_dir, sprites_dir, out_dir, lang="es"):
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
            page = build_submap(os.path.join(submapas_dir, fname), stem, lang=lang)
            if page is None:
                fail.append((stem, "sin nodos"))
                continue
            with open(os.path.join(out_dir, slug + ".html"), "w", encoding="utf-8") as f:
                f.write(page)
            ok += 1
        except Exception as ex:
            fail.append((stem, str(ex)))
    return ok, fail

