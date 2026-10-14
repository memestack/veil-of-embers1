import { Container, Sprite, Texture } from 'pixi.js';

/**
 * Pooled textured particles. Two layers: additive (fire, light, sparks) and
 * normal (smoke, fragments). Max count set by graphics quality.
 */
export interface EmitOpts {
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  life: number;
  tex?: Texture;
  frames?: Texture[];
  /** if true, the animation steps through frames over its life. */
  frameByLife?: boolean;
  scale?: number;
  scaleEnd?: number;
  alpha?: number;
  alphaEnd?: number;
  rot?: number;
  vr?: number;
  gravity?: number;
  drag?: number;
  tint?: number;
  add?: boolean;
  /** height above ground (for fragments that fall and bounce). */
  z?: number;
  vz?: number;
  flip?: boolean;
}

class P {
  sp: Sprite;
  alive = false;
  x = 0; y = 0; vx = 0; vy = 0; z = 0; vz = 0;
  life = 0; max = 1;
  s0 = 1; s1 = 1; a0 = 1; a1 = 0;
  rot = 0; vr = 0; grav = 0; drag = 0;
  frames: Texture[] | null = null;
  byLife = false;
  bounce = false;
  flip = 1;
  constructor() {
    this.sp = new Sprite(Texture.EMPTY);
    this.sp.anchor.set(0.5);
    this.sp.visible = false;
  }
}

export class Particles {
  private pool: P[] = [];
  private live: P[] = [];
  max = 900;

  constructor(private readonly addLayer: Container, private readonly normalLayer: Container) {}

  get count(): number {
    return this.live.length;
  }

  emit(o: EmitOpts): void {
    if (this.live.length >= this.max) return;
    const p = this.pool.pop() ?? new P();
    const layer = o.add ? this.addLayer : this.normalLayer;
    if (p.sp.parent !== layer) layer.addChild(p.sp);
    p.alive = true;
    p.x = o.x; p.y = o.y; p.vx = o.vx ?? 0; p.vy = o.vy ?? 0;
    p.z = o.z ?? 0; p.vz = o.vz ?? 0; p.bounce = o.z !== undefined; p.flip = o.flip ? -1 : 1;
    p.life = 0; p.max = o.life;
    p.s0 = o.scale ?? 1; p.s1 = o.scaleEnd ?? p.s0;
    p.a0 = o.alpha ?? 1; p.a1 = o.alphaEnd ?? 0;
    p.rot = o.rot ?? 0; p.vr = o.vr ?? 0;
    p.grav = o.gravity ?? 0; p.drag = o.drag ?? 0;
    p.frames = o.frames ?? null;
    p.byLife = o.frameByLife ?? true;
    p.sp.texture = o.tex ?? (o.frames ? o.frames[0] : Texture.WHITE);
    p.sp.tint = o.tint ?? 0xffffff;
    p.sp.blendMode = o.add ? 'add' : 'normal';
    p.sp.visible = true;
    this.apply(p);
    this.live.push(p);
  }

  private apply(p: P): void {
    const t = p.life / p.max;
    const s = p.s0 + (p.s1 - p.s0) * t;
    p.sp.scale.set(s * p.flip, s);
    p.sp.alpha = p.a0 + (p.a1 - p.a0) * t;
    p.sp.rotation = p.rot;
    p.sp.position.set(Math.round(p.x), Math.round(p.y - p.z));
    if (p.frames) {
      const i = p.byLife ? Math.min(p.frames.length - 1, Math.floor(t * p.frames.length)) : Math.floor(p.life * 12) % p.frames.length;
      p.sp.texture = p.frames[i];
    }
  }

  update(dt: number): void {
    const live = this.live;
    for (let i = live.length - 1; i >= 0; i--) {
      const p = live[i];
      p.life += dt;
      if (p.life >= p.max) {
        p.alive = false;
        p.sp.visible = false;
        live[i] = live[live.length - 1];
        live.pop();
        this.pool.push(p);
        continue;
      }
      if (p.drag) {
        const k = Math.exp(-p.drag * dt);
        p.vx *= k;
        p.vy *= k;
      }
      p.vy += p.grav * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.rot += p.vr * dt;
      if (p.bounce) {
        p.vz -= 420 * dt;
        p.z += p.vz * dt;
        if (p.z < 0) {
          p.z = 0;
          p.vz = -p.vz * 0.35;
          p.vx *= 0.6;
          p.vy *= 0.6;
        }
      }
      this.apply(p);
    }
  }

  clear(): void {
    for (const p of this.live) {
      p.alive = false;
      p.sp.visible = false;
      this.pool.push(p);
    }
    this.live.length = 0;
  }
}
