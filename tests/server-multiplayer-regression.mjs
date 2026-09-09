import fs from 'node:fs';

const html = fs.readFileSync('index.html', 'utf8');
const mp = fs.readFileSync('multiplayer-server.js', 'utf8');
let failures = 0;
function check(name, ok) { console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`); if (!ok) failures++; }

check('QQND websocket client is loaded', html.includes('multiplayer-server.js?v=20260909-1') && mp.includes("wss://api.qqnd.fyi/api/v1/ws"));
check('manual WebRTC exchange removed from runtime HTML', !html.includes('RTCPeerConnection') && !html.includes('createOffer()') && !html.includes('setRemoteDescription'));
check('shared room actions are present', html.includes("type: 'room.create'") || mp.includes("type: 'room.create'"));
check('game bridge uses game.action commit publish', mp.includes("type: 'game.action'") && mp.includes("type: 'game.state.commit'") && mp.includes("type: 'game.state.publish'"));
check('session resume is persisted locally', mp.includes('session.resume') && mp.includes('resumeToken'));
check('all table cards share player card CSS variables', html.includes('--game-card-w:94px') && html.includes('.peg-cards .card,.peg-cards .card-back') && html.includes('#resultCards .card,#resultCards .card-back'));
check('illegal cards are transparent without grayscale', html.includes('.card.illegal{opacity:.28!important;filter:none!important}'));
check('flight animation hides destination duplicate', html.includes('const flyingCards=new Set()') && html.includes("flyingCards.has(c.id)?'':cardHTML"));
check('summary cards have space above Done button', html.includes('#resultModal #resultCards{margin-bottom:30px'));
check('persistent connection overlay exists', html.includes('networkPresenceOverlay') && html.includes('game.player.bot_takeover'));
check('public room browser exists', html.includes('mpPublicRooms') && html.includes('mp-join-public'));

if (failures) { console.error(`\n${failures} regression check(s) failed.`); process.exit(1); }
console.log('\nAll server multiplayer/card regression checks passed.');
