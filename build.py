#!/usr/bin/env python3
"""
Genera la web del Corcho (corcho-principal.html + Sprites/ + notes/ + submaps/)
a partir de un vault de Obsidian.

Uso:
    python build.py /ruta/a/tu/vault/Deltarune Teorias  --out dist
    python build.py /ruta/a/tu/vault.zip                --out dist

El vault (carpeta o zip) debe contener, en algún punto:
    - un archivo "*.canvas" (el corcho principal, con nodos tipo "group")
    - Notas/*.md
    - Submapas/*.canvas   (opcional)
    - Sprites/            (imagenes, puede tener subcarpetas)

Notas por si vienes de otra conversación / sesión de Claude y no tienes
todo el contexto: este script es la versión "de una sola pieza" de todos los
scripts que se fueron escribiendo a mano, turno a turno, en el chat original.
Si algo no encaja con el vault real, lo más fiable es abrir lib/board_data.py,
lib/mdconvert_linked.py y lib/build_submap.py y mirar el formato exacto de
canvas/notas que se está asumiendo (basado en la convención descrita en
"Contexto Principal.md" del propio proyecto).
"""
import argparse, os, sys, shutil, zipfile, tempfile, html, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))

from encoding_fix import fix_encoding
import board_data
import board_template
from board_template import BOARD_TEMPLATE
import mdconvert_linked
from mdconvert_linked import convert_note_linked, slugify as md_slugify
import note_page_template
import build_submap

# Notas a las que aplicar el tema "pergamino" en vez del postit normal.
# Añade aquí el nombre exacto de la nota (sin .md) si quieres el mismo efecto
# para otras notas especiales.
PARCHMENT_NOTES = {"Profecía"}
WET_NOTES = {"Lake"}
RUSTED_NOTES = {"Shelter"}
CRYSTAL_NOTES = {"Cristal Oscuro"}
UNDERTALE_NOTES = {"Conexión Undertale"}
FOUNTAIN_NOTES = {"Fuentes Oscuras"}
GASTER_NOTES = {"Gaster (W. D. Gaster)"}


def find_vault_root(path):
    """Si path es un .zip lo descomprime a una carpeta temporal; si es una
    carpeta la usa tal cual. Devuelve la carpeta que contiene Notas/."""
    if os.path.isfile(path) and path.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp(prefix="corcho_vault_")
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        root = tmp
    else:
        root = path

    renamed, dropped = fix_encoding(root)
    if dropped:
        print(f"Aviso: se encontraron {len(dropped)} archivo(s) duplicados por encoding roto (mismo archivo exportado dos veces con corrupciones distintas). Se conservó la versión más reciente de cada uno:")
        for old_path, kept_path in dropped:
            print(f"   - descartado: {old_path}")
            print(f"     conservado: {kept_path}")

    # buscar la carpeta que tiene Notas/ dentro (puede estar anidada)
    for dirpath, dirnames, _ in os.walk(root):
        if "Notas" in dirnames:
            return dirpath
    raise SystemExit(f"No se encontró ninguna carpeta 'Notas' dentro de {path}")


def find_main_canvas(vault_dir):
    """Elige el .canvas principal: el que tenga más nodos, ignorando los que
    estén dentro de Submapas/."""
    candidates = []
    for fname in os.listdir(vault_dir):
        if fname.endswith(".canvas"):
            candidates.append(os.path.join(vault_dir, fname))
    if not candidates:
        raise SystemExit(f"No se encontró ningún .canvas principal en {vault_dir}")
    best, best_n = None, -1
    for c in candidates:
        try:
            d = json.load(open(c, encoding="utf-8"))
            n = len(d.get("nodes", []))
        except Exception:
            n = -1
        if n > best_n:
            best, best_n = c, n
    return best


# Notas de indice sueltas en la raiz del vault (una versión ES y otra EN,
# ambas con el MISMO stem de archivo -- solo cambia el idioma del contenido y
# del blurb -- para no tener que tocar ninguna lógica de enlaces/slugs).
EXTRA_ROOT_NOTES = ["Conexiones del Corcho.md", "Objetos del Mundo Oscuro.md"]
EXTRA_ROOT_BLURBS_ES = {
    "Conexiones del Corcho": "Explicación completa de cada línea del corcho: por qué cada conexión "
                               "está clasificada como oficial, teoría fuerte o teoría débil, organizada por bloques.",
    "Objetos del Mundo Oscuro": "Identidades reales de los personajes/objetos del Mundo Oscuro, "
                                  "Cap.1-5 — cada Darkner tiene un equivalente en el Mundo Claro.",
}
EXTRA_ROOT_BLURBS_EN = {
    "Conexiones del Corcho": "A full explanation of every line on the corkboard: why each connection "
                               "is classified as official, strong theory, or weak theory, organized by block.",
    "Objetos del Mundo Oscuro": "The real-world identities behind the Dark World's characters/objects, "
                                  "Ch.1-5 — every Darkner has a Light World counterpart.",
}

# Nota bilingue: el STEM (nombre de archivo) de una nota se mantiene SIEMPRE
# identico entre ES y EN -- incluso cuando el vault en espanol le puso un
# nombre en espanol ("Cristal Oscuro", "Profecía"...) -- porque los wikilinks
# (KNOWN_NOTES) y los sets de tema (PARCHMENT_NOTES, GASTER_NOTES...)
# resuelven por ese nombre exacto y cambiarlo rompería enlaces sin tocar
# codigo en cada sitio. Pero el usuario SI espera ver un titulo en ingles
# en la pestaña del navegador de la version EN, incluso para esas notas
# mezcladas (algunas ya tenian nombre en ingles como "Lake"/"Shelter", otras
# se quedaron en español al crear el vault). Este diccionario es SOLO de
# presentacion (el <title> de la pagina, y tambien la etiqueta visible de la
# tarjeta del corcho -- ver board_data.EN_TITLE_OVERRIDES, MISMO diccionario,
# una sola fuente de verdad para no desincronizar los dos sitios donde se usa):
# no toca el archivo, el slug ni el data-key de ningun badge. Las notas que sí
# tienen su propio "# Titulo" en ingles al principio del cuerpo (como los dos
# EXTRA_ROOT_NOTES) no lo necesitan -- ese H1 ya se usa como fallback
# automatico, ver build_lang().
EN_TITLE_OVERRIDES = board_data.EN_TITLE_OVERRIDES


def build_lang(vault_dir, notes_dir, submaps_dir, main_canvas, out_dir, lang,
                sprites_dir, sprites_prefix_notes, sprites_prefix_board,
                thumbs_out_dir, extra_root_blurbs, copy_sprites=False):
    """Genera un idioma completo del sitio (es o en) en out_dir. Reutiliza
    siempre el mismo Sprites/ fisico (sprites_dir): solo cambia el PREFIJO
    relativo con el que cada tipo de pagina referencia esas imagenes, segun
    la profundidad real de out_dir (out_dir/ para es, out_dir/en/ para en)."""
    os.makedirs(out_dir, exist_ok=True)
    out_notes = os.path.join(out_dir, "notes")
    out_submaps = os.path.join(out_dir, "submaps")
    for d in (out_notes, out_submaps):
        os.makedirs(d, exist_ok=True)

    if copy_sprites:
        out_sprites = os.path.join(out_dir, "Sprites")
        if os.path.isdir(sprites_dir):
            if os.path.isdir(out_sprites):
                shutil.rmtree(out_sprites)
            shutil.copytree(sprites_dir, out_sprites)
        print(f"[{lang}] Sprites copiados.")

    # Notas (incluye Notas/ + las notas de indice sueltas en la raiz del
    # vault de este idioma, para que la tira de periodico del hub enlace)
    note_files = [(fname, notes_dir) for fname in os.listdir(notes_dir) if fname.endswith(".md")]
    for fname in EXTRA_ROOT_NOTES:
        if os.path.isfile(os.path.join(vault_dir, fname)):
            note_files.append((fname, vault_dir))

    stems = [os.path.splitext(fname)[0] for fname, _ in note_files]
    mdconvert_linked.KNOWN_NOTES = {s: md_slugify(s) for s in stems}
    mdconvert_linked.SPRITES_ABS_DIR = sprites_dir

    index_cards = []
    for fname, srcdir in sorted(note_files):
        stem = fname[:-3]
        slug = md_slugify(stem)
        text = open(os.path.join(srcdir, fname), encoding="utf-8").read()
        body = convert_note_linked(text, sprites_prefix=sprites_prefix_notes, lang=lang)
        theme = (
            "parchment" if stem in PARCHMENT_NOTES else
            "wet" if stem in WET_NOTES else
            "rusted" if stem in RUSTED_NOTES else
            "crystal" if stem in CRYSTAL_NOTES else
            "undertale" if stem in UNDERTALE_NOTES else
            "fountain" if stem in FOUNTAIN_NOTES else
            "gaster" if stem in GASTER_NOTES else
            "postit"
        )
        # Titulo visible de la pagina (pestaña del navegador): en ES siempre
        # el stem tal cual, como antes. En EN, el usuario mezcló nombres de
        # archivo en español y en inglés al crear el vault -- así que en vez
        # de mostrar ese stem en crudo, se busca (en este orden) un titulo
        # explicito en EN_TITLE_OVERRIDES, luego un "# Titulo" real al
        # principio del cuerpo (lo tienen las notas de indice sueltas como
        # "Conexiones del Corcho"), y solo si ninguno existe se usa el stem.
        h1_title = None
        if lang == "en":
            m_title = re.search(r'^#\s+(.+)$', re.sub(r'^---.*?---\n', '', text, flags=re.S), re.M)
            h1_title = m_title.group(1).strip() if m_title else None
            page_title = EN_TITLE_OVERRIDES.get(stem) or h1_title or stem
        else:
            page_title = stem
        page = note_page_template.render_page(html.escape(page_title), body, theme=theme, lang=lang)
        with open(os.path.join(out_notes, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(page)
        if fname in EXTRA_ROOT_NOTES:
            if h1_title is None:
                m_title = re.search(r'^#\s+(.+)$', re.sub(r'^---.*?---\n', '', text, flags=re.S), re.M)
                h1_title = m_title.group(1).strip() if m_title else None
            index_cards.append({
                "title": h1_title or stem,
                "blurb": extra_root_blurbs.get(stem, ""),
                "slug": slug,
            })
    print(f"[{lang}] Notas generadas: {len(note_files)}")

    # Corcho principal
    data = board_data.extract_main_canvas_data(main_canvas, notes_dir, submaps_dir, sprites_dir)
    nodes_html, links_js, board_w, board_h, news_html = board_data.build_board_html(
        data, index_cards=index_cards, sprites_dir=sprites_dir, thumbs_out_dir=thumbs_out_dir,
        sprites_prefix=sprites_prefix_board, lang=lang,
    )
    board_html = BOARD_TEMPLATE.format(
        board_w=board_w, board_h=board_h, nodes_html=nodes_html, links_js=links_js,
        news_html=news_html, lang_switch=board_template.render_lang_switch(lang),
        sprites_prefix=sprites_prefix_board, lang=lang,
        **board_template.render_ui_strings(lang),
    )
    with open(os.path.join(out_dir, "corcho-principal.html"), "w", encoding="utf-8") as f:
        f.write(board_html)
    print(f"[{lang}] Corcho principal generado: {len(data['items'])} nodos, {len(data['edges'])} conexiones.")

    # Submapas
    ok, fail = build_submap.build_all_submaps(submaps_dir, notes_dir, sprites_dir, out_submaps, lang=lang)
    print(f"[{lang}] Submapas generados: {ok} (fallos: {len(fail)})")
    for stem, err in fail:
        print(f"   - {stem}: {err}")


def build(vault_path, out_dir):
    vault_dir = find_vault_root(vault_path)
    notes_dir = os.path.join(vault_dir, "Notas")
    submaps_dir = os.path.join(vault_dir, "Submapas")
    sprites_dir = os.path.join(vault_dir, "Sprites")
    main_canvas = find_main_canvas(vault_dir)

    print(f"Vault detectado en: {vault_dir}")
    print(f"Canvas principal:   {os.path.basename(main_canvas)}")

    out_sprites = os.path.join(out_dir, "Sprites")
    thumbs_out_dir = os.path.join(out_sprites, "_thumbs")

    # 1) Pasada en español (idioma por defecto, en la raiz de out_dir -- el
    #    mismo comportamiento y las mismas rutas de siempre)
    build_lang(
        vault_dir, notes_dir, submaps_dir, main_canvas, out_dir, "es",
        sprites_dir=sprites_dir, sprites_prefix_notes="../Sprites/", sprites_prefix_board="Sprites/",
        thumbs_out_dir=thumbs_out_dir, extra_root_blurbs=EXTRA_ROOT_BLURBS_ES, copy_sprites=True,
    )

    # index.html de redireccion, para que la URL raiz de GitHub Pages
    # (https://usuario.github.io/repo/) caiga directo en el corcho sin
    # tener que escribir /corcho-principal.html a mano.
    index_redirect = '''<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=corcho-principal.html">
<link rel="canonical" href="corcho-principal.html">
<title>Redirigiendo al Corcho…</title>
<style>body{background:#5c5347;color:#e8dcc0;font-family:Georgia,serif;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}</style>
</head><body>
<p>Abriendo el corcho… si no pasa nada, <a href="corcho-principal.html" style="color:#c9982e;">haz clic aquí</a>.</p>
</body></html>'''
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_redirect)
    print("index.html de redireccion generado.")

    # 2) Pasada en ingles, SOLO si el vault trae una subcarpeta EN/ con su
    #    propia Notas/ (y opcionalmente Submapas/ y su propio .canvas
    #    principal). Se genera en out_dir/en/, reutilizando el MISMO
    #    Sprites/ ya copiado arriba (no se duplica en disco).
    en_vault_dir = os.path.join(vault_dir, "EN")
    en_notes_dir = os.path.join(en_vault_dir, "Notas")
    en_has_canvas = os.path.isdir(en_vault_dir) and any(
        f.endswith(".canvas") for f in os.listdir(en_vault_dir)
    ) if os.path.isdir(en_vault_dir) else False
    if os.path.isdir(en_vault_dir) and os.path.isdir(en_notes_dir) and en_has_canvas:
        en_submaps_dir = os.path.join(en_vault_dir, "Submapas")
        en_main_canvas = find_main_canvas(en_vault_dir)
        en_out_dir = os.path.join(out_dir, "en")
        build_lang(
            en_vault_dir, en_notes_dir, en_submaps_dir, en_main_canvas, en_out_dir, "en",
            sprites_dir=sprites_dir, sprites_prefix_notes="../../Sprites/", sprites_prefix_board="../Sprites/",
            thumbs_out_dir=thumbs_out_dir, extra_root_blurbs=EXTRA_ROOT_BLURBS_EN, copy_sprites=False,
        )
    else:
        print("(Todavía no hay vault/EN/Notas/ + un .canvas principal en EN/ -- se omite la build en inglés "
              "por ahora. El interruptor Español/English del corcho seguirá ahí, pero solo funcionará "
              "una vez exista esa carpeta completa con el contenido traducido.)")

    print(f"\nListo. Sitio generado en: {os.path.abspath(out_dir)}")
    print(f"Abre {os.path.join(out_dir, 'corcho-principal.html')} en el navegador para verlo en local.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera la web del Corcho desde un vault de Obsidian.")
    parser.add_argument("vault", help="Carpeta del vault (con Notas/, Submapas/, Sprites/) o un .zip exportado")
    parser.add_argument("--out", default="dist", help="Carpeta de salida (por defecto: dist)")
    args = parser.parse_args()
    build(args.vault, args.out)

