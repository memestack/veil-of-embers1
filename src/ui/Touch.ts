import { input } from '../game/InputManager';

/** Virtual stick (left side) + large Dash, Pulse and Pause buttons. */
export class TouchControls {
  private root: HTMLElement;
  private stick: HTMLElement;
  private knob: HTMLElement;
  private id: number | null = null;
  private ox = 0;
  private oy = 0;
  onPause: (() => void) | null = null;

  constructor() {
    this.root = document.createElement('div');
    this.root.id = 'touch';
    this.root.innerHTML = `<div class="zone"><div class="stick"><div class="knob"></div></div></div>
      <button class="tb pulse" aria-label="Crown Pulse">Q</button><button class="tb dash" aria-label="Dash">DASH</button>
      <button class="tb pause" aria-label="Pause">II</button>`;
    document.body.appendChild(this.root);
    const zone = this.root.querySelector<HTMLElement>('.zone')!;
    this.stick = this.root.querySelector<HTMLElement>('.stick')!;
    this.knob = this.root.querySelector<HTMLElement>('.knob')!;
    zone.addEventListener('pointerdown', (e) => {
      if (this.id !== null) return;
      this.id = e.pointerId;
      zone.setPointerCapture(e.pointerId);
      this.ox = e.clientX;
      this.oy = e.clientY;
      this.stick.style.display = 'block';
      this.stick.style.left = `${this.ox}px`;
      this.stick.style.top = `${this.oy - zone.getBoundingClientRect().top}px`;
      this.update(e.clientX, e.clientY);
    });
    zone.addEventListener('pointermove', (e) => {
      if (e.pointerId === this.id) this.update(e.clientX, e.clientY);
    });
    const end = (e: PointerEvent) => {
      if (e.pointerId !== this.id) return;
      this.id = null;
      input.touchActive = false;
      input.touchX = input.touchY = 0;
      this.stick.style.display = 'none';
    };
    zone.addEventListener('pointerup', end);
    zone.addEventListener('pointercancel', end);
    this.root.querySelector('.dash')!.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      input.virtualDash();
    });
    this.root.querySelector('.pulse')!.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      input.virtualPulse();
    });
    this.root.querySelector('.pause')!.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      this.onPause?.();
    });
  }

  private update(x: number, y: number): void {
    let dx = x - this.ox, dy = y - this.oy;
    const l = Math.hypot(dx, dy);
    const max = 50;
    if (l > max) {
      dx = (dx / l) * max;
      dy = (dy / l) * max;
    }
    this.knob.style.transform = `translate(${dx}px, ${dy}px)`;
    const k = Math.min(1, l / max);
    input.touchActive = l > 6;
    input.touchX = l > 0 ? (dx / max) * (k > 0.25 ? 1 : k * 4) : 0;
    input.touchY = l > 0 ? (dy / max) * (k > 0.25 ? 1 : k * 4) : 0;
  }

  set visible(v: boolean) {
    this.root.classList.toggle('on', v);
    document.body.classList.toggle('touch', v);
  }
}
