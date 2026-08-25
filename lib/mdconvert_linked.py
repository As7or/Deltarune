import re, os, html, urllib.parse, unicodedata

def slugify(name):
    """Quita acentos/diacríticos del nombre para usarlo como nombre de archivo
    seguro (algunos descompresores de Windows corrompen nombres con tildes)."""
    nfkd = unicodedata.normalize('NFKD', name)
    return nfkd.encode('ascii', 'ignore').decode('ascii') or name

CALLOUT_ICONS = {
    "info": ("info", "#3a7bd5"),
    "tip": ("tip", "#2e8b57"),
    "example": ("cap", "#8a6a3a"),
    "danger": ("!", "#b23c30"),
    "quote": ("quote", "#6b3fa0"),
    "question": ("?", "#c9982e"),
}

# En "Objetos del Mundo Oscuro.md" cada "## Capítulo N — ..." agrupa varias
# secciones [!example] (Lugares, Personajes, Enemigos...) con sus tablas.
# Se les asigna una clase CSS distinta por capítulo -segun el color mas
# representativo de cada Mundo Oscuro- para que el postit y la tabla de esa
# seccion se distingan a simple vista de las de otro capitulo. Solo esta nota
# usa un encabezado "## Capítulo N", asi que no afecta a ningun otro archivo.
CHAPTER_COLOR_CLASS = {
    1: "chapter-c1",  # Reino de las Cartas -> rojo (cartas, alfombra roja del King)
    2: "chapter-c2",  # Mundo Ciber -> magenta neon
    3: "chapter-c3",  # Mundo TV -> cian/turquesa (Queen, estatica de TV)
    4: "chapter-c4",  # Iglesia y Santuario Oscuro -> violeta
    5: "chapter-c5",  # Reino de las Flores -> verde
}

# Diccionario {nombre original de la nota: nombre de archivo sin acentos} para
# saber que wikilinks [[Nombre]] se pueden convertir en enlaces reales, y con
# qué nombre de archivo real construir el href. Lo rellena el script llamador.
KNOWN_NOTES = {}

# Carpeta real donde estan los sprites en disco (para poder comprobar si un PNG/GIF
# tiene transparencia real y así no ponerle sombra). La rellena el script llamador.
SPRITES_ABS_DIR = None

# Indice recursivo nombre-de-archivo -> ruta relativa dentro de Sprites/, porque
# Obsidian resuelve ![[archivo.ext]] buscando en TODO el vault (subcarpetas
# incluidas), no solo en la raiz de Sprites/. Se construye una vez por sesion.
_sprite_index = None
def _build_sprite_index():
    global _sprite_index
    _sprite_index = {}
    if not SPRITES_ABS_DIR:
        return
    for dirpath, _, filenames in os.walk(SPRITES_ABS_DIR):
        rel_dir = os.path.relpath(dirpath, SPRITES_ABS_DIR)
        for fname in filenames:
            rel_path = fname if rel_dir == "." else f"{rel_dir}/{fname}"
            _sprite_index.setdefault(fname, rel_path)

def resolve_sprite_path(name):
    """Devuelve la ruta relativa real (con subcarpeta si hace falta) de un
    sprite dentro de Sprites/, buscando en todo el arbol si no esta suelto
    en la raiz."""
    if not SPRITES_ABS_DIR:
        return name
    if os.path.exists(os.path.join(SPRITES_ABS_DIR, name)):
        return name
    global _sprite_index
    if _sprite_index is None:
        _build_sprite_index()
    return _sprite_index.get(name, name)

_alpha_cache = {}
def has_real_transparency(name):
    if not SPRITES_ABS_DIR:
        return False
    if name in _alpha_cache:
        return _alpha_cache[name]
    result = False
    try:
        from PIL import Image
        path = os.path.join(SPRITES_ABS_DIR, resolve_sprite_path(name))
        im = Image.open(path)
        if getattr(im, "is_animated", False):
            im.seek(0)
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im2 = im.convert("RGBA")
            alpha = im2.getchannel("A")
            lo, hi = alpha.getextrema()
            result = lo < 250
    except Exception:
        result = False
    _alpha_cache[name] = result
    return result

_dims_cache = {}
def is_bust_shaped(name, threshold=1.15):
    """True si la imagen es cuadrada o más ancha que alta (típico de un busto/cara
    de talksprite), en vez de un sprite de cuerpo entero (claramente más alto que
    ancho). Se usa para decidir el tamaño sin depender del texto de la cabecera."""
    if not SPRITES_ABS_DIR:
        return False
    if name in _dims_cache:
        return _dims_cache[name]
    result = False
    try:
        from PIL import Image
        path = os.path.join(SPRITES_ABS_DIR, resolve_sprite_path(name))
        im = Image.open(path)
        w, h = im.size
        if w > 0:
            result = (h / w) < threshold
    except Exception:
        result = False
    _dims_cache[name] = result
    return result

def resolve_note_stem(target):
    if target in KNOWN_NOTES:
        return KNOWN_NOTES[target]
    base = re.sub(r"\s*\(.*?\)\s*", "", target).strip()
    if base in KNOWN_NOTES:
        return KNOWN_NOTES[base]
    # Algunos personajes tienen su alias/identidad entre parentesis en el
    # TITULO de su propia nota (p.ej. "Mad Mew Mew (Pink)", "Gaster (W. D.
    # Gaster)"). Si el texto es justo ese alias ("Pink", "Pink (Body)"...),
    # se resuelve tambien contra el parentesis del titulo, no solo contra el
    # nombre completo.
    for note_title, slug in KNOWN_NOTES.items():
        m = re.search(r"\((.+?)\)\s*$", note_title)
        if m and m.group(1).strip().lower() == base.lower():
            return slug
    return None

def img_url(name, sprites_prefix):
    return sprites_prefix + urllib.parse.quote(resolve_sprite_path(name))

def inline_md(text, sprites_prefix, force_small=False, respect_size=True):
    # Las imagenes y wikilinks se resuelven ANTES de escapar el texto (para que
    # nombres de archivo con apostrofes, & u otros caracteres no se corrompan al
    # pasar por html.escape). Se guardan como placeholders y se reinsertan al final.
    # respect_size=False para celdas de tabla: ahi el `|N` es un resto del ancho
    # de embed de Obsidian (casi siempre 50) y el tamano real ya lo controla el
    # CSS de table.note-table .inline-img, asi que no debe convertirse en un
    # max-width inline que lo aplaste.
    placeholders = {}
    def stash(fragment):
        key = f"\x00PH{len(placeholders)}\x00"
        placeholders[key] = fragment
        return key

    def img_sub(m):
        inner = m.group(1)
        parts = inner.split("|")
        name = parts[0].strip()
        size_style = ""
        if respect_size and len(parts) > 1 and parts[-1].strip().isdigit():
            size_style = f' style="width:auto;max-width:{parts[-1].strip()}px;"'
        if force_small:
            cls = "inline-img-small"
        else:
            cls = "inline-img inline-img-alpha" if has_real_transparency(name) else "inline-img"
        return stash(f'<img class="{cls}" src="{img_url(name, sprites_prefix)}" alt=""{size_style} loading="lazy">')
    text = re.sub(r"!\[\[(.+?)\]\]", img_sub, text)

    def youtube_sub(m):
        vid = m.group(1).strip()
        embed = (f'<div class="yt-embed"><iframe src="https://www.youtube.com/embed/{vid}" '
                 f'title="YouTube video" frameborder="0" '
                 f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                 f'allowfullscreen loading="lazy"></iframe></div>')
        return stash(embed)
    text = re.sub(r"\{\{youtube:\s*([A-Za-z0-9_-]+)\s*\}\}", youtube_sub, text)

    def wikilink_sub(m):
        inner = m.group(1)
        target = inner.split("|")[0].strip()
        display = inner.split("|")[-1].strip()
        m_sub = re.match(r"Submapas/(.+?)\.canvas$", target)
        if m_sub:
            sub_stem = slugify(m_sub.group(1))
            href = "../submaps/" + urllib.parse.quote(sub_stem) + ".html"
            return stash(f'<a class="submap-link" href="{href}">🗺️ {html.escape(display)}</a>')
        stem = resolve_note_stem(target)
        if stem:
            return stash(f'<a class="wikilink" href="{urllib.parse.quote(stem)}.html">{html.escape(display)}</a>')
        return stash(f'<span class="wikilink">{html.escape(display)}</span>')
    text = re.sub(r"\[\[(.+?)\]\]", wikilink_sub, text)

    text = html.escape(text)
    # Obsidian a veces mete un <br> literal dentro de una celda de tabla para
    # forzar salto de línea; al escapar el texto se convierte en texto visible
    # ("&lt;br&gt;"), hay que devolverlo a un salto de línea real.
    text = re.sub(r"&lt;br\s*/?&gt;", "<br>", text, flags=re.I)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)

    for key, val in placeholders.items():
        text = text.replace(key, val)
    return text

def extract_callout_by_title(md_text, target_title, sprites_prefix="../Sprites/"):
    """Busca, dentro de una nota completa, el callout (teoria/relacion) cuyo
    titulo coincide con target_title, y lo devuelve ya renderizado a HTML
    completo (con imagenes, wikilinks, etc.) usando el mismo pipeline que la
    pagina de nota normal. Se usa para que, al pulsar una burbuja de teoria
    en un submapa, se muestre el texto REAL y completo de la nota en vez del
    resumen abreviado que vive dentro del propio .canvas."""
    def norm(s):
        s = s.lower().strip()
        s = re.sub(r'["\'¿?¡!.,:;]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    target_norm = norm(target_title)
    if not target_norm:
        return None

    lines = md_text.split("\n")
    _, lines = parse_frontmatter(lines)
    n = len(lines)
    i = 0
    candidates = []  # (score, html)
    while i < n:
        line = lines[i]
        d, _ = depth_of(line)
        if d > 0:
            base_depth = d
            block = []
            first = True
            while i < n:
                dd, content = depth_of(lines[i])
                if dd == 0: break
                if not first and dd == base_depth and re.match(r"\[!\w+\][+-]?\s*", content):
                    break
                block.append((dd, content)); i += 1; first = False
            header = block[0][1]
            m = re.match(r"\[!(\w+)\][+-]?\s*(.*)", header)
            block_title = m.group(2).strip() if m else ""
            bt_norm = norm(block_title)
            if bt_norm:
                if bt_norm == target_norm:
                    score = 3
                elif target_norm in bt_norm or bt_norm in target_norm:
                    score = 2
                else:
                    # solapamiento de palabras como ultimo recurso
                    tset, bset = set(target_norm.split()), set(bt_norm.split())
                    overlap = len(tset & bset)
                    score = 1 if overlap >= max(1, min(len(tset), len(bset)) - 1) and overlap > 0 else 0
                if score > 0:
                    candidates.append((score, render_callout_block(block, sprites_prefix, body_only=True)))
            continue
        i += 1

    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]

def parse_frontmatter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm_lines = lines[1:i]
                rest = lines[i+1:]
                fm = {}
                for l in fm_lines:
                    if ":" in l:
                        k, v = l.split(":", 1)
                        fm[k.strip()] = v.strip().strip('"')
                return fm, rest
    return {}, lines

def split_row(r):
    # el pipe escapado \| (usado por Obsidian dentro de ![[img\|width]]) no debe
    # partir la celda; lo protegemos antes de dividir y lo restauramos después.
    SENTINEL = "\x00PIPE\x00"
    protected = r.replace("\\|", SENTINEL)
    cells = [c.strip().replace(SENTINEL, "|") for c in protected.strip("|").split("|")]
    return cells

def reliability_classes(cell_html):
    """Traduce los emojis de fiabilidad que ya vienen en el markdown original
    (🔵 suposicion fundada, 🟡 teoria mas debil del propio autor, 🆕 verdicto
    anadido/corregido tras el video) a clases CSS que se aplican a la CELDA
    (td) entera, para que el color de fondo rellene todo el hueco como en la
    hoja de calculo original en vez de solo un span interior. No requiere
    tocar ninguna nota: se deriva del emoji que ya esta en el texto (y sigue
    viendose bien en Obsidian, que no lee estas clases)."""
    classes = []
    if "🔵" in cell_html:
        classes.append("rel-blue")
    if "🟡" in cell_html:
        classes.append("rel-yellow")
    if "🆕" in cell_html:
        classes.append("rel-new")
    return classes

def parse_table(block_lines, sprites_prefix):
    rows = [l for l in block_lines if l.strip().startswith("|")]
    if len(rows) < 2:
        return None
    header = split_row(rows[0])
    body_rows = rows[2:]
    small_cols = {i for i, h in enumerate(header) if "talksprite" in h.lower() or "sprite" in h.lower()}
    reliability_cols = {i for i, h in enumerate(header) if "identidad" in h.lower()}
    # Las tablas de "Objetos del Mundo Oscuro.md" siguen siempre las mismas 4
    # columnas (Sprite / Mundo Oscuro / Identidad real / Sprite Mundo Claro).
    # Se marcan con una clase aparte para poder ajustar el ancho de las
    # columnas de TEXTO (nombre y descripcion) sin tocar el layout de otras
    # tablas del vault (p.ej. la comparativa de 2 columnas de Rudy.md).
    is_id_table = [h.strip() for h in header] == ["Sprite", "Mundo Oscuro", "Identidad real", "Sprite Mundo Claro"]
    table_cls = "note-table id-table" if is_id_table else "note-table"
    out = [f'<table class="{table_cls}">', "<tr>"]
    for h in header:
        out.append(f"<th>{inline_md(h, sprites_prefix, respect_size=False)}</th>")
    out.append("</tr>")
    for r in body_rows:
        cells = split_row(r)
        out.append("<tr>")
        for idx, c in enumerate(cells):
            # Si el contenido de la celda coincide EXACTAMENTE con el nombre de
            # una nota real del vault (p.ej. "Ralsei" en la columna Mundo
            # Oscuro), se enlaza automaticamente como [[wikilink]] sin tener
            # que tocar el markdown fila por fila en las 5 tablas x 5
            # capitulos. Coincidencia exacta a proposito: evita enlazar a
            # medias frases descriptivas ("Un cubo de ratones de ordenador")
            # que nunca van a coincidir con el nombre de una nota.
            c_stripped = c.strip()
            if c_stripped and not c_stripped.startswith("![[") and not c_stripped.startswith("[[") and resolve_note_stem(c_stripped):
                c = f"[[{c_stripped}]]"
            cell_html = inline_md(c, sprites_prefix, force_small=(idx in small_cols), respect_size=False)
            if idx in reliability_cols:
                classes = reliability_classes(cell_html)
                cls_attr = f' class="{" ".join(classes)}"' if classes else ""
                out.append(f"<td{cls_attr}>{cell_html}</td>")
            else:
                out.append(f"<td>{cell_html}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)

def depth_of(line):
    d = 0
    i = 0
    while i < len(line):
        if line[i] == '>':
            d += 1
            i += 1
            if i < len(line) and line[i] == ' ':
                i += 1
        else:
            break
    return d, line[i:]

def render_callout_block(lines, sprites_prefix, depth=0, body_only=False, chapter_class=None):
    header = lines[0][1]
    m = re.match(r"\[!(\w+)\]([+-]?)\s*(.*)", header)
    ctype = m.group(1) if m else "info"
    title = m.group(3) if m else ""
    icon, color = CALLOUT_ICONS.get(ctype, ("note", "#8a7a5c"))
    base_depth = lines[0][0]
    # "Ficha de personalidad" (callout tipo tip) es la unica seccion donde las
    # imagenes deben verse pequenas y centradas: no aportan tanto detalle ahi
    # como para ocupar toda la pagina.
    force_small_here = (ctype == "tip")
    body_parts = []
    i = 1
    while i < len(lines):
        d, content = lines[i]
        if d > base_depth:
            nested = []
            while i < len(lines) and lines[i][0] > base_depth:
                nested.append((lines[i][0]-base_depth, lines[i][1]))
                i += 1
            body_parts.append(render_callout_block(nested, sprites_prefix, depth+1, chapter_class=chapter_class))
        else:
            stripped = content.strip()
            # Imagen de cabecera: si es la PRIMERA linea de contenido de un
            # callout tipo "example" (las secciones de categoria de "Objetos
            # del Mundo Oscuro.md": Lugares, Personajes, Enemigos...) y va
            # sola en su propia linea, se trata como imagen de resumen del
            # capitulo/zona y se renderiza mas pequena y centrada (clase
            # fig-header), en vez de con la clase inline-img generica a
            # ancho completo que usan el resto de imagenes sueltas dentro de
            # cualquier callout del vault.
            if i == 1 and ctype == "example" and re.fullmatch(r"!\[\[.+?\]\]", stripped):
                mimg = re.match(r"!\[\[(.+?)\]\]", stripped)
                name = mimg.group(1).split("|")[0].strip()
                caption = ""
                if i+1 < len(lines) and lines[i+1][0] == d:
                    next_stripped = lines[i+1][1].strip()
                    if len(next_stripped) > 1 and next_stripped.startswith("*") and next_stripped.endswith("*"):
                        caption = next_stripped.strip("*")
                        i += 1
                fig_cls = "fig-header fig-alpha" if has_real_transparency(name) else "fig-header"
                body_parts.append(
                    f'<figure class="{fig_cls}"><img src="{img_url(name, sprites_prefix)}" alt="" loading="lazy">' +
                    (f"<figcaption>{html.escape(caption)}</figcaption>" if caption else "") + "</figure>"
                )
                i += 1
                continue
            if stripped.startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i][0] == d and lines[i][1].strip().startswith("|"):
                    table_lines.append(lines[i][1])
                    i += 1
                t = parse_table(table_lines, sprites_prefix)
                if t:
                    body_parts.append(t)
                continue
            if stripped.startswith("- ") or stripped.startswith("* "):
                items = []
                while i < len(lines) and lines[i][0] == d and (lines[i][1].strip().startswith("- ") or lines[i][1].strip().startswith("* ")):
                    items.append(lines[i][1].strip()[2:])
                    i += 1
                only_links = all(re.fullmatch(r"\[\[.+?\]\]", it.strip()) for it in items) and len(items) > 0
                if only_links:
                    chips = "".join(f'<span class="link-chip">{inline_md(it, sprites_prefix)}</span>' for it in items)
                    body_parts.append(f'<div class="link-row">{chips}</div>')
                else:
                    lis = "".join(f"<li>{inline_md(it, sprites_prefix)}</li>" for it in items)
                    body_parts.append(f'<ul class="note-list">{lis}</ul>')
                continue
            if stripped:
                body_parts.append(f"<p>{inline_md(content, sprites_prefix, force_small=force_small_here)}</p>")
            i += 1
    body = "".join(body_parts)
    if body_only:
        # Sin el div .callout envolvente: se usa cuando el contenedor que lo
        # recibe (p.ej. el popup tipo postit de un submapa) ya aporta su
        # propio marco visual, para no anidar una tarjeta postit dentro de
        # otra y generar margenes/huecos horizontales raros.
        return body
    # Las cabeceras de categoria de "Objetos del Mundo Oscuro.md" (Lugares,
    # Personajes, Enemigos...) siguen siempre el patron "EMOJI Etiqueta (N)".
    # Se separan en icono / etiqueta / contador para poder darles un
    # tratamiento de "ficha de expediente" (icono a modo de chincheta,
    # contador a modo de sello) en vez de un titulo de postit generico.
    case_match = re.match(r"^(\S+)\s+(.+?)\s*\((\d+)\)\s*$", title) if ctype == "example" and title else None
    if case_match:
        icon_txt, label_txt, count_txt = case_match.groups()
        title_html = (
            '<div class="callout-title case-tag">'
            f'<span class="case-tag-icon">{html.escape(icon_txt)}</span>'
            f'<span class="case-tag-label">{inline_md(label_txt, sprites_prefix)}</span>'
            f'<span class="case-tag-count">{html.escape(count_txt)}</span>'
            '</div>'
        )
    elif title:
        title_html = f'<div class="callout-title">{inline_md(title, sprites_prefix)}</div>'
    else:
        title_html = ""
    import importlib
    try:
        from note_page_template import rotation_for, torn_variant_for
    except ImportError:
        rotation_for = lambda t: 0
        torn_variant_for = lambda t: 1
    rot = rotation_for((title or ctype) + str(depth)) * (1.3 if depth > 0 else 1)
    torn_variant = torn_variant_for((title or ctype) + str(depth) + ctype)
    cls_extra = f" {chapter_class}" if chapter_class else ""
    cls_extra += f" callout-torn-{torn_variant}"
    return (f'<div class="callout callout-{ctype}{cls_extra}" style="transform:rotate({rot}deg);">'
            f'{title_html}<div class="callout-body">{body}</div></div>')

def convert_note_linked(md_text, sprites_prefix="../Sprites/", lang="es"):
    """Convierte una nota .md de Obsidian a HTML enlazando imagenes como
    archivos reales (sprites_prefix + nombre), sin base64."""
    lines = md_text.split("\n")
    fm, lines = parse_frontmatter(lines)
    out = []
    i = 0
    n = len(lines)
    chapter_class = None
    while i < n:
        line = lines[i]
        if line.strip().startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i]); i += 1
            t = parse_table(block, sprites_prefix)
            if t: out.append(t)
            continue
        d, _ = depth_of(line)
        if d > 0:
            base_depth = d
            block = []
            first = True
            while i < n:
                dd, content = depth_of(lines[i])
                if dd == 0: break
                if not first and dd == base_depth and re.match(r"\[!\w+\][+-]?\s*", content):
                    break
                block.append((dd, content)); i += 1; first = False
            out.append(render_callout_block(block, sprites_prefix, chapter_class=chapter_class))
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline_md(line[4:], sprites_prefix)}</h3>")
        elif line.startswith("## "):
            heading_text = line[3:]
            cap_match = re.match(r"Capítulo\s+(\d+)", heading_text.strip())
            if cap_match:
                chapter_class = CHAPTER_COLOR_CLASS.get(int(cap_match.group(1)))
            out.append(f"<h2>{inline_md(heading_text, sprites_prefix)}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline_md(line[2:], sprites_prefix)}</h1>")
        elif line.strip().startswith("![["):
            m = re.match(r"!\[\[(.+?)\]\]", line.strip())
            img_parts = m.group(1).split("|")
            name = img_parts[0].strip()
            size_style = ""
            if len(img_parts) > 1 and img_parts[-1].strip().isdigit():
                size_style = f' style="width:auto;max-width:{img_parts[-1].strip()}px;"'
            caption = ""
            if i+1 < n and lines[i+1].strip().startswith("*") and lines[i+1].strip().endswith("*"):
                caption = lines[i+1].strip().strip("*"); i += 1
            fig_cls = "fig-alpha" if has_real_transparency(name) else ""
            out.append(f'<figure class="{fig_cls}"><img src="{img_url(name, sprites_prefix)}" alt=""{size_style} loading="lazy">' +
                        (f"<figcaption>{html.escape(caption)}</figcaption>" if caption else "") + "</figure>")
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            items = []
            while i < n and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                items.append(lines[i].strip()[2:])
                i += 1
            only_links = all(re.fullmatch(r"\[\[.+?\]\]", it.strip()) for it in items) and len(items) > 0
            if only_links:
                chips = "".join(f'<span class="link-chip">{inline_md(it, sprites_prefix)}</span>' for it in items)
                out.append(f'<div class="link-row">{chips}</div>')
            else:
                lis = "".join(f"<li>{inline_md(it, sprites_prefix)}</li>" for it in items)
                out.append(f'<ul class="note-list">{lis}</ul>')
            continue
        elif line.strip() == "":
            pass
        else:
            out.append(f"<p>{inline_md(line, sprites_prefix)}</p>")
        i += 1
    fm_html = ""
    if fm:
        SKIP_VALUES = {"n/a", "na", "-", "ninguna", "ninguno", "", "no aplica"}
        SKIP_KEYS = {"confianza"}
        # Nota bilingüe: las CLAVES del frontmatter (tipo/mundo/especie/...) se
        # mantienen siempre en español, incluso en las notas traducidas al
        # inglés (EN/Notas/*.md) -- solo los VALORES se traducen. Por eso cada
        # tabla de abajo acepta tanto el fragmento en español como su
        # equivalente en inglés, para que el icono siga resolviendo bien en
        # ambos idiomas.
        FM_ICONS = {
            "tipo": {
                "personaje": "🧑", "character": "🧑",
                "lugar": "📍", "place": "📍",
                "tema": "💭", "topic": "💭",
                "objeto": "📦", "object": "📦",
                "evento": "📖", "event": "📖",
            },
            "mundo": {
                "lightner": "☀️", "darkner": "🌙",
                "ambos": "🌗", "both": "🌗",
                "planta": "🌱", "plant": "🌱",
            },
            "especie": {},
            "familia": {},
            "grupo": {
                "fun gang": "🎈",
                "colegio": "🏫", "school": "🏫",
                "iglesia": "⛪", "church": "⛪",
                "policía": "👮", "policia": "👮", "police": "👮",
                "ayuntamiento": "🏛️", "city hall": "🏛️", "town hall": "🏛️",
            },
            "estado": {
                "fallecido": "💀", "fallecida": "💀", "muerto": "💀", "muerta": "💀",
                "deceased": "💀", "dead": "💀",
            },
        }
        FM_DEFAULT_ICON = {"tipo": "🏷️", "mundo": "🌍", "especie": "🧬", "familia": "👪", "grupo": "👥", "estado": "⚠️"}
        # Nota bilingue: la CLAVE interna (key_slug, usada en data-key para el
        # CSS de color por categoria) se mantiene siempre en espanol para no
        # romper esas reglas -- pero la ETIQUETA visible ("TIPO", "MUNDO"...)
        # si debe traducirse al ingles en las notas de EN/, igual que ya se
        # traduce el VALOR. Este diccionario es solo de presentacion.
        FM_KEY_LABELS_EN = {
            "tipo": "Type", "mundo": "World", "especie": "Species",
            "familia": "Family", "grupo": "Group", "estado": "Status",
            "pronombres": "Pronouns",
        }

        def _icon_for(key, value):
            key_l = key.lower().strip()
            val_l = value.lower()
            table = FM_ICONS.get(key_l, {})
            for frag, ic in table.items():
                if frag in val_l:
                    return ic
            return FM_DEFAULT_ICON.get(key_l, "🏷️")

        parts = []
        for k, v in fm.items():
            key_slug = k.lower().strip()
            if key_slug in SKIP_KEYS:
                continue
            if v.strip().lower() in SKIP_VALUES:
                continue
            icon = _icon_for(k, v)
            label = FM_KEY_LABELS_EN.get(key_slug, k) if lang == "en" else k
            parts.append(
                f'<span class="fm-badge" data-key="{html.escape(key_slug)}">'
                f'<span class="fm-icon">{icon}</span><b>{html.escape(label)}</b><em>{html.escape(v[:60])}</em></span>'
            )
        if parts:
            fm_html = f'<div class="fm-bar">{"".join(parts)}</div>'
    return fm_html + "\n".join(out)

