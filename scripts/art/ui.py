"""Kit de interface: cartas por raridade, painéis, botões, barras, ícones, logo e cursor."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pix import Sprite, mat, mat_glow, Mat, ramp, hx, mix, darken

TAU = math.tau
OBS = [(14, 12, 20), (22, 19, 30), (30, 26, 40), (40, 35, 52)]
RARITY = {
    'common': dict(metal='#3fae7e', gem='#7af0b0', name='jade'),
    'rare': dict(metal='#8a5ad6', gem='#d6a6ff', name='ametista'),
    'legendary': dict(metal='#e0a536', gem='#fff0a0', name='ouro'),
}


def _frame(W, H, metal, inner=OBS, rivets=True, corner=4, thick=3):
    img = np.zeros((H, W, 4), np.uint8)
    r = ramp(metal, 5, spread=0.55)
    yy, xx = np.mgrid[0:H, 0:W]
    # cantos chanfrados
    def inside(x, y, inset):
        cx = np.minimum(x - inset, W - 1 - inset - x); cy = np.minimum(y - inset, H - 1 - inset - y)
        return (cx >= 0) & (cy >= 0) & (cx + cy >= max(0, corner - inset))
    outer = inside(xx, yy, 0)
    body = inside(xx, yy, thick)
    img[outer] = (*darken(r[0], 0.4), 255)
    ring1 = inside(xx, yy, 1) & ~inside(xx, yy, 2)
    ring2 = inside(xx, yy, 2) & ~inside(xx, yy, thick)
    img[ring1] = (*r[3], 255)
    img[ring2] = (*r[1], 255)
    # luz no topo/esquerda da moldura
    top = ring1 & ((yy < H / 2) | (xx < W / 2))
    img[top & (yy < 3)] = (*r[4], 255)
    img[body] = (*inner[1], 255)
    # textura de obsidiana em faixas diagonais
    stripe = body & (((xx + yy * 2) % 11) == 0)
    img[stripe] = (*inner[2], 255)
    inner_edge = body & ~inside(xx, yy, thick + 1)
    img[inner_edge] = (*inner[0], 255)
    if rivets:
        for (x, y) in ((thick + 3, thick + 3), (W - thick - 4, thick + 3), (thick + 3, H - thick - 4), (W - thick - 4, H - thick - 4)):
            img[y, x] = (*r[4], 255); img[y + 1, x] = (*r[1], 255); img[y, x + 1] = (*r[2], 255)
    return img, r


def card_frame(rarity: str) -> Image.Image:
    W, H = 104, 148
    R = RARITY[rarity]
    img, r = _frame(W, H, R['metal'], corner=8, thick=4)
    g = ramp(R['gem'], 5, spread=0.5)
    # janela da ilustração
    x0, y0, x1, y1 = 16, 20, W - 16, 74
    img[y0 - 1:y1 + 1, x0 - 1:x1 + 1] = (*r[2], 255)
    img[y0:y1, x0:x1] = (*OBS[0], 255)
    img[y0, x0:x1] = (*r[0], 255)
    # faixa do nome
    img[80:92, 8:W - 8] = (*darken(r[1], 0.3), 255)
    img[80, 8:W - 8] = (*r[3], 255); img[91, 8:W - 8] = (*r[0], 255)
    # gema superior em losango
    cx = W // 2
    for dy in range(-6, 7):
        w = 6 - abs(dy)
        for dx in range(-w, w + 1):
            col = g[4] if (dx < 0 and dy < 0) else (g[2] if dx + dy < 3 else g[1])
            img[8 + dy, cx + dx] = (*col, 255)
    for dy in range(-7, 8):
        w = 7 - abs(dy)
        for dx in (-w, w):
            if img[8 + dy, cx + dx, 3] and abs(dx) == w:
                img[8 + dy, cx + dx] = (*darken(r[0], 0.4), 255)
    # ornamentos de canto (filigrana)
    for (sx, sy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        bx = 6 if sx > 0 else W - 7
        by = 6 if sy > 0 else H - 7
        for k in range(6):
            img[by + sy * k, bx] = (*r[4], 255)
            img[by, bx + sx * k] = (*r[4], 255)
        img[by + sy * 2, bx + sx * 2] = (*g[3], 255)
    # gema inferior
    for dy in range(-3, 4):
        w = 3 - abs(dy)
        for dx in range(-w, w + 1):
            img[H - 9 + dy, cx + dx] = (*g[2 if dy > 0 else 4], 255)
    if rarity == 'legendary':
        # raios solares saindo da gema
        for a in range(8):
            ang = a / 8 * TAU
            for k in range(9, 13):
                x = int(cx + math.cos(ang) * k); y = int(8 + math.sin(ang) * k * 0.7)
                if 0 <= y < H and 0 <= x < W and img[y, x, 3]:
                    img[y, x] = (*g[3], 255)
    return Image.fromarray(img, 'RGBA')


def panel(metal='#a86a3a', W=48, H=48) -> Image.Image:
    img, _ = _frame(W, H, metal, corner=5, thick=3)
    return Image.fromarray(img, 'RGBA')


def button(state='normal') -> Image.Image:
    metal = {'normal': '#a86a3a', 'hover': '#e0a536', 'press': '#7a4a2a'}[state]
    inner = OBS if state != 'hover' else [(26, 18, 22), (40, 26, 30), (52, 34, 36), (64, 44, 44)]
    img, _ = _frame(64, 24, metal, inner=inner, rivets=False, corner=3, thick=2)
    return Image.fromarray(img, 'RGBA')


def bar_frame() -> Image.Image:
    img, _ = _frame(40, 12, '#8a6a4a', rivets=False, corner=2, thick=2)
    return Image.fromarray(img, 'RGBA')


def bar_fill(color: str) -> Image.Image:
    r = ramp(color, 5, spread=0.5)
    img = np.zeros((8, 16, 4), np.uint8)
    rows = [4, 3, 2, 2, 2, 1, 1, 0]
    for y, k in enumerate(rows):
        img[y, :] = (*r[k], 255)
    img[1, ::4] = (*r[4], 255)
    return Image.fromarray(img, 'RGBA')


def slot() -> Image.Image:
    img, _ = _frame(28, 28, '#8a6a4a', rivets=False, corner=3, thick=2)
    return Image.fromarray(img, 'RGBA')


def cursor() -> Image.Image:
    img = np.zeros((16, 16, 4), np.uint8)
    pts = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)]
    for i in range(10):
        for j in range(i + 1):
            if j <= i and i < 11 and j < 7:
                img[i, j] = (232, 220, 192, 255)
    for i in range(11):
        img[i, 0] = (60, 30, 20, 255)
    for i in range(7):
        img[i + 3, i] = (255, 210, 120, 255)
    return Image.fromarray(img, 'RGBA')


# ------------------------------------------------------------------ ícones
def _icon(fn):
    s = Sprite(24, 24)
    fn(s)
    return s.render()


GOLD = mat('#e0a536', spec=0.6); FIRE = mat_glow('#fff2b0', '#ff6a1a'); BOW = mat('#c98a34', spec=0.5)
ICEm = Mat(ramp('#7ae8ff', 5, spread=0.5), spec=0.8); VOLTm = mat_glow('#ffffff', '#7a8aff')
WINDm = mat('#d8d2c4', n=4); STEEL = mat('#a8acb8', spec=0.6); WINE = mat('#7a2440'); LEAF = mat('#3fae7e')
RED = mat('#d0403a', spec=0.5); VIOL = Mat(ramp('#b27aff', 5, spread=0.5), spec=0.8)


def ic_arrow(s):
    s.limb([(4, 20), (17, 7)], 1.0, 1.0, BOW, ex=0.3)
    s.poly([(14, 5), (20, 4), (19, 10)], FIRE, ex=0.4)
    s.poly([(3, 17), (7, 21), (3, 22)], mat('#e8dcc0', n=3), ex=0.3)


def ic_crown(s):
    for k in range(8):
        a = k / 8 * TAU
        s.ellipse(12 + math.cos(a) * 7.5, 12 + math.sin(a) * 7.5, 2.4, 2.4, FIRE, edge=False)
    s.ellipse(12, 12, 3.6, 3.6, GOLD, ex=0.6)


def ic_lance(s):
    s.limb([(3, 21), (12, 12), (21, 3)], 1.4, 2.6, FIRE, ex=0.5, edge=False)
    s.poly([(17, 3), (22, 2), (21, 7)], mat_glow('#ffffff', '#ffd27a'), ex=0.4)


def ic_chain(s):
    pts = [(3, 4), (10, 10), (7, 13), (15, 18), (12, 20), (21, 22)]
    s.limb(pts, 1.4, 1.0, VOLTm, ex=0.4, edge=False)
    for (x, y) in ((3, 4), (21, 22)):
        s.ellipse(x, y, 2.2, 2.2, STEEL)


def ic_lotus(s):
    for k in range(6):
        a = k / 6 * TAU - math.pi / 2
        s.poly([(12, 12), (12 + math.cos(a - 0.35) * 6, 12 + math.sin(a - 0.35) * 6), (12 + math.cos(a) * 10.5, 12 + math.sin(a) * 10.5),
                (12 + math.cos(a + 0.35) * 6, 12 + math.sin(a + 0.35) * 6)], ICEm, ex=0.4)
    s.ellipse(12, 12, 2.6, 2.6, mat_glow('#ffffff', '#4ae0ff'), edge=False)


def ic_wind(s):
    for (y, l, w) in ((7, 15, 1.2), (12, 18, 1.4), (17, 12, 1.1)):
        s.limb([(3, y + 1), (3 + l * 0.5, y - 1), (3 + l, y + 1), (3 + l + 2, y - 2)], w, w * 0.6, WINDm, ex=0.4)


def ic_twin(s):
    for o in (-3, 3):
        s.limb([(4 + o, 20), (16 + o, 8 - o * 0.3)], 0.9, 0.9, BOW, ex=0.3)
        s.poly([(14 + o, 6 - o * 0.3), (19 + o, 5 - o * 0.3), (18 + o, 10 - o * 0.3)], FIRE, ex=0.4)


def ic_pierce(s):
    s.ellipse(12, 12, 6, 7, mat('#4a4656', n=4), ex=0.4)
    s.limb([(2, 22), (22, 2)], 1.0, 1.0, BOW, ex=0.3)
    s.poly([(18, 2), (23, 1), (22, 6)], FIRE, ex=0.4)


def ic_crown_big(s):
    ic_crown(s)
    s.poly([(12, 0), (14, 3), (10, 3)], GOLD, ex=0.3)
    s.poly([(12, 24), (14, 21), (10, 21)], GOLD, ex=0.3)


def ic_burn(s):
    s.poly([(12, 2), (19, 13), (16, 21), (8, 21), (5, 13)], FIRE, ex=0.6, edge=False)
    s.poly([(12, 10), (15, 16), (12, 20), (9, 16)], mat_glow('#ffffff', '#ffd27a'), ex=0.5, edge=False)


def ic_pulse(s):
    for r, m in ((10, FIRE), (6.5, GOLD)):
        s.ellipse(12, 12, r, r, m, ex=0.5, edge=False)
    s.ellipse(12, 12, 3.4, 3.4, mat('#2a1a1a', n=3), ex=0.5)


def ic_speed(s):
    s.poly([(6, 4), (12, 4), (13, 14), (20, 16), (20, 20), (6, 20)], mat('#6e4b3a', n=4), ex=0.3)
    for y in (8, 12, 16):
        s.line(1, y, 4, y, (255, 210, 130))


def ic_hp(s):
    s.poly([(4, 4), (20, 4), (19, 14), (12, 21), (5, 14)], STEEL, ex=0.4)
    s.poly([(8, 7), (16, 7), (15, 13), (12, 17), (9, 13)], RED, ex=0.4)


def ic_lifesteal(s):
    s.poly([(12, 2), (18, 13), (16, 19), (8, 19), (6, 13)], RED, ex=0.6)
    s.px(10, 10, '#ffffff'); s.px(10, 11, '#ffd0d0')


def ic_focus(s):
    s.poly([(6, 3), (18, 3), (13, 12), (18, 21), (6, 21), (11, 12)], GOLD, ex=0.3)
    s.poly([(9, 6), (15, 6), (12, 10)], FIRE, ex=0.4, edge=False)
    s.poly([(9, 19), (15, 19), (12, 15)], FIRE, ex=0.4, edge=False)


def ic_magnet(s):
    s.limb([(6, 4), (5, 14), (12, 20), (19, 14), (18, 4)], 2.4, 2.4, RED, ex=0.4)
    for x in (6, 18):
        s.ellipse(x, 4, 2.6, 1.6, STEEL)


def ic_fury(s):
    s.poly([(4, 20), (8, 6), (12, 14), (16, 3), (20, 20)], FIRE, ex=0.5, edge=False)


def ic_tornado(s):
    for k in range(5):
        y = 4 + k * 4
        w = 9 - k * 1.6
        s.ellipse(12 + (k % 2) * 1.5, y, w, 1.8, FIRE if k % 2 == 0 else WINDm, ex=0.5)


def ic_shatter(s):
    ic_chain(s)
    for (x, y) in ((17, 6), (6, 17)):
        s.poly([(x - 3, y), (x, y - 4), (x + 3, y), (x, y + 4)], ICEm, ex=0.4)


def ic_dawn(s):
    s.ellipse(12, 15, 7, 7, GOLD, ex=0.6)
    for k in range(5):
        a = math.pi + k / 4 * math.pi
        s.limb([(12 + math.cos(a) * 8, 15 + math.sin(a) * 8), (12 + math.cos(a) * 12, 15 + math.sin(a) * 12)], 1.2, 0.6, FIRE, ex=0.4, edge=False)
    s.line(2, 20, 22, 20, (120, 60, 30))


def ic_solar_arrows(s):
    ic_arrow(s)
    s.ellipse(17, 17, 4, 4, FIRE, edge=False)


def ic_heal(s):
    s.poly([(9, 3), (15, 3), (15, 9), (21, 9), (21, 15), (15, 15), (15, 21), (9, 21), (9, 15), (3, 15), (3, 9), (9, 9)], LEAF, ex=0.4)


def ic_armor(s):
    s.ellipse(12, 13, 8, 8.5, STEEL, ex=0.6)
    s.poly([(12, 6), (15, 12), (12, 19), (9, 12)], GOLD, ex=0.4)


def ic_reroll(s):
    s.limb([(5, 12), (7, 6), (13, 4), (19, 8)], 1.4, 1.4, GOLD, ex=0.4)
    s.limb([(19, 12), (17, 18), (11, 20), (5, 16)], 1.4, 1.4, GOLD, ex=0.4)
    s.poly([(17, 4), (21, 9), (16, 10)], GOLD, ex=0.3)


ICONS = {
    'w_arrow': ic_arrow, 'w_crown': ic_crown, 'w_lance': ic_lance, 'w_chain': ic_chain, 'w_lotus': ic_lotus,
    'w_wind': ic_wind, 'u_twin': ic_twin, 'u_pierce': ic_pierce, 'u_crown_big': ic_crown_big, 'u_burn': ic_burn,
    'u_pulse': ic_pulse, 'u_speed': ic_speed, 'u_hp': ic_hp, 'u_lifesteal': ic_lifesteal, 'u_focus': ic_focus,
    'u_magnet': ic_magnet, 'u_fury': ic_fury, 'c_tornado': ic_tornado, 'c_shatter': ic_shatter, 'c_dawn': ic_dawn,
    'l_solar': ic_solar_arrows, 'u_heal': ic_heal, 'u_armor': ic_armor, 'm_reroll': ic_reroll,
}


def icons():
    return {k: _icon(f) for k, f in ICONS.items()}


# ------------------------------------------------------------------- logo
def logo(font_path: str) -> Image.Image:
    W, H = 340, 76
    big = ImageFont.truetype(font_path, 40)
    small = ImageFont.truetype(font_path, 13)
    for f in (big, small):
        try:
            f.set_variation_by_name('Bold')
        except Exception:
            pass
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    d.fontmode = '1'
    title = 'VEIL OF EMBERS'
    tw = d.textlength(title, font=big)
    d.text(((W - tw) / 2, 6), title, font=big, fill=255)
    sub = '— chronicle of the rune archer —'
    sw = d.textlength(sub, font=small)
    m2 = Image.new('L', (W, H), 0); d2 = ImageDraw.Draw(m2); d2.fontmode = '1'
    d2.text(((W - sw) / 2, 56), sub, font=small, fill=255)
    a = np.asarray(m) > 0
    b = np.asarray(m2) > 0
    out = np.zeros((H, W, 4), np.uint8)
    rows = np.nonzero(a.any(1))[0]
    y0, y1 = rows.min(), rows.max()
    grad = [(255, 246, 214), (255, 214, 120), (240, 160, 60), (200, 90, 40), (150, 50, 40)]
    for y in range(H):
        t = (y - y0) / max(1, (y1 - y0))
        col = grad[min(4, max(0, int(t * 5)))]
        out[y, a[y]] = (*col, 255)
    out[b] = (232, 220, 192, 255)
    sol = a | b
    # contorno duplo: escuro + aro vinho
    def dil(mask, n):
        r = mask.copy()
        for _ in range(n):
            q = r.copy()
            q[1:] |= r[:-1]; q[:-1] |= r[1:]; q[:, 1:] |= r[:, :-1]; q[:, :-1] |= r[:, 1:]
            r = q
        return r
    o1 = dil(sol, 1) & ~sol
    o2 = dil(sol, 2) & ~dil(sol, 1)
    out[o1] = (40, 10, 22, 255)
    out[o2] = (120, 30, 50, 200)
    # brasas autorais sobre o título
    for (x, y) in ((40, 4), (88, 2), (150, 1), (212, 3), (262, 5), (120, 50), (190, 51)):
        out[y, x] = (255, 220, 140, 255); out[y + 1, x] = (255, 120, 40, 200)
    return Image.fromarray(out, 'RGBA')
