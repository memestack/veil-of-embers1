"""Re-imports a redrawn asset kit (same folder/file names as export_kit.py) into the game atlases.

  python3 scripts/art/import_kit.py path/to/asset-kit

- Each frame keeps its name; a frame missing from the kit keeps the current art.
- Redrawn frames may be the original size or an exact integer multiple (2x, 3x, 4x...). All frames of
  one atlas are brought to the largest multiple found; the atlas is written with meta.scale = k, so
  PixiJS shows it at the same on-screen size with k times more detail.
- UI images and audio are copied over 1:1 (UI may be any size; keep the same aspect ratio).
"""
import json, os, re, shutil, sys
from PIL import Image

SRC = 'public/assets'
KIT = sys.argv[1]

def safe(n): return re.sub(r'[^a-zA-Z0-9_\-]', '_', n)

def pack(items, pad=2, maxw=4096):
    items = sorted(items, key=lambda t: -t[1].height)
    x = y = pad; rowh = 0; W = 0; pos = {}
    for name, im in items:
        if x + im.width + pad > maxw:
            x = pad; y += rowh + pad; rowh = 0
        pos[name] = (x, y)
        x += im.width + pad; rowh = max(rowh, im.height); W = max(W, x)
    H = y + rowh + pad
    sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for name, im in items: sheet.alpha_composite(im, pos[name])
    return sheet, pos

def main():
    report = []
    for root, _, files in os.walk(SRC):
        for f in sorted(files):
            if not f.endswith('.json'): continue
            p = os.path.join(root, f)
            d = json.load(open(p))
            if 'frames' not in d: continue
            key = os.path.relpath(p, SRC)[:-5]
            old = Image.open(os.path.join(root, d['meta']['image'])).convert('RGBA')
            old_k = int(float(d['meta'].get('scale', 1) or 1))
            owner = {}
            for a, fr in (d.get('animations') or {}).items():
                for i, fn in enumerate(fr): owner.setdefault(fn, (a, i))
            frames, ks, replaced = {}, [], 0
            for fn, fd in d['frames'].items():
                r = fd['frame']
                base = old.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
                ow, oh = fd['sourceSize']['w'] // old_k, fd['sourceSize']['h'] // old_k  # logical size
                a, i = owner.get(fn, (fn, 0))
                kp = os.path.join(KIT, 'sprites', key, safe(a), f'{safe(a)}_{i:02d}.png')
                if os.path.exists(kp):
                    im = Image.open(kp).convert('RGBA')
                    k = im.width / ow
                    if abs(k - round(k)) > 1e-6 or im.height != round(k) * oh or round(k) < 1:
                        sys.exit(f'ERRO: {kp} tem {im.width}x{im.height}; precisa ser {ow}x{oh} ou multiplo exato')
                    frames[fn] = (im, round(k)); replaced += 1
                else:
                    frames[fn] = (base, old_k)
                ks.append(frames[fn][1])
            K = max(ks)
            items = []
            for fn, (im, k) in frames.items():
                if k != K: im = im.resize((im.width * K // k, im.height * K // k), Image.NEAREST)
                items.append((fn, im))
            sheet, pos = pack(items)
            sheet.save(os.path.join(root, d['meta']['image']))
            for fn, im in items:
                x, y = pos[fn]
                d['frames'][fn]['frame'] = {'x': x, 'y': y, 'w': im.width, 'h': im.height}
                d['frames'][fn]['spriteSourceSize'] = {'x': 0, 'y': 0, 'w': im.width, 'h': im.height}
                d['frames'][fn]['sourceSize'] = {'w': im.width, 'h': im.height}
            d['meta']['size'] = {'w': sheet.width, 'h': sheet.height}
            d['meta']['scale'] = str(K)
            json.dump(d, open(p, 'w'))
            report.append(f'{key}: {replaced}/{len(frames)} quadros novos, escala {K}x')
    for sub in ('ui', 'audio'):
        kdir = os.path.join(KIT, sub)
        if not os.path.isdir(kdir): continue
        for r, _, fs in os.walk(kdir):
            for f in fs:
                dst = os.path.join(SRC, sub, os.path.relpath(os.path.join(r, f), kdir))
                if os.path.exists(dst):
                    shutil.copy(os.path.join(r, f), dst); report.append(f'{sub}: {os.path.relpath(dst, SRC)}')
    print('\n'.join(report))

if __name__ == '__main__':
    main()
