/**
 * Progression cards (structured data). Each card has a rarity, weight, max level,
 * an appearance condition and a numeric description per level.
 * The actual effect is computed in deriveStats() from the chosen levels.
 */
export type Rarity = 'common' | 'rare' | 'legendary';

export type Levels = Record<string, number>;

export interface CardDef {
  id: string;
  name: string;
  rarity: Rarity;
  icon: string;
  max: number;
  /** effect text when going to level `next` (1 = learn). */
  desc: (next: number) => string;
  /** extra appearance condition. */
  requires?: (lv: Levels, heroLevel: number) => boolean;
  weight?: number;
  kind: 'weapon' | 'passive' | 'combo' | 'heal';
}

const lv = (l: Levels, id: string) => l[id] ?? 0;

export const CARDS: CardDef[] = [
  // -------------------------------------------------------------- weapons
  { id: 'w_lance', name: 'Solar Lance', rarity: 'rare', icon: 'w_lance', max: 5, kind: 'weapon',
    desc: (n) => [
      'Fires a flaming lance that pierces an entire row of enemies (28 damage, every 2.6 s).',
      'Lance damage +30% and cooldown −0.3 s.',
      'Twin lance: two lances in a narrow fan.',
      'Damage +30%; the lance leaves embers that burn for 2 s.',
      'Triple lance and cooldown −0.4 s.'][n - 1] },
  { id: 'w_chain', name: 'Storm Chain', rarity: 'rare', icon: 'w_chain', max: 5, kind: 'weapon',
    desc: (n) => [
      'Lightning that jumps between 4 enemies (16 damage, every 2.2 s), stunning for 0.2 s.',
      '+2 jumps per chain.',
      'Damage +35% and jump range +25%.',
      'Fires two independent chains.',
      '+3 jumps and cooldown −0.5 s.'][n - 1] },
  { id: 'w_lotus', name: 'Crystal Lotus', rarity: 'rare', icon: 'w_lotus', max: 5, kind: 'weapon',
    desc: (n) => [
      'A crystal seed bursts into 6 radial shards that slow by 30% (every 3 s).',
      '+3 shards per burst.',
      'Shard damage +40%.',
      'Throws two seeds at once.',
      '+4 shards and 45% slow.'][n - 1] },
  { id: 'w_wind', name: 'Cinder Wind', rarity: 'rare', icon: 'w_wind', max: 5, kind: 'weapon',
    desc: (n) => [
      'A crescent gust ahead that pushes light creatures away (every 2.4 s).',
      'Knockback +35% and damage +50%.',
      'Gust also fires behind you.',
      'Arc 30% wider and cooldown −0.4 s.',
      'Gusts in four directions.'][n - 1] },
  // ------------------------------------------------------------- passives
  { id: 'u_twin', name: 'Twin Arrows', rarity: 'common', icon: 'u_twin', max: 3, kind: 'passive',
    desc: () => '+1 Rune Arrow per shot (in a fan).' },
  { id: 'u_pierce', name: 'Piercing Tip', rarity: 'common', icon: 'u_pierce', max: 3, kind: 'passive',
    desc: () => 'Arrows pierce +1 enemy and gain +10% damage.' },
  { id: 'u_crown_big', name: 'Greater Crown', rarity: 'common', icon: 'u_crown_big', max: 4, kind: 'passive',
    desc: () => '+1 flame on the Ember Crown, radius +4 px and spin +12%.' },
  { id: 'u_burn', name: 'Lingering Embers', rarity: 'common', icon: 'u_burn', max: 3, kind: 'passive',
    desc: () => 'Burn +3 damage/s and +1 s duration.' },
  { id: 'u_pulse', name: 'Hungry Pulse', rarity: 'rare', icon: 'u_pulse', max: 3, kind: 'passive',
    desc: () => 'Crown Pulse (Q): cost −8 energy, cooldown −0.6 s, radius +12%.' },
  { id: 'u_speed', name: 'Ash Steps', rarity: 'common', icon: 'u_speed', max: 3, kind: 'passive',
    desc: () => 'Speed +8% and dash cooldown −0.15 s.' },
  { id: 'u_hp', name: 'Basalt Skin', rarity: 'common', icon: 'u_hp', max: 4, kind: 'passive',
    desc: () => '+20 max health (heals 20) and +1 armour.' },
  { id: 'u_lifesteal', name: 'Amber Blood', rarity: 'rare', icon: 'u_lifesteal', max: 2, kind: 'passive',
    desc: (n) => `Recover ${n === 1 ? 2 : 3}% of damage dealt (max ${n === 1 ? 3 : 5} health per second).` },
  { id: 'u_focus', name: 'Rune Focus', rarity: 'common', icon: 'u_focus', max: 3, kind: 'passive',
    desc: () => 'All cooldowns −8%.' },
  { id: 'u_magnet', name: 'Ethereal Magnet', rarity: 'common', icon: 'u_magnet', max: 2, kind: 'passive',
    desc: () => 'Pickup radius +45% and experience +10%.' },
  { id: 'u_fury', name: 'Burning Fury', rarity: 'common', icon: 'u_fury', max: 4, kind: 'passive',
    desc: () => 'All damage +12%.' },
  // --------------------------------------------------------------- combos
  { id: 'c_tornado', name: 'Blazing Tornado', rarity: 'legendary', icon: 'c_tornado', max: 1, kind: 'combo', weight: 1.6,
    requires: (l) => lv(l, 'w_wind') >= 1,
    desc: () => 'CROWN + WIND: every gust releases 2 fire tornadoes that ignite and drag enemies; knockback +50%.' },
  { id: 'c_shatter', name: 'Thunder Shard', rarity: 'legendary', icon: 'c_shatter', max: 1, kind: 'combo', weight: 1.6,
    requires: (l) => lv(l, 'w_chain') >= 1 && lv(l, 'w_lotus') >= 1,
    desc: () => 'CHAIN + LOTUS: every electrocuted target fires a crystal shard at its neighbour (up to 6 per chain).' },
  { id: 'c_dawn', name: 'Circular Dawn', rarity: 'legendary', icon: 'c_dawn', max: 1, kind: 'combo', weight: 1.6,
    requires: (l) => lv(l, 'w_lance') >= 1,
    desc: () => 'LANCE + CROWN: the Pulse (Q) fires 3 radial Solar Lances from the crown (6 at lance level 3+).' },
  { id: 'l_solar', name: 'Solar Archer', rarity: 'legendary', icon: 'l_solar', max: 1, kind: 'combo',
    requires: (_l, h) => h >= 7,
    desc: () => 'Rune Arrows ignite their target; every 4th shot releases a fan of 5 flaming arrows.' },
  // -------------------------------------------------------------- reserve
  { id: 'u_heal', name: 'Restored Heart', rarity: 'common', icon: 'u_heal', max: 99, kind: 'heal', weight: 0.25,
    desc: () => 'Restores 40% of max health.' },
];

export const CARD_BY_ID: Record<string, CardDef> = Object.fromEntries(CARDS.map((c) => [c.id, c]));

export const RARITY_WEIGHT: Record<Rarity, number> = { common: 100, rare: 48, legendary: 16 };

export const RARITY_LABEL: Record<Rarity, string> = { common: 'Common · Jade', rare: 'Rare · Amethyst', legendary: 'Legendary · Solar Gold' };

/** Cards eligible right now (not maxed, conditions met). */
export function eligibleCards(levels: Levels, heroLevel: number): CardDef[] {
  return CARDS.filter((c) => (levels[c.id] ?? 0) < c.max && (!c.requires || c.requires(levels, heroLevel)));
}

/**
 * Draws `count` distinct cards weighted by rarity and weight. `rand` returns [0,1).
 * Rules: 'heal' only appears when options run out; the first level always offers at least one new weapon;
 * `minRarity` forces a minimum rarity (elite chests).
 */
export function rollCards(levels: Levels, heroLevel: number, rand: () => number, count = 3, minRarity?: Rarity): CardDef[] {
  const order: Rarity[] = ['common', 'rare', 'legendary'];
  let pool = eligibleCards(levels, heroLevel).filter((c) => c.kind !== 'heal');
  if (minRarity) {
    const strong = pool.filter((c) => order.indexOf(c.rarity) >= order.indexOf(minRarity));
    if (strong.length >= 1) pool = strong;
  }
  const picks: CardDef[] = [];
  const ownedWeapons = CARDS.filter((c) => c.kind === 'weapon' && (levels[c.id] ?? 0) > 0).length;
  if (ownedWeapons === 0) {
    const weapons = pool.filter((c) => c.kind === 'weapon');
    if (weapons.length) picks.push(weapons[Math.floor(rand() * weapons.length)]);
  }
  while (picks.length < count) {
    const cands = pool.filter((c) => !picks.includes(c));
    if (!cands.length) break;
    const w = cands.map((c) => RARITY_WEIGHT[c.rarity] * (c.weight ?? 1));
    const total = w.reduce((a, b) => a + b, 0);
    let r = rand() * total;
    let idx = 0;
    for (; idx < cands.length - 1; idx++) {
      r -= w[idx];
      if (r <= 0) break;
    }
    picks.push(cands[idx]);
  }
  if (picks.length < count) {
    const heal = CARD_BY_ID['u_heal'];
    if (!picks.includes(heal)) picks.push(heal);
  }
  return picks;
}
