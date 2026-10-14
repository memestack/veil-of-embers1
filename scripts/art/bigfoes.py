"""Elites e chefes — silhuetas grandes, autoradas parte a parte."""
import math
from pix import Sprite, mat, mat_glow, Mat, ramp, hx

TAU = math.tau

# ======================================================================
# ELITE — GUARDIÃO DE CORAL (blindado, cone de estilhaços, armadura quebrável)
# ======================================================================
M_GC_BODY = mat('#3c5560', light_hue=0.5)
M_GC_ARMOR = mat('#7a8f8c', spec=0.5, dither=True)
M_GC_CORAL = mat('#d4483a', light_hue=0.08, spec=0.3)
M_GC_CORAL2 = mat('#ff7a52', n=4)
M_GC_GLOW = mat_glow('#e9fffb', '#44d6c4')
M_GC_LIMB = mat('#26363f', n=4)


def guardiao(phase: float, charge=0.0, armored=True) -> Sprite:
    W = 60
    s = Sprite(W, W)
    st = math.sin(phase * TAU)
    by = 32 - abs(st) * 0.8 + charge * 1.5
    lean = -charge * 2.5
    # quatro pernas atarracadas
    for i, ox in enumerate((-12, -5, 4, 11)):
        sw = st * (1 if i % 2 else -1) * 1.8
        s.limb([(30 + ox, by + 4), (30 + ox + sw * 0.3, by + 10), (30 + ox + sw, by + 15)], 2.8, 2.2, M_GC_LIMB, ex=0.5)
    # corpo
    s.ellipse(28 + lean, by, 17, 11.5, M_GC_BODY, ex=0.7)
    if armored:
        # placas de armadura sobre o corpo
        for (x, y, rx, ry) in ((18, by - 4, 7, 6), (28, by - 6, 7.5, 6.5), (38, by - 4, 7, 6), (24, by + 3, 7, 5), (34, by + 3, 7, 5)):
            s.ellipse(x + lean, y, rx, ry, M_GC_ARMOR, ex=0.55)
    else:
        for (x, y) in ((20, by - 3), (30, by - 5), (37, by - 1)):
            s.ellipse(x + lean, y, 3.5, 2.6, M_GC_GLOW, edge=False)
        for (x0, y0, x1, y1) in ((16, by - 6, 24, by + 4), (32, by - 8, 28, by + 2)):
            s.line(x0 + lean, y0, x1 + lean, y1, (20, 40, 46), 200)
    # galhada de coral nas costas
    for (bx, h, lean2) in ((15, 15, -0.5), (24, 19, -0.15), (33, 17, 0.2), (41, 12, 0.5)):
        x0, y0 = bx + lean, by - 7
        pts = [(x0, y0), (x0 + lean2 * 4, y0 - h * 0.5), (x0 + lean2 * 7, y0 - h)]
        s.limb(pts, 2.2, 0.9, M_GC_CORAL, ex=0.5)
        s.limb([(x0 + lean2 * 3, y0 - h * 0.4), (x0 + lean2 * 3 + 4 * (1 if lean2 >= 0 else -1), y0 - h * 0.65)], 1.3, 0.7, M_GC_CORAL2, ex=0.4)
    # cabeça/canhão de estilhaços (abre na carga)
    hx_ = 46 + lean * 1.4 + charge * 2
    s.ellipse(hx_, by + 2, 6.5, 6.0, M_GC_ARMOR if armored else M_GC_BODY, ex=0.6)
    s.ellipse(hx_ + 4, by + 2.5, 2.4 + charge * 1.2, 2.6 + charge * 1.2, M_GC_GLOW, edge=False)
    s.px(round(hx_ - 1), round(by - 1), '#e9fffb'); s.px(round(hx_ + 1), round(by - 1), '#e9fffb')
    return s


# ======================================================================
# ELITE — SACERDOTISA DE VIDRO (invoca lacaios, marca zona antes do ataque)
# ======================================================================
M_SV_ROBE = mat('#1d4f63', spread=0.55, shift=0.1)
M_SV_ROBE2 = mat('#2f8aa0', n=4)
M_SV_GLASS = Mat(ramp('#8ef0ff', 5, spread=0.5), spec=0.8, alpha=0.85)
M_SV_SKIN = mat('#b9d4d8', n=4)
M_SV_STAFF = mat('#3b2a40', n=4)
M_SV_ORB = mat_glow('#ffffff', '#3fe0ff')


def sacerdotisa(phase: float, cast=0.0) -> Sprite:
    W, H = 56, 68
    s = Sprite(W, H)
    f = math.sin(phase * TAU)
    by = 40 + f * 1.4
    # manto em sino flutuante
    s.poly([(28, by - 16), (38, by - 4), (42 + f, by + 18), (34, by + 22), (28, by + 20), (21, by + 22), (14 - f, by + 18), (18, by - 4)], M_SV_ROBE, ex=0.5)
    s.poly([(28, by - 8), (33, by + 2), (31, by + 20), (25, by + 20), (23, by + 2)], M_SV_ROBE2, ex=0.35)
    # braços abertos (sobem ao conjurar)
    for side in (-1, 1):
        s.limb([(28 + side * 7, by - 8), (28 + side * 12, by - 3 - cast * 7), (28 + side * 15, by - 1 - cast * 12)], 2.3, 1.6, M_SV_ROBE, ex=0.5)
        s.ellipse(28 + side * 15, by - 1 - cast * 12, 1.8, 1.8, M_SV_SKIN)
    # cajado
    sx = 45
    s.limb([(sx, by - 26 - cast * 3), (sx, by + 18)], 1.1, 1.1, M_SV_STAFF, ex=0.4)
    s.ellipse(sx, by - 28 - cast * 3, 3.0 + cast * 1.5, 3.4 + cast * 1.5, M_SV_ORB, edge=False)
    # cabeça e coroa de vidro em leque
    s.ellipse(28, by - 18, 5.4, 5.8, M_SV_ROBE, ex=0.6)
    s.ellipse(28, by - 17, 3.6, 4.0, M_SV_SKIN, ex=0.5)
    for k in range(-3, 4):
        ang = -math.pi / 2 + k * 0.33
        x1 = 28 + math.cos(ang) * (13 + (3 - abs(k)) * 1.6)
        y1 = by - 22 + math.sin(ang) * (13 + (3 - abs(k)) * 1.6)
        s.poly([(28 + k * 1.5 - 1.2, by - 23), (x1, y1), (28 + k * 1.5 + 1.2, by - 23)], M_SV_GLASS, ex=0.4)
    s.px(27, round(by - 17), '#0b2a33'); s.px(29, round(by - 17), '#0b2a33')
    s.px(27, round(by - 18), '#cffcff'); s.px(29, round(by - 18), '#cffcff')
    return s


# ======================================================================
# CHEFE 1 — BATRÁQUIO COLOSSAL
# ======================================================================
M_BT_SKIN = mat('#1f6b70', light_hue=0.25, dither=True)
M_BT_BELLY = mat('#9cc7a4', dither=True)
M_BT_PLATE = mat('#5d6a7a', spec=0.55, dither=True)
M_BT_CRYST = Mat(ramp('#59e0d0', 5, spread=0.55), spec=0.7)
M_BT_MOUTH = mat('#4c1830', n=4)
M_BT_EYE = mat_glow('#fff6c4', '#ff8c22')
M_BT_CRACK = mat_glow('#fff0b0', '#ff5a1e')
M_BT_SPOT = mat('#0f3a44', n=4)


def batraquio(pose: str, t: float, enraged=False) -> Sprite:
    W, H = 148, 132
    s = Sprite(W, H)
    lift = 0.0; squash = 0.0; mouth = 0.0; breath = 0.0
    if pose == 'idle':
        breath = math.sin(t * TAU)
    elif pose == 'crouch':
        squash = t
    elif pose == 'leap':
        lift = -18 * math.sin(min(1, t) * math.pi) - 4; squash = -0.6
    elif pose == 'land':
        squash = 1.0 - t
    elif pose == 'spit':
        mouth = math.sin(t * math.pi)
    by = 82 + lift + squash * 4
    sw = 1 + squash * 0.12; sh = 1 - squash * 0.12
    # pata traseira
    s.ellipse(40, by + 18, 22 * sw, 16 * sh, M_BT_SKIN, ex=0.65)
    s.ellipse(32, by + 34 - squash * 2, 15 * sw, 5, M_BT_SPOT, ex=0.4)
    # corpo
    s.ellipse(70, by, 46 * sw, 34 * sh + breath * 0.8, M_BT_SKIN, ex=0.72)
    s.ellipse(80, by + 18, 30 * sw, 14 * sh + breath, M_BT_BELLY, ex=0.5)
    # placas minerais no dorso
    plates = ((46, by - 22, 11, 8), (62, by - 28, 12, 9), (79, by - 27, 11, 8), (54, by - 12, 9, 7), (70, by - 15, 10, 7.5))
    for (x, y, rx, ry) in plates:
        s.ellipse(x, y, rx * sw, ry * sh, M_BT_PLATE, ex=0.55)
    # cristais que brotam das placas
    for (x, y, h, lean) in ((48, by - 28, 12, -0.4), (64, by - 35, 16, 0.0), (80, by - 33, 13, 0.35), (57, by - 18, 9, -0.2)):
        s.poly([(x - 3, y + 2), (x + lean * h, y - h), (x + 3, y + 2)], M_BT_CRYST, ex=0.4)
    # cabeça
    hy = by - 8 - squash * 2
    s.ellipse(103, hy, 26 * sw, 22 * sh, M_BT_SKIN, ex=0.68)
    # boca (abre ao cuspir)
    m = mouth * 8
    s.poly([(86, hy + 6), (128, hy + 2 - m * 0.5), (126, hy + 7 + m), (88, hy + 12 + m * 0.6)], M_BT_MOUTH, ex=0.3)
    if mouth > 0.3:
        s.ellipse(118, hy + 6 + m * 0.3, 4 + m * 0.4, 3 + m * 0.4, M_BT_CRACK, edge=False)
    # olhos saltados
    for (ex_, ey, r) in ((96, hy - 18, 7.0), (114, hy - 15, 6.0)):
        s.ellipse(ex_, ey, r, r, M_BT_SKIN, ex=0.7)
        s.ellipse(ex_ + 1, ey - 0.5, r * 0.62, r * 0.62, M_BT_EYE, edge=False)
        s.line(ex_ + 1, ey - r * 0.5, ex_ + 1, ey + r * 0.5, (40, 10, 10))
    # pata dianteira
    s.limb([(100, by + 18), (104, by + 30), (110, by + 36 - squash * 2)], 6, 4.5, M_BT_SKIN, ex=0.55)
    for k in range(3):
        s.ellipse(106 + k * 4, by + 37 - squash * 2, 2.6, 1.8, M_BT_SPOT, ex=0.4)
    # manchas
    for (x, y, r) in ((50, by + 2, 4), (62, by + 8, 3), (90, by - 2, 3.5), (40, by + 12, 3)):
        s.ellipse(x, y, r * sw, r * 0.8 * sh, M_BT_SPOT, ex=0.3, edge=False)
    # fase 2: rachaduras incandescentes
    if enraged:
        for path in (((46, by - 4), (54, by + 2), (52, by + 10), (60, by + 16)),
                     ((76, by - 10), (72, by - 2), (78, by + 6)),
                     ((100, hy - 4), (106, hy + 1), (102, hy + 5))):
            s.limb(path, 1.3, 0.8, M_BT_CRACK, ex=0.3, edge=False)
    return s


# ======================================================================
# CHEFE 2 — CORAÇÃO DO VÉU (organismo cristalino pulsante, três fases)
# ======================================================================
M_CV_SHELL = Mat(ramp('#2a6f8a', 5, spread=0.55), spec=0.6, dither=True)
M_CV_SHELL2 = Mat(ramp('#3d9fb0', 5, spread=0.5), spec=0.7)
M_CV_CORAL = mat('#b8323a', light_hue=0.06, dither=True)
M_CV_CORE = mat_glow('#fff8e0', '#ff4a6a')
M_CV_CORE2 = mat_glow('#ffffff', '#ff9a3a')
M_CV_VEIN = mat_glow('#ffd0c0', '#c01848')
M_CV_FLESH = mat('#4a1630', dither=True)


def coracao(phase: int, t: float) -> Sprite:
    """phase 1: casca íntegra; 2: casca rachada, veias; 3: núcleo exposto."""
    W = 164
    s = Sprite(W, W)
    c = 82
    pulse = math.sin(t * TAU)
    beat = max(0, math.sin(t * TAU * 2)) ** 3
    # raízes de coral na base
    for k in range(7):
        ang = math.pi * (0.15 + k * 0.118)
        pts = [(c + math.cos(ang) * 30, c + 18 + math.sin(ang) * 18),
               (c + math.cos(ang) * 52, c + 30 + math.sin(ang) * 24 + pulse),
               (c + math.cos(ang) * 70, c + 34 + math.sin(ang) * 26)]
        s.limb(pts, 6, 1.8, M_CV_CORAL, ex=0.5)
    # carne pulsante
    s.ellipse(c, c + 6, 44 + beat * 2, 40 + beat * 2, M_CV_FLESH, ex=0.7)
    if phase >= 2:
        for k in range(9):
            ang = k * TAU / 9 + 0.2
            s.limb([(c + math.cos(ang) * 10, c + 6 + math.sin(ang) * 10),
                    (c + math.cos(ang + 0.2) * 28, c + 6 + math.sin(ang + 0.2) * 26),
                    (c + math.cos(ang + 0.1) * 40, c + 6 + math.sin(ang + 0.1) * 36)], 1.8, 0.8, M_CV_VEIN, ex=0.3, edge=False)
    # placas de casca cristalina
    n_plates = 10 if phase == 1 else (7 if phase == 2 else 3)
    for k in range(n_plates):
        ang = -math.pi / 2 + (k - n_plates / 2) * (TAU / 10) * (1.0 if phase == 1 else 1.12)
        r = 34 + beat * 1.5
        x, y = c + math.cos(ang) * r, c + 2 + math.sin(ang) * r * 0.9
        pts = [(x + math.cos(ang + 1.6) * 11, y + math.sin(ang + 1.6) * 11),
               (x + math.cos(ang) * 18, y + math.sin(ang) * 18),
               (x + math.cos(ang - 1.6) * 11, y + math.sin(ang - 1.6) * 11),
               (x - math.cos(ang) * 8, y - math.sin(ang) * 8)]
        s.poly(pts, M_CV_SHELL if k % 2 else M_CV_SHELL2, ex=0.45)
    # espinhos de cristal no topo
    for k in range(5):
        x = c - 24 + k * 12
        h = 22 + (2 - abs(k - 2)) * 9 + (pulse * 2 if phase == 3 else 0)
        s.poly([(x - 5, c - 20), (x + (k - 2) * 2, c - 20 - h), (x + 5, c - 20)], M_CV_SHELL2, ex=0.4)
    # núcleo
    cr = (13 if phase == 1 else (17 if phase == 2 else 22)) + beat * 3
    s.ellipse(c, c + 4, cr, cr * 1.05, M_CV_CORE, ex=0.8, edge=False)
    s.ellipse(c - 2, c + 1, cr * 0.5, cr * 0.5, M_CV_CORE2, ex=0.8, edge=False)
    if phase == 1:
        # véu de casca sobre o núcleo (só uma fresta)
        s.poly([(c - 16, c - 6), (c + 16, c - 6), (c + 12, c + 18), (c - 12, c + 18)], M_CV_SHELL, ex=0.4)
        s.line(c, c - 4, c, c + 16, (255, 120, 140))
        s.line(c + 1, c - 2, c + 1, c + 12, (255, 220, 200))
    return s


def tentaculo_seg(i: int) -> Sprite:
    """Segmento de tentáculo de coral (encadeado no jogo para formar raízes animadas)."""
    s = Sprite(20, 20)
    r = 7 - i * 0.8
    s.ellipse(10, 10, r + 1, r, M_CV_CORAL, ex=0.55)
    s.ellipse(9, 8.5, r * 0.35, r * 0.3, mat('#ff8a7a', n=3), edge=False)
    return s


def tentaculo_ponta() -> Sprite:
    s = Sprite(24, 24)
    s.poly([(4, 8), (22, 12), (4, 16)], M_CV_CORAL, ex=0.5)
    s.poly([(8, 10), (20, 12), (8, 14)], M_CV_SHELL2, ex=0.4)
    return s
