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
const BOARD_W = {board_w}, BOARD_H = {board_h};
const PAN_MARGIN = 400;

function clampPan(){{
  const vw = viewport.clientWidth, vh = viewport.clientHeight;
  const bw = BOARD_W * zoom, bh = BOARD_H * zoom;
  panX = Math.min(vw + PAN_MARGIN, Math.max(-bw - PAN_MARGIN, panX));
  panY = Math.min(vh + PAN_MARGIN, Math.max(-bh - PAN_MARGIN, panY));
}}

function applyTransform(){{ clampPan(); board.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{zoom}})`; viewport.style.backgroundPosition = `${{panX}}px ${{panY}}px`; viewport.style.backgroundSize = `auto, auto, auto, auto, auto, ${{300*zoom}}px ${{300*zoom}}px`; }}
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

