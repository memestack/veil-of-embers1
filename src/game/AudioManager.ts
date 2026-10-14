import { assets } from './AssetLoader';

/**
 * Web Audio: independent music and SFX buses, unlock after a user gesture,
 * per-window trigger limiting (avoids distortion in hordes) and
 * adaptive music (the combat "drive" layer grows with intensity).
 */
interface SfxRule {
  gain: number;
  /** minimum interval between triggers of the same sound (s). */
  gap: number;
  /** max simultaneous instances. */
  max: number;
}

const RULES: Record<string, SfxRule> = {
  arrow: { gain: 0.32, gap: 0.05, max: 4 },
  fire: { gain: 0.35, gap: 0.12, max: 3 },
  pulse: { gain: 0.8, gap: 0.2, max: 2 },
  lance: { gain: 0.55, gap: 0.1, max: 3 },
  thunder: { gain: 0.45, gap: 0.08, max: 3 },
  glass: { gain: 0.42, gap: 0.08, max: 3 },
  wind: { gain: 0.45, gap: 0.12, max: 2 },
  dash: { gain: 0.5, gap: 0.1, max: 2 },
  hurt: { gain: 0.7, gap: 0.15, max: 2 },
  die1: { gain: 0.22, gap: 0.035, max: 5 },
  die2: { gain: 0.26, gap: 0.05, max: 4 },
  xp: { gain: 0.16, gap: 0.03, max: 5 },
  heal: { gain: 0.5, gap: 0.2, max: 2 },
  card_open: { gain: 0.55, gap: 0.2, max: 1 },
  card_select: { gain: 0.6, gap: 0.1, max: 2 },
  rare: { gain: 0.55, gap: 0.2, max: 1 },
  legendary: { gain: 0.6, gap: 0.3, max: 1 },
  anchor: { gain: 0.85, gap: 0.5, max: 1 },
  victory: { gain: 0.8, gap: 1, max: 1 },
  defeat: { gain: 0.8, gap: 1, max: 1 },
  ui_hover: { gain: 0.35, gap: 0.04, max: 2 },
  ui_click: { gain: 0.5, gap: 0.04, max: 2 },
  croak: { gain: 0.75, gap: 0.5, max: 1 },
  slam: { gain: 0.8, gap: 0.2, max: 2 },
  telegraph: { gain: 0.4, gap: 0.25, max: 2 },
  explosion: { gain: 0.5, gap: 0.08, max: 3 },
  levelup: { gain: 0.6, gap: 0.3, max: 1 },
  spit: { gain: 0.5, gap: 0.1, max: 2 },
  summon: { gain: 0.5, gap: 0.3, max: 1 },
  portal: { gain: 0.6, gap: 0.5, max: 1 },
};

type Track = 'menu' | 'combat' | 'boss' | 'none';

export class AudioManager {
  ctx: AudioContext | null = null;
  private master!: GainNode;
  private musicBus!: GainNode;
  private sfxBus!: GainNode;
  private buffers: Record<string, AudioBuffer> = {};
  private lastPlay: Record<string, number> = {};
  private active: Record<string, number> = {};
  private musicNodes: { src: AudioBufferSourceNode; gain: GainNode; name: string }[] = [];
  private driveGain: GainNode | null = null;
  private current: Track = 'none';
  private wanted: Track = 'none';
  musicVolume = 0.6;
  sfxVolume = 0.8;
  muted = false;
  private decoding: Promise<void> | null = null;

  /** Creates the (suspended) context and decodes the already-fetched buffers. */
  init(): Promise<void> {
    if (this.decoding) return this.decoding;
    const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return Promise.resolve();
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.musicBus = this.ctx.createGain();
    this.sfxBus = this.ctx.createGain();
    const comp = this.ctx.createDynamicsCompressor();
    comp.threshold.value = -10;
    comp.ratio.value = 4;
    this.musicBus.connect(this.master);
    this.sfxBus.connect(this.master);
    this.master.connect(comp).connect(this.ctx.destination);
    this.applyVolumes();
    const ctx = this.ctx;
    this.decoding = Promise.all(
      Object.entries(assets.audio).map(async ([name, data]) => {
        try {
          this.buffers[name] = await ctx.decodeAudioData(data.slice(0));
        } catch (e) {
          console.warn('Failed to decode', name, e);
        }
      }),
    ).then(() => {
      if (this.wanted !== 'none') this.playMusic(this.wanted, true);
    });
    return this.decoding;
  }

  /** Called on any user gesture (autoplay policy). */
  unlock(): void {
    if (!this.ctx) void this.init();
    if (this.ctx && this.ctx.state === 'suspended') void this.ctx.resume();
  }

  applyVolumes(): void {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    this.master.gain.setTargetAtTime(this.muted ? 0 : 1, t, 0.05);
    this.musicBus.gain.setTargetAtTime(this.musicVolume * 0.55, t, 0.05);
    this.sfxBus.gain.setTargetAtTime(this.sfxVolume, t, 0.05);
  }

  play(name: string, opts: { rate?: number; gain?: number; pan?: number } = {}): void {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    const buf = this.buffers['sfx_' + name];
    if (!buf) return;
    const rule = RULES[name] ?? { gain: 0.5, gap: 0.05, max: 3 };
    const now = ctx.currentTime;
    if (now - (this.lastPlay[name] ?? -1) < rule.gap) return;
    if ((this.active[name] ?? 0) >= rule.max) return;
    this.lastPlay[name] = now;
    this.active[name] = (this.active[name] ?? 0) + 1;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = opts.rate ?? 1;
    const g = ctx.createGain();
    g.gain.value = rule.gain * (opts.gain ?? 1);
    let node: AudioNode = src.connect(g);
    if (opts.pan !== undefined && ctx.createStereoPanner) {
      const p = ctx.createStereoPanner();
      p.pan.value = Math.max(-1, Math.min(1, opts.pan));
      node = node.connect(p);
    }
    node.connect(this.sfxBus);
    src.onended = () => {
      this.active[name] = Math.max(0, (this.active[name] ?? 1) - 1);
    };
    src.start();
  }

  private loopSource(name: string, gain: number): { src: AudioBufferSourceNode; gain: GainNode; name: string } | null {
    const ctx = this.ctx;
    const buf = this.buffers['mus_' + name];
    if (!ctx || !buf) return null;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.loop = true;
    // compensates the MP3 encoder delay for a seamless loop
    const expected = assets.audioManifest.music[name] ?? buf.duration;
    const extra = buf.duration - expected;
    if (extra > 0.002) {
      const start = Math.min(extra, 1105 / buf.sampleRate);
      src.loopStart = start;
      src.loopEnd = start + expected;
    }
    const g = ctx.createGain();
    g.gain.value = 0;
    g.gain.setTargetAtTime(gain, ctx.currentTime, 0.6);
    src.connect(g).connect(this.musicBus);
    return { src, gain: g, name };
  }

  playMusic(track: Track, force = false): void {
    this.wanted = track;
    if (!this.ctx || (!force && track === this.current)) return;
    const ctx = this.ctx;
    for (const n of this.musicNodes) {
      n.gain.gain.setTargetAtTime(0, ctx.currentTime, 0.5);
      const s = n.src;
      setTimeout(() => {
        try {
          s.stop();
        } catch {
          /* already stopped */
        }
      }, 2500);
    }
    this.musicNodes = [];
    this.driveGain = null;
    this.current = track;
    if (track === 'none') return;
    const startAt = ctx.currentTime + 0.05;
    if (track === 'combat') {
      const base = this.loopSource('combat_base', 0.9);
      const drive = this.loopSource('combat_drive', 0.0);
      for (const n of [base, drive]) {
        if (!n) continue;
        n.src.start(startAt, n.src.loopStart);
        this.musicNodes.push(n);
      }
      if (drive) this.driveGain = drive.gain;
    } else {
      const n = this.loopSource(track, 0.9);
      if (n) {
        n.src.start(startAt, n.src.loopStart);
        this.musicNodes.push(n);
      }
    }
  }

  /** 0..1: combat intensity (horde density) drives the percussion layer. */
  setIntensity(v: number): void {
    if (!this.ctx || !this.driveGain) return;
    this.driveGain.gain.setTargetAtTime(Math.max(0, Math.min(1, v)) * 0.9, this.ctx.currentTime, 1.2);
  }

  /** Ducks the music (pause / cards). */
  duck(on: boolean): void {
    if (!this.ctx) return;
    this.musicBus.gain.setTargetAtTime(this.musicVolume * 0.55 * (on ? 0.35 : 1), this.ctx.currentTime, 0.15);
  }
}

export const audio = new AudioManager();
