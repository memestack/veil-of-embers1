import { defineConfig } from 'vite';

// base relativa: o build funciona servido de qualquer subpasta (itch.io, GitHub Pages, arquivo local via servidor)
export default defineConfig({
  base: './',
  build: {
    target: 'es2022',
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 1600,
  },
  server: { host: true },
});
