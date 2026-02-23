import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@execution-log': path.resolve(
        __dirname,
        '../../frontend/src/components/editor/execution-log',
      ),
    },
  },
  build: {
    outDir: path.resolve(__dirname, '../static/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'src/main.tsx'),
      output: {
        entryFileNames: 'run-inspector.js',
        assetFileNames: 'run-inspector.[ext]',
        format: 'iife',
        name: 'NormCodeInspector',
        inlineDynamicImports: true,
      },
    },
    sourcemap: false,
    cssCodeSplit: false,
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
