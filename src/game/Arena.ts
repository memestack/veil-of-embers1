import { Container, Sprite } from 'pixi.js';
import { assets, type MapData } from './AssetLoader';
import { PROPS } from '../content/props';

export interface PropCollider {
  x: number;
  y: number;
  r: number;
}

export interface LightSource {
  sprite: Sprite;
  base: number;
  flicker: boolean;
  phase: number;
}

const SOLID = new Set(['#', '~']);

/**
 * Arena built from a hand-authored map (JSON): ground layers with edge autotiling,
 * hand-placed props, colliders and ambient lights.
 */
export class Arena {
  readonly data: MapData;
  readonly T: number;
  readonly W: number;
  readonly H: number;
  readonly pxW: number;
  readonly pxH: number;
  readonly solid: Uint8Array;
  readonly colliders: PropCollider[] = [];
  readonly lights: LightSource[] = [];
  /** colliders per 64px cell for fast lookup. */
  private colGrid = new Map<number, PropCollider[]>();
  /** walkable tiles of each spawn zone. */
  readonly zoneCells: [number, number][][] = [];

  constructor(data: MapData) {
    this.data = data;
    this.T = data.tileSize;
    this.W = data.width;
    this.H = data.height;
    this.pxW = this.W * this.T;
    this.pxH = this.H * this.T;
    this.solid = new Uint8Array(this.W * this.H);
    for (let y = 0; y < this.H; y++) for (let x = 0; x < this.W; x++) this.solid[y * this.W + x] = SOLID.has(data.rows[y][x]) ? 1 : 0;
    for (const [zx, zy, zw, zh] of data.spawns) {
      const cells: [number, number][] = [];
      for (let y = zy; y < zy + zh; y++) for (let x = zx; x < zx + zw; x++) if (!this.isSolidTile(x, y)) cells.push([x, y]);
      this.zoneCells.push(cells);
    }
  }

  isSolidTile(tx: number, ty: number): boolean {
    if (tx < 0 || ty < 0 || tx >= this.W || ty >= this.H) return true;
    return this.solid[ty * this.W + tx] === 1;
  }

  isSolidAt(px: number, py: number): boolean {
    return this.isSolidTile(Math.floor(px / this.T), Math.floor(py / this.T));
  }

  tileCenter(tx: number, ty: number): [number, number] {
    return [tx * this.T + this.T / 2, ty * this.T + this.T / 2];
  }

  /** Builds the visual layers. */
  build(ground: Container, low: Container, tall: Container, lights: Container): void {
    const ts = `tiles_${this.data.tileset}` as const;
    const rows = this.data.rows;
    const at = (x: number, y: number): string => (x < 0 || y < 0 || x >= this.W || y >= this.H ? '#' : rows[y][x]);
    const mask = (x: number, y: number, same: (c: string) => boolean): number =>
      (same(at(x, y - 1)) ? 0 : 1) | (same(at(x + 1, y)) ? 0 : 2) | (same(at(x, y + 1)) ? 0 : 4) | (same(at(x - 1, y)) ? 0 : 8);
    // fixed per-position variation (tile painting; the map itself is hand-authored)
    const hash = (x: number, y: number): number => (((x * 73856093) ^ (y * 19349663)) >>> 0) % 100;
    const groundVar = (x: number, y: number): number => {
      const r = hash(x, y);
      return r < 55 ? 0 : r < 70 ? 1 : r < 80 ? 2 : r < 88 ? 3 : r < 95 ? 4 : 5;
    };
    const put = (name: string, idx: number, x: number, y: number) => {
      const fr = assets.anim(ts, name);
      const s = new Sprite(fr[idx % fr.length]);
      s.position.set(x * this.T, y * this.T);
      ground.addChild(s);
    };
    // layers: ground -> paths -> plazas -> cliffs/water (overlapping jagged edges)
    for (let y = 0; y < this.H; y++) for (let x = 0; x < this.W; x++) put('ground', groundVar(x, y), x, y);
    for (let y = 0; y < this.H; y++)
      for (let x = 0; x < this.W; x++) {
        const c = rows[y][x];
        if (c === ',') put(`cobble${mask(x, y, (q) => q === ',' || q === '=')}`, x + y, x, y);
      }
    for (let y = 0; y < this.H; y++)
      for (let x = 0; x < this.W; x++) if (rows[y][x] === '=') put(`plaza${mask(x, y, (q) => q === '=')}`, hash(x + 7, y + 3), x, y);
    for (let y = 0; y < this.H; y++)
      for (let x = 0; x < this.W; x++) if (SOLID.has(rows[y][x])) put(`cliff${mask(x, y, (q) => SOLID.has(q))}`, x * 7 + y * 3, x, y);
    // hand-placed props
    for (const p of this.data.props) {
      const def = PROPS[p.type];
      if (!def) {
        console.warn('Prop desconhecido no mapa:', p.type);
        continue;
      }
      const s = new Sprite(assets.tex('props', p.type));
      s.anchor.set(0.5, def.anchorY ?? 0.94);
      s.position.set(p.x, p.y);
      if (def.layer === 'tall') {
        s.zIndex = p.y;
        tall.addChild(s);
      } else low.addChild(s);
      if (def.r > 0) this.addCollider({ x: p.x, y: p.y + (def.oy ?? -2), r: def.r });
      if (def.light) {
        const l = new Sprite(assets.tex('fx', def.light.tex));
        l.anchor.set(0.5);
        l.blendMode = 'add';
        l.scale.set(def.light.scale);
        l.alpha = def.light.alpha;
        l.position.set(p.x, p.y + def.light.oy);
        lights.addChild(l);
        this.lights.push({ sprite: l, base: def.light.alpha, flicker: !!def.light.flicker, phase: (p.x * 0.13 + p.y * 0.07) % 6.28 });
      }
    }
  }

  private addCollider(c: PropCollider): void {
    this.colliders.push(c);
    const x0 = Math.floor((c.x - c.r) / 64), x1 = Math.floor((c.x + c.r) / 64);
    const y0 = Math.floor((c.y - c.r) / 64), y1 = Math.floor((c.y + c.r) / 64);
    for (let y = y0; y <= y1; y++)
      for (let x = x0; x <= x1; x++) {
        const k = x * 1000 + y;
        let a = this.colGrid.get(k);
        if (!a) this.colGrid.set(k, (a = []));
        a.push(c);
      }
  }

  updateLights(time: number): void {
    for (const l of this.lights) {
      if (!l.flicker) continue;
      l.sprite.alpha = l.base * (0.85 + 0.1 * Math.sin(time * 7 + l.phase) + 0.05 * Math.sin(time * 17.3 + l.phase * 2));
    }
  }

  /**
   * Resolves a circle against solid tiles and prop colliders.
   * Returns true on contact (useful to cancel charges).
   */
  resolve(e: { x: number; y: number }, r: number, props = true): boolean {
    let hit = false;
    const T = this.T;
    for (let iter = 0; iter < 2; iter++) {
      const tx0 = Math.floor((e.x - r) / T), tx1 = Math.floor((e.x + r) / T);
      const ty0 = Math.floor((e.y - r) / T), ty1 = Math.floor((e.y + r) / T);
      for (let ty = ty0; ty <= ty1; ty++) {
        for (let tx = tx0; tx <= tx1; tx++) {
          if (!this.isSolidTile(tx, ty)) continue;
          const cx = Math.max(tx * T, Math.min(e.x, tx * T + T));
          const cy = Math.max(ty * T, Math.min(e.y, ty * T + T));
          const dx = e.x - cx, dy = e.y - cy;
          const d2 = dx * dx + dy * dy;
          if (d2 < r * r) {
            hit = true;
            if (d2 > 0.0001) {
              const d = Math.sqrt(d2);
              e.x += (dx / d) * (r - d);
              e.y += (dy / d) * (r - d);
            } else {
              // centre inside the tile: push to the nearest free neighbour
              const [fx, fy] = this.nearestFree(e.x, e.y);
              e.x = fx;
              e.y = fy;
            }
          }
        }
      }
    }
    if (props) {
      const list = this.colGrid.get(Math.floor(e.x / 64) * 1000 + Math.floor(e.y / 64));
      if (list) {
        for (const c of list) {
          const dx = e.x - c.x, dy = e.y - c.y;
          const rr = r + c.r;
          const d2 = dx * dx + dy * dy;
          if (d2 < rr * rr && d2 > 0.0001) {
            const d = Math.sqrt(d2);
            e.x += (dx / d) * (rr - d);
            e.y += (dy / d) * (rr - d);
            hit = true;
          }
        }
      }
    }
    return hit;
  }

  nearestFree(px: number, py: number): [number, number] {
    const tx = Math.floor(px / this.T), ty = Math.floor(py / this.T);
    for (let rad = 0; rad < 12; rad++)
      for (let dy = -rad; dy <= rad; dy++)
        for (let dx = -rad; dx <= rad; dx++) {
          if (Math.max(Math.abs(dx), Math.abs(dy)) !== rad) continue;
          if (!this.isSolidTile(tx + dx, ty + dy)) return this.tileCenter(tx + dx, ty + dy);
        }
    return this.tileCenter(this.data.start[0], this.data.start[1]);
  }

  /** Simple line of sight by tile sampling (for charges and aiming). */
  lineFree(ax: number, ay: number, bx: number, by: number): boolean {
    const d = Math.hypot(bx - ax, by - ay);
    const n = Math.ceil(d / 12);
    for (let i = 1; i < n; i++) {
      const t = i / n;
      if (this.isSolidAt(ax + (bx - ax) * t, ay + (by - ay) * t)) return false;
    }
    return true;
  }
}
