import type { World } from './World';
import { clamp, damp } from '../utils/math';

/**
 * Camera: follows the heroine with smoothing and subtle look-ahead, respects map bounds,
 * applies "trauma" shake (with a reduce option) and keeps zoom at pixel multiples.
 */
export class CameraController {
  x = 0;
  y = 0;
  zoom = 3;
  viewW = 640;
  viewH = 360;
  private lookX = 0;
  private lookY = 0;
  private t = 0;

  /** Zoom in half device-pixel steps: crisp art on any screen (16:9, 21:9, 9:16). */
  resize(cssW: number, cssH: number, res: number): void {
    const portrait = cssH > cssW;
    // pulled-back camera: ~620 logical px of visible height (heroine ≈ 5–6% of the screen)
    const target = portrait ? Math.min(cssW / 340, cssH / 600) : Math.min(cssH / 620, cssW / 1100);
    const dev = Math.max(1, Math.round(target * res * 2) / 2);
    this.zoom = dev / res;
    this.viewW = cssW / this.zoom;
    this.viewH = cssH / this.zoom;
  }

  snap(w: World): void {
    this.x = w.hero.x;
    this.y = w.hero.y - 12;
    this.lookX = this.lookY = 0;
  }

  update(dt: number, w: World, res: number): void {
    const h = w.hero;
    this.t += dt;
    this.lookX = damp(this.lookX, h.vx * 0.28, 3, dt);
    this.lookY = damp(this.lookY, h.vy * 0.22, 3, dt);
    const tx = h.x + this.lookX;
    const ty = h.y - 12 + this.lookY;
    this.x = damp(this.x, tx, 7, dt);
    this.y = damp(this.y, ty, 7, dt);
    const ar = w.arena;
    const hw = this.viewW / 2, hh = this.viewH / 2;
    const cx = ar.pxW > this.viewW ? clamp(this.x, hw, ar.pxW - hw) : ar.pxW / 2;
    const cy = ar.pxH > this.viewH ? clamp(this.y, hh, ar.pxH - hh) : ar.pxH / 2;
    w.trauma = Math.max(0, w.trauma - dt * 1.6);
    const s = w.trauma * w.trauma * 7;
    const sx = s * (Math.sin(this.t * 47.3) + Math.sin(this.t * 21.1) * 0.5);
    const sy = s * (Math.cos(this.t * 43.7) + Math.cos(this.t * 17.9) * 0.5);
    w.root.scale.set(this.zoom);
    const unit = 1 / (this.zoom * res);
    const px = Math.round((-(cx + sx) * this.zoom + (hw * this.zoom)) / unit) * unit;
    const py = Math.round((-(cy + sy) * this.zoom + (hh * this.zoom)) / unit) * unit;
    w.root.position.set(px, py);
  }

  /** Converts screen coordinates (CSS px) to world. */
  toWorld(w: World, sx: number, sy: number): [number, number] {
    return [(sx - w.root.x) / this.zoom, (sy - w.root.y) / this.zoom];
  }
}
