BOARD_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Corcho Principal — Deltarune Teorías 🕵️</title>
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
  .node{{ position:absolute; text-align:center; cursor:pointer; user-select:none; transition:transform .18s ease, filter .18s ease; z-index:2; contain:layout; }}
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
  .thumb-dark img{{ object-fit:cover; }}

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

  #note-panel{{
    position:fixed; background:#fbf6e9; box-shadow:-4px 0 20px rgba(0,0,0,0.4);
    z-index:100; border-radius:0;
  }}
  /* modo lateral (por defecto) */
  #note-panel.mode-side{{ top:0; right:-560px; width:540px; height:100%; transition:right .28s ease; }}
  #note-panel.mode-side.open{{ right:0; }}
  /* modo centrado: ventana grande en medio de la pantalla, para ver el detalle */
  #note-panel.mode-center{{
    top:50%; left:50%; right:auto; width:min(920px,88vw); height:86vh; border-radius:12px;
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

  /* ---- Profecía: pergamino enrollado ---- */
  .node-scroll .scroll{{ position:relative; filter:drop-shadow(0 8px 12px rgba(0,0,0,.4)); }}
  .node-scroll .roll{{ position:relative; height:26px; width:100%;
    background:linear-gradient(180deg, #8a744c 0%, #d0b47c 32%, #f2e4bc 50%, #d0b47c 68%, #8a744c 100%); }}
  .node-scroll .roll-top{{ clip-path: path("M0,13 C9,4 20,1 31,5 C41,9 50,2 61,6 C73,11 83,3 95,7 C107,11 118,4 129,8 C138,11 146,6 150,12 L150,21 C141,25 131,20 121,24 C111,28 101,22 91,25 C81,28 71,23 61,26 C51,29 41,24 31,27 C21,29 11,25 4,21 L0,13 Z"); }}
  .node-scroll .roll-bottom{{ clip-path: path("M0,15 C9,24 20,27 31,23 C41,19 50,26 61,22 C73,17 83,25 95,21 C107,17 118,24 129,20 C138,17 146,22 150,16 L150,7 C141,3 131,8 121,4 C111,0 101,7 91,3 C81,0 71,5 61,2 C51,-1 41,4 31,1 C21,-1 11,3 4,7 L0,15 Z"); }}
  .node-scroll .roll::after{{ content:""; position:absolute; inset:0;
    background:radial-gradient(ellipse 90% 100% at 50% 50%, transparent 45%, rgba(150,105,30,.5) 100%); mix-blend-mode:multiply; }}
  .node-scroll .frizz{{ position:absolute; width:9px; height:7px; background:linear-gradient(160deg,#d0b47c,#8a744c);
    border-radius:58% 42% 61% 39% / 55% 60% 40% 45%; box-shadow:0 1px 2px rgba(0,0,0,.35); }}
  .node-scroll .roll-top .frizz{{ bottom:-3px; }} .node-scroll .roll-bottom .frizz{{ top:-3px; }}
  .node-scroll .f1{{ left:14px; transform:rotate(-12deg); }} .node-scroll .f2{{ left:64px; transform:rotate(8deg); }} .node-scroll .f3{{ left:112px; transform:rotate(-6deg); }}
  .node-scroll .sheet{{ position:relative; overflow:hidden; background:linear-gradient(170deg,#ecdcae,#d0b47c 60%,#c2a877);
    margin:-3px 5px; padding:8px 6px 10px; text-align:center; }}
  .node-scroll .sheet::before{{ content:""; position:absolute; inset:0; pointer-events:none;
    background:radial-gradient(ellipse 130% 90% at 50% 50%, transparent 38%, rgba(150,108,32,.55) 100%); }}
  .node-scroll .tear{{ position:absolute; width:8px; height:12px; background:var(--cork-base); z-index:3; }}
  .node-scroll .tear.left{{ left:-1px; clip-path:polygon(100% 0%, 0% 35%, 100% 55%, 20% 75%, 100% 100%); }}
  .node-scroll .tear.right{{ right:-1px; clip-path:polygon(0% 0%, 100% 30%, 10% 50%, 100% 70%, 0% 100%); }}
  .node-scroll .tear.t1{{ top:7px; }} .node-scroll .tear.t2{{ bottom:5px; }}
  .node-scroll .sheet .thumb{{ position:relative; z-index:2; margin:0 auto 4px; filter:sepia(.2); background:transparent !important; }}
  .node-scroll .sheet .title, .node-scroll .sheet .summary{{ position:relative; z-index:2; }}

  /* ---- Cristal Oscuro: gema facetada con brillo interior ---- */
  .node-crystal{{ text-align:center; }}
  .node-crystal .crystal{{
    position:relative; padding:22px 10px 14px;
    clip-path: polygon(50% 0%, 76% 7%, 100% 26%, 90% 50%, 100% 74%, 76% 93%, 50% 100%, 24% 93%, 0% 74%, 10% 50%, 0% 26%, 24% 7%);
    background:
      linear-gradient(112deg, transparent 16%, rgba(255,255,255,.32) 19%, transparent 24%),
      linear-gradient(68deg, transparent 52%, rgba(205,175,255,.26) 56%, transparent 62%),
      linear-gradient(155deg, transparent 72%, rgba(255,255,255,.16) 75%, transparent 80%),
      radial-gradient(circle at 46% 32%, rgba(195,155,245,.55), transparent 55%),
      linear-gradient(150deg, #170c26 0%, #3c2359 32%, #150c1f 58%, #4d2f70 84%, #150c1f 100%);
    box-shadow: 0 0 24px 3px rgba(130,80,200,.45), 0 12px 20px rgba(0,0,0,.55);
    animation: crystal-glow 4.5s ease-in-out infinite;
  }}
  @keyframes crystal-glow{{
    0%,100%{{ box-shadow: 0 0 22px 2px rgba(130,80,200,.4), 0 12px 20px rgba(0,0,0,.55); }}
    50%{{ box-shadow: 0 0 32px 7px rgba(160,110,230,.6), 0 12px 20px rgba(0,0,0,.55); }}
  }}
  .node-crystal .crystal-thumb{{
    background:transparent !important; margin-bottom:6px;
    filter: brightness(1.15) saturate(1.3) drop-shadow(0 0 7px rgba(170,120,235,.7));
  }}
  .node-crystal .title{{ color:#efe4ff; text-shadow:0 0 6px rgba(170,120,235,.8); font-family:Arial,sans-serif; font-size:11.5px; font-weight:bold; }}
  .node-crystal .summary{{ color:#c9b6e8; font-size:9px; font-style:italic; margin-top:2px; }}

  /* ---- Shelter: nota oxidada de refugio/bunker ---- */
  .node-rust{{ position:relative; }}
  .rivet{{
    position:absolute; top:-8px; left:50%; transform:translateX(-50%); z-index:5;
    width:13px; height:13px; border-radius:50%;
    background:radial-gradient(circle at 35% 30%, #d8d4c6, #4a463c 78%);
    box-shadow:0 2px 3px rgba(0,0,0,.6), inset 0 0 2px rgba(0,0,0,.5);
  }}
  .rust-card{{ position:relative; overflow:hidden;
    background:
      radial-gradient(circle at 18% 22%, rgba(170,85,25,.55) 0, transparent 20%),
      radial-gradient(circle at 78% 14%, rgba(150,68,18,.5) 0, transparent 17%),
      radial-gradient(circle at 60% 72%, rgba(165,80,22,.5) 0, transparent 23%),
      radial-gradient(circle at 12% 82%, rgba(140,62,15,.45) 0, transparent 18%),
      radial-gradient(circle at 92% 60%, rgba(150,70,20,.4) 0, transparent 15%),
      linear-gradient(155deg, #d6cfb8 0%, #c2b89a 45%, #a89e82 75%, #8f8770 100%);
    background-blend-mode: multiply, multiply, multiply, multiply, multiply, normal;
  }}
  .rust-stains{{ position:absolute; inset:0; pointer-events:none;
    background-image:
      radial-gradient(circle at 30% 40%, rgba(120,55,15,.35) 0 6px, transparent 8px),
      radial-gradient(circle at 70% 65%, rgba(120,55,15,.3) 0 4px, transparent 6px),
      radial-gradient(circle at 45% 85%, rgba(120,55,15,.3) 0 3px, transparent 5px);
    mix-blend-mode:multiply;
  }}
  .rust-streaks{{ position:absolute; inset:0; pointer-events:none; opacity:.55;
    background:repeating-linear-gradient(179deg, transparent 0 14px, rgba(135,60,16,.3) 15px 18px, transparent 19px 34px);
    mix-blend-mode:multiply;
  }}
  .node-rust .title{{ color:#3a2f1c; }}
  .node-rust .tag{{ color:#7a5636; }}
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
<img id="pipis-guest" src="Sprites/nike_Green_Pippins_overworld_exasperated.gif" alt="Pipis, mirando el corcho con cara de exasperación">
<div id="viewport">
  <div id="board">
    <svg id="strings"></svg>
{nodes_html}
  <svg id="highlight-svg"></svg>
  </div>
</div>
<div id="legend">
  <div><span class="dot" style="background:#2e8b46;"></span> Lightner</div>
  <div><span class="dot" style="background:#6b3fa0;"></span> Darkner</div>
  <div><span class="dot" style="background:#c9982e;"></span> Lugar</div>
  <div><span class="dot" style="background:#6b7280;"></span> Tema / Other</div>
  <div style="margin-top:6px;"><span class="swatch" style="background:#2e8b46;"></span> arista: oficial</div>
  <div><span class="swatch" style="background:#c9982e;"></span> arista: teoría fuerte</div>
  <div><span class="swatch" style="background:#b23c30;"></span> arista: teoría débil</div>
</div>
<div id="zoomhint">Rueda = zoom · arrastra el corcho vacío para moverte · clic en una nota = abrir su página<br><span style="opacity:.65; font-style:italic;">🧵 Sigue el hilo. (Pipis estaría orgulloso.)</span></div>
<div id="overlay"></div>
<div id="note-panel" class="mode-side">
  <div class="note-header">
    <span id="note-title-bar">Nota</span>
    <div class="btns">
      <button id="mode-side-btn" class="active" title="Ver al lado">▤ Lateral</button>
      <button id="mode-center-btn" title="Ver centrado, más grande">▣ Centrado</button>
      <button id="note-close">Cerrar ✕</button>
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

const nodeGroups = {{}}; // id -> [ edgeRecord, ... ]
const nodeEls = {{}}; // cache de elementos .node por id, para no repetir querySelector

function edgeGeometry(a, b){{
  const elA = nodeEls[a] || (nodeEls[a] = document.querySelector(`[data-id="${{a}}"]`));
  const elB = nodeEls[b] || (nodeEls[b] = document.querySelector(`[data-id="${{b}}"]`));
  if(!elA||!elB) return null;
  const p1 = center(elA), p2 = center(elB);
  const dist = Math.hypot(p2.x-p1.x, p2.y-p1.y);
  const jitter = 0.7 + edgeSeed(a,b)*0.6; // 0.7-1.3, cada cuerda con tension distinta
  const sag = Math.min(55, dist*0.09*jitter);
  const bow = (edgeSeed(b,a)-0.5)*18; // ligero arco lateral, no siempre cae recto
  const mx = (p1.x+p2.x)/2 + bow, my = (p1.y+p2.y)/2 + sag;
  return {{p1,p2,mx,my}};
}}

function applyEdgeGeometry(rec, geo){{
  const {{p1,p2,mx,my}} = geo;
  rec.shadow.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my+5}} ${{p2.x}} ${{p2.y}}`);
  rec.path.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
  rec.twist.setAttribute('d', `M ${{p1.x}} ${{p1.y-0.9}} Q ${{mx}} ${{my-0.9}} ${{p2.x}} ${{p2.y-0.9}}`);
  rec.twistDark.setAttribute('d', `M ${{p1.x}} ${{p1.y+0.9}} Q ${{mx}} ${{my+0.9}} ${{p2.x}} ${{p2.y+0.9}}`);
  rec.hit.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
  rec.knotA.setAttribute('cx', p1.x); rec.knotA.setAttribute('cy', p1.y);
  rec.knotB.setAttribute('cx', p2.x); rec.knotB.setAttribute('cy', p2.y);
  rec.p1 = p1; rec.p2 = p2; rec.mx = mx; rec.my = my;
}}

// Durante el arrastre de una nota no hace falta reconstruir las 245 conexiones
// enteras en cada mousemove (eso es lo que iba lento) — solo recalculamos las
// que tocan a esa nota en concreto, reutilizando los mismos elementos SVG.
function updateEdgesFor(nodeId){{
  const recs = nodeGroups[nodeId];
  if(!recs) return;
  recs.forEach(rec=>{{
    const geo = edgeGeometry(rec.a, rec.b);
    if(geo) applyEdgeGeometry(rec, geo);
  }});
}}

function draw(){{
  svg.innerHTML = '';
  highlightSvg.innerHTML = '';
  for(const k in nodeGroups) delete nodeGroups[k];
  for(const k in nodeEls) delete nodeEls[k];
  links.forEach(([a,b,color,label])=>{{
    const geo = edgeGeometry(a, b);
    if(!geo) return;
    const {{p1,p2,mx,my}} = geo;

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

    const knotA = document.createElementNS(NS,'circle');
    knotA.setAttribute('class','string-knot');
    knotA.setAttribute('cx', p1.x); knotA.setAttribute('cy', p1.y); knotA.setAttribute('r', 2.1);
    g.appendChild(knotA);
    const knotB = document.createElementNS(NS,'circle');
    knotB.setAttribute('class','string-knot');
    knotB.setAttribute('cx', p2.x); knotB.setAttribute('cy', p2.y); knotB.setAttribute('r', 2.1);
    g.appendChild(knotB);

    const hit = document.createElementNS(NS,'path');
    hit.setAttribute('class','string-hit');
    hit.setAttribute('d', `M ${{p1.x}} ${{p1.y}} Q ${{mx}} ${{my}} ${{p2.x}} ${{p2.y}}`);
    g.appendChild(hit);

    svg.appendChild(g);

    const rec = {{a, b, g, shadow, path, twist, twistDark, knotA, knotB, hit, p1, p2, mx, my}};
    (nodeGroups[a] = nodeGroups[a]||[]).push(rec);
    (nodeGroups[b] = nodeGroups[b]||[]).push(rec);

    // el "encendido" y la etiqueta se dibujan en una capa aparte, siempre por encima
    // de todo (incluidas las fotos), sin mover nada del DOM original — así el
    // mouseleave nunca se pierde y no se acumulan cuerdas iluminadas.
    hit.addEventListener('mouseenter', ()=> showHighlight(p1,p2,mx,my,color,label));
    hit.addEventListener('mouseleave', hideHighlight);
  }});
}}
window.addEventListener('resize', draw);
draw();

const allNodeEls = Array.from(document.querySelectorAll('.node'));
const allStringGroups = Array.from(document.querySelectorAll('.string-group'));

// pasar el raton por una nota ilumina toda su red de conexiones (como conectar
// pistas en un corcho de investigacion): las cuerdas ajenas se atenuan.
allNodeEls.forEach(n=>{{
  const nid = n.dataset.id;
  n.addEventListener('mouseenter', ()=>{{
    const mine = nodeGroups[nid] || [];
    if(!mine.length) return;
    allStringGroups.forEach(g=> g.style.opacity = '0.12');
    allNodeEls.forEach(other=>{{ if(other!==n) other.classList.add('dimmed'); }});
    mine.forEach(rec=>{{
      rec.g.style.opacity = '1';
      const otherId = rec.a === nid ? rec.b : rec.a;
      const otherEl = nodeEls[otherId] || (nodeEls[otherId] = document.querySelector(`[data-id="${{otherId}}"]`));
      if(otherEl) otherEl.classList.remove('dimmed');
    }});
  }});
  n.addEventListener('mouseleave', ()=>{{
    allStringGroups.forEach(g=> g.style.opacity = '');
    allNodeEls.forEach(other=> other.classList.remove('dimmed'));
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

let dragRAF = null;
window.addEventListener('mousemove', e=>{{
  if(mode === 'node' && dragEl){{
    if(Math.abs(e.clientX-startX) > 5 || Math.abs(e.clientY-startY) > 5) moved = true;
    const b=board.getBoundingClientRect();
    dragEl.style.left = ((e.clientX-b.left)/zoom-offX)+'px';
    dragEl.style.top = ((e.clientY-b.top)/zoom-offY)+'px';
    if(dragRAF === null){{
      dragRAF = requestAnimationFrame(()=>{{
        updateEdgesFor(dragEl.dataset.id);
        dragRAF = null;
      }});
    }}
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
    frame.src = 'data:text/html;charset=utf-8,' + encodeURIComponent('<body style="font-family:sans-serif;padding:20px;color:#555">Todavía no hay nota para <b>'+label+'</b>.</body>');
  }}
  panel.classList.add('open');
  overlay.classList.add('open');
}}
function closeNote(){{
  panel.classList.remove('open');
  overlay.classList.remove('open');
}}
document.getElementById('note-close').addEventListener('click', closeNote);
overlay.addEventListener('click', closeNote);
</script>
</body>
</html>
'''

