from pathlib import Path
import re

INDEX = Path('index.html')
html = INDEX.read_text(encoding='utf-8')

if '<!-- cribbage-ui-v2 -->' in html:
    print('Cribbage UI v2 already applied; nothing to do.')
    raise SystemExit(0)

board_functions = r'''  function boardProgress(index){index=Math.max(0,Math.min(120,index));const groupGap=.55;return(index+Math.floor(index/5)*groupGap)/(120+24*groupGap)}
  function boardPointV2(t,lane){
    t=Math.max(0,Math.min(1,t));
    const cx=143,turnY=94,bottom=496,baseRadius=66,offset=lane===0?-12:12,radius=baseRadius-offset,left=cx-radius,right=cx+radius;
    const straight=bottom-turnY,curve=Math.PI*radius,total=straight*2+curve,d=t*total;
    if(d<=straight)return{x:left,y:bottom-d};
    if(d<straight+curve){const angle=Math.PI-(d-straight)/radius;return{x:cx+radius*Math.cos(angle),y:turnY-radius*Math.sin(angle)}}
    return{x:right,y:turnY+d-straight-curve}
  }
  function boardTrackPathV2(lane){const cx=143,turnY=94,bottom=496,baseRadius=66,offset=lane===0?-12:12,radius=baseRadius-offset,left=cx-radius,right=cx+radius;return`M ${left} ${bottom} L ${left} ${turnY} A ${radius} ${radius} 0 0 1 ${right} ${turnY} L ${right} ${bottom}`}
  function renderCribBoard(){
    const root=$('#cribbageBoard');if(!root)return;const target=state?.target||121,boardKey=`${target}-two-lane-reference-v2`;
    if(root.dataset.target!==boardKey){
      let holes='';
      for(let lane=0;lane<2;lane++){
        const start=boardPointV2(0,lane);
        holes+=`<i class="board-hole start" data-lane="${lane}" data-start="1" style="left:${start.x}px;top:${start.y+18}px"></i><i class="board-hole start" data-lane="${lane}" data-start="2" style="left:${start.x}px;top:${start.y+34}px"></i>`;
        for(let i=1;i<=120;i++){const pt=boardPointV2(boardProgress(i),lane);holes+=`<i class="board-hole ${i%5===0?'fifth':''}" data-lane="${lane}" data-hole="${i}" style="left:${pt.x}px;top:${pt.y}px"></i>`}
      }
      const tracks=`<svg class="board-track-svg" viewBox="0 0 286 560" aria-hidden="true"><path class="board-track-border" d="${boardTrackPathV2(0)}"></path><path class="board-track-border" d="${boardTrackPathV2(1)}"></path><path class="board-track p0" d="${boardTrackPathV2(0)}"></path><path class="board-track p1" d="${boardTrackPathV2(1)}"></path></svg>`;
      root.innerHTML=`<div class="board-wood"></div>${tracks}${holes}<span class="board-number n120">120</span><span class="board-number n90">90</span><span class="board-number n60">60</span><span class="board-number n30">30</span><span class="board-start">START</span><span class="board-title">121</span><span class="board-finish">FINISH</span><div class="board-label">CRIBBAGE BOARD</div>`;
      root.dataset.target=boardKey
    }
    root.querySelectorAll('.board-peg').forEach(n=>n.remove());if(!state)return;
    const positions=state.pegPositions||state.scores.map(s=>[Math.max(0,s-1),s]);
    positions.forEach((pair,p)=>pair.forEach((score,index)=>{let pt;if(score<=0){const start=boardPointV2(0,p);pt={x:start.x,y:start.y+(index===0?34:18)}}else{const holeIndex=Math.min(score,target)/target*120;pt=boardPointV2(boardProgress(holeIndex),p)}const peg=document.createElement('i');peg.className=`board-peg p${p} ${index===0?'back':''}`;peg.style.left=`${pt.x}px`;peg.style.top=`${pt.y}px`;peg.title=`${state.names[p]}: ${score}`;root.appendChild(peg)}))
  }'''

pattern = re.compile(r"  function boardProgress\(index\)\{.*?\n  function renderScores\(\)\{", re.S)
html, count = pattern.subn(board_functions + "\n  function renderScores(){", html, count=1)
if count != 1:
    raise RuntimeError(f'Expected to replace one cribbage board function block, replaced {count}.')

style_block = r'''
  <style id="cribbageUiV2Styles">
    /* two-lane-reference-v2 */
    :root{
      --dev-ui-scale:1;
      --dev-board-x:0px;--dev-board-y:0px;--dev-board-scale:1;
      --dev-player-x:0px;--dev-player-y:0px;--dev-player-scale:1;
      --dev-opponent-x:0px;--dev-opponent-y:0px;--dev-opponent-scale:1;
      --dev-starter-x:0px;--dev-starter-y:0px;
      --dev-crib-x:0px;--dev-crib-y:0px;
      --dev-pegging-x:0px;--dev-pegging-y:0px;--dev-pegging-scale:1;
      --dev-prompt-y:0px;--dev-controls-y:0px;
    }
    #app{zoom:var(--dev-ui-scale)}

    /* Keep the hand stable: selection is expressed with light and outline, not vertical movement. */
    .card.selected{transform:none;z-index:3;filter:brightness(1.025);box-shadow:0 10px 20px rgba(0,0,0,.34),0 0 0 3px var(--gold),0 0 24px rgba(215,180,94,.24)}
    .seat.bottom .card:hover:not(:disabled),.seat.bottom .card.selected,.seat.bottom .card.selected:hover:not(:disabled){transform:none}

    /* Card backs share the cleaner navy diagonal language used by SKAT. */
    .card-back{position:relative;overflow:hidden;border:2px solid #efe6d0;background:repeating-linear-gradient(45deg,#19375d 0 6px,#244d80 6px 12px);box-shadow:0 8px 16px rgba(0,0,0,.32),inset 0 0 0 1px rgba(8,23,42,.46)}
    .card-back::before{content:"";position:absolute;inset:4px;border:1px solid rgba(255,255,255,.72);border-radius:5px;box-shadow:inset 0 0 0 1px rgba(8,27,49,.32)}
    .card-back::after{content:"";position:absolute;inset:9px;border:1px solid rgba(235,207,137,.38);border-radius:3px;background:repeating-linear-gradient(-45deg,rgba(255,255,255,.045) 0 2px,transparent 2px 6px)}

    /* Reference-inspired rectangular two-player board. The U tracks are SVG-backed so the geometry stays locked. */
    .crib-board{width:286px;height:560px;left:38px;top:72px;isolation:isolate;filter:drop-shadow(0 22px 30px rgba(0,0,0,.48)) drop-shadow(0 2px 2px rgba(0,0,0,.4));translate:var(--dev-board-x) var(--dev-board-y);scale:var(--dev-board-scale);transform-origin:top left}
    .crib-board .board-wood{z-index:0;inset:0;clip-path:none;border-radius:14px;background:radial-gradient(ellipse at 48% 7%,rgba(255,226,172,.22),transparent 24%),repeating-linear-gradient(7deg,rgba(45,21,8,.12) 0 1px,transparent 1px 9px),linear-gradient(90deg,#3d2112 0%,#81502a 13%,#b67c43 31%,#87532b 51%,#bd8248 70%,#7b4725 87%,#3a2012 100%);box-shadow:inset 0 0 0 2px rgba(255,230,177,.3),inset 0 0 0 5px rgba(57,28,13,.26),inset 14px 0 32px rgba(0,0,0,.22),inset -12px 0 28px rgba(0,0,0,.18),inset 0 -22px 36px rgba(31,14,7,.25)}
    .crib-board .board-wood::before{content:"";position:absolute;inset:7px;clip-path:none;border-radius:9px;background:linear-gradient(90deg,rgba(246,210,145,.18),rgba(103,61,29,.04) 24%,rgba(255,232,181,.14) 50%,rgba(79,43,20,.04) 76%,rgba(243,204,137,.16));box-shadow:inset 0 0 0 1px rgba(255,232,186,.13),inset 0 0 28px rgba(0,0,0,.12);pointer-events:none}
    .crib-board .board-wood::after{content:"";position:absolute;inset:11px;clip-path:none;border-radius:7px;background:repeating-linear-gradient(5deg,rgba(32,14,6,.13) 0 1px,transparent 1px 8px),repeating-linear-gradient(96deg,rgba(255,224,175,.035) 0 1px,transparent 1px 13px);opacity:.88;pointer-events:none}
    .board-track-svg{position:absolute;inset:0;width:100%;height:100%;z-index:1;overflow:visible;pointer-events:none}
    .board-track-border,.board-track{fill:none;stroke-linecap:round;stroke-linejoin:round}
    .board-track-border{stroke:#241208;stroke-width:29;opacity:.9}
    .board-track{stroke-width:20;filter:drop-shadow(0 1px 0 rgba(255,255,255,.14));opacity:.94}
    .board-track.p0{stroke:#4d8ed7}.board-track.p1{stroke:#c84d5a}
    .board-hole{z-index:3;width:6px;height:6px;background:radial-gradient(circle at 34% 30%,#4c2b18 0 10%,#211108 32%,#0b0503 72%,#020101 100%);box-shadow:0 0 0 1px rgba(255,235,198,.2),inset 0 1px 2px rgba(255,255,255,.06),inset 0 -2px 3px #000}
    .board-hole.fifth{width:7px;height:7px;background:radial-gradient(circle at 34% 30%,#3a2113 0 12%,#160a05 42%,#040201 100%);box-shadow:0 0 0 1px rgba(247,211,130,.58),0 0 0 3px rgba(60,31,13,.14),inset 0 1px 2px rgba(255,255,255,.05),inset 0 -2px 3px #000}
    .board-hole.start{width:8px;height:8px;box-shadow:0 0 0 1px rgba(247,211,130,.52),0 0 0 3px rgba(61,33,15,.18),inset 0 1px 2px rgba(255,255,255,.05),inset 0 -2px 3px #000}
    .board-peg{z-index:6}
    .board-lap{display:none}
    .board-number,.board-start,.board-finish,.board-title{position:absolute;z-index:2;font-family:Georgia,serif;font-weight:900;color:rgba(45,22,11,.76);text-shadow:0 1px rgba(255,235,194,.22);pointer-events:none;user-select:none}
    .board-number{left:143px;transform:translate(-50%,-50%);font-size:11px;letter-spacing:.04em;padding:1px 5px;border-radius:999px;background:rgba(231,194,128,.22)}
    .board-number.n120{top:63px}.board-number.n90{top:170px}.board-number.n60{top:285px}.board-number.n30{top:400px}
    .board-start,.board-finish{top:535px;transform:translateX(-50%);font-size:9px;letter-spacing:.08em}.board-start{left:77px}.board-finish{left:209px}.board-title{left:143px;top:526px;transform:translateX(-50%);font-size:10px;color:rgba(244,219,164,.72);background:rgba(56,28,13,.58);padding:3px 7px;border-radius:999px}

    /* Dev UI tuning offsets compose with the existing responsive transforms. */
    .seat.bottom{translate:var(--dev-player-x) var(--dev-player-y);scale:var(--dev-player-scale)}
    .seat.top{translate:var(--dev-opponent-x) var(--dev-opponent-y);scale:var(--dev-opponent-scale)}
    .starter-wrap{translate:var(--dev-starter-x) var(--dev-starter-y)}
    .crib-wrap{translate:var(--dev-crib-x) var(--dev-crib-y)}
    .peg-zone{translate:var(--dev-pegging-x) var(--dev-pegging-y);scale:var(--dev-pegging-scale)}
    .prompt{translate:0 var(--dev-prompt-y)}
    .controlbar{translate:0 var(--dev-controls-y)}

    .dev-ui-toggle{position:fixed;right:14px;bottom:14px;z-index:1200;border:1px solid rgba(240,213,139,.5);border-radius:999px;background:rgba(8,16,12,.9);color:#f0d58b;padding:8px 11px;font:900 10px/1 Inter,system-ui,sans-serif;letter-spacing:.1em;cursor:pointer;box-shadow:0 8px 22px rgba(0,0,0,.34);backdrop-filter:blur(8px)}
    .dev-ui-toggle:hover{background:#15241c}
    .dev-ui-panel{position:fixed;right:14px;top:14px;z-index:1199;width:min(340px,calc(100vw - 28px));max-height:calc(100vh - 76px);overflow:auto;padding:14px;border:1px solid rgba(240,213,139,.32);border-radius:16px;background:linear-gradient(180deg,rgba(16,25,20,.97),rgba(7,13,10,.97));color:#edf5ef;box-shadow:0 24px 60px rgba(0,0,0,.5);backdrop-filter:blur(12px)}
    .dev-ui-panel.hidden{display:none!important}.dev-ui-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:10px}.dev-ui-head strong{display:block;font:900 17px/1.1 Georgia,serif;color:#f3dfaa}.dev-ui-head small{display:block;margin-top:4px;color:#96aa9f;font-size:9px;line-height:1.35}.dev-ui-close{border:0;background:transparent;color:#aebdb5;font-size:19px;line-height:1;cursor:pointer}
    .dev-ui-group{margin:13px 0 6px;padding-top:10px;border-top:1px solid rgba(255,255,255,.08);color:#d8ba70;font-size:9px;font-weight:900;letter-spacing:.12em;text-transform:uppercase}.dev-ui-group:first-child{margin-top:4px;border-top:0;padding-top:0}
    .dev-ui-row{display:grid;grid-template-columns:88px minmax(0,1fr) 62px;gap:8px;align-items:center;margin:7px 0}.dev-ui-row label{color:#c6d2cb;font-size:10px}.dev-ui-row input[type="range"]{width:100%;accent-color:#d7b45e}.dev-ui-row input[type="number"]{width:62px;border:1px solid rgba(255,255,255,.13);border-radius:8px;background:#101a15;color:#eaf2ed;padding:5px 6px;font:800 10px/1 ui-monospace,SFMono-Regular,Consolas,monospace;text-align:right}
    .dev-ui-actions{display:flex;gap:8px;margin-top:13px;padding-top:11px;border-top:1px solid rgba(255,255,255,.08)}.dev-ui-actions button{flex:1;border:1px solid rgba(255,255,255,.12);border-radius:9px;background:rgba(255,255,255,.045);color:#e8efeb;padding:8px;font-size:10px;font-weight:900;cursor:pointer}.dev-ui-actions button.primary{border-color:#9c7b31;background:linear-gradient(180deg,#efd37c,#c39a42);color:#211b0d}.dev-ui-actions button:hover{filter:brightness(1.08)}
    @media(max-width:1180px){.crib-board{top:122px;left:18px}}
  </style>
'''

panel_block = r'''
<!-- cribbage-ui-v2 -->
<button id="devUiToggle" class="dev-ui-toggle" type="button" title="UI tuning · F2">DEV</button>
<aside id="devUiPanel" class="dev-ui-panel hidden" aria-label="Developer UI tuning">
  <div class="dev-ui-head"><div><strong>UI tuning</strong><small>F2 otwiera panel. Wartości zapisują się lokalnie; „Kopiuj wartości” daje JSON do późniejszego dostrojenia.</small></div><button id="devUiClose" class="dev-ui-close" type="button" aria-label="Zamknij">×</button></div>
  <div id="devUiControls"></div>
  <div class="dev-ui-actions"><button id="devUiReset" type="button">Reset</button><button id="devUiCopy" class="primary" type="button">Kopiuj wartości</button></div>
</aside>
<script id="cribbageUiV2DevScript">
(()=>{
  const KEY='cribbage.devUI.v1';
  const defaults={uiScale:1,boardX:0,boardY:0,boardScale:1,playerX:0,playerY:0,playerScale:1,opponentX:0,opponentY:0,opponentScale:1,starterX:0,starterY:0,cribX:0,cribY:0,peggingX:0,peggingY:0,peggingScale:1,promptY:0,controlsY:0};
  const specs=[
    {group:'Globalnie'},{key:'uiScale',label:'UI scale',min:.75,max:1.35,step:.01},
    {group:'Plansza'},{key:'boardX',label:'Board X',min:-320,max:520,step:1},{key:'boardY',label:'Board Y',min:-320,max:320,step:1},{key:'boardScale',label:'Board scale',min:.5,max:1.6,step:.01},
    {group:'Ręka gracza'},{key:'playerX',label:'Player X',min:-420,max:420,step:1},{key:'playerY',label:'Player Y',min:-320,max:320,step:1},{key:'playerScale',label:'Player scale',min:.6,max:1.5,step:.01},
    {group:'Przeciwnik'},{key:'opponentX',label:'Opponent X',min:-420,max:420,step:1},{key:'opponentY',label:'Opponent Y',min:-320,max:320,step:1},{key:'opponentScale',label:'Opponent scale',min:.6,max:1.5,step:.01},
    {group:'Karty środka'},{key:'starterX',label:'Starter X',min:-420,max:420,step:1},{key:'starterY',label:'Starter Y',min:-320,max:320,step:1},{key:'cribX',label:'Crib X',min:-420,max:420,step:1},{key:'cribY',label:'Crib Y',min:-320,max:320,step:1},
    {group:'Pegging'},{key:'peggingX',label:'Pegging X',min:-420,max:420,step:1},{key:'peggingY',label:'Pegging Y',min:-320,max:320,step:1},{key:'peggingScale',label:'Pegging scale',min:.6,max:1.5,step:.01},
    {group:'Komunikaty'},{key:'promptY',label:'Prompt Y',min:-320,max:320,step:1},{key:'controlsY',label:'Controls Y',min:-320,max:320,step:1}
  ];
  let values={...defaults};
  try{const saved=JSON.parse(localStorage.getItem(KEY)||'{}');for(const key of Object.keys(defaults))if(Number.isFinite(Number(saved[key])))values[key]=Number(saved[key])}catch(_){ }
  const css=document.documentElement.style;
  const px=v=>`${Number(v)||0}px`;
  function apply(){
    css.setProperty('--dev-ui-scale',String(values.uiScale));
    css.setProperty('--dev-board-x',px(values.boardX));css.setProperty('--dev-board-y',px(values.boardY));css.setProperty('--dev-board-scale',String(values.boardScale));
    css.setProperty('--dev-player-x',px(values.playerX));css.setProperty('--dev-player-y',px(values.playerY));css.setProperty('--dev-player-scale',String(values.playerScale));
    css.setProperty('--dev-opponent-x',px(values.opponentX));css.setProperty('--dev-opponent-y',px(values.opponentY));css.setProperty('--dev-opponent-scale',String(values.opponentScale));
    css.setProperty('--dev-starter-x',px(values.starterX));css.setProperty('--dev-starter-y',px(values.starterY));css.setProperty('--dev-crib-x',px(values.cribX));css.setProperty('--dev-crib-y',px(values.cribY));
    css.setProperty('--dev-pegging-x',px(values.peggingX));css.setProperty('--dev-pegging-y',px(values.peggingY));css.setProperty('--dev-pegging-scale',String(values.peggingScale));
    css.setProperty('--dev-prompt-y',px(values.promptY));css.setProperty('--dev-controls-y',px(values.controlsY));
    try{localStorage.setItem(KEY,JSON.stringify(values))}catch(_){ }
  }
  const controls=document.getElementById('devUiControls'),panel=document.getElementById('devUiPanel'),toggle=document.getElementById('devUiToggle');
  const inputPairs=new Map();
  for(const spec of specs){
    if(spec.group){const h=document.createElement('div');h.className='dev-ui-group';h.textContent=spec.group;controls.appendChild(h);continue}
    const row=document.createElement('div');row.className='dev-ui-row';const label=document.createElement('label');label.textContent=spec.label;const range=document.createElement('input');range.type='range';range.min=spec.min;range.max=spec.max;range.step=spec.step;range.value=values[spec.key];const number=document.createElement('input');number.type='number';number.min=spec.min;number.max=spec.max;number.step=spec.step;number.value=values[spec.key];
    const update=raw=>{let v=Number(raw);if(!Number.isFinite(v))v=defaults[spec.key];v=Math.max(spec.min,Math.min(spec.max,v));values[spec.key]=v;range.value=String(v);number.value=String(v);apply()};range.addEventListener('input',()=>update(range.value));number.addEventListener('input',()=>update(number.value));row.append(label,range,number);controls.appendChild(row);inputPairs.set(spec.key,{range,number})
  }
  function setOpen(open){panel.classList.toggle('hidden',!open);toggle.textContent=open?'DEV ×':'DEV'}
  toggle.addEventListener('click',()=>setOpen(panel.classList.contains('hidden')));document.getElementById('devUiClose').addEventListener('click',()=>setOpen(false));
  addEventListener('keydown',e=>{if(e.key==='F2'||(e.ctrlKey&&e.shiftKey&&e.key.toLowerCase()==='d')){e.preventDefault();setOpen(panel.classList.contains('hidden'))}});
  document.getElementById('devUiReset').addEventListener('click',()=>{values={...defaults};for(const [key,pair] of inputPairs){pair.range.value=String(values[key]);pair.number.value=String(values[key])}apply()});
  document.getElementById('devUiCopy').addEventListener('click',async e=>{const text=JSON.stringify(values,null,2);try{await navigator.clipboard.writeText(text);e.currentTarget.textContent='Skopiowano';setTimeout(()=>e.currentTarget.textContent='Kopiuj wartości',1200)}catch(_){const area=document.createElement('textarea');area.value=text;document.body.appendChild(area);area.select();document.execCommand('copy');area.remove();e.currentTarget.textContent='Skopiowano';setTimeout(()=>e.currentTarget.textContent='Kopiuj wartości',1200)}});
  window.cribbageDevUI={get:()=>({...values}),set:patch=>{for(const key of Object.keys(defaults))if(Object.hasOwn(patch,key)&&Number.isFinite(Number(patch[key])))values[key]=Number(patch[key]);for(const [key,pair] of inputPairs){pair.range.value=String(values[key]);pair.number.value=String(values[key])}apply();return{...values}},reset:()=>{document.getElementById('devUiReset').click();return{...values}}};
  apply();
})();
</script>
'''

if '</head>' not in html or '</body>' not in html:
    raise RuntimeError('index.html is missing expected closing tags.')

html = html.replace('</head>', style_block + '\n</head>', 1)
html = html.replace('</body>', panel_block + '\n</body>', 1)
INDEX.write_text(html, encoding='utf-8')
print('Applied Cribbage UI v2 redesign.')
