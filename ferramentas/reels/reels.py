#!/usr/bin/env python3
"""
Gerador de Reels (vídeo vertical 1080x1920, 30 fps, narração + trilha + legendas animadas)
para o Instagram @jacksonbueno.adv.

USO
    python3 ferramentas/reels/reels.py reels/AAAA-MM-DD/spec.json reels/AAAA-MM-DD
    python3 ferramentas/reels/reels.py reels/AAAA-MM-DD/spec.json reels/AAAA-MM-DD --preview   # só quadros de conferência

SAÍDAS (na pasta de saída)
    reel.mp4   vídeo final            capa.jpg   capa (último quadro da cena "cover")
    story.jpg  story avisando do Reels   preview/   quadros para conferir (abra com Read)

DEPENDÊNCIAS (o script instala/baixa o que faltar)
    ffmpeg; pip: piper-tts numpy pillow; voz pt_BR "faber" (Hugging Face, ~60 MB, cache em ~/.cache/piper);
    fontes: npm i @fontsource/montserrat (em ferramentas/); Poppins do sistema, se houver (senão usa Montserrat);
    emoji: NotoColorEmoji (se não houver, os emojis são omitidos).

SPEC (JSON)
{
  "tema": "...",                        # só referência
  "legenda": "texto da legenda (copy)",  # vai para legenda.txt
  "beats": [ cena, cena, ... ]          # cada cena vira um trecho com narração própria
}
Narração: "voz" no topo do spec = "dupla" (mulher e homem alternando; cada cena pode fixar "voz": "mulher" ou "homem"),
"mulher", "homem", "piper" (voz simples, rápida) ou "titular" (voz do titular; exige REELS_VOZ_REF). Padrão atual: "dupla".
As vozes "mulher"/"homem" são sintéticas (modelo Chatterbox Multilingual, licença MIT, CPU, ~8x o tempo real) e cada frase
é conferida por transcrição automática (faster-whisper) e refeita se sair errada.
Toda cena tem "kind", "say" (texto narrado; siglas são convertidas para pronúncia: INSS, CAT, FGTS, B91,
B31, LER, DORT, site...) e, opcionalmente, "cap" (legenda animada na tela; use null para não mostrar).
Se "cap" não for informado, a legenda usa o próprio "say". Palavras-chave ("key") são palavras do "cap"
(ou do "say") que disparam a animação no momento em que são faladas.

Tipos de cena (kind) e campos:
  hook       clip, pill, pill_emoji, line1, line2, key            vídeo de banco + pergunta gigante (gancho 0–3 s)
  cover      clip, pill, pill_emoji, pre, big1, big2, key, badge   vídeo de banco + selo redondo com a foto do titular;
             badge = {"photo": "fotos/x.jpg", "box": [x0,y0,x1,y1]} (recorte quadrado do rosto). O último quadro vira capa.jpg
  montage    segments: [{clip, text, key}]   (o 1º segmento começa no início; key = palavra que inicia o próximo)
  card       header, n, total, emoji, title, sub, bg_clip            cartão numerado sobre vídeo desfocado
  statement  badge, badge_emoji, lines[], highlight, highlight_key, follow1, follow2, follow_key, source
  list       title1, title2, items: [{tok, label, key}]              ex.: B91 / 12 / R$
  check      kicker, title, items: [{label, key}]                    checklist que vai sendo marcado
  cta        photo, question, site, sub, button, button_emoji, key_site, key_button   (foto do titular + site)
Clipes de banco: nomes de arquivo em ferramentas/reels/stock/ (sem .mp4); ver stock/README.md.
Campo opcional em clip: "clip_start" (segundos) para começar mais adiante no vídeo.
"""
import os, sys, json, math, random, subprocess, shutil, wave, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
STOCK = os.path.join(HERE, "stock")

def sh(cmd, **kw): return subprocess.run(cmd, check=True, **kw)

# ---------------- dependências ----------------
def ensure_deps():
    try:
        import numpy, PIL  # noqa
    except ImportError:
        sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "numpy", "pillow"])
    try:
        import piper  # noqa
    except ImportError:
        sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "piper-tts"])
    vdir = os.path.expanduser("~/.cache/piper"); os.makedirs(vdir, exist_ok=True)
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
    for suf in ("", ".json"):
        p = os.path.join(vdir, "faber.onnx" + suf)
        if not os.path.exists(p) or os.path.getsize(p) < 1000:
            sh(["curl", "-sSL", "--max-time", "300", "-o", p, base + suf])
    mont = os.path.join(ROOT, "ferramentas", "node_modules", "@fontsource", "montserrat")
    if not os.path.isdir(mont):
        sh(["npm", "i", "-s", "@fontsource/montserrat"], cwd=os.path.join(ROOT, "ferramentas"), stdout=subprocess.DEVNULL)
    return os.path.join(vdir, "faber.onnx")

VOICE = ensure_deps()
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

W, H, FPS = 1080, 1920, 30
NAVY = (10, 20, 36); NAVY2 = (22, 42, 70); AMBER = (255, 186, 48); WHITE = (250, 250, 246)
SOFT = (190, 200, 214); RED = (232, 72, 60); DIM = (120, 134, 154)
HANDLE = "@jacksonbueno.adv"; SITE = "jacksonbueno.adv.br"
MX = 150          # margem lateral de respiro (px) para todos os elementos inseridos
CW = W - 2 * MX   # largura útil

MS = os.path.join(ROOT, "ferramentas", "node_modules", "@fontsource", "montserrat", "files", "montserrat-latin-%d-normal.woff")
PP = "/usr/share/fonts/truetype/google-fonts/Poppins-%s.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_fc = {}
def M(w, s):
    k = ("m", w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(MS % w, s)
    return _fc[k]
def P(w, s):
    k = ("p", w, s)
    if k not in _fc:
        try: _fc[k] = ImageFont.truetype(PP % w, s)
        except OSError: _fc[k] = M({"Bold": 700, "Medium": 500, "Regular": 400}.get(w, 600), s)
    return _fc[k]

# ---------------- pronúncia ----------------
PRON = [(r"\bINSS\b", "í ene ésse ésse"), (r"\bFGTS\b", "éfe gê tê ésse"), (r"\bCAT\b", "cát"), (r"\bB91\b", "bê noventa e um"),
        (r"\bB31\b", "bê trinta e um"), (r"\bB94\b", "bê noventa e quatro"), (r"\bLER\b", "lér"), (r"\bDORT\b", "dórt"),
        (r"\bPAIR\b", "pair"), (r"\bEPI\b", "ê pê í"), (r"\bCID\b", "cid"), (r"\bNR\b", "ene érre"), (r"\bTST\b", "tê ésse tê"),
        (r"jacksonbueno\.adv\.br", "jéquisson buêno, ponto a dê vê, ponto bê érre"), (r"\bJackson\b", "Jéquisson"),
        (r"\b12 meses\b", "doze meses"), (r"\bR\$", "reais")]
def speakable(s):
    for a, b in PRON: s = re.sub(a, b, s)
    return s

# ---------------- easing ----------------
def cl(x): return max(0.0, min(1.0, x))
def eo(t): t = cl(t); return 1 - (1 - t) ** 3
def eb(t):
    t = cl(t); c1 = 2.2; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def eel(t):
    t = cl(t)
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1

def word_times(text, speech):
    words = text.split(); total = sum(len(w) + 1 for w in words) or 1; acc = 0; out = []
    for w in words:
        s = 0.12 + speech * acc / total; acc += len(w) + 1
        out.append((w, s, 0.12 + speech * acc / total))
    return out
def norm(s): return re.sub(r"[^\wà-ú]", "", s.lower())
def t_of(beat, key, default=0.3):
    if not key: return default
    k = norm(key)
    for w, s, e in beat["_wt"]:
        if k and k in norm(w): return s
    return default

# ---------------- fundo e utilidades ----------------
def make_bg():
    y = np.linspace(0, 1, H + 400)[:, None]; x = np.linspace(0, 1, W)[None, :]
    d = np.sqrt((x - 0.5) ** 2 + ((y - 0.35) * 0.6) ** 2)
    g = np.clip(1 - d * 1.5, 0, 1)[..., None]
    img = np.array(NAVY, float) + (np.array(NAVY2, float) - np.array(NAVY, float)) * g
    yy, xx = np.mgrid[0:H + 400, 0:W]
    img = img + (((xx + yy) // 60) % 2 == 0)[..., None] * 5
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
BG = make_bg()
def bg(gt):
    off = int((gt * 40) % 120); return BG.crop((0, off, W, off + H))

_d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
def fit(text, wt, maxw, start):
    s = start
    while s > 20 and _d0.textlength(text, font=M(wt, s)) > maxw: s -= 2
    return M(wt, s)
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def paste(base, lay, a=1.0, dx=0, dy=0, scale=1.0, cx=W // 2, cy=H // 2):
    if a <= 0: return
    if scale != 1.0:
        sw, shh = max(1, int(W * scale)), max(1, int(H * scale))
        lay = lay.resize((sw, shh), Image.BILINEAR)
        big = layer(); big.paste(lay, (int(cx - cx * scale), int(cy - cy * scale))); lay = big
    if a < 1:
        lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    base.paste(lay, (int(dx), int(dy)), lay)

_em = {}
def emoji(ch, size):
    if not ch or not os.path.exists(EMOJI_FONT): return None
    k = (ch, size)
    if k not in _em:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((90, 90), ch, font=f, embedded_color=True, anchor="mm")
        bb = im.getbbox()
        if not bb: _em[k] = None; return None
        im = im.crop(bb); r = size / max(im.size)
        _em[k] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _em[k]

def pill(img_or_lay, d, text, em_ch, cx=None, x=None, y=0, h=80, fill=AMBER, col=NAVY, size=40):
    pf = M(900, size); lw = d.textlength(text, font=pf); em = emoji(em_ch, int(h * 0.68))
    ew = (em.width + 14) if em else 0
    pw = lw + ew + 56; px = (cx - pw / 2) if cx is not None else x
    d.rounded_rectangle((px, y, px + pw, y + h), h // 2, fill=fill)
    if em: img_or_lay.paste(em, (int(px + 28), int(y + h / 2 - em.height / 2)), em)
    d.text((px + 28 + ew, y + h / 2 + 1), text, font=pf, fill=col, anchor="lm")

def grad_bottom(img, y0, y1, maxa=245):
    ramp = np.clip((np.arange(H) - y0) / max(1, (y1 - y0)), 0, 1) ** 1.3
    g = np.repeat((ramp * maxa).astype(np.uint8)[:, None], W, 1)
    return Image.composite(Image.new("RGB", (W, H), NAVY), img, Image.fromarray(g))
def grad_top(img, h=380, maxa=170):
    ramp = np.clip(1 - np.arange(H) / h, 0, 1) ** 1.5
    g = np.repeat((ramp * maxa).astype(np.uint8)[:, None], W, 1)
    return Image.composite(Image.new("RGB", (W, H), NAVY), img, Image.fromarray(g))
def shade(img, a=0.45): return Image.blend(img, Image.new("RGB", (W, H), NAVY), a)

# fotos do titular
_ph = {}
def photo(rel, box=None):
    k = (rel, tuple(box) if box else None)
    if k not in _ph:
        im = Image.open(os.path.join(ROOT, rel)).convert("RGB")
        if box: im = im.crop(tuple(box))
        r = max(W * 1.12 / im.width, H * 1.12 / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        bw, need = int(W * 1.12), int(H * 1.12); x0 = (im.width - bw) // 2
        _ph[k] = ImageEnhance.Contrast(im.crop((x0, 0, x0 + bw, need))).enhance(1.05)
    return _ph[k]
def kenburns(rel, t, dur, z0=1.0, z1=1.05, box=None):
    src = photo(rel, box); p = t / max(dur, 0.01); z = z0 + (z1 - z0) * p
    cw, ch = W / z, H / z; cx = src.width / 2; cy = ch / 2 + 4 + 20 * p
    return src.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
_face = {}
def face_circle(rel, box, d):
    k = (rel, tuple(box), d)
    if k not in _face:
        im = Image.open(os.path.join(ROOT, rel)).convert("RGB").crop(tuple(box)).resize((d, d), Image.LANCZOS)
        m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
        im.putalpha(m.resize((d, d), Image.LANCZOS)); _face[k] = im
    return _face[k]

# vídeos de banco -> quadros JPEG em cache
WORK = "/tmp/reels_work"
def extract(clip, start=0.0, blur=False):
    tag = f"{clip}_{start}_{int(blur)}"; d = os.path.join(WORK, "frames", tag)
    if os.path.isdir(d) and len(os.listdir(d)) > 5: return d
    os.makedirs(d, exist_ok=True)
    ex = "boxblur=10:2,eq=brightness=-0.12" if blur else "eq=contrast=1.06"
    vf = f"fps=30,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},unsharp=5:5:0.6,{ex}"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-i", os.path.join(STOCK, clip + ".mp4"), "-t", "20", "-vf", vf, "-q:v", "3", f"{d}/%04d.jpg"])
    return d
_nf = {}
def sframe(clip, t, start=0.0, blur=False):
    d = extract(clip, start, blur)
    if d not in _nf: _nf[d] = len(os.listdir(d))
    n = _nf[d]; i = int(t * 30) % (2 * n - 2) if n > 1 else 0   # vai e volta se o clipe acabar
    i = i if i < n else 2 * n - 2 - i
    return Image.open(f"{d}/{i + 1:04d}.jpg").convert("RGB")

# ---------------- moldura e legendas ----------------
def brand(d, y=150):
    d.text((W // 2, y), "JACKSON BUENO  ·  ADVOCACIA PARA O TRABALHADOR", font=P("Medium", 26), fill=SOFT, anchor="mt")
    d.rectangle((W // 2 - 36, y + 44, W // 2 + 36, y + 47), fill=AMBER)
def chrome(img, gt, total):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, int(W * gt / total), 10), fill=AMBER)
    d.text((W // 2, 1575), f"{HANDLE}   ·   {SITE}", font=P("Medium", 30), fill=(205, 212, 222), anchor="mt", stroke_width=2, stroke_fill=NAVY)
    return img
def chunks(wt):
    out, cur = [], []
    for w in wt:
        cur.append(w)
        if len(cur) == 3 or w[0][-1] in ".,:?!": out.append(cur); cur = []
    if cur: out.append(cur)
    return out
def captions(img, t, b):
    if not b.get("_cap"): return
    cur = None
    for c in b["_ch"]:
        if c[0][1] <= t: cur = c
    if cur is None or t > cur[-1][2] + 0.6: return
    d = ImageDraw.Draw(img); words = [w for w, s, e in cur]
    f = fit(" ".join(words), 800, W - 120, 54)   # legendas: tamanho aprovado pelo titular
    sp = d.textlength(" ", font=f); widths = [d.textlength(w, font=f) for w in words]
    tw = sum(widths) + sp * (len(words) - 1)
    pop = eb((t - cur[0][1]) / 0.18); y = 1440 + (1 - pop) * 14; x = W / 2 - tw / 2
    for (w, s, e), wd in zip(cur, widths):
        d.text((x, y), w, font=f, fill=AMBER if s <= t < e + 0.05 else WHITE, anchor="lm", stroke_width=7, stroke_fill=NAVY)
        x += wd + sp

# ---------------- cenas ----------------
def s_hook(t, dur, b, gt):
    img = sframe(b["clip"], t * 0.85, b.get("clip_start", 0))
    img = grad_top(img, 520, 200); img = grad_bottom(img, 900, 1500, 235)
    p = eb(t / 0.3); lay = layer(); dl = ImageDraw.Draw(lay)
    pill(lay, dl, b.get("pill", "CAMINHONEIRO"), b.get("pill_emoji", "🚛"), cx=W / 2, y=330, h=70, size=36)
    paste(img, lay, cl(p * 1.5), scale=0.6 + 0.4 * p, cx=W // 2, cy=365)
    td = t_of(b, b.get("key"), 0.4) - 0.1
    if t > td:
        q = eb((t - td) / 0.3); shk = math.sin((t - td) * 70) * 10 * max(0, 1 - (t - td) / 0.4)
        lay = layer(); dl = ImageDraw.Draw(lay)
        f = M(900, min(fit(b["line1"], 900, CW, 104).size, fit(b["line2"], 900, CW, 104).size))
        dl.text((W // 2, 1050), b["line1"], font=f, fill=WHITE, anchor="mt", stroke_width=4, stroke_fill=NAVY)
        dl.text((W // 2, 1060 + f.size), b["line2"], font=f, fill=AMBER, anchor="mt", stroke_width=4, stroke_fill=NAVY)
        paste(img, lay, cl(q * 1.5), dx=shk, scale=1.4 - 0.4 * q, cx=W // 2, cy=1200)
    return img

def s_cover(t, dur, b, gt):
    img = sframe(b["clip"], t, b.get("clip_start", 0))
    img = grad_top(img, 300, 150); img = grad_bottom(img, 980, 1400, 245)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 150), "JACKSON BUENO  ·  ADVOGADO TRABALHISTA", font=P("Medium", 26), fill=WHITE, anchor="mt", stroke_width=2, stroke_fill=NAVY)
    bd = b.get("badge")
    if bd:
        p = 1 if b.get("_still") else eb((t - 0.25) / 0.45)
        if p > 0.02:
            D = 250; cx, cy = W - MX - 130, 1000; r = int((D / 2 + 9) * p)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=AMBER)
            fc = face_circle(bd["photo"], bd["box"], max(10, int(D * p)))
            img.paste(fc, (int(cx - fc.width / 2), int(cy - fc.height / 2)), fc)
    pill(img, d, b.get("pill", "CAMINHONEIRO"), b.get("pill_emoji", "🚛"), x=MX, y=1010, h=66, size=32)
    d.text((W // 2, 1190), b["pre"], font=P("Bold", 46) if d.textlength(b["pre"], font=P("Bold", 46)) <= CW else fit(b["pre"], 700, CW, 46), fill=WHITE, anchor="mt")
    tp = t_of(b, b.get("key"), 0.3); k = 1 + 0.07 * math.sin(math.pi * cl((t - tp) / 0.35))
    lay = layer(); dl = ImageDraw.Draw(lay)
    f = M(900, min(fit(b["big1"], 900, CW, 104).size, fit(b["big2"], 900, CW, 104).size))
    dl.text((W // 2, 1275), b["big1"], font=f, fill=AMBER, anchor="mt")
    dl.text((W // 2, 1275 + f.size - 8), b["big2"], font=f, fill=AMBER, anchor="mt")
    paste(img, lay, 1, scale=k, cx=W // 2, cy=1400)
    return img

def s_montage(t, dur, b, gt):
    segs = b["segments"]; starts = [0.0] + [t_of(b, s.get("key"), 0) - 0.15 for s in segs[1:]]
    i = max(j for j in range(len(segs)) if t >= starts[j] or j == 0)
    sg = segs[i]; tl = t - starts[i]
    img = sframe(sg["clip"], tl, sg.get("clip_start", 0))
    if i == 1:
        jx = int(math.sin(t * 55) * 6); jy = int(math.cos(t * 41) * 6)
        img = img.transform((W, H), Image.AFFINE, (1, 0, jx, 0, 1, jy), Image.BILINEAR)
    img = shade(img, 0.28); img = grad_bottom(img, 1100, 1550, 200); img = grad_top(img)
    d = ImageDraw.Draw(img); brand(d)
    p = eb(tl / 0.28); lay = layer(); dl = ImageDraw.Draw(lay)
    txt = sg["text"]; f = fit(txt, 900, CW - 60, 76); tw = dl.textlength(txt, font=f); y = 820
    hi = (i % 2 == 1)
    dl.rectangle((W / 2 - tw / 2 - 30, y - 18, W / 2 + tw / 2 + 30, y + f.size + 26), fill=AMBER if hi else NAVY)
    dl.text((W // 2, y), txt, font=f, fill=NAVY if hi else WHITE, anchor="mt")
    dl.text((W // 2, y - 80), f"{i + 1}/{len(segs)}", font=M(800, 40), fill=AMBER, anchor="mt", stroke_width=4, stroke_fill=NAVY)
    paste(img, lay, cl(p * 1.6), scale=1.5 - 0.5 * p, cx=W // 2, cy=y + 60)
    return img

def s_card(t, dur, b, gt):
    img = shade(sframe(b.get("bg_clip", "estrada_pb_caminhoes"), gt - b["_card0"], 0, blur=True), 0.35)
    d = ImageDraw.Draw(img); brand(d)
    d.text((W // 2, 300), b.get("header", ""), font=fit(b.get("header", "") or " ", 800, CW, 36), fill=WHITE, anchor="mt")
    tot = b.get("total", 4)
    for i in range(tot):
        cx = W // 2 - (tot - 1) * 35 + i * 70
        d.rounded_rectangle((cx - 24, 370, cx + 24, 380), 5, fill=AMBER if i < b["n"] else (70, 84, 104))
    p = eb(t / 0.38); lay = layer(); dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((MX, 460, W - MX, 1260), 40, fill=(16, 32, 58, 235), outline=AMBER, width=5)
    dl.text((MX + 44, 500), f"{b['n']:02d}", font=M(900, 58), fill=AMBER, anchor="lt")
    dl.text((W - MX - 44, 512), f"/ {tot:02d}", font=M(800, 32), fill=DIM, anchor="rt")
    title = b["title"]; f = fit(title, 900, CW - 110, 76); words = title.split(); lines = [title]
    if f.size < 62 and len(words) > 1:
        hh = math.ceil(len(words) / 2) if len(words) > 2 else 1
        lines = [" ".join(words[:hh]), " ".join(words[hh:])]
        f = M(900, min(76, min(fit(l, 900, CW - 110, 76).size for l in lines)))
    y0 = 950 if len(lines) == 1 else 915
    for k, ln in enumerate(lines): dl.text((W // 2, y0 + k * (f.size + 6)), ln, font=f, fill=WHITE, anchor="mt")
    sub = b.get("sub", "")
    if sub: dl.text((W // 2, y0 + len(lines) * (f.size + 6) + 30), sub, font=P("Medium", 38) if _d0.textlength(sub, font=P("Medium", 38)) <= CW - 110 else fit(sub, 500, CW - 110, 38), fill=AMBER, anchor="mt")
    pe = eel((t - 0.2) / 0.7)
    if pe > 0.02:
        cy = 735; dl.ellipse((W // 2 - 135 * pe, cy - 135 * pe, W // 2 + 135 * pe, cy + 135 * pe), fill=(36, 64, 104, 255))
        em = emoji(b.get("emoji"), max(10, int(180 * pe)))
        if em: lay.paste(em, (int(W // 2 - em.width / 2), int(cy - em.height / 2)), em)
    paste(img, lay, 1, dx=(1 - p) * W * 0.9)
    return img

def s_statement(t, dur, b, gt):
    img = bg(gt); d = ImageDraw.Draw(img); brand(d)
    p = eb(t / 0.3); lay = layer(); dl = ImageDraw.Draw(lay)
    pill(lay, dl, b.get("badge", "ATENÇÃO"), b.get("badge_emoji", "⚠️"), cx=W / 2, y=330, h=70, fill=RED, col=WHITE, size=36)
    paste(img, lay, 1, scale=0.5 + 0.5 * p, cx=W // 2, cy=371)
    t1 = 0.35; lines = b.get("lines", [])
    f = M(900, min([fit(l, 900, CW, 76).size for l in lines] or [76]))
    for i, ln in enumerate(lines):
        a = eo((t - t1 - i * 0.12) / 0.3)
        if a <= 0: continue
        lay = layer(); ImageDraw.Draw(lay).text((W // 2, 490 + i * (f.size + 12)), ln, font=f, fill=WHITE, anchor="mt")
        paste(img, lay, a, dy=(1 - a) * 40)
    hl = b.get("highlight")
    if hl:
        th = t_of(b, b.get("highlight_key"), 1.2) - 0.15
        if t > th:
            pp = eo((t - th) / 0.35); f2 = fit(hl, 900, CW - 60, 86); tw = d.textlength(hl, font=f2)
            x0 = W / 2 - tw / 2 - 26; y0 = 490 + len(lines) * (f.size + 12) + 10
            d.rectangle((x0, y0, x0 + (tw + 52) * pp, y0 + f2.size + 34), fill=AMBER)
            if pp > 0.4: d.text((W // 2, y0 + 16), hl, font=f2, fill=NAVY, anchor="mt")
    tc = t_of(b, b.get("follow_key"), dur * 0.5) - 0.2
    if t > tc and (b.get("follow1") or b.get("follow2")):
        a = eo((t - tc) / 0.4); lay = layer(); dl = ImageDraw.Draw(lay)
        if b.get("follow1"): dl.text((W // 2, 1080), b["follow1"], font=fit(b["follow1"], 700, CW, 46), fill=WHITE, anchor="mt")
        if b.get("follow2"): dl.text((W // 2, 1150), b["follow2"], font=fit(b["follow2"], 700, CW, 46), fill=AMBER, anchor="mt")
        if b.get("source"): dl.text((W // 2, 1250), b["source"], font=fit(b["source"], 500, CW, 32), fill=DIM, anchor="mt")
        paste(img, lay, a, dy=(1 - a) * 30)
    return img

def s_list(t, dur, b, gt):
    img = bg(gt); d = ImageDraw.Draw(img); brand(d)
    a = eo(t / 0.3); lay = layer(); dl = ImageDraw.Draw(lay)
    dl.text((W // 2, 320), b["title1"], font=fit(b["title1"], 900, CW, 54), fill=WHITE, anchor="mt")
    dl.text((W // 2, 385), b["title2"], font=fit(b["title2"], 900, CW, 54), fill=AMBER, anchor="mt")
    paste(img, lay, a, dy=(1 - a) * 30)
    for i, it in enumerate(b["items"]):
        tp = t_of(b, it.get("key"), 0.5 + i * 0.8) - 0.15
        if t < tp: continue
        p = eb((t - tp) / 0.32); lay = layer(); dl = ImageDraw.Draw(lay); y = 540 + i * 200
        dl.rounded_rectangle((MX, y, W - MX, y + 150), 28, fill=(24, 46, 78))
        dl.rounded_rectangle((MX + 18, y + 18, MX + 132, y + 132), 22, fill=AMBER)
        dl.text((MX + 75, y + 77), it["tok"], font=fit(it["tok"], 900, 90, 54), fill=NAVY, anchor="mm")
        dl.text((MX + 160, y + 75), it["label"], font=fit(it["label"], 800, CW - 190, 40), fill=WHITE, anchor="lm")
        paste(img, lay, cl(p * 1.4), dx=(1 - p) * -500)
    return img

def s_check(t, dur, b, gt):
    img = bg(gt); d = ImageDraw.Draw(img); brand(d)
    a = eo(t / 0.3); lay = layer(); dl = ImageDraw.Draw(lay)
    dl.text((W // 2, 320), b.get("kicker", ""), font=fit(b.get("kicker", "") or " ", 800, CW, 34), fill=SOFT, anchor="mt")
    dl.text((W // 2, 380), b["title"], font=fit(b["title"], 900, CW, 78), fill=WHITE, anchor="mt")
    paste(img, lay, a, scale=0.8 + 0.2 * eb(t / 0.35), cx=W // 2, cy=440)
    for i, it in enumerate(b["items"]):
        y = 580 + i * 170; lay = layer(); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle((MX, y, W - MX, y + 136), 28, fill=(24, 46, 78))
        dl.rounded_rectangle((MX + 30, y + 31, MX + 104, y + 105), 16, outline=AMBER, width=5)
        dl.text((MX + 135, y + 68), it["label"], font=fit(it["label"], 800, CW - 170, 44), fill=WHITE, anchor="lm")
        ai = eo((t - 0.15 - i * 0.1) / 0.3); paste(img, lay, ai, dy=(1 - ai) * 40)
        tp = t_of(b, it.get("key"), 0.6 + i * 0.9) - 0.05
        if t > tp:
            k = eb((t - tp) / 0.25); d2 = ImageDraw.Draw(img)
            d2.rounded_rectangle((MX + 30, y + 31, MX + 104, y + 105), 16, fill=AMBER)
            d2.line([(MX + 46, y + 69), (MX + 62, y + 86)], fill=NAVY, width=10)
            if k > 0.5: d2.line([(MX + 62, y + 86), (MX + 90, y + 50)], fill=NAVY, width=10)
    return img

def s_cta(t, dur, b, gt):
    img = kenburns(b.get("photo", "fotos/jackson-mesa-sorrindo_cta.jpg"), t, dur, box=b.get("photo_box"))
    img = grad_top(img); img = grad_bottom(img, 640, 1080, 250); d = ImageDraw.Draw(img)
    d.text((W // 2, 150), "JACKSON BUENO  ·  ADVOGADO TRABALHISTA", font=P("Medium", 26), fill=WHITE, anchor="mt")
    a = eo(t / 0.35); lay = layer(); dl = ImageDraw.Draw(lay)
    q = b.get("question", "Quer entender o seu caso?")
    dl.text((W // 2, 1000), q, font=P("Bold", 48) if d.textlength(q, font=P("Bold", 48)) <= CW else fit(q, 800, CW, 48), fill=WHITE, anchor="mt")
    paste(img, lay, a, dy=(1 - a) * 30)
    ts = t_of(b, b.get("key_site", "acesse"), 1.2) - 0.1
    if t > ts:
        p = eb((t - ts) / 0.4); lay = layer(); dl = ImageDraw.Draw(lay)
        site = b.get("site", SITE)
        dl.rounded_rectangle((MX, 1095, W - MX, 1215), 30, fill=AMBER)
        dl.text((W // 2, 1157), site, font=fit(site, 900, CW - 90, 60), fill=NAVY, anchor="mm")
        dl.text((W // 2, 1280), b.get("sub", "Dr. Jackson Bueno · OAB/MG 211.217"), font=P("Medium", 32), fill=SOFT, anchor="mt")
        paste(img, lay, cl(p * 1.5), scale=0.7 + 0.3 * p, cx=W // 2, cy=1160)
    tm = t_of(b, b.get("key_button", "mande"), dur * 0.6) - 0.1
    if t > tm and b.get("button"):
        p = eb((t - tm) / 0.35); lay = layer(); dl = ImageDraw.Draw(lay)
        em = emoji(b.get("button_emoji", "🚛"), 46); txt = b["button"]; f = fit(txt, 800, CW - 140, 36)
        ew = (em.width + 14) if em else 0; tw = dl.textlength(txt, font=f) + ew + 56
        dl.rounded_rectangle((W / 2 - tw / 2, 1370, W / 2 + tw / 2, 1450), 40, outline=WHITE, width=4)
        if em: lay.paste(em, (int(W / 2 - tw / 2 + 28), int(1410 - em.height / 2)), em)
        dl.text((W / 2 - tw / 2 + 28 + ew, 1411), txt, font=f, fill=WHITE, anchor="lm")
        paste(img, lay, cl(p * 1.4), dy=(1 - p) * 40)
    return img

R = dict(hook=s_hook, cover=s_cover, montage=s_montage, card=s_card, statement=s_statement, list=s_list, check=s_check, cta=s_cta)
TAIL = {"cta": 2.2, "cover": 0.7, "hook": 0.12}

# ---------------- voz ----------------
# Vozes: ver tts(). "mulher"/"homem" sintéticas (Chatterbox); "titular" usa REELS_VOZ_REF (.wav limpo de 15–25 s)
# com a voz do titular (só se ele pedir; a amostra nunca vai para o repositório público).
_cb = None; _cb_default = None; _wh = None
def _check(path, expected):
    """Transcreve o áudio (faster-whisper) e devolve a semelhança 0–1 com o texto esperado."""
    global _wh
    import difflib, soundfile as sf
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "faster-whisper"]); from faster_whisper import WhisperModel
    if _wh is None: _wh = WhisperModel("small", device="cpu", compute_type="int8")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ar", "16000", "-ac", "1", path + ".16k.wav"])
    a, _ = sf.read(path + ".16k.wav", dtype="float32"); os.remove(path + ".16k.wav")
    got = " ".join(x.text for x in _wh.transcribe(a, language="pt", beam_size=3)[0])
    import unicodedata
    def n(z):
        z = unicodedata.normalize("NFD", z.lower()); z = "".join(c for c in z if unicodedata.category(c) != "Mn")
        return " ".join(w[1:] if w.startswith("h") else w for w in re.sub(r"[^a-z0-9 ]", " ", z).split())
    ratio = difflib.SequenceMatcher(None, n(got), n(expected)).ratio()
    exp_w = [w for w in n(expected).split() if len(w) >= 4]; got_w = n(got).split(); joined = n(got).replace(" ", "")
    def ok(w): return w in joined or any(difflib.SequenceMatcher(None, w, g).ratio() >= 0.85 for g in got_w)
    recall = sum(1 for w in exp_w if ok(w)) / max(1, len(exp_w))   # palavras importantes reconhecidas
    return min(ratio, recall), got

VOZ_DIR = os.path.join(HERE, "voz")
def tts(text, out, expected=None, voz=None):
    """voz: "mulher" (voz padrão do modelo, sintética), "homem" (sintética, referência voz/homem_ref.wav, gerada pelo Piper),
    "titular" (exige REELS_VOZ_REF com a amostra da voz do titular) ou "piper" (voz Piper simples, rápida)."""
    voz = voz or os.environ.get("REELS_VOZ", "piper")
    if voz == "piper":
        sh([sys.executable, "-m", "piper", "-m", VOICE, "-f", out, "--length-scale", "0.86", "--sentence-silence", "0.1"],
           input=text.encode(), capture_output=True)
        return
    ref = {"mulher": None, "homem": os.path.join(VOZ_DIR, "homem_ref.wav"), "titular": os.environ.get("REELS_VOZ_REF")}[voz]
    if voz == "titular" and not ref: sys.exit("voz 'titular' exige REELS_VOZ_REF")
    exag = os.environ.get("REELS_VOZ_EXAG", "0.55")
    import hashlib, copy
    cache = os.path.join(WORK, "voz_cache"); os.makedirs(cache, exist_ok=True)
    key = hashlib.sha1((text + "|" + voz + "|" + str(ref) + "|" + exag).encode()).hexdigest()[:16]
    cp = os.path.join(cache, key + ".wav")
    # ajuste de tom para as vozes ficarem bem distintas (preserva o timbre)
    PITCH = {"mulher": float(os.environ.get("REELS_PITCH_MULHER", "1.18")), "homem": float(os.environ.get("REELS_PITCH_HOMEM", "0.95"))}
    def finish(src):
        pt = PITCH.get(voz)
        if pt and abs(pt - 1) > 0.01: sh(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", f"rubberband=pitch={pt}:formant=preserved", out])
        else: shutil.copy(src, out)
    if os.path.exists(cp): finish(cp); return
    global _cb, _cb_default
    import torch, soundfile as sf
    torch.set_num_threads(os.cpu_count() or 2)
    if _cb is None:
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        except ImportError:
            sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "torch", "torchaudio"])
            sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "--no-deps", "chatterbox-tts"])
            sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "librosa==0.11.0", "s3tokenizer", "transformers==5.2.0",
                "diffusers==0.29.0", "resemble-perth>=1.0.0", "conformer==0.3.2", "safetensors", "pyloudnorm", "omegaconf", "soundfile"])
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        _cb = ChatterboxMultilingualTTS.from_pretrained(device="cpu"); _cb_default = copy.deepcopy(_cb.conds)
    best = (-1, None)
    for tent in range(4):   # gera, confere por transcrição e refaz se alguma palavra saiu errada
        if ref is None:
            _cb.conds = copy.deepcopy(_cb_default)
            w = _cb.generate(text, language_id="pt", exaggeration=float(exag), cfg_weight=0.5)
        else:
            w = _cb.generate(text, language_id="pt", audio_prompt_path=ref, exaggeration=float(exag), cfg_weight=0.5)
        raw = out + f".raw{tent}.wav"; sf.write(raw, w.squeeze(0).cpu().numpy(), _cb.sr)
        fin = out + f".t{tent}.wav"
        sh(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            f"atempo={os.environ.get('REELS_VOZ_TEMPO', '1.08')},highpass=f=70", "-ar", "22050", fin])
        os.remove(raw)
        sc, got = _check(fin, expected or text)
        print(f"  voz {voz} {os.path.basename(out)} tentativa {tent + 1}: {sc:.2f} | {got.strip()}", flush=True)
        if sc > best[0]: best = (sc, fin)
        if sc >= 0.86: break
    shutil.copy(best[1], cp); finish(cp)
    d = os.path.dirname(out) or "."
    for f in os.listdir(d):
        if f.startswith(os.path.basename(out) + ".t"): os.remove(os.path.join(d, f))

# ---------------- áudio ----------------
def dur_of(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
def write_wav(name, a, sr=44100):
    a = np.clip(a / (np.abs(a).max() or 1) * 0.9, -1, 1)
    with wave.open(name, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes((a * 32767).astype(np.int16).tobytes())
def make_music(T, cut_times, hit_times, wd, seed=1):
    sr = 44100; n = int(T * sr); t = np.arange(n) / sr; rng = np.random.default_rng(seed)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    beat = 60 / 112; bar = beat * 4
    progs = [[[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]], [[50, 53, 57], [58, 62, 65], [53, 57, 60], [57, 61, 64]]]
    chords = progs[seed % 2]; mus = np.zeros(n)
    def add(arr, sig, s):
        s = int(s * sr); e = min(n, s + len(sig))
        if 0 <= s < n: arr[s:e] += sig[:e - s]
    for k, b0 in enumerate(np.arange(0, T, beat)):
        tt = np.arange(int(0.35 * sr)) / sr
        add(mus, np.sin(2 * np.pi * (48 + 90 * np.exp(-tt * 35)) * tt) * np.exp(-tt * 9), b0)
        if k % 2 == 1:
            tt2 = np.arange(int(0.2 * sr)) / sr; add(mus, rng.standard_normal(len(tt2)) * np.exp(-tt2 * 25) * 0.35, b0)
        tt3 = np.arange(int(0.05 * sr)) / sr; hp = np.diff(np.r_[0, rng.standard_normal(len(tt3))])
        add(mus, hp * np.exp(-tt3 * 80) * 0.18, b0 + beat / 2)
        c = chords[int(b0 / bar) % 4]; tt4 = np.arange(int(beat * 0.9 * sr)) / sr
        add(mus, np.sign(np.sin(2 * np.pi * note(c[0] - 24) * tt4)) * 0.18 * np.exp(-tt4 * 3), b0)
        for j, m in enumerate([c[0], c[1], c[2], c[1]]):
            ts = np.arange(int(0.18 * sr)) / sr; add(mus, np.sin(2 * np.pi * note(m + 12) * ts) * np.exp(-ts * 18) * 0.16, b0 + j * beat / 4)
    for k, b0 in enumerate(np.arange(0, T, bar)):
        c = chords[k % 4]; tt = np.arange(int((bar + 0.3) * sr)) / sr
        env = np.minimum(1, tt / 0.4) * np.minimum(1, np.maximum(0, (bar + 0.3 - tt) / 0.4))
        add(mus, sum(np.sin(2 * np.pi * note(m) * tt) + 0.4 * np.sin(2 * np.pi * note(m) * 2.01 * tt) for m in c) * env * 0.07, b0)
    mus *= np.minimum(1, t / 0.3) * np.minimum(1, (T - t) / 1.5)
    sfx = np.zeros(n)
    for c in cut_times:
        L = int(0.35 * sr); tt = np.arange(L) / sr; x = rng.standard_normal(L)
        y = np.convolve(x, np.ones(6) / 6, "same") - np.convolve(x, np.ones(40) / 40, "same")
        add(sfx, y * np.sin(np.pi * np.clip(tt / 0.35, 0, 1)) ** 2 * 0.9, c - 0.2)
    tt = np.arange(int(0.5 * sr)) / sr; boom = np.sin(2 * np.pi * (40 + 60 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 6)
    for h in hit_times: add(sfx, boom, h)
    write_wav(f"{wd}/music.wav", mus); write_wav(f"{wd}/sfx.wav", sfx)

# ---------------- story de aviso ----------------
def make_story(capa_path, out_path, tema):
    capa = Image.open(capa_path).convert("RGB")
    from PIL import ImageFilter
    base = shade(capa.filter(ImageFilter.GaussianBlur(30)), 0.55); d = ImageDraw.Draw(base)
    pill(base, d, "REELS NOVO", "🎬", cx=W / 2, y=250, h=96, size=50)
    d.text((W // 2, 390), "Acabou de sair no perfil!", font=P("Bold", 60), fill=WHITE, anchor="mt")
    th = capa.resize((640, 1138), Image.LANCZOS)
    m = Image.new("L", th.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, th.width - 1, th.height - 1), 40, fill=255)
    d.rounded_rectangle((W // 2 - 330, 500, W // 2 + 330, 500 + 1158), 48, fill=AMBER)
    base.paste(th, (W // 2 - 320, 510), m)
    tri = [(W // 2 - 32, 700), (W // 2 - 32, 790), (W // 2 + 46, 745)]
    d.ellipse((W // 2 - 75, 670, W // 2 + 75, 820), fill=(10, 20, 36))
    d.polygon(tri, fill=WHITE)
    d.text((W // 2, 1710), "Toque no perfil e assista", font=P("Bold", 54), fill=WHITE, anchor="mt")
    d.text((W // 2, 1790), HANDLE, font=M(900, 56), fill=AMBER, anchor="mt")
    base.save(out_path, quality=92)

# ---------------- principal ----------------
def main():
    spec_path, outdir = sys.argv[1], sys.argv[2]; preview_only = "--preview" in sys.argv
    spec = json.load(open(spec_path)); beats = spec["beats"]
    os.makedirs(outdir, exist_ok=True); wd = os.path.join(WORK, "tmp"); shutil.rmtree(wd, ignore_errors=True); os.makedirs(wd)
    acc = 0.0
    for i, b in enumerate(beats):
        b["id"] = f"b{i:02d}"; p = f"{wd}/{b['id']}.wav"
        voz = b.get("voz") or spec.get("voz")
        if spec.get("voz") == "dupla" and not b.get("voz"): voz = "mulher" if i % 2 == 0 else "homem"
        tts(speakable(b["say"]), p, expected=b["say"], voz=voz)
        sp = dur_of(p); b["dur"] = round(sp + TAIL.get(b["kind"], 0.22), 3); b["start"] = acc; acc += b["dur"]
        cap = b.get("cap", b["say"]); b["_cap"] = cap
        b["_wt"] = word_times(cap or b["say"], sp - 0.15); b["_ch"] = chunks(b["_wt"])
    total = acc
    c0 = [b["start"] for b in beats if b["kind"] == "card"]
    for b in beats: b["_card0"] = c0[0] if c0 else 0
    def frame(b, t):
        img = R[b["kind"]](t, b["dur"], b, b["start"] + t); captions(img, t, b)
        if b["start"] > 0 and t < 0.16:
            z = 1 + 0.07 * (1 - eo(t / 0.16)); sw, shh = int(W * z), int(H * z)
            img = img.resize((sw, shh), Image.BILINEAR).crop(((sw - W) // 2, (shh - H) // 2, (sw - W) // 2 + W, (shh - H) // 2 + H))
        return chrome(img, b["start"] + t, total)
    # capa e story
    cov = [b for b in beats if b["kind"] == "cover"]
    if cov:
        cb = cov[0]; cb["_still"] = True; capa = frame(cb, cb["dur"] - 0.05); cb["_still"] = False
    else: capa = frame(beats[0], beats[0]["dur"] * 0.8)
    capa.save(f"{outdir}/capa.jpg", quality=92)
    make_story(f"{outdir}/capa.jpg", f"{outdir}/story.jpg", spec.get("tema", ""))
    pv = os.path.join(outdir, "preview"); os.makedirs(pv, exist_ok=True)
    for b in beats:
        for fr in (0.55, 0.95): frame(b, b["dur"] * fr).resize((540, 960)).save(f"{pv}/{b['id']}_{int(fr * 100)}.jpg", quality=80)
    print(f"duração total: {total:.1f}s; prévias em {pv}")
    if preview_only: return
    files = []
    for b in beats:
        n = int(round(b["dur"] * FPS)); tmp = f"{wd}/{b['id']}.tmp.mp4"
        pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for i in range(n): pr.stdin.write(frame(b, i / FPS).convert("RGB").tobytes())
        pr.stdin.close()
        if pr.wait() != 0: sys.exit("falha ao codificar " + b["id"])
        os.rename(tmp, f"{wd}/{b['id']}.mp4"); files.append(f"{wd}/{b['id']}.mp4"); print("cena ok", b["id"], flush=True)
    open(f"{wd}/list.txt", "w").write("".join(f"file '{f}'\n" for f in files))
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{wd}/list.txt", "-c", "copy", f"{wd}/video.mp4"])
    hits = []
    for b in beats:
        if b["kind"] == "hook": hits.append(b["start"] + t_of(b, b.get("key"), 0.4))
        if b["kind"] == "cover": hits.append(b["start"] + 0.1)
    make_music(total, [b["start"] for b in beats[1:]], hits, wd, seed=len(spec.get("tema", "")))
    ins, flt = [], []
    for k, b in enumerate(beats):
        ins += ["-i", f"{wd}/{b['id']}.wav"]; ms = int((b["start"] + 0.06) * 1000)
        flt.append(f"[{k}:a]aresample=44100,adelay={ms}|{ms}[v{k}]")
    fc = ";".join(flt) + ";" + "".join(f"[v{k}]" for k in range(len(beats))) + f"amix=inputs={len(beats)}:normalize=0,apad,atrim=0:{total}[a]"
    sh(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[a]", "-ac", "1", f"{wd}/voice.wav"])
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{wd}/video.mp4", "-i", f"{wd}/voice.wav", "-i", f"{wd}/music.wav", "-i", f"{wd}/sfx.wav", "-filter_complex",
        "[1:a]highpass=f=80,acompressor=threshold=-18dB:ratio=3,volume=1.7,aformat=channel_layouts=stereo,asplit[v1][v2];"
        "[2:a]volume=0.30,aformat=channel_layouts=stereo[m];[m][v1]sidechaincompress=threshold=0.05:ratio=5:attack=15:release=350[md];"
        "[3:a]volume=0.35,aformat=channel_layouts=stereo[s];[md][v2][s]amix=inputs=3:normalize=0,alimiter=limit=0.95[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{outdir}/reel.tmp.mp4"])
    os.rename(f"{outdir}/reel.tmp.mp4", f"{outdir}/reel.mp4")
    if spec.get("legenda"): open(f"{outdir}/legenda.txt", "w").write(spec["legenda"].strip() + "\n")
    print("pronto:", f"{outdir}/reel.mp4", f"({total:.1f}s)")

if __name__ == "__main__":
    main()
