import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Changed from 3000 to 5173
    open: true, // Automatically open app in browser on start
    proxy: {
      // Proxy API requests to backend to avoid CORS issues in dev
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  resolve: {
    alias: {
      // Optional: Add aliases for cleaner imports if desired
      // '@': '/src', 
    }
  }
})