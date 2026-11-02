import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const apiTarget = process.env.SOIL_API_TARGET || 'http://127.0.0.1:18000'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': apiTarget,
      '/tiles': apiTarget
    }
  },
  build: { outDir: 'dist' }
})
