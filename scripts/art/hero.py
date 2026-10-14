"""
Arqueira-rúnica — protagonista. Quadro 64x64, pés em y≈55, vista 3/4.
Direções: down (frente), up (costas), side (direita; o jogo espelha para a esquerda).
Poses: idle, walk, shoot, dash, hurt, death.
Paleta: marfim (capuz/túnica), bronze envelhecido (armadura), vinho escuro (capa),
âmbar (arco rúnico e detalhes).
"""
import math
from pix import Sprite, mat, mat_glow, Mat, ramp

TAU = math.tau
M_SKIN = mat('#d8a487', n=4, spread=0.5)
M_HAIR = mat('#7c2e2a', n=4)
M_HOOD = mat('#e8dcc0', spread=0.55, shadow_hue=0.72)
M_TUNIC = mat('#bfae8a', n=4)
M_LEG = mat('#6e4b3a', n=4)
M_HOOD_IN = Mat([(44, 22, 30), (62, 32, 38), (80, 44, 46)], outline=(30, 14, 22))
M_CLOAK = mat('#521630', spread=0.5, shift=0.12)
M_CLOAK_IN = mat('#3a0f22', n=4)
M_ARMOR = mat('#a8743a', spec=0.6, light_hue=0.12)
M_BELT = mat('#7a3e1e', n=4)
M_BOOT = mat('#3f2b25', n=4)
M_BOW = mat('#c98a34', spec=0.5)
M_RUNE = mat_glow('#fff2b0', '#ff9a2a')
M_STRING = Mat([(255, 236, 190)] * 3, emissive=True, outline=(120, 70, 30))


def _bow_vertical(s, x, top, bot, bend, glow=0.0):
    mid = (top + bot) / 2
    s.limb([(x, top), (x + bend * 0.7, top + (mid - top) * 0.45), (x + bend, mid),
            (x + bend * 0.7, bot - (bot - mid) * 0.45), (x, bot)], 1.25, 1.25, M_BOW, ex=0.45)
    s.ellipse(x + bend, mid, 1.6 + glow, 2.0 + glow, M_RUNE, edge=False)
    s.px(round(x + bend * 0.75), round(top + 3), '#ffd27a')
    s.px(round(x + bend * 0.75), round(bot - 3), '#ffd27a')


def hero(dirn: str, pose: str, t: float) -> Sprite:
    s = Sprite(64, 64)
    stride = 0.0; bob = 0.0; sway = 0.0; lean = 0.0; pull = 0.0; kneel = 0.0
    if pose == 'idle':
        bob = math.sin(t * TAU) * 0.5; sway = math.sin(t * TAU) * 1.0
    elif pose == 'walk':
        stride = math.sin(t * TAU) * 3.2; bob = -abs(math.cos(t * TAU)) * 1.2 + 0.6; sway = -stride * 0.6
    elif pose == 'shoot':
        pull = [0.4, 1.0, 1.0, 0.0][int(t * 4) % 4]; sway = 0.5
    elif pose == 'dash':
        lean = 3.0; stride = 3.5 * (1 if t < 0.5 else -1); sway = -4
    elif pose == 'hurt':
        lean = -2.0; bob = 1.0; sway = 2.0
    elif pose == 'death':
        kneel = t
    yb = bob + kneel * 8
    if dirn == 'down':
        _front(s, stride, yb, sway, lean, pull, kneel)
    elif dirn == 'up':
        _back(s, stride, yb, sway, lean, pull)
    else:
        _side(s, stride, yb, sway, lean, pull)
    return s


def _front(s, stride, yb, sway, lean, pull, kneel):
    cx = 32
    # capa atrás do corpo
    s.poly([(24, 30 + yb), (40, 30 + yb), (43 + sway * 0.4, 53), (32, 55 - kneel * 3), (21 + sway * 0.4, 53)], M_CLOAK_IN, ex=0.35)
    # pernas
    if kneel < 0.5:
        for side, ph in ((-1, 1), (1, -1)):
            st = stride * ph * 0.35
            hx = cx + side * 2.6
            s.limb([(hx, 43 + yb), (hx + side * 0.3, 48 + yb * 0.5 - st * 0.4), (hx + side * 0.5, 53 - abs(st) * 0.3)], 2.0, 1.6, M_LEG, ex=0.5)
            s.ellipse(hx + side * 0.5, 54 - abs(st) * 0.3 - max(0, st) * 0.6, 2.4, 1.6, M_BOOT, ex=0.5)
    else:
        s.ellipse(cx - 4, 53, 4.2, 2.2, M_BOOT, ex=0.5); s.ellipse(cx + 4, 53, 4.2, 2.2, M_BOOT, ex=0.5)
    # saia da túnica
    s.poly([(26, 40 + yb), (38, 40 + yb), (39.5, 47 + yb), (32, 48.5 + yb), (24.5, 47 + yb)], M_TUNIC, ex=0.4)
    s.poly([(28, 41 + yb), (36, 41 + yb), (35, 47.5 + yb), (29, 47.5 + yb)], M_CLOAK, ex=0.35)  # faixa vinho
    # peitoral
    s.ellipse(cx, 35.5 + yb, 6.6, 6.0, M_ARMOR, ex=0.6)
    s.poly([(25.5, 39.5 + yb), (38.5, 39.5 + yb), (38.5, 42 + yb), (25.5, 42 + yb)], M_BELT, ex=0.3)
    s.ellipse(cx, 40.8 + yb, 1.4, 1.2, M_RUNE, edge=False)
    # braços
    s.limb([(26, 32 + yb), (23.8, 37 + yb), (23.5, 41 + yb)], 1.9, 1.5, M_HOOD, ex=0.5)
    s.limb([(38, 32 + yb), (40.2, 37 + yb - pull * 2), (40 - pull * 2, 41 + yb - pull * 4)], 1.9, 1.5, M_HOOD, ex=0.5)
    s.ellipse(23.5, 41.6 + yb, 1.6, 1.5, M_SKIN)
    s.ellipse(40 - pull * 2, 41.6 + yb - pull * 4, 1.5, 1.4, M_SKIN)
    # ombreiras
    s.ellipse(25.6, 31.6 + yb, 3.2, 2.6, M_ARMOR, ex=0.6)
    s.ellipse(38.4, 31.6 + yb, 3.2, 2.6, M_ARMOR, ex=0.6)
    # arco na mão esquerda (lado esquerdo da tela)
    _bow_vertical(s, 21.2, 29 + yb, 50 + yb, -2.6, glow=pull * 0.6)
    s.line(21.2, 29 + yb, 21.2, 50 + yb, (255, 232, 180), 200)
    # trança sobre o ombro
    s.limb([(36.5, 26 + yb), (38.2, 31 + yb), (37.6, 36 + yb)], 1.7, 1.0, M_HAIR, ex=0.5)
    # cabeça: capuz, rosto, franja
    s.ellipse(cx, 23.5 + yb, 7.2, 6.8, M_HOOD, ex=0.6)
    s.ellipse(cx, 25.2 + yb, 5.4, 5.0, M_HOOD_IN, ex=0.4)
    s.ellipse(cx, 26.0 + yb, 4.4, 4.1, M_SKIN, ex=0.55)
    s.limb([(28.2, 22.5 + yb), (27.8, 26 + yb), (28.4, 29 + yb)], 1.2, 0.7, M_HAIR, ex=0.4)
    s.limb([(35.8, 22.5 + yb), (36.2, 26 + yb), (35.6, 29 + yb)], 1.2, 0.7, M_HAIR, ex=0.4)
    s.poly([(29, 22 + yb), (35, 22 + yb), (34, 23.6 + yb), (32, 23 + yb), (30, 23.8 + yb)], M_HAIR, ex=0.3)
    s.poly([(30, 15.8 + yb), (34, 15.8 + yb), (32, 18.8 + yb)], M_ARMOR, ex=0.3)  # diadema
    for x in (30, 34):
        s.px(x, round(26 + yb), '#1e0f14'); s.px(x, round(25 + yb), '#1e0f14')
        s.px(x + 1, round(25 + yb), '#fff3d6', 200)
    s.px(32, round(28 + yb), '#a8604c', 160)
    s.px(32, round(17 + yb), '#ffe7a0')
    # runas no peitoral
    for (x, y) in ((32, 34), (31, 35), (33, 35), (32, 36)):
        s.px(x, round(y + yb), '#ffd98a', 220)


def _back(s, stride, yb, sway, lean, pull):
    cx = 32
    for side, ph in ((-1, 1), (1, -1)):
        st = stride * ph * 0.35
        hx = cx + side * 2.6
        s.limb([(hx, 43 + yb), (hx + side * 0.3, 48 + yb * 0.5 + st * 0.3), (hx + side * 0.5, 53 - abs(st) * 0.3)], 2.0, 1.6, M_LEG, ex=0.5)
        s.ellipse(hx + side * 0.5, 54 - abs(st) * 0.3 - max(0, -st) * 0.6, 2.4, 1.6, M_BOOT, ex=0.5)
    s.limb([(26, 32 + yb), (23.8, 37 + yb), (23.5, 41 + yb)], 1.9, 1.5, M_HOOD, ex=0.5)
    s.limb([(38, 32 + yb), (40.2, 37 + yb), (40.5, 41 + yb)], 1.9, 1.5, M_HOOD, ex=0.5)
    # arco preso às costas (visível em diagonal)
    s.limb([(26, 26 + yb), (31, 33 + yb), (38, 44 + yb)], 1.2, 1.2, M_BOW, ex=0.4)
    # capa cobre o tronco
    s.poly([(25, 29 + yb), (39, 29 + yb), (43 + sway * 0.5, 52), (37, 54), (32, 52.5), (27, 54), (21 + sway * 0.5, 52)], M_CLOAK, ex=0.45)
    for x0 in (28, 32, 36):  # dobras
        s.line(x0, 34 + yb, x0 + sway * 0.3 + (x0 - 32) * 0.3, 51, (60, 14, 34), 170)
    s.ellipse(25.6, 31.6 + yb, 3.2, 2.6, M_ARMOR, ex=0.6)
    s.ellipse(38.4, 31.6 + yb, 3.2, 2.6, M_ARMOR, ex=0.6)
    # capuz e trança
    s.ellipse(cx, 23.5 + yb, 7.0, 6.8, M_HOOD, ex=0.65)
    s.line(29, 19 + yb, 30, 28 + yb, (170, 150, 120), 160); s.line(35, 19 + yb, 34, 28 + yb, (170, 150, 120), 160)
    s.limb([(32, 26 + yb), (32.5 + sway * 0.2, 32 + yb), (32 + sway * 0.4, 38 + yb)], 1.9, 1.0, M_HAIR, ex=0.5)
    s.ellipse(32 + sway * 0.4, 38.5 + yb, 1.4, 1.2, M_ARMOR)
    # aljava rúnica
    s.ellipse(36.5, 36 + yb, 1.6, 3.6, M_BELT, ex=0.5)
    for i in range(3):
        s.px(35.5 + i, round(31.5 + yb), '#ffd27a')


def _side(s, stride, yb, sway, lean, pull):
    cx = 31 + lean * 0.4
    # capa esvoaçando para trás
    s.poly([(cx - 3, 29 + yb), (cx + 1, 29 + yb), (cx - 2, 46 + yb), (cx - 9 + sway * 0.8, 53),
            (cx - 11 + sway, 49), (cx - 6, 38 + yb)], M_CLOAK, ex=0.4)
    # perna de trás
    st = stride
    s.limb([(cx - 1, 43 + yb), (cx - 1 - st * 0.4, 48 + yb * 0.5), (cx - 1 - st * 0.9, 53)], 1.9, 1.6, mat('#523628', n=4), ex=0.5)
    s.ellipse(cx - 0.2 - st * 0.9, 54, 2.6, 1.5, M_BOOT, ex=0.5)
    # braço de trás (puxa a corda)
    hand_x = cx + 6 - pull * 5
    s.limb([(cx - 0.5, 32 + yb), (cx + 2 - pull * 2, 36 + yb), (hand_x, 36.5 + yb)], 1.7, 1.4, M_HOOD, ex=0.5)
    # tronco
    s.poly([(cx - 3.5, 40 + yb), (cx + 4, 40 + yb), (cx + 4.5, 47 + yb), (cx - 4, 47 + yb)], M_TUNIC, ex=0.4)
    s.ellipse(cx + 0.5, 35.5 + yb, 4.6, 6.0, M_ARMOR, ex=0.6)
    s.poly([(cx - 4, 39.5 + yb), (cx + 5, 39.5 + yb), (cx + 5, 42 + yb), (cx - 4, 42 + yb)], M_BELT, ex=0.3)
    # perna da frente
    s.limb([(cx + 1.5, 43 + yb), (cx + 2 + st * 0.4, 48 + yb * 0.5), (cx + 2 + st * 0.9, 53)], 2.0, 1.6, M_LEG, ex=0.5)
    s.ellipse(cx + 3.2 + st * 0.9, 54, 2.7, 1.5, M_BOOT, ex=0.5)
    # arco à frente
    bx = cx + 9 + lean * 0.5
    _bow_vertical(s, bx, 28 + yb, 46 + yb, 2.8, glow=pull * 0.8)
    s.line(bx, 28 + yb, hand_x, 36.5 + yb, (255, 232, 180), 210)
    s.line(hand_x, 36.5 + yb, bx, 46 + yb, (255, 232, 180), 210)
    # braço da frente segura o arco
    s.limb([(cx + 1, 32 + yb), (cx + 5, 35 + yb), (bx + 2.4, 37 + yb)], 1.8, 1.4, M_HOOD, ex=0.5)
    s.ellipse(bx + 2.4, 37 + yb, 1.5, 1.5, M_SKIN)
    s.ellipse(hand_x, 36.5 + yb, 1.4, 1.4, M_SKIN)
    s.ellipse(cx + 0.5, 31.5 + yb, 3.4, 2.6, M_ARMOR, ex=0.6)
    # cabeça em perfil
    s.limb([(cx - 3, 26 + yb), (cx - 6, 30 + yb), (cx - 6.5 + sway * 0.3, 35 + yb)], 1.8, 1.0, M_HAIR, ex=0.5)
    s.ellipse(cx, 23.5 + yb, 6.0, 6.6, M_HOOD, ex=0.6)
    s.ellipse(cx + 3.0, 25.2 + yb, 3.6, 4.6, M_HOOD_IN, ex=0.4)
    s.ellipse(cx + 3.6, 25.8 + yb, 2.7, 3.7, M_SKIN, ex=0.5)
    s.poly([(cx + 1.5, 22 + yb), (cx + 5.6, 22 + yb), (cx + 5.0, 23.4 + yb), (cx + 2.0, 24.5 + yb)], M_HAIR, ex=0.3)
    s.px(round(cx + 5), round(25.5 + yb), '#1e0f14'); s.px(round(cx + 5), round(24.5 + yb), '#1e0f14')
    s.px(round(cx + 1), round(17.5 + yb), '#ffe7a0')
    for (x, y) in ((0, 34), (1, 35), (0, 36)):
        s.px(round(cx + x + 1), round(y + yb), '#ffd98a', 220)


ANIMS = {
    'idle': (4, 6), 'walk': (6, 11), 'shoot': (4, 12), 'dash': (3, 16), 'hurt': (2, 10),
}


def all_frames():
    """Retorna dict nome->lista de imagens. Nomes: hero_<dir>_<pose>."""
    out = {}
    for d in ('down', 'up', 'side'):
        for pose, (n, _fps) in ANIMS.items():
            out[f'hero_{d}_{pose}'] = [hero(d, pose, i / n).render() for i in range(n)]
    out['hero_down_death'] = [hero('down', 'death', min(1, i / 4)).render() for i in range(6)]
    return out
