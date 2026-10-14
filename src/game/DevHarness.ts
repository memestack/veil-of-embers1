/**
 * Test tools (only with the debug panel open: F3 or the ` key).
 *   G  invincibility          P  autopilot (follows the objective, flees the horde, picks cards)
 *   N  skip current step      B  stress test (≈420 creatures + max arsenal)
 *   T  speed 1× / 3×
 * Nothing here is visible in the normal game.
 */
import type { World } from './World';
import type { Director } from '../systems/Director';
import type { CardDef } from '../content/upgrades';
import type { EnemyKind } from '../content/enemies';
import { rng, TAU } from '../utils/math';

export class DevHarness {
  god = false;
  auto = false;
  turbo = 1;
  errors: string[] = [];
  private wander = 0;
  frameMs: number[] = [];

  constructor() {
    window.addEventListener('error', (e) => this.errors.push(String(e.message)));
    window.addEventListener('unhandledrejection', (e) => this.errors.push(String((e as PromiseRejectionEvent).reason)));
  }

  /** Autopilot movement vector. */
  move(w: World, d: Director): { x: number; y: number; dash: boolean; pulse: boolean } {
    const h = w.hero;
    let tx: number | null = null, ty = 0;
    const s = d.step;
    if (s.type === 'reach' || s.type === 'channel') [tx, ty] = d.anchorPos;
    else if (s.type === 'portal' && d.portalPos) [tx, ty] = d.portalPos;
    else if ((s.type === 'elite' && d.elite) || (s.type === 'boss' && d.boss)) {
      const e = s.type === 'elite' ? d.elite! : d.boss!.e;
      // orbits ~110 px from the target
      const a = Math.atan2(h.y - e.y, h.x - e.x) + 0.6;
      tx = e.x + Math.cos(a) * 120;
      ty = e.y + Math.sin(a) * 90;
    }
    if (tx === null) {
      this.wander += 1 / 60;
      const [cx, cy] = [w.arena.pxW / 2, w.arena.pxH / 2];
      tx = cx + Math.cos(this.wander * 0.3) * 220;
      ty = cy + Math.sin(this.wander * 0.3) * 140;
    }
    let mx = tx - h.x, my = ty - h.y;
    const l = Math.hypot(mx, my) || 1;
    const near = s.type === 'channel' || s.type === 'portal' ? 0 : 1;
    mx = (mx / l) * Math.min(1, l / 30);
    my = (my / l) * Math.min(1, l / 30);
    // horde repulsion
    let rx = 0, ry = 0, close = 0;
    for (const e of w.hash.query(h.x, h.y, 70)) {
      const dx = h.x - e.x, dy = h.y - e.y;
      const dd = Math.hypot(dx, dy) || 1;
      rx += (dx / dd) * (70 - dd) / 70;
      ry += (dy / dd) * (70 - dd) / 70;
      if (dd < 28) close++;
    }
    mx += rx * (0.9 + near * 0.6);
    my += ry * (0.9 + near * 0.6);
    const n = Math.hypot(mx, my);
    if (n > 1) {
      mx /= n;
      my /= n;
    }
    return { x: mx, y: my, dash: close >= 2 && h.dashCd <= 0, pulse: close >= 4 };
  }

  /** Automatic card choice: prefers legendaries and new weapons (covers the most content). */
  pickCard(offer: CardDef[]): CardDef {
    const score = (c: CardDef) => (c.rarity === 'legendary' ? 3 : c.kind === 'weapon' ? 2 : c.rarity === 'rare' ? 1.5 : 1) + rng.next() * 0.3;
    return [...offer].sort((a, b) => score(b) - score(a))[0];
  }

  stress(w: World, spawn: (k: EnemyKind, x: number, y: number) => unknown): void {
    for (const id of ['w_lance', 'w_chain', 'w_lotus', 'w_wind']) w.run.levels[id] = 5;
    Object.assign(w.run.levels, { u_twin: 3, u_pierce: 3, u_crown_big: 4, u_burn: 3, u_fury: 4, u_focus: 3, c_tornado: 1, c_shatter: 1, c_dawn: 1, l_solar: 1 });
    w.refreshStats();
    const kinds: EnemyKind[] = ['ferr', 'ferr', 'ferr', 'mord', 'mord', 'lodo', 'vesp', 'carap', 'sapo', 'suss'];
    for (let i = 0; i < 420; i++) {
      const a = rng.range(0, TAU), r = rng.range(180, 420);
      const [x, y] = w.arena.nearestFree(w.hero.x + Math.cos(a) * r, w.hero.y + Math.sin(a) * r * 0.7);
      spawn(kinds[i % kinds.length], x + rng.range(-10, 10), y + rng.range(-10, 10));
    }
  }

  stat(ms: number): void {
    this.frameMs.push(ms);
    if (this.frameMs.length > 600) this.frameMs.shift();
  }

  get p95(): number {
    if (!this.frameMs.length) return 0;
    const s = [...this.frameMs].sort((a, b) => a - b);
    return s[Math.floor(s.length * 0.95)];
  }
}
