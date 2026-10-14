import { Container, Sprite, Texture, TilingSprite } from 'pixi.js';
import type { World } from '../game/World';
import type { Combat, HitOpts } from './Combat';
import type { Enemy } from '../entities/Enemy';
import { assets } from '../game/AssetLoader';
import { audio } from '../game/AudioManager';
import { rng, TAU, angleDiff } from '../utils/math';

type ProjKind = 'arrow' | 'lance' | 'seed' | 'shard' | 'tornado';

class Proj {
  sp = new Sprite(Texture.EMPTY);
  glow: Sprite | null = null;
  kind: ProjKind = 'arrow';
  frames: Texture[] = [];
  x = 0; y = 0; vx = 0; vy = 0;
  h = 12;
  life = 0; t = 0;
  dmg = 0; r = 4;
  pierce = 0;
  hits: number[] = [];
  opts: HitOpts = {};
  alive = false;
  trailT = 0;
  tx = 0; ty = 0; sx = 0; sy = 0;
}

interface Bolt {
  segs: TilingSprite[];
  t: number;
  frames: Texture[];
}

/**
 * The archer's arsenal: Rune Arrow, Ember Crown (+Q Pulse), Solar Lance, Storm Chain,
 * Crystal Lotus and Cinder Wind, plus the three legendary combos.
 */
export class Weapons {
  combat!: Combat;
  private projs: Proj[] = [];
  private pool: Proj[] = [];
  private bolts: Bolt[] = [];
  private T: Record<string, Texture[]> = {};
  private timers = { arrow: 0.4, lance: 1.2, chain: 1.0, lotus: 1.5, wind: 1.2 };
  private volley = 0;
  // Crown
  private crownRing: Container;
  private ringSprite: Sprite;
  private fireRing: Sprite;
  private flames: { sp: Sprite; glow: Sprite; x: number; y: number }[] = [];
  private crownAngle = 0;
  private pulseT = -1;
  private pulseHit = new Set<number>();
  aimX: number | null = null;
  aimY: number | null = null;

  constructor(private readonly w: World) {
    for (const k of ['arrow', 'lance', 'crystal_seed', 'crystal_shard', 'tornado', 'bolt', 'wind', 'crown_flame', 'crown_ring', 'ember', 'glow_fire', 'glow_ice', 'glow_spirit'])
      this.T[k] = assets.anim('fx', k);
    this.crownRing = new Container();
    this.crownRing.scale.y = 0.62;
    this.ringSprite = new Sprite(this.T.crown_ring[0]);
    this.ringSprite.anchor.set(0.5);
    this.ringSprite.blendMode = 'add';
    this.crownRing.addChild(this.ringSprite);
    w.decals.addChild(this.crownRing);
    this.fireRing = new Sprite(assets.tex('fx', 'fire_ring'));
    this.fireRing.anchor.set(0.5, 0.54);
    this.fireRing.blendMode = 'add';
    w.fxAdd.addChild(this.fireRing);
  }

  get count(): number {
    return this.projs.length;
  }

  // ------------------------------------------------------------------ util
  private targetNearest(range: number): Enemy | null {
    const h = this.w.hero;
    if (this.aimX !== null && this.aimY !== null) return null;
    return this.w.hash.nearest(h.x, h.y, range, (e) => e.dying || (e.z > 30 && !e.boss));
  }

  private aimAngle(range: number): number | null {
    const h = this.w.hero;
    if (this.aimX !== null && this.aimY !== null) return Math.atan2(this.aimY - (h.y - 12), this.aimX - h.x);
    const t = this.targetNearest(range);
    return t ? Math.atan2(t.y - h.y, t.x - h.x) : null;
  }

  private spawn(kind: ProjKind, x: number, y: number, ang: number, speed: number, dmg: number, life: number, opts: HitOpts, pierce = 0): Proj {
    const p = this.pool.pop() ?? new Proj();
    if (p.sp.parent !== this.w.projectiles) this.w.projectiles.addChild(p.sp);
    p.kind = kind;
    p.x = x; p.y = y; p.vx = Math.cos(ang) * speed; p.vy = Math.sin(ang) * speed;
    p.t = 0; p.life = life; p.dmg = dmg; p.pierce = pierce; p.hits.length = 0; p.opts = opts; p.alive = true; p.trailT = 0;
    p.h = 12;
    p.frames = kind === 'arrow' ? this.T.arrow : kind === 'lance' ? this.T.lance : kind === 'seed' ? this.T.crystal_seed : kind === 'shard' ? this.T.crystal_shard : this.T.tornado;
    p.r = kind === 'lance' ? 7 : kind === 'tornado' ? 12 : kind === 'shard' ? 4 : 4;
    p.sp.texture = p.frames[0];
    p.sp.anchor.set(kind === 'arrow' || kind === 'lance' ? 0.7 : 0.5, kind === 'tornado' ? 0.85 : 0.5);
    p.sp.visible = true;
    p.sp.alpha = 1;
    p.sp.blendMode = kind === 'lance' || kind === 'tornado' ? 'add' : 'normal';
    p.sp.rotation = kind === 'tornado' || kind === 'seed' ? 0 : ang;
    p.sp.tint = kind === 'arrow' && this.w.stats.arrow.solar ? 0xffd0a0 : 0xffffff;
    const gtex = kind === 'arrow' ? null : kind === 'lance' || kind === 'tornado' ? 'glow_fire' : 'glow_ice';
    if (gtex && this.w.quality !== 'low') {
      if (!p.glow) {
        p.glow = new Sprite(this.T[gtex][0]);
        p.glow.anchor.set(0.5);
        p.glow.blendMode = 'add';
      }
      p.glow.texture = this.T[gtex][0];
      p.glow.scale.set(kind === 'lance' || kind === 'tornado' ? 0.9 : 0.4);
      p.glow.alpha = 0.45;
      p.glow.visible = true;
      if (p.glow.parent !== this.w.lights) this.w.lights.addChild(p.glow);
    } else if (p.glow) p.glow.visible = false;
    this.projs.push(p);
    return p;
  }

  private kill(p: Proj, i: number): void {
    p.alive = false;
    p.sp.visible = false;
    if (p.glow) p.glow.visible = false;
    this.projs[i] = this.projs[this.projs.length - 1];
    this.projs.pop();
    this.pool.push(p);
  }

  // ---------------------------------------------------------------- update
  update(dt: number): void {
    const w = this.w;
    const h = w.hero;
    const s = w.stats;
    if (h.alive) {
      const cd = s.cdMul;
      for (const k of Object.keys(this.timers) as (keyof typeof this.timers)[]) this.timers[k] -= dt;
      if (this.timers.arrow <= 0) this.fireArrows();
      if (s.lance.level > 0 && this.timers.lance <= 0) this.fireLance(cd);
      if (s.chain.level > 0 && this.timers.chain <= 0) this.fireChain(cd);
      if (s.lotus.level > 0 && this.timers.lotus <= 0) this.fireLotus(cd);
      if (s.wind.level > 0 && this.timers.wind <= 0) this.fireWind(cd);
    }
    this.updateCrown(dt);
    this.updateProjs(dt);
    this.updateBolts(dt);
  }

  private fireArrows(): void {
    const w = this.w, h = w.hero, a = w.stats.arrow;
    const ang = this.aimAngle(a.range);
    if (ang === null) {
      this.timers.arrow = 0.1;
      return;
    }
    this.timers.arrow = a.cooldown * w.stats.cdMul;
    this.volley++;
    h.faceAngle(ang);
    h.shootT = 0.25;
    const opts: HitOpts = { knock: 30, tint: 0xffe0a0, burn: a.solar ? { dps: w.stats.crown.burnDps, time: 2 } : undefined };
    const n = a.count;
    for (let i = 0; i < n; i++) {
      const off = (i - (n - 1) / 2) * 0.14;
      this.spawn('arrow', h.x + Math.cos(ang) * 8, h.y + Math.sin(ang) * 6, ang + off, a.speed, a.damage, a.range / a.speed + 0.15, opts, a.pierce);
    }
    if (a.solar && this.volley % 4 === 0) {
      for (let i = 0; i < 5; i++) this.spawn('arrow', h.x, h.y, ang + (i - 2) * 0.22, a.speed * 0.9, a.damage * 1.2, 0.8, { ...opts, tint: 0xffa040 }, 1);
      audio.play('fire', { rate: 1.3 });
    }
    audio.play('arrow', { rate: rng.range(0.92, 1.08) });
  }

  private fireLance(cdMul: number, angOverride?: number, fromX?: number, fromY?: number): void {
    const w = this.w, h = w.hero, L = w.stats.lance;
    let ang = angOverride ?? this.aimAngle(260);
    if (ang === null) ang = h.aim;
    if (angOverride === undefined) this.timers.lance = L.cooldown * cdMul;
    const n = angOverride === undefined ? L.count : 1;
    const opts: HitOpts = { source: 'lance', cd: 0.3, knock: 60, heavy: false, tint: 0xffb050, burn: L.embers ? { dps: 6, time: 2 } : undefined };
    for (let i = 0; i < n; i++) {
      const off = (i - (n - 1) / 2) * 0.12;
      this.spawn('lance', fromX ?? h.x, fromY ?? h.y, ang + off, 430, L.damage, 0.9, opts, 999);
    }
    audio.play('lance', { rate: rng.range(0.95, 1.05) });
  }

  private fireChain(cdMul: number): void {
    const w = this.w, h = w.hero, C = w.stats.chain;
    const first = w.hash.nearest(h.x, h.y, 190, (e) => e.dying);
    if (!first) {
      this.timers.chain = 0.25;
      return;
    }
    this.timers.chain = C.cooldown * cdMul;
    const used = new Set<number>();
    for (let c = 0; c < C.chains; c++) {
      let cur: Enemy | null = c === 0 ? first : w.hash.nearest(h.x, h.y, 220, (e) => e.dying || used.has(e.id));
      if (!cur) break;
      const pts: [number, number][] = [[h.x, h.y - 18]];
      let shards = 0;
      for (let j = 0; j < C.jumps && cur; j++) {
        used.add(cur.id);
        pts.push([cur.x, cur.bodyY]);
        this.combat.damageEnemy(cur, C.damage, { stun: 0.2, tint: 0xb0c0ff, knock: 20 });
        w.fx.explosion(cur.x, cur.bodyY, 'volt', 0.4);
        const prev: Enemy = cur;
        const next: Enemy | null = w.hash.nearest(prev.x, prev.y, C.jumpRange, (e) => e.dying || used.has(e.id));
        if (w.stats.combos.shatter && shards < 6) {
          const tgt = next ?? w.hash.nearest(prev.x, prev.y, 140, (e) => e.dying || e.id === prev.id);
          if (tgt) {
            shards++;
            const a = Math.atan2(tgt.y - prev.y, tgt.x - prev.x);
            this.spawn('shard', prev.x, prev.y, a, 260, w.stats.lotus.shardDamage * 1.2 || 10, 0.5, { slow: { amt: 0.3, time: 1 }, tint: 0x9af0ff, knock: 20 }, 1);
          }
        }
        cur = next;
      }
      this.makeBolt(pts);
    }
    w.shake(0.08);
    audio.play('thunder', { rate: rng.range(0.9, 1.15) });
  }

  private makeBolt(pts: [number, number][]): void {
    const segs: TilingSprite[] = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
      const len = Math.hypot(bx - ax, by - ay);
      const ts = new TilingSprite({ texture: this.T.bolt[0], width: Math.max(8, len), height: 12 });
      ts.anchor.set(0, 0.5);
      ts.position.set(ax, ay);
      ts.rotation = Math.atan2(by - ay, bx - ax);
      ts.blendMode = 'add';
      this.w.fxAdd.addChild(ts);
      segs.push(ts);
    }
    this.bolts.push({ segs, t: 0, frames: this.T.bolt });
  }

  private updateBolts(dt: number): void {
    for (let i = this.bolts.length - 1; i >= 0; i--) {
      const b = this.bolts[i];
      b.t += dt;
      const fi = Math.floor(b.t / 0.045) % b.frames.length;
      for (const s of b.segs) {
        s.texture = b.frames[fi];
        s.alpha = b.t < 0.08 ? 1 : Math.max(0, 1 - (b.t - 0.08) / 0.14);
      }
      if (b.t > 0.22) {
        for (const s of b.segs) s.destroy();
        this.bolts.splice(i, 1);
      }
    }
  }

  private fireLotus(cdMul: number): void {
    const w = this.w, h = w.hero, Lo = w.stats.lotus;
    const near = w.hash.query(h.x, h.y, 210).filter((e) => !e.dying);
    if (!near.length) {
      this.timers.lotus = 0.3;
      return;
    }
    this.timers.lotus = Lo.cooldown * cdMul;
    for (let k = 0; k < Lo.seeds; k++) {
      const t = near[Math.floor(rng.next() * Math.min(near.length, 10))];
      const p = this.spawn('seed', h.x, h.y, 0, 0, Lo.seedDamage, 0.42, { tint: 0x9af0ff });
      p.sx = h.x; p.sy = h.y; p.tx = t.x + rng.range(-8, 8); p.ty = t.y + rng.range(-8, 8);
    }
    audio.play('glass', { rate: 1.4, gain: 0.5 });
  }

  private lotusBurst(x: number, y: number): void {
    const w = this.w, Lo = w.stats.lotus;
    for (const e of w.hash.query(x, y, 26)) this.combat.damageEnemy(e, Lo.seedDamage, { slow: { amt: Lo.slow, time: 1.5 }, tint: 0x9af0ff, knock: 40, dirX: e.x - x, dirY: e.y - y });
    const base = rng.range(0, TAU);
    for (let i = 0; i < Lo.shards; i++) {
      const a = base + (i / Lo.shards) * TAU;
      this.spawn('shard', x, y, a, 230, Lo.shardDamage, 0.45, { slow: { amt: Lo.slow, time: 1.5 }, tint: 0x9af0ff, knock: 25 }, 1);
    }
    w.fx.crystal(x, y - 10, 1.1);
    audio.play('glass');
  }

  private fireWind(cdMul: number): void {
    const w = this.w, h = w.hero, W = w.stats.wind;
    let base = this.aimAngle(150);
    if (base === null) base = h.aim;
    this.timers.wind = W.cooldown * cdMul;
    const dirs = W.dirs === 4 ? [0, Math.PI / 2, Math.PI, -Math.PI / 2] : W.dirs === 2 ? [0, Math.PI] : [0];
    for (const d of dirs) {
      const ang = base + d;
      // visual: advancing crescent
      for (let k = 0; k < 2; k++)
        w.particles.emit({ x: h.x + Math.cos(ang) * (18 + k * 10), y: h.y - 10 + Math.sin(ang) * (18 + k * 10), vx: Math.cos(ang) * 150, vy: Math.sin(ang) * 150,
          life: 0.32, frames: this.T.wind, rot: ang, scale: 1.1 + k * 0.25, alpha: 0.9 - k * 0.3, alphaEnd: 0, drag: 2, add: false });
      for (const e of w.hash.query(h.x, h.y, 82)) {
        if (e.dying) continue;
        const ea = Math.atan2(e.y - h.y, e.x - h.x);
        if (Math.abs(angleDiff(ang, ea)) > W.arc / 2) continue;
        this.combat.damageEnemy(e, W.damage, { knock: W.knock, dirX: Math.cos(ea), dirY: Math.sin(ea), tint: 0xe8e2d4, burn: w.stats.combos.tornado ? { dps: w.stats.crown.burnDps, time: 1.5 } : undefined });
      }
      if (w.stats.combos.tornado) {
        for (const off of [-0.45, 0.45]) {
          const p = this.spawn('tornado', h.x, h.y, ang + off, 120, 8, 1.7, { source: 'tornado', cd: 0.3, knock: 160, burn: { dps: w.stats.crown.burnDps + 4, time: 2.5 }, tint: 0xffa040 }, 999);
          p.h = 0;
        }
      }
    }
    audio.play('wind', { rate: rng.range(0.9, 1.1) });
    if (w.stats.combos.tornado) audio.play('fire', { gain: 0.7 });
  }

  // ------------------------------------------------------------------ Coroa
  private updateCrown(dt: number): void {
    const w = this.w, h = w.hero, C = w.stats.crown;
    const want = C.flames;
    while (this.flames.length < want) {
      const sp = new Sprite(this.T.crown_flame[0]);
      sp.anchor.set(0.5, 0.85);
      sp.blendMode = 'add';
      const glow = new Sprite(this.T.glow_fire[0]);
      glow.anchor.set(0.5);
      glow.blendMode = 'add';
      glow.scale.set(0.45);
      glow.alpha = 0.16;
      w.actors.addChild(sp);
      w.lights.addChild(glow);
      this.flames.push({ sp, glow, x: 0, y: 0 });
    }
    // pulse: radius expands and returns
    let rMul = 1;
    if (this.pulseT >= 0) {
      this.pulseT += dt;
      const t = this.pulseT;
      rMul = t < 0.22 ? 1 + (w.stats.pulse.radiusMul - 1) * (t / 0.22) : t < 0.55 ? w.stats.pulse.radiusMul - (w.stats.pulse.radiusMul - 1) * ((t - 0.22) / 0.33) : 1;
      if (t < 0.3) {
        const R = C.radius * rMul + 10;
        for (const e of w.hash.query(h.x, h.y, R)) {
          if (e.dying || this.pulseHit.has(e.id)) continue;
          this.pulseHit.add(e.id);
          this.combat.damageEnemy(e, w.stats.pulse.damage, { knock: w.stats.pulse.knock, burn: { dps: C.burnDps + 3, time: C.burnTime + 1 }, heavy: !!e.elite, tint: 0xffb050 });
        }
      }
      if (t >= 0.6) this.pulseT = -1;
    }
    const R = C.radius * rMul;
    this.crownAngle += C.spin * dt * (this.pulseT >= 0 ? 2.2 : 1);
    const tint = w.run.skinTint;
    const cx = h.x, cy = h.y - 12;
    this.crownRing.position.set(Math.round(h.x), Math.round(h.y - 2));
    this.ringSprite.texture = this.T.crown_ring[Math.min(3, Math.floor((C.flames - 3) / 1.2))];
    this.ringSprite.rotation = -this.crownAngle * 0.35;
    this.ringSprite.scale.set((R + 8) / 36);
    this.ringSprite.alpha = h.alive ? 0.55 + (this.pulseT >= 0 ? 0.45 : 0) : 0;
    this.ringSprite.tint = tint;
    this.fireRing.texture = assets.anim('fx', 'fire_ring')[Math.floor(w.time * 10) % 4];
    this.fireRing.position.set(Math.round(h.x), Math.round(h.y - 4));
    this.fireRing.scale.set((R + 4) / 46);
    this.fireRing.alpha = h.alive ? 0.75 + (this.pulseT >= 0 ? 0.25 : 0) : 0;
    this.fireRing.tint = tint;
    const fi = Math.floor(w.time * 14);
    for (let i = 0; i < this.flames.length; i++) {
      const f = this.flames[i];
      const visible = i < want && h.alive;
      f.sp.visible = f.glow.visible = visible;
      if (!visible) continue;
      const a = this.crownAngle + (i / want) * TAU;
      f.x = cx + Math.cos(a) * R;
      f.y = cy + Math.sin(a) * R * 0.62;
      f.sp.texture = this.T.crown_flame[(fi + i * 2) % this.T.crown_flame.length];
      f.sp.position.set(Math.round(f.x), Math.round(f.y + 6));
      f.sp.zIndex = h.y + Math.sin(a) * R * 0.62 + 0.5;
      const sc = this.pulseT >= 0 ? 0.95 : 0.62;
      f.sp.scale.set(sc);
      f.sp.tint = tint;
      f.glow.position.set(f.sp.x, f.sp.y - 6);
      f.glow.tint = tint;
      // contact damage (per-target cooldown)
      if (h.alive) {
        for (const e of w.hash.query(f.x, f.y + 12, 8)) {
          if (e.dying) continue;
          this.combat.damageEnemy(e, C.damage, { source: 'crown', cd: C.hitCd, knock: 50, burn: { dps: C.burnDps, time: C.burnTime }, tint: 0xffb050, dirX: e.x - h.x, dirY: e.y - h.y });
        }
        if (w.quality !== 'low' && rng.next() < dt * 10) {
          w.particles.emit({ x: f.x, y: f.y, vx: -Math.sin(a) * 30, vy: Math.cos(a) * 18 - 14, life: 0.45, tex: this.T.ember[rng.int(0, 2)], add: true, alphaEnd: 0, tint });
        }
      }
    }
  }

  /** Crown Pulse (Q). Returns true if performed. */
  tryPulse(): boolean {
    const w = this.w, h = w.hero, P = w.stats.pulse;
    if (!h.alive || h.pulseCd > 0 || h.energy < P.cost) return false;
    h.energy -= P.cost;
    h.pulseCd = P.cooldown * w.stats.cdMul;
    this.pulseT = 0;
    this.pulseHit.clear();
    w.fx.shockwave(h.x, h.y - 4, (w.stats.crown.radius * P.radiusMul) / 52);
    w.fx.embers(h.x, h.y - 12, 26, 180);
    w.shake(0.3);
    w.screenFlash(0xffb050, 0.12);
    w.freeze(0.04);
    audio.play('pulse');
    if (w.stats.combos.dawn) {
      const n = w.stats.lance.level >= 3 ? 6 : 3;
      const base = rng.range(0, TAU);
      for (let i = 0; i < n; i++) this.fireLance(1, base + (i / n) * TAU, h.x, h.y);
    }
    return true;
  }

  // ----------------------------------------------------------- projectiles
  private updateProjs(dt: number): void {
    const w = this.w;
    for (let i = this.projs.length - 1; i >= 0; i--) {
      const p = this.projs[i];
      p.t += dt;
      if (p.kind === 'seed') {
        // parabolic arc to the target
        const k = Math.min(1, p.t / p.life);
        p.x = p.sx + (p.tx - p.sx) * k;
        p.y = p.sy + (p.ty - p.sy) * k;
        p.h = 12 + Math.sin(k * Math.PI) * 34;
        p.sp.rotation += dt * 9;
        if (k >= 1) {
          this.lotusBurst(p.x, p.y);
          this.kill(p, i);
          continue;
        }
      } else {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        if (p.kind === 'tornado') {
          // drags gently towards the vortex centre
          p.vx *= Math.exp(-0.4 * dt);
          p.vy *= Math.exp(-0.4 * dt);
        }
        if (p.t >= p.life || (p.kind !== 'tornado' && w.arena.isSolidAt(p.x, p.y))) {
          if (p.kind === 'arrow' || p.kind === 'shard') w.fx.hit(p.x, p.y - p.h, p.kind === 'shard' ? 0x9af0ff : 0xffe0a0);
          this.kill(p, i);
          continue;
        }
        const list = w.hash.query(p.x, p.y, p.r);
        let dead = false;
        for (const e of list) {
          if (e.dying || p.hits.includes(e.id)) continue;
          if (e.z > 26 && !e.boss && e.def.flying !== true) continue;
          const ok = this.combat.damageEnemy(e, p.dmg, { ...p.opts, dirX: p.vx, dirY: p.vy });
          if (!ok && p.opts.source) continue;
          p.hits.push(e.id);
          if (p.kind === 'lance') w.fx.embers(e.x, e.bodyY, 3, 60);
          if (p.hits.length > p.pierce) {
            dead = true;
            break;
          }
        }
        if (dead) {
          this.kill(p, i);
          continue;
        }
      }
      // visuals and trail
      const fr = p.frames;
      p.sp.texture = fr[Math.floor(p.t * 12) % fr.length];
      p.sp.position.set(Math.round(p.x), Math.round(p.y - p.h));
      if (p.glow) p.glow.position.set(p.sp.x, p.sp.y);
      p.trailT += dt;
      const gap = w.quality === 'low' ? 0.08 : 0.035;
      if (p.trailT > gap) {
        p.trailT = 0;
        if (p.kind === 'arrow') w.particles.emit({ x: p.x, y: p.y - p.h, life: 0.18, tex: this.T.ember[0], add: true, alpha: 0.8, alphaEnd: 0, tint: w.stats.arrow.solar ? 0xffa040 : 0xffe0a0 });
        else if (p.kind === 'lance' || p.kind === 'tornado') w.particles.emit({ x: p.x + rng.range(-3, 3), y: p.y - p.h + rng.range(-3, 3), vy: -20, life: 0.35, tex: this.T.ember[rng.int(0, 3)], add: true, alphaEnd: 0 });
        else if (p.kind === 'shard') w.particles.emit({ x: p.x, y: p.y - p.h, life: 0.15, tex: this.T.ember[0], add: true, alphaEnd: 0, tint: 0x9af0ff });
      }
    }
  }

  destroy(): void {
    for (const f of this.flames) {
      f.sp.destroy();
      f.glow.destroy();
    }
    this.flames.length = 0;
  }
}
