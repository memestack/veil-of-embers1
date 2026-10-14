import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SpatialHash } from '../src/utils/SpatialHash';
import { CARDS, rollCards, eligibleCards } from '../src/content/upgrades';
import { deriveStats, xpToNext } from '../src/content/stats';
import { migrate, SAVE_VERSION } from '../src/systems/Save';
import { Rng, dir8 } from '../src/utils/math';

test('spatial hash only finds nearby neighbours', () => {
  const h = new SpatialHash<{ x: number; y: number; radius: number; alive: boolean }>(48);
  const a = { x: 10, y: 10, radius: 5, alive: true };
  const b = { x: 300, y: 300, radius: 5, alive: true };
  const c = { x: 30, y: 12, radius: 5, alive: false };
  [a, b, c].forEach((i) => h.insert(i));
  const near = h.query(0, 0, 20);
  assert.deepEqual(near, [a]);
  assert.equal(h.nearest(290, 290, 50), b);
  h.clear();
  assert.equal(h.query(10, 10, 20).length, 0);
});

test('card pool has 14+ cards with real descriptions', () => {
  assert.ok(CARDS.length >= 14);
  for (const c of CARDS) {
    for (let n = 1; n <= Math.min(c.max, 5); n++) assert.ok(c.desc(n).length > 10, `${c.id} level ${n}`);
  }
});

test('draws never repeat a card nor offer a maxed card', () => {
  const r = new Rng(42);
  const levels: Record<string, number> = { u_twin: 3, u_pierce: 3 };
  for (let i = 0; i < 300; i++) {
    const offer = rollCards(levels, 5, () => r.next());
    assert.equal(new Set(offer.map((c) => c.id)).size, offer.length);
    assert.ok(!offer.some((c) => c.id === 'u_twin' || c.id === 'u_pierce'));
    assert.equal(offer.length, 3);
  }
});

test('first pick always includes a new weapon', () => {
  const r = new Rng(7);
  for (let i = 0; i < 100; i++) assert.ok(rollCards({}, 2, () => r.next()).some((c) => c.kind === 'weapon'));
});

test('combos only appear with prerequisites', () => {
  const ids = (l: Record<string, number>) => eligibleCards(l, 10).map((c) => c.id);
  assert.ok(!ids({}).includes('c_shatter'));
  assert.ok(ids({ w_chain: 1, w_lotus: 1 }).includes('c_shatter'));
  assert.ok(ids({ w_wind: 1 }).includes('c_tornado'));
  assert.ok(ids({ w_lance: 1 }).includes('c_dawn'));
});

test('cards really change stats', () => {
  const base = deriveStats({});
  const up = deriveStats({ u_twin: 2, u_fury: 1, u_crown_big: 2, w_lance: 3, c_dawn: 1, u_focus: 1 });
  assert.equal(up.arrow.count, base.arrow.count + 2);
  assert.ok(up.dmgMul > base.dmgMul);
  assert.equal(up.crown.flames, base.crown.flames + 2);
  assert.equal(up.lance.count, 2);
  assert.ok(up.combos.dawn);
  assert.ok(up.cdMul < 1);
  assert.ok(xpToNext(10) > xpToNext(1));
});

test('corrupted or old saves are recovered safely', () => {
  const d = migrate({ settings: { music: 'loud', sfx: 0.3 }, meta: { coins: 12 }, checkpoint: { act: 9, levels: {} } });
  assert.equal(d.version, SAVE_VERSION);
  assert.equal(d.settings.music, 0.6);
  assert.equal(d.settings.sfx, 0.3);
  assert.equal(d.meta.coins, 12);
  assert.equal(d.checkpoint, null);
  assert.equal(migrate('garbage').meta.coins, 0);
  // v1.0 saves without the new meta fields get safe defaults
  assert.deepEqual(d.meta.seen, []);
  assert.equal(d.meta.maxAct, 0);
  assert.equal(migrate({ meta: { maxAct: 7, seen: ['ferr', 3] } }).meta.maxAct, 2);
  assert.deepEqual(migrate({ meta: { seen: ['ferr', 3] } }).meta.seen, ['ferr']);
});

test('8 directions', () => {
  assert.equal(dir8(0), 0);
  assert.equal(dir8(Math.PI / 2), 2);
  assert.equal(dir8(Math.PI), 4);
  assert.equal(dir8(-Math.PI / 2), 6);
});
