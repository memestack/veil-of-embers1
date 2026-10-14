"""
Gera TODOS os assets visuais do jogo em public/assets/ a partir dos scripts autorais.
Uso:  python3 scripts/art/build_assets.py
Requer: Python 3.10+, Pillow, NumPy, SciPy.
"""
import json
import math
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pix import flash, dissolve_frames, shadow_sprite, upscale  # noqa: E402
import enemies as EN  # noqa: E402
import bigfoes as BF  # noqa: E402
import hero as HE  # noqa: E402
import env as EV  # noqa: E402
import fx as FX  # noqa: E402
import ui as UI  # noqa: E402
import terrain as TR  # noqa: E402
import creatures2 as C2  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'assets')


def pack(name: str, anims: dict, subdir: str, pad: int = 2, max_w: int = 2048):
    """Empacota quadros (dict anim -> [Image]) em atlas PNG + JSON no formato de spritesheet do PixiJS."""
    items = []
    for an, frames in anims.items():
        for i, im in enumerate(frames):
            items.append((f'{an}_{i}', im))
    items.sort(key=lambda kv: (-kv[1].height, -kv[1].width))
    x = y = pad; row_h = 0; W = 0
    pos = {}
    for key, im in items:
        if x + im.width + pad > max_w:
            x = pad; y += row_h + pad; row_h = 0
        pos[key] = (x, y)
        x += im.width + pad
        row_h = max(row_h, im.height)
        W = max(W, x)
    H = y + row_h + pad
    def p2(v):
        n = 1
        while n < v:
            n *= 2
        return n
    W, H = p2(W), p2(H)
    sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    frames = {}
    for key, im in items:
        px, py = pos[key]
        sheet.alpha_composite(im, (px, py))
        frames[key] = {
            'frame': {'x': px, 'y': py, 'w': im.width, 'h': im.height},
            'rotated': False, 'trimmed': False,
            'spriteSourceSize': {'x': 0, 'y': 0, 'w': im.width, 'h': im.height},
            'sourceSize': {'w': im.width, 'h': im.height},
        }
    data = {
        'frames': frames,
        'animations': {an: [f'{an}_{i}' for i in range(len(fr))] for an, fr in anims.items()},
        'meta': {'app': 'veu-de-brasas/scripts/art', 'image': f'{name}.png', 'format': 'RGBA8888',
                 'size': {'w': W, 'h': H}, 'scale': '1'},
    }
    d = os.path.join(OUT, subdir)
    os.makedirs(d, exist_ok=True)
    sheet.save(os.path.join(d, f'{name}.png'), optimize=True)
    with open(os.path.join(d, f'{name}.json'), 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f'  atlas {subdir}/{name}.png {W}x{H}  ({len(items)} quadros, {len(anims)} animações)')
    return data


def with_flash(anims: dict) -> dict:
    out = dict(anims)
    for k, frames in anims.items():
        out[k + '_flash'] = [flash(f) for f in frames]
    return out


def build_hero():
    print('herói')
    A = HE.all_frames()
    A['hero_down_hurt_flash'] = [flash(f, (255, 200, 200)) for f in A['hero_down_hurt']]
    pack('hero', A, 'characters')


def build_enemies():
    print('inimigos comuns')
    A = {}
    for d in range(8):
        a = EN.DIRS8[d]
        A[f'ferr_d{d}_walk'] = [EN.ferrugineo(a, i / 4).render() for i in range(4)]
        A[f'ferr_d{d}_attack'] = [EN.ferrugineo(a, 0.25, k).render() for k in (0.6, 1.0)]
        A[f'mord_d{d}_walk'] = [EN.mordalume(a, i / 4).render() for i in range(4)]
        A[f'mord_d{d}_attack'] = [EN.mordalume(a, 0.25, k).render() for k in (0.6, 1.0)]
        A[f'vesp_d{d}_fly'] = [EN.vespa(a, i / 4).render() for i in range(4)]
        A[f'vesp_d{d}_dive'] = [EN.vespa(a, i / 4, 1.0).render() for i in range(2)]
    A['lodo_walk'] = [EN.filho_do_lodo(i / 4).render() for i in range(4)]
    A['lodo_attack'] = [EN.filho_do_lodo(0.25, k).render() for k in (0.6, 1.0)]
    A['carap_walk'] = [EN.carapaca(i / 4).render() for i in range(4)]
    A['carap_attack'] = [EN.carapaca(0.0, k).render() for k in (0.5, 1.0)]
    A['sapo_idle'] = [EN.sapo('idle', i / 2).render() for i in range(2)]
    A['sapo_crouch'] = [EN.sapo('crouch', k).render() for k in (0.5, 1.0)]
    A['sapo_leap'] = [EN.sapo('leap', k).render() for k in (0.25, 0.5, 0.75)]
    A['sapo_land'] = [EN.sapo('land', k).render() for k in (0.0, 0.6)]
    A['suss_float'] = [EN.sussurrante(i / 4).render() for i in range(4)]
    A['suss_cast'] = [EN.sussurrante(0.0, k).render() for k in (0.33, 0.66, 1.0)]
    A = with_flash(A)
    tints = {'ferr': (255, 120, 60), 'mord': (90, 255, 220), 'vesp': (140, 240, 255), 'lodo': (255, 220, 160),
             'carap': (255, 110, 70), 'sapo': (110, 255, 200), 'suss': (160, 190, 255)}
    base = {'ferr': A['ferr_d2_walk'][0], 'mord': A['mord_d2_walk'][0], 'vesp': A['vesp_d2_fly'][0], 'lodo': A['lodo_walk'][0],
            'carap': A['carap_walk'][0], 'sapo': A['sapo_idle'][0], 'suss': A['suss_float'][0]}
    for k, img in base.items():
        A[f'{k}_death'] = dissolve_frames(img, 5, tints[k], seed=hash(k) % 1000)
    pack('enemies', A, 'enemies')


def build_bigfoes():
    print('elites e chefes')
    A = {}
    A['guard_walk'] = [BF.guardiao(i / 4).render() for i in range(4)]
    A['guard_charge'] = [BF.guardiao(0, k).render() for k in (0.35, 0.7, 1.0)]
    A['guardb_walk'] = [BF.guardiao(i / 4, 0, False).render() for i in range(4)]
    A['guardb_charge'] = [BF.guardiao(0, k, False).render() for k in (0.35, 0.7, 1.0)]
    A['sacer_float'] = [BF.sacerdotisa(i / 4).render() for i in range(4)]
    A['sacer_cast'] = [BF.sacerdotisa(i / 4, k).render() for i, k in enumerate((0.3, 0.6, 0.9, 1.0))]
    A = with_flash(A)
    A['guard_death'] = dissolve_frames(A['guardb_walk'][0], 6, (120, 255, 230), 11)
    A['sacer_death'] = dissolve_frames(A['sacer_float'][0], 6, (140, 240, 255), 12)
    pack('elites', A, 'enemies')

    B = {}
    for pre, en in (('batr', False), ('batr2', True)):
        B[f'{pre}_idle'] = [BF.batraquio('idle', i / 4, en).render() for i in range(4)]
        B[f'{pre}_crouch'] = [BF.batraquio('crouch', k, en).render() for k in (0.5, 1.0)]
        B[f'{pre}_leap'] = [BF.batraquio('leap', k, en).render() for k in (0.3, 0.5, 0.7)]
        B[f'{pre}_land'] = [BF.batraquio('land', k, en).render() for k in (0.0, 0.5)]
        B[f'{pre}_spit'] = [BF.batraquio('spit', k, en).render() for k in (0.3, 0.5, 0.8)]
    B['batr_flash'] = [flash(B['batr_idle'][0])]
    B['batr_death'] = dissolve_frames(B['batr2_idle'][0], 7, (255, 170, 80), 21)
    pack('boss_frog', B, 'enemies')

    C = {}
    for ph in (1, 2, 3):
        C[f'heart{ph}_pulse'] = [BF.coracao(ph, i / 6).render() for i in range(6)]
    C['heart_flash'] = [flash(C['heart1_pulse'][0])]
    C['heart_death'] = dissolve_frames(C['heart3_pulse'][0], 8, (255, 140, 180), 33)
    C['tentacle_seg'] = [BF.tentaculo_seg(i).render() for i in range(4)]
    C['tentacle_tip'] = [BF.tentaculo_ponta().render()]
    pack('boss_heart', C, 'enemies')


def build_enemies2():
    print('criaturas — segunda leva')
    A = {}
    A['wisp_float'] = [C2.wisp(i / 4).render() for i in range(4)]
    A['wisp_fuse'] = [C2.wisp(i / 3, 0.4 + i * 0.3).render() for i in range(3)]
    A['hermit_walk'] = [C2.hermit(i / 4).render() for i in range(4)]
    A['hermit_hide'] = [C2.hermit(0, k).render() for k in (0.5, 1.0)]
    A['golem_walk'] = [C2.golem(i / 4).render() for i in range(4)]
    A['golem_attack'] = [C2.golem(0, k).render() for k in (0.4, 1.0, 0.2)]
    for d in range(8):
        A[f'mite_d{d}_walk'] = [C2.mite(EN.DIRS8[d], i / 4).render() for i in range(4)]
    A['knight_walk'] = [C2.knight(i / 4).render() for i in range(4)]
    A['knight_windup'] = [C2.knight(0, 'windup', k).render() for k in (0.0, 1.0)]
    A['knight_swing'] = [C2.knight(0, 'swing', k).render() for k in (0.2, 0.6, 1.0)]
    A = with_flash(A)
    for k, img, tint in (('wisp', A['wisp_float'][0], (255, 180, 80)), ('hermit', A['hermit_walk'][0], (255, 120, 90)),
                         ('golem', A['golem_walk'][0], (120, 240, 255)), ('mite', A['mite_d2_walk'][0], (140, 240, 255)),
                         ('knight', A['knight_walk'][0], (255, 140, 60))):
        A[f'{k}_death'] = dissolve_frames(img, 6 if k == 'knight' else 5, tint, seed=len(k) * 13)
    pack('enemies2', A, 'enemies')
    W = {}
    for pre, en in (('wyrm', False), ('wyrm2', True)):
        for d in range(8):
            W[f'{pre}_head_d{d}'] = [C2.wyrm_head(EN.DIRS8[d], 0.0, en).render(), C2.wyrm_head(EN.DIRS8[d], 1.0, en).render()]
        W[f'{pre}_seg'] = [C2.wyrm_seg(i, en).render() for i in range(4)]
    for d in range(8):
        W[f'wyrm_tail_d{d}'] = [C2.wyrm_tail(EN.DIRS8[d]).render()]
    W['wyrm_mound'] = [C2.mound(i / 4).render() for i in range(4)]
    W['wyrm_flash'] = [flash(W['wyrm_seg'][0])]
    W['wyrm_death'] = dissolve_frames(W['wyrm2_seg'][0], 6, (255, 140, 60), 41)
    pack('boss_wyrm', W, 'enemies')
    C = {}
    for pre, en in (('col', False), ('col2', True)):
        C[f'{pre}_idle'] = [C2.colossus('idle', i / 4, en).render() for i in range(4)]
        C[f'{pre}_raise'] = [C2.colossus('raise', k, en).render() for k in (0.5, 1.0)]
        C[f'{pre}_slam'] = [C2.colossus('slam', k, en).render() for k in (0.5, 1.0)]
        C[f'{pre}_roar'] = [C2.colossus('roar', 0, en).render()]
    C['col_flash'] = [flash(C['col_idle'][0])]
    C['col_death'] = dissolve_frames(C['col2_idle'][0], 8, (150, 240, 255), 51)
    pack('boss_colossus', C, 'enemies')
    # retratos do bestiário
    d = os.path.join(OUT, 'ui', 'bestiary')
    os.makedirs(d, exist_ok=True)
    portraits = {
        'ferr': EN.ferrugineo(EN.DIRS8[1], 0.2), 'mord': EN.mordalume(EN.DIRS8[1], 0.2), 'lodo': EN.filho_do_lodo(0.2),
        'vesp': EN.vespa(EN.DIRS8[1], 0.2), 'carap': EN.carapaca(0.2), 'sapo': EN.sapo('idle', 0), 'suss': EN.sussurrante(0.2, 0.5),
        'wisp': C2.wisp(0.2), 'hermit': C2.hermit(0.2), 'golem': C2.golem(0.2), 'mite': C2.mite(EN.DIRS8[1], 0.2),
        'guard': BF.guardiao(0.2), 'sacer': BF.sacerdotisa(0.2, 0.5), 'knight': C2.knight(0, 'windup', 0.5),
        'wyrm': C2.wyrm_head(EN.DIRS8[1], 1.0), 'frog': BF.batraquio('spit', 0.5), 'colossus': C2.colossus('idle', 0), 'heart': BF.coracao(2, 0.2),
    }
    for k, spr in portraits.items():
        spr.render().save(os.path.join(d, f'{k}.png'))


def build_env():
    print('ambientes')
    for ar in 'abc':
        A = {}
        A['ground'] = [TR.ground(ar, i) for i in range(6)]
        for m in range(16):
            A[f'cobble{m}'] = [TR.cobble(ar, m, v) for v in range(2)]
            A[f'plaza{m}'] = [TR.plaza(ar, m, v) for v in range(4 if m == 0 else 2)]
            A[f'cliff{m}'] = [TR.cliff(ar, m, v) for v in range(2)]
        pack(f'tiles_{ar}', A, 'environment', pad=2)
    P = EV.props_all()
    A = {k: [v] for k, v in P.items()}
    A['anchor_off'] = [EV.anchor(0).render()]
    A['anchor_charge'] = [EV.anchor(1, i / 4).render() for i in range(4)]
    A['anchor_on'] = [EV.anchor(2).render()]
    A['portal'] = [EV.portal(i / 4).render() for i in range(4)]
    pack('props', A, 'environment')


def build_fx():
    print('efeitos')
    F = FX.all_fx()
    F['light_pool'] = [TR.light_pool()]
    F['light_hole'] = [TR.darkness_hole()]
    F['shadow_s'] = [shadow_sprite(14, 6)]
    F['shadow_m'] = [shadow_sprite(22, 8)]
    F['shadow_l'] = [shadow_sprite(36, 12)]
    F['shadow_xl'] = [shadow_sprite(96, 28)]
    pack('fx', F, 'effects')


def build_ui():
    print('interface')
    d = os.path.join(OUT, 'ui')
    os.makedirs(d, exist_ok=True)
    for r in UI.RARITY:
        UI.card_frame(r).save(os.path.join(d, f'card_{r}.png'))
    UI.panel().save(os.path.join(d, 'panel.png'))
    for r, meta in UI.RARITY.items():
        UI.panel(meta['metal']).save(os.path.join(d, f'frame_{r}.png'))
    UI.panel('#4a8a9a').save(os.path.join(d, 'panel_cool.png'))
    for st in ('normal', 'hover', 'press'):
        UI.button(st).save(os.path.join(d, f'button_{st}.png'))
    UI.bar_frame().save(os.path.join(d, 'bar_frame.png'))
    for nm, col in (('hp', '#d8403a'), ('energy', '#ff9a2a'), ('xp', '#5fd6c4'), ('boss', '#b02a5a'), ('elite', '#c07a3a')):
        UI.bar_fill(col).save(os.path.join(d, f'bar_{nm}.png'))
    UI.slot().save(os.path.join(d, 'slot.png'))
    UI.cursor().save(os.path.join(d, 'cursor.png'))
    font = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
    if not os.path.exists(font):
        font = os.path.join(OUT, 'fonts', 'Lora-Variable.ttf')
    UI.logo(font).save(os.path.join(d, 'logo.png'))
    idir = os.path.join(d, 'icons')
    os.makedirs(idir, exist_ok=True)
    for k, im in UI.icons().items():
        im.save(os.path.join(idir, f'{k}.png'))
    print(f'  {len(UI.ICONS)} ícones, 3 cartas, painéis, botões, barras, logo')


def build_menu_art():
    """Ilustração do menu (480x270) composta com os próprios sprites: noite de cristais, a heroína e a Coroa."""
    print('ilustração do menu')
    import numpy as np
    from pix import Sprite as PSprite, Mat, ramp as pramp, mat as pmat
    W, H = 480, 270
    sky = np.zeros((H, W, 4), np.uint8)
    top, bot = np.array([9, 10, 20]), np.array([22, 30, 44])
    for y in range(H):
        t = min(1, y / 200)
        band = np.floor(t * 9) / 9
        sky[y, :, :3] = (top + (bot - top) * band).astype(np.uint8)
        sky[y, :, 3] = 255
    img = Image.fromarray(sky, 'RGBA')
    # agulhas de cristal no horizonte (silhuetas em duas profundidades)
    rng = __import__('random').Random(4)
    for depth, col, hmin, hmax, n in ((0, '#0f222a', 50, 130, 14), (1, '#16343e', 25, 85, 11)):
        s = PSprite(W, H)
        M = Mat(pramp(col, 3, spread=0.25), outline=(8, 14, 20))
        for i in range(n):
            x = (i + rng.random()) * W / n
            h = rng.uniform(hmin, hmax)
            base = 212 + depth * 6
            w = rng.uniform(6, 11)
            s.poly([(x - w, base), (x + rng.uniform(-3, 3), base - h), (x + w, base)], M, ex=0.3)
        img.alpha_composite(s.render(outline=False))
    # solo
    grd = [TR.ground('a', i) for i in range(6)]
    for ty in range(208, H, 32):
        for tx in range(0, W, 32):
            img.alpha_composite(grd[(tx // 32 * 3 + ty // 32) % 6], (tx, ty))
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sa = np.zeros((H, W, 4), np.uint8)
    sa[208:212, :, 3] = 120
    img.alpha_composite(Image.fromarray(sa, 'RGBA'))
    P = EV.props_all()
    for name, x, y in (('coral_b', 70, 244), ('fungi_a', 116, 256), ('crystal_l', 22, 236), ('ruin_b', 186, 262), ('fungi_b', 316, 252),
                       ('tree_a', 400, 246), ('crystal_m', 452, 250), ('bones', 150, 266), ('shards', 280, 266)):
        sp = P[name]
        img.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height)))
    vesp = EN.vespa(math.pi * 0.75, 0.3).render()
    img.alpha_composite(vesp, (360, 176))
    sus = EN.sussurrante(0.2).render()
    img.alpha_composite(sus, (446, 222))
    # brasas no ar
    ea = np.array(img).copy()
    for _ in range(70):
        x, y = rng.randrange(0, W), rng.randrange(10, 230)
        ea[y, x, :3] = (255, 170 + rng.randrange(0, 60), 80)
        if rng.random() < 0.3 and y + 1 < H:
            ea[y + 1, x, :3] = (180, 80, 30)
    img = Image.fromarray(ea, 'RGBA')
    # anel da Coroa no chão + chamas + heroína
    cx, cy = 240, 236
    ring = FX.crown_ring(3).resize((128, 128), Image.NEAREST).resize((128, 64), Image.NEAREST)
    glow = FX.glow(64, FX.FIRE).resize((160, 80), Image.NEAREST)
    gl = np.array(glow).copy(); gl[..., 3] = (gl[..., 3] * 0.22).astype(np.uint8)
    img.alpha_composite(Image.fromarray(gl, 'RGBA'), (cx - 80, cy - 42))
    img.alpha_composite(ring, (cx - 64, cy - 34))
    for k in range(8):
        a = k / 8 * math.tau
        fx_, fy_ = cx + math.cos(a) * 52, cy - 2 + math.sin(a) * 24
        if math.sin(a) < 0:
            fl_ = FX.crown_flame(k % 6)
            img.alpha_composite(fl_, (int(fx_ - fl_.width / 2), int(fy_ - fl_.height + 6)))
    h = HE.hero('down', 'idle', 0.0).render()
    img.alpha_composite(h, (cx - 32, cy - 56))
    for k in range(8):
        a = k / 8 * math.tau
        fx_, fy_ = cx + math.cos(a) * 52, cy - 2 + math.sin(a) * 24
        if math.sin(a) >= 0:
            fl_ = FX.crown_flame((k + 3) % 6)
            img.alpha_composite(fl_, (int(fx_ - fl_.width / 2), int(fy_ - fl_.height + 6)))
    vig = FX.vignette().resize((W, H), Image.NEAREST)
    img.alpha_composite(vig)
    img.save(os.path.join(OUT, 'ui', 'menu_art.png'))


def build_act_thumbs():
    """Miniaturas do mapa da campanha: recortes reais de cada arena (terreno + props + luz)."""
    import json
    import numpy as np
    print('miniaturas dos atos')
    P = EV.props_all()
    for key, tiles, (cx, cy) in (('arena_a', 'a', (44, 7)), ('arena_b', 'b', (47, 17)), ('arena_c', 'c', (15, 7))):
        m = json.load(open(os.path.join(OUT, 'maps', key + '.json')))
        rows = m['rows']
        Wt, Ht = 12, 7
        x0, y0 = cx - Wt // 2, cy - Ht // 2
        img = Image.new('RGBA', (Wt * 32, Ht * 32), (0, 0, 0, 255))
        at = lambda x, y: '#' if x < 0 or y < 0 or x >= m['width'] or y >= m['height'] else rows[y][x]
        SOL = set('#~')
        def msk(x, y, same):
            return (0 if same(at(x, y - 1)) else 1) | (0 if same(at(x + 1, y)) else 2) | (0 if same(at(x, y + 1)) else 4) | (0 if same(at(x - 1, y)) else 8)
        for y in range(y0, y0 + Ht):
            for x in range(x0, x0 + Wt):
                px = ((x - x0) * 32, (y - y0) * 32)
                c = at(x, y)
                img.alpha_composite(TR.ground(tiles, (x * 7 + y * 3) % 6), px)
                if c == ',':
                    img.alpha_composite(TR.cobble(tiles, msk(x, y, lambda q: q in ',='), 0), px)
                if c == '=':
                    img.alpha_composite(TR.plaza(tiles, msk(x, y, lambda q: q == '='), (x + y) % 4), px)
                if c in SOL:
                    img.alpha_composite(TR.cliff(tiles, msk(x, y, lambda q: q in SOL), 0), px)
        for p in sorted(m['props'], key=lambda p: p['y']):
            spr = P.get(p['type'])
            if spr is None:
                continue
            x = p['x'] - x0 * 32 - spr.width // 2
            y = p['y'] - y0 * 32 - int(spr.height * 0.94)
            if -spr.width < x < img.width and -spr.height < y < img.height:
                img.alpha_composite(spr, (x, y))
        a = np.asarray(img).astype(np.float32)
        H_, W_ = a.shape[:2]
        yy, xx = np.mgrid[0:H_, 0:W_]
        d = np.hypot((xx - W_ / 2) / (W_ / 2), (yy - H_ / 2) / (H_ / 2))
        light = np.clip(1.15 - d * 0.75, 0.35, 1.1)[..., None]
        a[..., :3] = np.clip(a[..., :3] * light, 0, 255)
        Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'ui', f'act_{tiles}.png'))


def copy_font():
    d = os.path.join(OUT, 'fonts')
    os.makedirs(d, exist_ok=True)
    src = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
    if os.path.exists(src):
        shutil.copy(src, os.path.join(d, 'Lora-Variable.ttf'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    copy_font()
    build_hero()
    build_enemies()
    build_bigfoes()
    build_enemies2()
    build_env()
    build_fx()
    build_ui()
    build_menu_art()
    build_act_thumbs()
    print('ok')
