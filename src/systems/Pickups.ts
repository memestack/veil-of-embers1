import { Sprite, Texture } from 'pixi.js';
import type { World } from '../game/World';
import { assets } from '../game/AssetLoader';
import { audio } from '../game/AudioManager';
import { rng } from '../utils/math';

export type PickupKind = 'xp_s' | 'xp_m' | 'xp_l' | 'heart' | 'energy' | 'coin' | 'essence' | 'chest';

class Pickup {
  sp = new Sprite(Texture.EMPTY);
  kind: PickupKind = 'xp_s';
  value = 1;
  x = 0;
  y = 0;
  vx = 0;
  vy = 0;
  t = 0;
  magnet = false;
  alive = false;
  pop = 0;
  constructor() {
    this.sp.anchor.set(0.5, 0.8);
  }
}

/** Pooled pickups with magnet, crystal merging when there are too many, and pickup effects. */
export class Pickups {
  private pool: Pickup[] = [];
  readonly live: Pickup[] = [];
  private frames: Record<string, Texture[]> = {};
  vacuum = false;
  private xpCount = 0;

  constructor(private readonly w: World) {
    for (const k of ['xp_s', 'xp_m', 'xp_l', 'heart', 'energy', 'coin', 'essence', 'chest']) this.frames[k] = assets.anim('fx', k);
  }

  spawn(kind: PickupKind, x: number, y: number, value: number): void {
    const isXp = kind.startsWith('xp');
    if (isXp && this.xpCount > 240) {
      // merge into the nearest crystal to keep readability and performance
      let best: Pickup | null = null;
      let bd = 60 * 60;
      for (const p of this.live) {
        if (!p.kind.startsWith('xp')) continue;
        const d = (p.x - x) ** 2 + (p.y - y) ** 2;
        if (d < bd) {
          bd = d;
          best = p;
        }
      }
      if (best) {
        best.value += value;
        if (best.value >= 12) best.kind = 'xp_l';
        else if (best.value >= 4) best.kind = 'xp_m';
        return;
      }
    }
    const p = this.pool.pop() ?? new Pickup();
    if (p.sp.parent !== this.w.pickupsLayer) this.w.pickupsLayer.addChild(p.sp);
    p.kind = kind;
    p.value = value;
    p.x = x;
    p.y = y;
    const a = rng.range(0, Math.PI * 2);
    const v = kind === 'chest' ? 0 : rng.range(20, 60);
    p.vx = Math.cos(a) * v;
    p.vy = Math.sin(a) * v;
    p.t = rng.range(0, 3);
    p.magnet = false;
    p.alive = true;
    p.pop = 0.25;
    p.sp.visible = true;
    p.sp.alpha = 1;
    this.live.push(p);
    if (isXp) this.xpCount++;
  }

  update(dt: number): void {
    const w = this.w;
    const h = w.hero;
    const R = w.stats.pickupRadius;
    for (let i = this.live.length - 1; i >= 0; i--) {
      const p = this.live[i];
      p.t += dt;
      p.pop = Math.max(0, p.pop - dt);
      const dx = h.x - p.x, dy = h.y - 8 - p.y;
      const d = Math.hypot(dx, dy);
      const isXp = p.kind.startsWith('xp');
      if (h.alive && (d < R || (this.vacuum && isXp) || (p.kind === 'chest' && d < 24))) p.magnet = true;
      if (p.magnet && h.alive) {
        const acc = 900;
        p.vx += (dx / (d || 1)) * acc * dt;
        p.vy += (dy / (d || 1)) * acc * dt;
        const sp = Math.hypot(p.vx, p.vy);
        const max = this.vacuum ? 520 : 340;
        if (sp > max) {
          p.vx *= max / sp;
          p.vy *= max / sp;
        }
        if (d < 10) {
          this.collect(p);
          this.live.splice(i, 1);
          continue;
        }
      } else {
        p.vx *= Math.exp(-6 * dt);
        p.vy *= Math.exp(-6 * dt);
      }
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      const fr = this.frames[p.kind];
      p.sp.texture = fr[Math.floor(p.t * 6) % fr.length];
      const bob = p.kind === 'chest' ? 0 : Math.sin(p.t * 4) * 1.5;
      p.sp.position.set(Math.round(p.x), Math.round(p.y + bob));
      p.sp.scale.set(1 + p.pop * 2);
    }
    if (this.vacuum && !this.live.some((p) => p.kind.startsWith('xp'))) this.vacuum = false;
  }

  private collect(p: Pickup): void {
    const w = this.w;
    const h = w.hero;
    p.alive = false;
    p.sp.visible = false;
    this.pool.push(p);
    switch (p.kind) {
      case 'xp_s':
      case 'xp_m':
      case 'xp_l':
        this.xpCount--;
        w.gainXp(p.value);
        audio.play('xp', { rate: 0.9 + Math.min(0.6, w.run.xp / 200) });
        w.particles.emit({ x: h.x, y: h.y - 14, life: 0.2, frames: assets.anim('fx', 'spark'), add: true, scale: 0.6, tint: 0xffe0a0 });
        break;
      case 'heart': {
        const heal = Math.round(w.stats.maxHp * p.value * 0.01);
        h.hp = Math.min(h.maxHp, h.hp + heal);
        w.numbers.show(h.x, h.y - 44, heal, 0x7aff9a, false, '+');
        w.fx.heal(h.x, h.y);
        audio.play('heal');
        break;
      }
      case 'energy':
        h.energy = Math.min(100, h.energy + p.value);
        w.fx.embers(h.x, h.y - 16, 6, 60);
        audio.play('fire', { rate: 1.4, gain: 0.6 });
        break;
      case 'coin':
      case 'essence':
        w.run.coins += p.value;
        audio.play('xp', { rate: 0.6 });
        w.numbers.show(h.x, h.y - 44, p.value, 0xffb84a, false, '+');
        break;
      case 'chest':
        w.run.pendingChest++;
        w.run.coins += 15;
        h.hp = Math.min(h.maxHp, h.hp + 30);
        w.fx.explosion(p.x, p.y - 8, 'fire', 0.8);
        audio.play('rare');
        break;
    }
  }

  clear(): void {
    for (const p of this.live) {
      p.alive = false;
      p.sp.visible = false;
      this.pool.push(p);
    }
    this.live.length = 0;
    this.xpCount = 0;
  }
}
