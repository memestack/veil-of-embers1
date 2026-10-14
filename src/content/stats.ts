import type { Levels } from './upgrades';

/** Base numbers for the heroine and weapons. All balancing goes through here. */
export const BASE = {
  hp: 110,
  speed: 94,
  accel: 16,
  dashSpeed: 340,
  dashTime: 0.16,
  dashIframes: 0.28,
  dashCooldown: 1.1,
  hurtIframes: 0.6,
  pickupRadius: 48,
  energyMax: 100,
  energyRegen: 3.5,
  energyPerKill: 0.8,
};

export interface DerivedStats {
  maxHp: number;
  armor: number;
  speed: number;
  dashCooldown: number;
  pickupRadius: number;
  xpMul: number;
  dmgMul: number;
  cdMul: number;
  lifesteal: number;
  lifestealCap: number;
  arrow: { damage: number; cooldown: number; speed: number; range: number; count: number; pierce: number; solar: boolean };
  crown: { flames: number; radius: number; spin: number; damage: number; hitCd: number; burnDps: number; burnTime: number };
  pulse: { cost: number; cooldown: number; radiusMul: number; damage: number; knock: number };
  lance: { level: number; damage: number; cooldown: number; count: number; embers: boolean };
  chain: { level: number; damage: number; cooldown: number; jumps: number; jumpRange: number; chains: number };
  lotus: { level: number; seedDamage: number; shardDamage: number; shards: number; seeds: number; cooldown: number; slow: number };
  wind: { level: number; damage: number; cooldown: number; knock: number; dirs: number; arc: number };
  combos: { tornado: boolean; shatter: boolean; dawn: boolean };
}

export interface MetaMods {
  bonusHpPct: number;
}

export function deriveStats(l: Levels, meta: MetaMods = { bonusHpPct: 0 }): DerivedStats {
  const g = (id: string) => l[id] ?? 0;
  const dmgMul = 1 + 0.12 * g('u_fury');
  const cdMul = Math.pow(0.92, g('u_focus'));
  const lance = g('w_lance');
  const chain = g('w_chain');
  const lotus = g('w_lotus');
  const wind = g('w_wind');
  return {
    maxHp: Math.round((BASE.hp + 20 * g('u_hp')) * (1 + meta.bonusHpPct)),
    armor: g('u_hp'),
    speed: BASE.speed * (1 + 0.08 * g('u_speed')),
    dashCooldown: Math.max(0.5, BASE.dashCooldown - 0.15 * g('u_speed')),
    pickupRadius: BASE.pickupRadius * (1 + 0.45 * g('u_magnet')),
    xpMul: 1 + 0.1 * g('u_magnet'),
    dmgMul,
    cdMul,
    lifesteal: [0, 0.02, 0.03][g('u_lifesteal')],
    lifestealCap: [0, 3, 5][g('u_lifesteal')],
    arrow: {
      damage: 11 * (1 + 0.1 * g('u_pierce')),
      cooldown: 0.58,
      speed: 340,
      range: 230,
      count: 1 + g('u_twin'),
      pierce: g('u_pierce'),
      solar: g('l_solar') > 0,
    },
    crown: {
      flames: 3 + g('u_crown_big'),
      radius: 24 + 4 * g('u_crown_big'),
      spin: 3.1 * (1 + 0.12 * g('u_crown_big')),
      damage: 7,
      hitCd: 0.42,
      burnDps: 3 + 3 * g('u_burn'),
      burnTime: 2 + g('u_burn'),
    },
    pulse: {
      cost: 45 - 8 * g('u_pulse'),
      cooldown: 4.2 - 0.6 * g('u_pulse'),
      radiusMul: 3.4 * (1 + 0.12 * g('u_pulse')),
      damage: 24,
      knock: 240,
    },
    lance: {
      level: lance,
      damage: 30 * (lance >= 2 ? 1.3 : 1) * (lance >= 4 ? 1.3 : 1),
      cooldown: 2.6 - (lance >= 2 ? 0.3 : 0) - (lance >= 5 ? 0.4 : 0),
      count: lance >= 5 ? 3 : lance >= 3 ? 2 : 1,
      embers: lance >= 4,
    },
    chain: {
      level: chain,
      damage: 16 * (chain >= 3 ? 1.35 : 1),
      cooldown: 2.2 - (chain >= 5 ? 0.5 : 0),
      jumps: 4 + (chain >= 2 ? 2 : 0) + (chain >= 5 ? 3 : 0),
      jumpRange: 92 * (chain >= 3 ? 1.25 : 1),
      chains: chain >= 4 ? 2 : 1,
    },
    lotus: {
      level: lotus,
      seedDamage: 12,
      shardDamage: 9 * (lotus >= 3 ? 1.4 : 1),
      shards: 6 + (lotus >= 2 ? 3 : 0) + (lotus >= 5 ? 4 : 0),
      seeds: lotus >= 4 ? 2 : 1,
      cooldown: 3.0,
      slow: lotus >= 5 ? 0.45 : 0.3,
    },
    wind: {
      level: wind,
      damage: 9 * (wind >= 2 ? 1.5 : 1),
      cooldown: 2.4 - (wind >= 4 ? 0.4 : 0),
      knock: 250 * (wind >= 2 ? 1.35 : 1) * (g('c_tornado') ? 1.5 : 1),
      dirs: wind >= 5 ? 4 : wind >= 3 ? 2 : 1,
      arc: (wind >= 4 ? 1.3 : 1) * 2.0,
    },
    combos: { tornado: g('c_tornado') > 0, shatter: g('c_shatter') > 0, dawn: g('c_dawn') > 0 },
  };
}

/** Experience needed to go from level L to L+1. */
export const xpToNext = (L: number): number => Math.round(5 + L * 4 + L * L * 0.35);
