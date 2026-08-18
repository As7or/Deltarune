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
    background-color:#2e2620;
    background-image:
      radial-gradient(ellipse at 15% 20%, rgba(180,90,40,0.18) 0, transparent 40%),
      radial-gradient(ellipse at 85% 15%, rgba(140,60,20,0.15) 0, transparent 38%),
      radial-gradient(ellipse at 60% 85%, rgba(180,90,40,0.14) 0, transparent 42%),
      repeating-linear-gradient(90deg, rgba(0,0,0,0.06) 0px, transparent 2px, transparent 5px);
  }
  h1{ font-size:21px; color:#e8dcc0; border-bottom:2px solid #b5622e; padding-bottom:8px; letter-spacing:.02em; text-transform:uppercase; }
  h2{ font-size:16px; color:#d68b52; margin-top:24px; text-transform:uppercase; letter-spacing:.05em; }
  h3{ font-size:14px; color:#d68b52; }
  p{ font-size:14.5px; line-height:1.65; margin:8px 0; color:#d9cdb2; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; filter:saturate(0.85); }
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

  /* --- placas metalicas remachadas --- */
  .callout{
    position:relative;
    background: linear-gradient(160deg, #4a3d30 0%, #3a2f26 40%, #2e2620 100%);
    padding:18px 20px; margin:22px 6px 26px;
    border:1px solid #6b5842;
    box-shadow:2px 5px 14px rgba(0,0,0,0.5), inset 0 0 30px rgba(0,0,0,0.35);
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:#d68b52; }
  .callout-body p{ margin:5px 0; font-size:14px; line-height:1.55; color:#d9cdb2; }
  .callout-info{ background:linear-gradient(160deg,#38424a,#2a3238); }
  .callout-tip{ background:linear-gradient(160deg,#354a38,#28362a); }
  .callout-example{ background:linear-gradient(160deg,#4a3d30,#3a2f26); }
  .callout-danger{ background:linear-gradient(160deg,#4a2e28,#3a221e); }
  .callout-quote{ background:linear-gradient(160deg,#3d3548,#2c2736); }
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
    margin:0; padding:24px 26px 60px; font-family:Georgia, serif; color:#2c3a3d;
    background-color:#b9c9cb;
    background-image:
      radial-gradient(ellipse at 20% 15%, rgba(120,150,155,0.3) 0, transparent 42%),
      radial-gradient(ellipse at 80% 25%, rgba(90,120,130,0.25) 0, transparent 40%),
      radial-gradient(ellipse at 50% 90%, rgba(120,150,155,0.28) 0, transparent 45%);
  }
  h1{ font-size:22px; color:#1f3538; border-bottom:2px solid #4a6b70; padding-bottom:8px; }
  h2{ font-size:17px; color:#3d5a5f; margin-top:22px; }
  h3{ font-size:15px; color:#3d5a5f; }
  p{ font-size:15.5px; line-height:1.65; margin:8px 0; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#4a6266; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:2px; box-shadow:0 3px 10px rgba(20,40,42,0.3); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:#cbd9da; }
  table.note-table th, table.note-table td{ border:1px solid #9db0b2; padding:6px; font-size:13px; text-align:center; vertical-align:top; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- papel humedo, manchado --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.15) 0, transparent 40%),
      radial-gradient(ellipse at 75% 80%, rgba(60,90,95,0.12) 0, transparent 45%),
      #dbe6e7;
    padding:16px 18px 18px; margin:22px 10px 26px;
    box-shadow:2px 6px 14px rgba(20,40,42,0.28), inset 0 -10px 20px -14px rgba(20,40,42,0.15);
    border-radius:3px 12px 3px 14px/10px 3px 14px 3px;
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.03em; color:#1f3538; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; color:#2c3a3d; }
  .callout-info{ background:#c3dce8; }
  .callout-tip{ background:#c8e2d4; }
  .callout-example{ background:#dbe6e7; }
  .callout-danger{ background:#e0cccb; }
  .callout-quote{ background:#d3d3e6; }
  .callout-question{ background:#dce0c3; }
  .callout .callout{ margin:14px 4px 6px; box-shadow:3px 6px 16px rgba(20,40,42,0.35); }

  .wikilink{ color:#1f5258; border-bottom:1px dotted #1f5258; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(31,82,88,0.12); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:linear-gradient(180deg,#e4eeee,#c3d5d6); border:1px solid #9db0b2; border-radius:13px; padding:4px 12px; font-size:11px; color:#2c3a3d; font-family:'Segoe UI',sans-serif; }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#4a6b70; }
  .fm-badge b{ font-weight:700; color:#1f3538; text-transform:uppercase; font-size:9.5px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:#cbd9da; border:1px solid #9db0b2; border-radius:8px; padding:5px 13px; box-shadow:1px 2px 5px rgba(20,40,42,0.25); }
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
    margin:0; padding:24px 26px 60px; font-family:'Segoe UI', Georgia, serif; color:#c8f0e8;
    background-color:#0a1e1c;
    background-image:
      radial-gradient(ellipse at 20% 20%, rgba(45,180,160,0.22) 0, transparent 42%),
      radial-gradient(ellipse at 80% 30%, rgba(30,120,140,0.2) 0, transparent 40%),
      radial-gradient(ellipse at 50% 90%, rgba(45,180,160,0.18) 0, transparent 45%);
  }
  h1{ font-size:22px; color:#e8fff8; border-bottom:2px solid #3dd4bf; padding-bottom:8px; text-shadow:0 0 8px rgba(61,212,191,0.35); }
  h2{ font-size:17px; color:#8bd8c8; margin-top:22px; }
  h3{ font-size:15px; color:#8bd8c8; }
  p{ font-size:15.5px; line-height:1.65; margin:8px 0; color:#c8f0e8; }
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; }
  figure{ margin:14px 0; text-align:center; }
  figcaption{ font-size:12.5px; font-style:italic; color:#8bb8ad; margin-top:4px; }
  .inline-img{ width:100%; height:auto; display:block; margin:8px auto; border-radius:2px; box-shadow:0 0 16px rgba(45,180,160,0.25); }
  .inline-img-alpha{ width:auto; max-width:230px; max-height:280px; margin:8px auto; box-shadow:none; background:none; }
  .inline-img-small{ width:auto; height:110px; max-width:100%; display:block; margin:6px auto; box-shadow:none; }
  figure.fig-alpha img{ box-shadow:none; width:auto; max-width:230px; max-height:280px; margin:0 auto; }
  table.note-table{ width:100%; border-collapse:collapse; margin:12px 0; background:rgba(15,45,42,0.7); }
  table.note-table th, table.note-table td{ border:1px solid rgba(61,212,191,0.3); padding:6px; font-size:13px; text-align:center; vertical-align:top; color:#c8f0e8; }
  table.note-table .inline-img{ width:auto; max-width:100%; height:230px; margin:6px auto; box-shadow:none; }
  table.note-table .inline-img-small{ height:110px; }

  /* --- panel de agua oscura con brillo turquesa --- */
  .callout{
    position:relative;
    background: linear-gradient(170deg, rgba(20,60,55,0.6) 0%, rgba(10,30,28,0.8) 100%);
    padding:16px 18px 18px; margin:22px 8px 26px;
    border:1px solid rgba(61,212,191,0.35);
    box-shadow:0 0 20px rgba(45,180,160,0.18), inset 0 1px 0 rgba(200,240,232,0.08);
    border-radius:16px 4px 16px 4px;
  }
  .callout-title{ font-weight:bold; margin-bottom:8px; font-size:14px; text-transform:uppercase; letter-spacing:.04em; color:#3dd4bf; }
  .callout-body p{ margin:5px 0; font-size:14.5px; line-height:1.5; color:#c8f0e8; }
  .callout-info{ background:linear-gradient(170deg, rgba(25,70,110,0.55), rgba(12,32,45,0.75)); }
  .callout-tip{ background:linear-gradient(170deg, rgba(25,100,80,0.55), rgba(10,40,32,0.75)); }
  .callout-example{ background:linear-gradient(170deg, rgba(90,75,25,0.5), rgba(45,35,10,0.75)); }
  .callout-danger{ background:linear-gradient(170deg, rgba(120,35,45,0.5), rgba(50,15,20,0.75)); }
  .callout-quote{ background:linear-gradient(170deg, rgba(70,50,110,0.5), rgba(30,20,50,0.75)); }
  .callout-question{ background:linear-gradient(170deg, rgba(100,80,25,0.5), rgba(45,35,10,0.75)); }
  .callout .callout{ margin:14px 4px 6px; box-shadow:0 0 22px rgba(45,180,160,0.25); }

  .wikilink{ color:#3dd4bf; border-bottom:1px dotted #3dd4bf; text-decoration:none; cursor:pointer; }
  a.wikilink:hover{ background:rgba(61,212,191,0.12); }
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 20px; }
  .fm-badge{ display:inline-flex; align-items:baseline; gap:5px; background:rgba(20,60,55,0.6); border:1px solid rgba(61,212,191,0.35); border-radius:12px; padding:4px 12px; font-size:11px; color:#c8f0e8; font-family:'Segoe UI',sans-serif; }
  .fm-badge::before{ content:""; width:6px; height:6px; border-radius:50%; background:#3dd4bf; box-shadow:0 0 5px #3dd4bf; }
  .fm-badge b{ font-weight:700; color:#3dd4bf; text-transform:uppercase; font-size:9.5px;  margin-right:5px;}
  .fm-badge em{ font-style:normal; }
  .link-row{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 16px; }
  .link-chip{ display:inline-block; background:rgba(15,45,42,0.7); border:1px solid rgba(61,212,191,0.3); border-radius:8px; padding:5px 13px; box-shadow:0 0 10px rgba(45,180,160,0.15); }
  .link-chip a.wikilink{ font-size:13.5px; font-weight:600; border-bottom:none; }
  .note-list{ margin:8px 0; padding-left:22px; }
  .note-list li{ font-size:15px; line-height:1.55; margin:4px 0; color:#c8f0e8; }
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

