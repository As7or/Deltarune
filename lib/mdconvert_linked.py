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
    return None

def img_url(name, sprites_prefix):
    return sprites_prefix + urllib.parse.quote(resolve_sprite_path(name))

def inline_md(text, sprites_prefix, force_small=False):
    # Las imagenes y wikilinks se resuelven ANTES de escapar el texto (para que
    # nombres de archivo con apostrofes, & u otros caracteres no se corrompan al
    # pasar por html.escape). Se guardan como placeholders y se reinsertan al final.
    placeholders = {}
    def stash(fragment):
        key = f"\x00PH{len(placeholders)}\x00"
        placeholders[key] = fragment
        return key

    def img_sub(m):
        inner = m.group(1)
        name = inner.split("|")[0].strip()
        if force_small:
            cls = "inline-img-small"
        else:
            cls = "inline-img inline-img-alpha" if has_real_transparency(name) else "inline-img"
        return stash(f'<img class="{cls}" src="{img_url(name, sprites_prefix)}" alt="" loading="lazy">')
    text = re.sub(r"!\[\[(.+?)\]\]", img_sub, text)

    def wikilink_sub(m):
        inner = m.group(1)
        target = inner.split("|")[0].strip()
        display = inner.split("|")[-1].strip()
        submap_m = re.match(r"^Submapas/(.+?)\.canvas$", target)
        if submap_m:
            slug = slugify(submap_m.group(1))
            return stash(f'<a class="wikilink submap-link" href="../submaps/{urllib.parse.quote(slug)}.html">{html.escape(display)}</a>')
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

def parse_table(block_lines, sprites_prefix):
    rows = [l for l in block_lines if l.strip().startswith("|")]
    if len(rows) < 2:
        return None
    header = split_row(rows[0])
    body_rows = rows[2:]
    small_cols = {i for i, h in enumerate(header) if "talksprite" in h.lower()}
    out = ['<table class="note-table">', "<tr>"]
    for h in header:
        out.append(f"<th>{inline_md(h, sprites_prefix)}</th>")
    out.append("</tr>")
    for r in body_rows:
        cells = split_row(r)
        out.append("<tr>")
        for idx, c in enumerate(cells):
            out.append(f"<td>{inline_md(c, sprites_prefix, force_small=(idx in small_cols))}</td>")
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

def render_callout_block(lines, sprites_prefix, depth=0):
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
            body_parts.append(render_callout_block(nested, sprites_prefix, depth+1))
            continue
        if content.strip().startswith("|"):
            table_block = []
            while i < len(lines) and lines[i][0] == base_depth and lines[i][1].strip().startswith("|"):
                table_block.append(lines[i][1])
                i += 1
            t = parse_table(table_block, sprites_prefix)
            if t:
                body_parts.append(t)
            continue
        if re.match(r"^\s*[-*]\s+", content):
            bullet_lines = []
            while i < len(lines) and lines[i][0] == base_depth and re.match(r"^\s*[-*]\s+", lines[i][1]):
                bullet_lines.append(re.sub(r"^\s*[-*]\s+", "", lines[i][1]))
                i += 1
            items = "".join(f"<li>{inline_md(b, sprites_prefix, force_small=force_small_here)}</li>" for b in bullet_lines)
            body_parts.append(f"<ul>{items}</ul>")
            continue
        if content.strip():
            body_parts.append(f"<p>{inline_md(content, sprites_prefix, force_small=force_small_here)}</p>")
        i += 1
    body = "".join(body_parts)
    title_html = f'<div class="callout-title">{inline_md(title, sprites_prefix)}</div>' if title else ""
    import importlib
    try:
        from note_page_template import rotation_for
    except ImportError:
        rotation_for = lambda t: 0
    rot = rotation_for((title or ctype) + str(depth)) * (1.3 if depth > 0 else 1)
    return (f'<div class="callout callout-{ctype}" style="transform:rotate({rot}deg);">'
            f'{title_html}<div class="callout-body">{body}</div></div>')

def convert_note_linked(md_text, sprites_prefix="../Sprites/"):
    """Convierte una nota .md de Obsidian a HTML enlazando imagenes como
    archivos reales (sprites_prefix + nombre), sin base64."""
    lines = md_text.split("\n")
    fm, lines = parse_frontmatter(lines)
    out = []
    i = 0
    n = len(lines)
    last_heading = ""
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
            out.append(render_callout_block(block, sprites_prefix))
            continue
        if re.match(r"^\s*[-*]\s+", line):
            bullet_lines = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                bullet_lines.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            if last_heading == "relacionado":
                tags = "".join(
                    f'<span class="related-tag">🧷<span class="related-tag-label">{inline_md(b, sprites_prefix)}</span></span>'
                    for b in bullet_lines
                )
                out.append(f'<div class="related-web">{tags}</div>')
            else:
                items = "".join(f"<li>{inline_md(b, sprites_prefix)}</li>" for b in bullet_lines)
                out.append(f"<ul>{items}</ul>")
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline_md(line[4:], sprites_prefix)}</h3>")
        elif line.startswith("## "):
            heading_text = line[3:].strip()
            last_heading = re.sub(r"[^a-záéíóúñ]", "", heading_text.lower())
            out.append(f"<h2>{inline_md(heading_text, sprites_prefix)}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline_md(line[2:], sprites_prefix)}</h1>")
        elif last_heading == "submapa" and "Submapas/" in line and "[[" in line:
            m = re.search(r"\[\[Submapas/(.+?)\.canvas(?:\|(.+?))?\]\]", line)
            if m:
                slug = slugify(m.group(1))
                label = m.group(2) or "Abrir submapa gráfico"
                out.append(
                    '<a class="submap-cta" href="../submaps/' + urllib.parse.quote(slug) + '.html">'
                    '<span class="submap-cta-icon">🗺️</span>'
                    '<span class="submap-cta-text"><span class="submap-cta-title">' + html.escape(label) + '</span>'
                    '<span class="submap-cta-sub">Explora sus conexiones en su propio corcho</span></span>'
                    '</a>'
                )
            else:
                out.append(f"<p>{inline_md(line, sprites_prefix)}</p>")
        elif line.strip().startswith("![["):
            m = re.match(r"!\[\[(.+?)\]\]", line.strip())
            name = m.group(1).split("|")[0].strip()
            caption = ""
            if i+1 < n and lines[i+1].strip().startswith("*") and lines[i+1].strip().endswith("*"):
                caption = lines[i+1].strip().strip("*"); i += 1
            fig_cls = "fig-alpha" if has_real_transparency(name) else ""
            out.append(f'<figure class="{fig_cls}"><img src="{img_url(name, sprites_prefix)}" alt="" loading="lazy">' +
                        (f"<figcaption>{html.escape(caption)}</figcaption>" if caption else "") + "</figure>")
        elif line.strip() == "":
            pass
        else:
            out.append(f"<p>{inline_md(line, sprites_prefix)}</p>")
        i += 1
    fm_html = ""
    if fm:
        FM_ICONS = {"tipo": "🎭", "mundo": "🌍", "especie": "🧬", "familia": "👪",
                    "confianza": "🔍", "pronombres": "🏷️"}

        def _badge(k, v):
            icon = FM_ICONS.get(k.lower(), "📌")
            cls = "fm-badge"
            vlow = v.lower()
            if k.lower() == "mundo":
                if "ambos" in vlow:
                    cls += " w-ambos"
                elif "lightner" in vlow:
                    cls += " w-lightner"
                elif "darkner" in vlow:
                    cls += " w-darkner"
                else:
                    cls += " w-na"
            elif k.lower() == "confianza":
                if "oficial" in vlow:
                    cls += " c-oficial"
                elif "fuerte" in vlow:
                    cls += " c-fuerte"
                elif "mixta" in vlow:
                    cls += " c-mixta"
                elif "bil" in vlow:
                    cls += " c-debil"
            return (f'<span class="{cls}"><i>{icon}</i>'
                    f'<b>{html.escape(k)}</b>{html.escape(v[:60])}</span>')

        badges = "".join(_badge(k, v) for k, v in fm.items())
        fm_html = f'<div class="fm-bar">{badges}</div>'
    return fm_html + "\n".join(out)

