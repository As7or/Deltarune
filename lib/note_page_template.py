import zlib

def rotation_for(text):
    h = zlib.crc32((text or "x").encode("utf-8"))
    return round(((h % 700) - 350) / 100.0 * 0.28, 2)  # entre -0.98 y 0.98 grados

PAGE_CSS = '''
  body{ margin:0; padding:20px 24px 60px; font-family:Georgia, serif; color:#2c2416; background:#e9dfc8; }
  h1{ font-size:22px; border-bottom:2px solid #8a6a3a; padding-bottom:6px;}
  h2{ font-size:17px; color:#5a4020; margin-top:22px; }
  h3{ font-size:15px; color:#5a4020; }
  p{ font-size:15.5px; line-height:1.6; margin:8px 0; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#6b5c46; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:3px; box-shadow:0 2px 6px rgba(0,0,0,0.25); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  figure.fig-small img{ box-shadow:none; width:auto; height:130px; max-width:100%; margin:0 auto; }
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:#fbf6e9; }
  table.note-table th, table.note-table td{ border:1px solid #d8cba8; padding:6px; font-size:13px; text-align:center; vertical-align:top; }
  /* en la tabla comparativa, las figuras de cuerpo entero escalan a una ALTURA
     fija común (no solo un tope máximo), así un sprite con menos "relleno" en
     el PNG también se agranda hasta la misma escala en vez de quedarse pequeño */
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- postits --- */
  .callout{
    position:relative;
    background:#fdf6b2;
    padding:16px 18px 18px;
    margin:22px 14px 26px;
    box-shadow:2px 5px 10px rgba(0,0,0,0.28), inset 0 -14px 20px -14px rgba(0,0,0,0.06);
    border-radius:2px 2px 6px 6px/2px 2px 14px 6px;
    font-family:'Segoe UI', Tahoma, sans-serif;
  }
  .callout::before{
    content:""; position:absolute; top:0; right:0; width:0; height:0;
    border-style:solid; border-width:0 16px 16px 0;
    border-color:transparent rgba(0,0,0,0.13) transparent transparent;
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.03em; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; }

  .callout-info{ background:#cfe6f7; }
  .callout-tip{ background:#d9f0d2; }
  .callout-example{ background:#fdf1b8; }
  .callout-danger{ background:#f8d6d6; }
  .callout-quote{ background:#e6d9f5; }
  .callout-question{ background:#fbe3b0; }

  /* callout anidado: otro postit encima, mas pequeno y con mas sombra */
  .callout .callout{
    margin:14px 4px 6px;
    box-shadow:3px 6px 14px rgba(0,0,0,0.35), inset 0 -10px 16px -10px rgba(0,0,0,0.08);
  }

  .wikilink{ color:#8a3a30; border-bottom:1px dotted #8a3a30; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:#f3ead6; }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px; }
  .fm-badge{ background:#e4d6b0; border-radius:10px; padding:3px 10px; font-size:11px; color:#4a3b20; font-family:'Segoe UI',sans-serif; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border-radius:4px; overflow:hidden; box-shadow:0 3px 10px rgba(0,0,0,0.3); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_PARCHMENT = '''
  body{
    margin:0; padding:26px 30px 60px; font-family:'Palatino Linotype', Georgia, serif; color:#3f3120;
    background-color:#c9ad74;
    background-image:
      radial-gradient(ellipse at 18% 12%, rgba(120,90,40,0.20) 0, transparent 45%),
      radial-gradient(ellipse at 82% 28%, rgba(90,60,20,0.16) 0, transparent 42%),
      radial-gradient(ellipse at 55% 92%, rgba(70,45,15,0.22) 0, transparent 50%),
      radial-gradient(ellipse at 5% 80%, rgba(90,60,20,0.14) 0, transparent 40%),
      repeating-radial-gradient(circle at 50% 50%, rgba(90,60,20,0.05) 0px, transparent 2px, transparent 5px);
  }
  h1{ font-size:23px; color:#4a3418; border-bottom:2px solid #8a6a3a; padding-bottom:8px; letter-spacing:.03em; }
  h2{ font-size:17px; color:#5a4020; margin-top:24px; font-variant:small-caps; letter-spacing:.04em; }
  h3{ font-size:15px; color:#5a4020; font-variant:small-caps; }
  p{ font-size:15.5px; line-height:1.65; margin:8px 0; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#5a4520; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:2px; box-shadow:0 2px 8px rgba(40,25,5,0.35); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:#e9d9a8; }
  table.note-table th, table.note-table td{ border:1px solid #b8985e; padding:6px; font-size:13px; text-align:center; vertical-align:top; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- pergaminos enrollados, tipo rollo antiguo --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse at 50% 45%, #f3e3b2 0%, #ecd89e 30%, #d8b678 58%, #a97b46 82%, #6e4526 100%),
      radial-gradient(ellipse at 30% 35%, rgba(255,240,200,0.25) 0, transparent 45%),
      linear-gradient(124deg, transparent 30%, rgba(90,60,20,0.08) 31%, transparent 34%),
      linear-gradient(38deg, transparent 55%, rgba(90,60,20,0.07) 56%, transparent 60%),
      linear-gradient(160deg, transparent 15%, rgba(120,85,35,0.06) 16%, transparent 20%),
      repeating-linear-gradient(91deg, rgba(90,60,20,0.05) 0px, transparent 2px, transparent 5px),
      repeating-linear-gradient(4deg, rgba(90,60,20,0.04) 0px, transparent 3px, transparent 7px);
    padding:34px 26px 36px;
    margin:36px 10px 42px;
    border-left:8px solid #8a6a3a;
    box-shadow:0 6px 18px rgba(40,25,5,0.4), inset 0 0 60px rgba(90,55,25,0.4);
    font-family:'Palatino Linotype', Georgia, serif;
    clip-path: polygon(
      0% 2%, 7% 0%, 15% 1.5%, 23% 0.5%, 31% 2%, 39% 0%, 47% 1.5%, 55% 0.5%, 63% 2%, 71% 0%, 79% 1.5%, 87% 0.5%, 94% 1.5%, 100% 0.5%,
      99% 8%, 100% 15%, 98.5% 23%, 100% 31%, 99% 39%, 100% 47%, 98.5% 55%, 100% 63%, 99% 71%, 100% 79%, 98.5% 87%, 100% 94%, 99.5% 100%,
      92% 99%, 84% 100%, 76% 98.5%, 68% 100%, 60% 99%, 52% 100%, 44% 98.5%, 36% 100%, 28% 99%, 20% 100%, 12% 98.5%, 4% 100%, 0% 99%,
      1% 92%, 0% 84%, 1.5% 76%, 0% 68%, 1% 60%, 0% 52%, 1.5% 44%, 0% 36%, 1% 28%, 0% 20%, 1.5% 12%, 0% 6%
    );
  }
  .callout::before, .callout::after{
    content:""; position:absolute; left:-2px; right:-2px; height:26px; z-index:1;
    background:
      repeating-linear-gradient(135deg, transparent 0 7px, #5a3416 7px 8.5px),
      repeating-linear-gradient(45deg, transparent 0 7px, #5a3416 7px 8.5px),
      linear-gradient(180deg, #caa267, #8a6236 45%, #6e4a26 55%, #a37e46);
    box-shadow:0 3px 8px rgba(30,18,6,0.5);
  }
  .callout::before{ top:-13px; }
  .callout::after{ bottom:-13px; transform:scaleY(-1); }
  .callout-title{
    font-weight:bold; margin-bottom:8px; font-size:14.5px; color:#4a3418;
    text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid rgba(90,60,20,.35); padding-bottom:5px;
    position:relative; z-index:2;
  }
  .callout-body{ position:relative; z-index:2; }
  .callout-body p{ margin:6px 0; font-size:15px; line-height:1.55; color:#3f3120; }

  .callout-info{ border-left-color:#3a7bd5; }
  .callout-tip{ border-left-color:#2e8b57; }
  .callout-example{ border-left-color:#8a6a3a; }
  .callout-danger{ border-left-color:#b23c30; }
  .callout-quote{ border-left-color:#6b3fa0; }
  .callout-question{ border-left-color:#c9982e; }

  .callout .callout{
    margin:30px 14px 18px;
    box-shadow:0 8px 22px rgba(30,18,4,0.5), inset 0 0 46px rgba(90,55,25,0.44);
  }

  .wikilink{ color:#7a2e22; border-bottom:1px dotted #7a2e22; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(122,46,34,0.12); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px; }
  .fm-badge{ background:#d8bd82; border:1px solid #b8985e; border-radius:10px; padding:3px 10px; font-size:10.5px; color:#4a3b20; font-family:'Segoe UI',sans-serif; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border-radius:4px; overflow:hidden; box-shadow:0 3px 12px rgba(40,25,5,0.4); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_TMPL = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
'''

def render_page(title_escaped, body_html, theme="postit"):
    css = PAGE_CSS_PARCHMENT if theme == "parchment" else PAGE_CSS
    return PAGE_TMPL.format(title=title_escaped, css=css, body=body_html)

