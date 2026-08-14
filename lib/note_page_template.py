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
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; image-rendering:pixelated; image-rendering:-moz-crisp-edges; image-rendering:crisp-edges; }
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
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }
  .fm-badge{
    display:inline-flex; align-items:center; gap:6px;
    background:#f4ecd2; border:1px solid rgba(90,64,32,.3);
    border-radius:3px 12px 3px 12px;
    padding:4px 12px 4px 8px;
    font-size:11px; font-family:'Segoe UI', Tahoma, sans-serif; color:#4a3b20;
    box-shadow:0 2px 3px rgba(0,0,0,.15), inset 0 1px 0 rgba(255,255,255,.55);
  }
  .fm-badge:nth-child(odd){ transform:rotate(-0.7deg); }
  .fm-badge:nth-child(even){ transform:rotate(0.6deg); }
  .fm-badge i{ font-style:normal; font-size:13px; line-height:1; }
  .fm-badge b{ text-transform:uppercase; font-size:8.5px; letter-spacing:.07em; opacity:.62; font-weight:bold; margin-right:1px; }
  .fm-badge.w-lightner{ background:#dcefd9; border-color:#2e8b46; }
  .fm-badge.w-darkner{ background:#e8def0; border-color:#6b3fa0; }
  .fm-badge.w-ambos{ background:linear-gradient(90deg,#dcefd9 50%,#e8def0 50%); border-color:#7a5a94; }
  .fm-badge.w-na{ background:#e6e3dc; border-color:#6b7280; }
  .fm-badge.c-oficial{ background:#dcefd9; border-color:#2e8b46; }
  .fm-badge.c-fuerte{ background:#f5e8c8; border-color:#c9982e; }
  .fm-badge.c-debil{ background:#f5d9d3; border-color:#b23c30; }
  .fm-badge.c-mixta{ background:#eee6d6; border-color:#8a7a5c; }
  ul{ margin:10px 0; padding-left:24px; }
  ul li{ margin:5px 0; font-size:15px; line-height:1.5; }

  /* --- Relacionado: nube de etiquetas ancladas, como chinchetas de corcho --- */
  .related-web{ display:flex; flex-wrap:wrap; gap:14px 10px; margin:22px 2px 8px; padding:20px 4px 4px; border-top:2px dashed #c9b384; }
  .related-tag{
    display:inline-flex; align-items:center; gap:6px; background:#fdf6e9;
    border:1px solid #c9b384; border-radius:3px 10px 3px 10px;
    padding:7px 13px 7px 9px; font-size:13.5px; box-shadow:1px 3px 6px rgba(0,0,0,.2);
    transition:transform .15s ease, box-shadow .15s ease; cursor:default;
  }
  .related-tag:nth-child(3n+1){ transform:rotate(-1.6deg); }
  .related-tag:nth-child(3n+2){ transform:rotate(1.3deg); }
  .related-tag:nth-child(3n){ transform:rotate(-0.4deg); }
  .related-tag:hover{ transform:rotate(0deg) translateY(-3px) scale(1.05); box-shadow:2px 7px 12px rgba(0,0,0,.3); z-index:2; }
  .related-tag-label a.wikilink{ font-weight:bold; }

  /* --- Submapa: tarjeta llamativa, como un mapa clavado al corcho --- */
  .submap-cta{
    position:relative; display:flex; align-items:center; gap:14px; margin:26px 2px 30px;
    padding:16px 20px; text-decoration:none; color:inherit;
    background:
      repeating-linear-gradient(120deg, rgba(90,60,20,.05) 0 2px, transparent 2px 14px),
      linear-gradient(135deg,#fdf6e9,#f2e2bd);
    border:1px solid #c9982e; border-radius:4px 12px 4px 12px;
    box-shadow:2px 6px 12px rgba(0,0,0,.25); transition:transform .18s ease, box-shadow .18s ease;
  }
  .submap-cta::before{
    content:""; position:absolute; top:-8px; left:26px; width:15px; height:15px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #ff8a7a, #c73434 65%); box-shadow:0 3px 4px rgba(0,0,0,.45);
  }
  .submap-cta:hover{ transform:translateY(-3px) rotate(-0.4deg); box-shadow:3px 10px 18px rgba(0,0,0,.32); }
  .submap-cta-icon{ font-size:32px; line-height:1; flex-shrink:0; filter:drop-shadow(1px 2px 2px rgba(0,0,0,.35)); }
  .submap-cta-title{ display:block; font-weight:bold; font-size:15.5px; color:#5a4020; }
  .submap-cta-sub{ display:block; font-size:12px; font-style:italic; color:#7a6a4a; margin-top:2px; }
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
  img{ max-width:100%; border-radius:2px; display:block; margin:8px auto; image-rendering:pixelated; image-rendering:-moz-crisp-edges; image-rendering:crisp-edges; }
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
    clip-path: url(#deckle-scroll);
  }
  .callout::before, .callout::after{
    content:""; position:absolute; left:-2px; right:-2px; height:26px; z-index:1;
    background:
      repeating-linear-gradient(135deg, transparent 0 7px, #5a3416 7px 8.5px),
      repeating-linear-gradient(45deg, transparent 0 7px, #5a3416 7px 8.5px),
      linear-gradient(180deg, #caa267, #8a6236 45%, #6e4a26 55%, #a37e46);
    box-shadow:0 3px 8px rgba(30,18,6,0.5);
    clip-path: url(#deckle-scroll-cap);
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
  .fm-bar{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }
  .fm-badge{
    display:inline-flex; align-items:center; gap:6px;
    background:#d8bd82; border:1px solid #8a6a3a;
    border-radius:3px 12px 3px 12px;
    padding:4px 12px 4px 8px;
    font-size:10.5px; font-family:'Segoe UI', Tahoma, sans-serif; color:#4a3418;
    box-shadow:0 2px 3px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,240,200,.4);
  }
  .fm-badge:nth-child(odd){ transform:rotate(-0.7deg); }
  .fm-badge:nth-child(even){ transform:rotate(0.6deg); }
  .fm-badge i{ font-style:normal; font-size:13px; line-height:1; }
  .fm-badge b{ text-transform:uppercase; font-size:8.5px; letter-spacing:.07em; opacity:.68; font-weight:bold; margin-right:1px; }
  .fm-badge.w-lightner{ background:#c3d9a8; border-color:#3f6b2e; }
  .fm-badge.w-darkner{ background:#c9b3d8; border-color:#5a3a7a; }
  .fm-badge.w-ambos{ background:linear-gradient(90deg,#c3d9a8 50%,#c9b3d8 50%); border-color:#6b5040; }
  .fm-badge.w-na{ background:#c9c2ac; border-color:#5c5648; }
  .fm-badge.c-oficial{ background:#c3d9a8; border-color:#3f6b2e; }
  .fm-badge.c-fuerte{ background:#e0c478; border-color:#8a6a1e; }
  .fm-badge.c-debil{ background:#d9a892; border-color:#8a3a24; }
  .fm-badge.c-mixta{ background:#cbb98e; border-color:#6b5638; }

  ul{ margin:10px 0; padding-left:24px; }
  ul li{ margin:5px 0; font-size:15px; line-height:1.55; color:#3f3120; }

  .related-web{ display:flex; flex-wrap:wrap; gap:14px 10px; margin:24px 2px 8px; padding:20px 4px 4px; border-top:2px dashed #8a6a3a; }
  .related-tag{
    display:inline-flex; align-items:center; gap:6px; background:#e9d9a8;
    border:1px solid #8a6a3a; border-radius:3px 10px 3px 10px;
    padding:7px 13px 7px 9px; font-size:13.5px; box-shadow:1px 3px 6px rgba(30,18,4,.35);
    transition:transform .15s ease, box-shadow .15s ease;
  }
  .related-tag:nth-child(3n+1){ transform:rotate(-1.6deg); }
  .related-tag:nth-child(3n+2){ transform:rotate(1.3deg); }
  .related-tag:nth-child(3n){ transform:rotate(-0.4deg); }
  .related-tag:hover{ transform:rotate(0deg) translateY(-3px) scale(1.05); box-shadow:2px 7px 12px rgba(20,10,0,.45); z-index:2; }
  .related-tag-label a.wikilink{ font-weight:bold; color:#7a2e22; }

  .submap-cta{
    position:relative; display:flex; align-items:center; gap:14px; margin:28px 2px 30px;
    padding:16px 20px; text-decoration:none; color:#3f3120;
    background:
      repeating-linear-gradient(120deg, rgba(90,60,20,.08) 0 2px, transparent 2px 14px),
      linear-gradient(135deg,#e9d9a8,#d8bd82);
    border:1px solid #8a6a3a; border-radius:4px 12px 4px 12px;
    box-shadow:2px 6px 14px rgba(20,10,0,.4); transition:transform .18s ease, box-shadow .18s ease;
  }
  .submap-cta::before{
    content:""; position:absolute; top:-8px; left:26px; width:15px; height:15px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #ff8a7a, #c73434 65%); box-shadow:0 3px 4px rgba(0,0,0,.5);
  }
  .submap-cta:hover{ transform:translateY(-3px) rotate(-0.4deg); box-shadow:3px 10px 20px rgba(20,10,0,.5); }
  .submap-cta-icon{ font-size:32px; line-height:1; flex-shrink:0; filter:drop-shadow(1px 2px 2px rgba(0,0,0,.4)); }
  .submap-cta-title{ display:block; font-weight:bold; font-size:15.5px; color:#4a3418; }
  .submap-cta-sub{ display:block; font-size:12px; font-style:italic; color:#6b5c46; margin-top:2px; }
'''

PAGE_CSS_WET = PAGE_CSS + '''
  body{
    background-color:#5c5347;
  }
  .callout, table.note-table, .fm-bar{ position:relative; z-index:2; }
  #page-crumple{ position:fixed; inset:-10px; background:#8a8a8a; filter:url(#crumpleTex);
    mix-blend-mode:overlay; opacity:.38; pointer-events:none; z-index:1; }
  #page-creases{ position:fixed; inset:0; mix-blend-mode:overlay; opacity:.65; pointer-events:none; z-index:1;
    background:
      linear-gradient(108deg, transparent 16%, rgba(255,255,255,.35) 16.6%, rgba(0,0,0,.2) 17.2%, transparent 18%),
      linear-gradient(75deg, transparent 40%, rgba(255,255,255,.3) 40.6%, rgba(0,0,0,.16) 41.2%, transparent 42%),
      linear-gradient(130deg, transparent 64%, rgba(255,255,255,.3) 64.6%, rgba(0,0,0,.16) 65.2%, transparent 66%),
      linear-gradient(95deg, transparent 83%, rgba(255,255,255,.26) 83.6%, rgba(0,0,0,.14) 84.2%, transparent 85%);
  }
  .callout{
    background:
      radial-gradient(ellipse 60% 40% at 80% 15%, transparent 52%, rgba(122,92,52,.3) 56%, transparent 64%),
      radial-gradient(ellipse 46% 30% at 12% 90%, transparent 50%, rgba(91,66,35,.28) 55%, transparent 63%),
      #fdf6b2;
    background-blend-mode:multiply,multiply,normal;
    clip-path: url(#deckle-card-soft);
    box-shadow:2px 5px 10px rgba(0,0,0,.32), inset 0 0 22px rgba(90,64,32,.25);
    padding:22px 28px 26px;
  }
  .callout-info{ background-color:#cfe6f7; }
  .callout-tip{ background-color:#d9f0d2; }
  .callout-example{ background-color:#fdf1b8; }
  .callout-danger{ background-color:#f8d6d6; }
  .callout-quote{ background-color:#e6d9f5; }
  .callout-question{ background-color:#fbe3b0; }
  .callout .callout{ clip-path: url(#deckle-card-soft); padding:18px 24px 22px; }
  h2, h3{ color:#2b1c0a !important; text-shadow:0 1px 1px rgba(255,240,210,.4); }
  h2{ border-bottom-color:rgba(60,40,15,.5) !important; }
'''

PAGE_CSS_RUSTED = PAGE_CSS + '''
  body{
    background-color:#3a2c22;
    background-image:
      repeating-linear-gradient(0deg, rgba(0,0,0,.18) 0 3px, transparent 3px 26px),
      radial-gradient(ellipse 70% 40% at 15% 8%, rgba(180,90,40,.35) 0, transparent 55%),
      radial-gradient(ellipse 60% 45% at 85% 92%, rgba(120,50,20,.4) 0, transparent 60%),
      radial-gradient(ellipse 90% 60% at 50% 50%, rgba(90,60,40,.25) 0, transparent 70%),
      linear-gradient(160deg, #4a382a 0%, #2e2119 100%);
  }
  h1{ color:#e8c9a0; border-bottom-color:#8a5a2e; text-transform:uppercase; letter-spacing:.06em; }
  h2, h3{ color:#e8c9a0 !important; text-transform:uppercase; letter-spacing:.05em; text-shadow:1px 1px 0 rgba(0,0,0,.5); }
  h2{ border-bottom-color:#8a5a2e !important; }
  p{ color:#e6dcc8; }
  figcaption{ color:#c9a878; }
  .fm-badge{ background:#5a4130; border-color:#8a5a2e; color:#e8c9a0; }
  .wikilink{ color:#e0a860; border-bottom-color:#e0a860; }
  a.wikilink:hover{ background:rgba(224,168,96,.15); }

  /* --- postits como placas de metal remachadas, oxidadas por los bordes --- */
  .callout{
    position:relative;
    background:
      radial-gradient(ellipse 140% 100% at 50% -10%, rgba(255,255,255,.05), transparent 40%),
      repeating-linear-gradient(95deg, rgba(0,0,0,.08) 0 2px, transparent 2px 5px),
      linear-gradient(155deg, #6b5540 0%, #4a3626 60%, #3a2c22 100%);
    background-color:#584434;
    border:1px solid #2a1e14;
    border-radius:3px;
    box-shadow:2px 5px 12px rgba(0,0,0,.5), inset 0 0 30px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.08);
    padding:20px 24px 24px;
  }
  .callout::before{
    content:none;
  }
  .callout::after{
    content:""; position:absolute; inset:0; pointer-events:none; border-radius:3px;
    background:
      radial-gradient(circle 14px at 14px 14px, rgba(0,0,0,.55) 0 40%, transparent 42%),
      radial-gradient(circle 14px at calc(100% - 14px) 14px, rgba(0,0,0,.55) 0 40%, transparent 42%),
      radial-gradient(circle 14px at 14px calc(100% - 14px), rgba(0,0,0,.55) 0 40%, transparent 42%),
      radial-gradient(circle 14px at calc(100% - 14px) calc(100% - 14px), rgba(0,0,0,.55) 0 40%, transparent 42%),
      radial-gradient(circle 5px at 14px 14px, #c9a878 0 55%, #7a5230 60%, transparent 65%),
      radial-gradient(circle 5px at calc(100% - 14px) 14px, #c9a878 0 55%, #7a5230 60%, transparent 65%),
      radial-gradient(circle 5px at 14px calc(100% - 14px), #c9a878 0 55%, #7a5230 60%, transparent 65%),
      radial-gradient(circle 5px at calc(100% - 14px) calc(100% - 14px), #c9a878 0 55%, #7a5230 60%, transparent 65%);
  }
  .callout-title{ color:#f3ead6; text-shadow:1px 1px 0 rgba(0,0,0,.5); }
  .callout-body p{ color:#e6dcc8; }
  .callout-info{ background-color:#3f5a5e; }
  .callout-tip{ background-color:#3f5c40; }
  .callout-example{ background-color:#6b5228; }
  .callout-danger{ background-color:#6b332a; }
  .callout-quote{ background-color:#4a3a5a; }
  .callout-question{ background-color:#6b4f22; }
  .callout .callout{ box-shadow:3px 7px 16px rgba(0,0,0,.55), inset 0 0 24px rgba(0,0,0,.35); }
  table.note-table{ background:#4a3828; }
  table.note-table th, table.note-table td{ border-color:#2a1e14; color:#e6dcc8; }
  .related-web{ border-top-color:#8a5a2e; }
  .related-tag{ background:#584434; border-color:#8a5a2e; color:#e6dcc8; }
  .related-tag-label a.wikilink{ color:#e0a860; }
  .submap-cta{ background:linear-gradient(135deg,#584434,#3a2c22); border-color:#8a5a2e; color:#e6dcc8; }
  .submap-cta-title{ color:#f3ead6; }
  .submap-cta-sub{ color:#c9a878; }
'''

PAGE_CSS_CRYSTAL = PAGE_CSS + '''
  body{
    background-color:#0d0e1a;
    background-image:
      radial-gradient(ellipse 60% 40% at 20% 10%, rgba(120,90,220,.25) 0, transparent 55%),
      radial-gradient(ellipse 55% 45% at 85% 85%, rgba(60,180,220,.22) 0, transparent 60%),
      radial-gradient(ellipse 80% 60% at 50% 50%, rgba(40,30,80,.5) 0, transparent 70%),
      repeating-conic-gradient(from 0deg at 50% 0%, rgba(255,255,255,.02) 0deg 8deg, transparent 8deg 16deg),
      linear-gradient(160deg, #17182c 0%, #0a0b14 100%);
  }
  h1{ color:#cfe0ff; border-bottom-color:#6b5fd8; }
  h2, h3{ color:#cfe0ff !important; text-shadow:0 0 8px rgba(120,140,255,.5); }
  h2{ border-bottom-color:#6b5fd8 !important; }
  p{ color:#d8dcf0; }
  figcaption{ color:#a8b0e0; }
  .fm-badge{ background:#232544; border-color:#6b5fd8; color:#cfe0ff; }
  .wikilink{ color:#8fd8ff; border-bottom-color:#8fd8ff; }
  a.wikilink:hover{ background:rgba(143,216,255,.12); }

  /* --- postits como esquirlas de cristal traslucidas, con brillo interno --- */
  .callout{
    position:relative;
    background:
      linear-gradient(135deg, rgba(120,110,220,.16), rgba(40,180,220,.10) 55%, rgba(20,20,40,.3));
    background-color:#1a1c34;
    border:1px solid rgba(140,150,255,.35);
    clip-path:polygon(2% 0%, 96% 0%, 100% 8%, 100% 94%, 98% 100%, 4% 100%, 0% 92%, 0% 6%);
    box-shadow:0 0 18px rgba(110,120,240,.25), 0 6px 16px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.08);
    padding:22px 26px 26px;
  }
  .callout-title{ color:#e4ecff; text-shadow:0 0 6px rgba(140,160,255,.6); }
  .callout-body p{ color:#d8dcf0; }
  .callout-info{ background-color:#1e2f52; }
  .callout-tip{ background-color:#1e4438; }
  .callout-example{ background-color:#3a3350; }
  .callout-danger{ background-color:#4a2438; }
  .callout-quote{ background-color:#332a54; }
  .callout-question{ background-color:#2a3a5c; }
  .callout .callout{ clip-path:polygon(3% 0%, 95% 0%, 100% 10%, 100% 92%, 97% 100%, 5% 100%, 0% 90%, 0% 8%);
    box-shadow:0 0 22px rgba(110,120,240,.3), 0 8px 20px rgba(0,0,0,.55); }
  table.note-table{ background:#1a1c34; }
  table.note-table th, table.note-table td{ border-color:rgba(140,150,255,.3); color:#d8dcf0; }
  .related-web{ border-top-color:#6b5fd8; }
  .related-tag{ background:#1e2044; border-color:#6b5fd8; color:#d8dcf0; box-shadow:0 0 8px rgba(110,120,240,.25); }
  .related-tag-label a.wikilink{ color:#8fd8ff; }
  .submap-cta{ background:linear-gradient(135deg,#232544,#141530); border-color:#6b5fd8; color:#d8dcf0;
    box-shadow:0 0 16px rgba(110,120,240,.3), 2px 6px 12px rgba(0,0,0,.4); }
  .submap-cta-title{ color:#e4ecff; }
  .submap-cta-sub{ color:#a8b0e0; }
'''

DECKLE_DEFS_SVG = '''
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
<clipPath id="deckle-card-soft" clipPathUnits="objectBoundingBox">
  <path d="M0.005,0.02 C0.02,0.005 0.06,0.015 0.10,0.008 C0.16,0.018 0.22,0.005 0.28,0.012
    C0.36,0.02 0.44,0.005 0.52,0.012 C0.60,0.02 0.68,0.005 0.76,0.012
    C0.84,0.02 0.90,0.008 0.96,0.015 C0.99,0.02 0.995,0.03 0.995,0.05
    L0.995,0.95
    C0.995,0.97 0.99,0.98 0.96,0.985 C0.90,0.992 0.84,0.98 0.76,0.988
    C0.68,0.995 0.60,0.98 0.52,0.988 C0.44,0.995 0.36,0.98 0.28,0.988
    C0.22,0.995 0.16,0.982 0.10,0.992 C0.06,0.985 0.02,0.995 0.005,0.98
    L0.005,0.05
    C0.005,0.04 0.005,0.03 0.005,0.02 Z" />
</clipPath>
<clipPath id="deckle-page" clipPathUnits="objectBoundingBox">
  <path d="M0.005,0.03 C0.02,0.005 0.10,0.00 0.18,0.015 C0.27,0.03 0.34,0.00 0.43,0.018
    C0.52,0.035 0.59,0.00 0.68,0.02 C0.77,0.035 0.85,0.005 0.92,0.02
    C0.97,0.03 0.995,0.05 0.995,0.08 C1.005,0.16 0.985,0.22 0.995,0.30
    C1.005,0.38 0.98,0.44 0.995,0.52 C1.005,0.60 0.985,0.66 0.998,0.74
    C1.005,0.82 0.98,0.88 0.99,0.94 C0.995,0.975 0.96,0.995 0.90,0.998
    C0.82,1.005 0.74,0.985 0.65,0.998 C0.56,1.008 0.47,0.985 0.38,0.998
    C0.29,1.008 0.20,0.985 0.12,0.995 C0.06,1.003 0.02,0.985 0.008,0.94
    C-0.005,0.88 0.015,0.82 0.005,0.75 C-0.005,0.67 0.018,0.60 0.005,0.52
    C-0.005,0.44 0.018,0.37 0.005,0.30 C-0.005,0.22 0.018,0.15 0.005,0.08
    C0.00,0.05 0.00,0.04 0.005,0.03 Z" />
</clipPath>
<clipPath id="deckle-scroll" clipPathUnits="objectBoundingBox">
  <path d="M0,0.02 C0.06,0.005 0.14,0.03 0.22,0.01 C0.30,0.03 0.38,0.005 0.46,0.02
    C0.54,0.035 0.62,0.005 0.70,0.02 C0.78,0.035 0.86,0.005 0.94,0.02 C1,0.03 1,0.05 1,0.08
    L1,0.92 C1,0.95 1,0.97 0.94,0.98 C0.86,0.995 0.78,0.965 0.70,0.98
    C0.62,0.995 0.54,0.965 0.46,0.98 C0.38,0.995 0.30,0.97 0.22,0.99 C0.14,0.97 0.06,0.995 0,0.98
    C0,0.95 0,0.93 0,0.90 L0,0.10 C0,0.06 0,0.04 0,0.02 Z" />
</clipPath>
<clipPath id="deckle-scroll-cap" clipPathUnits="objectBoundingBox">
  <path d="M0,0.15 C0.06,0.02 0.14,0.28 0.22,0.08 C0.30,0.26 0.38,0.02 0.46,0.18
    C0.54,0.30 0.62,0.03 0.70,0.16 C0.78,0.28 0.86,0.02 0.94,0.14 C1,0.22 1,0.3 1,0.4
    L1,0.85 C0.9,0.95 0.8,0.8 0.7,0.92 C0.6,0.8 0.5,0.96 0.4,0.85
    C0.3,0.96 0.2,0.82 0.1,0.94 C0.04,0.86 0,0.8 0,0.7 L0,0.4 C0,0.3 0,0.22 0,0.15 Z" />
</clipPath>
</defs>
</svg>
'''

PAGE_TMPL = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{defs}{crumple}{body}
</body>
</html>
'''

def render_page(title_escaped, body_html, theme="postit"):
    if theme == "parchment":
        css = PAGE_CSS_PARCHMENT
        defs = DECKLE_DEFS_SVG
        crumple = ""
    elif theme == "wet":
        css = PAGE_CSS_WET
        defs = DECKLE_DEFS_SVG
        crumple = '<div id="page-crumple"></div><div id="page-creases"></div>'
    elif theme == "rusted":
        css = PAGE_CSS_RUSTED
        defs = ""
        crumple = ""
    elif theme == "crystal":
        css = PAGE_CSS_CRYSTAL
        defs = ""
        crumple = ""
    else:
        css = PAGE_CSS
        defs = ""
        crumple = ""
    return PAGE_TMPL.format(title=title_escaped, css=css, defs=defs, crumple=crumple, body=body_html)

