/**
 * Creature AI: simple, readable state machines
 * (approach, chase, telegraph, attack, recover, hurt, death).
 */
import type { World } from '../game/World';
import type { Combat } from '../systems/Combat';
import type { Hazards } from '../systems/Hazards';
import type { Enemy } from './Enemy';
import type { EnemyKind } from '../content/enemies';
import { assets } from '../game/AssetLoader';
import { audio } from '../game/AudioManager';
import { rng, TAU } from '../utils/math';

export interface AiCtx {
  w: World;
  combat: Combat;
  hazards: Hazards;
  spawn: (kind: EnemyKind, x: number, y: number) => Enemy | null;
}

type Ai = (e: Enemy, c: AiCtx, dt: number) => void;

const toHero = (e: Enemy, c: AiCtx) => {
  const dx = c.w.hero.x - e.x, dy = c.w.hero.y - e.y;
  const d = Math.hypot(dx, dy) || 1;
  return { dx: dx / d, dy: dy / d, d };
};

const setState = (e: Enemy, s: string) => {
  e.state = s;
  e.stateT = 0;
};

const chase = (e: Enemy, c: AiCtx, speedMul = 1, wobble = 0) => {
  const { dx, dy } = toHero(e, c);
  let vx = dx, vy = dy;
  if (wobble) {
    const k = Math.sin(c.w.time * 5 + e.id) * wobble;
    vx += -dy * k;
    vy += dx * k;
  }
  const sp = e.def.speed * speedMul;
  e.vx = vx * sp;
  e.vy = vy * sp;
  e.ang = Math.atan2(vy, vx);
  e.flip = vx < 0;
};

export const AI: Record<string, Ai> = {
  // ------------------------------------------------ Rustling: fast swarm, short lunge
  ferr(e, c) {
    const { d } = toHero(e, c);
    if (e.state === 'lunge') {
      if (e.stateT > 0.28) setState(e, 'move');
      e.setAnim('attack');
      return;
    }
    chase(e, c, 1, 0.35);
    e.setAnim('walk');
    if (d < 34 && e.stateT > 0.8 && rng.chance(0.08)) {
      setState(e, 'lunge');
      e.vx *= 2.1;
      e.vy *= 2.1;
    }
  },
  // ------------------------------------------------ Mordalume: flanqueia pelas laterais
  mord(e, c) {
    const h = c.w.hero;
    const { dx, dy, d } = toHero(e, c);
    if (e.mem.side === undefined) e.mem.side = rng.chance(0.5) ? 1 : -1;
    if (d > 80) {
      const off = Math.min(1, (d - 80) / 160) * 90 * e.mem.side;
      const tx = h.x - dy * off, ty = h.y + dx * off;
      const ax = tx - e.x, ay = ty - e.y;
      const l = Math.hypot(ax, ay) || 1;
      e.vx = (ax / l) * e.def.speed;
      e.vy = (ay / l) * e.def.speed;
      e.setAnim('walk');
    } else {
      e.vx = dx * e.def.speed * 1.6;
      e.vy = dy * e.def.speed * 1.6;
      e.setAnim(d < 26 ? 'attack' : 'walk');
    }
    e.ang = Math.atan2(e.vy, e.vx);
  },
  // ------------------------------------------------ Mire Child: slow, heavy mass
  lodo(e, c) {
    const { d } = toHero(e, c);
    chase(e, c, 1);
    e.setAnim(d < 30 ? 'attack' : 'walk');
  },
  // ------------------------------------------------ Glass Wasp: orbit, telegraphed aim, dive
  vesp(e, c) {
    const w = c.w, h = w.hero;
    e.z = 14 + Math.sin(w.time * 6 + e.id) * 2;
    if (e.state === 'move') {
      if (e.mem.orbit === undefined) e.mem.orbit = rng.range(0, TAU);
      e.mem.orbit += 0.7 * (1 / 60);
      const tx = h.x + Math.cos(e.mem.orbit) * 90, ty = h.y + Math.sin(e.mem.orbit) * 70;
      const ax = tx - e.x, ay = ty - e.y;
      const l = Math.hypot(ax, ay) || 1;
      const sp = e.def.speed * Math.min(1, l / 40);
      e.vx = (ax / l) * sp;
      e.vy = (ay / l) * sp;
      e.ang = Math.atan2(h.y - e.y, h.x - e.x);
      e.setAnim('fly');
      if (e.stateT > 2.2 + (e.id % 7) * 0.25 && l < 70) {
        setState(e, 'aim');
        e.ang = Math.atan2(h.y - e.y, h.x - e.x);
        e.tx = Math.cos(e.ang);
        e.ty = Math.sin(e.ang);
        c.hazards.line(e.x, e.y, e.ang, 150, 10, 0.55, () => undefined);
      }
    } else if (e.state === 'aim') {
      e.vx = -e.tx * 10;
      e.vy = -e.ty * 10;
      e.setAnim('fly');
      if (e.stateT > 0.55) setState(e, 'dive');
    } else if (e.state === 'dive') {
      e.vx = e.tx * 270;
      e.vy = e.ty * 270;
      e.z = 6;
      e.setAnim('dive');
      if (e.stateT > 0.55) setState(e, 'recover');
    } else {
      e.vx *= 0.9;
      e.vy *= 0.9;
      e.setAnim('fly');
      if (e.stateT > 0.8) setState(e, 'move');
    }
  },
  // ------------------------------------------------ Crimson Carapace: telegraphed frontal charge
  carap(e, c) {
    const w = c.w, h = w.hero;
    const { dx, dy, d } = toHero(e, c);
    if (e.state === 'move') {
      chase(e, c, 1);
      e.setAnim('walk');
      e.timer -= 1 / 60;
      if (d < 140 && e.timer <= 0 && w.arena.lineFree(e.x, e.y, h.x, h.y)) {
        setState(e, 'aim');
        e.tx = dx;
        e.ty = dy;
        e.flip = dx < 0;
        c.hazards.line(e.x, e.y - 6, Math.atan2(dy, dx), 150, 24, 0.7, () => undefined);
        audio.play('telegraph', { rate: 1.3, gain: 0.6 });
      }
    } else if (e.state === 'aim') {
      e.vx = e.vy = 0;
      e.setAnim('attack');
      if (e.stateT > 0.7) setState(e, 'charge');
    } else if (e.state === 'charge') {
      e.vx = e.tx * 215;
      e.vy = e.ty * 215;
      e.setAnim('attack');
      if (e.stateT > 0.65 || e.mem.bonk) {
        e.mem.bonk = 0;
        setState(e, 'recover');
        c.w.fx.dust(e.x, e.y, 5);
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim('walk');
      if (e.stateT > 1.0) {
        setState(e, 'move');
        e.timer = rng.range(2, 3.5);
      }
    }
  },
  // ------------------------------------------------ Rift Toad: arcing leap
  sapo(e, c) {
    const w = c.w, h = w.hero;
    if (e.state === 'move') {
      e.vx = e.vy = 0;
      e.z = 0;
      e.setAnim('idle');
      e.flip = h.x < e.x;
      if (e.stateT > (e.mem.wait ?? 0.9)) {
        setState(e, 'crouch');
      }
    } else if (e.state === 'crouch') {
      e.setAnim('crouch');
      if (e.stateT > 0.35) {
        setState(e, 'leap');
        const dx = h.x - e.x, dy = h.y - e.y;
        const d = Math.hypot(dx, dy) || 1;
        const jump = Math.min(110, d);
        e.tx = (dx / d) * (jump / 0.55);
        e.ty = (dy / d) * (jump / 0.55);
      }
    } else if (e.state === 'leap') {
      const t = e.stateT / 0.55;
      e.vx = e.tx;
      e.vy = e.ty;
      e.z = Math.sin(Math.min(1, t) * Math.PI) * 30;
      e.setAnim('leap');
      if (t >= 1) {
        e.z = 0;
        setState(e, 'land');
        w.fx.dust(e.x, e.y, 4, 0.7);
        const dd = Math.hypot(h.x - e.x, h.y - e.y);
        if (dd < 24) c.combat.hurtHero(e.damage, e.x, e.y);
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim('land');
      if (e.stateT > 0.25) {
        setState(e, 'move');
        e.mem.wait = rng.range(0.6, 1.3);
      }
    }
  },
  // ------------------------------------------------ Whisperer: keeps distance, fires soul orbs
  suss(e, c) {
    const w = c.w, h = w.hero;
    const { dx, dy, d } = toHero(e, c);
    e.z = 4 + Math.sin(w.time * 3 + e.id) * 2;
    e.flip = dx < 0;
    if (e.state === 'move') {
      let k = 0;
      if (d > 175) k = 1;
      else if (d < 115) k = -0.8;
      const strafe = Math.sin(w.time * 0.9 + e.id) * 0.6;
      e.vx = (dx * k - dy * strafe) * e.def.speed;
      e.vy = (dy * k + dx * strafe) * e.def.speed;
      e.setAnim('float');
      e.timer -= 1 / 60;
      if (e.timer <= 0 && d < 240) setState(e, 'cast');
    } else {
      e.vx = e.vy = 0;
      e.setAnim('cast');
      if (e.stateT > 0.75) {
        const a = Math.atan2(h.y - 12 - (e.y - 18), h.x - e.x);
        c.hazards.shoot(assets.anim('fx', 'orb_spirit'), e.x + (e.flip ? -8 : 8), e.y - 18, Math.cos(a) * 108, Math.sin(a) * 108, e.damage, 5, 3.5, false, 'glow_spirit');
        audio.play('summon', { rate: 2.2, gain: 0.35 });
        setState(e, 'move');
        e.timer = rng.range(2.4, 3.6);
      }
    }
  },
  // ------------------------------------------------ Ember Wisp: rushes, swells and bursts
  wisp(e, c) {
    const w = c.w, h = w.hero;
    const { dx, dy, d } = toHero(e, c);
    e.z = 10 + Math.sin(w.time * 8 + e.id) * 3;
    e.flip = dx < 0;
    if (e.state === 'move') {
      e.vx = dx * e.def.speed;
      e.vy = dy * e.def.speed;
      e.setAnim('float');
      if (d < 34) {
        setState(e, 'fuse');
        audio.play('telegraph', { rate: 2, gain: 0.4 });
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim('fuse');
      e.flashT = Math.sin(e.stateT * 40) > 0 ? 0.05 : 0;
      if (e.stateT > 0.6) {
        w.fx.explosion(e.x, e.y - 10, 'fire', 0.9);
        w.flashLight(e.x, e.y - 10, 120, 1, 0xffa050, 0.4);
        w.shake(0.2);
        if (Math.hypot(h.x - e.x, h.y - e.y) < 38) c.combat.hurtHero(e.damage, e.x, e.y);
        c.combat.kill(e);
      }
    }
  },
  // ------------------------------------------------ Coral Hermit: retreats into its shell
  hermit(e, c) {
    e.mem.hideCd = Math.max(0, (e.mem.hideCd ?? 0) - 1 / 60);
    if ((e.mem.hide ?? 0) > 0) {
      e.mem.hide -= 1 / 60;
      e.vx = e.vy = 0;
      e.setAnim('hide');
      if (e.mem.hide <= 0) e.mem.hideCd = 2.5;
      return;
    }
    chase(e, c, 1);
    e.setAnim('walk');
  },
  // ------------------------------------------------ Glass Golem: floor-marked slam
  golem(e, c) {
    const w = c.w;
    const { d } = toHero(e, c);
    if (e.state === 'move') {
      chase(e, c, 1);
      e.setAnim('walk');
      e.timer -= 1 / 60;
      if (d < 70 && e.timer <= 0) {
        setState(e, 'slam');
        e.tx = w.hero.x;
        e.ty = w.hero.y;
        c.hazards.ring(e.tx, e.ty, 34, 0.75, () => {
          w.fx.crystal(e.tx, e.ty - 4, 1.2);
          w.fx.dust(e.tx, e.ty, 6, 1);
          w.shake(0.25);
          audio.play('slam', { rate: 1.3, gain: 0.6 });
          if (Math.hypot(w.hero.x - e.tx, (w.hero.y - e.ty) / 0.62) < 36) c.combat.hurtHero(e.damage, e.tx, e.ty);
        });
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim('attack');
      if (e.stateT > 1.1) {
        setState(e, 'move');
        e.timer = 2.4;
      }
    }
  },
  mite(e, c) {
    chase(e, c, 1, 0.5);
    e.setAnim('walk');
  },
  // ------------------------------------------------ Elite: Ash Knight
  knight(e, c) {
    const w = c.w, h = w.hero;
    const { dx, dy, d } = toHero(e, c);
    e.flip = dx < 0;
    if (e.state === 'move') {
      chase(e, c, 1);
      e.setAnim('walk');
      e.timer -= 1 / 60;
      if (e.timer <= 0 && d < 120) {
        e.mem.n = (e.mem.n ?? 0) + 1;
        e.ang = Math.atan2(dy, dx);
        if (e.mem.n % 3 === 0) {
          setState(e, 'aimdash');
          c.hazards.line(e.x, e.y - 8, e.ang, 190, 26, 0.7, () => undefined);
        } else {
          setState(e, 'windup');
          c.hazards.cone(e.x, e.y - 8, e.ang, 92, 0.8, () => undefined);
        }
        audio.play('telegraph');
      }
    } else if (e.state === 'windup') {
      e.vx = e.vy = 0;
      e.setAnim('windup');
      if (e.stateT > 0.8) {
        setState(e, 'swing');
        audio.play('fire', { rate: 0.8 });
        w.shake(0.2);
        const ha = Math.atan2(h.y - e.y, h.x - e.x);
        let diff = Math.abs(ha - e.ang);
        if (diff > Math.PI) diff = Math.PI * 2 - diff;
        if (Math.hypot(h.x - e.x, h.y - e.y) < 96 && diff < Math.PI / 6 + 0.05) c.combat.hurtHero(e.damage * 1.2, e.x, e.y);
        for (let k = 0; k < 4; k++) {
          const a = e.ang + (k - 1.5) * 0.28;
          c.hazards.fire(e.x + Math.cos(a) * (40 + k * 6), e.y + Math.sin(a) * (30 + k * 4), 3.5, 7, 14);
        }
        w.flashLight(e.x + Math.cos(e.ang) * 40, e.y, 150, 0.9, 0xff8a3a, 0.5);
      }
    } else if (e.state === 'aimdash') {
      e.vx = e.vy = 0;
      e.setAnim('windup');
      if (e.stateT > 0.7) setState(e, 'charge');
    } else if (e.state === 'charge') {
      e.vx = Math.cos(e.ang) * 300;
      e.vy = Math.sin(e.ang) * 300;
      e.setAnim('swing');
      if (Math.random() < 0.5) c.hazards.fire(e.x, e.y, 2.5, 6, 10);
      if (e.stateT > 0.55 || e.mem.bonk) {
        e.mem.bonk = 0;
        setState(e, 'swing');
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim('swing');
      if (e.stateT > 0.6) {
        setState(e, 'move');
        e.timer = 1.6;
      }
    }
  },
  // ------------------------------------------------ Elite: Coral Warden
  guard(e, c) {
    const w = c.w, h = w.hero;
    const { dx, dy, d } = toHero(e, c);
    const broken = !!e.mem.armorBroke;
    const pre = broken ? 'b_' : '';
    if (e.state === 'move') {
      chase(e, c, broken ? 1.25 : 1);
      e.setAnim(pre + 'walk');
      e.timer -= 1 / 60;
      if (e.timer <= 0 && d < 190) {
        setState(e, 'aim');
        e.ang = Math.atan2(dy, dx);
        e.flip = dx < 0;
        e.mem.cone = 1;
        c.hazards.cone(e.x, e.y - 10, e.ang, 160, 0.9, () => undefined);
        audio.play('telegraph');
      }
    } else if (e.state === 'aim') {
      e.vx = e.vy = 0;
      e.setAnim(pre + 'charge');
      if (e.stateT > 0.9) {
        const n = broken ? 13 : 9;
        for (let i = 0; i < n; i++) {
          const a = e.ang + (i / (n - 1) - 0.5) * (Math.PI / 3);
          c.hazards.shoot(assets.anim('fx', 'coral_spike'), e.x + Math.cos(e.ang) * 20, e.y - 10, Math.cos(a) * 165, Math.sin(a) * 165, e.damage * 0.7, 5, 2.2);
        }
        audio.play('glass', { rate: 0.8 });
        w.shake(0.15);
        setState(e, 'recover');
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim(pre + 'walk');
      if (e.stateT > 0.8) {
        setState(e, 'move');
        e.timer = broken ? 2.8 : 3.8;
      }
    }
    void h;
  },
  // ------------------------------------------------ Elite: Glass Priestess
  sacer(e, c) {
    const w = c.w, h = w.hero;
    const { dx, dy, d } = toHero(e, c);
    e.flip = dx < 0;
    e.z = 6 + Math.sin(w.time * 2) * 3;
    if (e.state === 'move') {
      const k = d > 190 ? 1 : d < 140 ? -0.9 : 0;
      const strafe = 0.5;
      e.vx = (dx * k - dy * strafe) * e.def.speed;
      e.vy = (dy * k + dx * strafe) * e.def.speed;
      e.setAnim('float');
      e.timer -= 1 / 60;
      e.timer2 -= 1 / 60;
      if (e.timer <= 0) {
        // summon: three rune circles mark where the minions will appear
        setState(e, 'summon');
        audio.play('summon');
        for (let i = 0; i < 3; i++) {
          const a = rng.range(0, TAU);
          const [px, py] = w.arena.nearestFree(h.x + Math.cos(a) * 120, h.y + Math.sin(a) * 90);
          c.hazards.ring(px, py, 14, 0.9, () => {
            for (let k2 = 0; k2 < 2; k2++) c.spawn('ferr', px + rng.range(-6, 6), py + rng.range(-6, 6));
            w.fx.crystal(px, py - 6, 0.7);
          });
        }
      } else if (e.timer2 <= 0) {
        setState(e, 'zone');
        e.tx = h.x;
        e.ty = h.y;
        audio.play('telegraph');
        c.hazards.ring(e.tx, e.ty, 44, 1.1, () => {
          w.fx.crystal(e.tx, e.ty - 8, 2.0);
          w.fx.explosion(e.tx, e.ty - 6, 'ice', 1.2);
          audio.play('glass', { rate: 0.9 });
          w.shake(0.2);
          if (Math.hypot(w.hero.x - e.tx, (w.hero.y - e.ty) / 0.62) < 44) c.combat.hurtHero(e.damage * 1.5, e.tx, e.ty);
        });
      }
    } else {
      e.vx = e.vy = 0;
      e.setAnim('cast');
      if (e.stateT > 0.9) {
        if (e.state === 'summon') e.timer = 7.5;
        else e.timer2 = 4.6;
        setState(e, 'move');
      }
    }
  },
};

/** Generic movement, horde separation, scenery collision and contact damage. */
export function stepEnemies(c: AiCtx, dt: number): void {
  const w = c.w;
  const h = w.hero;
  const arena = w.arena;
  for (const e of w.enemies) {
    if (!e.alive) continue;
    e.animT += dt;
    e.stateT += dt;
    if (e.dying) {
      e.dieT += dt;
      continue;
    }
    if (e.boss) continue; // bosses have their own AI (bosses*.ts)
    if (e.stunT > 0) {
      e.vx *= 0.8;
      e.vy *= 0.8;
    } else {
      const ai = AI[e.kind];
      if (ai) ai(e, c, dt);
    }
    const slow = 1 - e.slowAmt;
    let mx = e.vx * slow + e.kx;
    let my = e.vy * slow + e.ky;
    e.kx *= Math.exp(-9 * dt);
    e.ky *= Math.exp(-9 * dt);
    // separation: avoids perfect stacks and forms organic masses
    const near = w.hash.query(e.x, e.y, e.radius + 2);
    let n = 0;
    for (const o of near) {
      if (o === e || o.dying) continue;
      const dx = e.x - o.x, dy = e.y - o.y;
      const rr = e.radius + o.radius;
      const d2 = dx * dx + dy * dy;
      if (d2 < rr * rr && d2 > 0.01) {
        const d = Math.sqrt(d2);
        const push = ((rr - d) / rr) * 60 * (o.def.mass / (e.def.mass + o.def.mass)) * 2;
        mx += (dx / d) * push;
        my += (dy / d) * push;
        if (++n > 5) break;
      }
    }
    e.x += mx * dt;
    e.y += my * dt;
    if (e.def.flying) {
      e.x = Math.max(16, Math.min(arena.pxW - 16, e.x));
      e.y = Math.max(16, Math.min(arena.pxH - 16, e.y));
    } else if (arena.resolve(e, e.radius, true) && e.state === 'charge') e.mem.bonk = 1;
    // contact damage
    if (h.alive && e.z < 20) {
      const dx = h.x - e.x, dy = h.y - e.y;
      const rr = e.radius + h.radius;
      if (dx * dx + dy * dy < rr * rr) {
        if (e.kind === 'wisp') continue;
        const mul = e.state === 'charge' || e.state === 'dive' || e.state === 'lunge' ? 1.3 : 1;
        c.combat.hurtHero(e.damage * mul, e.x, e.y);
      }
    }
  }
}
