import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const BACKEND_TARGET = 'http://localhost:8000';

export default defineConfig({
  plugins: [react()], 
  
  server: {
    proxy: {
      // Proxy all /api requests to the backend REST server
      '/api': {
        target: BACKEND_TARGET,
        changeOrigin: true,
        secure: false,
      },

      // Proxy all /ws requests to the backend WebSocket server
      '/ws': {
        target: BACKEND_TARGET,
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
  }
});