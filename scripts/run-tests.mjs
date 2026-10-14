// Runs tests/*.test.ts: bundles each one with esbuild (a Vite dependency)
// and runs it with Node's native runner (node:test). No extra dependencies.
import { build } from 'esbuild';
import { readdirSync, mkdirSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
const out = '.test-build';
rmSync(out, { recursive: true, force: true });
mkdirSync(out);
const files = readdirSync('tests').filter((f) => f.endsWith('.test.ts'));
for (const f of files) {
  await build({ entryPoints: [`tests/${f}`], bundle: true, platform: 'node', format: 'esm', outfile: `${out}/${f.replace('.ts', '.mjs')}`, external: ['pixi.js'], logLevel: 'error' });
}
const r = spawnSync(process.execPath, ['--test', ...files.map((f) => `${out}/${f.replace('.ts', '.mjs')}`)], { stdio: 'inherit' });
rmSync(out, { recursive: true, force: true });
process.exit(r.status ?? 1);
