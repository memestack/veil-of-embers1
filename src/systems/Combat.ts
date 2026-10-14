import type { World } from '../game/World';
import type { Enemy } from '../entities/Enemy';
import type { Pickups } from './Pickups';
import { audio } from '../game/AudioManager';
import { rng } from '../utils/math';

export interface HitOpts {
  /** source id for per-target damage cooldown (e.g. 'crown'). */
  source?: string;
  /** minimum interval between hits from this source on the same target. */
  cd?: number;
  knock?: number;
  /** knockback direction (if absent, away from the heroine). */
  dirX?: number;
  dirY?: number;
  burn?: { dps: number; time: number };
  slow?: { amt: number; time: number };
  stun?: number;
  /** heavy hit: hitstop + highlighted number. */
  heavy?: boolean;
  /** applies the global damage multiplier (default true). */
  scaled?: boolean;
  /** impact glow colour. */
  tint?: number;
  /** impact effect position (parts of composite bosses) */
  hitX?: number;
  hitY?: number;
}

/**
 * Data-driven combat: damage, armour, breakable armour, burn, slow, stun,
 * mass-based knockback, capped lifesteal, grouped numbers,
 * deaths with fragments and defined drops.
 */
export class Combat {
  pickups!: Pickups;
  onEnemyKilled: ((e: Enemy) => void) | null = null;

  constructor(private readonly w: World) {}

  damageEnemy(e: Enemy, base: number, o: HitOpts = {}): boolean {
    const w = this.w;
    if (!e.alive || e.dying) return false;
    if (e.owner) {
      // composite boss part: cooldown on the part, damage on the main body
      if (o.source) {
        const last = e.hitAt[o.source] ?? -99;
        if (w.time - last < (o.cd ?? 0)) return false;
        e.hitAt[o.source] = w.time;
      }
      return this.damageEnemy(e.owner, base, { ...o, source: undefined, knock: 0, hitX: e.x, hitY: e.bodyY });
    }
    if (o.source) {
      const last = e.hitAt[o.source] ?? -99;
      if (w.time - last < (o.cd ?? 0)) return false;
      e.hitAt[o.source] = w.time;
    }
    let dmg = base * (o.scaled === false ? 1 : w.stats.dmgMul);
    dmg = Math.max(1, dmg - e.def.armor);
    // breakable armour (Coral Warden)
    if (e.armorPool > 0) {
      const absorbed = Math.min(e.armorPool, dmg * 0.55);
      e.armorPool -= absorbed;
      dmg -= absorbed;
      if (e.armorPool <= 0) {
        e.mem.armorBroke = 1;
        w.fx.crystal(e.x, e.bodyY, 1.6);
        w.fx.explosion(e.x, e.bodyY, 'ice', 1.2);
        w.shake(0.35);
        audio.play('glass', { rate: 0.7 });
        w.hooks.banner('Armour broken!');
      }
    }
    // Heart crystal shield (phase 1)
    if (e.boss === 'heart' && e.phase === 1) dmg *= 0.65;
    // Hermit hiding in its shell
    if ((e.mem.hide ?? 0) > 0) dmg *= 0.2;
    else if (e.kind === 'hermit' && dmg >= 14 && !e.mem.hideCd) {
      e.mem.hide = 1.4;
      e.mem.hideCd = 1;
    }
    e.hp -= dmg;
    w.run.damage += dmg;
    e.flashT = 0.08;
    // lifesteal capped per second
    if (w.stats.lifesteal > 0 && w.lifestealBudget > 0 && w.hero.alive) {
      const heal = Math.min(w.lifestealBudget, dmg * w.stats.lifesteal);
      w.lifestealBudget -= heal;
      w.hero.hp = Math.min(w.hero.maxHp, w.hero.hp + heal);
    }
    if (o.knock && e.def.mass < 50) {
      let dx = o.dirX, dy = o.dirY;
      if (dx === undefined || dy === undefined) {
        dx = e.x - w.hero.x;
        dy = e.y - w.hero.y;
      }
      const l = Math.hypot(dx, dy) || 1;
      const k = o.knock / Math.max(0.5, e.def.mass);
      e.kx += (dx / l) * k;
      e.ky += (dy / l) * k;
    }
    if (o.burn) {
      e.burnT = Math.max(e.burnT, o.burn.time);
      e.burnDps = Math.max(e.burnDps, o.burn.dps);
    }
    if (o.slow) {
      e.slowT = Math.max(e.slowT, o.slow.time);
      e.slowAmt = Math.max(e.slowAmt, o.slow.amt);
    }
    if (o.stun && !e.boss) e.stunT = Math.max(e.stunT, o.stun);
    const hx = o.hitX ?? e.x, hy = o.hitY ?? e.bodyY;
    w.fx.hit(hx, hy, o.tint ?? 0xffe0a0, !!o.heavy);
    if (o.heavy) {
      w.freeze(0.035);
      w.numbers.show(hx, hy - 10, dmg, 0xffd27a, true);
    } else {
      e.dmgAccum += dmg;
    }
    if (e.hp <= 0) this.kill(e);
    return true;
  }

  /** Periodic flush of grouped numbers and per-creature status. */
  updateStatus(dt: number): void {
    const w = this.w;
    for (const e of w.enemies) {
      if (!e.alive || e.dying) continue;
      e.flashT = Math.max(0, e.flashT - dt);
      e.stunT = Math.max(0, e.stunT - dt);
      if (e.slowT > 0) {
        e.slowT -= dt;
        if (e.slowT <= 0) e.slowAmt = 0;
      }
      if (e.burnT > 0) {
        e.burnT -= dt;
        e.burnTick += dt;
        if (e.burnTick >= 0.5) {
          e.burnTick = 0;
          const d = e.burnDps * 0.5 * w.stats.dmgMul;
          e.hp -= d;
          e.dmgAccum += d;
          w.run.damage += d;
          w.fx.burn(e.x, e.bodyY);
          if (e.hp <= 0) {
            this.kill(e);
            continue;
          }
        }
      }
      e.dmgAccumT += dt;
      if (e.dmgAccumT > 0.35) {
        e.dmgAccumT = 0;
        if (e.dmgAccum >= 1) {
          const big = e.dmgAccum >= 25;
          w.numbers.show(e.x, e.bodyY - 8, e.dmgAccum, big ? 0xffe9b0 : 0xffffff, false);
          e.dmgAccum = 0;
        }
      }
    }
  }

  kill(e: Enemy): void {
    const w = this.w;
    if (e.dying) return;
    e.dying = true;
    e.dieT = 0;
    e.hp = 0;
    w.run.kills++;
    w.hero.energy = Math.min(100, w.hero.energy + 0.8);
    w.fx.death(e.x, e.bodyY, e.def.tint, e.elite || e.def.mass >= 2);
    if (e.kind === 'wisp') {
      w.fx.explosion(e.x, e.bodyY, 'fire', 0.7);
      audio.play('explosion', { rate: 1.4, gain: 0.5 });
    }
    audio.play(e.def.mass >= 2 || e.elite ? 'die2' : 'die1', { rate: rng.range(0.85, 1.15) });
    // defined drops
    const p = this.pickups;
    if (e.boss) {
      p.spawn('essence', e.x, e.y - 10, 10);
      for (let i = 0; i < 14; i++) p.spawn('xp_l', e.x + rng.range(-40, 40), e.y + rng.range(-24, 24), 6);
      p.spawn('heart', e.x + 20, e.y, 40);
    } else if (e.elite) {
      p.spawn('chest', e.x, e.y, 1);
      for (let i = 0; i < 8; i++) p.spawn('xp_m', e.x + rng.range(-24, 24), e.y + rng.range(-16, 16), 4);
    } else {
      const big = rng.chance(e.def.bigGem ?? 0);
      p.spawn(big ? 'xp_m' : 'xp_s', e.x, e.y, big ? e.def.xp + 1 : e.def.xp);
      if (rng.chance(0.012)) p.spawn('heart', e.x + 6, e.y, 18);
      else if (rng.chance(0.035)) p.spawn('energy', e.x - 6, e.y, 20);
      if (rng.chance(0.022)) p.spawn('coin', e.x, e.y + 4, 1);
    }
    this.onEnemyKilled?.(e);
  }

  hurtHero(amount: number, sx: number, sy: number): boolean {
    const w = this.w;
    const h = w.hero;
    if (!h.alive || h.invulnerable || w.god) return false;
    const dmg = Math.max(1, Math.round(amount * w.dmgMul - w.stats.armor));
    h.hp -= dmg;
    h.iframes = 0.6;
    h.hurtT = 0.5;
    const dx = h.x - sx, dy = h.y - sy;
    const l = Math.hypot(dx, dy) || 1;
    h.vx += (dx / l) * 110;
    h.vy += (dy / l) * 110;
    w.numbers.show(h.x, h.y - 40, dmg, 0xff6a5a, false);
    w.shake(0.32);
    w.screenFlash(0xff2a2a, 0.18);
    w.freeze(0.05);
    audio.play('hurt');
    if (h.hp <= 0) {
      h.hp = 0;
      h.alive = false;
      w.fx.explosion(h.x, h.y - 20, 'fire', 1.2);
      w.hooks.heroDied();
    }
    return true;
  }
}
