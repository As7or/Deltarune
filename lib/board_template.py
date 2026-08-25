BOARD_TEMPLATE = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{page_title}</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M4 26 L15 15' stroke='%23b23c30' stroke-width='2' fill='none'/%3E%3Ccircle cx='17' cy='13' r='6' fill='%23c73434'/%3E%3Ccircle cx='14.5' cy='10.5' r='1.8' fill='%23ffb3b3'/%3E%3C/svg%3E">
<style>
  :root{{
    --cork-base: #5c5347;
    --cork-shadow: rgba(15,12,8,0.55);
  }}
  html,body{{ margin:0; padding:0; font-family:'Segoe UI', Tahoma, sans-serif; height:100%; overflow:hidden; }}
  #viewport{{
    position:relative; width:100%; height:100vh; overflow:hidden;
    background-color: var(--cork-base);
    background-image:
      radial-gradient(ellipse 70% 55% at 42% 8%, rgba(255,244,214,0.10) 0%, transparent 55%),
      radial-gradient(circle at 15% 20%, rgba(255,255,255,0.045) 0, transparent 40%),
      radial-gradient(circle at 80% 10%, rgba(0,0,0,0.12) 0, transparent 35%),
      radial-gradient(circle at 60% 75%, rgba(0,0,0,0.16) 0, transparent 45%),
      radial-gradient(circle at 30% 85%, rgba(255,255,255,0.035) 0, transparent 40%),
      radial-gradient(circle at 8% 15%, rgba(80,50,20,.55) 0, transparent 1.4px),
      radial-gradient(circle at 63% 41%, rgba(80,50,20,.5) 0, transparent 1.1px),
      radial-gradient(circle at 27% 68%, rgba(80,50,20,.5) 0, transparent 1.3px),
      radial-gradient(circle at 91% 77%, rgba(80,50,20,.45) 0, transparent 1px),
      radial-gradient(circle at 47% 92%, rgba(255,220,170,.12) 0, transparent 1.2px),
      radial-gradient(circle at 75% 22%, rgba(255,220,170,.1) 0, transparent 1px),
      repeating-radial-gradient(circle at 50% 50%, rgba(60,38,12,0.12) 0px, transparent 2px, transparent 6px);
    background-size: auto, auto, auto, auto, auto, 46px 46px, 38px 38px, 52px 52px, 41px 41px, 33px 33px, 44px 44px, auto;
    cursor: grab;
  }}
  #viewport.panning{{ cursor: grabbing; }}
  #board{{ position:absolute; top:0; left:0; width:{board_w}px; height:{board_h}px; transform-origin: 0 0; will-change:transform; }}
  svg#strings{{ position:absolute; top:0; left:0; width:100%; height:100%; overflow:visible; }}
  .string-group{{ cursor:default; transition:opacity .2s ease; }}
  .string-hit{{ stroke:transparent; stroke-width:16; fill:none; pointer-events:stroke; }}
  .string-shadow{{ stroke:rgba(0,0,0,0.3); stroke-width:3; fill:none; }}
  .string-visible{{ fill:none; stroke-width:1.8; stroke-linecap:round; }}
  .string-twist{{ fill:none; stroke-width:1.1; stroke:rgba(255,255,255,.62); stroke-linecap:round; mix-blend-mode:overlay; }}
  .string-twist-dark{{ fill:none; stroke-width:.9; stroke:rgba(0,0,0,.35); stroke-linecap:round; mix-blend-mode:multiply; }}
  .string-knot{{ fill:#2a1c10; opacity:.75; }}
  #highlight-svg{{ position:absolute; top:0; left:0; width:100%; height:100%; overflow:visible; pointer-events:none; z-index:9999; }}
  .highlight-shadow{{ stroke:rgba(0,0,0,0.32); stroke-width:5.5; fill:none; }}
  .highlight-visible{{ stroke-width:4.5; fill:none; stroke-linecap:round; }}
  .highlight-label-bg{{ fill:rgba(35,24,12,0.92); }}
  .highlight-label{{ font-size:14px; font-weight:bold; fill:#efe6d3; }}
  .node{{ position:absolute; text-align:center; cursor:pointer; user-select:none; transition:transform .18s ease, filter .18s ease; z-index:2; }}
  .node::before{{
    content:""; position:absolute; left:8%; right:8%; bottom:-9px; height:16px; z-index:-1;
    background:radial-gradient(ellipse 60% 100% at 50% 0%, rgba(10,7,4,.5), transparent 72%);
    filter:blur(2px); transition:opacity .18s ease, transform .18s ease; transform-origin:top center;
  }}
  .node:hover{{ transform:rotate(0deg) scale(1.14) !important; z-index:10; filter:drop-shadow(0 14px 16px rgba(0,0,0,.4)); }}
  .node:hover::before{{ transform:scaleX(1.3) translateY(4px); opacity:.85; }}
  .node.dimmed{{ opacity:.22; filter:saturate(.5); }}
  .card{{ background:#fdfaf3; padding:6px 6px 8px 6px; border-radius:2px; box-shadow:3px 6px 10px var(--cork-shadow); }}
  .thumb{{ width:100%; display:flex; align-items:center; justify-content:center; overflow:hidden; background-color:#3a3a3a; }}
  .thumb-dark{{ background-color:#f2f2f2; }}
  .thumb img{{ width:100%; height:100%; object-fit:contain; display:block; image-rendering:pixelated; }}

  .news-clip{{
    position:absolute; width:560px; z-index:3; transform:rotate(-0.8deg);
    background:
      repeating-linear-gradient(0deg, rgba(0,0,0,.03) 0px, rgba(0,0,0,.03) 1px, transparent 1px, transparent 3px),
      radial-gradient(circle at 8% 12%, rgba(0,0,0,.05) 0, transparent 1px),
      radial-gradient(circle at 34% 68%, rgba(0,0,0,.045) 0, transparent 1px),
      radial-gradient(circle at 62% 22%, rgba(0,0,0,.05) 0, transparent 1px),
      radial-gradient(circle at 88% 55%, rgba(0,0,0,.045) 0, transparent 1px),
      #ece5d3;
    background-size: auto, 5px 5px, 6px 6px, 5px 5px, 6px 6px, auto;
    box-shadow:3px 8px 16px rgba(0,0,0,.5);
    padding:16px 20px 16px;
    font-family: Georgia, 'Times New Roman', serif;
    color:#241f16;
    clip-path: polygon(0% 1.5%, 6% 0%, 22% 1%, 40% 0.3%, 58% 1%, 76% 0.2%, 92% 1%, 100% 0%,
      99% 12%, 100% 30%, 98.5% 48%, 100% 66%, 99% 84%, 100% 97%,
      92% 100%, 74% 98.7%, 56% 100%, 38% 98.7%, 20% 100%, 3% 98.5%, 0% 88%, 1.2% 70%, 0% 52%, 1.2% 34%, 0% 16%);
  }}
  .news-clip .pin{{ position:absolute; top:-9px; left:50%; transform:translateX(-50%); width:15px; height:15px; z-index:5; }}
  .news-clip .pin svg{{ width:100%; height:100%; display:block; filter:drop-shadow(1px 2px 1px rgba(0,0,0,0.4)); }}
  .news-clip .news-masthead{{
    display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:6px;
    border-top:3px double #241f16; border-bottom:3px double #241f16;
    padding:5px 0; margin-bottom:12px;
  }}
  .news-clip .news-eyebrow{{
    font-family:'Segoe UI', Tahoma, sans-serif; font-size:10px; letter-spacing:.16em; text-transform:uppercase;
    color:#8a2f22; font-weight:bold;
  }}
  .news-clip .news-dateline{{
    font-family:Georgia, serif; font-style:italic; font-size:10px; color:#5a5142;
  }}
  .news-clip .news-cols{{ display:flex; gap:18px; }}
  .news-clip .news-col{{ flex:1 1 0; min-width:0; border-left:1px solid rgba(0,0,0,.18); padding-left:16px; }}
  .news-clip .news-col:first-child{{ border-left:none; padding-left:0; }}
  .news-clip .news-heading{{
    font-size:14.5px; font-weight:bold; line-height:1.15; margin-bottom:6px;
    font-variant:small-caps; letter-spacing:.02em; border-bottom:1px solid rgba(36,31,22,.25); padding-bottom:4px;
  }}
  .news-clip .news-body p{{ font-size:10.5px; line-height:1.42; margin:0 0 7px; text-align:justify; }}
  .news-clip .news-body p:first-letter{{ font-size:1.7em; font-weight:bold; float:left; line-height:.8; padding-right:2px; }}
  .news-clip .news-link{{ font-family:'Segoe UI', Tahoma, sans-serif; font-size:10px; color:#8a2f22; text-decoration:none; font-weight:bold; }}
  .news-clip .news-link:hover{{ text-decoration:underline; }}
  .noimg{{ color:#999; font-size:10px; padding:20px 0; }}
  .tag{{ font-size:8.5px; color:#8a7a5c; margin-top:5px; text-transform:uppercase; letter-spacing:.02em; }}
  .title{{ font-size:11px; font-weight:bold; color:#2c2416; margin-top:1px; }}
  .summary{{ font-size:9px; margin-top:3px; color:#5a4d38; font-style:italic; line-height:1.25; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }}
  .pin{{ position:absolute; top:-8px; left:50%; transform:translateX(-50%); width:14px; height:14px; z-index:5; }}
  .pin svg{{ width:100%; height:100%; display:block; filter:drop-shadow(1px 2px 1px rgba(0,0,0,0.4)); }}
  .submap-badge{{
    position:absolute; top:-6px; right:-6px; z-index:6; width:22px; height:22px;
    background:#fdfaf3; border-radius:50%; display:flex; align-items:center; justify-content:center;
    font-size:12px; box-shadow:1px 2px 4px rgba(0,0,0,0.4); text-decoration:none;
    transition:transform .15s ease;
  }}
  .submap-badge:hover{{ transform:scale(1.25); }}
  #legend{{ position:fixed; bottom:14px; left:14px; background:rgba(253,250,243,0.92); border-radius:6px; padding:10px 14px; font-size:11px; color:#3a2f22; box-shadow:2px 3px 8px rgba(0,0,0,0.25); z-index:90; }}
  #legend div{{ margin:3px 0; display:flex; align-items:center; gap:6px; }}
  #legend .swatch{{ width:20px; height:3px; display:inline-block; border-radius:2px; }}
  #legend .dot{{ width:11px; height:11px; border-radius:50%; display:inline-block; }}
  #zoomhint{{ position:fixed; bottom:14px; right:14px; background:rgba(253,250,243,0.92); border-radius:6px; padding:8px 12px; font-size:11px; color:#3a2f22; box-shadow:2px 3px 8px rgba(0,0,0,0.25); z-index:50; max-width:220px; }}
  #lang-switch{{
    position:fixed; top:16px; right:16px; z-index:95;
    background:linear-gradient(180deg, #fdfaf0, #f1e8d2);
    border-radius:3px; padding:14px 13px 12px; text-align:center;
    box-shadow:2px 5px 12px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(0,0,0,0.08);
    transform:rotate(-1.6deg);
  }}
  #lang-switch .pin{{ position:absolute; top:-9px; left:50%; transform:translateX(-50%); width:16px; height:16px; }}
  #lang-switch .pin svg{{ width:100%; height:100%; display:block; filter:drop-shadow(1px 2px 1px rgba(0,0,0,0.45)); }}
  #lang-switch .lang-opt{{
    display:block; font-family:'Segoe Print','Bradley Hand','Comic Sans MS',cursive;
    font-size:14px; font-weight:700; color:#9c8c68; text-decoration:none;
    letter-spacing:.02em; line-height:1.3; transition:color .15s ease, transform .15s ease;
  }}
  #lang-switch .lang-opt:hover{{ transform:scale(1.07); }}
  #lang-switch .lang-opt.active{{ color:#a8332a; text-decoration:underline wavy rgba(168,51,42,0.6); }}
  #lang-switch .lang-track{{
    position:relative; width:14px; height:30px; margin:5px auto; border-radius:7px;
    background:#3a2f22; box-shadow:inset 0 1px 3px rgba(0,0,0,0.55);
  }}
  #lang-switch .lang-lever{{
    position:absolute; top:2px; left:2px; width:10px; height:10px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #e8dcc0, #8a7a5c 70%);
    box-shadow:0 1px 2px rgba(0,0,0,0.5); transition:top .2s ease;
  }}
  #lang-switch .lang-lever.lang-lever-en{{ top:18px; }}

  #note-panel{{
    position:fixed; background:#fbf6e9; box-shadow:-4px 0 20px rgba(0,0,0,0.4);
    z-index:100; border-radius:0;
  }}
  /* modo lateral (por defecto) */
  #note-panel.mode-side{{ top:0; right:-560px; width:540px; height:100%; transition:right .28s ease; }}
  #note-panel.mode-side.open{{ right:0; }}
  /* modo centrado: ventana grande en medio de la pantalla, para ver el detalle */
  #note-panel.mode-center{{
    top:50%; left:50%; right:auto; width:min(760px,82vw); height:86vh; border-radius:12px;
    transform:translate(-50%,-50%) scale(0.94); opacity:0; pointer-events:none;
    box-shadow:0 24px 70px rgba(0,0,0,0.55);
    transition:opacity .2s ease, transform .2s ease;
  }}
  #note-panel.mode-center.open{{ opacity:1; pointer-events:auto; transform:translate(-50%,-50%) scale(1); }}
  #note-panel .note-header{{
    background:#3a2f22; color:#f3ead6; padding:14px 20px;
    display:flex; justify-content:space-between; align-items:center; gap:10px;
    border-radius:inherit; border-bottom-left-radius:0; border-bottom-right-radius:0;
  }}
  #note-panel .note-header .btns{{ display:flex; gap:8px; }}
  #note-panel .note-header button{{
    background:none; border:1px solid #f3ead6; color:#f3ead6; border-radius:4px;
    padding:4px 10px; cursor:pointer; font-size:13px; white-space:nowrap;
  }}
  #note-panel .note-header button.active{{ background:#f3ead6; color:#3a2f22; }}
  #note-panel iframe{{ width:100%; height:calc(100% - 49px); border:none; }}
  #overlay{{ position:fixed; inset:0; background:rgba(0,0,0,0.35); opacity:0; pointer-events:none; transition:opacity .28s ease; z-index:90; }}
  #overlay.open{{ opacity:1; pointer-events:auto; }}

  /* ---- Lago: papel mojado ---- */
  .node-wet .wet-card{{
    position:relative; overflow:hidden;
    background:
      radial-gradient(ellipse 65% 45% at 22% 20%, transparent 54%, rgba(122,92,52,.4) 58%, rgba(122,92,52,.14) 64%, transparent 70%),
      radial-gradient(ellipse 50% 35% at 82% 78%, transparent 48%, rgba(91,66,35,.35) 53%, transparent 62%),
      #fdfaf3;
    background-blend-mode: multiply, multiply, normal;
    clip-path: url(#deckle-card);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 22px rgba(90,64,32,.3);
  }}
  .node-wet .crumple{{ position:absolute; inset:-4px; background:#8a8a8a; filter:url(#crumpleTex);
    mix-blend-mode:overlay; opacity:.5; pointer-events:none; z-index:1; }}
  .node-wet .creases{{ position:absolute; inset:0; mix-blend-mode:overlay; opacity:.8; pointer-events:none; z-index:1;
    background:
      linear-gradient(112deg, transparent 27%, rgba(255,255,255,.4) 28%, rgba(0,0,0,.22) 29%, transparent 30%),
      linear-gradient(64deg, transparent 55%, rgba(255,255,255,.32) 56%, rgba(0,0,0,.18) 57%, transparent 58%),
      linear-gradient(146deg, transparent 74%, rgba(255,255,255,.3) 75%, rgba(0,0,0,.16) 76%, transparent 77%); }}
  .node-wet .thumb{{ position:relative; z-index:2; filter:sepia(.3) saturate(.8) contrast(.94) brightness(.94); }}
  .node-wet .tag, .node-wet .title, .node-wet .summary{{ position:relative; z-index:2; }}

  /* ---- Shelter: placa de metal oxidada y rasgada ---- */
  .node-rusted .rusted-card{{
    position:relative; overflow:hidden; border-radius:3px; border:2px solid #7a6a52;
    background:
      repeating-linear-gradient(90deg, rgba(0,0,0,.22) 0 2px, transparent 2px 26px),
      repeating-linear-gradient(0deg, rgba(0,0,0,.14) 0 2px, transparent 2px 26px),
      radial-gradient(ellipse 70% 40% at 15% 10%, rgba(200,100,40,.32) 0, transparent 55%),
      radial-gradient(ellipse 55% 40% at 85% 90%, rgba(160,70,25,.4) 0, transparent 60%),
      linear-gradient(160deg, #6b6058 0%, #3a332e 100%);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 18px rgba(0,0,0,.4), inset 0 0 0 1px rgba(0,0,0,.4);
  }}
  .node-rusted .rust-texture{{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:
      radial-gradient(circle 18px at 30% 70%, rgba(140,70,20,.35) 0, transparent 70%),
      radial-gradient(circle 24px at 75% 25%, rgba(120,55,15,.3) 0, transparent 70%); }}
  .node-rusted .rivet{{ position:absolute; width:7px; height:7px; border-radius:50%; z-index:2;
    background:radial-gradient(circle at 35% 30%, #d8c9a8, #7a6a50 65%); box-shadow:0 1px 2px rgba(0,0,0,.6); }}
  .node-rusted .rivet-tl{{ top:6px; left:6px; }} .node-rusted .rivet-tr{{ top:6px; right:6px; }}
  .node-rusted .rivet-bl{{ bottom:6px; left:6px; }} .node-rusted .rivet-br{{ bottom:6px; right:6px; }}
  .node-rusted .tag{{ position:relative; z-index:2; color:#e8c9a0; }}
  .node-rusted .title{{ position:relative; z-index:2; color:#f3ead6; }}
  .node-rusted .summary{{ position:relative; z-index:2; color:#d8c9b0; }}

  /* ---- Cristal Oscuro: esquirla traslucida con brillo, imagen completa sin recortes ---- */
  .node-crystal .crystal-card{{
    position:relative; overflow:hidden;
    background:
      linear-gradient(135deg, rgba(120,110,220,.22), rgba(40,180,220,.14) 55%, rgba(20,20,40,.55));
    background-color:#1a1c34;
    box-shadow:0 0 14px rgba(110,120,240,.35), 3px 6px 10px rgba(0,0,0,.5);
  }}
  .node-crystal .crystal-glow{{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:radial-gradient(ellipse 60% 40% at 25% 15%, rgba(180,180,255,.25) 0, transparent 60%); }}
  .node-crystal .tag{{ position:relative; z-index:2; color:#a8b0e0; }}
  .node-crystal .title{{ position:relative; z-index:2; color:#e4ecff; text-shadow:0 0 6px rgba(140,160,255,.5); }}
  .node-crystal .summary{{ position:relative; z-index:2; color:#c8ccf0; }}

  /* ---- Conexion Undertale: caja de dialogo clasica ---- */
  .node-undertale .undertale-card{{
    background:#000; border-radius:0; box-shadow:3px 6px 10px var(--cork-shadow);
    border:3px solid #fff; padding-bottom:8px;
  }}
  .node-undertale .tag{{ color:#fff; font-family:'Courier New', monospace; }}
  .node-undertale .title{{ color:#fff; font-family:'Courier New', monospace; }}
  .node-undertale .summary{{ color:#e0e0e0; font-family:'Courier New', monospace; }}

  /* ---- Fuentes Oscuras: agua ondulante ---- */
  .node-fountain .fountain-card{{
    position:relative; overflow:hidden;
    background:
      radial-gradient(ellipse 90% 60% at 50% 0%, rgba(180,220,255,.2) 0, transparent 55%),
      linear-gradient(160deg, rgba(50,120,180,.4), rgba(10,30,55,.6)), #173a5e;
    border-radius:20px 20px 26px 26px/16px 16px 30px 30px;
    box-shadow:0 0 14px rgba(100,180,255,.4), 3px 6px 10px var(--cork-shadow);
  }}
  .node-fountain .fountain-glow{{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:radial-gradient(ellipse 60% 40% at 50% 20%, rgba(200,230,255,.3) 0, transparent 60%); }}
  .node-fountain .tag{{ position:relative; z-index:2; color:#a8d4ec; }}
  .node-fountain .title{{ position:relative; z-index:2; color:#eaf7ff; text-shadow:0 0 6px rgba(150,210,255,.6); }}
  .node-fountain .summary{{ position:relative; z-index:2; color:#d5ecfb; }}

  /* ---- Gaster: posit viejo, gris y polvoriento, con el borde medio rasgado ---- */
  .node-gaster .gaster-card{{
    position:relative; overflow:hidden; border-radius:2px;
    background:linear-gradient(155deg, #cfcfc6 0%, #adada2 55%, #949488 100%);
    box-shadow:3px 6px 10px var(--cork-shadow), inset 0 0 16px rgba(0,0,0,.18);
    clip-path: polygon(
      0% 3%, 5% 0%, 13% 2%, 20% 0%, 29% 2.5%, 37% 0%, 46% 2%, 55% 0%, 64% 2.5%, 73% 0%, 82% 2%, 91% 0%, 97% 2%, 100% 0.5%,
      98% 16%, 100% 28%, 97% 40%, 100% 54%, 98% 66%, 100% 80%, 96% 92%, 100% 100%,
      86% 97%, 72% 100%, 58% 97%, 44% 100%, 30% 97%, 16% 100%, 4% 96%,
      2% 82%, 0% 68%, 2.5% 54%, 0% 40%, 2% 26%, 0% 13%
    );
  }}
  .node-gaster .gaster-dust{{ position:absolute; inset:0; z-index:1; pointer-events:none;
    background:
      radial-gradient(circle 1px at 20% 25%, rgba(0,0,0,.4) 0, transparent 100%),
      radial-gradient(circle 1px at 65% 60%, rgba(0,0,0,.35) 0, transparent 100%),
      radial-gradient(circle 1.2px at 40% 80%, rgba(0,0,0,.3) 0, transparent 100%),
      radial-gradient(circle 1px at 85% 20%, rgba(0,0,0,.35) 0, transparent 100%),
      radial-gradient(ellipse 40% 30% at 80% 85%, rgba(60,55,55,.14) 0%, transparent 70%); }}
  .node-gaster .thumb{{ position:relative; z-index:2; filter:grayscale(1) contrast(1.05); }}
  .node-gaster .tag{{ position:relative; z-index:2; color:#5a5a50; }}
  .node-gaster .title{{ position:relative; z-index:2; color:#2c2c24; }}
  .node-gaster .summary{{ position:relative; z-index:2; color:#4a4a40; }}

  /* ---- Profecía: pergamino enrollado ---- */
  .node-scroll .scroll{{ position:relative; filter:drop-shadow(0 8px 12px rgba(0,0,0,.4)); }}
  .node-scroll .roll{{ position:relative; height:22px; width:100%; z-index:2;
    background:linear-gradient(180deg,#e8cf9a 0%,#c2a066 30%,#9c7c46 55%,#c2a066 80%,#8a6a3a 100%);
    border-radius:11px; box-shadow:inset 0 -2px 3px rgba(0,0,0,.35), inset 0 2px 2px rgba(255,255,255,.35); }}
  .node-scroll .roll::before, .node-scroll .roll::after{{
    content:""; position:absolute; top:50%; width:16px; height:16px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #ecdba8, #7a5c30 75%);
    box-shadow:0 2px 3px rgba(0,0,0,.5); transform:translateY(-50%); }}
  .node-scroll .roll::before{{ left:-8px; }}
  .node-scroll .roll::after{{ right:-8px; }}
  .node-scroll .frizz{{ display:none; }}
  .node-scroll .sheet{{ position:relative; overflow:hidden;
    background:linear-gradient(170deg,#f1e2b8,#dcc38c 55%,#c9ac78);
    margin:-2px 3px; padding:12px 10px 12px; text-align:center; border-radius:2px; }}
  .node-scroll .sheet::before{{ content:""; position:absolute; inset:0; pointer-events:none;
    background:
      radial-gradient(ellipse 130% 90% at 50% 50%, transparent 45%, rgba(120,88,32,.4) 100%),
      repeating-linear-gradient(90deg, rgba(120,88,32,.05) 0 1px, transparent 1px 7px); }}
  .node-scroll .sheet::after{{ content:""; position:absolute; inset:0; pointer-events:none;
    box-shadow:inset 0 0 0 1px rgba(120,88,32,.3); }}
  .node-scroll .tear{{ display:none; }}
  .node-scroll .sheet .thumb{{ position:relative; z-index:2; margin:0 auto 6px; filter:sepia(.2); background:transparent !important; }}
  .node-scroll .sheet .title, .node-scroll .sheet .summary{{ position:relative; z-index:2; }}
  #wood-frame{{
    position:fixed; z-index:80; pointer-events:none;
    left:0; top:0; right:0; bottom:0;
    box-shadow:
      inset 0 0 0 6px #1c0f08,
      inset 0 0 0 9px #5a3420,
      inset 0 0 0 13px #7a4a2c,
      inset 0 0 0 15px #4a2c1a,
      inset 0 0 0 17px #3a2214,
      inset 0 26px 40px -28px rgba(0,0,0,.65),
      inset 0 -26px 40px -28px rgba(0,0,0,.55),
      inset 26px 0 40px -28px rgba(0,0,0,.5),
      inset -26px 0 40px -28px rgba(0,0,0,.5);
  }}
  .frame-screw{{
    position:fixed; z-index:81; width:9px; height:9px; border-radius:50%; pointer-events:none;
    background:radial-gradient(circle at 35% 30%, #cdb48a, #4a3420 75%);
    box-shadow:0 1px 2px rgba(0,0,0,.7), inset 0 0 1px rgba(0,0,0,.5);
  }}
  #pipis-guest{{
    position:fixed; left:200px; bottom:0; z-index:84; height:22vh; max-height:210px; min-height:130px;
    pointer-events:none; image-rendering:pixelated;
    filter:drop-shadow(6px 10px 14px rgba(0,0,0,.6));
  }}
  @media (max-width: 1100px){{ #pipis-guest{{ display:none; }} }}
</style>
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
</defs>
</svg>
</head>
<body>
<div id="wood-frame"></div>
<div class="frame-screw" style="left:11px; top:11px;"></div>
<div class="frame-screw" style="right:11px; top:11px;"></div>
<div class="frame-screw" style="left:11px; bottom:11px;"></div>
<div class="frame-screw" style="right:11px; bottom:11px;"></div>
<img id="pipis-guest" src="{sprites_prefix}nike_Green_Pippins_overworld_exasperated.gif" alt="{pipis_alt}">
<div id="viewport">
  <div id="board">
    <svg id="strings"></svg>
{nodes_html}
  <svg id="highlight-svg"></svg>
  </div>
</div>
{lang_switch}
<div id="legend">
  <div><span class="dot" style="background:#2e8b46;"></span> {legend_lightner}</div>
  <div><span class="dot" style="background:#6b3fa0;"></span> {legend_darkner}</div>
  <div><span class="dot" style="background:#3a9aa6;"></span> {legend_plant}</div>
  <div><span class="dot" style="background:#c9982e;"></span> {legend_place}</div>
  <div><span class="dot" style="background:#6b7280;"></span> {legend_topic}</div>
  <div style="margin-top:6px;"><span class="swatch" style="background:#2e8b46;"></span> {legend_edge_official}</div>
  <div><span class="swatch" style="background:#c9982e;"></span> {legend_edge_strong}</div>
  <div><span class="swatch" style="background:#b23c30;"></span> {legend_edge_weak}</div>
</div>
<div id="zoomhint">{zoomhint_text}<br><span style="opacity:.65; font-style:italic;">{zoomhint_thread}</span></div>
<div id="overlay"></div>
<div id="note-panel" class="mode-side">
  <div class="note-header">
    <span id="note-title-bar">{note_panel_default_title}</span>
    <div class="btns">
      <button id="mode-side-btn" class="active" title="{mode_side_title}">▤ {mode_side_label}</button>
      <button id="mode-center-btn" title="{mode_center_title}">▣ {mode_center_label}</button>
      <button id="note-close">{note_close_label} ✕</button>
    </div>
  </div>
  <iframe id="note-frame" src=""></iframe>
</div>

<script>
const svg = document.getElementById('strings');
const NS = 'http://www.w3.org/2000/svg';
const links = [
{links_js}
];

const board = document.getElementById('board');
const viewport = document.getElementById('viewport');
let zoom = 0.55, panX = 60, panY = 60;
let pinnedNodeId = null;
const MIN_ZOOM = 0.15, MAX_ZOOM = 2.5;

function applyTransform(){{
  board.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{zoom}})`;
}}
applyTransform();

viewport.addEventListener('wheel', (e) => {{
  e.preventDefault();
  const rect = viewport.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const boardX = (px - panX) / zoom, boardY = (py - panY) / zoom;
  const delta = -e.deltaY * 0.0015;
  const newZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom + delta * zoom));
  panX = px - boardX * newZoom;
  panY = py - boardY * newZoom;
  zoom = newZoom;
  applyTransform();
}}, {{ passive: false }});

function center(el){{
  const pin = el.querySelector('.pin');
  const b = board.getBoundingClientRect();
  if(pin){{
    const pr = pin.getBoundingClientRect();
    return {{ x: (pr.left - b.left)/zoom + pr.width/zoom/2, y: (pr.top - b.top)/zoom + pr.height/zoom/2 }};
  }}
  const r = el.getBoundingClientRect();
  return {{ x: (r.left - b.left)/zoom + r.width/zoom/2, y: (r.top - b.top)/zoom + r.height/zoom/2 }};
}}

const highlightSvg = document.getElementById('highlight-svg');

function showHighlight(p1,p2,mx,my,color,label){{
  highlightSvg.innerHTML = '';
  const g = document.createElementNS(NS,'g');
  const isWeak = color.toLowerCase() === '#b23c30';
  const shownLabel = label ? (isWeak ? '🎲 ' + label : label) : '';

  const shadow = document.createElementNS(NS,'path');
  shadow.setAttribute('class','highlight-shadow');
  shadow.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my+5}} ${{p2.x}} ${{p2.y}}`);
  g.appendChild(shadow);

  const path = document.createElementNS(NS,'path');
  path.setAttribute('class','highlight-visible');
  path.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
  path.setAttribute('stroke', color);
  path.style.filter = `drop-shadow(0 0 5px ${{color}}) drop-shadow(0 0 5px ${{color}})`;
  g.appendChild(path);

  if(shownLabel){{
    const textEl = document.createElementNS(NS,'text');
    textEl.setAttribute('x', mx);
    textEl.setAttribute('y', my);
    textEl.setAttribute('text-anchor','middle');
    textEl.setAttribute('class','highlight-label');
    textEl.textContent = shownLabel;
    g.appendChild(textEl);
    highlightSvg.appendChild(g);
    const bb = textEl.getBBox();
    const bgRect = document.createElementNS(NS,'rect');
    bgRect.setAttribute('x', bb.x - 8);
    bgRect.setAttribute('y', bb.y - 4);
    bgRect.setAttribute('width', bb.width + 16);
    bgRect.setAttribute('height', bb.height + 8);
    bgRect.setAttribute('rx', 3);
    bgRect.setAttribute('class','highlight-label-bg');
    g.insertBefore(bgRect, textEl);
  }} else {{
    highlightSvg.appendChild(g);
  }}
}}
function hideHighlight(){{
  highlightSvg.innerHTML = '';
}}

function edgeSeed(a,b){{
  let s = 0;
  const str = a+'|'+b;
  for(let i=0;i<str.length;i++) s = (s*31 + str.charCodeAt(i)) % 1000;
  return s/1000;
}}

const nodeGroups = {{}}; // id -> [ {{g, other}} ]

function draw(){{
  svg.innerHTML = '';
  highlightSvg.innerHTML = '';
  for(const k in nodeGroups) delete nodeGroups[k];
  links.forEach(([a,b,color,label])=>{{
    const elA = document.querySelector(`[data-id="${{a}}"]`);
    const elB = document.querySelector(`[data-id="${{b}}"]`);
    if(!elA||!elB) return;
    const p1 = center(elA), p2 = center(elB);
    const dist = Math.hypot(p2.x-p1.x, p2.y-p1.y);
    const jitter = 0.7 + edgeSeed(a,b)*0.6; // 0.7-1.3, cada cuerda con tension distinta
    const sag = Math.min(55, dist*0.09*jitter);
    const bow = (edgeSeed(b,a)-0.5)*18; // ligero arco lateral, no siempre cae recto
    const mx = (p1.x+p2.x)/2 + bow, my = (p1.y+p2.y)/2 + sag;

    const g = document.createElementNS(NS,'g');
    g.setAttribute('class','string-group');

    const shadow = document.createElementNS(NS,'path');
    shadow.setAttribute('class','string-shadow');
    shadow.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my+5}} ${{p2.x}} ${{p2.y}}`);
    g.appendChild(shadow);

    const path = document.createElementNS(NS,'path');
    path.setAttribute('class','string-visible');
    path.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
    path.setAttribute('stroke', color);
    g.appendChild(path);

    // brillo de hilo trenzado: dos pasadas finas desfasadas en direcciones opuestas
    // (una clara, una oscura) para simular las dos hebras retorcidas del cordel,
    // en vez de una linea de vector plana.
    const twist = document.createElementNS(NS,'path');
    twist.setAttribute('class','string-twist');
    twist.setAttribute('d', `M ${{p1.x}} ${{p1.y-0.9}} Q ${{mx}} ${{my-0.9}} ${{p2.x}} ${{p2.y-0.9}}`);
    g.appendChild(twist);

    const twistDark = document.createElementNS(NS,'path');
    twistDark.setAttribute('class','string-twist-dark');
    twistDark.setAttribute('d', `M ${{p1.x}} ${{p1.y+0.9}} Q ${{mx}} ${{my+0.9}} ${{p2.x}} ${{p2.y+0.9}}`);
    g.appendChild(twistDark);

    [p1,p2].forEach(p=>{{
      const knot = document.createElementNS(NS,'circle');
      knot.setAttribute('class','string-knot');
      knot.setAttribute('cx', p.x); knot.setAttribute('cy', p.y); knot.setAttribute('r', 2.1);
      g.appendChild(knot);
    }});

    const hit = document.createElementNS(NS,'path');
    hit.setAttribute('class','string-hit');
    hit.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
    g.appendChild(hit);

    svg.appendChild(g);

    (nodeGroups[a] = nodeGroups[a]||[]).push({{g, other:b}});
    (nodeGroups[b] = nodeGroups[b]||[]).push({{g, other:a}});

    // el "encendido" y la etiqueta se dibujan en una capa aparte, siempre por encima
    // de todo (incluidas las fotos), sin mover nada del DOM original — así el
    // mouseleave nunca se pierde y no se acumulan cuerdas iluminadas.
    hit.addEventListener('mouseenter', ()=> showHighlight(p1,p2,mx,my,color,label));
    hit.addEventListener('mouseleave', hideHighlight);
  }});
  if(pinnedNodeId) applyNetworkHighlight(pinnedNodeId);
}}
window.addEventListener('resize', draw);
draw();

// pasar el raton por una nota ilumina toda su red de conexiones (como conectar
// pistas en un corcho de investigacion): las cuerdas ajenas se atenuan. Al
// hacer clic y abrir la nota, ese resaltado se queda fijado hasta que se
// cierra el panel o se abre otra nota — no hace falta mantener el raton encima.
function applyNetworkHighlight(nid){{
  const mine = nodeGroups[nid] || [];
  if(!mine.length) return;
  document.querySelectorAll('.string-group').forEach(g=> g.style.opacity = '0.12');
  document.querySelectorAll('.node').forEach(other=> other.classList.add('dimmed'));
  const selfEl = document.querySelector(`[data-id="${{nid}}"]`);
  if(selfEl) selfEl.classList.remove('dimmed');
  mine.forEach(({{g,other}})=>{{
    g.style.opacity = '1';
    const otherEl = document.querySelector(`[data-id="${{other}}"]`);
    if(otherEl) otherEl.classList.remove('dimmed');
  }});
}}
function clearNetworkHighlight(){{
  document.querySelectorAll('.string-group').forEach(g=> g.style.opacity = '');
  document.querySelectorAll('.node').forEach(other=> other.classList.remove('dimmed'));
}}

document.querySelectorAll('.node').forEach(n=>{{
  const nid = n.dataset.id;
  n.addEventListener('mouseenter', ()=>{{
    applyNetworkHighlight(nid);
  }});
  n.addEventListener('mouseleave', ()=>{{
    if(pinnedNodeId){{
      applyNetworkHighlight(pinnedNodeId);
    }} else {{
      clearNetworkHighlight();
    }}
  }});
}});

let mode = null;
let dragEl=null, offX=0, offY=0, startX=0, startY=0, moved=false;
let panStartX=0, panStartY=0, panOrigX=0, panOrigY=0;

document.querySelectorAll('.node').forEach(n=>{{
  n.addEventListener('mousedown', e=>{{
    e.stopPropagation();
    mode = 'node';
    dragEl=n;
    moved = false;
    startX = e.clientX; startY = e.clientY;
    const r=n.getBoundingClientRect();
    offX=(e.clientX-r.left)/zoom; offY=(e.clientY-r.top)/zoom;
    n.style.transition='none';
  }});
}});

viewport.addEventListener('mousedown', e=>{{
  mode = 'pan';
  panStartX = e.clientX; panStartY = e.clientY;
  panOrigX = panX; panOrigY = panY;
  viewport.classList.add('panning');
}});

window.addEventListener('mousemove', e=>{{
  if(mode === 'node' && dragEl){{
    if(Math.abs(e.clientX-startX) > 5 || Math.abs(e.clientY-startY) > 5) moved = true;
    const b=board.getBoundingClientRect();
    dragEl.style.left = ((e.clientX-b.left)/zoom-offX)+'px';
    dragEl.style.top = ((e.clientY-b.top)/zoom-offY)+'px';
    draw();
  }} else if(mode === 'pan'){{
    panX = panOrigX + (e.clientX - panStartX);
    panY = panOrigY + (e.clientY - panStartY);
    applyTransform();
  }}
}});

window.addEventListener('mouseup', ()=>{{
  if(mode === 'node' && dragEl){{
    dragEl.style.transition='transform .15s ease';
    if(!moved){{
      const note = dragEl.dataset.note;
      const title = dragEl.querySelector('.title').textContent;
      const nid = dragEl.dataset.id;
      pinnedNodeId = nid;
      applyNetworkHighlight(nid);
      if(note){{
        openNote(note, title);
      }} else {{
        openNote(null, title);
      }}
    }}
  }}
  if(mode === 'pan'){{
    viewport.classList.remove('panning');
  }}
  mode = null;
  dragEl=null;
}});

const panel = document.getElementById('note-panel');
const overlay = document.getElementById('overlay');
const frame = document.getElementById('note-frame');
const noteTitleBar = document.getElementById('note-title-bar');
const modeSideBtn = document.getElementById('mode-side-btn');
const modeCenterBtn = document.getElementById('mode-center-btn');

function setPanelMode(mode){{
  panel.classList.remove('mode-side','mode-center');
  panel.classList.add(mode);
  modeSideBtn.classList.toggle('active', mode === 'mode-side');
  modeCenterBtn.classList.toggle('active', mode === 'mode-center');
}}
modeSideBtn.addEventListener('click', ()=> setPanelMode('mode-side'));
modeCenterBtn.addEventListener('click', ()=> setPanelMode('mode-center'));

function openNote(noteStem, label){{
  noteTitleBar.textContent = label;
  if(noteStem){{
    frame.src = 'notes/' + encodeURIComponent(noteStem) + '.html';
  }} else {{
    frame.src = 'data:text/html;charset=utf-8,' + encodeURIComponent('<body style="font-family:sans-serif;padding:20px;color:#555">{no_note_prefix} <b>'+label+'</b>.</body>');
  }}
  panel.classList.add('open');
  overlay.classList.add('open');
}}
function closeNote(){{
  panel.classList.remove('open');
  overlay.classList.remove('open');
  pinnedNodeId = null;
  clearNetworkHighlight();
}}
document.getElementById('note-close').addEventListener('click', closeNote);
overlay.addEventListener('click', closeNote);
</script>
</body>
</html>
'''


def render_ui_strings(lang):
    """Todos los textos fijos del "chrome" del corcho (leyenda, tooltip de
    zoom, controles del panel de nota, titulo de pestaña, mensaje de "aun
    no hay nota"...) que antes estaban escritos directamente en español
    dentro de BOARD_TEMPLATE. Devuelve un dict listo para pasarlo como
    **kwargs a BOARD_TEMPLATE.format(), igual que ya se hacia con
    render_lang_switch(). 'lang' es 'es' o 'en'."""
    if lang == "en":
        return dict(
            page_title="Main Corkboard — Deltarune Theories 🕵️",
            pipis_alt="Pipis, looking at the corkboard with an exasperated face",
            legend_lightner="Lightner", legend_darkner="Darkner", legend_plant="Plant",
            legend_place="Place", legend_topic="Topic / Other",
            legend_edge_official="edge: official", legend_edge_strong="edge: strong theory",
            legend_edge_weak="edge: weak theory",
            zoomhint_text="Wheel = zoom · drag empty corkboard to move · click a note = open its page",
            zoomhint_thread="🧵 Follow the thread. (Pipis would be proud.)",
            note_panel_default_title="Note",
            mode_side_title="View side-by-side", mode_side_label="Side",
            mode_center_title="View centered, bigger", mode_center_label="Centered",
            note_close_label="Close",
            no_note_prefix="There's no note yet for",
        )
    return dict(
        page_title="Corcho Principal — Deltarune Teorías 🕵️",
        pipis_alt="Pipis, mirando el corcho con cara de exasperación",
        legend_lightner="Lightner", legend_darkner="Darkner", legend_plant="Planta",
        legend_place="Lugar", legend_topic="Tema / Other",
        legend_edge_official="arista: oficial", legend_edge_strong="arista: teoría fuerte",
        legend_edge_weak="arista: teoría débil",
        zoomhint_text="Rueda = zoom · arrastra el corcho vacío para moverte · clic en una nota = abrir su página",
        zoomhint_thread="🧵 Sigue el hilo. (Pipis estaría orgulloso.)",
        note_panel_default_title="Nota",
        mode_side_title="Ver al lado", mode_side_label="Lateral",
        mode_center_title="Ver centrado, más grande", mode_center_label="Centrado",
        note_close_label="Cerrar",
        no_note_prefix="Todavía no hay nota para",
    )


def render_lang_switch(lang):
    """Interruptor ES/EN clavado al corcho -- SOLO aparece en el corcho
    principal (nunca en notas ni submapas, por decision explicita). 'lang' es
    'es' o 'en': el idioma de ESTA pagina que se esta generando ahora mismo.
    Los dos idiomas se construyen en carpetas hermanas (out_dir/ para es,
    out_dir/en/ para en), asi que el enlace cruzado es siempre relativo a un
    unico nivel de profundidad en cualquiera de los dos sentidos."""
    es_active = (lang == "es")
    en_href = "en/corcho-principal.html" if es_active else "corcho-principal.html"
    es_href = "corcho-principal.html" if es_active else "../corcho-principal.html"
    return f'''<div id="lang-switch">
    <div class="pin"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8" fill="#c73434"/><circle cx="8" cy="8" r="2.4" fill="#ffb3b3"/></svg></div>
    <a class="lang-opt lang-es{' active' if es_active else ''}" href="{es_href}">Español</a>
    <div class="lang-track"><div class="lang-lever{' lang-lever-en' if not es_active else ''}"></div></div>
    <a class="lang-opt lang-en{' active' if not es_active else ''}" href="{en_href}">English</a>
  </div>'''

