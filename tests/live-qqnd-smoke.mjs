import assert from 'node:assert/strict';

const WS_URL = process.env.QQND_WS_URL || 'wss://api.qqnd.fyi/api/v1/ws';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

class SocketClient {
  constructor(label) {
    this.label = label;
    this.ws = null;
    this.queue = [];
    this.session = null;
    this.resumeToken = '';
  }

  async open() {
    this.ws = new WebSocket(WS_URL);
    this.ws.addEventListener('message', event => {
      try { this.queue.push(JSON.parse(String(event.data))); }
      catch (error) { console.error(`[${this.label}] invalid JSON`, error); }
    });
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`${this.label}: websocket open timeout`)), 10_000);
      this.ws.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
      this.ws.addEventListener('error', () => { clearTimeout(timer); reject(new Error(`${this.label}: websocket error`)); }, { once: true });
    });
    await this.waitFor('hello');
  }

  send(payload) {
    assert.equal(this.ws?.readyState, WebSocket.OPEN, `${this.label}: socket must be open`);
    this.ws.send(JSON.stringify(payload));
  }

  async waitFor(type, predicate = () => true, timeoutMs = 10_000) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const index = this.queue.findIndex(message => message?.type === type && predicate(message));
      if (index >= 0) return this.queue.splice(index, 1)[0];
      const immediateError = this.queue.find(message => message?.type === 'error');
      if (immediateError && type !== 'error') throw new Error(`${this.label}: server error while waiting for ${type}: ${JSON.stringify(immediateError)}`);
      await sleep(25);
    }
    throw new Error(`${this.label}: timeout waiting for ${type}; queued=${JSON.stringify(this.queue.slice(-12))}`);
  }

  async createSession(nickname) {
    this.send({ type: 'session.create', nickname });
    const created = await this.waitFor('session.created');
    this.session = created.session;
    this.resumeToken = created.resumeToken;
    assert.ok(this.session?.id, `${this.label}: session id missing`);
    assert.ok(this.resumeToken, `${this.label}: resume token missing`);
    return created;
  }

  close() {
    try { this.ws?.close(); } catch (_) {}
  }
}

function assertPrivateState(message, label) {
  assert.equal(message.authoritative, true, `${label}: state must be authoritative`);
  assert.equal(message.state?.mode, 'network-server', `${label}: projected mode`);
  assert.equal(message.state?.hands?.[0]?.length, 6, `${label}: own hand has six cards`);
  assert.equal(message.state?.hands?.[1]?.length, 6, `${label}: opponent hand has six placeholders`);
  assert.ok(message.state.hands[0].every(card => !String(card.id).startsWith('hidden-')), `${label}: own cards are visible`);
  assert.ok(message.state.hands[1].every(card => String(card.id).startsWith('hidden-')), `${label}: opponent cards stay private`);
}

const stamp = Date.now().toString().slice(-8);
const host = new SocketClient('host');
const guest = new SocketClient('guest');
let resumedGuest = null;
let roomId = '';

try {
  await Promise.all([host.open(), guest.open()]);
  await host.createSession(`SmokeA${stamp}`);
  await guest.createSession(`SmokeB${stamp}`);

  host.send({ type: 'room.create', game: 'cribbage', name: `Smoke ${stamp}`, visibility: 'private', maxPlayers: 2 });
  const created = await host.waitFor('room.created');
  roomId = created.room.id;
  assert.equal(created.room.game, 'cribbage');
  assert.equal(created.room.visibility, 'private');

  guest.send({ type: 'room.join', roomId });
  await guest.waitFor('room.joined');
  await host.waitFor('room.updated', message => message.room?.players?.length === 2);

  host.send({ type: 'game.start', roomId, botCount: 0, settings: { target: 61 } });
  const [hostStarted, guestStarted] = await Promise.all([
    host.waitFor('game.started'),
    guest.waitFor('game.started'),
  ]);
  assert.equal(hostStarted.authoritative, true);
  assert.equal(guestStarted.authoritative, true);

  let [hostState, guestState] = await Promise.all([
    host.waitFor('game.state'),
    guest.waitFor('game.state'),
  ]);
  assertPrivateState(hostState, 'host');
  assertPrivateState(guestState, 'guest');
  const initialRevision = Math.min(hostState.revision, guestState.revision);

  const hostDiscard = hostState.state.hands[0].slice(0, 2).map(card => card.id);
  host.send({ type: 'game.action', roomId, action: 'confirm-discard', payload: { cardIds: hostDiscard } });
  [hostState, guestState] = await Promise.all([
    host.waitFor('game.state', message => message.revision > initialRevision),
    guest.waitFor('game.state', message => message.revision > initialRevision),
  ]);
  assert.equal(hostState.state.discardsDone[0], true);
  assert.equal(guestState.state.discardsDone[1], true);

  const guestDiscard = guestState.state.hands[0].slice(0, 2).map(card => card.id);
  const afterFirstDiscardRevision = Math.min(hostState.revision, guestState.revision);
  guest.send({ type: 'game.action', roomId, action: 'confirm-discard', payload: { cardIds: guestDiscard } });
  [hostState, guestState] = await Promise.all([
    host.waitFor('game.state', message => message.revision > afterFirstDiscardRevision && message.state?.phase === 'pegging'),
    guest.waitFor('game.state', message => message.revision > afterFirstDiscardRevision && message.state?.phase === 'pegging'),
  ]);
  assert.equal(hostState.state.starter?.id?.length > 0, true);
  assert.equal(guestState.state.starter?.id?.length > 0, true);

  const actorIsHost = hostState.state.active === 0;
  const actor = actorIsHost ? host : guest;
  const actorState = actorIsHost ? hostState : guestState;
  const legalId = actorState.state.legalCardIds[0];
  assert.ok(legalId, 'active player must have a legal opening card');
  const peggingRevision = Math.min(hostState.revision, guestState.revision);
  actor.send({ type: 'game.action', roomId, action: 'play-card', payload: { cardId: legalId } });
  const [afterPlayHost, afterPlayGuest] = await Promise.all([
    host.waitFor('game.state', message => message.revision > peggingRevision && message.state?.playedCards?.length === 1),
    guest.waitFor('game.state', message => message.revision > peggingRevision && message.state?.playedCards?.length === 1),
  ]);
  assert.equal(afterPlayHost.state.playedCards[0].id, legalId);
  assert.equal(afterPlayGuest.state.playedCards[0].id, legalId);

  const actorAfter = actorIsHost ? afterPlayHost : afterPlayGuest;
  const illegalTurnCard = actorAfter.state.hands[0][0]?.id;
  assert.ok(illegalTurnCard, 'actor must still own a card for wrong-turn test');
  actor.send({ type: 'game.action', roomId, action: 'play-card', payload: { cardId: illegalTurnCard } });
  const rejected = await actor.waitFor('error', message => message.code === 'not_your_turn');
  assert.equal(rejected.code, 'not_your_turn');

  const guestCardsBeforeReconnect = afterPlayGuest.state.hands[0].map(card => card.id).sort();
  const guestSession = guest.session.id;
  const guestToken = guest.resumeToken;
  guest.close();
  await sleep(250);

  resumedGuest = new SocketClient('guest-resume');
  await resumedGuest.open();
  resumedGuest.send({ type: 'session.resume', sessionId: guestSession, resumeToken: guestToken });
  const resumed = await resumedGuest.waitFor('session.resumed');
  assert.equal(resumed.session.id, guestSession, 'resume restores the same session');
  resumedGuest.send({ type: 'game.state.get', roomId });
  const resumedState = await resumedGuest.waitFor('game.state');
  assert.equal(resumedState.viewerSeat, 1, 'resume restores the same seat');
  assert.equal(resumedState.authoritative, true);
  assert.deepEqual(resumedState.state.hands[0].map(card => card.id).sort(), guestCardsBeforeReconnect, 'resume restores the same private hand');
  assert.ok(resumedState.revision >= afterPlayGuest.revision, 'resume does not roll state back');

  console.log('PASS  live QQND Cribbage: private room create/join/start');
  console.log('PASS  live QQND Cribbage: private projected hands');
  console.log('PASS  live QQND Cribbage: legal discard + pegging action');
  console.log('PASS  live QQND Cribbage: illegal wrong-turn action rejected');
  console.log('PASS  live QQND Cribbage: reconnect resumes same session/seat/state');
} finally {
  try { resumedGuest?.send({ type: 'room.leave', roomId }); } catch (_) {}
  try { host.send({ type: 'room.leave', roomId }); } catch (_) {}
  await sleep(50);
  resumedGuest?.close();
  guest.close();
  host.close();
}
