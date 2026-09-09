from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Quick Play is safe now that Cribbage is server-authoritative and exactly 2-player.
s = s.replace(
    '<button class="action primary" data-action="mp-join">Dołącz kodem</button><button class="action secondary" data-action="mp-refresh">Odśwież publiczne</button>',
    '<button class="action primary" data-action="mp-join">Dołącz kodem</button><button class="action secondary" data-action="mp-refresh">Odśwież publiczne</button><button class="action secondary" data-action="mp-quick">Szybka gra</button>',
    1,
)

# All network seats render opponent cards as backs; the server already sends hidden placeholders.
s = s.replace(
    "const isRemote=(state.mode==='network-host'||state.mode==='network-guest')&&p===1;",
    "const isRemote=(state.mode==='network-host'||state.mode==='network-guest'||state.mode==='network-server')&&p===1;",
    1,
)

# In authoritative online discard both players may choose their two cards independently.
s = s.replace(
    "const box=$('#controls'),isDiscard=!!state&&state.phase==='discard'&&(state.mode==='local'||state.active===0);",
    "const box=$('#controls'),isDiscard=!!state&&state.phase==='discard'&&(state.mode==='local'||state.mode==='network-server'||state.active===0);",
    1,
)

# Better prompt when the server says it is the remote seat's pegging turn.
s = s.replace(
    "body=state.mode==='bot'&&state.active===1?t('prompt.botTurn'):state.mode==='local'?t('prompt.localTurn',{name:state.names[state.active]}):t('prompt.yourTurn')",
    "body=state.mode==='network-server'&&state.active===1?(prefs.language==='pl'?'Kolej rywala.':'Opponent’s turn.'):state.mode==='bot'&&state.active===1?t('prompt.botTurn'):state.mode==='local'?t('prompt.localTurn',{name:state.names[state.active]}):t('prompt.yourTurn')",
    1,
)

bind = r'''  function bindMpClient(client){
    client.addEventListener('connection',e=>{mp.connected=!!e.detail.connected;updateNetworkPill(mp.connected);if(!e.detail.connected&&mp.inGame)presenceOverlay('Utracono połączenie','Próbuję wznowić sesję i odzyskać ten sam seat…')});
    client.addEventListener('rooms',e=>renderPublicRooms(e.detail.rooms));
    client.addEventListener('room',e=>{const room=e.detail.room;mp.roomData=room;mp.room=room.id;mp.role=room.ownerSessionId===client.session?.id?'host':'guest';mp.names=(room.players||[]).map(p=>p.nickname);mp.connected=true;renderMpLobby();updateNetworkPill(true);if(e.detail.resumed&&room.status==='playing'){mp.inGame=true;client.getState()}});
    client.addEventListener('room-left',()=>{mp.room='';mp.roomData=null;mp.role=null;mp.inGame=false;mpEl('mpLobby')?.classList.add('hidden');mpEl('mpSetup')?.classList.remove('hidden');updateNetworkPill(false)});
    client.addEventListener('match-found',e=>{const room=e.detail.room;mp.roomData=room;mp.room=room.id;mp.role=room.ownerSessionId===client.session?.id?'host':'guest';mp.names=(room.players||[]).map(p=>p.nickname);renderMpLobby();mpStatus('mpLobbyStatus',prefs.language==='pl'?'Znaleziono przeciwnika. Start gry…':'Opponent found. Starting…');if(mp.role==='host')setTimeout(()=>client.startGame({target:121}),80)});
    client.addEventListener('queue',e=>{const msg=e.detail;if(msg.type==='queue.joined')mpStatus('mpGuestStatus',prefs.language==='pl'?`Szukam przeciwnika · pozycja ${msg.position}`:`Searching · position ${msg.position}`);else mpStatus('mpGuestStatus','')});
    client.addEventListener('server-error',e=>{const code=e.detail?.code||'server_error';mpStatus('mpLobbyStatus',code,true);if(mp.inGame)toast(code)});
    client.addEventListener('game-started',e=>{const msg=e.detail;mp.inGame=true;mp.viewerSeat=Number(msg.seat);mp.revision=Number(msg.revision)||0;mp.role=msg.hostSessionId===client.session?.id?'host':'guest';mp.roomData=msg.room||mp.roomData;mp.room=mp.roomData?.id||mp.room;mp.names=(mp.roomData?.players||[]).map(p=>p.nickname);closeAll();updateNetworkPill(true);client.getState()});
    client.addEventListener('game-state',e=>{const msg=e.detail;if(!mp.inGame||msg.type!=='game.state'||!msg.state)return;if(msg.authoritative!==true){presenceOverlay('Błąd trybu online','Cribbage oczekuje teraz kanonicznego stanu z qqnd-game-server.');return}const next=normalizeNetworkState(msg.state);animateAuthoritativeDelta(state,next);mp.revision=Math.max(mp.revision,Number(msg.revision)||0);state=next;closeAll();updateNetworkPill(true);render();maybeOpenNetworkShow()});
    client.addEventListener('presence',e=>{const msg=e.detail;if(msg.type==='game.player.connection'){if(msg.connected){presenceOverlay('Gracz wrócił',`${msg.nickname||'Gracz'} odzyskał swój seat i zastany stan.`,true,1800)}else{const seconds=Math.max(0,Math.ceil(((msg.graceDeadline||Date.now())-Date.now())/1000));presenceOverlay(`Utracono połączenie z graczem ${msg.nickname||''}`.trim(),`Serwer zachowuje rękę i seat. Grace period: ${seconds} s.`)}}else if(msg.type==='game.player.bot_takeover'){presenceOverlay(`Gracz ${msg.nickname||''} nadal jest offline`.trim(),'Cribbage nie ma jeszcze bota online, więc po grace period gra czeka na powrót tego samego seat. Reconnect odzyska dokładnie zastany stan.')}else if(msg.type==='game.host.changed'){presenceOverlay('Zmienił się właściciel lobby','Gra jest server-authoritative — zmiana hosta nie zmienia kanonicznego stanu.',true,1800)}else if(msg.type==='game.presence'){const down=(msg.presence||[]).find(p=>!p.connected||p.botActive);if(!down&&mp.inGame)hidePresenceOverlay()}})
  }
'''
s, n = re.subn(r"  function bindMpClient\(client\)\{.*?\n  \}\n  async function ensureMpClient", lambda _m: bind + "  async function ensureMpClient", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('bindMpClient replacement failed')

network = r'''  let optimisticNetworkCardId='';
  let networkShowIndex=-1,networkShowKey='';
  function normalizeNetworkState(raw){return{...raw,selected:[],difficulty:'medium',training:false,log:state?.log||[],showQueue:[],showIndex:0,showAwarded:[]}}
  function animateAuthoritativeDelta(previous,next){if(!previous||!Array.isArray(previous.playedCards)||!Array.isArray(next.playedCards))return;if(next.playedCards.length!==previous.playedCards.length+1)return;const card=next.playedCards.at(-1);if(!card)return;if(card.id===optimisticNetworkCardId){optimisticNetworkCardId='';return}const p=next.lastPlayer===0?0:1;animatePlay(p,card)}
  function openNetworkShowResult(){if(!state||networkShowIndex<0)return;const item=state.showResults?.[networkShowIndex];if(!item)return;const score=item.score||{};$('#resultTitle').textContent=item.type==='crib'?t('result.crib',{name:state.names[item.player]}):t('result.hand',{name:state.names[item.player]});$('#resultPoints').textContent=score.total||0;const rows=[['score.fifteens',score.fifteens],['score.pairs',score.pairs],['score.runs',score.runs],['score.flush',score.flush],['score.nobs',score.nobs]].filter(x=>x[1]);$('#resultBreakdown').innerHTML=(rows.length?rows.map(([k,v])=>`<div><span>${t(k)}</span><b>${v}</b></div>`).join(''):`<div><span>${t('score.none')}</span><b>0</b></div>`)+`<div class="total"><span>${t('score.total')}</span><b>${score.total||0}</b></div>`;const cards=[...(item.cards||[]),...(item.starter?[item.starter]:[])];$('#resultCards').innerHTML=cards.map(c=>cardHTML(c)).join('');$('#resultCards button').parentElement?.querySelectorAll('button').forEach(b=>b.disabled=true);const last=networkShowIndex>=(state.showResults?.length||1)-1;$('[data-action="result-next"]').textContent=last?t('common.done'):t('common.continue');$('#resultModal').classList.remove('hidden')}
  function maybeOpenNetworkShow(){if(!state||!['hand-end','gameover'].includes(state.phase)||!state.showResults?.length)return;const key=`${state.handNo}:${state.scores.join('-')}:${state.showResults.length}`;if(key===networkShowKey)return;networkShowKey=key;networkShowIndex=0;setTimeout(openNetworkShowResult,30)}
  function advanceNetworkShow(){if(networkShowIndex<0)return;networkShowIndex++;if(networkShowIndex<(state.showResults?.length||0)){openNetworkShowResult();return}networkShowIndex=-1;$('#resultModal').classList.add('hidden');if(state?.phase==='gameover')toast(t('result.wins',{name:state.names[state.winnerPending]}))}
  function sendNetworkAction(action,payload={}){if(!mp.connected||!mp.client||!mp.inGame)return;mp.client.action(action,payload)}
  function startNetworkGame(){if(mp.role!=='host'||!mp.connected||!mp.client||mp.roomData?.players?.length!==2)return;mp.client.startGame({target:121})}
'''
s, n = re.subn(r"  function hiddenCards\(count,label\).*?  function startNetworkGame\(\)\{.*?\}\n", lambda _m: network, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('legacy bridge block replacement failed')

interceptor = r'''  function networkClickInterceptor(e){if(!state||state.mode!=='network-server')return;const card=e.target.closest('[data-card]');if(card&&card.closest('#bottomHand')&&state.phase==='pegging'){e.preventDefault();e.stopImmediatePropagation();if(state.active!==0)return;const chosen=state.hands[0].find(c=>c.id===card.dataset.card);if(!chosen)return;if(state.legalCardIds?.length&&!state.legalCardIds.includes(chosen.id)){toast(t('toast.illegal'));return}if(state.count+val(chosen)>31){toast(t('toast.illegal'));return}optimisticNetworkCardId=chosen.id;animatePlay(0,chosen);sendNetworkAction('play-card',{cardId:chosen.id});return}const button=e.target.closest('[data-action]');if(!button)return;const action=button.dataset.action;if(action==='confirm-discard'){e.preventDefault();e.stopImmediatePropagation();if(state.selected.length===2)sendNetworkAction('confirm-discard',{cardIds:[...state.selected]});else toast(t('toast.needTwo'))}else if(action==='go'){e.preventDefault();e.stopImmediatePropagation();if(state.active===0)sendNetworkAction('go')}else if(action==='next-hand'){e.preventDefault();e.stopImmediatePropagation();sendNetworkAction('next-hand')}else if(action==='result-next'){e.preventDefault();e.stopImmediatePropagation();advanceNetworkShow()}}
'''
s, n = re.subn(r"  function networkClickInterceptor\(e\)\{.*?\}\n  function multiplayerUiClick", lambda _m: interceptor + "  function multiplayerUiClick", s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('networkClickInterceptor replacement failed')

# Quick play action and no bridge polling/commits in B2.
s = s.replace("else if(action==='mp-refresh')refreshRooms();", "else if(action==='mp-refresh')refreshRooms();else if(action==='mp-quick'){ensureMpClient().then(client=>{client.joinQueue();mpStatus('mpGuestStatus',prefs.language==='pl'?'Szukam przeciwnika…':'Searching for opponent…')}).catch(()=>{})}", 1)
s = s.replace("  setInterval(networkTick,180);\n", "", 1)

# Let authoritative online players select discard cards locally regardless of canonical seat number.
s = s.replace(
    "if(state.phase==='discard'&&state.active===p&&(state.mode==='local'||p===0)){",
    "if(state.phase==='discard'&&p===0&&(state.mode==='network-server'||(state.active===p&&(state.mode==='local'||p===0)))){",
    1,
)

# Version cache bust for the authoritative client.
s = s.replace('multiplayer-server.js?v=20260909-1', 'multiplayer-server.js?v=20260909-2', 1)

p.write_text(s, encoding='utf-8')
print('Applied Cribbage server-authoritative B2 frontend migration.')
