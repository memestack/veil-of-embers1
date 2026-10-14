"""
Terreno das arenas (tiles de 32 px), desenhado em camadas:
  solo (base escura)  ->  trilha de paralelepípedos / praça de blocos (sobrepostas, bordas irregulares)
  ->  penhascos / água (sobrepostos, contorno orgânico, face vertical voltada ao sul).
As bordas são auto-encaixadas por máscara de vizinhos (N=1, E=2, S=4, W=8) e o perfil irregular
começa e termina na mesma altura nos cantos, então tiles vizinhos emendam sem costura.
"""
import math
import numpy as np
from PIL import Image
from pix import hx, mix, darken

T = 32
RNG_SEED = 9001

PAL = {
    'a': dict(ground='#25272e', ground2='#2a2c34', speck='#1d1e24', cobble='#3b3d47', cobble_hi='#4a4c57', grout='#18191e',
              brick='#363844', brick_hi='#444654', brick_lo='#2a2b34', wall='#14151a', wall2='#1a1b21', rim='#4a4b58', face='#0e0f13',
              face_hi='#2c2d36', moss='#27463f', accent='#8c3a32'),
    'b': dict(ground='#1b2a2e', ground2='#1f3034', speck='#152125', cobble='#30454a', cobble_hi='#3e575c', grout='#11191c',
              brick='#2f4246', brick_hi='#3c5357', brick_lo='#243437', wall='#0d171a', wall2='#112024', rim='#3f6b6c', face='#091114',
              face_hi='#1f3a3c', moss='#2b5a55', accent='#3fd6d2'),
    'c': dict(ground='#21233a', ground2='#25283f', speck='#1a1b2e', cobble='#353852', cobble_hi='#434763', grout='#14152a',
              brick='#33354f', brick_hi='#41446a', brick_lo='#272940', wall='#0b2230', wall2='#0e2a3a', rim='#4fa0b4', face='#081a24',
              face_hi='#1d4c5e', moss='#2a4a52', accent='#b0703c'),
}


def _rgb(c):
    return np.array(hx(c), np.float32)


def _profile(t, n_seed, base=3.0, amp=1.6):
    """Perfil irregular contínuo: vale `base` nos cantos (t=0 e t=1)."""
    r = np.random.default_rng(n_seed)
    p = np.full_like(t, base)
    for n in (2, 3, 5, 7):
        p += r.uniform(-amp, amp) / (n * 0.6) * np.sin(math.pi * n * t)
    return p


def _edge_depth(mask: int, seed: int, base=3.0, amp=1.6):
    """Para cada pixel: quanto ele está 'dentro' da borda irregular mais próxima (negativo = fora)."""
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    yy += 0.5
    xx += 0.5
    depth = np.full((T, T), 99.0, np.float32)
    t_x = xx / T
    t_y = yy / T
    if mask & 1:  # norte
        depth = np.minimum(depth, yy - _profile(t_x, seed + 1, base, amp))
    if mask & 4:  # sul
        depth = np.minimum(depth, (T - yy) - _profile(t_x, seed + 3, base, amp))
    if mask & 8:  # oeste
        depth = np.minimum(depth, xx - _profile(t_y, seed + 7, base, amp))
    if mask & 2:  # leste
        depth = np.minimum(depth, (T - xx) - _profile(t_y, seed + 11, base, amp))
    return depth


def _grain(a, rng, colors, density):
    m = rng.random((T, T)) < density
    idx = rng.integers(0, len(colors), (T, T))
    for i, c in enumerate(colors):
        sel = m & (idx == i)
        a[sel, :3] = c
    return a


# ------------------------------------------------------------------- solo
def ground(arena: str, var: int) -> Image.Image:
    P = PAL[arena]
    rng = np.random.default_rng(100 + var + ord(arena) * 13)
    a = np.zeros((T, T, 4), np.float32)
    a[..., :3] = _rgb(P['ground'])
    a[..., 3] = 255
    # manchas grandes muito sutis (quebram a grade)
    yy, xx = np.mgrid[0:T, 0:T]
    for _ in range(2):
        cx, cy, r = rng.uniform(0, T), rng.uniform(0, T), rng.uniform(6, 14)
        for ox in (-T, 0, T):
            for oy in (-T, 0, T):
                d = np.hypot(xx - cx - ox, (yy - cy - oy) * 1.3)
                a[d < r, :3] = _rgb(P['ground2'])
    _grain(a, rng, [_rgb(P['speck']), _rgb(P['ground2']), mix(hx(P['ground']), hx(P['cobble']), 0.4)], 0.18)
    if var == 3:  # musgo raro
        cx, cy = rng.integers(6, 26, 2)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (1, 1), (2, 0)):
            a[(cy + dy) % T, (cx + dx) % T, :3] = _rgb(P['moss'])
    if var == 4:  # seixos
        for _ in range(3):
            x, y = rng.integers(2, 30, 2)
            a[y, x, :3] = _rgb(P['cobble_hi'])
            a[y + 1, x, :3] = _rgb(P['grout'])
    if var == 5:  # rachadura
        x, y = rng.integers(4, 12, 2)
        for i in range(10):
            a[min(T - 1, y + i // 2), min(T - 1, x + i), :3] = _rgb(P['speck'])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


# ------------------------------------------------------- paralelepípedos
def cobble(arena: str, mask: int, var: int) -> Image.Image:
    """Trilha de pedras irregulares assentadas (Voronoi autoral de sementes fixas por variante)."""
    P = PAL[arena]
    rng = np.random.default_rng(300 + var * 31 + ord(arena))
    pts = []
    for gy in range(4):
        for gx in range(4):
            pts.append((gx * 8 + 4 + rng.uniform(-2.2, 2.2), gy * 8 + 4 + rng.uniform(-2.2, 2.2)))
    pts = np.array(pts)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32) + 0.5
    best = np.full((T, T), 1e9)
    second = np.full((T, T), 1e9)
    owner = np.zeros((T, T), int)
    for i, (px, py) in enumerate(pts):
        for ox in (-T, 0, T):
            for oy in (-T, 0, T):
                d = np.hypot(xx - px - ox, (yy - py - oy) * 1.1)
                upd = d < best
                second = np.where(upd, best, np.minimum(second, d))
                owner = np.where(upd, i, owner)
                best = np.where(upd, d, best)
    edge = second - best
    a = np.zeros((T, T, 4), np.float32)
    shades = [mix(hx(P['cobble']), hx(P['cobble_hi']), rng.uniform(0, 0.6)) for _ in pts]
    for i in range(len(pts)):
        a[owner == i, :3] = shades[i]
    # bisel: luz no topo/esquerda da pedra, sombra embaixo
    lit = np.zeros((T, T), bool)
    for i, (px, py) in enumerate(pts):
        sel = owner == i
        lit |= sel & ((yy - py) < -2.2) & (edge > 1.2) & (edge < 2.6)
    a[lit, :3] = _rgb(P['cobble_hi'])
    a[edge < 1.25, :3] = _rgb(P['grout'])
    a[..., 3] = 255
    _grain(a, rng, [_rgb(P['grout'])], 0.04)
    if mask:
        depth = _edge_depth(mask, 50 + var * 3 + mask, base=3.5, amp=2.2)
        a[depth < 0, 3] = 0
        a[(depth >= 0) & (depth < 1.2), :3] = _rgb(P['grout'])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


# -------------------------------------------------------------- praça
def plaza(arena: str, mask: int, var: int) -> Image.Image:
    """Praça de blocos assentados em amarração (16x8), com bisel e blocos gastos."""
    P = PAL[arena]
    rng = np.random.default_rng(500 + var * 17 + ord(arena))
    a = np.zeros((T, T, 4), np.float32)
    a[..., 3] = 255
    a[..., :3] = _rgb(P['grout'])
    for row in range(4):
        off = 8 if row % 2 else 0
        for col in range(-1, 3):
            x0 = col * 16 + off
            y0 = row * 8
            shade = mix(hx(P['brick_lo']), hx(P['brick_hi']), rng.uniform(0.3, 0.6))
            if arena == 'c' and rng.random() < 0.05:
                shade = mix(hx(P['accent']), hx(P['brick']), 0.55)
            for y in range(y0 + 1, y0 + 8):
                for x in range(x0 + 1, x0 + 16):
                    if 0 <= x < T:
                        a[y, x, :3] = shade
            # bisel
            for x in range(x0 + 1, x0 + 16):
                if 0 <= x < T:
                    a[y0 + 1, x, :3] = mix(shade, hx(P['brick_hi']), 0.6)
                    a[y0 + 7, x, :3] = darken(shade, 0.25)
            if rng.random() < 0.25:  # trinca
                cx = x0 + rng.integers(3, 12)
                for k in range(3):
                    if 0 <= cx + k < T:
                        a[y0 + 3 + k % 2, cx + k, :3] = _rgb(P['grout'])
    _grain(a, rng, [_rgb(P['brick_lo'])], 0.05)
    if mask:
        depth = _edge_depth(mask, 70 + var * 5 + mask, base=3.0, amp=2.6)
        a[depth < 0, 3] = 0
        a[(depth >= 0) & (depth < 1.3), :3] = _rgb(P['grout'])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


# --------------------------------------------------------- penhasco/água
def cliff(arena: str, mask: int, var: int) -> Image.Image:
    """Massa sólida com contorno orgânico. `mask` = lados vizinhos de chão caminhável.
    Na arena C é água profunda com borda de espuma; nas demais, rocha com face vertical ao sul."""
    P = PAL[arena]
    rng = np.random.default_rng(700 + var * 7 + mask * 3 + ord(arena))
    water = arena == 'c'
    a = np.zeros((T, T, 4), np.float32)
    a[..., 3] = 255
    a[..., :3] = _rgb(P['wall'])
    yy, xx = np.mgrid[0:T, 0:T]
    # textura do topo
    if water:
        for _ in range(4):
            x, y, l = rng.integers(0, T), rng.integers(0, T), rng.integers(3, 8)
            for i in range(l):
                a[y, (x + i) % T, :3] = _rgb(P['wall2'])
        for _ in range(2):
            x, y = rng.integers(0, T), rng.integers(0, T)
            a[y, x, :3] = _rgb(P['face_hi'])
    else:
        for _ in range(3):
            cx, cy, r = rng.uniform(0, T), rng.uniform(0, T), rng.uniform(4, 9)
            for ox in (-T, 0, T):
                for oy in (-T, 0, T):
                    d = np.hypot(xx - cx - ox, (yy - cy - oy) * 1.2)
                    a[d < r, :3] = _rgb(P['wall2'])
        _grain(a, rng, [_rgb(P['face'])], 0.08)
        if arena == 'b' and rng.random() < 0.6:  # brotos de vidro no topo
            for _ in range(2):
                x, y = rng.integers(4, 28), rng.integers(8, 26)
                for k in range(4):
                    a[y - k, x, :3] = mix(hx(P['rim']), (255, 255, 255), 0.15 * k)
    if not mask:
        return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    face_h = 0 if water else 9
    side = mask & ~4
    depth = _edge_depth(side, 900 + var * 11 + mask, base=2.5, amp=2.0) if side else np.full((T, T), 99.0)
    if mask & 4:
        # o chão ao sul começa abaixo de uma borda irregular; acima dela, a face vertical do penhasco
        prof = _profile((xx + 0.5) / T, 1300 + var + mask, base=3.0 if water else 2.5, amp=1.8)
        south = (T - (yy + 0.5)) - prof
        depth = np.minimum(depth, south)
        if not water:
            face = (south >= 0) & (south < face_h)
            a[face, :3] = _rgb(P['face'])
            # estrias verticais e luz no topo da face
            for x in range(T):
                if (x + var * 3) % 5 == 0:
                    col = face[:, x]
                    a[col, x, :3] = darken(hx(P['face']), 0.4)
            top = (south >= face_h - 1.2) & (south < face_h)
            a[top, :3] = _rgb(P['face_hi'])
            rim = (south >= face_h) & (south < face_h + 1.2)
            a[rim, :3] = _rgb(P['rim'])
    a[depth < 0, 3] = 0
    rim2 = (depth >= 0) & (depth < 1.3)
    a[rim2, :3] = _rgb(P['rim'])
    if water:
        foam = (depth >= 1.3) & (depth < 2.4)
        a[foam, :3] = mix(hx(P['rim']), hx(P['wall']), 0.5)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def light_pool(size=160, bands=14):
    """Poça de luz suave (bandas finas) para iluminar o solo ao redor da heroína e das fontes de luz."""
    c = size / 2
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.hypot(xx - c + 0.5, yy - c + 0.5) / c
    v = np.clip(1 - d, 0, 1) ** 1.6
    v = np.floor(v * bands) / bands
    a = np.zeros((size, size, 4), np.uint8)
    a[..., 0] = 255
    a[..., 1] = 236
    a[..., 2] = 200
    a[..., 3] = (v * 255).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def darkness_hole(size=128, bands=12):
    """Máscara para o véu de escuridão: branco no centro (onde a luz 'fura' a escuridão)."""
    c = size / 2
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.hypot(xx - c + 0.5, yy - c + 0.5) / c
    v = np.clip(1 - d, 0, 1) ** 1.2
    v = np.floor(v * bands) / bands
    a = np.zeros((size, size, 4), np.uint8)
    a[..., :3] = 255
    a[..., 3] = (v * 255).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')
