import { Sprite, Texture, TilingSprite } from 'pixi.js';
import type { World } from '../game/World';
import type { Combat } from './Combat';
import { assets } from '../game/AssetLoader';

/** Textured floor warnings (ring, cone, line) that precede heavy attacks. */
interface Tele {
  sp: Sprite | TilingSprite;
  t: number;
  dur: number;
  done: () => void;
  baseAlpha: number;
}

/** Readable enemy projectiles (slow enough to react to). */
interface Shot {
  sp: Sprite;
  frames: Texture[];
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  dmg: number;
  life: number;
  t: number;
  spin: boolean;
  glow: Sprite | null;
}

/** Burning ground: hurts the heroine while she stands in it. */
interface Fire {
  sp: Sprite;
  x: number;
  y: number;
  r: number;
  t: number;
  life: number;
  dmg: number;
  tick: number;
}

export class Hazards {
  private fires: Fire[] = [];
  private teles: Tele[] = [];
  private shots: Shot[] = [];
  private shotPool: Shot[] = [];
  combat!: Combat;
  maxShots = 160;

  constructor(private readonly w: World) {}

  get shotCount(): number {
    return this.shots.length;
  }

  ring(x: number, y: number, radius: number, dur: number, done: () => void): void {
    const s = new Sprite(assets.tex('fx', 'tele_ring'));
    s.anchor.set(0.5);
    s.position.set(x, y);
    s.scale.set(radius / 47.5, (radius / 47.5) * 0.62);
    this.add(s, dur, done);
  }

  cone(x: number, y: number, angle: number, length: number, dur: number, done: () => void): Sprite {
    const s = new Sprite(assets.tex('fx', 'tele_cone'));
    s.anchor.set(0, 0.5);
    s.position.set(x, y);
    s.rotation = angle;
    s.scale.set(length / 94);
    this.add(s, dur, done);
    return s;
  }

  line(x: number, y: number, angle: number, length: number, width: number, dur: number, done: () => void): TilingSprite {
    const s = new TilingSprite({ texture: assets.tex('fx', 'tele_line'), width: Math.max(8, length), height: 16 });
    s.anchor.set(0, 0.5);
    s.position.set(x, y);
    s.rotation = angle;
    s.scale.y = width / 12;
    this.add(s, dur, done);
    return s;
  }

  private add(sp: Sprite | TilingSprite, dur: number, done: () => void): void {
    this.w.decals.addChild(sp);
    sp.alpha = 0;
    this.teles.push({ sp, t: 0, dur, done, baseAlpha: 0.9 });
  }

  shoot(frames: Texture[], x: number, y: number, vx: number, vy: number, dmg: number, r = 5, life = 4, spin = false, glowTex?: string): void {
    if (this.shots.length >= this.maxShots) return;
    const s: Shot = this.shotPool.pop() ?? { sp: new Sprite(Texture.EMPTY), frames, x: 0, y: 0, vx: 0, vy: 0, r, dmg, life, t: 0, spin, glow: null };
    s.frames = frames;
    s.x = x; s.y = y; s.vx = vx; s.vy = vy; s.r = r; s.dmg = dmg; s.life = life; s.t = 0; s.spin = spin;
    s.sp.texture = frames[0];
    s.sp.anchor.set(0.5);
    s.sp.visible = true;
    s.sp.rotation = spin ? 0 : Math.atan2(vy, vx);
    if (s.sp.parent !== this.w.projectiles) this.w.projectiles.addChild(s.sp);
    if (glowTex) {
      if (!s.glow) {
        s.glow = new Sprite(assets.tex('fx', glowTex));
        s.glow.anchor.set(0.5);
        s.glow.blendMode = 'add';
      } else s.glow.texture = assets.tex('fx', glowTex);
      s.glow.scale.set(0.45);
      s.glow.alpha = 0.55;
      s.glow.visible = true;
      if (s.glow.parent !== this.w.lights) this.w.lights.addChild(s.glow);
    } else if (s.glow) s.glow.visible = false;
    this.shots.push(s);
  }

  /** Fire patch on the floor (hostile). */
  fire(x: number, y: number, life = 3, dmg = 6, r = 14): void {
    if (this.fires.length > 60) return;
    const sp = new Sprite(assets.tex('fx', 'ground_fire'));
    sp.anchor.set(0.5);
    sp.blendMode = 'add';
    sp.position.set(x, y);
    sp.scale.set(r / 16);
    this.w.decals.addChild(sp);
    this.fires.push({ sp, x, y, r, t: 0, life, dmg, tick: 0.4 });
  }

  update(dt: number): void {
    const w = this.w;
    const fr = assets.anim('fx', 'ground_fire');
    for (let i = this.fires.length - 1; i >= 0; i--) {
      const f = this.fires[i];
      f.t += dt;
      f.tick -= dt;
      f.sp.texture = fr[Math.floor((f.t + f.x * 0.01) * 10) % fr.length];
      f.sp.alpha = f.t < 0.2 ? f.t / 0.2 : f.t > f.life - 0.5 ? Math.max(0, (f.life - f.t) / 0.5) : 1;
      if (f.tick <= 0) {
        f.tick = 0.5;
        if (Math.hypot(w.hero.x - f.x, (w.hero.y - f.y) / 0.62) < f.r + 4) this.combat.hurtHero(f.dmg, f.x, f.y);
        if (Math.random() < 0.6) w.fx.embers(f.x, f.y - 4, 1, 30);
      }
      if (f.t >= f.life) {
        f.sp.destroy();
        this.fires.splice(i, 1);
      }
    }
    for (let i = this.teles.length - 1; i >= 0; i--) {
      const t = this.teles[i];
      t.t += dt;
      const k = t.t / t.dur;
      const blink = k > 0.7 ? 0.65 + 0.35 * Math.abs(Math.sin(t.t * 22)) : 1;
      t.sp.alpha = Math.min(1, k * 4) * t.baseAlpha * blink;
      if (t.t >= t.dur) {
        t.sp.destroy();
        this.teles.splice(i, 1);
        t.done();
      }
    }
    const h = w.hero;
    for (let i = this.shots.length - 1; i >= 0; i--) {
      const s = this.shots[i];
      s.t += dt;
      s.x += s.vx * dt;
      s.y += s.vy * dt;
      let dead = s.t >= s.life || w.arena.isSolidAt(s.x, s.y + 6);
      if (!dead && h.alive) {
        const dx = h.x - s.x, dy = h.y - 12 - s.y;
        if (dx * dx + dy * dy < (s.r + 6) ** 2) {
          if (this.combat.hurtHero(s.dmg, s.x, s.y)) dead = true;
          else if (!h.invulnerable) dead = true;
        }
      }
      if (dead) {
        w.fx.hit(s.x, s.y, 0xff9a8a);
        s.sp.visible = false;
        if (s.glow) s.glow.visible = false;
        this.shots.splice(i, 1);
        this.shotPool.push(s);
        continue;
      }
      s.sp.texture = s.frames[Math.floor(s.t * 10) % s.frames.length];
      if (s.spin) s.sp.rotation += dt * 8;
      s.sp.position.set(Math.round(s.x), Math.round(s.y));
      if (s.glow) s.glow.position.set(s.sp.x, s.sp.y);
    }
  }

  clearShots(): void {
    for (const s of this.shots) {
      s.sp.visible = false;
      if (s.glow) s.glow.visible = false;
      this.shotPool.push(s);
    }
    this.shots.length = 0;
  }
}
