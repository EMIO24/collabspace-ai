import { io } from 'socket.io-client';

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.heartbeatInterval = null;
    this.connectionState = "disconnected"; // disconnected | connecting | connected
  }

  connect(workspaceId, token) {
    if (this.socket) {
      this.disconnect();
    }

    this.connectionState = "connecting";

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

    this.socket = io(wsUrl, {
      path: `/ws/workspace/${workspaceId}/`,
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1200,
    });

    // 🔌 Successfully connected
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.connectionState = "connected";
      this.reconnectAttempts = 0;

      this.startHeartbeat();
    });

    // ❌ Disconnected
    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.connectionState = "disconnected";
      this.stopHeartbeat();
    });

    // ⚠️ Connection errors
    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.connectionState = "disconnected";
      this.reconnectAttempts++;
    });

    // Register socket event forwarding
    this.setupEventListeners();
  }

  setupEventListeners() {
    const events = [
      'task.created',
      'task.updated',
      'task.deleted',
      'message.new',
      'user.presence',
      'user.typing',
      'notification.new',
    ];

    events.forEach(eventName => {
      this.socket.on(eventName, (data) => this.emit(eventName, data));
    });
  }

  // ❤️ Heartbeat to keep connection alive
  startHeartbeat() {
    if (this.heartbeatInterval) return;

    this.heartbeatInterval = setInterval(() => {
      if (this.socket && this.socket.connected) {
        this.socket.emit("heartbeat", { time: Date.now() });
      }
    }, 15000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.stopHeartbeat();
    this.listeners.clear();
  }

  // 📢 Event Emitter
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;

    const list = this.listeners.get(event);
    const idx = list.indexOf(callback);

    if (idx > -1) list.splice(idx, 1);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(cb => cb(data));
    }
  }

  // 📩 Send Methods
  sendMessage(channelId, content) {
    this.socket?.emit('message.send', { channel: channelId, content });
  }

  sendTyping(channelId, typing) {
    this.socket?.emit('user.typing', { channel: channelId, typing });
  }

  updatePresence(status) {
    this.socket?.emit('user.presence', { status });
  }
}

export default new WebSocketManager();
