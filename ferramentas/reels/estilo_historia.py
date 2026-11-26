#!/usr/bin/env python3
"""
Estilo "história" para Reels do @jacksonbueno.adv, na identidade visual do site jacksonbueno.adv.br e do feed
(mesmas cores e fontes de ferramentas/gerar.py): azul-toga #0f1624, dourado #daa843, pergaminho #fbf8f2,
títulos em Playfair Display 800 com palavra em itálico dourado, texto em Montserrat, selo "JB" + "DIREITO DO ACIDENTADO",
etiquetas em pílula de contorno dourado e botão verde do WhatsApp (#006336).
Estrutura inspirada no modelo enviado pelo titular em 26/11/2026 (história com gancho, cartões de papel, carimbo, fecho).

Mesmo gerador do reels.py (voz, legendas animadas, trilha, regra dos clipes), com cenas novas:
  foto    clip, kicker, parts[{t,k}], sub{t,k}, src, badge{photo,box}, stamp{...}      vídeo/foto de banco em preto e branco + título
  papel   clip, rot, kicker, parts[{t,k}], sub{t,k}, sticker{...}, stamp{...}           fundo pergaminho com foto colada (polaroid)
  texto   parts[{t,k}], sub{t,k}                                                         só texto, fundo azul-toga
  fecho   photo, photo_box, parts[{t,k}], button, note, button_k                         foto do titular em P&B + botão verde do WhatsApp
t: texto do título; *palavra* = itálico dourado. k: palavra falada que dispara a animação.
Campos do spec: "tema", "legenda", "voz", "beats": [ {kind, say, cap?, ...} ].

USO (igual ao reels.py):  python3 ferramentas/reels/estilo_historia.py spec.json pasta_saida [--preview]
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels
from reels import (W, H, MX, CW, ROOT, M, fit, layer, paste, eo, eb, cl, t_of, sframe, face_circle, np, Image, ImageDraw)
from PIL import ImageOps, ImageEnhance, ImageFilter, ImageFont

TOGA = (15, 22, 36); BG0 = (8, 13, 25); GOLD = (218, 168, 67); GOLD_D = (186, 136, 46)
PERG = (251, 248, 242); MUTED = (185, 189, 199); GREEN = (0, 99, 54); SLATE = (91, 96, 112)
_d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))

# ---------------- fontes ----------------
PFP = os.path.join(ROOT, "ferramentas", "node_modules", "@fontsource", "playfair-display", "files", "playfair-display-latin-%d-%s.woff")
_pf = {}
def PF(w, s, italic=False):
    k = (w, s, italic)
    if k not in _pf: _pf[k] = ImageFont.truetype(PFP % (w, "italic" if italic else "normal"), s)
    return _pf[k]

def parse(text):
    """'Assaltado *trabalhando*?' -> palavras, cada uma com trechos (texto, itálico)."""
    words, cur, ital, buf = [], [], False, ""
    for ch in text:
        if ch == "*":
            if buf: cur.append((buf, ital)); buf = ""
            ital = not ital
        elif ch == " ":
            if buf: cur.append((buf, ital)); buf = ""
            if cur: words.append(cur); cur = []
        else: buf += ch
    if buf: cur.append((buf, ital))
    if cur: words.append(cur)
    return words

def wlen(word, size, wt=800):
    return sum(PF(wt, size, it).getlength(tx) for tx, it in word)

def wrap(text, size, maxw, wt=800):
    words = parse(text); sp = PF(wt, size).getlength(" "); lines, cur, w = [], [], 0
    for wd in words:
        l = wlen(wd, size, wt)
        if cur and w + sp + l > maxw: lines.append(cur); cur, w = [wd], l
        else: w = w + (sp if cur else 0) + l; cur.append(wd)
    if cur: lines.append(cur)
    return lines

def draw_line(d, x, base_y, line, size, col, col_it, wt=800):
    sp = PF(wt, size).getlength(" ")
    for wd in line:
        for tx, it in wd:
            f = PF(wt, size, it); d.text((x, base_y), tx, font=f, fill=col_it if it else col, anchor="ls"); x += f.getlength(tx)
        x += sp

def fit_size(parts, start, maxw, wt=800):
    s = start
    while s > 40 and any(wlen(wd, s, wt) > maxw for p in parts for wd in parse(p["t"])): s -= 2
    return s

# ---------------- fundos ----------------
def _grad(c0, c1, c2=None):
    y = np.linspace(0, 1, H)[:, None, None]
    if c2 is None: a = np.array(c0, float) * (1 - y) + np.array(c1, float) * y
    else:
        a = np.where(y < 0.55, np.array(c0, float) * (1 - y / 0.55) + np.array(c1, float) * (y / 0.55),
                     np.array(c1, float) * (1 - (y - 0.55) / 0.45) + np.array(c2, float) * ((y - 0.55) / 0.45))
    return np.repeat(a, W, 1)
def _dark():
    yy, xx = np.mgrid[0:H, 0:W]; t = np.clip((xx / W * 0.6 + yy / H * 0.4), 0, 1)[..., None]
    a = np.where(t < 0.55, np.array((8, 13, 25), float) * (1 - t / 0.55) + np.array((20, 26, 41), float) * (t / 0.55),
                 np.array((20, 26, 41), float) * (1 - (t - 0.55) / 0.45) + np.array((36, 45, 66), float) * ((t - 0.55) / 0.45))
    g = np.clip(1 - np.sqrt((xx - W * 0.95) ** 2 + (yy - H * 0.06) ** 2) / 760, 0, 1)[..., None]   # brilho dourado no canto
    a = a + g * np.array((60, 44, 12), float) * 0.55
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def _light():
    rng = np.random.default_rng(5); a = _grad((251, 248, 242), (241, 236, 225)) + rng.normal(0, 2.4, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
DARK, LIGHT = _dark(), _light()

def _ramp():
    ys = np.arange(H) / H
    a = np.interp(ys, [0, 0.30, 0.62, 1.0], [0.55, 0.35, 0.88, 1.0])
    return Image.fromarray((np.repeat(a[:, None], W, 1) * 255).astype(np.uint8))
RAMP = _ramp(); SOLID = Image.new("RGB", (W, H), BG0)

def bw(img):
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.1)
    return ImageOps.colorize(g, black=(6, 10, 20), white=(240, 238, 232)).convert("RGB")
def photo_bg(img):   # o mesmo degradê escuro das capas do feed
    return Image.composite(SOLID, img, RAMP)

# ---------------- elementos ----------------
def put(img, fn, a=1.0, dy=0.0, scale=1.0, cx=W // 2, cy=H // 2):
    if a <= 0.001: return
    if a >= 0.999 and not dy and scale == 1.0: fn(ImageDraw.Draw(img)); return
    lay = layer(); fn(ImageDraw.Draw(lay)); paste(img, lay, a, dy=dy, scale=scale, cx=cx, cy=cy)

def spaced(d, x, y, text, font, fill, sp=3, anchor="l"):
    w = sum(d.textlength(c, font=font) + sp for c in text) - sp
    if anchor == "r": x -= w
    elif anchor == "m": x -= w / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill, anchor="lm"); x += d.textlength(c, font=font) + sp
    return w

def header(img, light=False, y=200):
    d = ImageDraw.Draw(img); ink = TOGA if light else PERG; g = GOLD_D if light else GOLD
    d.ellipse((MX, y - 39, MX + 78, y + 39), outline=g, width=3)
    d.text((MX + 39, y + 1), "JB", font=PF(700, 34), fill=g, anchor="mm")
    d.text((MX + 98, y - 12), "Jackson Bueno Advogados", font=PF(700, 30), fill=ink, anchor="lm")
    spaced(d, MX + 98, y + 22, "DIREITO DO ACIDENTADO", M(600, 17), g, sp=4)

def kicker(img, text, y, t, t0, light=False):
    a = eo((t - t0) / 0.25)
    if a <= 0: return
    g = GOLD_D if light else GOLD; edge = GOLD_D if light else (150, 118, 52); f = M(700, 22)
    w = sum(_d0.textlength(c, font=f) + 4 for c in text) + 52
    def fn(d):
        d.rounded_rectangle((MX, y, MX + w, y + 52), 26, outline=edge, width=2); spaced(d, MX + 26, y + 27, text, f, g, sp=4)
    put(img, fn, a, dy=(1 - a) * 18)

def block(img, b, t, light=False, bottom=1360, size=92, top=None, gap=14):
    """Kicker + título (partes que entram nas palavras-chave) + barra dourada + sub + fonte. Ancorado embaixo (ou em 'top')."""
    parts = b.get("parts", []); maxw = CW
    sz = fit_size(parts, size, maxw); lh = int(sz * 1.1)
    plines = [(i, ln) for i, p in enumerate(parts) for ln in wrap(p["t"], sz, maxw)]
    col = TOGA if light else PERG; it = GOLD_D if light else GOLD
    hh = len(plines) * lh
    if b.get("sub") or b.get("src"): hh += 40 + 6 + 28
    if b.get("sub"): hh += int(36 * 1.4) * len(_sub_lines(b["sub"]["t"]))
    if b.get("src"): hh += 52
    ktop = (top if top is not None else bottom - hh)
    if b.get("kicker"):
        kicker(img, b["kicker"], ktop - 86, t, 0.05, light)
    y = ktop
    for n, (pi, ln) in enumerate(plines):
        k = parts[pi].get("k"); t0 = t_of(b, k, 0.15 + 0.1 * pi) - 0.12 + 0.08 * (n - sum(1 for q in plines[:n] if q[0] != pi) * 0)
        a = eo((t - t0) / 0.3); base = y + int(sz * 0.92)
        put(img, lambda d, ln=ln, base=base: draw_line(d, MX, base, ln, sz, col, it), a, dy=(1 - a) * 34)
        y += lh
    if b.get("sub") or b.get("src"):
        ts = t_of(b, (b.get("sub") or {}).get("k"), 0.9) - 0.1; a = eo((t - ts) / 0.35)
        y += 40
        put(img, lambda d, y=y: d.rectangle((MX, y, MX + 120, y + 6), fill=GOLD_D if light else GOLD), a)
        y += 6 + 28
        if b.get("sub"):
            for s in _sub_lines(b["sub"]["t"]):
                put(img, lambda d, y=y, s=s: d.text((MX, y), s, font=M(500, 36), fill=SLATE if light else (214, 212, 206), anchor="la"), a, dy=(1 - a) * 16)
                y += int(36 * 1.4)
        if b.get("src"):
            put(img, lambda d, y=y: d.text((MX, y + 8), b["src"], font=M(600, 25), fill=GOLD_D if light else GOLD, anchor="la"), a)
    return ktop

def _sub_lines(text):
    f = M(500, 36); words = text.split(); lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if _d0.textlength(trial, font=f) > CW and cur: lines.append(cur); cur = w
        else: cur = trial
    if cur: lines.append(cur)
    return lines

def stamp(img, s, t, b, light=False):
    t0 = t_of(b, s.get("k"), 1.0) - 0.1; p = eb((t - t0) / 0.32)
    if t < t0: return
    fs = s.get("size", 40); f = M(800, fs); lines = s["t"].split("\n")
    tw = max(_d0.textlength(l, font=f) for l in lines); th = len(lines) * (fs + 8); pad = 26
    w, h = int(tw + pad * 2), int(th + pad * 2 - 8)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = GOLD_D if light else GOLD
    if s.get("fill"): d.rounded_rectangle((0, 0, w - 1, h - 1), 10, fill=GOLD); tc = TOGA
    else: d.rounded_rectangle((0, 0, w - 1, h - 1), 10, outline=col, width=6); d.rounded_rectangle((12, 12, w - 13, h - 13), 6, outline=col, width=2); tc = col
    for i, l in enumerate(lines): d.text((w / 2, pad - 4 + i * (fs + 8)), l, font=f, fill=tc, anchor="mt")
    sc = 0.55 + 0.45 * p; im = im.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS).rotate(s.get("rot", -6), resample=Image.BICUBIC, expand=True)
    cx, cy = s["pos"]; img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def sticker(img, s, t, b):
    t0 = t_of(b, s.get("k"), 1.0) - 0.1; p = eb((t - t0) / 0.35)
    if t < t0: return
    D = s.get("d", 250); im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=GOLD); d.ellipse((12, 12, D - 13, D - 13), outline=TOGA, width=3)
    d.text((D / 2, D * 0.42), s.get("big", ""), font=PF(800, s.get("bigsize", 78)), fill=TOGA, anchor="mm")
    d.text((D / 2, D * 0.74), s.get("small", ""), font=M(800, 22), fill=TOGA, anchor="mm")
    sc = 0.4 + 0.6 * p; im = im.resize((max(1, int(D * sc)),) * 2, Image.LANCZOS).rotate(s.get("rot", 8), resample=Image.BICUBIC, expand=True)
    cx, cy = s["pos"]; img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def badge(img, bd, t):
    p = eb((t - 0.25) / 0.45)
    if p <= 0.02: return
    D = 240; cx, cy = bd.get("pos", (W - MX - 120, 760)); r = int((D / 2 + 8) * p); d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD)
    fc = face_circle(bd["photo"], bd["box"], max(10, int(D * p))); img.paste(fc, (int(cx - fc.width / 2), int(cy - fc.height / 2)), fc)

def polaroid(img, frame, t, rot=-3, pw=640, ph=520, cx=W // 2, cy=600, t0=0.0):
    p = eb((t - t0) / 0.45)
    if t < t0: return
    B = 20; im = ImageOps.fit(frame, (pw, ph), centering=(0.5, 0.45))
    card = Image.new("RGBA", (pw + 2 * B, ph + B + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rectangle((0, 0, card.width - 1, card.height - 1), fill=(255, 253, 248)); card.paste(im, (B, B))
    sh = Image.new("RGBA", (card.width + 120, card.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((60, 78, 60 + card.width, 78 + card.height), fill=(15, 22, 36, 110)); sh = sh.filter(ImageFilter.GaussianBlur(16)); sh.paste(card, (60, 60), card)
    for tx in (card.width * 0.12, card.width * 0.78):
        tape = Image.new("RGBA", (190, 62), (226, 200, 140, 205)).rotate(-28 if tx < 200 else 24, expand=True, resample=Image.BICUBIC)
        sh.paste(tape, (int(60 + tx - tape.width / 2 + 30), int(60 - 34)), tape)
    sc = 1.12 - 0.12 * p; out = sh.resize((int(sh.width * sc), int(sh.height * sc)), Image.LANCZOS).rotate(rot + (1 - p) * 4, expand=True, resample=Image.BICUBIC)
    out.putalpha(out.split()[3].point(lambda v: int(v * cl(p * 1.6)))); img.paste(out, (int(cx - out.width / 2), int(cy - out.height / 2)), out)

# ---------------- cenas ----------------
def s_foto(t, dur, b, gt):
    img = photo_bg(bw(sframe(b["clip"], t * 0.85, b.get("clip_start", 0)))); header(img)
    if b.get("badge"): badge(img, b["badge"], t)
    block(img, b, t, bottom=b.get("bottom", 1360))
    if b.get("stamp"): stamp(img, b["stamp"], t, b)
    return img

def s_papel(t, dur, b, gt):
    img = LIGHT.copy(); header(img, light=True)
    polaroid(img, bw(sframe(b["clip"], t * 0.8, b.get("clip_start", 0))), t, rot=b.get("rot", -3), cy=b.get("poly_y", 620))
    block(img, b, t, light=True, top=b.get("text_y", 1010), size=b.get("size", 84))
    if b.get("sticker"): sticker(img, b["sticker"], t, b)
    if b.get("stamp"): stamp(img, b["stamp"], t, b, light=True)
    return img

def s_texto(t, dur, b, gt):
    img = DARK.copy(); header(img)
    block(img, b, t, top=b.get("text_y", 640), size=b.get("size", 100))
    if b.get("stamp"): stamp(img, b["stamp"], t, b)
    return img

def s_fecho(t, dur, b, gt):
    img = photo_bg(bw(reels.kenburns(b["photo"], t, dur, box=b.get("photo_box")))); header(img)
    block(img, b, t, bottom=b.get("bottom", 1130), size=b.get("size", 96))
    tb = t_of(b, b.get("button_k"), 1.5) - 0.15
    if t > tb:
        q = eb((t - tb) / 0.4); y = 1170
        def fn(d):
            d.rounded_rectangle((MX, y, W - MX, y + 130), 65, fill=GREEN)
            d.text((MX + 50, y + 65), b.get("button", "Quero saber se tenho direito"), font=M(700, 31), fill=(255, 255, 255), anchor="lm")
            d.ellipse((W - MX - 112, y + 17, W - MX - 17, y + 112), fill=(255, 255, 255))
            d.line([(W - MX - 88, y + 65), (W - MX - 44, y + 65)], fill=GREEN, width=8)
            d.line([(W - MX - 64, y + 43), (W - MX - 42, y + 65), (W - MX - 64, y + 87)], fill=GREEN, width=8, joint="curve")
            d.text((MX, y + 168), b.get("note", "Atendimento confidencial  •  WhatsApp, contato na bio"), font=M(600, 24), fill=GOLD, anchor="lm")
        put(img, fn, cl(q * 1.5), dy=(1 - q) * 40)
    return img

reels.R.update(cover=s_foto, foto=s_foto, papel=s_papel, texto=s_texto, fecho=s_fecho)
reels.TAIL.update({"fecho": 2.0, "foto": 0.4, "papel": 0.7, "texto": 0.4})

# ---------------- legendas, rodapé, story, trilha ----------------
def captions(img, t, b):
    if not b.get("_cap"): return
    cur = None
    for c in b["_ch"]:
        if c[0][1] <= t: cur = c
    if cur is None or t > cur[-1][2] + 0.6: return
    light = b["kind"] == "papel"; d = ImageDraw.Draw(img); words = [w for w, s, e in cur]
    f = fit(" ".join(words), 800, W - 120, 54)
    sp = d.textlength(" ", font=f); widths = [d.textlength(w, font=f) for w in words]; tw = sum(widths) + sp * (len(words) - 1)
    pop = eb((t - cur[0][1]) / 0.18); y = 1440 + (1 - pop) * 14; x = W / 2 - tw / 2
    base, hi, stk = (TOGA, GOLD_D, PERG) if light else (PERG, GOLD, BG0)
    for (w, s, e), wd in zip(cur, widths):
        d.text((x, y), w, font=f, fill=hi if s <= t < e + 0.05 else base, anchor="lm", stroke_width=6, stroke_fill=stk); x += wd + sp
reels.captions = captions

def chrome(img, gt, total):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, int(W * gt / total), 8), fill=GOLD)
    light = sum(img.getpixel((60, 1590))) / 3 > 170
    d.text((MX, 1590), reels.HANDLE, font=M(500, 25), fill=SLATE if light else MUTED, anchor="lm")
    d.text((W - MX, 1590), reels.SITE, font=M(700, 25), fill=GOLD_D if light else GOLD, anchor="rm")
    return img
reels.chrome = chrome

def make_story(capa_path, out_path, tema):
    capa = Image.open(capa_path).convert("RGB"); base = DARK.copy(); d = ImageDraw.Draw(base)
    f = M(700, 26); txt = "REELS NOVO"; w = sum(d.textlength(c, font=f) + 5 for c in txt) + 56
    d.rounded_rectangle((W / 2 - w / 2, 250, W / 2 + w / 2, 306), 28, outline=(150, 118, 52), width=2); spaced(d, W / 2 - w / 2 + 28, 279, txt, f, GOLD, sp=5)
    d.text((W // 2, 400), "Acabou de sair no perfil", font=PF(800, 64), fill=PERG, anchor="mt")
    th = capa.resize((640, 1138), Image.LANCZOS); m = Image.new("L", th.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, th.width - 1, th.height - 1), 40, fill=255)
    d.rounded_rectangle((W // 2 - 330, 520, W // 2 + 330, 520 + 1158), 48, outline=GOLD, width=5); base.paste(th, (W // 2 - 320, 530), m)
    d.ellipse((W // 2 - 75, 690, W // 2 + 75, 840), fill=GOLD); d.polygon([(W // 2 - 26, 722), (W // 2 - 26, 808), (W // 2 + 50, 765)], fill=TOGA)
    d.text((W // 2, 1730), "Toque no perfil e assista", font=M(600, 38), fill=PERG, anchor="mt"); d.text((W // 2, 1790), reels.HANDLE, font=PF(700, 52), fill=GOLD, anchor="mt")
    base.save(out_path, quality=92)
reels.make_story = make_story

_old_music = reels.make_music
def make_music(T, cut_times, hit_times, wd, seed=1):
    return _old_music(T, cut_times, sorted(set(list(hit_times) + [c + 0.05 for c in cut_times])), wd, seed)
reels.make_music = make_music

if __name__ == "__main__":
    reels.main()
