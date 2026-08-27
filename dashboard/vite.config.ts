import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8005',
    },
  },
  preview: {
    allowedHosts: ['.manus.computer'],
  },
  build: {
    outDir: 'dist',
  },
});
