import { Container, Sprite, Texture } from 'pixi.js';
import { assets } from './AssetLoader';
import { Arena } from './Arena';
import { Hero } from '../entities/Hero';
import { Enemy } from '../entities/Enemy';
import { SpatialHash } from '../utils/SpatialHash';
import { Particles } from '../render/Particles';
import { DamageNumbers } from '../render/DamageNumbers';
import { Fx } from '../render/Fx';
import { Lighting } from '../render/Lighting';
import { deriveStats, xpToNext, type DerivedStats } from '../content/stats';
import type { ActDef } from '../content/acts';
import type { Levels } from '../content/upgrades';
import type { Quality } from '../systems/Save';

/** Persistent run state (carried across acts). */
export interface RunState {
  levels: Levels;
  heroLevel: number;
  xp: number;
  hpFrac: number;
  time: number;
  kills: number;
  damage: number;
  coins: number;
  actsDone: number;
  act: number;
  rerolls: number;
  bonusHpPct: number;
  skinTint: number;
  pendingLevels: number;
  pendingChest: number;
}

export interface WorldHooks {
  levelUp(): void;
  heroDied(): void;
  actComplete(): void;
  victory(): void;
  objective(text: string, hint?: string): void;
  bossBar(name: string | null, frac: number): void;
  banner(text: string, sub?: string): void;
  /** records a creature as seen (bestiary) */
  bossSeen(kind: string): void;
  bossSlain(): void;
}

/**
 * World of one act: render layers, entities and services shared by the systems.
 */
export class World {
  readonly root = new Container();
  readonly ground = new Container();
  readonly decals = new Container();
  readonly shadows = new Container();
  readonly pickupsLayer = new Container();
  readonly actors = new Container();
  readonly projectiles = new Container();
  readonly fxNormal = new Container();
  readonly fxAdd = new Container();
  readonly lights = new Container();
  readonly top = new Container();

  readonly arena: Arena;
  readonly hero: Hero;
  readonly enemies: Enemy[] = [];
  readonly hash = new SpatialHash<Enemy>(48);
  readonly particles: Particles;
  readonly numbers: DamageNumbers;
  readonly fx: Fx;
  stats: DerivedStats;
  time = 0;
  hitstop = 0;
  trauma = 0;
  flashAlpha = 0;
  flashColor = 0xffffff;
  /** act multipliers */
  hpMul: number;
  dmgMul: number;
  quality: Quality;
  reduceFlash = false;
  reduceShake = false;
  heroLight: Sprite;
  readonly lighting: Lighting;
  lifestealBudget = 0;
  /** transient lights (explosions, lightning, hits): x, y, radius, intensity, colour, life, max life. */
  readonly flashes: [number, number, number, number, number, number, number][] = [];

  flashLight(x: number, y: number, r: number, i: number, color: number, life: number): void {
    if (this.flashes.length > 40) this.flashes.shift();
    this.flashes.push([x, y, r, i, color, life, life]);
  }

  /** test tool: ignores incoming damage. */
  god = false;

  constructor(
    readonly act: ActDef,
    readonly run: RunState,
    readonly hooks: WorldHooks,
    quality: Quality,
  ) {
    this.quality = quality;
    this.hpMul = act.hpMul;
    this.dmgMul = act.dmgMul;
    const map = assets.maps[act.map];
    if (!map) throw new Error(`Mapa ausente: ${act.map}`);
    this.arena = new Arena(map);
    this.actors.sortableChildren = true;
    this.fxAdd.blendMode = 'add';
    this.lighting = new Lighting();
    this.root.addChild(this.ground, this.decals, this.shadows, this.pickupsLayer, this.actors, this.lighting.overlay, this.projectiles, this.fxNormal, this.fxAdd, this.lights, this.top);
    this.arena.build(this.ground, this.decals, this.actors, this.lights);
    this.lighting.ambient = act.tint;
    this.particles = new Particles(this.fxAdd, this.fxNormal);
    this.particles.max = quality === 'low' ? 320 : quality === 'medium' ? 650 : 1000;
    this.numbers = new DamageNumbers(this.top);
    this.fx = new Fx(this);
    this.stats = deriveStats(run.levels, { bonusHpPct: run.bonusHpPct });
    this.hero = new Hero();
    const [sx, sy] = this.arena.tileCenter(map.start[0], map.start[1]);
    this.hero.x = sx;
    this.hero.y = sy;
    this.hero.maxHp = this.stats.maxHp;
    this.hero.hp = Math.max(1, Math.round(this.stats.maxHp * run.hpFrac));
    this.shadows.addChild(this.hero.shadow);
    this.actors.addChild(this.hero.root);
    this.heroLight = new Sprite(assets.tex('fx', 'glow_fire'));
    this.heroLight.anchor.set(0.5);
    this.heroLight.blendMode = 'add';
    this.heroLight.scale.set(2.6);
    this.heroLight.alpha = 0.1;
    this.lights.addChild(this.heroLight);
  }

  refreshStats(): void {
    const before = this.stats.maxHp;
    this.stats = deriveStats(this.run.levels, { bonusHpPct: this.run.bonusHpPct });
    this.hero.maxHp = this.stats.maxHp;
    if (this.stats.maxHp > before) this.hero.hp += this.stats.maxHp - before;
    this.hero.hp = Math.min(this.hero.hp, this.hero.maxHp);
  }

  addEnemy(e: Enemy): void {
    this.enemies.push(e);
    this.shadows.addChild(e.shadow);
    this.actors.addChild(e.root);
  }

  removeEnemy(e: Enemy): void {
    e.alive = false;
    e.root.destroy({ children: true });
    e.shadow.destroy();
  }

  /** Gains experience (with multiplier) and queues level-ups. */
  gainXp(v: number): void {
    this.run.xp += v * this.stats.xpMul;
    let need = xpToNext(this.run.heroLevel);
    while (this.run.xp >= need) {
      this.run.xp -= need;
      this.run.heroLevel++;
      this.run.pendingLevels++;
      need = xpToNext(this.run.heroLevel);
    }
  }

  shake(amount: number): void {
    this.trauma = Math.min(1, this.trauma + amount * (this.reduceShake ? 0.3 : 1));
  }

  freeze(t: number): void {
    this.hitstop = Math.max(this.hitstop, t);
  }

  screenFlash(color: number, alpha: number): void {
    this.flashColor = color;
    this.flashAlpha = Math.max(this.flashAlpha, alpha * (this.reduceFlash ? 0.25 : 1));
  }

  /** Loose sprite in the world (decals, auras) — the caller manages its lifetime. */
  sprite(tex: Texture, layer: Container, x: number, y: number, add = false): Sprite {
    const s = new Sprite(tex);
    s.anchor.set(0.5);
    s.position.set(x, y);
    if (add) s.blendMode = 'add';
    layer.addChild(s);
    return s;
  }

  destroy(): void {
    this.particles.clear();
    this.numbers.clear();
    this.lighting.destroy();
    this.root.destroy({ children: true });
  }
}
