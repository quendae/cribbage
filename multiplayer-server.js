(() => {
  'use strict';
  const DEFAULT_URL = 'wss://api.qqnd.fyi/api/v1/ws';
  const SESSION_KEY = 'cribbage.qqnd.session.v1';

  class QQNDMultiplayerClient extends EventTarget {
    constructor({ url = DEFAULT_URL, game = 'cribbage' } = {}) {
      super();
      this.url = url;
      this.game = game;
      this.ws = null;
      this.session = null;
      this.resumeToken = '';
      this.room = null;
      this.started = false;
      this.manualClose = false;
      this.reconnectTimer = null;
      this.reconnectAttempt = 0;
      this.pendingNickname = '';
      this.readyPromise = null;
      this.readyResolve = null;
    }

    emit(type, detail) { this.dispatchEvent(new CustomEvent(type, { detail })); }
    send(payload) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) throw new Error('qqnd_socket_not_open');
      this.ws.send(JSON.stringify(payload));
    }

    loadSession() {
      try {
        const saved = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
        if (saved?.sessionId && saved?.resumeToken) return saved;
      } catch (_) {}
      return null;
    }

    saveSession() {
      if (!this.session?.id || !this.resumeToken) return;
      try { localStorage.setItem(SESSION_KEY, JSON.stringify({ sessionId: this.session.id, resumeToken: this.resumeToken })); } catch (_) {}
    }

    clearSession() {
      this.session = null;
      this.resumeToken = '';
      try { localStorage.removeItem(SESSION_KEY); } catch (_) {}
    }

    async connect(nickname = 'Gracz') {
      this.pendingNickname = String(nickname || 'Gracz').trim().slice(0, 20) || 'Gracz';
      if (this.ws?.readyState === WebSocket.OPEN && this.session) return this.session;
      if (this.readyPromise) return this.readyPromise;
      this.manualClose = false;
      this.readyPromise = new Promise(resolve => { this.readyResolve = resolve; });
      this.openSocket();
      return this.readyPromise;
    }

    openSocket() {
      clearTimeout(this.reconnectTimer);
      const ws = new WebSocket(this.url);
      this.ws = ws;
      ws.addEventListener('message', event => this.onMessage(event.data));
      ws.addEventListener('close', () => this.onClose());
      ws.addEventListener('error', () => this.emit('connection', { connected: false, state: 'error' }));
    }

    onClose() {
      this.emit('connection', { connected: false, state: 'closed' });
      if (this.manualClose) return;
      const delay = Math.min(8000, 500 * (2 ** Math.min(this.reconnectAttempt++, 4)));
      this.reconnectTimer = setTimeout(() => this.openSocket(), delay);
    }

    onMessage(raw) {
      let message;
      try { message = JSON.parse(raw); } catch (_) { return; }
      if (message.type === 'hello') {
        const saved = this.loadSession();
        if (saved) this.send({ type: 'session.resume', sessionId: saved.sessionId, resumeToken: saved.resumeToken });
        else this.send({ type: 'session.create', nickname: this.pendingNickname });
        return;
      }
      if (message.type === 'session.created') {
        this.session = message.session;
        this.resumeToken = message.resumeToken;
        this.saveSession();
        this.reconnectAttempt = 0;
        this.readyResolve?.(this.session);
        this.readyResolve = null;
        this.readyPromise = null;
        this.emit('connection', { connected: true, state: 'ready', resumed: false });
        this.emit('session', { session: this.session, resumed: false });
        return;
      }
      if (message.type === 'session.resumed') {
        const saved = this.loadSession();
        this.session = message.session;
        this.resumeToken = saved?.resumeToken || this.resumeToken;
        this.reconnectAttempt = 0;
        this.readyResolve?.(this.session);
        this.readyResolve = null;
        this.readyPromise = null;
        this.emit('connection', { connected: true, state: 'ready', resumed: true });
        this.emit('session', { session: this.session, resumed: true, rooms: message.rooms || [] });
        const active = (message.rooms || []).find(room => room.game === this.game);
        if (active) { this.room = active; this.emit('room', { room: active, resumed: true }); }
        return;
      }
      if (message.type === 'error') {
        if (message.code === 'invalid_session_credentials') {
          this.clearSession();
          this.send({ type: 'session.create', nickname: this.pendingNickname });
          return;
        }
        this.emit('server-error', message);
        return;
      }
      if (message.type === 'rooms.list') { this.emit('rooms', { rooms: message.rooms || [] }); return; }
      if (message.type === 'room.created' || message.type === 'room.joined' || message.type === 'room.updated') {
        this.room = message.room;
        this.emit('room', { room: message.room, event: message.type });
        return;
      }
      if (message.type === 'room.left' || message.type === 'room.closed') {
        if (!message.roomId || this.room?.id === message.roomId) this.room = null;
        this.emit('room-left', message);
        return;
      }
      if (message.type === 'match.found') {
        this.room = message.room;
        this.emit('match-found', message);
        this.emit('room', { room: message.room, event: message.type });
        return;
      }
      if (message.type === 'queue.joined' || message.type === 'queue.left') { this.emit('queue', message); return; }
      if (message.type === 'game.started') {
        this.started = true;
        this.room = message.room || this.room;
        this.emit('game-started', message);
        return;
      }
      if (message.type === 'game.state' || message.type === 'game.state.empty') { this.emit('game-state', message); return; }
      if (message.type === 'game.player.connection' || message.type === 'game.player.bot_takeover' || message.type === 'game.presence' || message.type === 'game.host.changed') {
        this.emit('presence', message);
        return;
      }
      this.emit('message', message);
    }

    listRooms() { this.send({ type: 'rooms.list', game: this.game }); }
    createRoom(name, visibility = 'public') { this.send({ type: 'room.create', game: this.game, name, visibility, maxPlayers: 2 }); }
    joinRoom(roomId) { this.send({ type: 'room.join', roomId: String(roomId || '').trim().toUpperCase() }); }
    leaveRoom(roomId = this.room?.id) { if (roomId) this.send({ type: 'room.leave', roomId }); }
    startGame(settings = {}) { if (!this.room?.id) throw new Error('qqnd_room_missing'); this.send({ type: 'game.start', roomId: this.room.id, botCount: 0, settings }); }
    action(action, payload = {}, actionId) { if (!this.room?.id) return; this.send({ type: 'game.action', roomId: this.room.id, action, payload, ...(actionId ? { actionId } : {}) }); }
    getState() { if (this.room?.id) this.send({ type: 'game.state.get', roomId: this.room.id }); }
    joinQueue() { this.send({ type: 'queue.join', game: this.game }); }
    leaveQueue() { this.send({ type: 'queue.leave', game: this.game }); }
    close() { this.manualClose = true; clearTimeout(this.reconnectTimer); try { this.ws?.close(); } catch (_) {} this.ws = null; }
  }

  window.QQNDMultiplayerClient = QQNDMultiplayerClient;
})();
