from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Load the shared QQND transport before the monolithic game script.
needle = '<script>\n(() => {\n  \'use strict\';'
replacement = '<script src="./multiplayer-server.js?v=20260909-1"></script>\n<script>\n(() => {\n  \'use strict\';'
if needle not in s:
    raise SystemExit('main script marker missing')
s = s.replace(needle, replacement, 1)

# Multiplayer modal: shared rooms instead of manual SDP exchange.
modal = '''<div id="multiplayerModal" class="modal hidden">
  <section class="modal-card mp-server-card">
    <header class="modal-head"><div><div class="eyebrow">QQND CARD ROOM</div><h2>Multiplayer online</h2></div><button class="icon" data-action="mp-close">×</button></header>
    <p class="modal-copy">Pokoje działają przez wspólny serwer QQND. Nie trzeba już kopiować ofert WebRTC ani kodów SDP.</p>
    <label class="field"><span>Twój nick</span><input id="mpNick" maxlength="20" value="Gracz"></label>
    <div id="mpSetup" class="mp-grid">
      <section class="mp-box"><h3>Utwórz pokój</h3><label class="field"><span>Nazwa stołu</span><input id="mpRoomName" maxlength="40" value="Cribbage"></label><label class="field"><span>Widoczność</span><select id="mpVisibility"><option value="public">Publiczny</option><option value="private">Prywatny</option></select></label><div class="mp-actions"><button class="action primary" data-action="mp-create">Utwórz pokój</button></div><p id="mpHostStatus" class="mp-status"></p></section>
      <section class="mp-box"><h3>Dołącz</h3><label class="field"><span>Kod pokoju</span><input id="mpRoomInput" maxlength="16" placeholder="ABCD-EFGH"></label><div class="mp-actions"><button class="action primary" data-action="mp-join">Dołącz kodem</button><button class="action secondary" data-action="mp-refresh">Odśwież publiczne</button></div><p id="mpGuestStatus" class="mp-status"></p></section>
    </div>
    <section class="mp-box mp-public-box"><div class="mp-public-head"><h3>Publiczne stoły</h3><small>Cribbage · 2 graczy</small></div><div id="mpPublicRooms" class="mp-public-rooms"><span class="mp-empty">Kliknij „Odśwież publiczne”.</span></div></section>
    <section id="mpLobby" class="hidden">
      <div class="mp-room"><div><div class="eyebrow">POKÓJ</div><b id="mpRoomDisplay">—</b></div><button class="action secondary" data-action="mp-copy-room">Kopiuj kod</button></div>
      <div id="mpSeats"></div><p id="mpLobbyStatus" class="mp-status"></p>
      <div class="modal-actions"><button class="action secondary" data-action="mp-leave">Opuść pokój</button><button id="mpStart" class="action primary" data-action="mp-start" disabled>Rozpocznij grę</button></div>
    </section>
  </section>
</div>

<div id="newGameModal"'''
s, n = re.subn(r'<div id="multiplayerModal" class="modal hidden">.*?<div id="newGameModal"', modal, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('multiplayer modal replace failed')

# Persistent reconnect/presence status required by the runbook.
s = s.replace('<div id="toast" class="toast hidden"></div>', '<div id="toast" class="toast hidden"></div>\n<div id="networkPresenceOverlay" class="network-presence hidden" role="status" aria-live="assertive"><b id="networkPresenceTitle">Połączenie</b><span id="networkPresenceBody"></span></div>', 1)

# UI/card/summary overrides. All physical cards use the player card size.
css = r'''
    /* 2026-09-09 card consistency + QQND room UI */
    :root{--game-card-w:94px;--game-card-h:134px}
    .seat.bottom .card,.seat.bottom .card-back,.seat.top .card,.seat.top .card-back,
    .starter-wrap .card,.starter-wrap .card-back,.crib-wrap .card,.crib-wrap .card-back,
    .peg-cards .card,.peg-cards .card-back,#resultCards .card,#resultCards .card-back{width:var(--game-card-w)!important;height:var(--game-card-h)!important;border-radius:10px!important}
    .seat.top .card,.seat.top .card-back{margin-left:-58px}.seat.top .card:first-child,.seat.top .card-back:first-child{margin-left:0}
    .peg-cards .card,.peg-cards .card-back{margin-left:-30px}.peg-cards .card:first-child,.peg-cards .card-back:first-child{margin-left:0}
    .starter-wrap .card,.starter-wrap .card-back{margin:0}.crib-wrap .card-back{margin-left:-62px}.crib-wrap .card-back:first-child{margin-left:0}
    .seat.top .card .corner,.starter-wrap .card .corner,.peg-cards .card .corner,#resultCards .card .corner{top:8px;left:9px;font-size:21px}.seat.top .card .corner small,.starter-wrap .card .corner small,.peg-cards .card .corner small,#resultCards .card .corner small{font-size:19px}.seat.top .card .center-suit,.starter-wrap .card .center-suit,.peg-cards .card .center-suit,#resultCards .card .center-suit{font-size:48px}
    .card.illegal{opacity:.28!important;filter:none!important}.card.illegal:hover{filter:none!important}
    #resultModal #resultCards{margin-bottom:30px;min-height:150px!important}.result-grid{margin-bottom:8px}
    .mp-server-card{width:min(900px,100%)}.mp-public-box{margin-top:14px}.mp-public-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.mp-public-head h3{margin:0}.mp-public-head small{color:var(--muted);font-size:10px}.mp-public-rooms{display:grid;gap:8px;margin-top:10px;max-height:180px;overflow:auto}.mp-public-room{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;padding:10px 11px;border:1px solid var(--line);border-radius:11px;background:rgba(255,255,255,.025)}.mp-public-room b{display:block;font-size:12px}.mp-public-room small,.mp-empty{color:var(--muted);font-size:10px}.mp-public-room .action{min-height:34px;padding:6px 10px;font-size:10px}
    .network-presence{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:1350;width:min(520px,calc(100vw - 30px));padding:18px 20px;border:1px solid rgba(240,213,139,.5);border-radius:17px;background:rgba(8,16,12,.96);box-shadow:0 24px 70px rgba(0,0,0,.58);text-align:center;backdrop-filter:blur(10px)}.network-presence b{display:block;color:#f2d77f;font:900 20px/1.2 Georgia,serif}.network-presence span{display:block;margin-top:8px;color:#dbe5df;font-size:12px;line-height:1.5}.network-presence.good{border-color:rgba(105,214,150,.45)}.network-presence.good b{color:#9ee1b8}
    @media(max-width:760px){:root{--game-card-w:68px;--game-card-h:98px}.seat.top .card,.seat.top .card-back{margin-left:-43px}.peg-cards .card,.peg-cards .card-back{margin-left:-24px}.crib-wrap .card-back{margin-left:-46px}#resultModal #resultCards{min-height:112px!important;margin-bottom:24px}.seat.top .card .corner,.starter-wrap .card .corner,.peg-cards .card .corner,#resultCards .card .corner{font-size:16px}.seat.top .card .corner small,.starter-wrap .card .corner small,.peg-cards .card .corner small,#resultCards .card .corner small{font-size:14px}.seat.top .card .center-suit,.starter-wrap .card .center-suit,.peg-cards .card .center-suit,#resultCards .card .center-suit{font-size:34px}.mp-grid{grid-template-columns:1fr}}
'''
idx = s.find('</style>')
if idx < 0:
    raise SystemExit('style close missing')
s = s[:idx] + css + s[idx:]

# Replace WebRTC transport helpers with QQND room/session helpers.
transport = r'''  const mpEl=id=>document.getElementById(id);
  function mpStatus(id,msg,error=false){const n=mpEl(id);if(n){n.textContent=msg||'';n.classList.toggle('error',error)}}
  function normalizeNick(value){return String(value||'').normalize('NFKC').replace(/[\u200B-\u200D\u2060\uFEFF]/g,'').replace(/\s+/g,' ').trim()}
  function validateNick(value){const nickname=normalizeNick(value),len=Array.from(nickname).length;if(len<2||len>20)return{ok:false,message:prefs.language==='pl'?'Nick musi mieć od 2 do 20 znaków.':'Nickname must be 2–20 characters.'};if(/https?:|www\.|[<>@]/iu.test(nickname)||/[^\p{L}\p{N} _-]/u.test(nickname))return{ok:false,message:prefs.language==='pl'?'Nick zawiera niedozwolone znaki.':'Nickname contains unsupported characters.'};return{ok:true,nickname}}
  async function copyText(value){if(!value)return;try{await navigator.clipboard.writeText(value);mpStatus('mpLobbyStatus',prefs.language==='pl'?'Skopiowano.':'Copied.')}catch(_){mpStatus('mpLobbyStatus',prefs.language==='pl'?'Nie udało się skopiować automatycznie.':'Automatic copy failed.',true)}}
  function updateNetworkPill(connected=mp.connected){const pill=mpEl('networkPill');if(!pill)return;pill.classList.toggle('hidden',!mp.inGame);pill.classList.toggle('offline',!connected);mpEl('networkPillText').textContent=mp.room||'—'}
  let presenceTimer=0;
  function presenceOverlay(title,body,good=false,autoHide=0){const box=mpEl('networkPresenceOverlay');if(!box)return;clearTimeout(presenceTimer);mpEl('networkPresenceTitle').textContent=title;mpEl('networkPresenceBody').textContent=body;box.classList.remove('hidden');box.classList.toggle('good',good);if(autoHide)presenceTimer=setTimeout(()=>box.classList.add('hidden'),autoHide)}
  function hidePresenceOverlay(){clearTimeout(presenceTimer);mpEl('networkPresenceOverlay')?.classList.add('hidden')}
  function resetNetwork(clearGame=false){try{mp.client?.close()}catch(_){}Object.assign(mp,{role:null,room:'',roomData:null,client:null,connected:false,inGame:false,revision:0,lastSignature:'',names:['',''],viewerSeat:-1});updateNetworkPill(false);hidePresenceOverlay();if(clearGame&&state&&String(state.mode).startsWith('network')){state=null;render();$('#mainMenu').classList.remove('hidden')}}
  function renderPublicRooms(rooms){const root=mpEl('mpPublicRooms');if(!root)return;const available=(rooms||[]).filter(r=>r.game==='cribbage'&&r.status!=='finished');root.innerHTML=available.length?available.map(r=>`<div class="mp-public-room"><div><b>${escapeHtml(r.name||'Cribbage')}</b><small>${escapeHtml(r.id)} · ${r.players?.length||0}/2</small></div><button class="action secondary" data-action="mp-join-public" data-room="${escapeHtml(r.id)}" ${r.players?.length>=2?'disabled':''}>Dołącz</button></div>`).join(''):'<span class="mp-empty">Brak wolnych publicznych stołów.</span>'}
  function bindMpClient(client){
    client.addEventListener('connection',e=>{mp.connected=!!e.detail.connected;updateNetworkPill(mp.connected);if(!e.detail.connected&&mp.inGame)presenceOverlay('Utracono połączenie','Próbuję wznowić sesję i odzyskać ten sam seat…')});
    client.addEventListener('rooms',e=>renderPublicRooms(e.detail.rooms));
    client.addEventListener('room',e=>{const room=e.detail.room;mp.roomData=room;mp.room=room.id;mp.role=room.ownerSessionId===client.session?.id?'host':'guest';mp.names=(room.players||[]).map(p=>p.nickname);mp.connected=true;renderMpLobby();updateNetworkPill(true)});
    client.addEventListener('room-left',()=>{mp.room='';mp.roomData=null;mp.role=null;mp.inGame=false;mpEl('mpLobby')?.classList.add('hidden');mpEl('mpSetup')?.classList.remove('hidden');updateNetworkPill(false)});
    client.addEventListener('game-started',e=>{const msg=e.detail;mp.inGame=true;mp.viewerSeat=Number(msg.seat);mp.revision=Number(msg.revision)||0;mp.role=msg.hostSessionId===client.session?.id?'host':'guest';mp.roomData=msg.room||mp.roomData;mp.room=mp.roomData?.id||mp.room;mp.names=(mp.roomData?.players||[]).map(p=>p.nickname);closeAll();updateNetworkPill(true);if(mp.role==='host'){state=newState('network-host','medium',[mp.names[0]||'Host',mp.names[1]||'Gość'],121,Math.floor(Math.random()*2));dealHand();networkTick()}else{client.getState()}});
    client.addEventListener('game-action',e=>{if(mp.role==='host'&&mp.inGame){executeRemoteAction(e.detail.action,e.detail.payload||{});networkTick()}});
    client.addEventListener('game-state',e=>{const msg=e.detail;if(mp.role!=='guest'||!mp.inGame||msg.type!=='game.state'||!msg.state)return;mp.revision=Math.max(mp.revision,Number(msg.revision)||0);state=msg.state;closeAll();updateNetworkPill(true);render()});
    client.addEventListener('presence',e=>{const msg=e.detail;if(msg.type==='game.player.connection'){if(msg.connected){presenceOverlay('Gracz wrócił',`${msg.nickname||'Gracz'} odzyskał swój seat.`,true,1800)}else{const seconds=Math.max(0,Math.ceil(((msg.graceDeadline||Date.now())-Date.now())/1000));presenceOverlay(`Utracono połączenie z graczem ${msg.nickname||''}`.trim(),`Serwer czeka na wznowienie sesji. Grace period: ${seconds} s.`)}}else if(msg.type==='game.player.bot_takeover'){presenceOverlay(`Bot przejął miejsce gracza ${msg.nickname||''}`.trim(),'To jest przejściowy tryb B1: stan pozostaje host-authoritative. Pełne bezpieczne przejęcie rozdania zostanie zapewnione w B2.')}else if(msg.type==='game.host.changed'){presenceOverlay('Zmienił się host stołu','Faza B1 nie rekonstruuje prywatnego pełnego stanu po utracie hosta. Poczekaj na jego reconnect; nie cofamy rozgrywki.')}else if(msg.type==='game.presence'){const down=(msg.presence||[]).find(p=>!p.connected||p.botActive);if(!down&&mp.inGame)hidePresenceOverlay()}})
  }
  async function ensureMpClient(){const checked=validateNick(mpEl('mpNick')?.value||'Gracz');if(!checked.ok){mpStatus('mpHostStatus',checked.message,true);mpStatus('mpGuestStatus',checked.message,true);throw new Error('bad_nick')}if(!mp.client){mp.client=new window.QQNDMultiplayerClient({game:'cribbage'});bindMpClient(mp.client)}await mp.client.connect(checked.nickname);return mp.client}
  async function openMultiplayer(){mpStatus('mpHostStatus','');mpStatus('mpGuestStatus','');mpStatus('mpLobbyStatus','');mpEl('mpSetup').classList.remove('hidden');mpEl('mpLobby').classList.add('hidden');mpEl('multiplayerModal').classList.remove('hidden');try{const client=await ensureMpClient();client.listRooms()}catch(_){}}
  function renderMpLobby(){if(!mp.roomData)return;mpEl('mpSetup').classList.add('hidden');mpEl('mpLobby').classList.remove('hidden');mpEl('mpRoomDisplay').textContent=mp.room||'—';const players=mp.roomData.players||[];mpEl('mpSeats').innerHTML=[0,1].map(p=>`<div class="mp-lobby-seat"><b>${escapeHtml(players[p]?.nickname||(prefs.language==='pl'?'Wolne miejsce':'Open seat'))}</b><small>${players[p]?.connected===false?(prefs.language==='pl'?'Rozłączony':'Disconnected'):(players[p]?(prefs.language==='pl'?'Połączono':'Connected'):(prefs.language==='pl'?'Oczekiwanie':'Waiting'))}</small></div>`).join('');mpEl('mpStart').disabled=!(mp.role==='host'&&players.length===2&&players.every(p=>p.connected!==false))}
  async function createRoom(){try{const client=await ensureMpClient();client.createRoom((mpEl('mpRoomName')?.value||'Cribbage').trim()||'Cribbage',mpEl('mpVisibility')?.value||'public');mpStatus('mpHostStatus',prefs.language==='pl'?'Tworzenie pokoju…':'Creating room…')}catch(_){}}
  async function joinRoom(roomId){try{const client=await ensureMpClient();const id=String(roomId||mpEl('mpRoomInput')?.value||'').trim().toUpperCase();if(!id){mpStatus('mpGuestStatus','Wpisz kod pokoju.',true);return}client.joinRoom(id);mpStatus('mpGuestStatus',prefs.language==='pl'?'Dołączanie…':'Joining…')}catch(_){}}
  async function refreshRooms(){try{const client=await ensureMpClient();client.listRooms()}catch(_){}}
  function hiddenCards'''
s, n = re.subn(r'  const mpEl=id=>document\.getElementById\(id\);.*?  function hiddenCards', transport, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('transport block replace failed')

# Animation: hide the destination card until the flying card arrives.
old_anim = re.search(r'  function animatePlay\(p,c\)\{.*?\}\n  function playCard', s, flags=re.S)
if not old_anim:
    raise SystemExit('animatePlay block missing')
new_anim = r'''  const flyingCards=new Set();
  function animatePlay(p,c){if(prefs.animations==='off'||matchMedia('(prefers-reduced-motion:reduce)').matches)return false;const hand=$(`.hand[data-player="${p}"]`),source=hand?.querySelector(`[data-card="${c.id}"]`)||hand?.querySelector('.card-back:last-child, .card:last-child'),target=$('#pegCards');if(!source||!target)return false;const from=source.getBoundingClientRect(),to=target.getBoundingClientRect(),wrap=document.createElement('div');wrap.innerHTML=cardHTML(c);const ghost=wrap.firstElementChild;ghost.disabled=true;ghost.classList.add('flight-card');flyingCards.add(c.id);Object.assign(ghost.style,{left:`${from.left}px`,top:`${from.top}px`,width:`${from.width}px`,height:`${from.height}px`});document.body.appendChild(ghost);const dx=to.left+to.width/2-from.left-from.width/2,dy=to.top+to.height/2-from.top-from.height/2;const done=()=>{ghost.remove();flyingCards.delete(c.id);render()};const animation=ghost.animate([{transform:'translate3d(0,0,0) scale(1)',opacity:.82},{offset:.62,transform:`translate3d(${dx*.72}px,${dy*.72-26}px,0) scale(1.04)`,opacity:1},{transform:`translate3d(${dx}px,${dy}px,0) scale(1)`,opacity:1}],{duration:hand?.id==='bottomHand'?460:400,easing:'cubic-bezier(.18,.78,.22,1)',fill:'forwards'});animation.onfinish=done;animation.oncancel=done;return true}
  function playCard'''
s = s[:old_anim.start()] + new_anim + s[old_anim.end():]

old_tick = r"  function networkTick(){if(mp.role!=='host'||!mp.connected||!mp.inGame||mp.channel?.readyState!=='open'||!state)return;const view=guestView(),signature=JSON.stringify(view);if(signature===mp.lastSignature)return;mp.lastSignature=signature;mp.seq++;mpSend({v:1,type:'state',seq:mp.seq,view})}\n  function sendGuestAction(action,payload={}){if(mp.role!=='guest'||!mp.connected)return;mp.clientSeq++;mpSend({v:1,type:'action',clientSeq:mp.clientSeq,action,payload})}"
new_tick = r"  function networkTick(){if(mp.role!=='host'||!mp.connected||!mp.inGame||!mp.client||!state)return;const view=guestView(),signature=JSON.stringify(view);if(signature===mp.lastSignature)return;mp.lastSignature=signature;mp.revision=(mp.revision||0)+1;mp.client.commit(mp.revision,state);const guest=mp.roomData?.players?.find(p=>p.id!==mp.client.session?.id);if(guest)mp.client.publish(mp.revision,guest.id,view)}\n  function sendGuestAction(action,payload={}){if(mp.role!=='guest'||!mp.connected||!mp.client)return;mp.client.action(action,payload)}"
if old_tick not in s:
    raise SystemExit('network tick marker missing')
s = s.replace(old_tick, new_tick, 1)

s, n = re.subn(r"  function startNetworkGame\(\)\{.*?\}\n  function networkClickInterceptor", "  function startNetworkGame(){if(mp.role!=='host'||!mp.connected||!mp.client||mp.roomData?.players?.length!==2)return;mp.client.startGame({target:121})}\n  function networkClickInterceptor", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('startNetworkGame replace failed')

s, n = re.subn(r"  function multiplayerUiClick\(e\)\{.*?\}\n  setInterval\(networkTick,180\);", r'''  function multiplayerUiClick(e){const button=e.target.closest('[data-action]');if(!button)return;const action=button.dataset.action;if(!action.startsWith('mp-')&&action!=='multiplayer-p2p')return;e.preventDefault();e.stopImmediatePropagation();if(action==='multiplayer-p2p')openMultiplayer();else if(action==='mp-close')mpEl('multiplayerModal').classList.add('hidden');else if(action==='mp-create')createRoom();else if(action==='mp-join')joinRoom();else if(action==='mp-join-public')joinRoom(button.dataset.room);else if(action==='mp-refresh')refreshRooms();else if(action==='mp-copy-room')copyText(mp.room);else if(action==='mp-leave'){mp.client?.leaveRoom(mp.room);resetNetwork(true);mpEl('multiplayerModal').classList.add('hidden')}else if(action==='mp-start')startNetworkGame()}
  setInterval(networkTick,180);''', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('multiplayer click replace failed')

# Do not render the final pegging card underneath its flight ghost.
old_peg = "$('#pegCards').innerHTML=state.pegHistory.map((c,i)=>cardHTML(c,`played p${i%2}`)).join('');"
new_peg = "$('#pegCards').innerHTML=state.pegHistory.map((c,i)=>flyingCards.has(c.id)?'':cardHTML(c,`played p${i%2}`)).join('');"
if old_peg not in s:
    raise SystemExit('peg render marker missing')
s = s.replace(old_peg, new_peg, 1)

# Product copy no longer calls the feature P2P.
s = s.replace('Multiplayer P2P', 'Multiplayer online')
s = s.replace('opcjonalny multiplayer P2P', 'multiplayer przez QQND Card Room')
s = s.replace('PRYWATNY STÓŁ P2P', 'QQND CARD ROOM')

p.write_text(s, encoding='utf-8')
print('Applied QQND B1 multiplayer and card/animation fixes.')
