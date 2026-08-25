import zlib

def rotation_for(text):
    h = zlib.crc32((text or "x").encode("utf-8"))
    return round(((h % 700) - 350) / 100.0 * 0.28, 2)  # entre -0.98 y 0.98 grados

def torn_variant_for(text):
    """Numero 1-4 deterministico (segun el texto) que elige una de las 4
    variantes de borde rasgado irregular (callout-torn-1..4) del tema
    Gaster, para que distintos postits de la misma nota no compartan
    siempre el mismo recorte."""
    h = zlib.crc32(((text or "x") + "|torn").encode("utf-8"))
    return (h % 4) + 1

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
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:#fbf6e9; }
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

  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{
    position:relative; display:inline-flex; align-items:baseline; gap:5px;
    background:linear-gradient(180deg, #fffcf4, #f0e3bd);
    border:1px solid #c9b783; border-radius:13px; padding:4px 12px 4px 10px;
    font-size:11px; color:#4a3b20; font-family:'Segoe UI',sans-serif;
    box-shadow:0 1px 3px rgba(60,45,15,0.2), inset 0 1px 0 rgba(255,255,255,0.6);
  }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#8a6a3a; flex-shrink:0; align-self:center; }
  .fm-badge b{ font-weight:700; color:#2c2416; text-transform:uppercase; font-size:9.5px; letter-spacing:.03em;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #a8672e; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #3a7ba0; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #4a8a5a; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #9a4a7a; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #c9982e; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:#fdf6e3; border:1px solid #d8c48a; border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#8a3a30 !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }

  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{
    display:inline-block; background:#fdf6e3; border:1px solid #d8c48a; border-radius:8px;
    padding:5px 13px; box-shadow:1px 2px 4px rgba(60,45,15,0.18);
    transform:rotate(-0.6deg);
  }
  .link-chip:nth-child(3n+1){ transform:rotate(0.7deg); }
  .link-chip:nth-child(3n+2){ transform:rotate(-0.9deg); }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; }
  .link-chip:hover{ background:#f3ead0; box-shadow:1px 3px 6px rgba(60,45,15,0.28); }

  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:15px; line-height:1.55; margin:4px 0; }

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
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:#e9d9a8; }
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

  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{
    position:relative; display:inline-flex; align-items:baseline; gap:5px;
    background:linear-gradient(180deg, #e9d4a0, #cfa860);
    border:1px solid #96773f; border-radius:12px; padding:4px 12px 4px 10px;
    font-size:10.5px; color:#3f2d10; font-family:'Segoe UI',sans-serif;
    box-shadow:0 1px 3px rgba(30,18,4,0.35), inset 0 1px 0 rgba(255,240,200,0.4);
  }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#5a3416; flex-shrink:0; align-self:center; }
  .fm-badge b{ font-weight:700; color:#2c1c08; text-transform:uppercase; font-size:9px; letter-spacing:.03em;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #8a5420; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #2e6280; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #3a6b3e; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #7a3560; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #a87820; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:#e9d4a0; border:1px solid #96773f; border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#7a2e22 !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }

  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{
    display:inline-block; background:#d8bd82; border:1px solid #96773f; border-radius:6px;
    padding:5px 13px; box-shadow:1px 2px 5px rgba(30,18,4,0.35);
    transform:rotate(-0.5deg);
  }
  .link-chip:nth-child(3n+1){ transform:rotate(0.6deg); }
  .link-chip:nth-child(3n+2){ transform:rotate(-0.8deg); }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; color:#3f2d10; }
  .link-chip:hover{ background:#cbae72; }

  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:15px; line-height:1.55; margin:4px 0; }

  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border-radius:4px; overflow:hidden; box-shadow:0 3px 12px rgba(40,25,5,0.4); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_RUSTED = '''
  body{
    margin:0; padding:24px 26px 60px; font-family:'Consolas','Courier New',monospace; color:#e8dcc0;
    background-color:#2b1f16;
    background-image:
      radial-gradient(ellipse at 12% 15%, rgba(200,90,30,0.32) 0, transparent 38%),
      radial-gradient(ellipse at 88% 10%, rgba(160,55,15,0.3) 0, transparent 36%),
      radial-gradient(ellipse at 65% 40%, rgba(120,40,10,0.22) 0, transparent 40%),
      radial-gradient(ellipse at 20% 70%, rgba(190,80,25,0.26) 0, transparent 40%),
      radial-gradient(ellipse at 80% 85%, rgba(150,50,15,0.28) 0, transparent 42%),
      radial-gradient(ellipse at 45% 92%, rgba(200,100,35,0.2) 0, transparent 38%),
      repeating-linear-gradient(90deg, rgba(0,0,0,0.08) 0px, transparent 2px, transparent 5px),
      repeating-linear-gradient(4deg, rgba(0,0,0,0.06) 0px, transparent 3px, transparent 8px);
      background-repeat: repeat;
    background-size: 560px 700px;
  }
  h1{ font-size:21px; color:#f0dcc0; border-bottom:3px solid #b5622e; padding-bottom:8px; letter-spacing:.02em; text-transform:uppercase; text-shadow:0 0 10px rgba(200,100,40,0.3); }
  h2{ font-size:16px; color:#e0975a; margin-top:24px; text-transform:uppercase; letter-spacing:.05em; }
  h3{ font-size:14px; color:#e0975a; }
  p{ font-size:14.5px; line-height:1.65; margin:8px 0; color:#d9cdb2; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; filter:saturate(0.8) sepia(0.12); }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12px; font-style:italic; color:#b5a688; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border:1px solid #5a4a38; box-shadow:0 3px 10px rgba(0,0,0,0.5); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:#3a2f28; }
  table.note-table th, table.note-table td{ border:1px solid #5a4a38; padding:6px; font-size:12.5px; text-align:center; vertical-align:top; color:#d9cdb2; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- carteles de acero oxidado, simplemente atornillados al corcho: placa
     metalica rectangular (sin bordes rasgados de papel) con un remache
     visible en cada esquina y textura de chapa/costuras de panel. El remachado
     va en un ::before propio (no en el "background" de .callout) para que no
     desaparezca cuando .callout-info/tip/example/... pisa ese "background"
     con su propio color por tipo de aviso. --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse at 15% 20%, rgba(180,80,25,0.35) 0%, transparent 30%),
      radial-gradient(ellipse at 85% 75%, rgba(160,60,15,0.3) 0%, transparent 32%),
      radial-gradient(ellipse at 60% 10%, rgba(140,50,10,0.25) 0%, transparent 28%),
      linear-gradient(160deg, #4a3d30 0%, #3a2f26 40%, #2e2620 100%);
    padding:26px 26px 24px; margin:24px 8px 28px;
    border:2px solid #6b5842;
    border-radius:3px;
    box-shadow:2px 5px 14px rgba(0,0,0,0.5), inset 0 0 30px rgba(0,0,0,0.35), inset 0 0 50px rgba(150,60,20,0.12), inset 0 0 0 1px rgba(0,0,0,0.4);
  }
  .callout::before{
    content:""; position:absolute; inset:0; z-index:1; pointer-events:none; border-radius:inherit;
    background:
      radial-gradient(circle 5px at 17px 17px, #d0c0a0 0%, #6b5a3e 58%, transparent 64%),
      radial-gradient(circle 5px at calc(100% - 17px) 17px, #d0c0a0 0%, #6b5a3e 58%, transparent 64%),
      radial-gradient(circle 5px at 17px calc(100% - 17px), #d0c0a0 0%, #6b5a3e 58%, transparent 64%),
      radial-gradient(circle 5px at calc(100% - 17px) calc(100% - 17px), #d0c0a0 0%, #6b5a3e 58%, transparent 64%),
      repeating-linear-gradient(90deg, rgba(0,0,0,.14) 0 2px, transparent 2px 26px),
      repeating-linear-gradient(0deg, rgba(0,0,0,.1) 0 2px, transparent 2px 26px);
  }
  .callout-title{ position:relative; z-index:2; font-weight:bold; margin-bottom:8px; font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:#e0975a; }
  .callout-body{ position:relative; z-index:2; }
  .callout-body p{ margin:5px 0; font-size:14px; line-height:1.55; color:#d9cdb2; }
  .callout-info{ background:radial-gradient(ellipse at 20% 20%, rgba(160,70,20,0.28) 0%, transparent 32%), linear-gradient(160deg,#38424a,#2a3238); }
  .callout-tip{ background:radial-gradient(ellipse at 80% 25%, rgba(160,70,20,0.28) 0%, transparent 32%), linear-gradient(160deg,#354a38,#28362a); }
  .callout-example{ background:radial-gradient(ellipse at 15% 75%, rgba(180,85,25,0.32) 0%, transparent 32%), linear-gradient(160deg,#4a3d30,#3a2f26); }
  .callout-danger{ background:radial-gradient(ellipse at 75% 20%, rgba(190,90,25,0.35) 0%, transparent 32%), linear-gradient(160deg,#4a2e28,#3a221e); }
  .callout-quote{ background:radial-gradient(ellipse at 25% 80%, rgba(160,70,20,0.28) 0%, transparent 32%), linear-gradient(160deg,#3d3548,#2c2736); }
  .callout-question{ background:linear-gradient(160deg,#4a3d20,#3a2f18); }
  .callout .callout{ margin:14px 4px 6px; box-shadow:3px 6px 16px rgba(0,0,0,0.6); }

  .wikilink{ color:#e0975a; border-bottom:1px dotted #e0975a; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(224,151,90,0.15); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:#4a3d30; border:1px solid #6b5842; border-radius:3px; padding:4px 11px; font-size:10.5px; color:#d9cdb2; font-family:'Consolas',monospace; }
  .fm-badge::before{ content:"▪"; color:#d68b52; }
  .fm-badge b{ font-weight:700; color:#e0975a; text-transform:uppercase; font-size:9px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #d68b52; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #7a9ab0; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #8ab06a; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #b06a8a; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #e0b040; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:#3a2f26; border:1px solid #6b5842; border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#e0975a !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:#3a2f26; border:1px solid #6b5842; border-radius:3px; padding:5px 13px; box-shadow:1px 2px 5px rgba(0,0,0,0.4); }
  .link-chip a.wikilink{ font-size:13px; font-weight:600; border-bottom:none; }
  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:14.5px; line-height:1.55; margin:4px 0; color:#d9cdb2; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border:1px solid #6b5842; overflow:hidden; }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_WET = '''
  body{
    margin:0; padding:24px 26px 60px; font-family:Georgia, serif; color:#3a3220;
    background-color:#e8e0c4;
    background-image:
      /* pliegues de papel, muy marcados */
      linear-gradient(112deg, transparent 28%, rgba(255,255,255,0.5) 29%, rgba(90,75,30,0.22) 30%, transparent 32%),
      linear-gradient(75deg, transparent 46%, rgba(255,255,255,0.45) 47%, rgba(90,75,30,0.18) 48%, transparent 50%),
      linear-gradient(140deg, transparent 12%, rgba(255,255,255,0.4) 13%, rgba(90,75,30,0.15) 14%, transparent 16%),
      linear-gradient(160deg, transparent 20%, rgba(90,75,30,0.18) 21%, transparent 23%),
      linear-gradient(35deg, transparent 58%, rgba(255,255,255,0.4) 59%, rgba(90,75,30,0.15) 60%, transparent 62%),
      linear-gradient(20deg, transparent 76%, rgba(90,75,30,0.18) 77%, transparent 79%),
      linear-gradient(95deg, transparent 86%, rgba(90,75,30,0.14) 87%, transparent 89%),
      /* manchas de agua amarillentas, como cercos de humedad en papel viejo */
      radial-gradient(circle at 14% 20%, transparent 55%, rgba(196,168,90,0.35) 58%, rgba(196,168,90,0.1) 64%, transparent 68%),
      radial-gradient(circle at 82% 15%, transparent 50%, rgba(196,168,90,0.3) 53%, transparent 60%),
      radial-gradient(circle at 70% 68%, transparent 52%, rgba(196,168,90,0.38) 55%, rgba(196,168,90,0.1) 62%, transparent 66%),
      radial-gradient(circle at 25% 80%, transparent 48%, rgba(196,168,90,0.28) 51%, transparent 58%),
      /* gotas de agua brillantes */
      radial-gradient(circle at 55% 40%, rgba(255,255,255,0.55) 0%, transparent 38%),
      radial-gradient(circle at 35% 92%, rgba(255,255,255,0.5) 0%, transparent 36%),
      radial-gradient(circle at 92% 82%, rgba(255,255,255,0.45) 0%, transparent 34%);
      background-repeat: repeat;
    background-size: 620px 800px;
  }
  h1{ font-size:22px; color:#4a3d18; border-bottom:2px solid #a08840; padding-bottom:8px; }
  h2{ font-size:17px; color:#6b5828; margin-top:22px; }
  h3{ font-size:15px; color:#6b5828; }
  p{ font-size:15.5px; line-height:1.65; margin:8px 0; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#6b5c38; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:2px; box-shadow:0 3px 10px rgba(80,65,20,0.3); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:#ede4c8; }
  table.note-table th, table.note-table td{ border:1px solid #c4b06a; padding:6px; font-size:13px; text-align:center; vertical-align:top; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- papel humedo amarillento, con cerco de mancha visible alrededor --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.35) 0, transparent 40%),
      radial-gradient(ellipse at 78% 30%, transparent 45%, rgba(180,150,70,0.3) 50%, transparent 62%),
      radial-gradient(ellipse at 25% 82%, transparent 50%, rgba(180,150,70,0.26) 55%, transparent 66%),
      linear-gradient(160deg, #f2ead0 0%, #e0d3a4 100%);
    padding:16px 18px 18px; margin:22px 10px 26px;
    box-shadow:2px 6px 14px rgba(90,70,20,0.32), inset 0 -12px 22px -16px rgba(90,70,20,0.2);
    border-radius:3px 12px 3px 14px/10px 3px 14px 3px;
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.03em; color:#4a3d18; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; color:#3a3220; }
  .callout-info{ background:#dce0c8; }
  .callout-tip{ background:#e0dcb8; }
  .callout-example{ background:#f2ead0; }
  .callout-danger{ background:#ecd8c0; }
  .callout-quote{ background:#e6ddc8; }
  .callout-question{ background:#f0e4b8; }
  .callout .callout{ margin:14px 4px 6px; box-shadow:3px 6px 16px rgba(90,70,20,0.4); }

  .wikilink{ color:#8a6a20; border-bottom:1px dotted #8a6a20; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(138,106,32,0.12); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:linear-gradient(180deg,#f2ead0,#e0d3a4); border:1px solid #c4b06a; border-radius:13px; padding:4px 12px; font-size:11px; color:#2c3a3d; font-family:'Segoe UI',sans-serif; }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#a08840; }
  .fm-badge b{ font-weight:700; color:#4a3d18; text-transform:uppercase; font-size:9.5px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #a86a30; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #4a7a8a; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #5a8a4a; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #9a5a70; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #c99a30; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:#e0d3a4; border:1px solid #c4b06a; border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#4a3d18 !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:#e0d3a4; border:1px solid #c4b06a; border-radius:8px; padding:5px 13px; box-shadow:1px 2px 5px rgba(90,70,20,0.28); }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; }
  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:15px; line-height:1.55; margin:4px 0; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border-radius:6px; overflow:hidden; box-shadow:0 3px 10px rgba(20,40,42,0.3); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_CRYSTAL = '''
  body{
    margin:0; padding:24px 26px 60px; font-family:'Segoe UI', Georgia, serif; color:#d8ecff;
    background-color:#140e26;
    background-image:
      radial-gradient(ellipse at 15% 15%, rgba(120,90,220,0.25) 0, transparent 42%),
      radial-gradient(ellipse at 85% 25%, rgba(70,180,220,0.22) 0, transparent 40%),
      radial-gradient(ellipse at 50% 90%, rgba(120,90,220,0.2) 0, transparent 45%);
  }
  h1{ font-size:22px; color:#eaf6ff; border-bottom:2px solid #7de8ff; padding-bottom:8px; text-shadow:0 0 8px rgba(125,232,255,0.4); }
  h2{ font-size:17px; color:#a8d8ff; margin-top:22px; }
  h3{ font-size:15px; color:#a8d8ff; }
  p{ font-size:15.5px; line-height:1.65; margin:8px 0; color:#d8ecff; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#a8c0d8; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:2px; box-shadow:0 0 16px rgba(125,150,255,0.3); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:rgba(30,22,55,0.7); }
  table.note-table th, table.note-table td{ border:1px solid rgba(125,150,255,0.3); padding:6px; font-size:13px; text-align:center; vertical-align:top; color:#d8ecff; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- panel de cristal translucido con brillo --- */
  .callout{
    position:relative;
    background: linear-gradient(160deg, rgba(60,45,100,0.55) 0%, rgba(30,22,55,0.75) 100%);
    padding:16px 18px 18px; margin:22px 8px 26px;
    border:1px solid rgba(125,232,255,0.35);
    box-shadow:0 0 20px rgba(90,120,255,0.2), inset 0 1px 0 rgba(255,255,255,0.08);
    border-radius:4px 14px 4px 14px;
    backdrop-filter: blur(1px);
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.04em; color:#7de8ff; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; color:#d8ecff; }
  .callout-info{ background:linear-gradient(160deg, rgba(45,80,140,0.5), rgba(25,40,70,0.7)); }
  .callout-tip{ background:linear-gradient(160deg, rgba(45,120,100,0.5), rgba(20,55,48,0.7)); }
  .callout-example{ background:linear-gradient(160deg, rgba(100,80,40,0.5), rgba(55,42,20,0.7)); }
  .callout-danger{ background:linear-gradient(160deg, rgba(140,45,60,0.5), rgba(60,20,28,0.7)); }
  .callout-quote{ background:linear-gradient(160deg, rgba(90,60,150,0.5), rgba(40,25,65,0.7)); }
  .callout-question{ background:linear-gradient(160deg, rgba(120,95,30,0.5), rgba(55,42,15,0.7)); }
  .callout .callout{ margin:14px 4px 6px; box-shadow:0 0 22px rgba(90,120,255,0.28); }

  .wikilink{ color:#7de8ff; border-bottom:1px dotted #7de8ff; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(125,232,255,0.12); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:rgba(60,45,100,0.5); border:1px solid rgba(125,232,255,0.35); border-radius:12px; padding:4px 12px; font-size:11px; color:#d8ecff; font-family:'Segoe UI',sans-serif; }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#7de8ff; box-shadow:0 0 5px #7de8ff; }
  .fm-badge b{ font-weight:700; color:#7de8ff; text-transform:uppercase; font-size:9.5px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #e0975a; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #5ab0e0; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #5ee89f; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #c07de8; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #f0d060; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:rgba(45,35,80,0.6); border:1px solid rgba(125,232,255,0.35); border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#7de8ff !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:rgba(45,35,80,0.6); border:1px solid rgba(125,232,255,0.3); border-radius:8px; padding:5px 13px; box-shadow:0 0 10px rgba(90,120,255,0.15); }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; }
  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:15px; line-height:1.55; margin:4px 0; color:#d8ecff; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border-radius:6px; overflow:hidden; border:1px solid rgba(125,232,255,0.3); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_UNDERTALE = '''
  body{ margin:0; padding:24px 26px 60px; font-family:'Courier New',monospace; color:#ffffff; background:#000000; }
  h1{ font-size:20px; color:#ffffff; border-bottom:2px solid #ffffff; padding-bottom:8px; letter-spacing:.03em; }
  h2{ font-size:16px; color:#ffffff; margin-top:24px; letter-spacing:.03em; }
  h3{ font-size:14px; color:#ffffff; }
  p{ font-size:14.5px; line-height:1.7; margin:8px 0; color:#ffffff; }
  img{ max-width:100%; border-radius:0; display:block; margin:8px auto; image-rendering:pixelated; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12px; font-style:italic; color:#aaaaaa; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border:2px solid #ffffff; }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:#000000; }
  table.note-table th, table.note-table td{ border:1px solid #ffffff; padding:6px; font-size:12.5px; text-align:center; vertical-align:top; color:#ffffff; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- caja de dialogo clasica de Undertale --- */
  .callout{
    position:relative; background:#000000; padding:16px 20px; margin:22px 4px 26px;
    border:3px solid #ffffff; border-radius:0;
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:#ffffff; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.6; color:#ffffff; }
  .callout::before{ content:"*"; position:absolute; left:8px; top:14px; color:#ffffff; font-size:16px; }
  .callout-body{ padding-left:14px; }
  .callout-info, .callout-tip, .callout-example, .callout-danger, .callout-quote, .callout-question{ background:#000000; }
  .callout .callout{ margin:14px 2px 6px; border-width:2px; }

  .wikilink{ color:#ffff00; border-bottom:1px dotted #ffff00; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(255,255,0,0.15); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:#000000; border:1px solid #ffffff; border-radius:0; padding:4px 11px; font-size:10.5px; color:#ffffff; font-family:'Courier New',monospace; }
  .fm-badge b{ font-weight:700; color:#ffff00; text-transform:uppercase; font-size:9px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #ffff00; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #00ffff; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #00ff88; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #ff66ff; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #ff8800; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:#000000; border:1px solid #ffffff; border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#ffff00 !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:#000000; border:1px solid #ffffff; border-radius:0; padding:5px 13px; }
  .link-chip a.wikilink{ font-size:13px; font-weight:600; border-bottom:none; }
  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:14.5px; line-height:1.6; margin:4px 0; color:#ffffff; }
  .note-list li::marker{ color:#ffffff; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border:3px solid #ffffff; overflow:hidden; }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_FOUNTAIN = '''
  body{
    margin:0; padding:24px 26px 60px; font-family:'Segoe UI', Georgia, serif; color:#dceef5;
    background-color:#16303d;
    background-image:
      radial-gradient(ellipse at 20% 10%, rgba(90,150,190,0.35) 0, transparent 40%),
      radial-gradient(ellipse at 80% 20%, rgba(60,120,160,0.3) 0, transparent 38%),
      radial-gradient(ellipse at 30% 55%, rgba(70,130,170,0.28) 0, transparent 42%),
      radial-gradient(ellipse at 75% 65%, rgba(50,100,140,0.3) 0, transparent 40%),
      radial-gradient(ellipse at 45% 90%, rgba(80,140,180,0.26) 0, transparent 42%),
      repeating-linear-gradient(95deg, rgba(255,255,255,0.02) 0px, transparent 3px, transparent 7px);
  }
  h1{ font-size:22px; color:#eaf6fc; border-bottom:2px solid #6fb8dc; padding-bottom:8px; text-shadow:0 0 10px rgba(111,184,220,0.4); }
  h2{ font-size:17px; color:#a8d4ec; margin-top:22px; }
  h3{ font-size:15px; color:#a8d4ec; }
  p{ font-size:15.5px; line-height:1.65; margin:8px 0; color:#dceef5; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#9bc0d4; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:2px; box-shadow:0 0 16px rgba(90,150,190,0.3); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:rgba(20,55,70,0.7); }
  table.note-table th, table.note-table td{ border:1px solid rgba(111,184,220,0.35); padding:6px; font-size:13px; text-align:center; vertical-align:top; color:#dceef5; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- panel liso de agua, textura continua, sin bordes rasgados --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse at 30% 20%, rgba(140,190,220,0.3) 0%, transparent 45%),
      radial-gradient(ellipse at 70% 70%, rgba(50,100,140,0.35) 0%, transparent 50%),
      linear-gradient(160deg, #2c5570 0%, #1a3a4d 100%);
    padding:18px 20px 20px; margin:22px 8px 26px;
    border:1px solid rgba(111,184,220,0.4);
    border-radius:8px;
    box-shadow:0 0 20px rgba(60,130,170,0.28), inset 0 1px 0 rgba(200,230,245,0.1);
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.04em; color:#a8dcf0; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; color:#dceef5; }
  .callout-info{ background:linear-gradient(160deg,#2c4a70,#1a2d4d); }
  .callout-tip{ background:linear-gradient(160deg,#2c705f,#1a4d40); }
  .callout-example{ background:linear-gradient(160deg,#70652c,#4d451a); }
  .callout-danger{ background:linear-gradient(160deg,#702c35,#4d1a20); }
  .callout-quote{ background:linear-gradient(160deg,#502c70,#301a4d); }
  .callout-question{ background:linear-gradient(160deg,#70652c,#4d451a); }
  .callout .callout{ margin:14px 4px 6px; box-shadow:0 0 22px rgba(60,130,170,0.3); }

  .wikilink{ color:#6fb8dc; border-bottom:1px dotted #6fb8dc; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(61,212,191,0.12); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:rgba(25,70,90,0.6); border:1px solid rgba(111,184,220,0.4); border-radius:12px; padding:4px 12px; font-size:11px; color:#dceef5; font-family:'Segoe UI',sans-serif; }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#6fb8dc; box-shadow:0 0 5px #6fb8dc; }
  .fm-badge b{ font-weight:700; color:#6fb8dc; text-transform:uppercase; font-size:9.5px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #6fb8dc; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #3dd4bf; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #7de8c0; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #a0d8e8; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #f0c060; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#8a2020; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:rgba(15,45,42,0.7); border:1px solid rgba(61,212,191,0.35); border-radius:8px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#6fb8dc !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.25);
  }
  .submap-link:hover{ filter:brightness(1.1); }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:rgba(15,45,42,0.7); border:1px solid rgba(61,212,191,0.3); border-radius:8px; padding:5px 13px; box-shadow:0 0 10px rgba(45,180,160,0.15); }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; }
  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:15px; line-height:1.55; margin:4px 0; color:#dceef5; }
  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border-radius:6px; overflow:hidden; border:1px solid rgba(61,212,191,0.3); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

PAGE_CSS_GASTER = '''
  body{
    margin:0; padding:24px 26px 60px; font-family:'Consolas','Courier New',monospace; color:#c4c4be;
    background-color:#141412;
    background-image:
      radial-gradient(ellipse at 20% 10%, rgba(255,255,255,0.035) 0, transparent 40%),
      radial-gradient(ellipse at 80% 15%, rgba(0,0,0,0.35) 0, transparent 40%),
      radial-gradient(ellipse at 50% 90%, rgba(0,0,0,0.4) 0, transparent 50%),
      repeating-linear-gradient(0deg, rgba(255,255,255,0.012) 0px, transparent 1px, transparent 3px);
  }
  body::after{
    content:""; position:fixed; inset:0; pointer-events:none; z-index:9998;
    background:repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 3px);
    mix-blend-mode:overlay;
  }
  h1{
    font-size:21px; color:#e8e8e2; border-bottom:2px solid #5a5a54; padding-bottom:8px; letter-spacing:.04em;
    text-shadow:1px 0 0 rgba(120,40,50,0.22), -1px 0 0 rgba(60,120,130,0.18);
  }
  h2{ font-size:16px; color:#9a9a92; margin-top:24px; letter-spacing:.03em; text-transform:uppercase; }
  h3{ font-size:14px; color:#9a9a92; }
  p{ font-size:14.5px; line-height:1.7; margin:8px 0; color:#bcbcb4; }
  img{ max-width:100%; border-radius:1px; display:block; margin:8px auto; filter:grayscale(0.85) contrast(1.08) brightness(0.96); }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12px; font-style:italic; color:#7c7c74; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border:1px solid #3a3a34; box-shadow:0 3px 12px rgba(0,0,0,0.6); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; max-width:700px; border-collapse:collapse; margin:12px auto; background:#1c1c19; }
  table.note-table th, table.note-table td{ border:1px solid #454540; padding:6px; font-size:12.5px; text-align:center; vertical-align:top; color:#bcbcb4; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- postit viejo, gris y polvoriento, con el borde rasgado a mano: papel
     envejecido, motas de polvo, manchas y una esquina suelta a punto de
     despegarse, en vez del postit amarillo brillante habitual. El recorte
     base (clip-path) se sustituye por 4 variantes irregulares y no
     periodicas -- .callout-torn-1..4, mas abajo -- para que cada postit de
     la nota tenga un borde distinto, ninguno con el patron de diente de
     sierra regular/poligonal de antes. --- */
  .callout{
    position:relative;
    background:
      radial-gradient(circle 1px at 12% 18%, rgba(0,0,0,0.5) 0, transparent 100%),
      radial-gradient(circle 1px at 34% 62%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1.4px at 71% 30%, rgba(0,0,0,0.45) 0, transparent 100%),
      radial-gradient(circle 1px at 82% 74%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1.2px at 55% 88%, rgba(0,0,0,0.35) 0, transparent 100%),
      radial-gradient(ellipse 40% 30% at 85% 15%, rgba(70,55,55,0.16) 0%, transparent 70%),
      radial-gradient(ellipse 30% 25% at 10% 85%, rgba(55,60,62,0.14) 0%, transparent 65%),
      linear-gradient(155deg, #cfcfc6 0%, #b7b7ac 45%, #a3a398 100%);
    padding:18px 20px 20px; margin:24px 14px 28px;
    box-shadow:2px 6px 14px rgba(0,0,0,0.55), inset 0 -14px 22px -16px rgba(0,0,0,0.25);
    font-family:'Segoe UI', Tahoma, sans-serif;
    /* recorte de respaldo por si algun postit no recibe clase de variante */
    clip-path: polygon(
      0% 0.6%, 44% 0.3%, 68% 0.2%, 93.5% 0.1%, 100% 0.5%,
      99.7% 30%, 99.5% 55%, 99.6% 75%, 99.7% 98.7%,
      98.5% 100%, 80% 99.7%, 46% 99.6%, 0% 99.7%,
      0.4% 55%, 0.5% 0%
    );
  }
  /* --- 4 variantes de borde rasgado, generadas con desplazamientos
     irregulares (no una funcion periodica) por cada uno de los 4 lados, con
     picos ocasionales mas profundos que simulan mordiscos/rasgones mas
     grandes en vez de un serrucho uniforme. Cada variante lleva ademas su
     propio juego de manchas (mas o menos amarillentas/grisaceas) para que
     ademas de la forma cambie el "sucio" del papel. --- */
  .callout.callout-torn-1{
    background:
      radial-gradient(circle 1px at 14% 22%, rgba(0,0,0,0.5) 0, transparent 100%),
      radial-gradient(circle 1px at 38% 61%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1.3px at 73% 33%, rgba(0,0,0,0.45) 0, transparent 100%),
      radial-gradient(circle 1px at 84% 71%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1.1px at 58% 87%, rgba(0,0,0,0.35) 0, transparent 100%),
      radial-gradient(circle 0.8px at 22% 44%, rgba(0,0,0,0.3) 0, transparent 100%),
      radial-gradient(ellipse 20% 15% at 78% 20%, rgba(90,58,30,0.22) 0%, rgba(90,58,30,0.08) 55%, transparent 78%),
      radial-gradient(ellipse 15% 11% at 15% 80%, rgba(70,60,40,0.18) 0%, transparent 72%),
      radial-gradient(ellipse 40% 30% at 85% 15%, rgba(70,55,55,0.16) 0%, transparent 70%),
      radial-gradient(ellipse 30% 25% at 10% 85%, rgba(55,60,62,0.14) 0%, transparent 65%),
      linear-gradient(155deg, #cfcfc6 0%, #b7b7ac 45%, #a3a398 100%);
    clip-path: polygon(
      0% 0.4%, 44.1% 0.3%, 47.5% 0.2%, 47.8% 0.3%, 67.6% 0.4%, 68% 0.5%, 69.9% 0.3%, 80.5% 0.2%, 93.5% 0.1%, 95.2% 0.1%, 99.2% 0.6%, 99.3% 0.2%, 100% 0.5%,
      99.8% 0%, 99.9% 30.2%, 99.9% 46%, 99.6% 48.9%, 99.6% 54.6%, 98.8% 56.8%, 99.7% 62.4%, 99.5% 63.9%, 99.8% 67.2%, 99.5% 73.9%, 99.6% 75.2%, 99.5% 90.7%, 99.7% 100%,
      100% 99.7%, 98.5% 99.6%, 97% 99.5%, 95.2% 99.6%, 92% 99.8%, 81.8% 99.9%, 80.8% 99.8%, 79.9% 99.6%, 53.8% 100%, 46% 99.5%, 37.3% 99.7%, 0% 100%,
      0.2% 100%, 0.7% 98.3%, 1% 88.2%, 0% 80.7%, 0.3% 75.6%, 0.3% 74.2%, 0.2% 60.8%, 0.2% 57.1%, 0.1% 42.3%, 0.2% 0%
    );
  }
  .callout.callout-torn-2{
    background:
      radial-gradient(circle 1px at 20% 30%, rgba(0,0,0,0.5) 0, transparent 100%),
      radial-gradient(circle 1.2px at 44% 68%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1px at 66% 24%, rgba(0,0,0,0.42) 0, transparent 100%),
      radial-gradient(circle 1.4px at 88% 58%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1px at 30% 85%, rgba(0,0,0,0.32) 0, transparent 100%),
      /* pliegue/arruga: dos franjas diagonales de luz y sombra, como un doblez de papel */
      linear-gradient(115deg, transparent 41%, rgba(255,255,255,0.20) 42.5%, rgba(0,0,0,0.14) 44%, transparent 45.5%),
      linear-gradient(21deg, transparent 66%, rgba(255,255,255,0.16) 67.5%, rgba(0,0,0,0.12) 69%, transparent 70.5%),
      radial-gradient(ellipse 26% 18% at 24% 26%, rgba(100,68,32,0.24) 0%, rgba(100,68,32,0.08) 55%, transparent 80%),
      radial-gradient(ellipse 18% 13% at 82% 78%, rgba(80,64,38,0.2) 0%, transparent 75%),
      radial-gradient(ellipse 34% 26% at 88% 12%, rgba(70,55,55,0.14) 0%, transparent 68%),
      linear-gradient(150deg, #d0c9b8 0%, #b7ac93 45%, #9c9280 100%);
    clip-path: polygon(
      0% 1.5%, 43.2% 0.1%, 50% 0.6%, 59.7% 0.3%, 59.7% 0.5%, 63.7% 0.3%, 67.4% 0.3%, 85.8% 0.4%, 89.7% 0%, 98.1% 0.1%, 100% 0%,
      99.9% 0%, 99.6% 36.6%, 99.5% 38.9%, 100% 51.3%, 99.7% 53.4%, 99.9% 67%, 99.6% 79.7%, 99.4% 86.5%, 99.1% 89.4%, 99.9% 93.4%, 99.5% 100%,
      100% 99.6%, 77.3% 99.6%, 72.6% 98.9%, 66.9% 99.8%, 66.1% 99.7%, 64.5% 99.5%, 49.2% 99.4%, 47% 99.6%, 42.3% 98.6%, 38.8% 99.8%, 34.3% 99.7%, 0% 98.7%,
      0.1% 100%, 0.3% 94.6%, 0.3% 86.5%, 0.1% 80.5%, 0.1% 79.5%, 0.4% 77.8%, 0.8% 70.9%, 0.4% 62.8%, 0% 56.9%, 0.4% 49.9%, 0.2% 45.3%, 0.6% 41.9%, 0.4% 41.7%, 0.3% 30.9%, 0% 0%
    );
  }
  .callout.callout-torn-3{
    background:
      radial-gradient(circle 1.1px at 10% 40%, rgba(0,0,0,0.48) 0, transparent 100%),
      radial-gradient(circle 1px at 50% 15%, rgba(0,0,0,0.38) 0, transparent 100%),
      radial-gradient(circle 1.3px at 76% 55%, rgba(0,0,0,0.44) 0, transparent 100%),
      radial-gradient(circle 1px at 60% 90%, rgba(0,0,0,0.36) 0, transparent 100%),
      radial-gradient(circle 0.9px at 90% 20%, rgba(0,0,0,0.3) 0, transparent 100%),
      radial-gradient(circle 1px at 20% 78%, rgba(0,0,0,0.34) 0, transparent 100%),
      radial-gradient(ellipse 24% 34% at 30% 60%, rgba(60,58,52,0.2) 0%, rgba(60,58,52,0.06) 60%, transparent 82%),
      radial-gradient(ellipse 14% 10% at 68% 12%, rgba(72,60,36,0.18) 0%, transparent 75%),
      radial-gradient(ellipse 38% 28% at 12% 12%, rgba(64,64,64,0.15) 0%, transparent 70%),
      linear-gradient(150deg, #c6c6bd 0%, #a8a89d 50%, #8f8f84 100%);
    clip-path: polygon(
      0% 0.5%, 33.5% 0.3%, 40.3% 0.1%, 40.4% 0.1%, 63.7% 0.4%, 68.3% 0.1%, 80.8% 0.3%, 84.6% 0.3%, 97.8% 0.3%, 100% 0.5%,
      99.6% 0%, 99.7% 33.4%, 99.6% 34.5%, 99.8% 35.8%, 99.9% 42.3%, 99.6% 49.2%, 99.8% 55.6%, 98.8% 56%, 99.8% 83.2%, 99.6% 100%,
      100% 99.8%, 97.5% 99.8%, 94.7% 99.8%, 93% 99.7%, 90.2% 100%, 79.2% 99.6%, 68.3% 99.9%, 67.9% 99.9%, 64.6% 99.9%, 64.5% 99.6%, 53.2% 99.6%, 47% 99.6%, 42.3% 99%, 0% 99.7%,
      0.4% 100%, 0.2% 99.9%, 0% 90.4%, 0.1% 73.2%, 0.1% 59.1%, 0.3% 56.8%, 0.1% 56%, 0.1% 55.6%, 0.1% 47.5%, 0.1% 37.9%, 0% 35.6%, 0.3% 33.1%, 0.4% 33%, 0.7% 0%
    );
  }
  .callout.callout-torn-4{
    background:
      radial-gradient(circle 1px at 26% 18%, rgba(0,0,0,0.46) 0, transparent 100%),
      radial-gradient(circle 1.2px at 55% 48%, rgba(0,0,0,0.4) 0, transparent 100%),
      radial-gradient(circle 1px at 80% 30%, rgba(0,0,0,0.42) 0, transparent 100%),
      radial-gradient(circle 1.3px at 40% 82%, rgba(0,0,0,0.38) 0, transparent 100%),
      radial-gradient(circle 0.9px at 92% 76%, rgba(0,0,0,0.3) 0, transparent 100%),
      /* esquina arrugada: pliegue corto concentrado en una zona, no un doblez de lado a lado */
      linear-gradient(60deg, transparent 78%, rgba(255,255,255,0.22) 80%, rgba(0,0,0,0.16) 82%, transparent 84%),
      linear-gradient(60deg, transparent 84%, rgba(255,255,255,0.16) 86%, rgba(0,0,0,0.12) 88%, transparent 90%),
      radial-gradient(ellipse 22% 16% at 66% 82%, rgba(96,66,34,0.22) 0%, rgba(96,66,34,0.08) 55%, transparent 78%),
      radial-gradient(ellipse 16% 12% at 12% 30%, rgba(74,62,38,0.18) 0%, transparent 74%),
      radial-gradient(ellipse 36% 26% at 90% 10%, rgba(70,55,55,0.15) 0%, transparent 68%),
      linear-gradient(160deg, #d3cdb0 0%, #b8ae8c 48%, #9e9576 100%);
    clip-path: polygon(
      0% 1.5%, 30.7% 0.6%, 47.5% 0.2%, 49.4% 0.4%, 49.9% 1.1%, 53.3% 0.2%, 57.1% 0%, 83.6% 0.3%, 89.8% 0%, 92.9% 0.8%, 93.3% 0.1%, 99.6% 0.1%, 100% 1.1%,
      99.7% 0%, 99.8% 39.3%, 99.5% 44.6%, 99% 45.4%, 99.9% 46.1%, 99.9% 48.6%, 99.8% 56.5%, 99.8% 57.6%, 99% 83.2%, 98.6% 84.6%, 99.1% 87.1%, 99.4% 88.1%, 99.9% 97.8%, 98.8% 99.9%,
      99.4% 100%, 100% 99.9%, 85.8% 100%, 81.2% 99.8%, 74.8% 99%, 74% 98.6%, 67.9% 99.2%, 57.5% 99.3%, 51.5% 99.7%, 37.8% 99.4%, 0% 99.6%,
      0.5% 100%, 0.4% 93.9%, 0% 92.9%, 1.3% 88.3%, 0.1% 82.9%, 0.1% 78.9%, 0.2% 67.2%, 0.6% 60.8%, 0.2% 59.7%, 1.1% 54.3%, 0.2% 45.3%, 0.2% 44%, 0.5% 0%
    );
  }
  .callout::after{
    content:""; position:absolute; top:-6px; right:10%; width:34px; height:26px; z-index:2;
    background:linear-gradient(200deg, #c2c2b6 40%, #9c9c90 100%);
    clip-path: polygon(0% 100%, 100% 100%, 78% 8%, 34% 0%, 12% 38%);
    box-shadow:1px 2px 4px rgba(0,0,0,0.5);
    transform:rotate(-7deg);
    opacity:.92;
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.04em; color:#2c2c26; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; color:#38382e; }
  /* --- las listas con vinetas dentro de un postit heredaban el color claro
     pensado para el fondo oscuro de la pagina (#bcbcb4), casi invisible
     sobre el papel claro del postit -- p.ej. los bloques "Referencias y
     pistas por capitulo" de la nota de Gaster. Se oscurecen igual que el
     resto del texto del postit (.callout-body p). --- */
  .callout .note-list li{ color:#38382e; }
  .callout .note-list li::marker{ color:#6a5f4e; }

  .callout-info{ background:linear-gradient(155deg,#c4d0d0,#a5b0b0); }
  .callout-tip{ background:linear-gradient(155deg,#c4cfc2,#a3aea1); }
  .callout-example{ background:linear-gradient(155deg,#cfcfc6,#b0b0a4); }
  .callout-danger{ background:linear-gradient(155deg,#d2c0bc,#b09a95); }
  .callout-quote{ background:linear-gradient(155deg,#c8c4ce,#a8a3ae); }
  .callout-question{ background:linear-gradient(155deg,#d0ccb6,#b0ab92); }

  .callout .callout{
    margin:16px 4px 8px;
    box-shadow:3px 7px 16px rgba(0,0,0,0.6), inset 0 -10px 16px -10px rgba(0,0,0,0.18);
  }

  .wikilink{ color:#e8e8e0; border-bottom:1px dotted #8a8a80; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(255,255,255,0.08); }

  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{
    position:relative; display:inline-flex; align-items:baseline; gap:5px;
    background:linear-gradient(180deg, rgba(38,38,35,0.5), rgba(26,26,24,0.5));
    border:1px solid #4a4a42; border-radius:2px; padding:4px 12px 4px 10px;
    font-size:10.5px; color:#c4c4bc; font-family:'Consolas','Courier New',monospace;
  }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#8a8a80; flex-shrink:0; align-self:center; }
  .fm-badge b{ font-weight:700; color:#e8e8e0; text-transform:uppercase; font-size:9px; letter-spacing:.03em;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .fm-icon{ font-size:12px; margin-right:1px; filter:grayscale(1); }
  .fm-badge[data-key="tipo"]{ border-left:3px solid #8a8a80; }
  .fm-badge[data-key="mundo"]{ border-left:3px solid #6e7676; }
  .fm-badge[data-key="especie"]{ border-left:3px solid #75786c; }
  .fm-badge[data-key="familia"]{ border-left:3px solid #7a6e74; }
  .fm-badge[data-key="grupo"]{ border-left:3px solid #8a826e; }
  .fm-badge[data-key="estado"]{
    border:2px solid #8a2020; background:rgba(140,20,20,0.12); font-weight:700;
    text-transform:uppercase; letter-spacing:.04em; transform:rotate(-2deg);
    box-shadow:0 0 0 1px rgba(140,20,20,0.25) inset;
  }
  .fm-badge[data-key="estado"] em{ color:#c47070; }
  .submap-link{
    display:inline-flex; align-items:center; gap:6px; margin:14px 0 6px;
    background:#1e1e1b; border:1px solid #4a4a42; border-radius:3px;
    padding:8px 16px; font-size:14px; font-weight:600; color:#e0e0d6 !important;
    text-decoration:none; box-shadow:1px 3px 8px rgba(0,0,0,0.4);
  }
  .submap-link:hover{ filter:brightness(1.15); }

  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{
    display:inline-block; background:#1e1e1b; border:1px solid #4a4a42; border-radius:3px;
    padding:5px 13px; box-shadow:1px 2px 5px rgba(0,0,0,0.4);
  }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; }
  .link-chip:hover{ background:#28281e; }

  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:14.5px; line-height:1.55; margin:4px 0; color:#bcbcb4; }
  .note-list li::marker{ color:#6a6a60; }

  .yt-embed{ position:relative; width:100%; max-width:560px; aspect-ratio:16/9; margin:14px auto; border:1px solid #4a4a42; overflow:hidden; filter:grayscale(0.7); }
  .yt-embed iframe{ position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
'''

# --- CSS compartido por TODOS los temas: no depende de colores de cada tema,
# asi que se anade una sola vez en vez de duplicarlo 7 veces. Cubre: colores
# reales de fiabilidad en la columna "Identidad real" (antes solo emoji),
# tamano reducido para las imagenes de cabecera de capitulo/zona, y el
# lightbox de "clic para ver completa" que aplica a cualquier imagen del sitio.
SHARED_CSS_EXTRA = '''
  /* --- la nota se adapta al ancho de la tabla en vez de estirarse hasta el
     borde de la ventana: sin esto, en pantallas anchas el postit ocupaba
     todo el viewport mientras la tabla se quedaba con un ancho fijo mucho
     mas estrecho, dejando un hueco enorme alrededor. Va despues del CSS de
     cada tema (que solo pone margin:0) para poder centrar con margin:auto. --- */
  body{ max-width:800px; margin:0 auto; }

  /* --- fiabilidad de identidad: el fondo se aplica a la CELDA entera (td),
     no a un span interior, para que rellene el hueco completo como en la
     hoja de calculo original en vez de verse como un subrayado/resaltado --- */
  table.note-table td.rel-blue{ background:#b7c9ef; }
  table.note-table td.rel-yellow{ background:#f0b429; }
  table.note-table td.rel-blue.rel-yellow{ background:linear-gradient(180deg,#b7c9ef 50%,#f0b429 50%); }
  table.note-table td.rel-new{ color:#c0392b; font-weight:700; }

  /* --- imagen de cabecera de capitulo/zona: foto de expediente clavada al
     corcho con una chincheta, en vez de una imagen suelta generica --- */
  figure.fig-header{
    position:relative; display:block; width:fit-content; max-width:100%;
    margin:20px auto 26px; padding:9px 9px 7px;
    background:#fffdf6; border:1px solid rgba(0,0,0,0.07);
    box-shadow:0 12px 22px -8px rgba(0,0,0,0.42), 0 2px 5px rgba(0,0,0,0.18);
    transform:rotate(-0.6deg);
  }
  figure.fig-header::before{
    content:""; position:absolute; top:-9px; left:50%; margin-left:-8px;
    width:16px; height:16px; border-radius:50%; z-index:2;
    background:radial-gradient(circle at 34% 30%, #ff9c8c, #b91f1f 55%, #650d0d 100%);
    box-shadow:0 3px 4px rgba(0,0,0,0.45);
  }
  figure.fig-header img{
    width:auto; max-width:540px; max-height:560px; margin:0 auto; display:block;
    box-shadow:inset 0 0 0 1px rgba(0,0,0,0.08);
  }
  figure.fig-header figcaption{
    font-family:'Courier New', monospace; font-size:11px; letter-spacing:.03em;
    text-transform:uppercase; margin-top:9px; padding-top:7px;
    border-top:1px dashed rgba(0,0,0,0.22);
  }

  /* --- cabecera de categoria tipo "expediente" (Lugares/Personajes/...):
     icono a modo de chincheta, contador a modo de sello de tinta --- */
  .case-tag{
    display:flex; align-items:center; gap:10px;
    padding-bottom:9px; border-bottom:2px dashed rgba(0,0,0,0.22);
  }
  .case-tag-icon{
    font-size:19px; line-height:1; flex-shrink:0;
    filter:drop-shadow(0 1px 1px rgba(0,0,0,0.3));
  }
  .case-tag-label{ flex:1; }
  .case-tag-count{
    display:inline-flex; align-items:center; justify-content:center;
    min-width:26px; height:26px; padding:0 5px; flex-shrink:0;
    border:2px solid #8a2020; border-radius:50%; background:rgba(138,32,32,0.07);
    color:#8a2020; font-family:'Courier New', monospace; font-weight:700; font-size:12px;
    letter-spacing:0; text-transform:none; transform:rotate(-9deg); opacity:.85;
  }

  /* --- "Objetos del Mundo Oscuro.md": cada capitulo tiñe sus postits de
     categoria (Lugares/Personajes/Enemigos/...) y las tablas que contienen
     con el color mas representativo de ese Mundo Oscuro, para distinguir
     un capitulo de otro de un vistazo sin perder el aspecto de postit --- */
  .callout.chapter-c1{ background:#f9d6d0; }
  .callout.chapter-c1 table.note-table{ background:#fdf1ee; border-color:#e3a99e; }
  .callout.chapter-c1 table.note-table th{ background:#efb2a6; color:#5c1e14; }
  .callout.chapter-c1 table.note-table td{ border-color:#eecac2; }

  .callout.chapter-c2{ background:#f4d3ef; }
  .callout.chapter-c2 table.note-table{ background:#fdf1fb; border-color:#d19bcb; }
  .callout.chapter-c2 table.note-table th{ background:#e4aedc; color:#4d1a48; }
  .callout.chapter-c2 table.note-table td{ border-color:#ecc9e6; }

  .callout.chapter-c3{ background:#cceff1; }
  .callout.chapter-c3 table.note-table{ background:#eefbfc; border-color:#89c7cc; }
  .callout.chapter-c3 table.note-table th{ background:#a4dde1; color:#0f3d40; }
  .callout.chapter-c3 table.note-table td{ border-color:#c4e9eb; }

  .callout.chapter-c4{ background:#ded1f4; }
  .callout.chapter-c4 table.note-table{ background:#f6f1fc; border-color:#ac91d6; }
  .callout.chapter-c4 table.note-table th{ background:#c3a9e6; color:#341c5c; }
  .callout.chapter-c4 table.note-table td{ border-color:#dccbf0; }

  .callout.chapter-c5{ background:#d6ecc4; }
  .callout.chapter-c5 table.note-table{ background:#f3faee; border-color:#9bc981; }
  .callout.chapter-c5 table.note-table th{ background:#b6dd9c; color:#25470f; }
  .callout.chapter-c5 table.note-table td{ border-color:#d3e9c3; }

  /* --- tablas de identidad (Sprite/Mundo Oscuro/Identidad real/Sprite Mundo
     Claro): las columnas de texto se quedaban con mucho hueco horizontal
     vacio porque el layout automatico las ensancha al ancho de la fila mas
     larga de toda la columna. Se les da un ancho propio mas ajustado (que
     envuelve en varias lineas si hace falta) y el nombre se ve mas grande,
     dejando las columnas de sprite tal cual para no deformar las imagenes. --- */
  table.note-table.id-table td, table.note-table.id-table th{ word-wrap:break-word; overflow-wrap:break-word; }
  table.note-table.id-table th:nth-child(2), table.note-table.id-table td:nth-child(2){
    width:15%; font-size:15px; font-weight:700;
  }
  table.note-table.id-table th:nth-child(3), table.note-table.id-table td:nth-child(3){ width:27%; }

  /* --- pergamino de la Profecia: el callout "[!prophecy]- Titulo" (ver
     mdconvert_linked.py, ctype=="prophecy") se usa dentro de la nota de
     CUALQUIER personaje que tenga relacion con la Profecia, para mostrar
     ese vinculo siempre como un rollo de pergamino abierto -- el mismo
     diseño que usa la propia nota de Profecía (tema "parchment") -- sin
     importar el tema visual del resto de esa nota (postit, Gaster, Undertale,
     Cristal...). Va aqui, en el CSS compartido, en vez de en cada tema, para
     no tener que duplicarlo 8 veces y para que gane siempre por orden de
     carga (este bloque se añade DESPUES del CSS del tema en el <style> de
     la pagina). Reutiliza el mismo recorte irregular de "rollo antiguo" que
     PAGE_CSS_PARCHMENT, con el borde-barra enrollado arriba y abajo. */
  .callout.prophecy-scroll{
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
  .callout.prophecy-scroll::before, .callout.prophecy-scroll::after{
    content:""; position:absolute; left:-2px; right:-2px; height:26px; z-index:1;
    background:
      repeating-linear-gradient(135deg, transparent 0 7px, #5a3416 7px 8.5px),
      repeating-linear-gradient(45deg, transparent 0 7px, #5a3416 7px 8.5px),
      linear-gradient(180deg, #caa267, #8a6236 45%, #6e4a26 55%, #a37e46);
    box-shadow:0 3px 8px rgba(30,18,6,0.5);
  }
  .callout.prophecy-scroll::before{ top:-13px; }
  .callout.prophecy-scroll::after{ bottom:-13px; transform:scaleY(-1); }
  .prophecy-scroll .callout-title{
    font-weight:bold; margin-bottom:8px; font-size:14.5px; color:#4a3418 !important;
    text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid rgba(90,60,20,.35); padding-bottom:5px;
    position:relative; z-index:2; font-family:'Palatino Linotype', Georgia, serif;
  }
  .prophecy-scroll .callout-body{ position:relative; z-index:2; }
  .prophecy-scroll .callout-body p{ margin:6px 0; font-size:15px; line-height:1.55; color:#3f3120 !important; }
  .prophecy-scroll .callout-body img.inline-img{
    width:auto; max-width:80%; height:auto; display:block; margin:10px auto;
    border-radius:2px; box-shadow:0 2px 8px rgba(40,25,5,0.35); border:none;
  }
  .prophecy-scroll .wikilink{ color:#7a2e22 !important; border-bottom:1px dotted #7a2e22 !important; }
  .prophecy-scroll a.wikilink:hover{ background:rgba(122,46,34,0.12); }

  /* --- lightbox: clic en cualquier imagen para verla a tamano completo --- */
  img{ cursor: zoom-in; }
  #lightbox-overlay{
    display:none; position:fixed; inset:0; z-index:9999;
    background:rgba(0,0,0,0.86); align-items:center; justify-content:center;
    cursor: zoom-out; padding:24px; box-sizing:border-box;
  }
  #lightbox-overlay.open{ display:flex; }
  #lightbox-overlay img{
    max-width:92vw; max-height:92vh; width:auto; height:auto; display:block;
    margin:0; border-radius:4px; box-shadow:0 8px 32px rgba(0,0,0,0.6); cursor: zoom-out;
  }
'''

SHARED_BODY_EXTRA = '''
<div id="lightbox-overlay"><img id="lightbox-img" src="" alt=""></div>
<script>
(function(){
  var overlay = document.getElementById('lightbox-overlay');
  var lbImg = document.getElementById('lightbox-img');
  document.addEventListener('click', function(e){
    var t = e.target;
    if(t && t.tagName === 'IMG' && t.id !== 'lightbox-img'){
      lbImg.src = t.getAttribute('src');
      overlay.classList.add('open');
    } else if(overlay.classList.contains('open')){
      overlay.classList.remove('open');
      lbImg.src = '';
    }
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape'){ overlay.classList.remove('open'); lbImg.src = ''; }
  });
})();
</script>
'''

PAGE_TMPL = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{css}{shared_css}</style>
</head>
<body>
{body}
{shared_body}
</body>
</html>
'''

THEME_CSS = {
    "postit": PAGE_CSS,
    "parchment": PAGE_CSS_PARCHMENT,
    "rusted": PAGE_CSS_RUSTED,
    "wet": PAGE_CSS_WET,
    "crystal": PAGE_CSS_CRYSTAL,
    "undertale": PAGE_CSS_UNDERTALE,
    "fountain": PAGE_CSS_FOUNTAIN,
    "gaster": PAGE_CSS_GASTER,
}

def render_page(title_escaped, body_html, theme="postit", lang="es"):
    css = THEME_CSS.get(theme, PAGE_CSS)
    return PAGE_TMPL.format(
        title=title_escaped, css=css, shared_css=SHARED_CSS_EXTRA,
        body=body_html, shared_body=SHARED_BODY_EXTRA, lang=lang,
    )

