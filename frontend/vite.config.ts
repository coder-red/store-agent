import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const backend = `http://localhost:${process.env.BACKEND_PORT || '8000'}`

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': backend,
      '/ws': { target: backend.replace('http', 'ws'), ws: true },
      '/webhook': backend,
      '/health': backend,
    },
  },
  preview: {
    proxy: {
      '/api': backend,
      '/ws': { target: backend.replace('http', 'ws'), ws: true },
      '/webhook': backend,
      '/health': backend,
    },
  },
  build: {
    outDir: 'dist',
  },
})
