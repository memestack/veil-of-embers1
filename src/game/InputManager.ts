/**
 * Unified input: keyboard (WASD/arrows, Space, Q, Esc, 1-3), mouse (optional manual aim)
 * and touch (virtual stick + large buttons). "Pressed this frame" state is consumed
 * by the simulation via consume().
 */
export class InputManager {
  private down = new Set<string>();
  private pressed = new Set<string>();
  mouseX = 0;
  mouseY = 0;
  mouseActive = false;
  touchX = 0;
  touchY = 0;
  touchActive = false;
  private touchVirtual = { dash: false, pulse: false };
  onAnyKey: ((code: string) => void) | null = null;

  attach(): void {
    window.addEventListener('keydown', (e) => {
      if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.code)) e.preventDefault();
      if (!this.down.has(e.code)) this.pressed.add(e.code);
      this.down.add(e.code);
      this.onAnyKey?.(e.code);
    });
    window.addEventListener('keyup', (e) => this.down.delete(e.code));
    window.addEventListener('blur', () => this.down.clear());
    window.addEventListener('pointermove', (e) => {
      if (e.pointerType === 'mouse') {
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;
        this.mouseActive = true;
      }
    });
  }

  isDown(...codes: string[]): boolean {
    return codes.some((c) => this.down.has(c));
  }

  /** true only once per press. */
  consume(code: string): boolean {
    if (code === 'Space' && this.touchVirtual.dash) {
      this.touchVirtual.dash = false;
      return true;
    }
    if (code === 'KeyQ' && this.touchVirtual.pulse) {
      this.touchVirtual.pulse = false;
      return true;
    }
    if (this.pressed.has(code)) {
      this.pressed.delete(code);
      return true;
    }
    return false;
  }

  clearPressed(): void {
    this.pressed.clear();
    this.touchVirtual.dash = this.touchVirtual.pulse = false;
  }

  /** Normalised movement vector (keyboard + touch). */
  move(): { x: number; y: number } {
    let x = 0;
    let y = 0;
    if (this.isDown('KeyA', 'ArrowLeft')) x -= 1;
    if (this.isDown('KeyD', 'ArrowRight')) x += 1;
    if (this.isDown('KeyW', 'ArrowUp')) y -= 1;
    if (this.isDown('KeyS', 'ArrowDown')) y += 1;
    if (this.touchActive) {
      x += this.touchX;
      y += this.touchY;
    }
    const l = Math.hypot(x, y);
    if (l > 1) {
      x /= l;
      y /= l;
    }
    return { x, y };
  }

  virtualDash(): void {
    this.touchVirtual.dash = true;
  }
  virtualPulse(): void {
    this.touchVirtual.pulse = true;
  }
}

export const input = new InputManager();
