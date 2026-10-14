/**
 * Authored campaign script: three acts, each a sequence of steps (objectives) with a wave table
 * giving time, composition, formation and gates. The Director only executes this table; the only
 * variation allowed is the exact position inside a gate.
 */
import type { EnemyKind, BossKind } from './enemies';

export type Formation = 'cluster' | 'arc' | 'line' | 'ring';

export interface WaveEntry {
  /** seconds since the step started (or since the cycle started, for looping steps) */
  at: number;
  /** if set, the entry is a continuous stream from `at` to `until` */
  until?: number;
  every?: number;
  kinds: Partial<Record<EnemyKind, number>>;
  count: number;
  formation?: Formation;
  /** spawn-zone indices of the map (empty = any zone off screen) */
  gates?: number[];
  label?: string;
}

export type StepType = 'survive' | 'reach' | 'channel' | 'elite' | 'boss' | 'portal' | 'victory';

export interface Step {
  type: StepType;
  text: string;
  hint?: string;
  duration?: number;
  /** repeats the wave table every N seconds (steps without a fixed duration) */
  loop?: number;
  waves: WaveEntry[];
  elite?: EnemyKind;
  boss?: BossKind;
}

export interface ActDef {
  id: number;
  roman: string;
  title: string;
  subtitle: string;
  map: 'arena_a' | 'arena_b' | 'arena_c';
  /** ambient light (multiplied over the arena); light sources open brighter pools */
  tint: number;
  hpMul: number;
  dmgMul: number;
  steps: Step[];
}

const S = (at: number, until: number, every: number, kinds: WaveEntry['kinds'], count: number, formation: Formation = 'cluster', gates?: number[]): WaveEntry =>
  ({ at, until, every, kinds, count, formation, gates });
const B = (at: number, kinds: WaveEntry['kinds'], count: number, formation: Formation = 'cluster', gates?: number[], label?: string): WaveEntry =>
  ({ at, kinds, count, formation, gates, label });

export const ACTS: ActDef[] = [
  {
    id: 0, roman: 'I', title: 'The Ash Garden', subtitle: 'The first Anchor sleeps beneath the roots.',
    map: 'arena_a', tint: 0x64667c, hpMul: 1, dmgMul: 1,
    steps: [
      { type: 'survive', duration: 170, text: 'Survive the tide', hint: 'WASD to move · your arrows fire on their own · Space: dash',
        waves: [
          S(1, 28, 1.7, { ferr: 1 }, 3),
          B(14, { ferr: 1 }, 8, 'arc', undefined, 'Swarm'),
          B(22, { mord: 1 }, 5, 'arc'),
          S(28, 58, 1.25, { ferr: 3, mord: 1 }, 4),
          B(40, { lodo: 1 }, 3, 'cluster'),
          S(58, 86, 0.95, { ferr: 4, mord: 2, lodo: 0.5 }, 5),
          B(70, { ferr: 1 }, 26, 'ring', undefined, 'Scarlet siege'),
          S(86, 130, 0.75, { ferr: 5, mord: 3, carap: 0.4, hermit: 0.4 }, 6),
          B(96, { carap: 1, ferr: 2 }, 10, 'line'),
          B(110, { hermit: 1 }, 4, 'arc', undefined, 'Coral hermits'),
          B(120, { lodo: 1, mord: 1 }, 10, 'arc'),
          S(130, 170, 0.6, { ferr: 6, mord: 3, lodo: 0.6, carap: 0.5, hermit: 0.5 }, 6),
          B(145, { ferr: 1, mord: 1 }, 34, 'ring', undefined, 'The tide rises'),
        ] },
      { type: 'reach', text: 'Follow the ember to the Anchor', hint: 'The golden arrow points the way', loop: 6,
        waves: [S(0, 6, 1.4, { ferr: 3, mord: 1 }, 4)] },
      { type: 'channel', duration: 16, text: 'Rekindle the Anchor', hint: 'Stay inside the circle of light · Q: Crown Pulse',
        waves: [
          S(0, 16, 0.55, { ferr: 4, mord: 2 }, 5),
          B(2.5, { lodo: 1 }, 4, 'arc'),
          B(6, { ferr: 1 }, 22, 'ring', undefined, 'The tide answers'),
          B(11, { carap: 1, hermit: 1 }, 3, 'cluster'),
        ] },
      { type: 'elite', elite: 'guard', text: 'Defeat the Coral Warden', hint: 'Break its armour and dodge the spike cone', loop: 9,
        waves: [S(0, 9, 2.4, { ferr: 2, mord: 1 }, 3)] },
      { type: 'boss', boss: 'wyrm', text: 'The Ash Wyrm rises', hint: 'Avoid the fire cone · when it burrows, leave the marked mounds', loop: 12,
        waves: [S(2, 12, 3.4, { ferr: 2, mord: 1 }, 3)] },
      { type: 'portal', text: 'Step through the ember portal', loop: 8, waves: [S(2, 8, 3, { ferr: 1 }, 3)] },
    ],
  },
  {
    id: 1, roman: 'II', title: 'The Glass Wood', subtitle: 'Crystals sing where the trees died.',
    map: 'arena_b', tint: 0x52707a, hpMul: 1.45, dmgMul: 1.15,
    steps: [
      { type: 'survive', duration: 150, text: 'Cross the wood',
        waves: [
          S(0, 35, 1.15, { ferr: 3, vesp: 1 }, 4),
          B(12, { vesp: 1 }, 6, 'arc', undefined, 'Glass flight'),
          B(26, { sapo: 1 }, 3, 'cluster'),
          S(35, 150, 0.75, { ferr: 4, mord: 2, vesp: 1.5, sapo: 0.6, wisp: 0.8, hermit: 0.4 }, 5),
          B(45, { wisp: 1 }, 6, 'arc', undefined, 'Ember wisps: keep your distance'),
          B(55, { ferr: 1, mord: 1 }, 32, 'ring', undefined, 'Siege'),
          B(72, { golem: 1 }, 2, 'line', undefined, 'Glass golems'),
          B(84, { vesp: 1 }, 10, 'arc'),
          B(110, { sapo: 1, carap: 1, golem: 0.5 }, 6, 'arc'),
          B(128, { ferr: 1, vesp: 1, wisp: 1 }, 36, 'ring', undefined, 'Full flight'),
        ] },
      { type: 'elite', elite: 'sacer', text: 'Defeat the Glass Priestess', hint: 'Leave the marked zones before they erupt', loop: 10,
        waves: [S(0, 10, 2.0, { ferr: 3, vesp: 1 }, 4)] },
      { type: 'reach', text: 'Reach the Anchor behind the crystals', loop: 6, waves: [S(0, 6, 1.2, { ferr: 3, vesp: 1 }, 4)] },
      { type: 'channel', duration: 18, text: 'Rekindle the second Anchor',
        waves: [
          S(0, 18, 0.5, { ferr: 4, mord: 2, vesp: 1.5, wisp: 0.6 }, 5),
          B(3, { sapo: 1 }, 4, 'arc'),
          B(7, { ferr: 1, mord: 1 }, 30, 'ring', undefined, 'The tide answers'),
          B(12, { carap: 1, golem: 1 }, 3, 'cluster'),
        ] },
      { type: 'boss', boss: 'frog', text: 'The Colossal Batrach awakens', hint: 'Watch its shadow: it marks where it will land', loop: 12,
        waves: [S(2, 12, 3.2, { mord: 1, ferr: 2 }, 3)] },
      { type: 'portal', text: 'Descend into the Sanctum', loop: 8, waves: [] },
    ],
  },
  {
    id: 2, roman: 'III', title: 'The Sunken Sanctum', subtitle: 'At the bottom, the heart of the rift beats.',
    map: 'arena_c', tint: 0x5e5e88, hpMul: 2.1, dmgMul: 1.3,
    steps: [
      { type: 'survive', duration: 150, text: 'Hold out in the Sanctum waters',
        waves: [
          S(0, 30, 0.85, { ferr: 4, mord: 2, suss: 1, mite: 1 }, 5),
          B(10, { suss: 1 }, 5, 'arc', undefined, 'Whispers'),
          B(22, { lodo: 1, carap: 1 }, 5, 'line'),
          S(30, 150, 0.5, { ferr: 6, mord: 3, vesp: 1.5, suss: 1, sapo: 0.7, lodo: 0.5, wisp: 1, golem: 0.3, hermit: 0.4 }, 7),
          B(40, { ferr: 1, mord: 1 }, 36, 'ring', undefined, 'Total tide'),
          B(62, { vesp: 1, wisp: 1 }, 12, 'arc'),
          B(80, { knight: 1 }, 1, 'cluster', undefined, 'An Ash Knight joins the tide'),
          B(100, { ferr: 1, mord: 1, suss: 1 }, 44, 'ring', undefined, 'The rift overflows'),
          B(125, { carap: 1, lodo: 1, golem: 1 }, 8, 'line'),
        ] },
      { type: 'boss', boss: 'colossus', text: 'The Glass Colossus blocks the way', hint: 'Fists land on the marked circles · crystal rain follows', loop: 12,
        waves: [S(3, 12, 3.6, { ferr: 2, mite: 2 }, 4)] },
      { type: 'reach', text: 'Climb to the altar of the last Anchor', loop: 6, waves: [S(0, 6, 1.0, { ferr: 3, suss: 1 }, 4)] },
      { type: 'channel', duration: 20, text: 'Rekindle the final Anchor',
        waves: [
          S(0, 20, 0.42, { ferr: 5, mord: 2, vesp: 1, suss: 1, wisp: 0.8 }, 6),
          B(3, { carap: 1 }, 3, 'arc'),
          B(7, { ferr: 1, mord: 1 }, 40, 'ring', undefined, 'The rift screams'),
          B(13, { sapo: 1, lodo: 1, golem: 1 }, 6, 'cluster'),
        ] },
      { type: 'boss', boss: 'heart', text: 'Destroy the Heart of the Veil', hint: 'Every pattern has a gap: find it', loop: 14,
        waves: [S(3, 14, 3.6, { ferr: 2, suss: 1 }, 3)] },
      { type: 'victory', text: 'The Veil is sealed', waves: [] },
    ],
  },
];
