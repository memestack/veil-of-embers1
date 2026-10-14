"""Exports every game asset as individual, named PNG frames + manifest + contact sheets,
so the art can be redrawn by hand and re-imported with the same names."""
import json, os, re, csv, shutil, sys
from PIL import Image, ImageDraw

SRC = 'public/assets'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'asset-kit'

DESC = {
  'characters/hero': 'Heroína (arqueira-rúnica). down=frente, up=costas, side=perfil (olhando para a DIREITA; a esquerda é espelhada no jogo).',
  'enemies/enemies': 'Inimigos comuns 1: ferr (besouro), mord (aranha), vesp (vespa) em 8 direções d0..d7; lodo, carap, sapo, suss em vista 3/4 (olhando para a direita).',
  'enemies/enemies2': 'Inimigos comuns 2 + elite: wisp, hermit, golem, mite (8 direções), knight (elite).',
  'enemies/elites': 'Elites: guard (Coral Warden com armadura) / guardb (sem armadura), sacer (Glass Priestess).',
  'enemies/boss_wyrm': 'Chefe Ash Wyrm: cabeça 8 direções (2 quadros: boca fechada/aberta), segmento do corpo, cauda 8 direções, montinho de terra. Prefixo wyrm2_ = fase 2 (enfurecido).',
  'enemies/boss_frog': 'Chefe Colossal Batrach: batr_ = fase 1, batr2_ = fase 2.',
  'enemies/boss_colossus': 'Chefe Glass Colossus: col_ = fase 1, col2_ = fase 2.',
  'enemies/boss_heart': 'Chefe final Heart of the Veil: heart1/2/3 = fases, tentáculos.',
  'environment/tiles_a': 'Tiles 32x32 do Ato I. ground = chão; cobbleN/plazaN/cliffN = bordas automáticas (N = máscara de vizinhos: Norte=1, Leste=2, Sul=4, Oeste=8).',
  'environment/tiles_b': 'Tiles 32x32 do Ato II (mesmas regras do tiles_a).',
  'environment/tiles_c': 'Tiles 32x32 do Ato III (mesmas regras do tiles_a).',
  'environment/props': 'Objetos de cenário (árvores, pedras, lanternas, Âncoras, portal...). A base do objeto (o "pé") fica na borda de baixo do quadro.',
  'effects/fx': 'Efeitos visuais: projéteis, chamas, explosões, raios, avisos no chão, luzes, partículas, números de dano, sombras.',
}

def safe(n): return re.sub(r'[^a-zA-Z0-9_\-]', '_', n)

def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    rows = []
    for root, _, files in os.walk(SRC):
        for f in sorted(files):
            if not f.endswith('.json'): continue
            p = os.path.join(root, f)
            d = json.load(open(p))
            if 'frames' not in d: continue
            key = os.path.relpath(p, SRC)[:-5]
            img = Image.open(os.path.join(root, d['meta']['image'])).convert('RGBA')
            anims = d.get('animations') or {}
            owner = {}
            for a, fr in anims.items():
                for i, fn in enumerate(fr): owner.setdefault(fn, (a, i, len(fr)))
            base = os.path.join(OUT, 'sprites', key)
            sheet_items = []
            for fn, fd in d['frames'].items():
                r = fd['frame']
                anim, idx, n = owner.get(fn, (fn, 0, 1))
                folder = os.path.join(base, safe(anim))
                os.makedirs(folder, exist_ok=True)
                crop = img.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
                name = f'{safe(anim)}_{idx:02d}.png'
                out = os.path.join(folder, name)
                crop.save(out)
                rows.append([os.path.relpath(out, OUT), key, anim, idx, n, r['w'], r['h'], fn])
                sheet_items.append((anim, idx, crop))
            contact(key, sheet_items)
    # standalone UI images (frames, buttons, icons, portraits, logo, menu art)
    for root, _, files in os.walk(os.path.join(SRC, 'ui')):
        for f in sorted(files):
            if not f.endswith('.png'): continue
            src = os.path.join(root, f)
            dst = os.path.join(OUT, 'ui', os.path.relpath(src, os.path.join(SRC, 'ui')))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
            w, h = Image.open(src).size
            rows.append([os.path.relpath(dst, OUT), 'ui', os.path.splitext(f)[0], 0, 1, w, h, ''])
    # audio
    for f in sorted(os.listdir(os.path.join(SRC, 'audio'))):
        if f.endswith('.mp3'):
            dst = os.path.join(OUT, 'audio', f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(SRC, 'audio', f), dst)
            rows.append([os.path.relpath(dst, OUT), 'audio', f[:-4], 0, 1, '', '', ''])
    with open(os.path.join(OUT, 'MANIFEST.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['arquivo', 'atlas', 'animacao', 'quadro', 'total_quadros', 'largura', 'altura', 'nome_no_jogo'])
        w.writerows(rows)
    print(len(rows), 'files')

def contact(key, items):
    """Reference sheet: each animation on one row, scaled 2x, with its name."""
    by = {}
    for a, i, im in items: by.setdefault(a, []).append((i, im))
    S = 2 if max(im.width for _, _, im in items) <= 80 else 1
    rows = sorted(by.items())
    lw = 190
    W = lw + max(sum(im.width * S + 6 for _, im in fr) for _, fr in rows) + 10
    H = sum(max(im.height for _, im in fr) * S + 10 for _, fr in rows) + 40
    W = min(W, 6000)
    sheet = Image.new('RGBA', (W, H), (24, 20, 30, 255))
    dr = ImageDraw.Draw(sheet)
    import unicodedata
    txt = unicodedata.normalize('NFKD', key + '   ' + DESC.get(key, '')).encode('ascii', 'ignore').decode()
    dr.text((8, 8), txt[:170], fill=(255, 210, 122, 255))
    y = 32
    for a, fr in rows:
        fr.sort(key=lambda t: t[0])
        rh = max(im.height for _, im in fr) * S
        dr.text((8, y + rh // 2 - 6), f'{a} ({len(fr)})', fill=(230, 220, 200, 255))
        x = lw
        for _, im in fr:
            big = im.resize((im.width * S, im.height * S), Image.NEAREST)
            dr.rectangle((x - 1, y - 1, x + big.width, y + big.height), outline=(60, 50, 70, 255))
            sheet.alpha_composite(big, (x, y))
            x += big.width + 6
            if x > W - 50: break
        y += rh + 10
    os.makedirs(os.path.join(OUT, '_referencia'), exist_ok=True)
    sheet.convert('RGB').save(os.path.join(OUT, '_referencia', key.replace('/', '__') + '.png'))

if __name__ == '__main__':
    main()
