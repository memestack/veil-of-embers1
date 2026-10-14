import './styles/main.css';
import { Game } from './game/Game';

/** Entry point: starts the game and shows failures readably. */
const game = new Game();
game.start().catch((err: unknown) => {
  console.error(err);
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;inset:0;display:grid;place-items:center;color:#ffd27a;background:#07060b;font:16px serif;padding:20px;text-align:center;z-index:99';
  const webgl = (() => {
    try {
      return !!document.createElement('canvas').getContext('webgl2');
    } catch {
      return false;
    }
  })();
  box.textContent = webgl
    ? `Could not start the game: ${String(err)}`
    : 'This browser does not support WebGL 2, which Veil of Embers requires. Enable hardware acceleration or use a modern browser.';
  document.body.appendChild(box);
});
