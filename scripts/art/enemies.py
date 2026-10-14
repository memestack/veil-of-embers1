"""
Criaturas do VÉU DE BRASAS — cada espécie tem anatomia, pose e ciclo próprios.
Insetos/aracnídeos são vistos de cima e pré-renderizados em 8 direções
(re-rasterização da geometria, sem rotação de pixels). Criaturas de corpo
alto (lodo, sapo, carapaça, espectro, elites, chefes) usam vista 3/4 voltada
para a direita; o jogo espelha para a esquerda.
"""
import math
from pix import Sprite, mat, mat_glow, Mat, rot, hx, mix, ramp, darken

TAU = math.tau
DIRS8 = [i * TAU / 8 for i in range(8)]  # 0 = direita, sentido horário (y para baixo)


def P(cx, cy, a):
    """Transforma coordenadas locais (x = frente) para o quadro, girando por a."""
    def f(x, y):
        return rot(cx + x, cy + y, cx, cy, a)
    return f


# ======================================================================
# 1. FERRUGÍNEOS — insetos escarlates velozes, corpo em 3 segmentos
# ======================================================================
M_FERR_SHELL = mat('#b5302a', spec=0.5, light_hue=0.08)
M_FERR_DARK = mat('#5e1820')
M_FERR_LEG = mat('#3a1418', n=4)
M_FERR_GLOW = mat_glow('#ffd27a', '#ff6a2a')


def ferrugineo(a: float, phase: float, attack=0.0) -> Sprite:
    W = 24; c = 12
    s = Sprite(W, W)
    T = P(c, c, a)
    # patas: 3 pares, marcha em tripé
    for i, (lx, spread) in enumerate(((3.0, 0.9), (0.0, 1.0), (-3.2, 1.1))):
        for side in (-1, 1):
            ph = phase * TAU + (0 if (i % 2 == 0) == (side > 0) else math.pi)
            sw = math.sin(ph) * 1.6
            knee = T(lx + sw * 0.5, side * 4.2)
            foot = T(lx + sw + (1.5 - i * 1.5) * spread, side * 7.0)
            s.limb([T(lx, side * 1.6), knee, foot], 0.75, 0.45, M_FERR_LEG, ex=0.3)
    # abdômen segmentado
    s.ellipse(*T(-4.2, 0), 4.6, 3.6, M_FERR_SHELL, rot=a,
              ex=0.55)
    M_seg = M_FERR_SHELL
    # tórax e cabeça
    s.ellipse(*T(0.6, 0), 2.6, 2.6, M_FERR_DARK, rot=a, ex=0.5)
    hx_, hy_ = T(3.6 + attack * 1.0, 0)
    s.ellipse(hx_, hy_, 2.6, 2.3, M_FERR_SHELL, rot=a, ex=0.6)
    # mandíbulas (abrem no ataque)
    op = 0.6 + attack * 1.2
    for side in (-1, 1):
        s.limb([T(5.4 + attack, side * 1.0), T(7.0 + attack, side * (1.2 + op)), T(8.0 + attack, side * 0.4)],
               0.6, 0.35, M_FERR_LEG, ex=0.3)
    # sulcos do abdômen + olhos incandescentes
    for k in (-5.5, -3.5):
        for j in range(-2, 3):
            x, y = T(k, j * 1.2)
            s.px(round(x), round(y), '#5e1820', 170)
    for side in (-1, 1):
        x, y = T(4.8 + attack, side * 1.3)
        s.px(round(x), round(y), '#ffd27a')
    # antenas
    for side in (-1, 1):
        x0, y0 = T(5.6, side * 0.8); x1, y1 = T(9.2, side * 3.2 + math.sin(phase * TAU) * 0.6)
        s.line(x0, y0, x1, y1, '#2a0e12', 220)
    return s


# ======================================================================
# 2. MORDALUMES — aranhas baixas turquesa, oito patas articuladas
# ======================================================================
M_MORD_BODY = mat('#1f8f8c', spec=0.35)
M_MORD_BACK = mat('#145a63')
M_MORD_LEG = mat('#0d3640', n=4)
M_MORD_EYE = mat_glow('#e9fff4', '#5fffd0')


def mordalume(a: float, phase: float, attack=0.0) -> Sprite:
    W = 30; c = 15
    s = Sprite(W, W)
    T = P(c, c, a)
    for i in range(4):
        base = math.radians(38 + i * 34)            # ângulo a partir da frente
        for side in (-1, 1):
            ph = phase * TAU + (i % 2) * math.pi + (side > 0) * math.pi
            sw = math.sin(ph) * 0.16
            ang = base + sw
            kx, ky = math.cos(ang) * 6.0, math.sin(ang) * 6.0 * side
            fa = ang + 0.12 * (1 if i < 2 else -1)
            fx, fy = math.cos(fa) * 11.0, math.sin(fa) * 11.0 * side
            s.limb([T(-1.0 + (1.5 - i) * 0.8, side * 1.6), T(kx, ky), T(fx, fy)], 0.85, 0.45, M_MORD_LEG, ex=0.3)
    s.ellipse(*T(-5.0, 0), 5.0, 4.4, M_MORD_BACK, rot=a, ex=0.6)
    s.ellipse(*T(1.0, 0), 3.6, 3.3, M_MORD_BODY, rot=a, ex=0.55)
    # quelíceras
    for side in (-1, 1):
        s.limb([T(3.8, side * 1.1), T(5.6 + attack * 1.5, side * (0.6 + attack))], 0.8, 0.5, M_MORD_LEG, ex=0.3)
    # padrão de marcas no abdômen (ampulheta clara)
    for (x, y) in ((-5, 0), (-4, 0), (-6, 0), (-5, -1), (-5, 1), (-7, -1), (-7, 1), (-3, -1), (-3, 1)):
        X, Y = T(x, y)
        s.px(round(X), round(Y), '#7ff2d9', 200)
    for (x, y) in ((3, -1), (3, 1), (2.2, -2), (2.2, 2)):
        X, Y = T(x, y)
        s.px(round(X), round(Y), '#e9fff4')
    return s


# ======================================================================
# 3. FILHOS DO LODO — massa pálida lenta, barriga translúcida com brasa
# ======================================================================
M_LODO = mat('#b7b39a', spread=0.55, light_hue=0.15, spec=0.4)
M_LODO_BELLY = Mat([(70, 120, 110), (90, 165, 150), (130, 210, 190), (190, 240, 220), (235, 255, 245)],
                   emissive=True, alpha=0.78, outline=(40, 60, 60))
M_LODO_CORE = mat_glow('#fff1c2', '#ff8a3a')
M_LODO_DRIP = mat('#8d8a74', n=4)


def filho_do_lodo(phase: float, attack=0.0) -> Sprite:
    W, H = 30, 30
    s = Sprite(W, H)
    sq = math.sin(phase * TAU) * 1.2  # squash/stretch leve
    cy = 18 + sq * 0.3
    # pseudópodes / poça
    s.ellipse(15, 25, 10 + sq * 0.6, 3.2, M_LODO_DRIP, ex=0.4)
    s.ellipse(15, cy - 2, 8.6 + sq * 0.5 + attack * 1.4, 9.5 - sq * 0.5 - attack * 1.2, M_LODO, ex=0.75)
    s.ellipse(15.5, cy + 0.5, 5.2, 5.0, M_LODO_BELLY, ex=0.8, edge=False)
    s.ellipse(16, cy + 1, 1.6 + 0.4 * math.sin(phase * TAU * 2), 1.5, M_LODO_CORE, edge=False)
    # gotas laterais
    s.ellipse(6.5 - sq * 0.4, cy + 4, 1.8, 2.4, M_LODO, ex=0.6)
    s.ellipse(24 + sq * 0.4, cy + 3, 1.5, 2.0, M_LODO, ex=0.6)
    # olhos fundos e boca
    for x in (12, 17):
        s.px(x, int(cy - 7), '#1a1a20'); s.px(x, int(cy - 6), '#1a1a20')
        s.px(x, int(cy - 7), '#d8ffef', 120)
    for x in range(12, 18):
        s.px(x, int(cy - 3 + (1 if x in (12, 17) else 0) + attack), '#3b3a2c', 220)
    return s


# ======================================================================
# 4. VESPAS DE VIDRO — voadoras, asas translúcidas, ferrão de cristal
# ======================================================================
M_VESP_BODY = mat('#2bb3c4', spec=0.6, light_hue=0.5)
M_VESP_STRIPE = mat('#0f3f5c')
M_VESP_WING = Mat([(150, 220, 235), (180, 240, 250), (210, 250, 255), (235, 255, 255)], emissive=True,
                  alpha=0.45, outline=(90, 170, 200))
M_VESP_STING = mat_glow('#f2ffff', '#4ae0ff')


def vespa(a: float, phase: float, dive=0.0) -> Sprite:
    W = 34; c = 17
    s = Sprite(W, W)
    T = P(c, c, a)
    flap = math.sin(phase * TAU * 2)
    # asas atrás do corpo
    for side in (-1, 1):
        wl = 7.5 + flap * 1.8
        pts = [T(1.5, side * 1.0), T(-1 + flap, side * (wl)), T(-5.5, side * (wl - 1.0)), T(-3, side * 1.4)]
        s.poly(pts, M_VESP_WING, ex=0.3, edge=False)
        pts2 = [T(-0.5, side * 1.0), T(-4.5, side * (wl - 2.5)), T(-7.0, side * (wl - 3.5)), T(-4.0, side * 1.0)]
        s.poly(pts2, M_VESP_WING, ex=0.3, edge=False)
    # abdômen listrado + ferrão
    s.ellipse(*T(-5.2, 0), 4.2, 2.8, M_VESP_BODY, rot=a, ex=0.6)
    for k in (-6.5, -4.3):
        for j in (-2, -1, 0, 1, 2):
            X, Y = T(k, j)
            s.px(round(X), round(Y), '#0f3f5c', 210)
    s.limb([T(-8.6, 0), T(-11.0 - dive * 1.5, 0)], 1.0, 0.4, M_VESP_STING, ex=0.4)
    s.ellipse(*T(0.2, 0), 2.4, 2.1, M_VESP_STRIPE, rot=a)
    s.ellipse(*T(3.2, 0), 2.2, 2.4, M_VESP_BODY, rot=a)
    for side in (-1, 1):
        X, Y = T(4.0, side * 1.4)
        s.px(round(X), round(Y), '#f2ffff')
    return s


# ======================================================================
# 5. CARAPAÇAS RUBRAS — soldados encouraçados, escudo frontal e investida
# ======================================================================
M_CAR_SHELL = mat('#9c2222', spec=0.55, light_hue=0.06, dither=True)
M_CAR_PLATE = mat('#c4523a', spec=0.4)
M_CAR_FLESH = mat('#3d1a22')
M_CAR_HORN = mat('#e8cfae', n=4)
M_CAR_EYE = mat_glow('#fff5c8', '#ffb347')


def carapaca(phase: float, attack=0.0) -> Sprite:
    W, H = 42, 42
    s = Sprite(W, H)
    step = math.sin(phase * TAU)
    lean = attack * 3.0
    bob = abs(step) * 0.8
    # pernas grossas (trás e frente) com passada pesada
    for i, ox in enumerate((-6, 3)):
        sw = step * (1 if i == 0 else -1) * 2.2
        s.limb([(20 + ox, 27 - bob), (19 + ox + sw * 0.4, 32), (20 + ox + sw, 36)], 2.6, 2.0, M_CAR_FLESH, ex=0.5)
        s.ellipse(20.5 + ox + sw, 36.3, 3.0, 1.4, M_CAR_HORN, ex=0.4)
    # casco principal (cúpula)
    s.ellipse(19 + lean * 0.4, 21 - bob, 13, 10.5, M_CAR_SHELL, ex=0.7)
    # placas de borda
    for k in range(5):
        ang = math.pi * (0.85 + k * 0.09)
        x = 19 + lean * 0.4 + math.cos(ang) * 11.5
        y = 21 - bob + math.sin(ang) * 9.0 + 4
        s.ellipse(x, y, 2.6, 2.0, M_CAR_PLATE, ex=0.5)
    # escudo frontal / cabeça encaixada
    s.ellipse(30 + lean, 24 - bob, 6.2, 6.8, M_CAR_PLATE, ex=0.6)
    s.limb([(33 + lean, 19 - bob), (37 + lean * 1.3, 15 - bob), (38.5 + lean * 1.4, 13 - bob)], 1.6, 0.6, M_CAR_HORN, ex=0.4)
    s.ellipse(33.5 + lean, 25 - bob, 1.3, 1.1, M_CAR_EYE, edge=False)
    # sulcos do casco
    for (x0, y0, x1, y1) in ((12, 15, 16, 28), (19, 12, 20, 30), (25, 14, 25, 28)):
        s.line(x0 + lean * 0.4, y0 - bob, x1 + lean * 0.4, y1 - bob, '#4d0f17', 150)
    return s


# ======================================================================
# 6. SAPOS DA FENDA — anfíbios azul-esverdeados, salto em arco
# ======================================================================
M_SAPO = mat('#2d8a86', light_hue=0.2, spec=0.3)
M_SAPO_BELLY = mat('#a8d6b0', n=4)
M_SAPO_SPOT = mat('#13505a', n=4)
M_SAPO_EYE = mat_glow('#ffe9a8', '#ff9a2e')
M_SAPO_MOUTH = mat('#4a1c2c', n=4)


def sapo(pose: str, t: float) -> Sprite:
    """pose: idle (respira), crouch (prepara), leap (no ar), land."""
    W, H = 38, 38
    s = Sprite(W, H)
    lift = 0.0; stretch = 0.0; leg_ext = 0.0
    if pose == 'idle':
        breath = math.sin(t * TAU) * 0.6
    else:
        breath = 0
    if pose == 'crouch':
        stretch = -1.5 * t
    if pose == 'leap':
        lift = -6 * math.sin(t * math.pi); stretch = 1.6; leg_ext = 1.0
    if pose == 'land':
        stretch = -1.4 * (1 - t)
    by = 24 + lift
    # patas traseiras dobradas (ou estendidas no salto)
    if leg_ext:
        s.limb([(13, by + 3), (6, by + 6), (2, by + 7)], 2.4, 1.4, M_SAPO, ex=0.5)
        s.ellipse(2.5, by + 7.5, 2.6, 1.2, M_SAPO_SPOT, ex=0.4)
    else:
        s.ellipse(11, by + 4 - stretch * 0.3, 6.0, 4.4 - stretch * 0.2, M_SAPO, ex=0.6)
        s.ellipse(9, by + 8.4, 4.2, 1.6, M_SAPO_SPOT, ex=0.4)
    # corpo
    s.ellipse(18, by - stretch * 0.4, 10 + stretch * 0.6, 7.2 - stretch * 0.5 + breath * 0.3, M_SAPO, ex=0.7)
    s.ellipse(20, by + 3.8, 7, 3.4 + breath * 0.4, M_SAPO_BELLY, ex=0.5)
    # cabeça e boca larga
    s.ellipse(26, by - 3 - stretch * 0.6, 7.2, 5.6, M_SAPO, ex=0.65)
    s.poly([(25, by - 0.5), (33.5, by - 2.6), (32.5, by - 0.6), (26, by + 1.2)], M_SAPO_MOUTH, ex=0.3)
    # olhos saltados
    s.ellipse(25, by - 8 - stretch * 0.6, 2.4, 2.4, M_SAPO, ex=0.7)
    s.ellipse(25.4, by - 8.2 - stretch * 0.6, 1.3, 1.3, M_SAPO_EYE, edge=False)
    s.ellipse(29.5, by - 7.2 - stretch * 0.6, 2.0, 2.0, M_SAPO, ex=0.7)
    s.ellipse(29.8, by - 7.4 - stretch * 0.6, 1.0, 1.0, M_SAPO_EYE, edge=False)
    # pata dianteira
    s.limb([(24, by + 3), (25, by + 7), (27, by + 8.5)], 1.6, 1.1, M_SAPO, ex=0.5)
    # manchas dorsais (autorais)
    for (x, y, r) in ((14, by - 4, 1.4), (19, by - 5.5, 1.2), (16.5, by - 1.5, 1.0), (11, by - 1, 1.0)):
        s.ellipse(x, y - stretch * 0.4, r, r * 0.8, M_SAPO_SPOT, ex=0.3, edge=False)
    # pupila em fenda
    s.px(25, int(by - 8 - stretch * 0.6), '#2a0d10'); s.px(30, int(by - 7 - stretch * 0.6), '#2a0d10')
    return s


# ======================================================================
# 7. SUSSURRANTES — espectros pequenos com capuz e chama-alma
# ======================================================================
M_SUS_CLOTH = Mat(ramp('#3b3a6b', 5, shift=0.1), alpha=0.92)
M_SUS_CLOTH2 = Mat(ramp('#5b5aa0', 5), alpha=0.8)
M_SUS_FACE = mat_glow('#d9fbff', '#4f6bd9')
M_SUS_SOUL = mat_glow('#ffffff', '#8ee8ff')


def sussurrante(phase: float, cast=0.0) -> Sprite:
    W, H = 28, 34
    s = Sprite(W, H)
    f = math.sin(phase * TAU)
    by = 15 + f * 1.2
    # cauda espectral ondulante
    tail = [(14, by + 6), (13 + f * 1.5, by + 11), (15 - f * 2, by + 15), (13 + f, by + 17)]
    s.limb(tail, 4.5, 0.6, M_SUS_CLOTH2, ex=0.4)
    # manto
    s.poly([(14, by - 9), (21, by + 2), (19, by + 8), (14, by + 6), (9, by + 8), (7, by + 2)], M_SUS_CLOTH, ex=0.5)
    # capuz
    s.ellipse(14, by - 4, 5.2, 5.6, M_SUS_CLOTH, ex=0.65)
    s.ellipse(14.6, by - 3.2, 3.0, 3.2, Mat([(5, 6, 18)] * 3, outline=(5, 6, 18)), ex=0.5)
    # olhos
    s.px(13, int(by - 3), '#d9fbff'); s.px(16, int(by - 3), '#d9fbff')
    # mãos e orbe de alma (cresce ao conjurar)
    r = 1.6 + cast * 1.6
    s.ellipse(21.5 + cast, by + 1, r + 0.8, r + 0.8, M_SUS_FACE, ex=0.8, edge=False)
    s.ellipse(21.5 + cast, by + 1, r, r, M_SUS_SOUL, ex=0.8, edge=False)
    s.ellipse(19, by + 2.5, 1.3, 1.1, M_SUS_CLOTH2)
    return s
