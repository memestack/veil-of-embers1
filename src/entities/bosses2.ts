/**
 * Second set of bosses:
 *  - The Ash Wyrm: segmented serpent (head + 10 armoured segments + tail). Slithers after the archer,
 *    breathes a telegraphed cone of fire, burrows and resurfaces under one of three marked mounds.
 *    At half health it enrages and calls lightning down on marked circles.
 *  - The Glass Colossus: slow giant. Telegraphed fist slams that shatter into crystal shards,
 *    crystal rain on marked circles, summons golems when enraged.
 */
import { Sprite, Texture } from 'pixi.js';
import type { AiCtx } from './behaviors';
import type { Boss } from './bosses';
import { Enemy } from './Enemy';
import { BOSSES } from '../content/enemies';
import { assets } from '../game/AssetLoader';
import { audio } from '../game/AudioManager';
import { rng, TAU, dir8, angleDiff, clamp } from '../utils/math';

const groundDist = (ax: number, ay: number, bx: number, by: number) => Math.hypot(ax - bx, (ay - by) / 0.62);

function makeCore(c: AiCtx, kind: 'wyrm' | 'colossus', x: number, y: number): Enemy {
  const def = BOSSES[kind];
  const e = new Enemy(kind, def);
  e.x = x;
  e.y = y;
  e.maxHp = e.hp = Math.round(def.hp * c.w.hpMul);
  e.damage = def.damage;
  c.w.addEnemy(e);
  return e;
}

// =======================================================================================
export class WyrmBoss implements Boss {
  e: Enemy;
  private parts: Enemy[] = [];
  private trail: { x: number; y: number }[] = [];
  private heading = 0;
  private plan: string[] = [];
  private mounds: { x: number; y: number; real: boolean; at: number; done: boolean }[] = [];
  private head: Sprite;
  private tex: Record<string, Texture[]> = {};
  private boltT = 0;
  private readonly SEG = 10;
  private readonly GAP = 5;

  constructor(private readonly c: AiCtx, x: number, y: number) {
    this.e = makeCore(c, 'wyrm', x, y);
    for (const [k, v] of Object.entries(assets.sheet('boss_wyrm').animations)) this.tex[k] = v;
    // the head is drawn by the core entity itself
    this.head = this.e.sprite;
    this.head.anchor.set(0.5);
    for (let i = 0; i <= this.SEG; i++) {
      const p = new Enemy('wyrm', { ...BOSSES.wyrm, radius: i === this.SEG ? 8 : 12, shadow: 'shadow_l' });
      p.owner = this.e;
      p.x = x;
      p.y = y;
      p.sprite.anchor.set(0.5);
      c.w.addEnemy(p);
      this.parts.push(p);
    }
    for (let i = 0; i < (this.SEG + 2) * this.GAP; i++) this.trail.push({ x, y: y + i * 3 });
    this.heading = -Math.PI / 2;
    this.e.state = 'emerge';
    audio.play('slam', { rate: 0.6 });
    c.w.fx.dust(x, y, 14, 2);
    c.w.shake(0.6);
  }

  private get pre(): string {
    return this.e.phase === 2 ? 'wyrm2' : 'wyrm';
  }

  private go(s: string): void {
    this.e.state = s;
    this.e.stateT = 0;
  }

  private next(): void {
    if (!this.plan.length) this.plan = this.e.phase === 1 ? ['chase', 'breath', 'chase', 'burrow'] : ['chase', 'burrow', 'breath', 'chase', 'breath', 'burrow'];
    const n = this.plan.shift()!;
    this.go(n);
    if (n === 'breath') {
      audio.play('telegraph', { rate: 0.8 });
      this.c.hazards.cone(this.e.x, this.e.y, this.heading, 130, 0.9, () => undefined);
    }
    if (n === 'burrow') {
      audio.play('slam', { rate: 0.7, gain: 0.7 });
      this.c.w.hooks.banner('The Wyrm burrows', 'One of the mounds is real');
    }
  }

  private setVisible(v: boolean): void {
    this.e.root.visible = v;
    this.e.shadow.visible = v;
    for (const p of this.parts) {
      p.root.visible = v;
      p.shadow.visible = v;
    }
  }

  /** Moves the head and drags the body along the trail. */
  private slither(dt: number, speed: number, turn: number, tx: number, ty: number): void {
    const e = this.e, w = this.c.w;
    const want = Math.atan2(ty - e.y, tx - e.x);
    this.heading += clamp(angleDiff(this.heading, want), -turn * dt, turn * dt);
    const nx = e.x + Math.cos(this.heading) * speed * dt;
    const ny = e.y + Math.sin(this.heading) * speed * dt;
    if (w.arena.isSolidAt(nx, ny)) this.heading += 2.4 * dt * 8;
    else {
      e.x = nx;
      e.y = ny;
    }
    const last = this.trail[0];
    if (Math.hypot(e.x - last.x, e.y - last.y) > 3) {
      this.trail.unshift({ x: e.x, y: e.y });
      if (this.trail.length > (this.SEG + 2) * this.GAP + 4) this.trail.pop();
    }
  }

  private placeBody(): void {
    const w = this.c.w;
    const head = this.tex[`${this.pre}_head_d${dir8(this.heading)}`];
    this.head.texture = head[this.e.state === 'breath' && this.e.stateT > 0.6 ? 1 : 0];
    this.e.root.position.set(Math.round(this.e.x), Math.round(this.e.y - 6));
    this.e.root.zIndex = this.e.y + 1;
    this.e.shadow.position.set(Math.round(this.e.x), Math.round(this.e.y + 6));
    this.e.root.scale.x = 1;
    this.head.tint = this.e.flashT > 0 ? 0xff9a9a : 0xffffff;
    for (let i = 0; i < this.parts.length; i++) {
      const p = this.parts[i];
      const t = this.trail[Math.min(this.trail.length - 1, (i + 1) * this.GAP)];
      p.x = t.x;
      p.y = t.y;
      const tail = i === this.parts.length - 1;
      if (tail) {
        const prev = this.trail[Math.min(this.trail.length - 1, i * this.GAP)];
        p.sprite.texture = this.tex[`wyrm_tail_d${dir8(Math.atan2(prev.y - t.y, prev.x - t.x))}`][0];
      } else {
        p.sprite.texture = this.tex[`${this.pre}_seg`][Math.min(3, Math.floor(i / 3))];
      }
      const wob = Math.sin(w.time * 6 - i * 0.7) * 1.2;
      p.root.position.set(Math.round(p.x), Math.round(p.y - 6 + wob));
      p.root.zIndex = p.y;
      p.shadow.position.set(Math.round(p.x), Math.round(p.y + 5));
      p.sprite.tint = this.e.flashT > 0 ? 0xff9a9a : 0xffffff;
    }
  }

  update(dt: number): void {
    const e = this.e, c = this.c, w = c.w, h = w.hero;
    if (e.dying) {
      for (const p of this.parts) if (!p.dying) {
        p.dying = true;
        p.dieT = 0;
      }
      return;
    }
    e.stateT += dt;
    e.flashT = Math.max(0, e.flashT - dt);
    const T = e.stateT;
    if (e.phase === 1 && e.hp < e.maxHp * 0.5 && e.state === 'chase') {
      e.phase = 2;
      this.plan = [];
      w.hooks.banner('The Wyrm is ablaze!', 'Lightning answers its call');
      audio.play('croak', { rate: 1.4 });
      w.shake(0.5);
      w.screenFlash(0xff7a3a, 0.2);
    }
    const speed = e.phase === 1 ? 105 : 140;
    switch (e.state) {
      case 'emerge':
        this.slither(dt, 60, 2, h.x, h.y);
        if (T > 1.2) this.next();
        break;
      case 'chase':
        this.slither(dt, speed, e.phase === 1 ? 2.0 : 2.6, h.x, h.y);
        if (e.phase === 2) {
          this.boltT -= dt;
          if (this.boltT <= 0) {
            this.boltT = 1.6;
            for (let k = 0; k < 3; k++) {
              const [bx, by] = w.arena.nearestFree(h.x + rng.range(-70, 70), h.y + rng.range(-50, 50));
              c.hazards.ring(bx, by, 22, 0.9 + k * 0.15, () => {
                w.fx.skyBolt(bx, by);
                audio.play('thunder', { rate: 0.8 });
                if (groundDist(h.x, h.y, bx, by) < 24) c.combat.hurtHero(e.damage, bx, by);
              });
            }
          }
        }
        if (T > 4.2) this.next();
        break;
      case 'breath': {
        this.slither(dt, 0.01, 0.6, h.x, h.y);
        if (T >= 0.9 && T - dt < 0.9) {
          audio.play('fire', { rate: 0.6 });
          audio.play('lance', { rate: 0.7 });
          w.shake(0.3);
          for (let k = 0; k < 7; k++) {
            const a = this.heading + (k - 3) * 0.16;
            const d = 40 + (k % 3) * 28;
            c.hazards.fire(e.x + Math.cos(a) * d, e.y + Math.sin(a) * d * 0.8, 4, 7, 14);
          }
          for (let k = 0; k < 10; k++) {
            const a = this.heading + rng.range(-0.5, 0.5);
            w.particles.emit({ x: e.x, y: e.y - 6, vx: Math.cos(a) * rng.range(140, 240), vy: Math.sin(a) * rng.range(140, 240), drag: 3,
              life: 0.6, frames: assets.anim('fx', 'explosion'), scale: 0.6, scaleEnd: 1.2, add: true });
          }
          w.flashLight(e.x + Math.cos(this.heading) * 60, e.y + Math.sin(this.heading) * 60, 180, 1, 0xff8a3a, 0.6);
          const ha = Math.atan2(h.y - e.y, h.x - e.x);
          if (Math.hypot(h.x - e.x, h.y - e.y) < 130 && Math.abs(angleDiff(this.heading, ha)) < Math.PI / 6 + 0.05) c.combat.hurtHero(e.damage * 1.2, e.x, e.y);
        }
        if (T > 1.6) this.next();
        break;
      }
      case 'burrow': {
        // dives: the body disappears front to back
        if (T < 0.8) this.slither(dt, 50, 1, e.x + Math.cos(this.heading) * 10, e.y + Math.sin(this.heading) * 10 + 20);
        if (T >= 0.8 && T - dt < 0.8) {
          this.setVisible(false);
          w.fx.dust(e.x, e.y, 10, 1.6);
          const realIdx = rng.int(0, 2);
          this.mounds = [];
          for (let k = 0; k < 3; k++) {
            const [mx, my] = w.arena.nearestFree(h.x + rng.range(-110, 110), h.y + rng.range(-80, 80));
            this.mounds.push({ x: mx, y: my, real: k === realIdx, at: 1.0 + k * 0.55, done: false });
          }
          for (const p of this.parts) p.x = p.y = -9999;
          e.x = e.y = -9999;
        }
        for (const m of this.mounds) {
          if (!m.done && T >= m.at) {
            m.done = true;
            w.particles.emit({ x: m.x, y: m.y, life: 1.1, frames: this.tex['wyrm_mound'], frameByLife: true, alpha: 1, alphaEnd: 0.6 });
            c.hazards.ring(m.x, m.y, 44, 1.1, () => {
              w.fx.dust(m.x, m.y, 8, 1.2);
              w.shake(m.real ? 0.6 : 0.2);
              audio.play('slam', { rate: m.real ? 0.8 : 1.3, gain: m.real ? 1 : 0.4 });
              if (!m.real) return;
              w.fx.explosion(m.x, m.y - 8, 'fire', 1.4);
              w.fx.shockwave(m.x, m.y, 1.3, true);
              if (groundDist(h.x, h.y, m.x, m.y) < 46) c.combat.hurtHero(e.damage * 1.3, m.x, m.y);
              e.x = m.x;
              e.y = m.y;
              this.trail = [];
              for (let i = 0; i < (this.SEG + 2) * this.GAP; i++) this.trail.push({ x: m.x, y: m.y + i * 0.5 });
              this.heading = Math.atan2(h.y - m.y, h.x - m.x);
              this.setVisible(true);
              this.go('emerge');
            });
          }
        }
        break;
      }
    }
    if (e.root.visible) {
      this.placeBody();
      // contact with head and body
      if (h.alive) {
        if (Math.hypot(h.x - e.x, h.y - e.y) < 20) c.combat.hurtHero(e.damage, e.x, e.y);
        else for (const p of this.parts) if (Math.hypot(h.x - p.x, h.y - p.y) < p.radius + 6) {
          c.combat.hurtHero(e.damage * 0.7, p.x, p.y);
          break;
        }
      }
    }
    w.hooks.bossBar(e.def.name, Math.max(0, e.hp / e.maxHp));
  }

  destroy(): void {
    this.mounds.length = 0;
  }
}

// =======================================================================================
export class ColossusBoss implements Boss {
  e: Enemy;
  private plan: string[] = [];
  private fists: [number, number][] = [];

  constructor(private readonly c: AiCtx, x: number, y: number) {
    this.e = makeCore(c, 'colossus', x, y);
    this.e.state = 'intro';
    this.e.animName = 'col_roar';
    audio.play('slam', { rate: 0.5 });
    c.w.shake(0.7);
  }

  private get pre(): string {
    return this.e.phase === 2 ? 'col2_' : 'col_';
  }

  private go(s: string): void {
    this.e.state = s;
    this.e.stateT = 0;
  }

  private next(): void {
    if (!this.plan.length) this.plan = this.e.phase === 1 ? ['walk', 'slam', 'walk', 'rain'] : ['slam', 'rain', 'walk', 'slam', 'summon', 'rain'];
    const n = this.plan.shift()!;
    this.go(n);
    const w = this.c.w, h = w.hero, e = this.e;
    if (n === 'slam') {
      e.flip = h.x < e.x;
      this.fists = [[e.x - 46, e.y + 6], [e.x + 46, e.y + 6], [e.x + (h.x - e.x) * 0.5, e.y + (h.y - e.y) * 0.5]];
      for (const [fx, fy] of this.fists) this.c.hazards.ring(fx, fy, 40, 1.0, () => undefined);
      audio.play('telegraph', { rate: 0.7 });
    }
    if (n === 'rain') {
      audio.play('croak', { rate: 1.8, gain: 0.6 });
      const count = e.phase === 1 ? 8 : 14;
      for (let k = 0; k < count; k++) {
        const [rx, ry] = w.arena.nearestFree(h.x + rng.range(-120, 120), h.y + rng.range(-80, 80));
        const delay = 1.0 + k * 0.08;
        this.c.hazards.ring(rx, ry, 18, delay, () => {
          w.fx.crystal(rx, ry - 4, 0.8);
          audio.play('glass', { rate: 1.2 + rng.range(0, 0.4), gain: 0.5 });
          if (groundDist(h.x, h.y, rx, ry) < 20) this.c.combat.hurtHero(e.damage * 0.8, rx, ry);
        });
        w.particles.emit({ x: rx, y: ry - 160, vy: 160 / delay, life: delay, tex: assets.tex('fx', 'falling_shard'), alpha: 1, alphaEnd: 1 });
      }
    }
    if (n === 'summon') {
      for (let k = 0; k < 2; k++) {
        const [sx, sy] = w.arena.nearestFree(e.x + (k ? 90 : -90), e.y + 40);
        this.c.hazards.ring(sx, sy, 20, 0.9, () => this.c.spawn('golem', sx, sy));
      }
    }
  }

  update(dt: number): void {
    const e = this.e, c = this.c, w = c.w, h = w.hero;
    if (e.dying) return;
    e.animT += dt;
    e.stateT += dt;
    e.flashT = Math.max(0, e.flashT - dt);
    const T = e.stateT;
    if (e.phase === 1 && e.hp < e.maxHp * 0.5 && e.state !== 'slam') {
      e.phase = 2;
      this.plan = [];
      this.go('roar');
      w.hooks.banner('The Colossus cracks!', 'Its core burns red');
      audio.play('glass', { rate: 0.5 });
      w.shake(0.7);
      w.screenFlash(0xff5aa0, 0.25);
    }
    switch (e.state) {
      case 'intro':
      case 'roar':
        e.setAnim(this.pre + 'roar');
        if (T > 1.4) this.next();
        break;
      case 'walk': {
        const dx = h.x - e.x, dy = h.y - e.y;
        const d = Math.hypot(dx, dy) || 1;
        e.x += (dx / d) * e.def.speed * (e.phase === 2 ? 1.5 : 1) * dt;
        e.y += (dy / d) * e.def.speed * (e.phase === 2 ? 1.5 : 1) * dt;
        e.flip = dx < 0;
        w.arena.resolve(e, 26, false);
        e.setAnim(this.pre + 'idle');
        if (T > (e.phase === 1 ? 2.6 : 1.6)) this.next();
        break;
      }
      case 'slam':
        e.setAnim(this.pre + (T < 1.0 ? 'raise' : 'slam'));
        if (T >= 1.0 && T - dt < 1.0) {
          w.shake(0.8);
          w.freeze(0.06);
          audio.play('slam');
          for (const [fx, fy] of this.fists) {
            w.fx.shockwave(fx, fy, 1.1, true);
            w.fx.crystal(fx, fy - 6, 1.4);
            w.fx.dust(fx, fy, 8, 1.4);
            if (groundDist(h.x, h.y, fx, fy) < 42) c.combat.hurtHero(e.damage * 1.2, fx, fy);
            const n = e.phase === 1 ? 6 : 10;
            for (let k = 0; k < n; k++) {
              const a = (k / n) * TAU + rng.range(0, 0.3);
              c.hazards.shoot(assets.anim('fx', 'crystal_shard'), fx, fy - 6, Math.cos(a) * 120, Math.sin(a) * 96, e.damage * 0.6, 5, 2.4, false, 'glow_ice');
            }
          }
        }
        if (T > 1.7) this.next();
        break;
      case 'rain':
      case 'summon':
        e.setAnim(this.pre + 'roar');
        if (T > 1.6) this.next();
        break;
    }
    if (h.alive && groundDist(h.x, h.y, e.x, e.y) < e.radius + 6) c.combat.hurtHero(e.damage, e.x, e.y);
    e.sync(e.state === 'walk' ? 5 : 8);
    w.hooks.bossBar(e.def.name, Math.max(0, e.hp / e.maxHp));
  }

  destroy(): void {
    this.fists.length = 0;
  }
}
