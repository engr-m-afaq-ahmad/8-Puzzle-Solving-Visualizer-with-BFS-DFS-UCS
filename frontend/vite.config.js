import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: Vite hot-reloads on :5173 and proxies /api to Flask on :5000.
// Prod: `npm run build` emits static assets into backend/static, which
// Flask serves from the same origin on :5000 (relative API URLs).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
