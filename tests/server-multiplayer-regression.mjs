import fs from 'node:fs';

const html = fs.readFileSync('index.html', 'utf8');
const mp = fs.readFileSync('multiplayer-server.js', 'utf8');
let failures = 0;
function check(name, ok) { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`); if (!ok) failures++; }

check('QQND websocket client is loaded', html.includes('multiplayer-server.js?v=20260909-2') && mp.includes("wss://api.qqnd.fyi/api/v1/ws"));
check('manual WebRTC exchange removed from runtime HTML', !html.includes('RTCPeerConnection') && !html.includes('createOffer()') && !html.includes('setRemoteDescription'));
check('shared public/private room actions are present', mp.includes("type: 'room.create'") && mp.includes("type: 'room.join'"));
check('authoritative client sends actions but never canonical state', mp.includes("type: 'game.action'") && !mp.includes('game.state.commit') && !mp.includes('game.state.publish') && !html.includes('.commit(mp.revision') && !html.includes('.publish(mp.revision'));
check('frontend requires authoritative game.state', html.includes("msg.authoritative!==true") && html.includes("mode:'network-server'"));
check('session resume is persisted locally', mp.includes('session.resume') && mp.includes('resumeToken'));
check('Quick Play uses shared matchmaking queue', mp.includes("type: 'queue.join'") && html.includes("data-action=\"mp-quick\""));
check('all table cards share player card CSS variables', html.includes('--game-card-w:94px') && html.includes('.peg-cards .card,.peg-cards .card-back') && html.includes('#resultCards .card,#resultCards .card-back'));
check('illegal cards are transparent without grayscale', html.includes('.card.illegal{opacity:.28!important;filter:none!important}'));
check('flight animation hides destination duplicate', html.includes('const flyingCards=new Set()') && html.includes("flyingCards.has(c.id)?'':cardHTML"));
check('authoritative animation handles opponent delta', html.includes('animateAuthoritativeDelta') && html.includes('optimisticNetworkCardId'));
check('summary cards have space above Done button', html.includes('#resultModal #resultCards{margin-bottom:30px'));
check('server scoring results are rendered without client addPoints', html.includes('openNetworkShowResult') && html.includes('item.score||{}'));
check('persistent connection overlay exists', html.includes('networkPresenceOverlay') && html.includes('game.player.bot_takeover'));
check('public room browser exists', html.includes('mpPublicRooms') && html.includes('mp-join-public'));

try { new Function(mp); check('multiplayer-server.js parses as JavaScript', true); } catch (error) { console.error(error); check('multiplayer-server.js parses as JavaScript', false); }
const inlineScripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(match => match[1]).filter(Boolean);
let parseOk = true;
for (const code of inlineScripts) {
  try { new Function(code); } catch (error) { parseOk = false; console.error(error); break; }
}
check('inline runtime scripts parse as JavaScript', parseOk);

if (failures) { console.error(`\n${failures} regression check(s) failed.`); process.exit(1); }
console.log('\nAll authoritative multiplayer/card regression checks passed.');
