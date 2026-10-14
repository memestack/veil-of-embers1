import { Container, RenderTexture, Sprite, Texture, type Renderer } from 'pixi.js';
import { assets } from '../game/AssetLoader';

/**
 * Darkness veil with light pools: every frame a half-resolution light map
 * (dark base + additive light "holes") is drawn over the world with multiply blending.
 * Result: a gloomy arena, warm pools on the heroine, lanterns, fungi and Anchors,
 * and spells (drawn above the veil) always readable.
 */
export class Lighting {
  readonly overlay: Sprite;
  private rt: RenderTexture;
  private scene = new Container();
  private base: Sprite;
  private holes: Sprite[] = [];
  private used = 0;
  private holeTex: Texture;
  private scale = 0.5;
  ambient = 0x55576a;
  enabled = true;

  constructor() {
    this.rt = RenderTexture.create({ width: 64, height: 64 });
    this.overlay = new Sprite(this.rt);
    this.overlay.blendMode = 'multiply';
    this.base = new Sprite(Texture.WHITE);
    this.scene.addChild(this.base);
    this.holeTex = assets.tex('fx', 'light_hole');
  }

  /** Fits the texture to the visible world frame (in screen px). */
  resize(screenW: number, screenH: number): void {
    const w = Math.max(16, Math.ceil(screenW * this.scale));
    const h = Math.max(16, Math.ceil(screenH * this.scale));
    if (this.rt.width !== w || this.rt.height !== h) this.rt.resize(w, h);
    this.base.width = w;
    this.base.height = h;
  }

  begin(): void {
    this.used = 0;
    this.base.tint = this.ambient;
  }

  /** Light in screen coordinates (CSS px), radius in CSS px, intensity 0..1, optional colour. */
  light(sx: number, sy: number, radius: number, intensity = 1, tint = 0xffffff): void {
    let h = this.holes[this.used];
    if (!h) {
      h = new Sprite(this.holeTex);
      h.anchor.set(0.5);
      h.blendMode = 'add';
      this.scene.addChild(h);
      this.holes.push(h);
    }
    this.used++;
    h.visible = true;
    h.position.set(sx * this.scale, sy * this.scale);
    h.scale.set((radius * 2 * this.scale) / 128);
    h.alpha = Math.min(1, intensity);
    h.tint = tint;
  }

  end(renderer: Renderer): void {
    for (let i = this.used; i < this.holes.length; i++) this.holes[i].visible = false;
    renderer.render({ container: this.scene, target: this.rt, clear: true });
  }

  /** Positions the veil (child of the world container) to exactly cover the screen. */
  place(worldX: number, worldY: number, zoom: number): void {
    this.overlay.position.set(-worldX / zoom, -worldY / zoom);
    this.overlay.scale.set(1 / (zoom * this.scale));
    this.overlay.visible = this.enabled;
  }

  destroy(): void {
    this.scene.destroy({ children: true });
    this.rt.destroy(true);
  }
}
