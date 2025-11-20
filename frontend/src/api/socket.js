import { io } from 'socket.io-client';

// Load Vite environment variables for the WebSocket connection
const WS_URL = import.meta.env.VITE_WS_URL || '';
const PATH = import.meta.env.VITE_SOCKET_PATH || '/ws';

let socket = null;

export function initSocket(opts = {}) {
  // Return existing socket if already initialized
  if (socket) return socket;
  
  const token = localStorage.getItem('authToken');
  
  socket = io(WS_URL || undefined, {
    path: PATH,
    autoConnect: false,
    transports: ['websocket'],
    // Pass token for connection authentication handshake
    auth: token ? { token } : undefined,
    ...opts
  });
  
  return socket;
}

export function getSocket() {
  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}