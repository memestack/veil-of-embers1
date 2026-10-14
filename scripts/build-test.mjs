// Build de teste local (sem Vite): esbuild + PixiJS 8 carregado por import map.
// Uso interno da validação; o build oficial é `npm run build` (Vite).
import { build } from 'esbuild';
import { cpSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
const out = process.argv[2] ?? 'dist-test';
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
await build({
  entryPoints: ['src/main.ts'], bundle: true, format: 'esm', outfile: `${out}/game.js`, external: ['pixi.js', '/assets/*'],
  loader: { '.css': 'css' }, define: { 'import.meta.env': '{"BASE_URL":"./"}' }, target: 'es2022', minify: false, sourcemap: false,
});
const cssPath = `${out}/game.css`;
writeFileSync(cssPath, readFileSync(cssPath, 'utf8').replaceAll('url(/assets/', 'url(assets/'));
cpSync('public/assets', `${out}/assets`, { recursive: true });
const pixi = process.env.PIXI_URL ?? 'https://cdn.jsdelivr.net/npm/pixi.js@8/dist/pixi.min.mjs';
writeFileSync(`${out}/index.html`, `<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>Véu de Brasas</title><link rel="stylesheet" href="game.css"><script type="importmap">{"imports":{"pixi.js":"${pixi}"}}</script></head>
<body><div id="app"></div><div id="ui"></div><script type="module" src="game.js"></script></body></html>`);
console.log('ok ->', out);
