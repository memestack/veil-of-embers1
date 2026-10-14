/**
 * Uniform spatial grid for neighbourhood queries in hordes.
 * Rebuilt every simulation step, reusing arrays (no GC).
 */
export interface Spatial {
  x: number;
  y: number;
  radius: number;
  alive: boolean;
}

export class SpatialHash<T extends Spatial> {
  private cells = new Map<number, T[]>();
  private used: T[][] = [];
  private readonly result: T[] = [];

  constructor(public readonly cellSize = 48) {}

  private key(cx: number, cy: number): number {
    return (cx + 1024) * 4096 + (cy + 1024);
  }

  clear(): void {
    for (const arr of this.used) arr.length = 0;
    this.used.length = 0;
  }

  insert(item: T): void {
    const cx = Math.floor(item.x / this.cellSize);
    const cy = Math.floor(item.y / this.cellSize);
    const k = this.key(cx, cy);
    let arr = this.cells.get(k);
    if (!arr) {
      arr = [];
      this.cells.set(k, arr);
    }
    if (arr.length === 0) this.used.push(arr);
    arr.push(item);
  }

  /** Returns items whose circle may intersect circle (x, y, r). The array is reused: copy it if you need to keep it. */
  query(x: number, y: number, r: number): T[] {
    const out = this.result;
    out.length = 0;
    const cs = this.cellSize;
    const x0 = Math.floor((x - r - 24) / cs);
    const x1 = Math.floor((x + r + 24) / cs);
    const y0 = Math.floor((y - r - 24) / cs);
    const y1 = Math.floor((y + r + 24) / cs);
    for (let cy = y0; cy <= y1; cy++) {
      for (let cx = x0; cx <= x1; cx++) {
        const arr = this.cells.get(this.key(cx, cy));
        if (!arr) continue;
        for (let i = 0; i < arr.length; i++) {
          const it = arr[i];
          if (!it.alive) continue;
          const dx = it.x - x;
          const dy = it.y - y;
          const rr = r + it.radius;
          if (dx * dx + dy * dy <= rr * rr) out.push(it);
        }
      }
    }
    return out;
  }

  /** Nearest within r (ignores `exclude`). */
  nearest(x: number, y: number, r: number, exclude?: (t: T) => boolean): T | null {
    const list = this.query(x, y, r);
    let best: T | null = null;
    let bd = Infinity;
    for (const it of list) {
      if (exclude && exclude(it)) continue;
      const d = (it.x - x) ** 2 + (it.y - y) ** 2;
      if (d < bd) {
        bd = d;
        best = it;
      }
    }
    return best;
  }
}
