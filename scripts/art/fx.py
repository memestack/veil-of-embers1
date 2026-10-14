"""
VFX autorais: Coroa de Brasas, projéteis, raios, cristais, vento, explosões,
telegraphs, partículas, coletáveis e dígitos de dano. Brilhos usam bandas de
cor posterizadas (pixel art), não gradientes suaves.
"""
import math
import numpy as np
from PIL import Image
from pix import Sprite, mat, mat_glow, Mat, ramp, hx, mix, darken

TAU = math.tau

FIRE = [(110, 20, 20), (200, 60, 24), (255, 130, 40), (255, 200, 90), (255, 246, 214)]
ICE = [(20, 70, 110), (40, 150, 190), (90, 220, 230), (180, 250, 250), (250, 255, 255)]
VOLT = [(60, 40, 140), (110, 110, 255), (170, 200, 255), (225, 240, 255), (255, 255, 255)]
WIND = [(70, 70, 80), (130, 130, 140), (190, 186, 180), (230, 226, 214), (255, 250, 240)]
HOLY = [(120, 70, 20), (210, 140, 40), (255, 210, 110), (255, 240, 190), (255, 255, 250)]
DANGER = [(110, 10, 20), (190, 30, 40), (240, 70, 60), (255, 140, 110), (255, 220, 200)]
SPIRIT = [(40, 40, 120), (70, 90, 200), (120, 170, 255), (200, 230, 255), (255, 255, 255)]


def banded(W, H, fn, pal, alpha_floor=0.0):
    """Imagem a partir de campo escalar 0..1 quantizado na paleta (0 = transparente)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = fn(xx + 0.5, yy + 0.5)
    v = np.nan_to_num(np.clip(v, 0, 1))
    out = np.zeros((H, W, 4), np.uint8)
    n = len(pal)
    idx = np.clip((v * n).astype(int), 0, n)
    for i in range(1, n + 1):
        m = idx == i
        out[m, :3] = pal[i - 1]
        out[m, 3] = 255
    # banda mais externa semitransparente para assentar no cenário
    m = idx == 1
    out[m, 3] = 170
    return Image.fromarray(out, 'RGBA')


def glow(size, pal, power=1.4):
    c = size / 2
    return banded(size, size, lambda x, y: np.clip(1 - np.hypot(x - c, y - c) / c, 0, 1) ** power * 1.05, pal)


# ----------------------------------------------------------- Coroa de Brasas
def crown_flame(i):
    """Língua de fogo da coroa (aponta para cima; o jogo gira tangente à órbita)."""
    W, H = 20, 28
    ph = i / 6 * TAU

    def f(x, y):
        u = (x - W / 2) / (W / 2)
        v = (H - y) / H  # 0 base, 1 topo
        width = (1 - v) ** 0.7 * (0.95 + 0.1 * math.sin(ph + v * 6))
        sway = math.sin(ph + v * 5) * 0.22 * v
        d = 1 - abs(u - sway) / max(0.05, width)
        flick = 0.15 * math.sin(ph * 2 + v * 11)
        return d * (1.15 - v * 0.55 + flick)
    return banded(W, H, np.vectorize(f), FIRE)


def crown_ring(level):
    """Anel de runas gravadas (64x64) — a quantidade de runas comunica o nível."""
    S = 72
    img = np.zeros((S, S, 4), np.uint8)
    c = S / 2 - 0.5
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx - c, yy - c)
    band = (r > 29) & (r < 31.2)
    img[band] = (200, 110, 40, 210)
    band2 = (r > 33) & (r < 34.2)
    img[band2] = (255, 190, 90, 150)
    glyphs = [
        [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 2)],
        [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 2), (1, 1), (2, 0), (0, 0), (2, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)],
        [(1, 0), (0, 1), (2, 1), (1, 2), (1, 1)],
    ]
    n = 4 + level * 2
    for k in range(n):
        a = k / n * TAU
        gx, gy = c + math.cos(a) * 31.5, c + math.sin(a) * 31.5
        for (dx, dy) in glyphs[k % len(glyphs)]:
            x, y = int(gx + dx - 1), int(gy + dy - 1)
            if 0 <= x < S and 0 <= y < S:
                img[y, x] = (255, 236, 170, 255)
    return Image.fromarray(img, 'RGBA')


def fire_ring(i):
    """Aro de fogo em perspectiva (elipse) — a assinatura visual da Coroa de Brasas. 4 quadros de chama."""
    W, H = 104, 56
    cx, cy = W / 2, H / 2 + 2
    ph = i / 4 * TAU

    def f(x, y):
        dx, dy = (x - cx) / 46, (y - cy) / 21
        r = math.hypot(dx, dy)
        a = math.atan2(dy, dx)
        tongue = 0.035 * math.sin(a * 9 + ph) + 0.025 * math.sin(a * 17 - ph * 2)
        # chamas sobem: a borda superior da elipse fica mais alta
        up = max(0, -(y - cy)) / 21 * 0.05
        d = abs(r - 1.0 - tongue * 0.6 + up)
        return (1 - d / (0.13 + 0.05 * (1 + math.sin(a * 5 + ph)))) * 1.15
    return banded(W, H, np.vectorize(f), FIRE)


def ember(i):
    pal = FIRE
    size = [3, 5, 7, 5][i]
    W = 8
    img = np.zeros((W, W, 4), np.uint8)
    c = W // 2
    for y in range(W):
        for x in range(W):
            d = abs(x - c) + abs(y - c)
            if d <= size // 2:
                col = pal[4] if d == 0 else (pal[3] if d == 1 else pal[2])
                img[y, x] = (*col, 255)
    return Image.fromarray(img, 'RGBA')


# --------------------------------------------------------------- projéteis
def arrow(level=0):
    s = Sprite(22, 9)
    s.limb([(2, 4.5), (15, 4.5)], 0.7, 0.7, mat('#c98a34', n=4), ex=0.3)
    s.poly([(14, 2), (21, 4.5), (14, 7)], Mat(ramp('#ffd27a', 4, spread=0.5), emissive=True), ex=0.4)
    s.poly([(1, 2), (5, 4.5), (1, 7), (3, 4.5)], mat('#e8dcc0', n=3), ex=0.3)
    img = s.render()
    a = np.asarray(img).copy()
    for x in (7, 10):
        a[4, x, :3] = (255, 230, 150)
    return Image.fromarray(a, 'RGBA')


def lance(i):
    W, H = 56, 14
    ph = i / 4 * TAU

    def f(x, y):
        u = x / W
        cy = H / 2 + math.sin(ph + u * 9) * 0.6 * (1 - u)
        w = (0.25 + 0.75 * u ** 0.6) * H / 2 * (1 if u < 0.92 else (1 - u) / 0.08)
        d = 1 - abs(y - cy) / max(0.1, w)
        return d * (0.55 + 0.6 * u) + 0.08 * math.sin(ph * 2 + u * 20)
    return banded(W, H, np.vectorize(f), FIRE)


def bolt_segment(i):
    """Segmento de raio (16px) — o jogo encadeia vários entre dois pontos."""
    W, H = 16, 12
    rng = np.random.default_rng(31 + i)
    ys = [6] + list(6 + rng.integers(-4, 5, 3)) + [6]
    xs = [0, 4, 8, 12, 16]
    img = np.zeros((H, W, 4), np.uint8)
    for k in range(4):
        x0, y0, x1, y1 = xs[k], ys[k], xs[k + 1], ys[k + 1]
        n = 12
        for j in range(n + 1):
            t = j / n
            x = int(min(W - 1, x0 + (x1 - x0) * t)); y = int(round(y0 + (y1 - y0) * t))
            for dy, col, al in ((-1, VOLT[1], 200), (1, VOLT[1], 200), (0, VOLT[4], 255)):
                yy = y + dy
                if 0 <= yy < H and img[yy, x, 3] < al:
                    img[yy, x] = (*col, al)
    return Image.fromarray(img, 'RGBA')


def spark(i):
    S = 16; c = 7.5
    rays = 4 + (i % 2) * 2
    L = [3, 7, 6, 3][i]

    def f(x, y):
        a = math.atan2(y - c, x - c); r = math.hypot(x - c, y - c)
        ray = abs(math.cos(a * rays / 2)) ** 8
        return max((1 - r / (L + 0.01)) * 1.2 * (0.3 + ray), (1 - r / 2.2) if i < 3 else 0)
    return banded(S, S, np.vectorize(f), HOLY)


def crystal_seed():
    s = Sprite(14, 14)
    s.poly([(7, 1), (12, 7), (7, 13), (2, 7)], Mat(ramp('#7ae8ff', 5, spread=0.5), spec=0.8), ex=0.4)
    s.px(6, 5, '#ffffff'); s.px(6, 6, '#ffffff')
    return s.render()


def crystal_shard():
    s = Sprite(12, 8)
    s.poly([(1, 4), (6, 1), (11, 4), (6, 7)], Mat(ramp('#9af0ff', 4, spread=0.5), spec=0.8), ex=0.4)
    return s.render()


def crystal_burst(i):
    S = 56; c = S / 2
    r0 = 6 + i * 5

    def f(x, y):
        r = math.hypot(x - c, y - c); a = math.atan2(y - c, x - c)
        spikes = abs(math.cos(a * 4)) ** 4
        ring = 1 - abs(r - r0) / (3.5 + spikes * 3)
        return ring * (1.1 - i * 0.12)
    return banded(S, S, np.vectorize(f), ICE)


def wind_crescent(i):
    S = 56; c = S / 2
    r0 = 12 + i * 4

    def f(x, y):
        r = math.hypot(x - c, y - c); a = math.atan2(y - c, x - c)  # 0 = direita
        if abs(a) > 1.35:
            return 0
        thick = 4.0 * math.cos(a * 1.1)
        return (1 - abs(r - r0) / max(0.5, thick)) * (1.05 - i * 0.13) * (0.7 + 0.3 * math.cos(a * 6 + i))
    return banded(S, S, np.vectorize(f), WIND)


def fire_tornado(i):
    W, H = 28, 44
    ph = i / 6 * TAU

    def f(x, y):
        v = 1 - y / H
        cx = W / 2 + math.sin(ph + v * 7) * (2 + v * 3)
        w = 2.5 + v * 9
        d = 1 - abs(x - cx) / w
        bands = 0.75 + 0.35 * math.sin(v * 22 - ph * 3 + (x - cx) * 0.4)
        return d * bands * (1.1 - v * 0.25)
    return banded(W, H, np.vectorize(f), FIRE)


def explosion(i, pal=FIRE):
    S = 56; c = S / 2
    t = (i + 1) / 7
    r_out = 6 + t * 22

    def f(x, y):
        r = math.hypot(x - c, y - c); a = math.atan2(y - c, x - c)
        wob = 1 + 0.12 * math.sin(a * 7 + i)
        core = (1 - r / (r_out * wob)) * (1.4 - t)
        hole = r < (t - 0.45) * r_out * 1.4
        return 0 if hole else core
    return banded(S, S, np.vectorize(f), pal)


def heal_fx(i):
    S = 16
    img = np.zeros((S, S, 4), np.uint8)
    yoff = 10 - i * 2
    for (x, y) in ((7, 0), (7, 1), (7, 2), (6, 1), (8, 1)):
        if 0 <= y + yoff < S:
            img[y + yoff, x] = (180, 255, 200, 255)
    img[min(S - 1, yoff + 1), 7] = (255, 255, 255, 255)
    for (x, y) in ((3, 6), (12, 9), (10, 3)):
        yy = (y + 12 - i * 3) % S
        img[yy, x] = (120, 240, 170, 200)
    return Image.fromarray(img, 'RGBA')


def smoke(i):
    s = Sprite(20, 20)
    r = 4 + i * 1.6
    M = Mat(ramp('#5a5462', 4, spread=0.4), alpha=0.75 - i * 0.12)
    s.ellipse(10, 11 - i, r, r * 0.85, M, ex=0.6, edge=False)
    s.ellipse(7, 9 - i, r * 0.6, r * 0.5, M, ex=0.6, edge=False)
    return s.render(outline=False)


def dash_streak():
    W, H = 40, 10
    return banded(W, H, np.vectorize(lambda x, y: (x / W) * (1 - abs(y - H / 2) / (1 + 4 * x / W))), HOLY)


def telegraph_ring():
    S = 96; c = S / 2 - 0.5
    img = np.zeros((S, S, 4), np.uint8)
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx - c, yy - c); a = np.arctan2(yy - c, xx - c)
    edge = (r > 44) & (r < 47.5)
    dash = (np.floor((a + math.pi) / TAU * 24) % 2) == 0
    img[edge & dash] = (255, 90, 70, 255)
    img[edge & ~dash] = (170, 30, 40, 200)
    inner = r < 44
    img[inner] = (200, 30, 40, 60)
    hatch = inner & (((xx + yy) % 8) == 0)
    img[hatch] = (240, 70, 60, 110)
    return Image.fromarray(img, 'RGBA')


def telegraph_cone():
    """Cone de 60° apontando para a direita, origem à esquerda-centro."""
    W, H = 96, 96
    img = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = xx - 0.0, yy - H / 2
    r = np.hypot(dx, dy); a = np.arctan2(dy, dx)
    inside = (np.abs(a) < math.radians(30)) & (r < 94)
    edge = inside & ((np.abs(np.abs(a) - math.radians(30)) < 0.05) | (r > 90))
    img[inside] = (200, 40, 40, 60)
    img[inside & (((xx - yy) % 8) == 0)] = (240, 80, 60, 110)
    img[edge] = (255, 110, 80, 240)
    return Image.fromarray(img, 'RGBA')


def telegraph_line():
    W, H = 64, 16
    img = np.zeros((H, W, 4), np.uint8)
    img[2:14] = (200, 40, 40, 60)
    img[2] = (255, 110, 80, 230); img[13] = (255, 110, 80, 230)
    for x in range(0, W, 8):
        img[3:13, x:x + 2] = (240, 80, 60, 110)
    return Image.fromarray(img, 'RGBA')


def chunk(i):
    img = np.zeros((6, 6, 4), np.uint8)
    shapes = [[(2, 2), (3, 2), (2, 3), (3, 3)], [(1, 2), (2, 2), (3, 2), (2, 3)], [(2, 1), (2, 2), (3, 3)], [(1, 1), (2, 2), (3, 3), (4, 4)]]
    for (x, y) in shapes[i]:
        img[y, x] = (255, 255, 255, 255)
    return Image.fromarray(img, 'RGBA')


def beam(i):
    W, H = 40, 120
    ph = i / 4 * TAU

    def f(x, y):
        v = y / H
        w = 7 + 3 * math.sin(ph + v * 10)
        return (1 - abs(x - W / 2) / w) * (0.6 + 0.6 * v)
    return banded(W, H, np.vectorize(f), HOLY)


def shockwave(i):
    S = 112; c = S / 2
    r0 = 10 + i * 12

    def f(x, y):
        r = math.hypot(x - c, (y - c) * 1.6)
        return (1 - abs(r - r0) / 4.5) * (1.1 - i * 0.18)
    return banded(S, S, np.vectorize(f), HOLY)


def boss_wave(i):
    S = 112; c = S / 2
    r0 = 10 + i * 12

    def f(x, y):
        r = math.hypot(x - c, (y - c) * 1.6)
        return (1 - abs(r - r0) / 5) * (1.1 - i * 0.16)
    return banded(S, S, np.vectorize(f), [(30, 60, 70), (40, 110, 120), (90, 200, 190), (170, 240, 230), (240, 255, 250)])


def orb(i, pal):
    S = 14; c = 6.5
    r = 5.2 + (i % 2) * 0.6
    return banded(S, S, lambda x, y: (1 - np.hypot(x - c, y - c) / r) * 1.3, pal)


def mudball(i):
    s = Sprite(18, 18)
    s.ellipse(9, 9, 6.5 + (i % 2) * 0.4, 6, mat('#3e8a7a', spec=0.4), ex=0.7)
    s.ellipse(9, 10, 3, 2.6, mat_glow('#fff0b0', '#ff7a2a'), edge=False)
    return s.render()


def coral_spike():
    s = Sprite(16, 8)
    s.poly([(1, 2), (15, 4), (1, 6)], mat('#e05a48', spec=0.5, n=4), ex=0.4)
    return s.render()


def levelup(i):
    S = 72; c = S / 2
    t = (i + 1) / 6

    def f(x, y):
        r = math.hypot(x - c, y - c); a = math.atan2(y - c, x - c)
        star = abs(math.cos(a * 4)) ** 10
        ring = 1 - abs(r - t * 32) / 3
        rays = (1 - r / (12 + 24 * t)) * star * (1.3 - t)
        return max(ring * (1.2 - t), rays)
    return banded(S, S, np.vectorize(f), HOLY)


def vignette():
    W, H = 160, 90

    def f(x, y):
        u = (x - W / 2) / (W / 2); v = (y - H / 2) / (H / 2)
        d = math.sqrt(u * u * 0.8 + v * v)
        return max(0, (d - 0.72)) * 2.2
    pal = [(6, 4, 12)] * 5
    img = banded(W, H, np.vectorize(f), pal)
    a = np.asarray(img).copy()
    yy, xx = np.mgrid[0:H, 0:W]
    u = (xx - W / 2) / (W / 2); v = (yy - H / 2) / (H / 2)
    d = np.sqrt(u * u * 0.8 + v * v)
    alpha = np.clip((d - 0.72) * 2.2, 0, 1)
    alpha = np.floor(alpha * 5) / 5 * 200
    a[..., :3] = (6, 4, 12)
    a[..., 3] = alpha.astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


# ----------------------------------------------------------- coletáveis
def pickup_xp(size, i):
    cols = ['#ffbf4a', '#4fe0d0', '#b27aff'][size]
    s = Sprite(12, 14)
    k = [0.7, 0.9, 1.1][size]
    s.poly([(6, 7 - 6 * k), (6 + 3.5 * k, 7), (6, 7 + 6 * k), (6 - 3.5 * k, 7)], Mat(ramp(cols, 5, spread=0.55), spec=0.9), ex=0.45)
    img = s.render()
    a = np.asarray(img).copy()
    gl = [(5, 4), (6, 3), (7, 5), None][i]
    if gl:
        a[gl[1], gl[0]] = (255, 255, 255, 255)
    return Image.fromarray(a, 'RGBA')


def pickup_heart(i):
    s = Sprite(16, 16)
    sc = 1 + (0.08 if i == 1 else 0)
    M = Mat(ramp('#e0403a', 5, spread=0.5), spec=0.6)
    s.ellipse(5.5, 6.5, 3.4 * sc, 3.2 * sc, M, ex=0.6); s.ellipse(10.5, 6.5, 3.4 * sc, 3.2 * sc, M, ex=0.6)
    s.poly([(2.4, 7.5), (13.6, 7.5), (8, 14)], M, ex=0.5)
    s.ellipse(8, 9, 1.4, 1.4, mat_glow('#fff0b0', '#ff9a2a'), edge=False)
    return s.render()


def pickup_energy(i):
    s = Sprite(14, 14)
    s.ellipse(7, 7, 5 + (i % 2) * 0.5, 5 + (i % 2) * 0.5, mat_glow('#fff8d0', '#ff7a1a'), ex=0.7, edge=False)
    img = s.render()
    a = np.asarray(img).copy()
    for (x, y) in ((7, 3), (6, 7), (8, 7), (7, 10)):
        a[y, x] = (255, 255, 230, 255)
    return Image.fromarray(a, 'RGBA')


def pickup_coin(i):
    """Brasa de Âmbar (moeda de meta progressão)."""
    s = Sprite(14, 14)
    w = [5, 4, 2, 4][i]
    s.ellipse(7, 7, w, 5.5, Mat(ramp('#d9922e', 5, spread=0.55), spec=0.8), ex=0.6)
    if w > 3:
        s.ellipse(7, 7, w * 0.45, 2.4, mat_glow('#fff2b0', '#ff7a2a'), edge=False)
    return s.render()


def pickup_essence(i):
    s = Sprite(16, 18)
    M = Mat(ramp('#c070ff', 5, spread=0.55), spec=0.9)
    s.poly([(8, 1 + (i % 2)), (14, 8), (8, 17), (2, 8)], M, ex=0.45)
    s.poly([(8, 5), (11, 8), (8, 13), (5, 8)], mat_glow('#ffffff', '#e8a0ff'), ex=0.5, edge=False)
    return s.render()


def chest(open_=False):
    s = Sprite(28, 24)
    M = mat('#6a3e2a', n=4); M_B = mat('#c08a3a', spec=0.6, n=4)
    s.poly([(3, 10), (25, 10), (24, 22), (4, 22)], M, ex=0.3)
    if open_:
        s.poly([(3, 10), (25, 10), (23, 3), (5, 3)], M, ex=0.3)
        s.ellipse(14, 10, 8, 2.4, mat_glow('#fff4c0', '#ffaa3a'), edge=False)
    else:
        s.poly([(2, 11), (26, 11), (24, 4), (4, 4)], M, ex=0.4)
    s.poly([(12, 9), (16, 9), (16, 14), (12, 14)], M_B, ex=0.3)
    for x in (4, 23):
        s.poly([(x, 10), (x + 2, 10), (x + 2, 22), (x, 22)], M_B, ex=0.2)
    return s.render()


# ---------------------------------------------------------- dígitos de dano
DIGITS = {
    '0': ["0111", "1001", "1001", "1001", "1001", "1001", "0110"],
    '1': ["0010", "0110", "0010", "0010", "0010", "0010", "0111"],
    '2': ["0110", "1001", "0001", "0010", "0100", "1000", "1111"],
    '3': ["1110", "0001", "0001", "0110", "0001", "0001", "1110"],
    '4': ["1001", "1001", "1001", "1111", "0001", "0001", "0001"],
    '5': ["1111", "1000", "1110", "0001", "0001", "1001", "0110"],
    '6': ["0110", "1000", "1000", "1110", "1001", "1001", "0110"],
    '7': ["1111", "0001", "0010", "0010", "0100", "0100", "0100"],
    '8': ["0110", "1001", "1001", "0110", "1001", "1001", "0110"],
    '9': ["0110", "1001", "1001", "0111", "0001", "0001", "0110"],
    '+': ["0000", "0000", "0100", "1110", "0100", "0000", "0000"],
    '!': ["0100", "0100", "0100", "0100", "0100", "0000", "0100"],
}


def digit(ch):
    g = DIGITS[ch]
    img = np.zeros((9, 6, 4), np.uint8)
    for y, row in enumerate(g):
        for x, b in enumerate(row):
            if b == '1':
                img[y + 1, x + 1] = (255, 255, 255, 255)
    # contorno escuro
    sol = img[..., 3] > 0
    out = img.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)):
        sh = np.zeros_like(sol)
        sh[max(dy, 0):9 + min(dy, 0), max(dx, 0):6 + min(dx, 0)] = sol[max(-dy, 0):9 + min(-dy, 0), max(-dx, 0):6 + min(-dx, 0)]
        m = sh & ~sol
        out[m] = (20, 8, 16, 255)
    # sombreado inferior do glifo
    for y in range(9):
        for x in range(6):
            if sol[y, x] and y >= 5:
                out[y, x, :3] = (205, 205, 215)
    return Image.fromarray(out, 'RGBA')


def ground_fire(i):
    W, H = 40, 24
    ph = i / 4 * TAU

    def f(x, y):
        dx, dy = (x - W / 2) / 18, (y - H / 2) / 9
        r = math.hypot(dx, dy)
        lick = 0.25 * math.sin(x * 0.9 + ph * 2) * (1 - r)
        return (1 - r) * 1.1 + lick
    return banded(W, H, np.vectorize(f), FIRE)


def sky_bolt(i):
    W, H = 24, 121
    rng = np.random.default_rng(77 + i)
    xs = [12]
    for _ in range(11):
        xs.append(int(np.clip(xs[-1] + rng.integers(-4, 5), 3, 20)))
    img = np.zeros((H, W, 4), np.uint8)
    for k in range(11):
        y0, y1 = k * 11, (k + 1) * 11
        for y in range(y0, y1):
            t = (y - y0) / 11
            x = int(round(xs[k] + (xs[k + 1] - xs[k]) * t))
            for dx, col, al in ((-2, VOLT[1], 140), (2, VOLT[1], 140), (-1, VOLT[3], 230), (1, VOLT[3], 230), (0, VOLT[4], 255)):
                xx = x + dx
                if 0 <= xx < W and img[y, xx, 3] < al:
                    img[y, xx] = (*col, al)
    return Image.fromarray(img, 'RGBA')


def falling_shard():
    s = Sprite(12, 22)
    s.poly([(6, 21), (10, 6), (6, 1), (2, 6)], Mat(ramp('#8ef0ff', 5, spread=0.5), spec=0.9), ex=0.4)
    return s.render()


def spore(i):
    img = np.zeros((6, 6, 4), np.uint8)
    pts = [[(2, 2), (3, 2), (2, 3), (3, 3)], [(2, 2), (3, 3)], [(3, 2)], [(2, 3), (3, 3), (2, 2)]][i]
    for (x, y) in pts:
        img[y, x] = (255, 255, 255, 255)
    return Image.fromarray(img, 'RGBA')


def all_fx():
    F = {}
    F['crown_flame'] = [crown_flame(i) for i in range(6)]
    F['crown_ring'] = [crown_ring(l) for l in range(4)]
    F['fire_ring'] = [fire_ring(i) for i in range(4)]
    F['ground_fire'] = [ground_fire(i) for i in range(4)]
    F['sky_bolt'] = [sky_bolt(i) for i in range(4)]
    F['falling_shard'] = [falling_shard()]
    F['spore'] = [spore(i) for i in range(4)]
    F['ember'] = [ember(i) for i in range(4)]
    F['arrow'] = [arrow()]
    F['lance'] = [lance(i) for i in range(4)]
    F['bolt'] = [bolt_segment(i) for i in range(4)]
    F['spark'] = [spark(i) for i in range(4)]
    F['crystal_seed'] = [crystal_seed()]
    F['crystal_shard'] = [crystal_shard()]
    F['crystal_burst'] = [crystal_burst(i) for i in range(5)]
    F['wind'] = [wind_crescent(i) for i in range(5)]
    F['tornado'] = [fire_tornado(i) for i in range(6)]
    F['explosion'] = [explosion(i) for i in range(7)]
    F['explosion_ice'] = [explosion(i, ICE) for i in range(7)]
    F['explosion_volt'] = [explosion(i, VOLT) for i in range(7)]
    F['heal'] = [heal_fx(i) for i in range(4)]
    F['smoke'] = [smoke(i) for i in range(4)]
    F['dash_streak'] = [dash_streak()]
    F['tele_ring'] = [telegraph_ring()]
    F['tele_cone'] = [telegraph_cone()]
    F['tele_line'] = [telegraph_line()]
    F['chunk'] = [chunk(i) for i in range(4)]
    F['beam'] = [beam(i) for i in range(4)]
    F['shockwave'] = [shockwave(i) for i in range(5)]
    F['boss_wave'] = [boss_wave(i) for i in range(5)]
    F['orb_spirit'] = [orb(i, SPIRIT) for i in range(2)]
    F['orb_danger'] = [orb(i, DANGER) for i in range(2)]
    F['mudball'] = [mudball(i) for i in range(2)]
    F['coral_spike'] = [coral_spike()]
    F['levelup'] = [levelup(i) for i in range(6)]
    F['glow_fire'] = [glow(64, FIRE)]
    F['glow_ice'] = [glow(64, ICE)]
    F['glow_holy'] = [glow(64, HOLY)]
    F['glow_spirit'] = [glow(64, SPIRIT)]
    F['glow_danger'] = [glow(64, DANGER)]
    F['vignette'] = [vignette()]
    F['xp_s'] = [pickup_xp(0, i) for i in range(4)]
    F['xp_m'] = [pickup_xp(1, i) for i in range(4)]
    F['xp_l'] = [pickup_xp(2, i) for i in range(4)]
    F['heart'] = [pickup_heart(i) for i in range(2)]
    F['energy'] = [pickup_energy(i) for i in range(2)]
    F['coin'] = [pickup_coin(i) for i in range(4)]
    F['essence'] = [pickup_essence(i) for i in range(2)]
    F['chest'] = [chest(False), chest(True)]
    for ch in DIGITS:
        F['digit_' + ('plus' if ch == '+' else 'bang' if ch == '!' else ch)] = [digit(ch)]
    return F
