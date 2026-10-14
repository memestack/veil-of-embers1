"""Second wave of creatures: Ember Wisp, Coral Hermit, Glass Golem, Shard Mite, Ash Knight (elite),
Ash Wyrm (segmented boss) and Glass Colossus (boss). Same authored part-based pipeline as enemies.py."""
import math
from pix import Sprite, mat, mat_glow, Mat, ramp, rot

TAU = math.tau


def P(cx, cy, a):
    def f(x, y):
        return rot(cx + x, cy + y, cx, cy, a)
    return f


# ---------------------------------------------------------------- Ember Wisp
M_WISP = mat_glow('#fff6c8', '#ff5a1a')
M_WISP2 = mat_glow('#ffffff', '#ffb040')
M_WISP_EYE = Mat([(40, 10, 10)] * 3, outline=(40, 10, 10))


def wisp(phase: float, fuse=0.0) -> Sprite:
    s = Sprite(28, 30)
    f = math.sin(phase * TAU)
    by = 16 + f * 1.5
    r = 6 + fuse * 2.5 + (math.sin(phase * TAU * 4) * fuse * 1.2)
    # cauda de chamas
    s.limb([(14, by + 2), (13 - f * 2, by + 8), (15 + f * 2, by + 12)], r * 0.7, 0.6, M_WISP, ex=0.5, edge=False)
    s.ellipse(14, by, r, r * 0.95, M_WISP, ex=0.8, edge=False)
    s.ellipse(13, by - 1, r * 0.55, r * 0.5, M_WISP2, ex=0.8, edge=False)
    # carinha travessa
    s.px(12, round(by - 1), (40, 10, 10)); s.px(16, round(by - 1), (40, 10, 10))
    s.line(12, by + 2, 16, by + 2, (90, 20, 10), 200)
    for k in range(3):
        a = phase * TAU + k * 2.1
        s.px(round(14 + math.cos(a) * (r + 3)), round(by - 3 + math.sin(a) * (r + 2)), (255, 220, 140))
    return s


# --------------------------------------------------------------- Coral Hermit
M_HER_SHELL = mat('#c8503e', light_hue=0.07, spec=0.4, dither=True)
M_HER_SPIKE = mat('#f08a6a', n=4)
M_HER_LEG = mat('#3a6a74', n=4)
M_HER_BODY = mat('#5a9aa2', n=4)
M_HER_EYE = mat_glow('#fff6c0', '#ffb030')


def hermit(phase: float, hide=0.0) -> Sprite:
    s = Sprite(40, 36)
    st = math.sin(phase * TAU)
    by = 22 + hide * 3
    if hide < 0.6:
        for i, ox in enumerate((-9, -3, 4, 10)):
            sw = st * (1 if i % 2 else -1) * 1.6 * (1 - hide)
            s.limb([(20 + ox, by + 2), (20 + ox * 1.25 + sw, by + 7), (20 + ox * 1.4 + sw * 1.4, by + 10)], 1.3, 0.8, M_HER_LEG, ex=0.4)
        # garra grande à frente
        s.limb([(30, by), (35, by - 2), (37, by + 2)], 2.0, 1.4, M_HER_LEG, ex=0.5)
        s.ellipse(37, by + 1, 3.2, 2.4, M_HER_BODY, ex=0.6)
        s.ellipse(30, by - 4, 1.4, 1.4, M_HER_EYE, edge=False)
    # concha de coral espiralada
    s.ellipse(18, by - 4, 12, 9.5 - hide, M_HER_SHELL, ex=0.75)
    s.limb([(10, by - 6), (16, by - 11), (24, by - 10), (27, by - 5)], 2.0, 1.0, M_HER_SPIKE, ex=0.4, edge=True)
    for (x, h) in ((10, 7), (17, 10), (24, 8)):
        s.poly([(x - 2, by - 10), (x, by - 10 - h), (x + 2, by - 10)], M_HER_SPIKE, ex=0.4)
    return s


# ---------------------------------------------------------------- Glass Golem
M_GOL = Mat(ramp('#3fa6b8', 5, spread=0.55), spec=0.75, dither=True)
M_GOL_DK = Mat(ramp('#1f5866', 4, spread=0.5), spec=0.5)
M_GOL_CORE = mat_glow('#ffffff', '#5af0ff')


def golem(phase: float, slam=0.0) -> Sprite:
    s = Sprite(56, 60)
    st = math.sin(phase * TAU)
    by = 40 - abs(st) * 0.8
    for i, ox in enumerate((-7, 6)):
        sw = st * (1 if i else -1) * 2.0
        s.poly([(26 + ox - 4 + sw, by + 4), (26 + ox + 4 + sw, by + 4), (26 + ox + 5 + sw * 1.4, by + 16), (26 + ox - 5 + sw * 1.4, by + 16)], M_GOL_DK, ex=0.35)
    # tronco facetado
    s.poly([(14, by - 16), (38, by - 18), (42, by + 4), (28, by + 8), (12, by + 4)], M_GOL, ex=0.4)
    s.ellipse(27, by - 6, 4.5, 4.5, M_GOL_CORE, edge=False)
    # braços (sobem no golpe)
    lift = slam * 18
    s.poly([(10, by - 14), (16, by - 12), (10, by + 6 - lift), (2, by + 4 - lift)], M_GOL_DK, ex=0.35)
    s.poly([(38, by - 16), (44, by - 14), (52, by + 6 - lift), (44, by + 8 - lift)], M_GOL, ex=0.35)
    # cabeça pequena
    s.poly([(22, by - 16), (32, by - 17), (31, by - 25), (23, by - 24)], M_GOL, ex=0.35)
    s.px(25, round(by - 21), '#ffffff'); s.px(29, round(by - 21), '#ffffff')
    return s


# ----------------------------------------------------------------- Shard Mite
M_MITE = Mat(ramp('#6ae0f0', 4, spread=0.5), spec=0.8)
M_MITE_LEG = mat('#1f5866', n=3)


def mite(a: float, phase: float) -> Sprite:
    s = Sprite(18, 18)
    T = P(9, 9, a)
    for i in range(3):
        for side in (-1, 1):
            sw = math.sin(phase * TAU + i * 2 + (side > 0) * math.pi) * 1.2
            s.limb([T(1 - i * 2, side * 1), T(2 - i * 2.5 + sw, side * 5)], 0.6, 0.5, M_MITE_LEG, ex=0.3)
    s.poly([T(6, 0), T(0, -4), T(-5, 0), T(0, 4)], M_MITE, ex=0.4)
    X, Y = T(3, 0)
    s.px(round(X), round(Y), '#ffffff')
    return s


# ------------------------------------------------------------- Ash Knight (elite)
M_KN_ARMOR = mat('#4a4450', spec=0.55, dither=True)
M_KN_ARMOR2 = mat('#6a606e', spec=0.6, n=4)
M_KN_CAPE = mat('#3a1018', n=4)
M_KN_BLADE = mat_glow('#fff4c0', '#ff4a10')
M_KN_EYE = mat_glow('#ffffff', '#ff7a1a')


def knight(phase: float, pose='walk', t=0.0) -> Sprite:
    s = Sprite(64, 64)
    st = math.sin(phase * TAU) if pose == 'walk' else 0
    by = 40 - abs(st) * 0.6
    s.poly([(26, by - 14), (36, by - 14), (40, by + 14), (22, by + 14)], M_KN_CAPE, ex=0.3)
    for i, ox in enumerate((-4, 4)):
        sw = st * (1 if i else -1) * 2.2
        s.limb([(31 + ox, by + 4), (31 + ox + sw * 0.5, by + 10), (31 + ox + sw, by + 16)], 2.4, 2.0, M_KN_ARMOR, ex=0.5)
    s.ellipse(31, by - 4, 8, 10, M_KN_ARMOR, ex=0.6)
    s.ellipse(25, by - 11, 4, 3.4, M_KN_ARMOR2, ex=0.6)
    s.ellipse(37, by - 11, 4, 3.4, M_KN_ARMOR2, ex=0.6)
    # elmo com crista
    s.ellipse(31, by - 19, 5.5, 6, M_KN_ARMOR2, ex=0.6)
    s.poly([(29, by - 25), (33, by - 25), (31, by - 31)], M_KN_BLADE, ex=0.4, edge=False)
    s.line(28, by - 19, 34, by - 19, (20, 10, 10))
    s.px(30, round(by - 19), '#ffb050'); s.px(33, round(by - 19), '#ffb050')
    # espada flamejante: repouso / erguida (windup) / golpe
    if pose == 'windup':
        ang = -2.2 + t * 0.3
    elif pose == 'swing':
        ang = -1.2 + t * 2.6
    else:
        ang = 0.6 + st * 0.05
    hx_, hy_ = 40, by - 6
    tx, ty = hx_ + math.cos(ang) * 24, hy_ + math.sin(ang) * 24
    s.limb([(36, by - 10), (hx_, hy_)], 2.0, 1.8, M_KN_ARMOR2, ex=0.5)
    s.limb([(hx_, hy_), (tx, ty)], 2.2, 1.0, M_KN_BLADE, ex=0.5, edge=False)
    return s


# ----------------------------------------------------------- Ash Wyrm (boss)
M_WY_SCALE = mat('#4a2a2a', spec=0.4, dither=True)
M_WY_PLATE = mat('#7a3a2a', spec=0.5)
M_WY_CRACK = mat_glow('#fff0b0', '#ff5a10')
M_WY_HORN = mat('#d8c8a8', n=4)
M_WY_MOUTH = mat('#2a0a0a', n=3)


def wyrm_head(a: float, open_=0.0, enraged=False) -> Sprite:
    s = Sprite(64, 64)
    T = P(32, 32, a)
    # mandíbula inferior
    s.poly([T(4, -6 - open_ * 4), T(24, -4 - open_ * 6), T(26, 0), T(24, 4 + open_ * 6), T(4, 6 + open_ * 4)], M_WY_SCALE, ex=0.4)
    if open_ > 0.2:
        s.poly([T(8, -3 - open_ * 3), T(24, -2 - open_ * 4), T(24, 2 + open_ * 4), T(8, 3 + open_ * 3)], M_WY_MOUTH, ex=0.3)
        s.ellipse(*T(14, 0), 3 + open_ * 2, 2 + open_ * 2, M_WY_CRACK, rot=a, edge=False)
    # crânio
    s.ellipse(*T(0, 0), 15, 12, M_WY_PLATE, rot=a, ex=0.7)
    s.ellipse(*T(6, 0), 10, 8, M_WY_SCALE, rot=a, ex=0.6)
    for side in (-1, 1):
        s.limb([T(-6, side * 8), T(-14, side * 14), T(-22, side * 15)], 2.6, 0.8, M_WY_HORN, ex=0.5)
        X, Y = T(6, side * 6)
        s.ellipse(X, Y, 2.2, 2.0, M_WY_CRACK, edge=False)
    if enraged:
        s.limb([T(-10, 0), T(0, 2), T(8, -1)], 1.2, 0.8, M_WY_CRACK, ex=0.3, edge=False)
    return s


def wyrm_seg(i: int, enraged=False) -> Sprite:
    s = Sprite(40, 40)
    r = 13 - i * 0.6
    s.ellipse(20, 21, r, r * 0.9, M_WY_SCALE, ex=0.7)
    s.ellipse(20, 17, r * 0.8, r * 0.55, M_WY_PLATE, ex=0.6)
    for k in (-1, 0, 1):
        s.poly([(20 + k * 6 - 2, 12), (20 + k * 6, 4 + abs(k) * 2), (20 + k * 6 + 2, 12)], M_WY_HORN, ex=0.4)
    s.limb([(12, 22), (20, 25), (28, 22)], 1.0 + (0.6 if enraged else 0), 0.8, M_WY_CRACK, ex=0.3, edge=False)
    return s


def wyrm_tail(a: float) -> Sprite:
    s = Sprite(40, 40)
    T = P(20, 20, a)
    s.poly([T(-8, -7), T(16, 0), T(-8, 7)], M_WY_SCALE, ex=0.5)
    s.poly([T(-4, -3), T(12, 0), T(-4, 3)], M_WY_PLATE, ex=0.4)
    return s


def mound(t: float) -> Sprite:
    s = Sprite(64, 32)
    s.ellipse(32, 20, 26 + t * 3, 9 + t, mat('#2c2420', n=4), ex=0.4)
    for k in range(6):
        a = k / 6 * TAU + t
        s.ellipse(32 + math.cos(a) * 20, 19 + math.sin(a) * 6, 3, 2, mat('#4a3a30', n=3), ex=0.5)
    s.ellipse(32, 18, 10 + t * 4, 3 + t, M_WY_CRACK, ex=0.6, edge=False)
    return s


# -------------------------------------------------------- Glass Colossus (boss)
M_CO = Mat(ramp('#2f8496', 5, spread=0.55), spec=0.8, dither=True)
M_CO_DK = Mat(ramp('#183c4a', 5, spread=0.5), spec=0.5, dither=True)
M_CO_CORE = mat_glow('#ffffff', '#ff5aa0')
M_CO_CORE2 = mat_glow('#ffffff', '#ffb040')


def colossus(pose: str, t: float, enraged=False) -> Sprite:
    W, H = 150, 160
    s = Sprite(W, H)
    breath = math.sin(t * TAU) if pose == 'idle' else 0
    lift = {'idle': 0, 'raise': t * 40, 'slam': (1 - t) * 40, 'roar': 10}.get(pose, 0)
    by = 112 + breath
    core = M_CO_CORE if enraged else M_CO_CORE2
    # pernas-pilar
    for ox in (-22, 22):
        s.poly([(75 + ox - 12, by), (75 + ox + 12, by), (75 + ox + 15, by + 40), (75 + ox - 15, by + 40)], M_CO_DK, ex=0.35)
    # tronco
    s.poly([(36, by - 60), (114, by - 64), (122, by - 6), (98, by + 8), (52, by + 8), (28, by - 6)], M_CO, ex=0.4)
    s.poly([(60, by - 48), (90, by - 50), (92, by - 22), (58, by - 20)], M_CO_DK, ex=0.35)
    s.ellipse(75, by - 34, 11 + breath * 0.5, 11 + breath * 0.5, core, ex=0.8, edge=False)
    # facetas e trincas do vidro
    for (x0, y0, x1, y1) in ((44, by - 50, 56, by - 14), (106, by - 54, 96, by - 16), (62, by - 12, 88, by - 14)):
        s.line(x0, y0, x1, y1, (16, 50, 60), 200)
    # cabeça
    s.poly([(62, by - 62), (88, by - 64), (90, by - 86), (75, by - 94), (60, by - 86)], M_CO, ex=0.4)
    eye = (255, 120, 180) if enraged else (255, 230, 160)
    for x in (68, 81):
        s.px(x, round(by - 76), eye); s.px(x + 1, round(by - 76), eye)
    # braços
    for side in (-1, 1):
        sx = 75 + side * 44
        s.poly([(sx - 10, by - 58), (sx + 10, by - 60), (sx + side * 16, by - 10 - lift), (sx - side * 4, by - 4 - lift)], M_CO, ex=0.35)
        s.ellipse(sx + side * 6, by - 4 - lift, 15, 12, M_CO_DK, ex=0.6)
    # cristais nos ombros
    for side in (-1, 1):
        for k in range(3):
            x = 75 + side * (30 + k * 8)
            s.poly([(x - 4, by - 58), (x + side * 2, by - 80 - k * 6), (x + 4, by - 58)], M_CO, ex=0.4)
    if enraged:
        s.limb([(48, by - 50), (60, by - 30), (54, by - 10)], 1.2, 0.8, M_CO_CORE, ex=0.3, edge=False)
        s.limb([(104, by - 52), (94, by - 30), (102, by - 8)], 1.2, 0.8, M_CO_CORE, ex=0.3, edge=False)
    return s
