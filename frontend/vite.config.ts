import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true }
    }
  },
  build: {
    // 拆分大依赖，让首屏只下载 main chunk（约 350KB gzipped）
    // element-plus 全量打包约 700KB gzipped，路由级 dynamic import 异步加载
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('element-plus') || id.includes('@element-plus')) {
              return 'element-plus'
            }
            if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) {
              return 'vue-runtime'
            }
            if (id.includes('@vueuse') || id.includes('axios')) {
              return 'vendor-misc'
            }
            return 'vendor'
          }
          return undefined
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      }
    },
    chunkSizeWarningLimit: 800,
  }
})