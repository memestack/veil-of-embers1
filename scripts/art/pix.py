"""
pix.py — núcleo da pipeline de pixel art autoral do VÉU DE BRASAS.

Cada sprite é descrito por PARTES (formas vetoriais autorais: elipses, polígonos,
membros afunilados) com um MATERIAL (rampa de cor com hue-shift). O núcleo:
  1. rasteriza cada parte com supersampling e reduz para pixels limpos;
  2. calcula volume (mapa de altura por transformada de distância) e normais;
  3. ilumina com luz direcional (cima-esquerda) e quantiza na rampa do material
     (com dithering ordenado opcional), produzindo sombreamento de pixel art;
  4. marca linhas internas entre partes sobrepostas e aplica contorno seletivo;
  5. aplica decorações pixel a pixel (olhos, runas, brilhos) escritas à mão.

Não há geração procedural de conteúdo: as formas, poses e quadros de animação
são autorados nos scripts de cada família de assets.
"""
from __future__ import annotations
import colorsys
import math
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

SS = 4  # supersampling
LIGHT = np.array([-0.55, -0.75, 0.85])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0


# ----------------------------------------------------------------- cores
def hx(c: str) -> tuple[int, int, int]:
    c = c.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def to_hex(rgb) -> str:
    return '#%02x%02x%02x' % tuple(int(max(0, min(255, v))) for v in rgb[:3])


def _hue_toward(h: float, target: float, amt: float) -> float:
    d = ((target - h + 0.5) % 1.0) - 0.5
    return (h + d * amt) % 1.0


def ramp(base: str, n: int = 5, spread: float = 0.62, shadow_hue: float = 0.70,
         light_hue: float = 0.13, shift: float = 0.22, sat_boost: float = 0.12) -> list[tuple[int, int, int]]:
    """Rampa com hue-shift: sombras puxam para violeta/azul, luzes para âmbar."""
    r, g, b = [v / 255 for v in hx(base)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    mid = (n - 1) / 2
    for i in range(n):
        k = (i - mid) / mid  # -1..1
        if k < 0:
            hh = _hue_toward(h, shadow_hue, -k * shift)
            ll = l * (1 + k * spread)
            ss = min(1, s * (1 - k * sat_boost))
        else:
            hh = _hue_toward(h, light_hue, k * shift * 0.7)
            ll = l + (1 - l) * k * spread * 0.85
            ss = s * (1 - k * 0.25)
        rr, gg, bb = colorsys.hls_to_rgb(hh, max(0.02, min(0.97, ll)), max(0, min(1, ss)))
        out.append((int(rr * 255), int(gg * 255), int(bb * 255)))
    return out


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def darken(c, t=0.4):
    return mix(c, (8, 4, 14), t)


@dataclass
class Mat:
    ramp: list
    outline: tuple = None
    emissive: bool = False
    spec: float = 0.0          # brilho especular (metal, vidro, carapaça)
    alpha: float = 1.0
    dither: bool = False
    amb: float = 0.32
    pattern: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None

    def __post_init__(self):
        if self.outline is None:
            self.outline = darken(self.ramp[0], 0.55)


def mat(base: str, n=5, **kw) -> Mat:
    rk = {k: kw.pop(k) for k in list(kw) if k in ('spread', 'shadow_hue', 'light_hue', 'shift', 'sat_boost')}
    return Mat(ramp(base, n, **rk), **kw)


def mat_glow(core: str, edge: str, n=5, alpha=1.0) -> Mat:
    a, b = hx(edge), hx(core)
    return Mat([mix(a, b, i / (n - 1)) for i in range(n)], emissive=True, alpha=alpha,
               outline=darken(a, 0.35))


def shift(a, dy, dx, fill=0):
    """Deslocamento sem wrap-around (preenche bordas)."""
    out = np.full_like(a, fill)
    H, W = a.shape[:2]
    ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
    xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


# --------------------------------------------------------------- partes
@dataclass
class Part:
    mask: np.ndarray
    mat: Mat
    ex: float = 0.6          # curvatura do volume (menor = mais plano)
    lift: float = 0.0        # deslocamento da luz (partes "mais altas" mais claras)
    edge: bool = True        # desenha linha interna sobre partes abaixo
    tilt: tuple = (0.0, 0.0) # inclinação extra da normal (dx, dy)
    flat: float = 0.0        # 0..1 mistura com normal plana
    shade_bias: float = 0.0


class Sprite:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.parts: list[Part] = []
        self.decor: list[tuple] = []   # (x, y, rgba)
        self.post: list[Callable] = []

    # --- rasterização com supersampling
    def _layer(self):
        im = Image.new('L', (self.w * SS, self.h * SS), 0)
        return im, ImageDraw.Draw(im)

    def _finish(self, im: Image.Image, thr=0.5) -> np.ndarray:
        a = np.asarray(im.resize((self.w, self.h), Image.BOX), dtype=np.float32) / 255.0
        return a >= thr

    def ellipse(self, cx, cy, rx, ry, m: Mat, rot=0.0, **kw):
        im, d = self._layer()
        if abs(rot) < 1e-6:
            d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=255)
        else:
            pts = []
            for i in range(48):
                t = i / 48 * math.tau
                x, y = rx * math.cos(t), ry * math.sin(t)
                c, s = math.cos(rot), math.sin(rot)
                pts.append(((cx + x * c - y * s) * SS, (cy + x * s + y * c) * SS))
            d.polygon(pts, fill=255)
        return self.add(self._finish(im), m, **kw)

    def poly(self, pts: Sequence[tuple], m: Mat, **kw):
        im, d = self._layer()
        d.polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        return self.add(self._finish(im), m, **kw)

    def limb(self, pts: Sequence[tuple], r0: float, r1: float, m: Mat, **kw):
        """Membro afunilado ao longo de uma polilinha (r0 no início, r1 no fim)."""
        im, d = self._layer()
        n = len(pts)
        tot = sum(math.dist(pts[i], pts[i + 1]) for i in range(n - 1)) or 1
        acc = 0.0
        for i in range(n - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            seg = math.dist(pts[i], pts[i + 1])
            steps = max(2, int(seg * 3))
            for k in range(steps + 1):
                t = k / steps
                u = (acc + seg * t) / tot
                r = r0 + (r1 - r0) * u
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=255)
            acc += seg
        return self.add(self._finish(im, 0.45), m, **kw)

    def custom(self, fn: Callable[[ImageDraw.ImageDraw, int], None], m: Mat, thr=0.5, **kw):
        im, d = self._layer()
        fn(d, SS)
        return self.add(self._finish(im, thr), m, **kw)

    def add(self, mask, m: Mat, clip: Optional[np.ndarray] = None, **kw):
        if clip is not None:
            mask = mask & clip
        p = Part(mask, m, **kw)
        self.parts.append(p)
        return p

    def px(self, x, y, c, a=255):
        if isinstance(c, str):
            c = hx(c)
        self.decor.append((int(x), int(y), (c[0], c[1], c[2], a)))

    def line(self, x0, y0, x1, y1, c, a=255):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.px(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c, a)

    # --- composição
    def render(self, outline=True, dither=None) -> Image.Image:
        H, W = self.h, self.w
        rgb = np.zeros((H, W, 3), np.float32)
        alpha = np.zeros((H, W), np.float32)
        owner = -np.ones((H, W), np.int32)
        level = np.zeros((H, W), np.int32)
        yy, xx = np.mgrid[0:H, 0:W]
        for idx, p in enumerate(self.parts):
            m = p.mask
            if not m.any():
                continue
            dist = distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]
            mx = dist.max() or 1
            hgt = (dist / mx) ** p.ex
            gy, gx = np.gradient(hgt * min(6.0, mx) * 0.9)
            nx = -gx + p.tilt[0]
            ny = -gy + p.tilt[1]
            nz = np.ones_like(nx)
            if p.flat:
                nx *= (1 - p.flat); ny *= (1 - p.flat)
            nl = np.sqrt(nx * nx + ny * ny + nz * nz)
            diff = np.clip((nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / nl, 0, 1)
            mt = p.mat
            if mt.emissive:
                inten = 0.25 + 0.75 * hgt
            else:
                inten = mt.amb + 0.78 * diff + 0.18 * hgt + p.lift + p.shade_bias
                inten = inten - 0.25  # escurece base, preserva tons altos
            if mt.pattern is not None:
                inten = inten + mt.pattern(xx, yy)
            n = len(mt.ramp)
            v = np.clip(inten, 0, 0.999) * n
            use_d = mt.dither if dither is None else (dither and mt.dither)
            if use_d:
                v = v + (BAYER4[yy % 4, xx % 4] - 0.5) * 0.85
            li = np.clip(v.astype(np.int32), 0, n - 1)
            if mt.spec > 0:
                sp = (diff > 0.93) & (hgt > 0.45)
                li = np.where(sp, n - 1, li)
            # linha interna: pixels da parte vizinhos de OUTRA parte já desenhada
            if p.edge:
                outside_owned = np.zeros_like(m)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    sm = shift(m, dy, dx, True)
                    so = shift(owner >= 0, dy, dx, False)
                    outside_owned |= (~sm) & so
                edgepx = m & outside_owned
                li = np.where(edgepx, np.maximum(li - 2, 0), li)
            cols = np.array(mt.ramp, np.float32)[li]
            a = mt.alpha
            sel = m
            if a < 1:
                has = alpha[sel] > 0
                base = np.where(has[:, None], rgb[sel], cols[sel])
                rgb[sel] = base * (1 - a) + cols[sel] * a
                alpha[sel] = np.where(has, alpha[sel], a)
            else:
                rgb[sel] = cols[sel]
                alpha[sel] = 1.0
            owner[sel] = idx
            level[sel] = li[sel]
        # decoração autoral pixel a pixel
        out = np.zeros((H, W, 4), np.float32)
        out[..., :3] = rgb
        out[..., 3] = alpha * 255
        for (x, y, c) in self.decor:
            if 0 <= x < W and 0 <= y < H:
                a = c[3] / 255
                base = out[y, x, :3] if out[y, x, 3] > 0 else np.array(c[:3], np.float32)
                out[y, x, :3] = base * (1 - a) + np.array(c[:3]) * a
                out[y, x, 3] = max(out[y, x, 3], c[3])
                if owner[y, x] < 0:
                    owner[y, x] = -2
        if outline:
            solid = out[..., 3] > 30
            ol = np.zeros((H, W, 4), np.float32)
            for dy, dx, w_ in ((1, 0, 1.0), (-1, 0, 0.0), (0, 1, 0.5), (0, -1, 0.5)):
                src = shift(solid, dy, dx, False)
                srco = shift(owner, dy, dx, -1)
                cand = (~solid) & src & (ol[..., 3] == 0)
                ys, xs = np.nonzero(cand)
                for y, x in zip(ys, xs):
                    o = srco[y, x]
                    if o >= 0:
                        c = self.parts[o].mat.outline
                        if dy == 1 or dx == 1:  # luz vem de cima-esquerda: contorno inferior mais escuro
                            c = darken(c, 0.25)
                    else:
                        c = (20, 12, 20)
                    ol[y, x] = (*c, 255)
            m2 = ol[..., 3] > 0
            out[m2] = ol[m2]
        for f in self.post:
            out = f(out)
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


# --------------------------------------------------------- utilidades de quadro
def rot(px, py, cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)


def flash(img: Image.Image, color=(255, 246, 230)) -> Image.Image:
    a = np.asarray(img).copy()
    m = a[..., 3] > 0
    a[m, 0], a[m, 1], a[m, 2] = color
    return Image.fromarray(a, 'RGBA')


def dissolve_frames(img: Image.Image, n=5, tint=(255, 120, 60), seed=7) -> list[Image.Image]:
    """Quadros de morte: o sprite racha, clareia na borda e se desfaz em grãos."""
    a = np.asarray(img).astype(np.float32)
    H, W = a.shape[:2]
    rng = np.random.default_rng(seed)
    order = rng.random((H, W))
    yy, xx = np.mgrid[0:H, 0:W]
    m = a[..., 3] > 0
    if m.any():
        cy, cx = yy[m].mean(), xx[m].mean()
    else:
        cy, cx = H / 2, W / 2
    rad = np.hypot(yy - cy, xx - cx)
    rad = rad / (rad[m].max() + 1e-6 if m.any() else 1)
    frames = []
    for i in range(n):
        t = (i + 1) / (n + 0.5)
        b = a.copy()
        thr = t * 1.15
        gone = (order * 0.6 + (1 - rad) * 0.4) < thr
        burn = ((order * 0.6 + (1 - rad) * 0.4) < thr + 0.12) & ~gone
        b[gone, 3] = 0
        b[burn, :3] = b[burn, :3] * 0.3 + np.array(tint) * 0.7
        # leve deslocamento para baixo dos grãos (assentamento)
        sh = int(t * 2)
        if sh:
            b = np.roll(b, sh, axis=0)
            b[:sh] = 0
        frames.append(Image.fromarray(b.clip(0, 255).astype(np.uint8), 'RGBA'))
    return frames


def shadow_sprite(w, h, alpha=110) -> Image.Image:
    """Sombra elíptica pixelada com dois níveis (sem gradiente suave)."""
    s = Sprite(w, h)
    im = np.zeros((h, w, 4), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((xx - (w - 1) / 2) / (w / 2)) ** 2 + ((yy - (h - 1) / 2) / (h / 2)) ** 2
    im[d < 1.0] = (10, 6, 18, alpha * 0.55)
    im[d < 0.55] = (10, 6, 18, alpha)
    return Image.fromarray(im, 'RGBA')


def upscale(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def sheet_preview(frames: list[Image.Image], cols=8, scale=3, bg=(34, 38, 46)) -> Image.Image:
    w = max(f.width for f in frames); h = max(f.height for f in frames)
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGBA', (cols * w, rows * h), bg + (255,))
    for i, f in enumerate(frames):
        out.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    return upscale(out, scale)
