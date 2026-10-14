# Asset credits — Veil of Embers

No third-party graphics, music or sound effects are used at runtime. Everything in `public/assets/`
was generated for this project by the authored pipelines included in the repository.

## Made originally for the project

| Folder | Content | Source |
|---|---|---|
| `public/assets/characters/` | Rune archer: 3 views (front, back, mirrorable side), idle, walk, shoot, dash, hurt, death | `scripts/art/hero.py` |
| `public/assets/enemies/enemies.*` | 7 creatures (insects/arachnids/wasps pre-rendered in 8 directions; mire child, carapace, toad and wraith in 3/4 view), attack frames, hit flash and dissolve deaths | `scripts/art/enemies.py` |
| `public/assets/enemies/enemies2.*` | Ember Wisp (float/fuse), Coral Hermit (walk/hide), Glass Golem (walk/slam), Shard Mite (8 directions), Ash Knight (walk/wind-up/swing), all with hit flash and death | `scripts/art/creatures2.py` |
| `public/assets/enemies/elites.*` | Coral Warden (with and without armour) and Glass Priestess | `scripts/art/bigfoes.py` |
| `public/assets/enemies/boss_frog.*`, `boss_heart.*` | Colossal Batrach (2 phases × 5 poses) and Heart of the Veil (3 phases, tentacles) | `scripts/art/bigfoes.py` |
| `public/assets/enemies/boss_wyrm.*` | Ash Wyrm: head in 8 directions (closed/open jaw, 2 phases), body segments, tail, burrow mound, death | `scripts/art/creatures2.py` |
| `public/assets/enemies/boss_colossus.*` | Glass Colossus: idle, raise, slam and roar in 2 phases, hit flash, death | `scripts/art/creatures2.py` |
| `public/assets/environment/` | 3 layered tilesets (ground, cobble paths, brick plazas, jagged cliffs/water with 16 edge masks and variants), props, Anchors and portal | `scripts/art/terrain.py`, `scripts/art/env.py` |
| `public/assets/effects/` | Ember Crown (flames and rune rings), fire ring, burning ground, projectiles, lightning and sky bolts, crystals and falling shards, wind, tornado, explosions (fire/ice/lightning), telegraphs, light pools, spores, particles, pickups, damage digits, shadows, vignette | `scripts/art/fx.py` |
| `public/assets/ui/` | Card frames (Jade/Amethyst/Solar Gold), panels, buttons, bars, slots, cursor, 24 icons, logo, menu illustration, 18 bestiary portraits, 3 act illustrations | `scripts/art/ui.py` + `build_assets.py` |
| `public/assets/maps/` | 3 hand-drawn ASCII arenas with manually placed props, plazas, paths, spawn zones and objectives | `scripts/maps/build_maps.py` |
| `public/assets/audio/` | 3 music themes (menu, two-layer adaptive combat, boss) and 30 effects | `scripts/audio/build_audio.py` (own synthesis with NumPy/SciPy, encoded to MP3 with FFmpeg) |

**How the art was made:** no image generator or asset store was available in the environment. The art was drawn
as code: every character, creature and object is composed part by part (head, hood, legs, plates, crystals…) with
authored vector shapes, rasterised to clean pixels and shaded with custom hue-shifted colour ramps, selective
outlines, inner lines, ordered dithering on large pieces and pixel-level details (eyes, runes, highlights). Poses
and animation frames are written by hand in the scripts. Running `npm run assets` regenerates everything
deterministically.

## Third party

| Item | Author | Licence | Use / changes |
|---|---|---|---|
| **Lora** font (`public/assets/fonts/Lora-Variable.ttf`) | Cyreal | SIL Open Font License 1.1 | Interface text and logo (rasterised to pixel art, with banded gradient, outline and embers drawn on top) |
| **PixiJS 8** (npm dependency) | PixiJS contributors | MIT | WebGL rendering engine |

## Reference

The visual intensity (dense hordes, fire ring, rarity cards) was inspired by the description of a gameplay video of
*Magic Archer – RPG Game*. No character, logo, interface, name or asset from that product was copied.
