"""
Lee el canvas principal (00 Corcho Principal.canvas) y genera:
  - los datos de cada personaje/lugar/tema (items)
  - las conexiones entre ellos (edges)
  - el HTML de las tarjetas del corcho, listo para insertar en la plantilla
"""
import json, os, re, html, random, urllib.parse, unicodedata

def slugify(name):
    nfkd = unicodedata.normalize('NFKD', name)
    return nfkd.encode('ascii', 'ignore').decode('ascii') or name

NODE_COLOR_MAP = {
    "4": "#2e8b46", "6": "#6b3fa0",
    "#6b7280": "#6b7280", "6b7280": "#6b7280",
    "3": "#c9982e", None: "#6b7280",
}
EDGE_COLOR_MAP = {
    "1": "#b23c30", "2": "#c97a3d", "3": "#c9982e",
    "4": "#2e8b46", "5": "#3a9aa6", "6": "#6b3fa0", None: "#8a7a5c",
}


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


def build_board_html(data, scale=0.24, pad=220, card_w=150, index_cards=None):
    """A partir de {"items","edges"} genera (nodes_html, links_js, board_w, board_h)."""
    items = data["items"]
    edges = data["edges"]

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
            link_html = f'<a class="news-link" href="{c["href"]}">Abrir nota →</a>' if c["href"] else ""
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
      <span class="news-eyebrow">Boletín del Corcho</span>
      <span class="news-dateline">Edición especial · Deltarune Teorías</span>
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
        thumb_h = max(min_h, min(max_h, inner_w * aspect))

        if it["img"]:
            src = "Sprites/" + urllib.parse.quote(it["img"])
            img_tag = f'<img src="{src}" alt="" loading="lazy">'
        else:
            img_tag = '<div class="noimg"><i>sin imagen</i></div>'

        note_attr = slugify(it["note"]) if it["note"] else ""
        title = html.escape(it["label"])
        tag = html.escape(it["tag"])
        summary = html.escape(it["summary"])
        approx_card_h = thumb_h + 60
        thumb_class = "thumb thumb-dark" if it.get("dark") else "thumb"

        submap_badge = ""
        if it.get("submap"):
            submap_url = "submaps/" + urllib.parse.quote(slugify(it["submap"])) + ".html"
            submap_badge = (f'<a class="submap-badge" href="{submap_url}" '
                             f'title="Ver submapa de {title}" onmousedown="event.stopPropagation()">🗺️</a>')

        if it["label"] == "Profecía":
            node_html.append(f'''
  <div class="node node-scroll" data-id="{nid}" data-note="{note_attr}" style="left:{x-card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="scroll">
      <div class="roll roll-top"><div class="frizz f1"></div><div class="frizz f2"></div><div class="frizz f3"></div></div>
      <div class="sheet">
        <div class="tear left t1"></div><div class="tear left t2"></div>
        <div class="tear right t1"></div><div class="tear right t2"></div>
        <div class="{thumb_class}" style="height:{max(60,thumb_h*0.55):.0f}px;">{img_tag}</div>
        <div class="title">{title}</div>
        <div class="summary">{summary}</div>
      </div>
      <div class="roll roll-bottom"><div class="frizz f1"></div><div class="frizz f2"></div><div class="frizz f3"></div></div>
    </div>
  </div>''')
        elif it["label"] == "Lake":
            node_html.append(f'''
  <div class="node node-wet" data-id="{nid}" data-note="{note_attr}" style="left:{x-card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{card_w}px; transform:rotate({rot:.1f}deg);">
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
        elif it["label"] == "Cristal Oscuro":
            node_html.append(f'''
  <div class="node node-crystal" data-id="{nid}" data-note="{note_attr}" style="left:{x-card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{card_w}px; transform:rotate({rot:.1f}deg);">
    {submap_badge}
    <div class="crystal">
      <div class="crystal-facets"></div>
      <div class="{thumb_class} crystal-thumb" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        elif it["label"] == "Shelter":
            node_html.append(f'''
  <div class="node node-rust" data-id="{nid}" data-note="{note_attr}" style="left:{x-card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="rivet"></div>
    {submap_badge}
    <div class="card rust-card">
      <div class="rust-stains"></div><div class="rust-streaks"></div>
      <div class="{thumb_class}" style="height:{thumb_h:.0f}px;">{img_tag}</div>
      <div class="tag">{tag}</div>
      <div class="title">{title}</div>
      <div class="summary">{summary}</div>
    </div>
  </div>''')
        else:
            node_html.append(f'''
  <div class="node" data-id="{nid}" data-note="{note_attr}" style="left:{x-card_w/2:.0f}px; top:{y-approx_card_h/2:.0f}px; width:{card_w}px; transform:rotate({rot:.1f}deg);">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    {submap_badge}
    <div class="card" style="border-top:5px solid {it['color']};">
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

    return "\n".join(node_html) + news_html, links_js, board_w, board_h, ""

