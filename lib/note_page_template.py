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
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:#3a2f28; }
  table.note-table th, table.note-table td{ border:1px solid #5a4a38; padding:6px; font-size:12.5px; text-align:center; vertical-align:top; color:#d9cdb2; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- placas metalicas remachadas, con manchas de oxido y borde rasgado --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse at 15% 20%, rgba(180,80,25,0.35) 0%, transparent 30%),
      radial-gradient(ellipse at 85% 75%, rgba(160,60,15,0.3) 0%, transparent 32%),
      radial-gradient(ellipse at 60% 10%, rgba(140,50,10,0.25) 0%, transparent 28%),
      linear-gradient(160deg, #4a3d30 0%, #3a2f26 40%, #2e2620 100%);
    padding:20px 22px; margin:24px 6px 28px;
    border:1px solid #6b5842;
    box-shadow:2px 5px 14px rgba(0,0,0,0.5), inset 0 0 30px rgba(0,0,0,0.35), inset 0 0 50px rgba(150,60,20,0.12);
    clip-path: polygon(
      0% 3%, 3% 0%, 10% 2%, 16% 0%, 24% 2%, 31% 0%, 39% 2%, 46% 0%, 54% 2%, 61% 0%, 69% 2%, 76% 0%, 84% 2%, 91% 0%, 97% 2%, 100% 0%,
      98% 14%, 100% 24%, 97% 33%, 100% 46%, 98% 55%, 100% 67%, 96% 78%, 100% 88%, 96% 100%,
      88% 97%, 78% 100%, 68% 97%, 58% 100%, 47% 97%, 37% 100%, 27% 97%, 17% 100%, 8% 97%, 0% 100%,
      3% 87%, 0% 76%, 4% 64%, 0% 53%, 3% 40%, 0% 28%, 3% 16%
    );
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:#e0975a; }
  .callout-body p{ margin:5px 0; font-size:14px; line-height:1.55; color:#d9cdb2; }
  .callout-info{ background:radial-gradient(ellipse at 20% 20%, rgba(160,70,20,0.28) 0%, transparent 32%), linear-gradient(160deg,#38424a,#2a3238); }
  .callout-tip{ background:radial-gradient(ellipse at 80% 25%, rgba(160,70,20,0.28) 0%, transparent 32%), linear-gradient(160deg,#354a38,#28362a); }
  .callout-example{ background:radial-gradient(ellipse at 15% 75%, rgba(180,85,25,0.32) 0%, transparent 32%), linear-gradient(160deg,#4a3d30,#3a2f26); }
  .callout-danger{ background:radial-gradient(ellipse at 75% 20%, rgba(190,90,25,0.35) 0%, transparent 32%), linear-gradient(160deg,#4a2e28,#3a221e); }
  .callout-quote{ background:radial-gradient(ellipse at 25% 80%, rgba(160,70,20,0.28) 0%, transparent 32%), linear-gradient(160deg,#3d3548,#2c2736); }
  .callout-question{ background:linear-gradient(160deg,#4a3d20,#3a2f18); }
  .callout::before, .callout::after{
    content:""; position:absolute; width:8px; height:8px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #a89880, #4a3d2e 70%);
    box-shadow:0 1px 2px rgba(0,0,0,0.6);
  }
  .callout::before{ top:6px; left:6px; }
  .callout::after{ bottom:6px; right:6px; }
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
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:#ede4c8; }
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
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:rgba(30,22,55,0.7); }
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
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:#000000; }
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
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:rgba(20,55,70,0.7); }
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

THEME_CSS = {
    "postit": PAGE_CSS,
    "parchment": PAGE_CSS_PARCHMENT,
    "rusted": PAGE_CSS_RUSTED,
    "wet": PAGE_CSS_WET,
    "crystal": PAGE_CSS_CRYSTAL,
    "undertale": PAGE_CSS_UNDERTALE,
    "fountain": PAGE_CSS_FOUNTAIN,
}

def render_page(title_escaped, body_html, theme="postit"):
    css = THEME_CSS.get(theme, PAGE_CSS)
    return PAGE_TMPL.format(title=title_escaped, css=css, body=body_html)

