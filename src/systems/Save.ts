/**
 * Local persistence (localStorage) with a schema version and safe recovery:
 * missing or corrupted data falls back to defaults without breaking the game.
 */
import type { Levels } from '../content/upgrades';

export const SAVE_VERSION = 1;
const KEY = 'veu-de-brasas.save';

export type Quality = 'low' | 'medium' | 'high';

export interface Settings {
  music: number;
  sfx: number;
  quality: Quality;
  reduceFlash: boolean;
  reduceShake: boolean;
  uiScale: number;
  manualAim: boolean;
  touchControls: 'auto' | 'on' | 'off';
}

export interface Checkpoint {
  act: number;
  levels: Levels;
  heroLevel: number;
  xp: number;
  hpFrac: number;
  stats: RunStatsData;
}

export interface RunStatsData {
  time: number;
  kills: number;
  damage: number;
  coins: number;
  actsDone: number;
}

export interface MetaData {
  coins: number;
  unlocked: string[];
  selectedSkin: string;
  enabledMods: string[];
  wins: number;
  bestTime: number;
  /** creature/boss ids met at least once (bestiary) */
  seen: string[];
  /** highest act reached (0..2), unlocks the campaign map */
  maxAct: number;
  runs: number;
  deaths: number;
  totalKills: number;
  bestKills: number;
  bestLevel: number;
  bossesSlain: number;
}

export interface SaveData {
  version: number;
  settings: Settings;
  meta: MetaData;
  checkpoint: Checkpoint | null;
}

export const DEFAULT_SETTINGS: Settings = {
  music: 0.6,
  sfx: 0.8,
  quality: 'high',
  reduceFlash: false,
  reduceShake: false,
  uiScale: 1,
  manualAim: false,
  touchControls: 'auto',
};

const DEFAULT: SaveData = {
  version: SAVE_VERSION,
  settings: { ...DEFAULT_SETTINGS },
  meta: { coins: 0, unlocked: ['skin_ember'], selectedSkin: 'skin_ember', enabledMods: [], wins: 0, bestTime: 0, seen: [], maxAct: 0, runs: 0, deaths: 0, totalKills: 0, bestKills: 0, bestLevel: 0, bossesSlain: 0 },
  checkpoint: null,
};

function isObj(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null;
}

/** Field-by-field merge, keeping only types compatible with the default. */
function mergeShallow<T extends object>(base: T, src: unknown): T {
  const out = { ...base } as Record<string, unknown>;
  if (!isObj(src)) return out as T;
  for (const k of Object.keys(base)) {
    const bv = (base as Record<string, unknown>)[k];
    const sv = src[k];
    if (sv === undefined) continue;
    if (Array.isArray(bv) ? Array.isArray(sv) : typeof bv === typeof sv) out[k] = sv;
  }
  return out as T;
}

export function migrate(raw: unknown): SaveData {
  if (!isObj(raw)) return structuredClone(DEFAULT);
  const settings = mergeShallow(DEFAULT.settings, raw.settings);
  const meta = mergeShallow(DEFAULT.meta, raw.meta);
  if (!meta.unlocked.includes('skin_ember')) meta.unlocked.push('skin_ember');
  meta.seen = meta.seen.filter((x) => typeof x === 'string');
  meta.maxAct = Math.max(0, Math.min(2, Math.floor(meta.maxAct)));
  let checkpoint: Checkpoint | null = null;
  const cp = raw.checkpoint;
  if (isObj(cp) && typeof cp.act === 'number' && cp.act >= 0 && cp.act <= 2 && isObj(cp.levels)) {
    checkpoint = {
      act: cp.act,
      levels: Object.fromEntries(Object.entries(cp.levels).filter(([, v]) => typeof v === 'number')) as Levels,
      heroLevel: typeof cp.heroLevel === 'number' ? cp.heroLevel : 1,
      xp: typeof cp.xp === 'number' ? cp.xp : 0,
      hpFrac: typeof cp.hpFrac === 'number' ? Math.max(0.3, Math.min(1, cp.hpFrac)) : 1,
      stats: mergeShallow({ time: 0, kills: 0, damage: 0, coins: 0, actsDone: 0 }, cp.stats),
    };
  }
  return { version: SAVE_VERSION, settings, meta, checkpoint };
}

class SaveStore {
  data: SaveData = structuredClone(DEFAULT);

  load(): void {
    try {
      const txt = localStorage.getItem(KEY);
      this.data = txt ? migrate(JSON.parse(txt)) : structuredClone(DEFAULT);
    } catch {
      this.data = structuredClone(DEFAULT);
    }
  }

  save(): void {
    try {
      localStorage.setItem(KEY, JSON.stringify(this.data));
    } catch {
      /* storage unavailable (private mode): the game keeps running without saving */
    }
  }
}

export const store = new SaveStore();

/** Reliquary: meta-progression unlocks (cosmetics and light modifiers, no mandatory grind). */
export interface MetaItem {
  id: string;
  kind: 'skin' | 'mod';
  name: string;
  desc: string;
  cost: number;
  icon: string;
  tint?: number;
}

export const META_ITEMS: MetaItem[] = [
  { id: 'skin_ember', kind: 'skin', name: 'Ember Crown', desc: 'The original circlet, in glowing gold.', cost: 0, icon: 'w_crown', tint: 0xffffff },
  { id: 'skin_frost', kind: 'skin', name: 'Ash-Blue Crown', desc: 'Cold flames, the colour of moonlight on glass.', cost: 60, icon: 'w_crown', tint: 0x9ad8ff },
  { id: 'skin_jade', kind: 'skin', name: 'Solar Jade Crown', desc: 'Green-gold fire from the ancient gardens.', cost: 120, icon: 'w_crown', tint: 0xb8ff9a },
  { id: 'mod_reroll', kind: 'mod', name: 'Second Reading', desc: '+1 card reroll per run.', cost: 80, icon: 'm_reroll' },
  { id: 'mod_basalt', kind: 'mod', name: 'Kindled Start', desc: 'Start with +15% max health.', cost: 100, icon: 'u_hp' },
  { id: 'mod_wind', kind: 'mod', name: 'Inherited Gust', desc: 'Start the run with Cinder Wind level 1.', cost: 150, icon: 'w_wind' },
];
