"""
Lee el canvas principal (00 Corcho Principal.canvas) y genera:
  - los datos de cada personaje/lugar/tema (items)
  - las conexiones entre ellos (edges)
  - el HTML de las tarjetas del corcho, listo para insertar en la plantilla
"""
import json, os, re, html, random, math, urllib.parse, unicodedata, subprocess, tempfile

def slugify(name):
    nfkd = unicodedata.normalize('NFKD', name)
    return nfkd.encode('ascii', 'ignore').decode('ascii') or name

# Tamano por encima del cual una miniatura del corcho se comprime: las tarjetas
# se muestran a ~150px de ancho, asi que no tiene sentido cargar un gif/imagen
# de varios MB en su tamano original solo para eso (era una de las causas de
# que el corcho fuera lento, sobre todo al hacer zoom con muchas tarjetas).
THUMB_SIZE_LIMIT = 400 * 1024  # bytes
_thumb_cache = {}

def make_board_thumb(img_name, sprites_dir, thumbs_out_dir, max_w=220):
    """Si img_name pesa mas de THUMB_SIZE_LIMIT, genera una version reducida
    dentro de thumbs_out_dir y devuelve su ruta relativa a partir de 'Sprites/'.
    Si no hace falta comprimir (o falla), devuelve la ruta original."""
    original_rel = img_name
    if img_name in _thumb_cache:
        return _thumb_cache[img_name]

    src_path = os.path.join(sprites_dir, img_name)
    try:
        size = os.path.getsize(src_path)
    except OSError:
        _thumb_cache[img_name] = original_rel
        return original_rel

    if size <= THUMB_SIZE_LIMIT:
        _thumb_cache[img_name] = original_rel
        return original_rel

    ext = os.path.splitext(img_name)[1].lower()
    os.makedirs(thumbs_out_dir, exist_ok=True)
    out_name = img_name
    out_path = os.path.join(thumbs_out_dir, out_name)

    try:
        if ext == ".gif":
            cmd = [
                "ffmpeg", "-y", "-i", src_path, "-t", "4",
                "-vf", f"fps=10,scale={max_w}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=64[p];[s1][p]paletteuse",
                out_path, "-loglevel", "error",
            ]
            subprocess.run(cmd, check=True)
        else:
            from PIL import Image
            im = Image.open(src_path)
            im = im.convert("RGBA")
            w, h = im.size
            if w > max_w:
                im = im.resize((max_w, int(h * max_w / w)), Image.LANCZOS)
            # normalizamos siempre a PNG para las miniaturas estaticas: mas
            # predecible que reusar la extension original (algunos .webp no
            # comprimen bien vueltos a guardar como .webp con Pillow por defecto)
            out_name = os.path.splitext(img_name)[0] + "_thumb.png"
            out_path = os.path.join(thumbs_out_dir, out_name)
            im.save(out_path, "PNG", optimize=True)
        rel = "_thumbs/" + out_name
        _thumb_cache[img_name] = rel
        return rel
    except Exception:
        _thumb_cache[img_name] = original_rel
        return original_rel

NODE_COLOR_MAP = {
    "4": "#2e8b46", "6": "#6b3fa0",
    "#6b7280": "#6b7280", "6b7280": "#6b7280",
    "3": "#c9982e", None: "#6b7280",
    # "5" (cian de Obsidian) se reserva para personajes-planta como Flowery:
    # no son Darkners al uso, asi que se distinguen del morado generico.
    "5": "#3a9aa6",
}
EDGE_COLOR_MAP = {
    "1": "#b23c30", "2": "#c97a3d", "3": "#c9982e",
    "4": "#2e8b46", "5": "#3a9aa6", "6": "#6b3fa0", None: "#8a7a5c",
}
# Temas ⚪ que comparten el mismo diseño de pergamino/scroll de Profecía --
# misma pinta de rollo de papiro, solo cambia el texto de dentro.
PARCHMENT_LABELS = {"Profecía", "Roaring Knight", "Titan", "Ángel"}


def _note_for_label(label, note_stems):
    if label in note_stems:
        return label
    base = re.sub(r"\s*\(.*?\)\s*", "", label).strip()
    if base in note_stems:
        return base
    return None


def _match_submap(label, submap_stems):
    if label in submap_stems:
        return label
    base = re.sub(r"\s*\(.*?\)\s*", "", label).strip()
    return base if base in submap_stems else None


def _parse_cap(text):
    """Lee el nodo de texto '-cap' que acompaña a cada grupo con la ficha
    (categoria, datos rapidos, resumen de una linea)."""
    lines = [l for l in text.split("\n") if l.strip()]
    tag, facts, summary = "", [], ""
    if lines:
        m = re.match(r"#\s*(.+?)\s*—\s*\*\*(.+?)\*\*", lines[0])
        if m:
            tag = m.group(1).strip()
    for l in lines[1:]:
        if l.startswith("## "):
            summary = l[3:].strip()
        elif l.startswith("**") and l.endswith("**"):
            facts.append(l.strip("*"))
    return tag, facts, summary


def _mean_brightness(path):
    try:
        from PIL import Image
        im = Image.open(path)
        if getattr(im, "is_animated", False):
            im.seek(0)
        im = im.convert("RGBA")
        total, count = 0, 0
        for i, px in enumerate(im.getdata()):
            if i % 7 != 0:
                continue
            r, g, b, a = px
            if a < 25:
                continue
            total += 0.299 * r + 0.587 * g + 0.114 * b
            count += 1
        return (total / count) if count else None
    except Exception:
        return None


def extract_main_canvas_data(canvas_path, notes_dir, submaps_dir, sprites_dir):
    """Devuelve {"items": [...], "edges": [...]} a partir del canvas principal."""
    d = json.load(open(canvas_path, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    edges = d["edges"]

    note_stems = {os.path.splitext(f)[0] for f in os.listdir(notes_dir) if f.endswith(".md")}
    submap_stems = set()
    if os.path.isdir(submaps_dir):
        submap_stems = {os.path.splitext(f)[0] for f in os.listdir(submaps_dir) if f.endswith(".canvas")}

    items = []
    for gid, n in nodes.items():
        if n.get("type") != "group":
            continue
        label = n.get("label")
        if not label:
            continue
        cap_node = nodes.get(gid + "-cap")
        tag, facts, summary = _parse_cap(cap_node.get("text", "")) if cap_node else ("", [], "")
        cx = n["x"] + n["width"] / 2
        cy = n["y"] + n["height"] / 2
        bg = n.get("background")
        img_name = bg.split("/")[-1] if bg else None

        dark = False
        if img_name:
            b = _mean_brightness(os.path.join(sprites_dir, img_name))
            dark = b is not None and b < 70

        items.append({
            "id": gid, "label": label, "tag": tag, "facts": facts, "summary": summary,
            "cx": cx, "cy": cy, "w": n["width"], "h": n["height"],
            "color": NODE_COLOR_MAP.get(n.get("color"), "#6b7280"),
            "img": img_name, "dark": dark,
            "note": _note_for_label(label, note_stems),
            "submap": _match_submap(label, submap_stems),
        })

    group_ids = {it["id"] for it in items}
    elinks = []
    for e in edges:
        fn, tn = e.get("fromNode"), e.get("toNode")
        if fn in group_ids and tn in group_ids:
            elinks.append({
                "from": fn, "to": tn,
                "color": EDGE_COLOR_MAP.get(e.get("color"), "#8a7a5c"),
                "label": e.get("label", "") or "",
            })

    return {"items": items, "edges": elinks, "hub": nodes.get("hub")}


# Nota bilingue: igual que en build.py (mismo diccionario, es la unica
# fuente de verdad -- build.py lo referencia como board_data.EN_TITLE_OVERRIDES
# para el <title> de cada nota), estas son las etiquetas EN a mostrar para los
# nodos del corcho cuyo nombre interno (it["label"]) se quedo en español al
# crear el vault. Solo afecta al texto MOSTRADO en la tarjeta -- it["label"]
# en si no se toca, porque mas abajo se usa como clave para decidir el tema
# visual de la tarjeta (Profecía, Lake, Shelter, Cristal Oscuro...) y cambiar
# ese valor rompería esas comparaciones.
EN_TITLE_OVERRIDES = {
    "7 Flores de Colores": "7 Colored Flowers",
    "Conexión Undertale": "Undertale Connection",
    "Cristal Oscuro": "Shadow Crystal",
    "Fuentes Oscuras": "Dark Fountains",
    "Huevo": "Egg",
    "Jugador": "Player",
    "Profecía": "Prophecy",
    "Rutas": "Routes",
    "Sr. Cattenheimer": "Mr. Cattenheimer",
    "Ángel": "Angel",
}


# ---------------------------------------------------------------------------
# Decoracion ambiental del corcho principal:
#   1) El rincon de Gaster, convertido en un foco de paranoia: mas hilos rojos
#      sueltos, arañazos, chinchetas sin nota, cinta rota y notas inquietantes.
#   2) Posits/sellos de estado narrativo (Cristal Oscuro, desaparecido,
#      capturado, muerto) anclados junto al nodo correspondiente.
# Puramente cosmetico (pointer-events:none) y determinista (semillas fijas),
# asi que el resultado es estable entre builds mientras no cambien las
# posiciones de los nodos.
# ---------------------------------------------------------------------------
# Citas reales asociadas a Gaster/Undertale, tal cual aparecen en el juego
# (en ingles en las dos versiones del sitio -- es el "codigo" que los fans
# descifran, la traduccion solo va en el tooltip). "text" se muestra en
# Wingdings; "gloss" es lo que se lee al pasar el raton por encima.
GASTER_QUOTES = [
    {"text": "Entry Number 17", "gloss_es": "Entrada 17", "gloss_en": "Entry 17"},
    {"text": "Don't forget.", "gloss_es": "no lo olvides", "gloss_en": "don't forget"},
    {"text": "Darker yet darker...", "gloss_es": "cada vez más oscuro...", "gloss_en": "darker yet darker..."},
    {"text": "Entry Number 20", "gloss_es": "Entrada 20", "gloss_en": "Entry 20"},
]

# Posits de estado narrativo: en vez de los comentarios de investigador
# genericos (retirados por ahora, solo se queda el rincon de Gaster), cada
# personaje en un estado narrativo concreto lleva un posit/sello que lo dice
# directamente. Anclados junto al nodo, nunca encima de la tarjeta.
DARK_CRYSTAL_NIDS = {"g_jevil", "g12", "g7", "g_gerson", "g_pink"}   # Jevil, Spamton, Roaring Knight, Gerson Boom, Mad Mew Mew (Pink): los 5 jefes que sueltan un Cristal Oscuro
MISSING_NIDS = {"g_papyrus", "g13", "g6"}                            # Papyrus (nunca visto), Asriel, Dess: desaparecidos o aun no vistos
CAPTURED_NIDS = {"g21", "g_undyne"}                                  # Asgore, Undyne: capturados por el Caballero
DEAD_CROSS_NIDS = {"g_gerson"}                                       # Gerson Boom: el unico portador de Cristal que ya esta muerto

_STAMP_TXT = {
    "missing":  {"es": "DESAPARECIDO", "en": "MISSING"},
    "captured": {"es": "CAPTURADO", "en": "CAPTURED"},
}


def _build_board_decorations(items, board_w, board_h, lang, sprites_prefix="Sprites/"):
    by_id = {it["id"]: it for it in items}
    node_pts = [(it["px"], it["py"]) for it in items]
    out = []

    def place_near(ox, oy, seed, base_ang=None, dist_range=(120, 175), min_dist=150):
        rng = random.Random(seed)
        placed = None
        for _try in range(8):
            ang = (base_ang + rng.uniform(-30, 30)) if base_ang is not None else rng.uniform(0, 360)
            dist = rng.uniform(*dist_range)
            cand = (ox + math.cos(math.radians(ang)) * dist, oy + math.sin(math.radians(ang)) * dist)
            if all((cand[0]-px)**2 + (cand[1]-py)**2 > min_dist**2 for (px, py) in node_pts):
                placed = cand
                break
        if not placed:
            base = base_ang if base_ang is not None else 0
            placed = (ox + math.cos(math.radians(base)) * dist_range[1], oy + math.sin(math.radians(base)) * dist_range[1])
        return placed, rng

    # ---- Cristal Oscuro: foto del objeto junto a cada jefe que lo suelta ----
    crystal_src = sprites_prefix + urllib.parse.quote("Shadow_Crystal_item.webp")
    crystal_cap = "Shadow Crystal" if lang == "en" else "Cristal Oscuro"
    for nid in DARK_CRYSTAL_NIDS:
        it = by_id.get(nid)
        if not it:
            continue
        ox, oy = it["px"], it["py"]
        # Gerson tambien lleva la cruz de "muerto" -- la alejamos hacia arriba
        # para que el posit del cristal y la cruz no se pisen entre si.
        base_ang = 270 if nid in DEAD_CROSS_NIDS else None
        (px, py), rng = place_near(ox, oy, f"crystal-{nid}", base_ang=base_ang)
        rot = rng.uniform(-10, 10)
        out.append(
            f'<div class="doodle doodle-note item-photo" style="left:{px:.0f}px; top:{py:.0f}px; transform:rotate({rot:.1f}deg);">'
            f'<img src="{crystal_src}" alt="" loading="lazy"><span class="cap">{html.escape(crystal_cap)}</span></div>'
        )

    # ---- Desaparecidos / no vistos aun: sello rojo ----
    for nid in MISSING_NIDS:
        it = by_id.get(nid)
        if not it:
            continue
        ox, oy = it["px"], it["py"]
        # el sello es mas ancho que un post-it normal (palabra larga en
        # mayusculas) -- mas distancia y radio de choque para que no invada
        # ninguna tarjeta vecina.
        (px, py), rng = place_near(ox, oy, f"missing-{nid}", dist_range=(195, 250), min_dist=210)
        rot = rng.uniform(-18, 18)
        txt = _STAMP_TXT["missing"]["en"] if lang == "en" else _STAMP_TXT["missing"]["es"]
        out.append(
            f'<div class="doodle doodle-stamp stamp-missing" style="left:{px:.0f}px; top:{py:.0f}px; transform:rotate({rot:.1f}deg);">{txt}</div>'
        )

    # ---- Capturados por el Caballero: sello ----
    for nid in CAPTURED_NIDS:
        it = by_id.get(nid)
        if not it:
            continue
        ox, oy = it["px"], it["py"]
        (px, py), rng = place_near(ox, oy, f"captured-{nid}", dist_range=(195, 250), min_dist=210)
        rot = rng.uniform(-18, 18)
        txt = _STAMP_TXT["captured"]["en"] if lang == "en" else _STAMP_TXT["captured"]["es"]
        out.append(
            f'<div class="doodle doodle-stamp stamp-captured" style="left:{px:.0f}px; top:{py:.0f}px; transform:rotate({rot:.1f}deg);">{txt}</div>'
        )

    # ---- Muerto: cruz de tumba ----
    for nid in DEAD_CROSS_NIDS:
        it = by_id.get(nid)
        if not it:
            continue
        ox, oy = it["px"], it["py"]
        (px, py), rng = place_near(ox, oy, f"cross-{nid}", base_ang=90)
        rot = rng.uniform(-12, 12)
        out.append(
            f'<div class="doodle doodle-cross" style="left:{px:.0f}px; top:{py:.0f}px; transform:rotate({rot:.1f}deg);">'
            f'<svg viewBox="0 0 20 26"><rect x="8" y="1" width="4" height="24" rx="1" fill="#7a6a52"/><rect x="1" y="7" width="18" height="4" rx="1" fill="#7a6a52"/></svg></div>'
        )

    # ---- Rincon de Gaster: foco de paranoia y deterioro ----
    gaster_it = next((it for it in items if it["label"] == "Gaster (W. D. Gaster)"), None)
    if gaster_it:
        gx, gy = gaster_it["px"], gaster_it["py"]
        grng = random.Random("gaster-paranoia-v2")
        vw, vh = 760, 600
        out.append(f'<div class="doodle gaster-vignette" style="left:{gx-vw/2:.0f}px; top:{gy-vh/2:.0f}px; width:{vw}px; height:{vh}px;"></div>')

        # hilos rojos disparados en todas direcciones, mas densos que antes
        for i in range(10):
            ang = grng.uniform(0, 360)
            length = grng.randint(80, 220)
            out.append(f'<div class="doodle doodle-arrow ink-red gaster-string" style="left:{gx:.0f}px; top:{gy:.0f}px; width:{length}px; transform:rotate({ang:.1f}deg);"></div>')

        # arañazos frenéticos agrupados (deterioro)
        scratch_base = grng.uniform(0, 360)
        scratch_dist = grng.randint(70, 130)
        sang = math.radians(grng.uniform(0, 360))
        scx = gx + math.cos(sang) * scratch_dist
        scy = gy + math.sin(sang) * scratch_dist
        for i in range(3):
            out.append(f'<div class="doodle gaster-scratch" style="left:{scx:.0f}px; top:{scy+i*7:.0f}px; width:64px; transform:rotate({scratch_base+i*4:.1f}deg);"></div>')

        # cinta rota / resto de recorte arrancado
        tdx = grng.choice([-1, 1]) * grng.randint(150, 260)
        tdy = grng.choice([-1, 1]) * grng.randint(60, 140)
        out.append(f'<div class="doodle gaster-tape" style="left:{gx+tdx:.0f}px; top:{gy+tdy:.0f}px; transform:rotate({grng.uniform(-30,30):.1f}deg);"></div>')

        # chinchetas muertas (sin nota, hilo cortado)
        for i in range(4):
            dx = grng.choice([-1, 1]) * grng.randint(140, 260)
            dy = grng.choice([-1, 1]) * grng.randint(130, 230)
            out.append(f'<div class="doodle doodle-pin-lone" style="left:{gx+dx:.0f}px; top:{gy+dy:.0f}px;"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>')

        # notas de Gaster: citas reales del juego, en Wingdings, como
        # negativos pegados con celo o chincheta (la traduccion solo sale
        # al pasar el raton por encima, como un mensaje cifrado de verdad).
        # Un angulo base distinto por nota (arriba-izq, abajo, izquierda,
        # DERECHA) para que se repartan alrededor en vez de amontonarse
        # todas al mismo lado -- con jitter + comprobacion contra todos los
        # nodos (incluida la propia tarjeta de Gaster) para que ninguna
        # tape la cara.
        base_angles = [215, 120, 165, 350]
        for i, q in enumerate(GASTER_QUOTES):
            base_ang = base_angles[i % len(base_angles)]
            placed = None
            for _try in range(8):
                ang = base_ang + grng.uniform(-22, 22)
                dist = grng.uniform(230, 340)
                cand = (gx + math.cos(math.radians(ang)) * dist, gy + math.sin(math.radians(ang)) * dist)
                if all((cand[0]-px)**2 + (cand[1]-py)**2 > 195**2 for (px, py) in node_pts):
                    placed = cand
                    break
            if not placed:
                placed = (gx + math.cos(math.radians(base_ang)) * 340, gy + math.sin(math.radians(base_ang)) * 340)
            nx, ny = placed
            rot = grng.uniform(-16, 16)
            gloss = q["gloss_es"] if lang != "en" else q["gloss_en"]
            tape = grng.random() < 0.5
            out.append(
                f'<div class="doodle doodle-note gaster-note{" tape" if tape else ""}" '
                f'style="left:{nx:.0f}px; top:{ny:.0f}px; transform:rotate({rot:.1f}deg);" '
                f'title="{html.escape(gloss)}">{html.escape(q["text"])}</div>'
            )

    return "\n".join(out)


def build_board_html(data, scale=0.24, pad=220, card_w=150, index_cards=None, sprites_dir=None, thumbs_out_dir=None, sprites_prefix="Sprites/", lang="es"):
    """A partir de {"items","edges"} genera (nodes_html, links_js, board_w, board_h)."""
    items = data["items"]
    edges = data["edges"]
    UI = {
        "es": {"open_note": "Abrir nota →", "eyebrow": "Boletín del Corcho",
               "dateline": "Edición especial · Deltarune Teorías", "no_img": "sin imagen"},
        "en": {"open_note": "Open note →", "eyebrow": "The Corkboard Bulletin",
               "dateline": "Special edition · Deltarune Theories", "no_img": "no image"},
    }[lang if lang in ("es", "en") else "es"]

    xs = [it["cx"] for it in items]
    ys = [it["cy"] for it in items]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    board_w = int((maxx - minx) * scale + pad * 2)
    board_h = int((maxy - miny) * scale + pad * 2)

    for it in items:
        it["px"] = (it["cx"] - minx) * scale + pad
        it["py"] = (it["cy"] - miny) * scale + pad

    inner_w = card_w - 12
    min_h, max_h = 60, 230

    # Los nodos con tema visual especial (Shelter, Lago, Cristal Oscuro, etc.)
    # usan una tarjeta mas ancha que el resto, para poder verse mas grandes
    # sin que la imagen de fondo quede con bordes de letterbox feos al
    # forzar solo la altura. El ancho interior se recalcula por nodo mas
    # abajo, dentro del bucle principal.
    BIG_CARD_WIDTHS = {
        "Shelter": 230, "Lake": 230, "Cristal Oscuro": 230,
        "Conexión Undertale": 230, "Profecía": 210, "Fuentes Oscuras": 220,
    }

    news_html = ""
    hub = data.get("hub")
    index_cards = index_cards or []
    if hub or index_cards:
        cards = []
        if hub:
            raw = hub.get("text", "")
            lines = [l for l in raw.split("\n") if l.strip()]
            heading, rest = "", []
            for l in lines:
                l2 = re.sub(r"^#+\s*", "", l).strip("*")
                if not heading:
                    heading = l2
                else:
                    rest.append(l2)
            blurb = " ".join(rest)
            blurb = re.sub(r'`([^`]+)`', r'\1', blurb)[:150]
            cards.append({"title": heading, "blurb": blurb, "href": None})
        for c in index_cards:
            cards.append({
                "title": c["title"], "blurb": c["blurb"],
                "href": "notes/" + urllib.parse.quote(c["slug"]) + ".html",
            })

        cols = []
        for c in cards:
            link_html = f'<a class="news-link" href="{c["href"]}">{UI["open_note"]}</a>' if c["href"] else ""
            cols.append(f'''
    <div class="news-col">
      <div class="news-heading">{html.escape(c["title"])}</div>
      <div class="news-body"><p>{html.escape(c["blurb"])}</p></div>
      {link_html}
    </div>''')

        news_x = pad * 0.35
        news_y = board_h - pad - 250
        news_html = f'''
  <div class="news-clip" style="left:{news_x:.0f}px; top:{news_y:.0f}px;">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    <div class="news-masthead">
      <span class="news-eyebrow">{UI["eyebrow"]}</span>
      <span class="news-dateline">{UI["dateline"]}</span>
    </div>
    <div class="news-cols">{''.join(cols)}</div>
  </div>'''

    node_html = []

    for it in items:
        nid = it["id"]
        random.seed(nid)
        rot = random.uniform(-3.5, 3.5)
        x, y = it["px"], it["py"]

        aspect = (it["h"] / it["w"]) if it.get("w") and it.get("h") else 0.8
        this_card_w = BIG_CARD_WIDTHS.get(it["label"], card_w)
        this_inner_w = this_card_w - 12
        # para los nodos grandes no forzamos el tope de 230: dejamos que la
        # altura seguida el aspecto real de la imagen de fondo (sin recorte
        # artificial), para que no queden bordes de letterbox feos
        this_max_h = 900 if it["label"] in BIG_CARD_WIDTHS else max_h
        thumb_h = max(min_h, min(this_max_h, this_inner_w * aspect))

        if it["img"]:
            img_ref = it["img"]
            if sprites_dir and thumbs_out_dir:
                img_ref = make_board_thumb(it["img"], sprites_dir, thumbs_out_dir)
            src = sprites_prefix + urllib.parse.quote(img_ref)
            img_tag = f'<img src="{src}" alt="" loading="lazy">'
        else:
            img_tag = f'<div class="noimg"><i>{UI["no_img"]}</i></div>'

        note_attr = slugify(it["note"]) if it["note"] else ""
        display_label = EN_TITLE_OVERRIDES.get(it["label"], it["label"]) if lang == "en" else it["label"]
        title = html.escape(display_label)
        tag = html.escape(it["tag"])
        summary = html.escape(it["summary"])
        approx_card_h = thumb_h + 60
        thumb_class = "thumb thumb-dark" if it.get("dark") else "thumb"

        submap_badge = ""
        if it.get("submap"):
            submap_url = "submaps/" + urllib.parse.quote(slugify(it["submap"])) + ".html"
            submap_tooltip = f"View submap of {title}" if lang == "en" else f"Ver submapa de {title}"
            submap_badge = (f'<a class="submap-badge" href="{submap_url}" '
                             f'title="{submap_tooltip}" onmousedown="event.stopPropagation()">🗺️</a>')

        if it["label"] in PARCHMENT_LABELS:
            node_html.append(f'''
  <div class="node node-scroll" data-id="{nid}" data-note="{note_attr}" data-theme="parchment" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="scroll">
      <div class="roll roll-top"><div class="frizz f1"></div><div class="frizz f2"></div><div class="frizz f3"></div></div>
      <div class="sheet">
        <div class="tear left t1"></div><div class="tear left t2"></div>
        <div class="tear right t1"></div><div class="tear right t2"></div>
        <div class="{thumb_class}" style="height:{max(95,thumb_h*0.82):.0f}px;">{img_tag}</div>
        <div class="title">{title}</div>
        <div class="summary">{summary}</div>
      </div>
      <div class="roll roll-bottom"><div class="frizz f1"></div><div class="frizz f2"></div><div class="frizz f3"></div></div>
    </div>
  </div>''')
        elif it["label"] == "Lake":
            node_html.append(f'''
  <div class="node node-wet" data-id="{nid}" data-note="{note_attr}" data-theme="wet" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card wet-card" style="border-top:5px solid {it['color']};">
      <div class="crumple"></div><div class="creases"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] == "Shelter":
            node_html.append(f'''
  <div class="node node-rusted" data-id="{nid}" data-note="{note_attr}" data-theme="rusted" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card rusted-card" style="border-top:5px solid {it['color']};">
      <div class="rust-texture"></div>
      <div class="rivet rivet-tl"></div><div class="rivet rivet-tr"></div><div class="rivet rivet-bl"></div><div class="rivet rivet-br"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] == "Cristal Oscuro":
            node_html.append(f'''
  <div class="node node-crystal" data-id="{nid}" data-note="{note_attr}" data-theme="crystal" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card crystal-card" style="border-top:5px solid {it['color']};">
      <div class="crystal-glow"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] == "Conexión Undertale":
            node_html.append(f'''
  <div class="node node-undertale" data-id="{nid}" data-note="{note_attr}" data-theme="undertale" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card undertale-card" style="border-top:5px solid {it['color']};">
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] == "Fuentes Oscuras":
            node_html.append(f'''
  <div class="node node-fountain" data-id="{nid}" data-note="{note_attr}" data-theme="fountain" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card fountain-card" style="border-top:5px solid {it['color']};">
      <div class="fountain-glow"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] == "Gaster (W. D. Gaster)":
            node_html.append(f'''
  <div class="node node-gaster" data-id="{nid}" data-note="{note_attr}" data-theme="gaster" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card gaster-card" style="border-top:5px solid {it['color']};">
      <div class="gaster-dust"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] in ("Forgotten Man", "Huevo", "Everyman"):
            # Diseno "olvidado": foto vieja y desteñida en una caja polvorienta,
            # con telarana en la esquina y el borde inferior rasgado a mano.
            node_html.append(f'''
  <div class="node node-forgotten" data-id="{nid}" data-note="{note_attr}" data-theme="forgotten" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card forgotten-card" style="border-top:5px solid {it['color']};">
      <div class="dust-motes"></div>
      <div class="cracks"></div>
      <div class="cobweb"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
    <div class="torn-strip"></div>
  </div>''')
        else:
            # Por categoria (segun el tag "mundo" tecleado en el canvas, no el
            # color crudo -- Titan es un caso donde no coinciden): los
            # Lightner se quedan con la tarjeta clasica; los Darkner pasan a
            # verse como un negativo fotografico; las Plantas, como papel
            # vegetal traslucido. Lugares y Temas ya con tema propio no pasan
            # por aqui. FRIEND es el mismo negativo de los Darkner pero en
            # negro (es una amenaza real, no un Darkner al uso); Rutas usa el
            # aspecto de terminal/mecanica de juego en verde fosforo.
            extra_card_cls = ""
            node_theme = "postit"
            if it["label"] == "FRIEND":
                extra_card_cls = " friend-card"
                node_theme = "friend"
            elif it["label"] == "Rutas":
                extra_card_cls = " rutas-card"
                node_theme = "rutas"
            elif "Darkner" in it["tag"]:
                extra_card_cls = " darkner-card"
                node_theme = "darkner"
            elif "Planta" in it["tag"]:
                extra_card_cls = " planta-card"
                node_theme = "planta"
            node_html.append(f'''
  <div class="node" data-id="{nid}" data-note="{note_attr}" data-theme="{node_theme}" style="left:{x-this_card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{this_card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card{extra_card_cls}" style="border-top:5px solid {it['color']};">
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')

    links_js = ",\n  ".join(
        "[" + ",".join(json.dumps(v, ensure_ascii=False) for v in (e['from'], e['to'], e['color'], e['label'])) + "]"
        for e in edges
    )

    decorations_html = _build_board_decorations(items, board_w, board_h, lang, sprites_prefix=sprites_prefix)

    return "\n".join(node_html) + news_html + decorations_html, links_js, board_w, board_h, ""

