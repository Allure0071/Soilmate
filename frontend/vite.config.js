import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const apiTarget = process.env.SOIL_API_TARGET || 'http://127.0.0.1:18000'
const dataApiTarget = process.env.SOIL_DATA_API_TARGET || apiTarget
const tileTarget = process.env.SOIL_TILE_TARGET || apiTarget

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api/data': dataApiTarget,
      '/api': apiTarget,
      '/tiles': tileTarget
    }
  },
  build: { outDir: 'dist' }
})
