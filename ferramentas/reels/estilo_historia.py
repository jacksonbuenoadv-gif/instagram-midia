#!/usr/bin/env python3
"""
Estilo "história" para Reels do @jacksonbueno.adv (modelo enviado pelo titular em 26/11/2026).

Mesmo gerador do reels.py (voz, legendas animadas, trilha, regra dos clipes), com cenas novas:
  foto    clip, label, lines[{t,c,k}], sub{t,k}, circle{box,k}, stamp{...}, tag{...}   foto de banco em preto e branco azulado + título
  papel   clip, rot, kicker, lines[{t,c,k}], sub{t,k}, sticker{...}, tag{...}, stamp{...} fundo de papel com foto colada (polaroid)
  texto   lines[{t,c,k}]                                                              só texto grande, aparece palavra por frase
  fecho   photo, photo_box, lines[{t,c,k}], button, button_k, assinatura              fundo âmbar com botão (chamada para o WhatsApp)
c: "w" branco, "a" âmbar, "d" apagado, "n" azul-marinho (em papel/âmbar), "o" âmbar escuro (em papel)
k: palavra falada que dispara a animação.

USO (igual ao reels.py):  python3 ferramentas/reels/estilo_historia.py spec.json pasta_saida [--preview]
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels
from reels import (W, H, NAVY, NAVY2, AMBER, WHITE, SOFT, DIM, MX, CW, HANDLE, SITE, M, P, fit, layer, paste, eo, eb, cl,
                   t_of, sframe, grad_bottom, grad_top, face_circle, np, Image, ImageDraw)
from PIL import ImageOps, ImageEnhance, ImageFilter

_d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
PAPER = (233, 227, 213)
AMBER_D = (196, 116, 0)        # âmbar escuro: texto sobre papel claro
INK = (14, 26, 46)
COL = {"w": WHITE, "a": AMBER, "d": (150, 160, 176), "n": INK, "o": AMBER_D}

# ---------------- utilidades ----------------
def _paper():
    rng = np.random.default_rng(7)
    low = rng.normal(0, 1, (H // 4 + 2, W // 4 + 2))
    low = np.array(Image.fromarray(np.clip(low * 22 + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) - 128
    fine = rng.normal(0, 1, (H, W))
    img = np.array(PAPER, float)[None, None, :] + (low / 22 * 3.5)[..., None] + (fine * 3.2)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.07 * np.clip(np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) - 0.5, 0, 1)
    return Image.fromarray(np.clip(img * vig[..., None], 0, 255).astype(np.uint8))
PAPER_IMG = _paper()

def bw(img):
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.12)
    return ImageOps.colorize(g, black=(8, 16, 30), white=(238, 240, 242)).convert("RGB")

def spaced(d, x, y, text, font, fill, sp=3, anchor="l"):
    w = sum(d.textlength(c, font=font) + sp for c in text) - sp
    if anchor == "r": x -= w
    elif anchor == "m": x -= w / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill, anchor="lm"); x += d.textlength(c, font=font) + sp
    return w

def header(img, ink, y=150):
    d = ImageDraw.Draw(img); f = P("Bold", 22)
    spaced(d, MX, y, "JACKSON BUENO", f, ink)
    w = spaced(d, W - MX, y, "ADVOCACIA PARA O TRABALHADOR", f, ink, anchor="r")
    d.rectangle((W - MX - w - 28, y - 7, W - MX - w - 14, y + 7), fill=AMBER)
    d.rectangle((MX, y + 26, W - MX, y + 28), fill=ink)

def put(img, fn, a=1.0, dy=0.0, scale=1.0, cx=W // 2, cy=H // 2):
    if a <= 0.001: return
    if a >= 0.999 and not dy and scale == 1.0: fn(ImageDraw.Draw(img)); return
    lay = layer(); fn(ImageDraw.Draw(lay)); paste(img, lay, a, dy=dy, scale=scale, cx=cx, cy=cy)

def title_font(lines, size=104):
    return M(900, min([fit(l["t"], 900, CW, size).size for l in lines] or [size]))

def draw_lines(img, b, t, y0, ink_default="w", size=104, gap=10):
    """Frases grandes, uma por linha, que sobem e aparecem na palavra falada (k)."""
    lines = b.get("lines", [])
    if not lines: return y0
    f = title_font(lines, size); y = y0
    for i, ln in enumerate(lines):
        t0 = t_of(b, ln.get("k"), 0.15 + 0.12 * i) - 0.12
        a = eo((t - t0) / 0.28); col = COL[ln.get("c", ink_default)]
        fs = M(900, min(f.size, fit(ln["t"], 900, CW, size).size)) if ln.get("solo") else f
        put(img, lambda d, y=y, ln=ln, fs=fs, col=col: d.text((MX, y), ln["t"], font=fs, fill=col, anchor="la"), a, dy=(1 - a) * 36)
        y += fs.size + gap
    return y

def height_of(b, size=104, gap=10):
    lines = b.get("lines", []); f = title_font(lines, size)
    return len(lines) * (f.size + gap)

def label(img, b, t, y, ink=NAVY, fill=AMBER):
    txt = b.get("label")
    if not txt: return
    a = eo((t - 0.05) / 0.25); f = P("Bold", 26); d0 = ImageDraw.Draw(img)
    w = sum(d0.textlength(c, font=f) + 3 for c in txt) + 30
    def fn(d):
        d.rectangle((MX, y, MX + w, y + 46), fill=fill); spaced(d, MX + 15, y + 24, txt, f, ink, sp=3)
    put(img, fn, a, dy=(1 - a) * 20)

def sub(img, b, t, y, col=SOFT):
    s = b.get("sub")
    if not s: return
    t0 = t_of(b, s.get("k"), 0.8) - 0.1; a = eo((t - t0) / 0.35)
    sz = 40
    while sz > 24 and _d0.textlength(s["t"], font=P("Medium", sz)) > CW: sz -= 2
    f = P("Medium", sz)
    put(img, lambda d: d.text((MX, y), s["t"], font=f, fill=col, anchor="la"), a, dy=(1 - a) * 20)

def circle_mark(img, c, t, b):
    t0 = t_of(b, c.get("k"), 0.6) - 0.1; p = cl((t - t0) / 0.55)
    if p <= 0: return
    x0, y0, x1, y1 = c["box"]; cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    pts = []; n = 90
    for i in range(int(n * p) + 1):
        a = math.radians(-110 + 395 * i / n); r = 1 + 0.045 * (i / n)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    if len(pts) > 1:
        d = ImageDraw.Draw(img); d.line(pts, fill=AMBER, width=10, joint="curve")

def stamp(img, s, t, b, default_k=None):
    """Carimbo inclinado (contorno ou cheio) que bate na tela."""
    t0 = t_of(b, s.get("k"), 1.0) - 0.1; p = eb((t - t0) / 0.32)
    if t < t0: return
    fs = s.get("size", 44); f = M(900, fs); lines = s["t"].split("\n"); d0 = ImageDraw.Draw(img)
    tw = max(d0.textlength(l, font=f) for l in lines); th = len(lines) * (fs + 8)
    pad = 26; w, h = int(tw + pad * 2), int(th + pad * 2 - 8)
    s_im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(s_im)
    fill = s.get("fill", False); col = s.get("color", AMBER)
    if fill: d.rounded_rectangle((0, 0, w - 1, h - 1), 10, fill=col)
    else:
        d.rounded_rectangle((0, 0, w - 1, h - 1), 10, outline=col, width=7); d.rounded_rectangle((12, 12, w - 13, h - 13), 6, outline=col, width=3)
    tc = s.get("text", NAVY if fill else col)
    for i, l in enumerate(lines): d.text((w / 2, pad - 4 + i * (fs + 8)), l, font=f, fill=tc, anchor="mt")
    sc = 0.55 + 0.45 * p; s_im = s_im.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS)
    s_im = s_im.rotate(s.get("rot", -6), resample=Image.BICUBIC, expand=True)
    cx, cy = s["pos"]; img.paste(s_im, (int(cx - s_im.width / 2), int(cy - s_im.height / 2)), s_im)

def sticker(img, s, t, b):
    """Selo redondo (âmbar) com texto, como o '3 listras' do modelo."""
    t0 = t_of(b, s.get("k"), 1.0) - 0.1; p = eb((t - t0) / 0.35)
    if t < t0: return
    D = s.get("d", 250); im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=AMBER); d.ellipse((12, 12, D - 13, D - 13), outline=NAVY, width=4)
    big, small = s.get("big", ""), s.get("small", "")
    d.text((D / 2, D * 0.42), big, font=M(900, s.get("bigsize", 96)), fill=NAVY, anchor="mm")
    d.text((D / 2, D * 0.74), small, font=M(900, 24), fill=NAVY, anchor="mm")
    sc = 0.4 + 0.6 * p; im = im.resize((max(1, int(D * sc)), max(1, int(D * sc))), Image.LANCZOS).rotate(s.get("rot", 8), resample=Image.BICUBIC, expand=True)
    cx, cy = s["pos"]; img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def price_tag(img, s, t, b):
    """Etiqueta de preço (papel branco com furo) para o número que importa."""
    t0 = t_of(b, s.get("k"), 1.0) - 0.1; p = eb((t - t0) / 0.35)
    if t < t0: return
    w, h = 470, 190; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(0, h / 2), (46, 0), (w - 1, 0), (w - 1, h - 1), (46, h - 1)], fill=(250, 247, 238), outline=(60, 60, 60))
    d.ellipse((38, h / 2 - 12, 62, h / 2 + 12), fill=(90, 90, 90))
    d.text((w / 2 + 38, 44), s["small"], font=P("Bold", 24), fill=INK, anchor="mm")
    d.text((w / 2 + 38, 112), s["big"], font=M(900, s.get("bigsize", 76)), fill=INK, anchor="mm")
    sc = 0.5 + 0.5 * p; im = im.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS).rotate(s.get("rot", 7), resample=Image.BICUBIC, expand=True)
    cx, cy = s["pos"]; img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def extras(img, b, t):
    if b.get("circle"): circle_mark(img, b["circle"], t, b)
    if b.get("tag"): price_tag(img, b["tag"], t, b)
    if b.get("sticker"): sticker(img, b["sticker"], t, b)
    if b.get("stamp"): stamp(img, b["stamp"], t, b)

def polaroid(img, frame, t, rot=-3, pw=640, ph=520, cx=W // 2, cy=520, t0=0.0):
    p = eb((t - t0) / 0.45)
    if t < t0: return
    B = 20; ph_img = ImageOps.fit(frame, (pw, ph), centering=(0.5, 0.45))
    card = Image.new("RGBA", (pw + 2 * B, ph + B + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rectangle((0, 0, card.width - 1, card.height - 1), fill=(252, 250, 244)); card.paste(ph_img, (B, B))
    sh = Image.new("RGBA", (card.width + 120, card.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((60, 78, 60 + card.width, 78 + card.height), fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(16)); sh.paste(card, (60, 60), card)
    for tx in (card.width * 0.12, card.width * 0.78):   # fita adesiva nos cantos de cima
        tape = Image.new("RGBA", (190, 62), (226, 212, 170, 215)); tape = tape.rotate(-28 if tx < 200 else 24, expand=True, resample=Image.BICUBIC)
        sh.paste(tape, (int(60 + tx - tape.width / 2 + 30), int(60 - 34)), tape)
    sc = (1.12 - 0.12 * p); out = sh.resize((int(sh.width * sc), int(sh.height * sc)), Image.LANCZOS).rotate(rot + (1 - p) * 4, expand=True, resample=Image.BICUBIC)
    out.putalpha(out.split()[3].point(lambda v: int(v * cl(p * 1.6))))
    img.paste(out, (int(cx - out.width / 2), int(cy - out.height / 2)), out)

# ---------------- cenas ----------------
def s_foto(t, dur, b, gt):
    img = bw(sframe(b["clip"], t * 0.85, b.get("clip_start", 0)))
    img = grad_top(img, 360, 170); img = grad_bottom(img, 560, 1320, 242)
    header(img, WHITE)
    lines = b.get("lines", []); hh = height_of(b); ytop = 1375 - hh - (62 if b.get("sub") else 0)
    label(img, b, t, ytop - 78)
    y = draw_lines(img, b, t, ytop); sub(img, b, t, y + 6)
    extras(img, b, t)
    return img

def s_papel(t, dur, b, gt):
    img = PAPER_IMG.copy(); header(img, INK)
    fr = bw(sframe(b["clip"], t * 0.8, b.get("clip_start", 0)))
    polaroid(img, fr, t, rot=b.get("rot", -3), cy=b.get("poly_y", 540))
    d = ImageDraw.Draw(img); y = b.get("text_y", 930)
    if b.get("kicker"):
        a = eo((t - 0.2) / 0.3); f = P("Bold", 27)
        put(img, lambda d: spaced(d, MX, y + 14, b["kicker"], f, INK, sp=3), a, dy=(1 - a) * 18); y += 52
    y = draw_lines(img, b, t, y, ink_default="n", size=100)
    sub(img, b, t, y + 6, col=(88, 96, 112))
    extras(img, b, t)
    return img

def s_texto(t, dur, b, gt):
    img = reels.bg(gt); header(img, WHITE)
    lines = b.get("lines", []); hh = height_of(b, 100, 14)
    y = draw_lines(img, b, t, 700, size=100, gap=14); sub(img, b, t, y + 10)
    extras(img, b, t)
    return img

def s_fecho(t, dur, b, gt):
    img = Image.new("RGB", (W, H), AMBER); header(img, INK)
    p = eb(t / 0.4); D = 250
    if b.get("photo"):
        fc = face_circle(b["photo"], b["photo_box"], max(10, int(D * p))); cx, cy = MX + D // 2, 500
        d = ImageDraw.Draw(img); r = int((D / 2 + 10) * p); d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK)
        img.paste(fc, (int(cx - fc.width / 2), int(cy - fc.height / 2)), fc)
        d.text((cx + D // 2 + 40, cy - 28), "Dr. Jackson Bueno", font=M(900, 40), fill=INK, anchor="lm")
        d.text((cx + D // 2 + 40, cy + 22), "Advogado de acidente de trabalho", font=P("Medium", 27), fill=INK, anchor="lm")
        d.text((cx + D // 2 + 40, cy + 58), "e doença ocupacional · OAB/MG 211.217", font=P("Medium", 27), fill=INK, anchor="lm")
    y = draw_lines(img, b, t, 760, ink_default="n", size=100)
    tb = t_of(b, b.get("button_k"), 1.5) - 0.15
    if t > tb:
        q = eb((t - tb) / 0.4); bt = b.get("button", "ME CHAMA NO WHATSAPP")
        def fn(d):
            d.rounded_rectangle((MX, y + 50, W - MX, y + 190), 70, fill=INK)
            f = P("Bold", 30)
            d.text((MX + 50, y + 105), bt, font=f, fill=WHITE, anchor="lm"); d.text((MX + 50, y + 146), b.get("button2", "O contato está na bio"), font=P("Medium", 26), fill=AMBER, anchor="lm")
            d.ellipse((W - MX - 130, y + 65, W - MX - 20, y + 175), fill=AMBER)
            d.line([(W - MX - 100, y + 120), (W - MX - 52, y + 120)], fill=INK, width=8); d.line([(W - MX - 72, y + 98), (W - MX - 50, y + 120), (W - MX - 72, y + 142)], fill=INK, width=8, joint="curve")
        put(img, fn, cl(q * 1.5), dy=(1 - q) * 40)
    if b.get("after"):
        ta = t_of(b, b.get("after_k"), 2.5) - 0.1; a = eo((t - ta) / 0.35)
        put(img, lambda d: d.text((W // 2, y + 250), b["after"], font=P("Bold", 30), fill=INK, anchor="mm"), a, dy=(1 - a) * 20)
    return img

reels.R.update(foto=s_foto, papel=s_papel, texto=s_texto, fecho=s_fecho)
reels.TAIL.update({"fecho": 2.0, "foto": 0.4, "papel": 0.7, "texto": 0.4})

# rodapé legível em fundo claro/âmbar e barra de progresso que não some
_old_chrome = reels.chrome
def chrome(img, gt, total):
    d = ImageDraw.Draw(img)
    top = img.getpixel((20, 40)); light = sum(top) / 3 > 150
    bar = INK if (light or (top[0] > 200 and top[2] < 120)) else AMBER
    d.rectangle((0, 0, int(W * gt / total), 10), fill=bar)
    reg = img.crop((300, 1565, 780, 1615)).resize((1, 1), Image.BILINEAR).getpixel((0, 0))
    if sum(reg) / 3 > 140:
        d.text((W // 2, 1575), f"{HANDLE}   ·   {SITE}", font=P("Medium", 30), fill=INK, anchor="mt")
    else:
        d.text((W // 2, 1575), f"{HANDLE}   ·   {SITE}", font=P("Medium", 30), fill=(205, 212, 222), anchor="mt", stroke_width=2, stroke_fill=NAVY)
    return img
reels.chrome = chrome

# um "baque" de graves no começo de cada cena nova (como no modelo)
_old_music = reels.make_music
def make_music(T, cut_times, hit_times, wd, seed=1):
    return _old_music(T, cut_times, sorted(set(list(hit_times) + [c + 0.05 for c in cut_times])), wd, seed)
reels.make_music = make_music

if __name__ == "__main__":
    reels.main()
