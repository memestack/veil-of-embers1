import { Container, Sprite, Texture } from 'pixi.js';
import { assets } from '../game/AssetLoader';

/**
 * Damage numbers built from pixel-art digits (own atlas, no Canvas text).
 * Count is capped; the combat system groups small hits before showing them.
 */
class Num {
  c = new Container();
  digits: Sprite[] = [];
  life = 0;
  max = 0.8;
  vy = -38;
  x = 0;
  y = 0;
  alive = false;
  scale = 1;
}

export class DamageNumbers {
  private pool: Num[] = [];
  private live: Num[] = [];
  private tex: Record<string, Texture> = {};
  max = 40;

  constructor(private readonly layer: Container) {
    for (const ch of '0123456789') this.tex[ch] = assets.tex('fx', `digit_${ch}`);
    this.tex['+'] = assets.tex('fx', 'digit_plus');
    this.tex['!'] = assets.tex('fx', 'digit_bang');
  }

  show(x: number, y: number, value: number, tint = 0xffffff, big = false, prefix = ''): void {
    if (this.live.length >= this.max) {
      // recycle the oldest
      const old = this.live.shift()!;
      old.alive = false;
      old.c.visible = false;
      this.pool.push(old);
    }
    const n = this.pool.pop() ?? new Num();
    if (n.c.parent !== this.layer) this.layer.addChild(n.c);
    const text = prefix + String(Math.max(1, Math.round(value))) + (big ? '!' : '');
    while (n.digits.length < text.length) {
      const s = new Sprite(Texture.EMPTY);
      n.digits.push(s);
      n.c.addChild(s);
    }
    for (let i = 0; i < n.digits.length; i++) {
      const s = n.digits[i];
      if (i < text.length) {
        s.texture = this.tex[text[i]];
        s.x = i * 5 - text.length * 2.5;
        s.y = -4;
        s.tint = tint;
        s.visible = true;
      } else s.visible = false;
    }
    n.x = x + (Math.random() - 0.5) * 8;
    n.y = y;
    n.life = 0;
    n.max = big ? 1.0 : 0.7;
    n.vy = big ? -46 : -36;
    n.scale = big ? 1.5 : 1;
    n.alive = true;
    n.c.visible = true;
    this.live.push(n);
  }

  update(dt: number): void {
    for (let i = this.live.length - 1; i >= 0; i--) {
      const n = this.live[i];
      n.life += dt;
      if (n.life >= n.max) {
        n.alive = false;
        n.c.visible = false;
        this.live.splice(i, 1);
        this.pool.push(n);
        continue;
      }
      n.vy *= Math.exp(-3 * dt);
      n.y += n.vy * dt;
      const t = n.life / n.max;
      const pop = t < 0.12 ? 1 + (0.12 - t) * 4 : 1;
      n.c.scale.set(n.scale * pop);
      n.c.alpha = t > 0.6 ? 1 - (t - 0.6) / 0.4 : 1;
      n.c.position.set(Math.round(n.x), Math.round(n.y));
    }
  }

  clear(): void {
    for (const n of this.live) {
      n.alive = false;
      n.c.visible = false;
      this.pool.push(n);
    }
    this.live.length = 0;
  }
}
