/// <reference types="vitest" />
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: './index.html',
        xliff: './xliff.html',
        tmx: './tmx.html',
      },
    },
  },
  plugins: [vue()],
  test: {
    environment: 'jsdom',
  },
})
