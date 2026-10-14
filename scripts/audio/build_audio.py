"""
Síntese autoral de música e efeitos do VÉU DE BRASAS (NumPy/SciPy -> WAV -> MP3 via ffmpeg).
Uso: python3 scripts/audio/build_audio.py
Todas as notas, timbres e arranjos estão escritos aqui; nada é amostrado de terceiros.
"""
import json
import os
import subprocess
import tempfile

import numpy as np
from scipy.signal import lfilter, butter, fftconvolve

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'assets', 'audio')
RNG = np.random.default_rng(1234)


# ------------------------------------------------------------------ básico
def t_(d):
    return np.arange(int(d * SR)) / SR


def note_hz(n):  # n: semitons a partir de A4
    return 440.0 * 2 ** (n / 12)


NOTES = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}


def hz(name: str) -> float:
    pc, octv = name[:-1], int(name[-1])
    return note_hz(NOTES[pc] + (octv - 4) * 12)


def env(n, a=0.005, d=0.1, s=0.6, r=0.2, dur=None):
    a_n = max(1, int(a * SR)); d_n = max(1, int(d * SR)); r_n = max(1, int(r * SR))
    total = n
    sus_n = max(0, total - a_n - d_n - r_n)
    e = np.concatenate([np.linspace(0, 1, a_n), np.linspace(1, s, d_n), np.full(sus_n, s), np.linspace(s, 0, r_n)])
    return e[:total] if len(e) >= total else np.pad(e, (0, total - len(e)))


def expdecay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def lp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), 'low')
    return lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), 'high')
    return lfilter(b, a, x)


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), min(0.99, hi / (SR / 2))], 'band')
    return lfilter(b, a, x)


def _phase(f, t):
    if np.ndim(f) == 0:
        return 2 * np.pi * f * t, float(f)
    f = np.broadcast_to(f, t.shape)
    return np.cumsum(2 * np.pi * f / SR), float(np.max(f))


def saw(f, t):
    ph, fmax = _phase(f, t)
    out = np.zeros_like(t)
    for k in range(1, 14):
        if fmax * k > SR / 2.2:
            break
        out += np.sin(ph * k) / k
    return out * 0.6


def square(f, t):
    out = np.zeros_like(t)
    for k in range(1, 16, 2):
        if f * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * f * k * t) / k
    return out * 0.7


def tri(f, t):
    return 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))


def noise(n):
    return RNG.uniform(-1, 1, n)


_IR_CACHE = {}


def reverb(x, size=1.6, mix=0.3, bright=4000):
    key = (size, bright)
    if key not in _IR_CACHE:
        n = int(size * SR)
        ir = noise(n) * np.exp(-np.arange(n) / SR / (size / 4.5))
        ir = lp(ir, bright)
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        _IR_CACHE[key] = ir / np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(x, _IR_CACHE[key])[: len(x)]
    return x * (1 - mix) + wet * mix * 0.9


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def soft(x, drive=1.4):
    return np.tanh(x * drive) / np.tanh(drive)


def write_mp3(name, x, stereo=False, kbps=96):
    os.makedirs(OUT, exist_ok=True)
    x = np.asarray(x, np.float64)
    if stereo and x.ndim == 1:
        x = np.stack([x, x], 1)
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
        f.write(pcm.tobytes())
        raw = f.name
    ch = 2 if (stereo or x.ndim == 2) else 1
    dst = os.path.join(OUT, name + '.mp3')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', str(ch), '-i', raw,
                    '-c:a', 'libmp3lame', '-b:a', f'{kbps}k', dst], check=True)
    os.unlink(raw)
    return dst


# --------------------------------------------------------------------- SFX
def sfx_arrow():
    n = int(0.28 * SR); t = t_(0.28)
    tw = np.sin(2 * np.pi * (520 - 240 * t / 0.28) * t) * expdecay(n, 0.05) * 0.5
    wh = bp(noise(n), 1500, 6000) * env(n, 0.01, 0.08, 0.3, 0.15) * 0.8
    return norm(tw + wh, 0.7)


def sfx_fire():
    n = int(0.6 * SR)
    base = lp(noise(n), 900) * env(n, 0.02, 0.2, 0.5, 0.3) * 1.2
    crack = np.zeros(n)
    for _ in range(18):
        p = RNG.integers(0, n - 800)
        crack[p:p + 300] += bp(noise(300), 2000, 8000) * expdecay(300, 0.002) * RNG.uniform(0.3, 1)
    return norm(base + crack, 0.75)


def sfx_pulse():
    n = int(0.9 * SR); t = t_(0.9)
    boom = np.sin(2 * np.pi * (110 * np.exp(-t * 3)) * t) * expdecay(n, 0.25)
    whoosh = lp(noise(n), 2400) * env(n, 0.01, 0.3, 0.3, 0.4)
    fire = np.pad(sfx_fire(), (0, n))[:n]
    return norm(reverb(soft(boom * 1.2 + whoosh * 0.8 + fire * 0.4), 1.2, 0.25), 0.9)


def sfx_lance():
    n = int(0.7 * SR); t = t_(0.7)
    roar = lp(noise(n), 2500) * env(n, 0.03, 0.2, 0.4, 0.35)
    tone = saw(180 + 120 * t, t) * env(n, 0.01, 0.2, 0.2, 0.3) * 0.4
    return norm(reverb(soft(roar + tone), 1.0, 0.2), 0.8)


def sfx_thunder():
    n = int(0.55 * SR)
    x = np.zeros(n)
    for k in range(6):
        p = int(k * 0.035 * SR)
        L = int(0.05 * SR)
        x[p:p + L] += hp(noise(L), 1500) * expdecay(L, 0.015)
    buzz = square(70, t_(0.55)) * expdecay(n, 0.12) * 0.4
    return norm(reverb(soft(x + buzz, 2.0), 1.2, 0.2), 0.8)


def sfx_glass():
    n = int(0.8 * SR); t = t_(0.8)
    x = np.zeros(n)
    for f in (2400, 3150, 3870, 4620, 5800):
        d = RNG.integers(0, int(0.06 * SR))
        L = n - d
        x[d:] += np.sin(2 * np.pi * f * RNG.uniform(0.97, 1.03) * t[:L]) * expdecay(L, RNG.uniform(0.08, 0.25)) * 0.3
    x += hp(noise(n), 4000) * expdecay(n, 0.04) * 0.6
    return norm(reverb(x, 1.4, 0.35, 9000), 0.7)


def sfx_wind():
    n = int(0.6 * SR); t = t_(0.6)
    x = noise(n)
    out = np.zeros(n)
    for i in range(0, n, 2048):
        fc = 500 + 2500 * np.sin(np.pi * i / n)
        seg = x[i:i + 2048]
        out[i:i + len(seg)] = bp(seg, fc * 0.6, fc * 1.6)
    return norm(out * env(n, 0.08, 0.2, 0.6, 0.3), 0.7)


def sfx_dash():
    n = int(0.25 * SR)
    x = bp(noise(n), 800, 5000) * env(n, 0.005, 0.06, 0.4, 0.15)
    return norm(x, 0.65)


def sfx_hurt():
    n = int(0.35 * SR); t = t_(0.35)
    thud = np.sin(2 * np.pi * (140 * np.exp(-t * 5)) * t) * expdecay(n, 0.12)
    grit = lp(noise(n), 1500) * expdecay(n, 0.05) * 0.6
    return norm(soft(thud + grit, 1.8), 0.85)


def sfx_die(var=0):
    n = int(0.3 * SR); t = t_(0.3)
    f0 = [380, 260][var]
    pop = np.sin(2 * np.pi * (f0 * np.exp(-t * 9)) * t) * expdecay(n, 0.06)
    squ = bp(noise(n), 600, 3000) * expdecay(n, 0.04) * 0.5
    return norm(pop + squ, 0.6)


def sfx_xp():
    n = int(0.3 * SR); t = t_(0.3)
    x = (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * expdecay(n, 0.07)
    return norm(x, 0.45)


def sfx_heal():
    t = t_(0.7); n = len(t)
    x = np.zeros(n)
    for i, f in enumerate((hz('C5'), hz('E5'), hz('G5'), hz('C6'))):
        d = int(i * 0.07 * SR)
        x[d:] += np.sin(2 * np.pi * f * t[: n - d]) * expdecay(n - d, 0.25) * 0.3
    return norm(reverb(x, 1.2, 0.3), 0.6)


def chord(notes, dur, tau=0.6, wave='sine', stagger=0.0):
    t = t_(dur); n = len(t)
    x = np.zeros(n)
    for i, nm in enumerate(notes):
        d = int(i * stagger * SR)
        f = hz(nm)
        w = np.sin(2 * np.pi * f * t[: n - d]) + 0.25 * np.sin(2 * np.pi * 2 * f * t[: n - d]) + 0.1 * tri(3 * f, t[: n - d])
        x[d:] += w * expdecay(n - d, tau)
    return x


def sfx_card_open():
    n = int(0.6 * SR)
    sweep = bp(noise(n), 600, 3000) * env(n, 0.15, 0.2, 0.3, 0.2) * 0.5
    return norm(reverb(sweep + chord(['A4', 'E5'], 0.6, 0.3) * 0.4, 1.3, 0.3), 0.6)


def sfx_card_select():
    return norm(reverb(chord(['D5', 'A5', 'D6'], 0.5, 0.18, stagger=0.03), 1.0, 0.25), 0.6)


def sfx_rare():
    x = chord(['F#4', 'A4', 'C#5', 'E5', 'A5'], 1.2, 0.5, stagger=0.06)
    shimmer = hp(noise(len(x)), 6000) * expdecay(len(x), 0.3) * 0.15
    return norm(reverb(x + shimmer, 1.8, 0.35), 0.7)


def sfx_legendary():
    x = chord(['D4', 'A4', 'D5', 'F#5', 'A5', 'D6'], 2.0, 0.9, stagger=0.08)
    t = t_(2.0)
    swell = saw(hz('D3'), t) * env(len(t), 0.4, 0.5, 0.4, 0.9) * 0.25
    shimmer = hp(noise(len(t)), 7000) * env(len(t), 0.3, 0.6, 0.3, 0.8) * 0.2
    return norm(reverb(soft(x + lp(swell, 2000) + shimmer), 2.4, 0.4), 0.85)


def sfx_anchor():
    t = t_(3.0); n = len(t)
    gong = sum(np.sin(2 * np.pi * f * t) * expdecay(n, tau) * a for f, tau, a in ((82, 1.6, 1), (164.6, 1.1, 0.5), (247, 0.9, 0.35), (391, 0.6, 0.2)))
    rise = sum(np.sin(2 * np.pi * hz(nm) * t) for nm in ('D5', 'A5', 'D6')) * np.clip(t / 2.2, 0, 1) ** 2 * expdecay(n, 1.5) * 0.25
    return norm(reverb(gong + rise, 2.8, 0.4), 0.9)


def sfx_victory():
    seq = [('D4', 0.0), ('F#4', 0.18), ('A4', 0.36), ('D5', 0.54)]
    t = t_(3.2); n = len(t)
    x = np.zeros(n)
    for nm, st in seq:
        d = int(st * SR)
        f = hz(nm)
        x[d:] += (saw(f, t[: n - d]) * 0.3 + np.sin(2 * np.pi * f * t[: n - d])) * env(n - d, 0.02, 0.3, 0.4, 1.5) * 0.4
    x += chord(['D3', 'A3', 'D4', 'F#4', 'A4'], 3.2, 1.4, stagger=0.0)[: n] * 0.5 * (t > 0.72)
    return norm(reverb(lp(soft(x), 5000), 2.4, 0.35), 0.85)


def sfx_defeat():
    seq = [('A3', 0.0), ('F3', 0.4), ('D3', 0.8), ('C#3', 1.2)]
    t = t_(3.0); n = len(t)
    x = np.zeros(n)
    for nm, st in seq:
        d = int(st * SR)
        x[d:] += (tri(hz(nm), t[: n - d]) + 0.3 * saw(hz(nm) / 2, t[: n - d])) * env(n - d, 0.05, 0.3, 0.5, 1.2) * 0.4
    return norm(reverb(lp(x, 1800), 2.6, 0.45), 0.8)


def sfx_ui_hover():
    t = t_(0.06)
    return norm(np.sin(2 * np.pi * 1760 * t) * expdecay(len(t), 0.015), 0.25)


def sfx_ui_click():
    t = t_(0.12)
    x = np.sin(2 * np.pi * 880 * t) * expdecay(len(t), 0.03) + hp(noise(len(t)), 3000) * expdecay(len(t), 0.006) * 0.4
    return norm(x, 0.45)


def sfx_croak():
    t = t_(1.2); n = len(t)
    f = 70 + 18 * np.sin(2 * np.pi * 7 * t)
    ph = np.cumsum(2 * np.pi * f / SR)
    x = np.sign(np.sin(ph)) * 0.6 + np.sin(ph * 2) * 0.4
    x = lp(x, 900) * env(n, 0.05, 0.3, 0.7, 0.4)
    return norm(reverb(soft(x, 2.0), 1.8, 0.3), 0.9)


def sfx_slam():
    t = t_(1.0); n = len(t)
    boom = np.sin(2 * np.pi * (70 * np.exp(-t * 2.5)) * t) * expdecay(n, 0.35)
    debris = lp(noise(n), 2500) * expdecay(n, 0.18) * 0.7
    return norm(reverb(soft(boom * 1.4 + debris, 2.2), 1.6, 0.25), 0.95)


def sfx_telegraph():
    t = t_(0.7); n = len(t)
    x = (np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 233 * t)) * env(n, 0.1, 0.2, 0.7, 0.2) * 0.4
    return norm(x * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t)), 0.5)


def sfx_explosion():
    t = t_(1.0); n = len(t)
    x = lp(noise(n), 1800) * expdecay(n, 0.25) + np.sin(2 * np.pi * (90 * np.exp(-t * 4)) * t) * expdecay(n, 0.2)
    return norm(reverb(soft(x, 2.0), 1.4, 0.25), 0.85)


def sfx_levelup():
    x = chord(['A4', 'C#5', 'E5', 'A5'], 0.9, 0.35, stagger=0.06)
    return norm(reverb(x, 1.6, 0.3), 0.65)


def sfx_spit():
    t = t_(0.4); n = len(t)
    x = lp(noise(n), 1400) * env(n, 0.01, 0.1, 0.3, 0.2) + np.sin(2 * np.pi * (300 * np.exp(-t * 6)) * t) * expdecay(n, 0.08)
    return norm(x, 0.7)


def sfx_summon():
    t = t_(1.0); n = len(t)
    x = sum(np.sin(2 * np.pi * f * t * (1 + 0.1 * t)) for f in (523, 659, 784)) * env(n, 0.3, 0.3, 0.4, 0.3) * 0.3
    return norm(reverb(x + hp(noise(n), 5000) * env(n, 0.3, 0.3, 0.2, 0.3) * 0.2, 1.8, 0.4), 0.6)


def sfx_portal():
    t = t_(1.6); n = len(t)
    x = sum(np.sin(2 * np.pi * hz(nm) * t) for nm in ('D4', 'A4', 'E5')) * np.clip(t / 0.8, 0, 1) * expdecay(n, 0.9) * 0.3
    return norm(reverb(x, 2.2, 0.4), 0.6)


# ------------------------------------------------------------------- música
def pluck(f, dur, bright=3000, tau=0.5):
    t = t_(dur)
    x = (saw(f, t) * 0.6 + np.sin(2 * np.pi * f * t)) * expdecay(len(t), tau)
    return lp(x, bright)


def pad(f, dur, bright=1200):
    t = t_(dur)
    x = saw(f, t) + saw(f * 1.005, t) + 0.5 * saw(f * 0.5, t)
    return lp(x, bright) * env(len(t), dur * 0.3, 0.2, 0.8, dur * 0.4) * 0.25


def bell(f, dur):
    t = t_(dur)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * expdecay(len(t), 0.4) + 0.3 * np.sin(2 * np.pi * f * 5.4 * t) * expdecay(len(t), 0.15)
    return x * expdecay(len(t), 1.2)


def kick(dur=0.4):
    t = t_(dur)
    return np.sin(2 * np.pi * (45 + 110 * np.exp(-t * 28)) * t) * expdecay(len(t), 0.16)


def tom(f=110, dur=0.4):
    t = t_(dur)
    return (np.sin(2 * np.pi * f * (1 + 0.6 * np.exp(-t * 20)) * t) + lp(noise(len(t)), 900) * 0.2) * expdecay(len(t), 0.18)


def shaker(dur=0.08):
    n = int(dur * SR)
    return hp(noise(n), 6000) * env(n, 0.005, 0.02, 0.3, 0.05) * 0.4


def snare(dur=0.25):
    t = t_(dur)
    return (bp(noise(len(t)), 1200, 7000) * 0.7 + np.sin(2 * np.pi * 190 * t) * 0.4) * expdecay(len(t), 0.07)


def place(buf, x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= buf.shape[0]:
        return
    seg = x[: buf.shape[0] - i] * gain
    L = np.cos((pan + 1) * np.pi / 4); R = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(seg), 0] += seg * L * 1.41
    buf[i:i + len(seg), 1] += seg * R * 1.41


def render_loop(build, length):
    """Renderiza duas voltas e devolve a segunda, para que caudas de reverb atravessem o ponto de loop."""
    buf = np.zeros((int(length * 2 * SR) + SR * 4, 2))
    build(buf, 0.0)
    build(buf, length)
    start = int(length * SR)
    return buf[start:start + int(length * SR)].copy()


def music_menu():
    bpm = 72; beat = 60 / bpm; bars = 16; L = bars * 4 * beat
    prog = [['D3', 'A3', 'F4'], ['A#2', 'F3', 'D4'], ['C3', 'G3', 'E4'], ['A2', 'E3', 'C#4']]
    arp = ['D5', 'F5', 'A5', 'E5', 'D5', 'C5', 'A4', 'C5']
    melody = [('A5', 0, 2), ('G5', 2, 1), ('F5', 3, 1), ('E5', 4, 3), ('D5', 8, 2), ('E5', 10, 1), ('F5', 11, 1),
              ('A5', 12, 4), ('C6', 16, 2), ('A#5', 18, 2), ('A5', 20, 4), ('G5', 24, 2), ('F5', 26, 2), ('E5', 28, 4)]

    def build(buf, off):
        for b in range(bars):
            ch = prog[(b // 2) % 4]
            if b % 2 == 0:
                for i, nm in enumerate(ch):
                    place(buf, reverb(pad(hz(nm), beat * 8 + 1.5, 900), 2.5, 0.5), off + b * 4 * beat, 0.5, -0.4 + i * 0.4)
            for k in range(8):
                nm = arp[(k + b * 3) % 8]
                place(buf, pluck(hz(nm), 1.4, 2500, 0.35), off + (b * 4 + k * 0.5) * beat, 0.16, 0.5 if k % 2 else -0.5)
        for rep in (0, 32):
            for nm, st, du in melody:
                if st + rep < bars * 4:
                    place(buf, reverb(bell(hz(nm), du * beat + 2), 3.0, 0.5), off + (st + rep) * beat, 0.16, 0.1)
    x = render_loop(build, L)
    return norm(x, 0.7), L


def music_combat(layer: str):
    """Duas camadas sincronizadas: 'base' (baixo, arpejo, pad) e 'drive' (percussão, metais)."""
    bpm = 112; beat = 60 / bpm; bars = 24; L = bars * 4 * beat
    roots = ['D2', 'D2', 'A#1', 'C2', 'D2', 'D2', 'F2', 'C2']
    arp_sets = [['D4', 'F4', 'A4', 'D5'], ['D4', 'F4', 'A4', 'D5'], ['A#3', 'D4', 'F4', 'A#4'], ['C4', 'E4', 'G4', 'C5'],
                ['D4', 'F4', 'A4', 'E5'], ['D4', 'G4', 'A#4', 'D5'], ['F4', 'A4', 'C5', 'F5'], ['C4', 'E4', 'G4', 'A#4']]

    def build(buf, off):
        for b in range(bars):
            tb = off + b * 4 * beat
            r = roots[b % 8]
            intensity = b / bars
            if layer == 'base':
                for k in range(8):
                    nm = r if k % 4 != 3 else r[:-1] + str(int(r[-1]) + 1)
                    place(buf, lp(saw(hz(nm), t_(beat * 0.45)) * env(int(beat * 0.45 * SR), 0.005, 0.08, 0.6, 0.08), 600 + 500 * intensity),
                          tb + k * 0.5 * beat, 0.35)
                arp = arp_sets[b % 8]
                for k in range(16):
                    nm = arp[(k * 3 + b) % 4]
                    place(buf, pluck(hz(nm), 0.5, 2200 + 1500 * intensity, 0.16), tb + k * 0.25 * beat, 0.11 + 0.05 * intensity,
                          -0.6 if k % 2 else 0.6)
                if b % 2 == 0:
                    place(buf, reverb(pad(hz(arp[0]) / 2, beat * 8 + 1, 800), 2.0, 0.45), tb, 0.35)
            else:
                for k in range(4):
                    place(buf, kick(), tb + k * beat, 0.7)
                    if k % 2 == 1:
                        place(buf, snare(), tb + k * beat, 0.35, 0.1)
                    for h in range(4):
                        place(buf, shaker(), tb + (k + h * 0.25) * beat, 0.25 if h % 2 else 0.14, 0.4)
                if b % 4 == 3:
                    for k, f in enumerate((180, 150, 120, 100)):
                        place(buf, tom(f), tb + (3 + k * 0.25) * beat, 0.5, -0.3 + k * 0.2)
                if b % 2 == 0:
                    for nm in ('D4', 'A4', 'D5'):
                        stab = lp(saw(hz(nm), t_(0.35)) + saw(hz(nm) * 1.01, t_(0.35)), 2500) * env(int(0.35 * SR), 0.01, 0.1, 0.5, 0.15)
                        place(buf, stab, tb + 2.5 * beat, 0.09)
    x = render_loop(build, L)
    return norm(soft(x * 1.1), 0.75), L


def music_boss():
    bpm = 126; beat = 60 / bpm; bars = 16; L = bars * 4 * beat
    roots = ['D2', 'D#2', 'D2', 'C2', 'D2', 'D#2', 'F2', 'C#2']

    def build(buf, off):
        for b in range(bars):
            tb = off + b * 4 * beat
            r = roots[b % 8]
            for k in range(16):
                place(buf, lp(saw(hz(r), t_(beat * 0.22)) * env(int(beat * 0.22 * SR), 0.003, 0.05, 0.6, 0.05), 900), tb + k * 0.25 * beat, 0.3)
            for k in range(4):
                place(buf, kick(), tb + k * beat, 0.8)
                place(buf, snare(), tb + (k + 0.5) * beat, 0.18 if k % 2 == 0 else 0.4)
            for k, f in enumerate((200, 170, 140, 120)) if b % 2 == 1 else []:
                place(buf, tom(f), tb + (2 + k * 0.5) * beat, 0.5)
            # metais graves dramáticos
            if b % 2 == 0:
                for nm in (r[:-1] + '3', 'A3', r[:-1] + '4'):
                    br = lp(saw(hz(nm), t_(beat * 3.5)) + saw(hz(nm) * 1.007, t_(beat * 3.5)), 1600) * env(int(beat * 3.5 * SR), 0.08, 0.3, 0.6, 0.5)
                    place(buf, br, tb, 0.12)
            # coro de sinos
            for k, nm in enumerate(('D5', 'D#5', 'A4', 'F5')):
                if (b + k) % 4 == 0:
                    place(buf, reverb(bell(hz(nm), 3), 2.5, 0.5), tb + k * beat, 0.12)
    x = render_loop(build, L)
    return norm(soft(x * 1.2), 0.78), L


SFX = {
    'arrow': sfx_arrow, 'fire': sfx_fire, 'pulse': sfx_pulse, 'lance': sfx_lance, 'thunder': sfx_thunder,
    'glass': sfx_glass, 'wind': sfx_wind, 'dash': sfx_dash, 'hurt': sfx_hurt, 'die1': lambda: sfx_die(0),
    'die2': lambda: sfx_die(1), 'xp': sfx_xp, 'heal': sfx_heal, 'card_open': sfx_card_open,
    'card_select': sfx_card_select, 'rare': sfx_rare, 'legendary': sfx_legendary, 'anchor': sfx_anchor,
    'victory': sfx_victory, 'defeat': sfx_defeat, 'ui_hover': sfx_ui_hover, 'ui_click': sfx_ui_click,
    'croak': sfx_croak, 'slam': sfx_slam, 'telegraph': sfx_telegraph, 'explosion': sfx_explosion,
    'levelup': sfx_levelup, 'spit': sfx_spit, 'summon': sfx_summon, 'portal': sfx_portal,
}

if __name__ == '__main__':
    manifest = {'sfx': [], 'music': {}}
    for name, fn in SFX.items():
        x = fn()
        x = np.concatenate([np.zeros(32), x, np.zeros(int(0.02 * SR))])
        write_mp3('sfx_' + name, x)
        manifest['sfx'].append(name)
        print('sfx', name, f'{len(x) / SR:.2f}s')
    for name, fn in (('menu', music_menu), ('combat_base', lambda: music_combat('base')),
                     ('combat_drive', lambda: music_combat('drive')), ('boss', music_boss)):
        x, L = fn()
        write_mp3('mus_' + name, x, stereo=True, kbps=128)
        manifest['music'][name] = round(L, 5)
        print('music', name, f'{L:.2f}s')
    with open(os.path.join(OUT, 'audio.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print('ok')
