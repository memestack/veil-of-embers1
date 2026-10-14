/**
 * Authored bosses with telegraphed patterns and phases:
 *  - Colossal Batrach: leap with target shadow, shockwave, mud fan, summons; enrage at 50%.
 *  - Heart of the Veil: crystal arcs with gaps, spiral, coral roots in lines, pulsing rings.
 */
import { Sprite } from 'pixi.js';
import type { AiCtx } from './behaviors';
import { Enemy } from './Enemy';
import { BOSSES } from '../content/enemies';
import { assets } from '../game/AssetLoader';
import { audio } from '../game/AudioManager';
import { rng, TAU, clamp } from '../utils/math';

export interface Boss {
  e: Enemy;
  update(dt: number): void;
  destroy(): void;
}

function makeBoss(c: AiCtx, kind: 'frog' | 'heart', x: number, y: number): Enemy {
  const def = BOSSES[kind];
  const e = new Enemy(kind, def);
  e.x = x;
  e.y = y;
  e.maxHp = e.hp = Math.round(def.hp * c.w.hpMul);
  e.damage = def.damage;
  c.w.addEnemy(e);
  return e;
}

/** "Elliptical" distance on the floor plane (the ground is seen in 3/4). */
const groundDist = (ax: number, ay: number, bx: number, by: number) => Math.hypot(ax - bx, (ay - by) / 0.62);

// =======================================================================================
export class FrogBoss implements Boss {
  e: Enemy;
  private plan: string[] = [];
  private waves: { x: number; y: number; r: number; hit: boolean }[] = [];
  private sx = 0;
  private sy = 0;

  constructor(private readonly c: AiCtx, x: number, y: number) {
    this.e = makeBoss(c, 'frog', x, y);
    this.e.state = 'intro';
    this.e.z = 260;
    this.e.animName = 'batr_leap';
    audio.play('croak');
  }

  private get pre(): string {
    return this.e.phase === 2 ? 'batr2_' : 'batr_';
  }

  private go(s: string): void {
    this.e.state = s;
    this.e.stateT = 0;
  }

  private next(): void {
    if (!this.plan.length) this.plan = this.e.phase === 1 ? ['leap', 'spit', 'leap', 'summon'] : ['leap', 'leap', 'spit', 'leap', 'spit', 'summon'];
    const n = this.plan.shift()!;
    if (n === 'leap') this.startLeap();
    else if (n === 'spit') this.go('spit');
    else {
      this.go('summon');
      audio.play('croak', { rate: 1.2 });
      for (let i = 0; i < (this.e.phase === 1 ? 3 : 5); i++) {
        const a = rng.range(0, TAU);
        const [px, py] = this.c.w.arena.nearestFree(this.e.x + Math.cos(a) * 130, this.e.y + Math.sin(a) * 90);
        const s = this.c.spawn('sapo', px, py);
        if (s) this.c.w.fx.dust(px, py, 4);
      }
    }
  }

  private startLeap(): void {
    const w = this.c.w, h = w.hero;
    this.go('crouch');
    this.sx = this.e.x;
    this.sy = this.e.y;
    // target: the heroine's position (clamped to the free area)
    const [tx, ty] = w.arena.nearestFree(h.x, h.y);
    this.e.tx = tx;
    this.e.ty = ty;
    this.e.flip = tx < this.e.x;
    this.c.hazards.ring(tx, ty, 56, 1.4, () => undefined);
    audio.play('telegraph', { rate: 0.8 });
  }

  update(dt: number): void {
    const e = this.e, c = this.c, w = c.w, h = w.hero;
    if (e.dying) return;
    e.animT += dt;
    e.stateT += dt;
    e.flashT = Math.max(0, e.flashT - dt);
    const T = e.stateT;
    // enrage at 50%
    if (e.phase === 1 && e.hp < e.maxHp * 0.5 && e.state !== 'air' && e.state !== 'intro') {
      e.phase = 2;
      this.plan = [];
      this.go('roar');
      w.hooks.banner('The Batrach is enraged!', 'Its leaps grow faster');
      audio.play('croak', { rate: 0.85 });
      w.shake(0.6);
      w.screenFlash(0xff7a3a, 0.2);
    }
    switch (e.state) {
      case 'intro': {
        e.z = Math.max(0, 260 - T * 260);
        e.setAnim(this.pre + 'leap');
        if (e.z <= 0) this.land(1.2);
        break;
      }
      case 'idle':
        e.setAnim(this.pre + 'idle');
        e.flip = h.x < e.x;
        if (T > (e.phase === 1 ? 1.0 : 0.55)) this.next();
        break;
      case 'crouch':
        e.setAnim(this.pre + 'crouch');
        if (T > (e.phase === 1 ? 0.6 : 0.42)) this.go('air');
        break;
      case 'air': {
        const dur = e.phase === 1 ? 0.85 : 0.7;
        const k = clamp(T / dur, 0, 1);
        e.x = this.sx + (e.tx - this.sx) * k;
        e.y = this.sy + (e.ty - this.sy) * k;
        e.z = Math.sin(k * Math.PI) * 110;
        e.setAnim(this.pre + 'leap');
        if (k >= 1) this.land(1);
        break;
      }
      case 'land':
        e.setAnim(this.pre + 'land');
        if (T > 0.6) this.go('idle');
        break;
      case 'spit': {
        e.setAnim(this.pre + 'spit');
        e.flip = h.x < e.x;
        const shots = e.phase === 1 ? [0.35] : [0.3, 0.75];
        for (const s of shots) {
          if (T >= s && T - dt < s) {
            const n = e.phase === 1 ? 5 : 9;
            const spread = e.phase === 1 ? 1.1 : 1.6;
            const mx = e.x + (e.flip ? -60 : 60), my = e.y - 30;
            const base = Math.atan2(h.y - my, h.x - mx);
            for (let i = 0; i < n; i++) {
              const a = base + (i / (n - 1) - 0.5) * spread;
              c.hazards.shoot(assets.anim('fx', 'mudball'), mx, my, Math.cos(a) * 140, Math.sin(a) * 140, e.damage * 0.75, 7, 3.2, true, 'glow_fire');
            }
            audio.play('spit');
          }
        }
        if (T > (e.phase === 1 ? 0.9 : 1.2)) this.go('idle');
        break;
      }
      case 'summon':
        e.setAnim(this.pre + 'idle');
        if (T > 0.9) this.go('idle');
        break;
      case 'roar':
        e.setAnim('batr2_spit');
        if (T > 1.2) this.go('idle');
        break;
    }
    // expanding shockwaves
    for (let i = this.waves.length - 1; i >= 0; i--) {
      const wv = this.waves[i];
      wv.r += 175 * dt;
      if (!wv.hit && h.alive && !h.invulnerable) {
        const d = groundDist(h.x, h.y, wv.x, wv.y);
        if (Math.abs(d - wv.r) < 10) {
          wv.hit = true;
          c.combat.hurtHero(e.damage * 0.8, wv.x, wv.y);
        }
      }
      if (wv.r > 230) this.waves.splice(i, 1);
    }
    // body: contact only while grounded
    if (e.z < 10 && h.alive && groundDist(h.x, h.y, e.x, e.y) < e.radius + 6) c.combat.hurtHero(e.damage, e.x, e.y);
    if (e.z < 10) w.arena.resolve(e, 20, false);
    e.sync(e.state === 'idle' ? 6 : 10);
    w.hooks.bossBar(e.def.name, Math.max(0, e.hp / e.maxHp));
  }

  private land(power: number): void {
    const e = this.e, c = this.c, w = c.w, h = w.hero;
    e.z = 0;
    this.go('land');
    w.shake(0.7 * power);
    w.freeze(0.06);
    audio.play('slam');
    w.fx.dust(e.x, e.y, 12, 2.2);
    w.fx.shockwave(e.x, e.y, 1.4, true);
    if (h.alive && groundDist(h.x, h.y, e.x, e.y) < 58) c.combat.hurtHero(e.damage * 1.3, e.x, e.y);
    this.waves.push({ x: e.x, y: e.y, r: 30, hit: false });
    // the visual wave follows the hitbox
    for (let k = 0; k < 3; k++)
      w.particles.emit({ x: e.x, y: e.y, life: 1.15, frames: assets.anim('fx', 'boss_wave'), frameByLife: false, scale: 0.6 + k * 0.05, scaleEnd: 4.2 + k * 0.05, alpha: 0.9, alphaEnd: 0.1, add: true });
  }

  destroy(): void {
    this.waves.length = 0;
  }
}

// =======================================================================================
interface Root {
  segs: Sprite[];
  ax: number;
  ay: number;
  bx: number;
  by: number;
  t: number;
}

export class HeartBoss implements Boss {
  e: Enemy;
  private plan: string[] = [];
  private roots: Root[] = [];
  private spiralA = 0;
  private glow: Sprite;

  constructor(private readonly c: AiCtx, x: number, y: number) {
    this.e = makeBoss(c, 'heart', x, y);
    this.e.state = 'intro';
    this.e.animName = 'heart1_pulse';
    this.e.root.alpha = 0;
    this.glow = new Sprite(assets.tex('fx', 'glow_danger'));
    this.glow.anchor.set(0.5);
    this.glow.blendMode = 'add';
    this.glow.scale.set(3.2);
    this.glow.alpha = 0;
    c.w.lights.addChild(this.glow);
    audio.play('anchor', { rate: 0.6 });
  }

  private go(s: string): void {
    this.e.state = s;
    this.e.stateT = 0;
  }

  private get core(): [number, number] {
    return [this.e.x, this.e.y - 52];
  }

  private next(): void {
    const p = this.e.phase;
    if (!this.plan.length)
      this.plan = p === 1 ? ['arcs', 'rest', 'spiral', 'rest'] : p === 2 ? ['arcs', 'roots', 'rest', 'spiral', 'roots', 'summon', 'rest'] : ['pulse', 'roots', 'spiral', 'rest', 'arcs', 'pulse', 'roots', 'summon', 'rest'];
    const n = this.plan.shift()!;
    this.go(n);
    if (n === 'roots') this.castRoots();
    if (n === 'summon') {
      audio.play('summon', { rate: 0.7 });
      for (let i = 0; i < 6; i++) {
        const [px, py] = this.c.w.arena.nearestFree(this.e.x + rng.range(-260, 260), this.e.y + rng.range(40, 130));
        this.c.hazards.ring(px, py, 12, 0.8, () => {
          this.c.spawn(rng.chance(0.5) ? 'ferr' : 'suss', px, py);
        });
      }
    }
    if (n === 'pulse') {
      audio.play('telegraph', { rate: 0.7 });
      this.c.w.hooks.banner('The Heart is about to pulse', 'Slip through the gap or dash');
    }
  }

  private ring(n: number, speed: number, gap: number, gapAt: number, tex = 'crystal_shard'): void {
    const [cx, cy] = this.core;
    for (let i = 0; i < n; i++) {
      const k = (i - gapAt + n) % n;
      if (k < gap) continue;
      const a = (i / n) * TAU;
      this.c.hazards.shoot(assets.anim('fx', tex), cx, cy, Math.cos(a) * speed, Math.sin(a) * speed * 0.8, this.e.damage * 0.7, 5, 6);
    }
  }

  private castRoots(): void {
    const w = this.c.w, h = w.hero;
    const base = Math.atan2(h.y - this.e.y, h.x - this.e.x);
    const offs = this.e.phase === 3 ? [-0.55, -0.18, 0.18, 0.55] : [-0.4, 0, 0.4];
    audio.play('telegraph');
    for (const o of offs) {
      const a = base + o;
      const L = 420;
      const ax = this.e.x + Math.cos(a) * 40, ay = this.e.y + Math.sin(a) * 26;
      this.c.hazards.line(ax, ay, a, L, 22, 1.1, () => {
        const segs: Sprite[] = [];
        const n = Math.floor(L / 16);
        for (let i = 0; i < n; i++) {
          const x = ax + Math.cos(a) * i * 16, y = ay + Math.sin(a) * i * 16;
          if (w.arena.isSolidAt(x, y)) break;
          const s = new Sprite(i === n - 1 ? assets.tex('boss_heart', 'tentacle_tip') : assets.anim('boss_heart', 'tentacle_seg')[i % 4]);
          s.anchor.set(0.5, 0.7);
          s.position.set(x, y);
          s.rotation = i === n - 1 ? a : 0;
          s.zIndex = y;
          s.scale.set(0);
          w.actors.addChild(s);
          segs.push(s);
        }
        const last = segs.length ? segs[segs.length - 1] : null;
        this.roots.push({ segs, ax, ay, bx: last ? last.x : ax, by: last ? last.y : ay, t: 0 });
        audio.play('slam', { rate: 1.4, gain: 0.5 });
        w.shake(0.2);
      });
    }
  }

  update(dt: number): void {
    const e = this.e, c = this.c, w = c.w, h = w.hero;
    if (e.dying) {
      this.glow.alpha = Math.max(0, this.glow.alpha - dt);
      for (const r of this.roots) for (const s of r.segs) s.destroy();
      this.roots.length = 0;
      return;
    }
    e.animT += dt;
    e.stateT += dt;
    e.flashT = Math.max(0, e.flashT - dt);
    const T = e.stateT;
    // fases
    const frac = e.hp / e.maxHp;
    const want = frac > 0.66 ? 1 : frac > 0.33 ? 2 : 3;
    if (want > e.phase && e.state !== 'intro') {
      e.phase = want;
      this.plan = [];
      this.go('shift');
      w.fx.crystal(e.x, e.y - 50, 2.2);
      w.fx.explosion(e.x, e.y - 50, 'fire', 1.6);
      w.shake(0.7);
      w.screenFlash(0xff5a8a, 0.25);
      audio.play('glass', { rate: 0.6 });
      w.hooks.banner(want === 2 ? 'The shell cracks' : 'The core is exposed', want === 2 ? 'Coral roots slash across the arena' : 'The Veil\'s last breath');
    }
    e.setAnim(`heart${e.phase}_pulse`);
    const [cx, cy] = this.core;
    this.glow.position.set(cx, cy);
    this.glow.alpha = (0.25 + 0.15 * Math.sin(w.time * 6)) * e.root.alpha;
    switch (e.state) {
      case 'intro':
        e.root.alpha = Math.min(1, T / 1.6);
        if (T > 2.0) {
          this.go('rest');
          w.shake(0.5);
        }
        break;
      case 'rest':
        if (T > (e.phase === 3 ? 0.9 : 1.4)) this.next();
        break;
      case 'shift':
        if (T > 1.6) this.next();
        break;
      case 'arcs': {
        const n = e.phase === 1 ? 3 : 4;
        for (let k = 0; k < n; k++) {
          const at = 0.2 + k * 0.62;
          if (T >= at && T - dt < at) {
            this.ring(e.phase === 3 ? 30 : 24, 95 + e.phase * 8, 4, Math.floor(rng.range(0, 24)));
            audio.play('glass', { rate: 1.3, gain: 0.6 });
          }
        }
        if (T > 0.3 + n * 0.62) this.go('rest');
        break;
      }
      case 'spiral': {
        e.mem.st = (e.mem.st ?? 0) + dt;
        const step = e.phase === 3 ? 0.07 : 0.1;
        while (e.mem.st >= step) {
          e.mem.st -= step;
          this.spiralA += 0.33;
          const arms = e.phase === 1 ? 2 : 3;
          for (let k = 0; k < arms; k++) {
            const a = this.spiralA + (k / arms) * TAU;
            c.hazards.shoot(assets.anim('fx', 'orb_danger'), cx, cy, Math.cos(a) * 92, Math.sin(a) * 92 * 0.8, e.damage * 0.6, 5, 6, false, 'glow_danger');
          }
        }
        if (T > 2.6) this.go('rest');
        break;
      }
      case 'roots':
        if (T > 2.4) this.go('rest');
        break;
      case 'summon':
        if (T > 1.0) this.go('rest');
        break;
      case 'pulse': {
        for (let k = 0; k < 3; k++) {
          const at = 0.7 + k * 0.9;
          if (T >= at && T - dt < at) {
            this.ring(56, 120, 6, Math.floor(rng.range(0, 56)), 'orb_danger');
            w.fx.shockwave(cx, cy, 1.6);
            audio.play('pulse', { rate: 0.8 });
            w.shake(0.25);
          }
        }
        if (T > 3.4) this.go('rest');
        break;
      }
    }
    // active roots: grow, hurt and retract
    for (let i = this.roots.length - 1; i >= 0; i--) {
      const r = this.roots[i];
      r.t += dt;
      const s = r.t < 0.15 ? r.t / 0.15 : r.t > 1.1 ? Math.max(0, 1 - (r.t - 1.1) / 0.25) : 1;
      for (const sp of r.segs) sp.scale.set(s);
      if (s > 0.6 && h.alive) {
        // point-segment distance
        const vx = r.bx - r.ax, vy = r.by - r.ay;
        const l2 = vx * vx + vy * vy || 1;
        const t = clamp(((h.x - r.ax) * vx + (h.y - r.ay) * vy) / l2, 0, 1);
        const d = Math.hypot(h.x - (r.ax + vx * t), h.y - (r.ay + vy * t));
        if (d < 14) c.combat.hurtHero(e.damage, h.x - vx, h.y - vy);
      }
      if (r.t > 1.4) {
        for (const sp of r.segs) sp.destroy();
        this.roots.splice(i, 1);
      }
    }
    if (h.alive && groundDist(h.x, h.y, e.x, e.y) < 46) c.combat.hurtHero(e.damage, e.x, e.y);
    e.sync(8 + e.phase * 2);
    w.hooks.bossBar(e.def.name, Math.max(0, e.hp / e.maxHp));
  }

  destroy(): void {
    for (const r of this.roots) for (const s of r.segs) s.destroy();
    this.roots.length = 0;
    this.glow.destroy();
  }
}
