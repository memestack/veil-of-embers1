/**
 * Scenery object properties: collider (circle at the feet), layer
 * (low = floor decal; high = depth-sorted) and ambient light.
 */
export interface PropDef {
  /** collider radius in px (0 = walk-through). */
  r: number;
  /** vertical offset of the collider centre from the foot. */
  oy?: number;
  layer: 'low' | 'tall';
  anchorY?: number;
  light?: { tex: 'glow_fire' | 'glow_ice' | 'glow_holy' | 'glow_spirit' | 'glow_danger'; scale: number; alpha: number; oy: number; flicker?: boolean };
}

export const PROPS: Record<string, PropDef> = {
  coral_a: { r: 7, layer: 'tall' },
  coral_b: { r: 7, layer: 'tall' },
  fungi_a: { r: 0, layer: 'low', light: { tex: 'glow_ice', scale: 1.1, alpha: 0.28, oy: -10 } },
  fungi_b: { r: 0, layer: 'low', light: { tex: 'glow_ice', scale: 1.0, alpha: 0.25, oy: -8 } },
  monument: { r: 24, oy: -6, layer: 'tall', light: { tex: 'glow_fire', scale: 1.6, alpha: 0.32, oy: -50, flicker: true } },
  ruin_a: { r: 11, layer: 'tall' },
  ruin_b: { r: 12, layer: 'tall' },
  roots: { r: 0, layer: 'low' },
  bones: { r: 0, layer: 'low' },
  lantern: { r: 4, layer: 'tall', light: { tex: 'glow_fire', scale: 1.15, alpha: 0.42, oy: -34, flicker: true } },
  lantern_off: { r: 4, layer: 'tall' },
  stele: { r: 9, layer: 'tall', light: { tex: 'glow_fire', scale: 0.5, alpha: 0.2, oy: -26 } },
  arch: { r: 0, layer: 'tall' },
  crystal_s: { r: 6, layer: 'tall', light: { tex: 'glow_ice', scale: 0.6, alpha: 0.18, oy: -10 } },
  crystal_m: { r: 10, layer: 'tall', light: { tex: 'glow_ice', scale: 0.9, alpha: 0.22, oy: -18 } },
  crystal_l: { r: 15, layer: 'tall', light: { tex: 'glow_ice', scale: 1.3, alpha: 0.26, oy: -28 } },
  crystal_v: { r: 10, layer: 'tall', light: { tex: 'glow_spirit', scale: 1.0, alpha: 0.26, oy: -18 } },
  tree_a: { r: 9, layer: 'tall', light: { tex: 'glow_ice', scale: 1.4, alpha: 0.18, oy: -70 } },
  tree_b: { r: 9, layer: 'tall', light: { tex: 'glow_ice', scale: 1.3, alpha: 0.16, oy: -66 } },
  pool: { r: 0, layer: 'low', anchorY: 0.5, light: { tex: 'glow_ice', scale: 1.2, alpha: 0.18, oy: -14 } },
  plank: { r: 0, layer: 'low', anchorY: 0.6 },
  shards: { r: 0, layer: 'low' },
  pillar: { r: 11, layer: 'tall' },
  pillar_broken: { r: 11, layer: 'tall' },
  kelp: { r: 0, layer: 'tall' },
  altar: { r: 0, layer: 'low', anchorY: 0.75 },
  rift: { r: 0, layer: 'low', anchorY: 0.55, light: { tex: 'glow_danger', scale: 3.4, alpha: 0.3, oy: -40, flicker: true } },
};
