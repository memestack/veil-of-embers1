"""
Ambientes: tilesets (32x32) das três arenas, props e Âncoras.
As texturas de piso recebem pedras, rachaduras e musgo desenhados como partes;
o grão fino usa um hash determinístico por tile (detalhe de textura, não de mapa).
"""
import math
import numpy as np
from PIL import Image
from pix import Sprite, mat, mat_glow, Mat, ramp, hx, mix, darken

T = 32
TAU = math.tau


def _grain(img: Image.Image, seed: int, amt=10, density=0.18) -> Image.Image:
    a = np.asarray(img).astype(np.int16).copy()
    rng = np.random.default_rng(seed)
    m = rng.random(a.shape[:2]) < density
    d = rng.integers(-amt, amt + 1, a.shape[:2])
    for c in range(3):
        a[..., c] = np.where(m & (a[..., 3] > 0), a[..., c] + d, a[..., c])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def _wrap_parts(draw_fn):
    """Desenha a mesma composição deslocada para tornar o tile contínuo."""
    s = Sprite(T, T)
    for ox in (-T, 0, T):
        for oy in (-T, 0, T):
            draw_fn(s, ox, oy)
    return s


ARENAS = {
    'a': dict(ground='#2b2e36', ground2='#33363f', path='#3e3a3a', moss='#2d5a50', accent='#b23a32',
              wall='#1b1c24', wall_top='#2a2733', lip='#5d5662', fungus='#4fe0c8'),
    'b': dict(ground='#1d3236', ground2='#243e42', path='#3a3c44', moss='#2f6a66', accent='#3fd6d2',
              wall='#0f2026', wall_top='#18323a', lip='#4aa7aa', fungus='#7af0ff'),
    'c': dict(ground='#252836', ground2='#292c3c', path='#3a3442', moss='#2c4b52', accent='#c27a40',
              wall='#0c2a38', wall_top='#11384a', lip='#5aa6b8', fungus='#ffcf7a'),
}


def floor_tile(arena: str, variant: int) -> Image.Image:
    """Piso discreto: o fundo não compete com hordas e magias (detalhes raros e de baixo contraste)."""
    P = ARENAS[arena]
    base = Image.new('RGBA', (T, T), hx(P['ground']) + (255,))
    M_PATCH = Mat([mix(hx(P['ground']), hx(P['ground2']), k) for k in (0.3, 0.6, 0.85)], outline=hx(P['ground']))
    M_PEB = mat(P['ground2'], n=3, spread=0.22)
    M_MOSS = mat(P['moss'], n=3, spread=0.18)
    patch = [(9, 22, 9, 6), (22, 9, 8, 5), (16, 16, 11, 7), (6, 6, 7, 5), (25, 24, 7, 5), (14, 12, 10, 6)][variant % 6]

    def draw(s, ox, oy):
        x, y, rx, ry = patch
        s.ellipse(x + ox, y + oy, rx, ry, M_PATCH, ex=0.2, edge=False)
        if variant == 1:
            s.ellipse(24 + ox, 7 + oy, 1.4, 1.0, M_PEB, ex=0.5)
            s.ellipse(8 + ox, 20 + oy, 1.0, 0.8, M_PEB, ex=0.5)
        if variant == 3:
            s.ellipse(20 + ox, 22 + oy, 3.2, 1.8, M_MOSS, ex=0.3)
        if variant == 4:
            for (px, py) in ((12, 9), (14, 10), (11, 11)):
                s.ellipse(px + ox, py + oy, 0.9, 0.7, M_PEB, ex=0.5)
    s = _wrap_parts(draw)
    s.parts = [p for p in s.parts if p.mask.any()]
    base.alpha_composite(s.render(outline=False))
    out = _grain(base, 1000 + variant + ord(arena) * 7, 6, 0.32)
    if variant == 2:
        a = np.asarray(out).copy()
        for (x, y) in ((4, 4), (5, 5), (6, 5), (7, 6), (8, 7), (8, 8), (9, 9), (11, 9), (12, 10), (13, 10)):
            a[y % T, x % T, :3] = darken(hx(P['ground']), 0.35)
        out = Image.fromarray(a, 'RGBA')
    return out


def path_tile(arena: str, variant: int) -> Image.Image:
    return _soften(_path_tile(arena, variant), ARENAS[arena]['path'], 0.5 if arena != 'c' else 0.62)


def _soften(img: Image.Image, color: str, k: float) -> Image.Image:
    """Reduz o contraste do tile em direção à cor-base (trilhas não competem com a ação)."""
    a = np.asarray(img).astype(np.float32)
    a[..., :3] = a[..., :3] * (1 - k) + np.array(hx(color), np.float32) * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def _path_tile(arena: str, variant: int) -> Image.Image:
    P = ARENAS[arena]
    base = Image.new('RGBA', (T, T), hx(P['path']) + (255,))
    M_SLAB = mat(P['path'], n=4, spread=0.1, shift=0.05)
    if arena == 'c':
        # mosaico: losangos de cobre e pedra
        s = Sprite(T, T)
        M_COP = mat('#8a5a3a', n=4, spread=0.3)
        M_DK = mat('#2e2a3a', n=3, spread=0.25)
        for (x, y) in ((8, 8), (24, 8), (8, 24), (24, 24), (16, 16), (0, 16), (32, 16), (16, 0), (16, 32), (0, 0), (32, 0), (0, 32), (32, 32)):
            m = M_COP if (x + y + variant * 16) % 32 == 0 else M_DK
            s.poly([(x, y - 6.5), (x + 6.5, y), (x, y + 6.5), (x - 6.5, y)], m, ex=0.3)
        img = s.render(outline=False)
        base.alpha_composite(img)
        return _grain(base, 2000 + variant, 6, 0.2)

    def draw(s, ox, oy):
        if arena == 'b':
            for k in range(4):  # tábuas de passarela
                s.poly([(ox + 1, oy + k * 8 + 1), (ox + 31, oy + k * 8 + 1 + (variant % 2)),
                        (ox + 31, oy + k * 8 + 7), (ox + 1, oy + k * 8 + 7)], M_SLAB, ex=0.2)
        else:
            for (x, y, rx, ry) in ((8, 8, 9, 7), (24, 22, 9, 8), (24, 4, 7, 5), (6, 26, 6, 6))[: 3 + variant % 2]:
                s.ellipse(x + ox, y + oy, rx, ry, M_SLAB, ex=0.22)
    s = _wrap_parts(draw)
    s.parts = [p for p in s.parts if p.mask.any()]
    base.alpha_composite(s.render(outline=False))
    out = _grain(base, 3000 + variant + ord(arena), 7, 0.22)
    return out


def wall_tile(arena: str, mask: int, alt: int = 0) -> Image.Image:
    """mask: bits N=1, E=2, S=4, W=8 indicam vizinho caminhável naquele lado."""
    P = ARENAS[arena]
    img = Image.new('RGBA', (T, T), hx(P['wall']) + (255,))
    s = Sprite(T, T)
    if arena == 'a':  # rocha tomada por raízes
        M_R = mat('#2a1e20', n=3, spread=0.2); M_ROCK = mat(P['wall_top'], n=4, spread=0.18)
        s.ellipse(10 + alt * 4, 12, 9, 7, M_ROCK, ex=0.4); s.ellipse(24, 22 - alt * 3, 8, 7, M_ROCK, ex=0.4)
        s.limb([(-2, 18 + alt * 2), (10, 15), (20, 19), (34, 14)], 1.6, 1.3, M_R, ex=0.4)
        s.limb([(6, -2), (8, 10), (4, 34)], 1.2, 1.0, M_R, ex=0.4)
    elif arena == 'b':  # matagal de vidro escuro
        M_G = Mat(ramp('#1e4a54', 4, spread=0.5), spec=0.6)
        for (x, y, h) in ((8 + alt * 3, 26, 14), (20, 30, 18), (28 - alt * 2, 22, 11), (14, 16, 9)):
            s.poly([(x - 3, y), (x, y - h), (x + 3, y)], M_G, ex=0.35)
    else:  # água profunda com reflexo
        img = Image.new('RGBA', (T, T), hx('#0d2c3a') + (255,))
        a = np.asarray(img).copy()
        for (x, y, l) in ((4 + alt * 6, 8, 6), (18, 14, 8), (8, 22 + alt * 2, 5), (22, 27, 6)):
            for i in range(l):
                a[y % T, (x + i) % T, :3] = (40, 96, 116)
        img = Image.fromarray(a, 'RGBA')
    s.parts = [p for p in s.parts if p.mask.any()]
    if s.parts:
        img.alpha_composite(s.render(outline=False))
    a = np.asarray(img).copy()
    lip = hx(P['lip']); face_hi = mix(hx(P['wall_top']), lip, 0.4); face = darken(hx(P['wall']), 0.2)
    if mask & 4:  # face vertical voltada ao sul (profundidade 3/4)
        a[T - 9:T, :, :3] = face
        a[T - 9, :, :3] = face_hi
        a[T - 10, :, :3] = lip
        for x in range(0, T, 7):
            a[T - 8:T - 2, (x + alt * 3) % T, :3] = darken(face, 0.35)
        a[T - 1, :, :3] = darken(face, 0.5)
    if mask & 1:
        a[0:2, :, :3] = lip; a[2, :, :3] = face_hi
    if mask & 2:
        a[:, T - 2:T, :3] = lip
    if mask & 8:
        a[:, 0:2, :3] = lip
    return _grain(Image.fromarray(a, 'RGBA'), 4000 + mask * 3 + alt + ord(arena), 6, 0.15)


# ======================================================================
# PROPS
# ======================================================================
def prop_coral(kind=0) -> Sprite:
    s = Sprite(40, 48)
    M = mat('#a8302c', light_hue=0.07, spec=0.3); M2 = mat('#d45a44', n=4)
    s.ellipse(20, 43, 9, 3.5, mat('#3a2a30', n=3), ex=0.3)
    branches = [((20, 43), (18, 30), (12, 18), (10, 8)), ((20, 43), (23, 28), (30, 16), (32, 6)),
                ((19, 34), (25, 24), (26, 14)), ((18, 30), (14, 26), (6, 22))] if kind == 0 else \
               [((20, 43), (20, 26), (16, 12)), ((20, 34), (28, 24), (34, 22)), ((20, 30), (12, 22), (8, 14)), ((18, 20), (22, 12), (24, 4))]
    for b in branches:
        s.limb(list(b), 3.2, 1.2, M, ex=0.5)
    for b in branches:
        x, y = b[-1]
        s.ellipse(x, y, 1.8, 1.8, M2, ex=0.5)
    return s


def prop_fungi(kind=0) -> Sprite:
    s = Sprite(32, 32)
    M_ST = mat('#cfd9cf', n=4); M_CAP = mat_glow('#c9fff3', '#2bbfa8')
    caps = ((10, 18, 5.5), (20, 14, 7), (24, 23, 4)) if kind == 0 else ((9, 22, 4.5), (16, 16, 5.5), (23, 20, 4.2), (14, 25, 3))
    for (x, y, r) in caps:
        s.limb([(x, y + r + 5), (x, y)], r * 0.32, r * 0.25, M_ST, ex=0.5)
    for (x, y, r) in caps:
        s.ellipse(x, y, r, r * 0.62, M_CAP, ex=0.7)
        s.px(x - 1, int(y - r * 0.3), '#ffffff')
    return s


def prop_monument() -> Sprite:
    s = Sprite(80, 112)
    M = mat('#4d4a58', dither=True, spread=0.5); M2 = mat('#6c6878', n=4); M_G = mat_glow('#ffe2a0', '#ff7a2a')
    s.ellipse(40, 100, 30, 9, mat('#2c2a34', n=4), ex=0.3)
    s.poly([(16, 100), (64, 100), (60, 92), (20, 92)], M2, ex=0.3)
    s.poly([(24, 94), (56, 94), (52, 30), (44, 14), (34, 20), (28, 30)], M, ex=0.35)
    # rachadura brilhante e runa
    s.limb([(44, 16), (40, 34), (44, 50), (38, 70), (41, 90)], 1.2, 0.8, M_G, ex=0.3, edge=False)
    s.poly([(32, 40), (36, 34), (36, 46)], mat('#2a2734', n=3), ex=0.2)
    for (x, y) in ((33, 58), (34, 59), (35, 60), (34, 61), (33, 62), (48, 62), (48, 63), (49, 64)):
        s.px(x, y, '#ffcf7a', 200)
    return s


def prop_ruin_stone(kind=0) -> Sprite:
    s = Sprite(36, 40)
    M = mat('#4a4654', spread=0.5); M_M = mat('#2d5a50', n=4)
    if kind == 0:
        s.poly([(6, 36), (30, 36), (28, 8), (18, 4), (8, 10)], M, ex=0.35)
        s.ellipse(14, 14, 6, 3, M_M, ex=0.3)
    else:
        s.poly([(4, 36), (32, 36), (30, 24), (20, 20), (6, 26)], M, ex=0.35)
        s.ellipse(22, 25, 6, 2.5, M_M, ex=0.3)
    for (x, y) in ((18, 18), (18, 22), (17, 20), (19, 20)):
        s.px(x, y + (10 if kind else 0), '#ffcf7a', 150)
    return s


def prop_roots() -> Sprite:
    s = Sprite(56, 32)
    M = mat('#4a2e2a', n=4); M2 = mat('#6e423a', n=4)
    s.limb([(2, 26), (14, 20), (26, 24), (40, 16), (54, 18)], 3.0, 1.2, M, ex=0.45)
    s.limb([(12, 30), (20, 22), (30, 12), (34, 4)], 2.2, 0.8, M2, ex=0.45)
    s.limb([(30, 26), (40, 28), (50, 24)], 1.8, 0.8, M, ex=0.45)
    return s


def prop_bones() -> Sprite:
    s = Sprite(28, 18)
    M = mat('#d8cfb4', n=4)
    s.ellipse(9, 10, 5, 4, M, ex=0.6)
    s.px(7, 10, '#2a2420'); s.px(10, 10, '#2a2420')
    s.limb([(14, 12), (25, 9)], 1.3, 1.1, M, ex=0.5)
    s.limb([(15, 15), (24, 15)], 1.1, 1.0, M, ex=0.5)
    return s


def prop_lantern(lit=True) -> Sprite:
    s = Sprite(20, 44)
    M = mat('#3d3440', n=4); M_C = mat('#a86a3a', spec=0.5, n=4); M_G = mat_glow('#fff4c8', '#ffa040')
    s.limb([(10, 42), (10, 14)], 1.4, 1.1, M, ex=0.4)
    s.ellipse(10, 42, 4, 1.6, M, ex=0.3)
    s.poly([(5, 14), (15, 14), (14, 4), (6, 4)], M_C, ex=0.3)
    s.ellipse(10, 9, 2.6, 3.4, M_G if lit else mat('#3a3a44', n=3), ex=0.6, edge=False)
    s.poly([(4, 4), (16, 4), (10, 0)], M_C, ex=0.3)
    return s


def prop_stele() -> Sprite:
    s = Sprite(28, 52)
    M = mat('#3e4250', spread=0.5); M_C = mat('#b06a3a', spec=0.5, n=4)
    s.ellipse(14, 48, 11, 3.5, mat('#22242c', n=3), ex=0.3)
    s.poly([(5, 48), (23, 48), (22, 10), (14, 4), (6, 10)], M, ex=0.3)
    for y in (16, 24, 32, 40):
        s.line(9, y, 19, y, (60, 64, 78))
    s.ellipse(14, 20, 3, 3, M_C, ex=0.5)
    for (x, y) in ((11, 28), (17, 28), (14, 34), (12, 36), (16, 36)):
        s.px(x, y, '#d9874a')
    return s


def prop_arch() -> Sprite:
    s = Sprite(72, 72)
    M = mat('#4a4656', dither=True, spread=0.5)
    s.limb([(14, 70), (12, 40), (18, 18), (36, 8), (54, 18), (60, 40), (60, 52)], 6, 5, M, ex=0.4)
    s.poly([(54, 70), (66, 70), (64, 54), (56, 52)], M, ex=0.3)  # parte caída
    for (x, y) in ((36, 9), (35, 10), (37, 10), (36, 11)):
        s.px(x, y, '#ffcf7a')
    return s


def prop_crystal(size=1, hue='#3fd6d2') -> Sprite:
    W, H = (24, 36) if size == 0 else ((36, 56) if size == 1 else (52, 84))
    s = Sprite(W, H)
    k = [0.6, 1.0, 1.5][size]
    M = Mat(ramp(hue, 5, spread=0.55), spec=0.8)
    M2 = Mat(ramp('#1a6670', 4, spread=0.5), spec=0.5)
    base_y = H - 3
    s.ellipse(W / 2, base_y, W * 0.4, 3, mat('#18262c', n=3), ex=0.3)
    shards = ((-6, 22, -0.3), (0, 34, 0.0), (6, 26, 0.25), (-2, 14, -0.6), (9, 12, 0.6))
    for (dx, h, lean) in shards:
        x = W / 2 + dx * k
        hh = h * k
        mm = M if h > 15 else M2
        s.poly([(x - 3.5 * k, base_y), (x + lean * hh, base_y - hh), (x + 3.5 * k, base_y), (x, base_y + 1)], mm, ex=0.35)
        s.line(x, base_y - 2, x + lean * hh * 0.8, base_y - hh * 0.8, (230, 255, 255), 150)
    return s


def prop_tree_mineral(kind=0) -> Sprite:
    s = Sprite(72, 96)
    M = mat('#5a6470', dither=True, spread=0.5); M_L = Mat(ramp('#4bc8c0', 5, spread=0.5), spec=0.7)
    s.ellipse(36, 92, 16, 4, mat('#1a2a2e', n=3), ex=0.3)
    s.limb([(36, 92), (34, 70), (38, 50), (34, 30)], 6, 3, M, ex=0.45)
    s.limb([(36, 60), (50, 46), (60, 40)], 3, 1.5, M, ex=0.45)
    s.limb([(35, 50), (22, 38), (12, 34)], 3, 1.5, M, ex=0.45)
    for (x, y, r) in ((34, 24, 12), (56, 34, 9), (14, 28, 9), (44, 16, 8)) if kind == 0 else ((30, 26, 13), (52, 38, 10), (16, 34, 7)):
        s.poly([(x - r, y + r * 0.4), (x - r * 0.4, y - r), (x + r * 0.5, y - r * 0.8), (x + r, y + r * 0.3), (x, y + r * 0.8)], M_L, ex=0.4)
    return s


def prop_pool() -> Sprite:
    s = Sprite(64, 36)
    M_W = Mat([(14, 52, 64), (20, 72, 86), (34, 104, 118), (90, 180, 190), (200, 250, 250)], emissive=True)
    M_R = mat('#3e4a52', n=4)
    s.ellipse(32, 18, 30, 15, M_R, ex=0.3)
    s.ellipse(32, 18, 26, 12, M_W, ex=0.25, edge=False)
    for (x, y, l) in ((18, 14, 8), (34, 20, 10), (26, 24, 5)):
        s.line(x, y, x + l, y, (150, 230, 235), 170)
    return s


def prop_plank() -> Sprite:
    s = Sprite(48, 24)
    M = mat('#5a4a44', n=4)
    s.poly([(2, 8), (34, 4), (36, 12), (4, 16)], M, ex=0.2)
    s.poly([(20, 14), (46, 12), (44, 20), (22, 22)], M, ex=0.2)
    return s


def prop_shards() -> Sprite:
    s = Sprite(32, 20)
    M = Mat(ramp('#59e0d0', 4, spread=0.5), spec=0.8)
    for (x, y, r, a) in ((8, 12, 3, 0.4), (16, 14, 4, -0.3), (24, 10, 2.5, 1.0), (13, 7, 2, 0.2)):
        s.poly([(x - r, y + 1), (x + math.cos(a) * r, y - r * 1.6), (x + r, y + 1)], M, ex=0.4)
    return s


def prop_pillar(broken=False) -> Sprite:
    s = Sprite(32, 88)
    M = mat('#3c3e52', dither=True, spread=0.5); M_C = mat('#b06a3a', spec=0.5, n=4)
    s.ellipse(16, 84, 14, 4, mat('#1a1c26', n=3), ex=0.3)
    s.poly([(4, 84), (28, 84), (27, 76), (5, 76)], M, ex=0.3)
    top = 42 if broken else 12
    s.poly([(7, 77), (25, 77), (24, top), (8, top + (6 if broken else 0))], M, ex=0.4)
    if not broken:
        s.poly([(4, 14), (28, 14), (26, 6), (6, 6)], M, ex=0.3)
    else:
        s.poly([(8, top + 6), (14, top - 4), (18, top + 2), (24, top - 2), (24, top + 4)], M, ex=0.3)
    s.poly([(7, 60), (25, 60), (25, 63), (7, 63)], M_C, ex=0.2)
    for x in range(10, 23, 4):
        s.line(x, top + 8, x, 58, (40, 42, 58), 160)
    return s


def prop_kelp() -> Sprite:
    s = Sprite(28, 44)
    M = mat('#2e6a5a', n=4); M2 = mat('#4a9a7a', n=4)
    s.limb([(10, 42), (8, 30), (12, 18), (9, 4)], 2.0, 0.8, M, ex=0.4)
    s.limb([(16, 42), (19, 28), (16, 16), (20, 8)], 2.0, 0.8, M2, ex=0.4)
    s.limb([(13, 42), (14, 34), (12, 26)], 1.6, 0.8, M, ex=0.4)
    return s


def prop_altar(lit=False) -> Sprite:
    s = Sprite(64, 56)
    M = mat('#3e4050', dither=True, spread=0.5); M_C = mat('#b06a3a', spec=0.6, n=4)
    s.ellipse(32, 46, 28, 9, mat('#22242e', n=3), ex=0.3)
    s.poly([(8, 46), (56, 46), (52, 36), (12, 36)], M, ex=0.3)
    s.poly([(16, 38), (48, 38), (46, 22), (18, 22)], M, ex=0.35)
    s.poly([(14, 24), (50, 24), (48, 18), (16, 18)], M_C, ex=0.3)
    return s


def prop_rift() -> Sprite:
    """A fenda pulsante ao fundo do Santuário (grande, emissiva)."""
    s = Sprite(160, 96)
    M_R = mat('#1a1428', n=4)
    M_G = mat_glow('#ffd6f0', '#a01a6a')
    M_G2 = mat_glow('#ffffff', '#ff5aa0')
    s.ellipse(80, 60, 76, 30, mat('#202032', n=4, spread=0.4), ex=0.25)
    s.poly([(20, 64), (60, 50), (78, 22), (96, 48), (140, 58), (100, 70), (80, 88), (58, 72)], M_R, ex=0.3)
    s.poly([(40, 62), (66, 54), (80, 30), (92, 52), (120, 60), (94, 66), (80, 80), (64, 68)], M_G, ex=0.4, edge=False)
    s.poly([(62, 60), (74, 56), (80, 42), (86, 56), (100, 60), (86, 64), (80, 72), (72, 64)], M_G2, ex=0.5, edge=False)
    return s


def anchor(state: int, t: float = 0.0) -> Sprite:
    """Âncora do Véu: 0 apagada, 1 canalizando (pulso t), 2 reacendida."""
    s = Sprite(56, 80)
    M = mat('#4a4658', dither=True, spread=0.5); M_C = mat('#c08040', spec=0.6)
    s.ellipse(28, 72, 24, 7, mat('#24222e', n=3), ex=0.3)
    s.poly([(10, 72), (46, 72), (42, 64), (14, 64)], M, ex=0.3)
    s.limb([(28, 66), (28, 22)], 5, 3.5, M, ex=0.45)
    # anel/garra que segura a brasa
    s.limb([(16, 30), (14, 18), (20, 8), (28, 5), (36, 8), (42, 18), (40, 30)], 2.2, 2.2, M_C, ex=0.5)
    if state == 0:
        s.ellipse(28, 18, 6, 6, mat('#3a3440', n=4), ex=0.6)
    else:
        r = 6 + (math.sin(t * TAU) * 1.2 if state == 1 else 2)
        s.ellipse(28, 18, r + 2, r + 2, mat_glow('#ffe8a8', '#ff6a1a'), ex=0.8, edge=False)
        s.ellipse(28, 18, r * 0.6, r * 0.6, mat_glow('#ffffff', '#ffd27a'), ex=0.8, edge=False)
    for (x, y) in ((28, 40), (27, 44), (29, 44), (28, 48), (28, 54)):
        s.px(x, y, '#ffcf7a' if state else '#6a5a50', 220)
    return s


def portal(t: float) -> Sprite:
    s = Sprite(64, 64)
    r = 22 + math.sin(t * TAU) * 1.5
    s.ellipse(32, 34, r + 4, (r + 4) * 0.5, mat('#3c3448', n=4), ex=0.3)
    s.ellipse(32, 34, r, r * 0.45, mat_glow('#fff1d0', '#ff8a3a'), ex=0.6, edge=False)
    s.ellipse(32, 34, r * 0.55, r * 0.25, mat_glow('#ffffff', '#ffd27a'), ex=0.6, edge=False)
    return s


def props_all():
    """Retorna dict nome->(frames, meta). Mais de 25 props distintos."""
    P = {}
    P['coral_a'] = prop_coral(0); P['coral_b'] = prop_coral(1)
    P['fungi_a'] = prop_fungi(0); P['fungi_b'] = prop_fungi(1)
    P['monument'] = prop_monument()
    P['ruin_a'] = prop_ruin_stone(0); P['ruin_b'] = prop_ruin_stone(1)
    P['roots'] = prop_roots(); P['bones'] = prop_bones()
    P['lantern'] = prop_lantern(True); P['lantern_off'] = prop_lantern(False)
    P['stele'] = prop_stele(); P['arch'] = prop_arch()
    P['crystal_s'] = prop_crystal(0); P['crystal_m'] = prop_crystal(1); P['crystal_l'] = prop_crystal(2)
    P['crystal_v'] = prop_crystal(1, '#8a7aff')
    P['tree_a'] = prop_tree_mineral(0); P['tree_b'] = prop_tree_mineral(1)
    P['pool'] = prop_pool(); P['plank'] = prop_plank(); P['shards'] = prop_shards()
    P['pillar'] = prop_pillar(False); P['pillar_broken'] = prop_pillar(True)
    P['kelp'] = prop_kelp(); P['altar'] = prop_altar(); P['rift'] = prop_rift()
    return {k: v.render() for k, v in P.items()}
