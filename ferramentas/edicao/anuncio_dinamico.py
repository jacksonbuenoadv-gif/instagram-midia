"""Edição dinâmica do vídeo 'Doença do trabalho é acidente de trabalho' (Jackson Bueno Advogados).
Zonas seguras do Meta (Reels/Stories/Feed 4:5): texto entre y=285 e y=1248, laterais 65 px.
Uso: python3 render2.py [--preview t1,t2] [--out final.mp4]
"""
import json, sys, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BASE = 'base.mov'
FONT = 'node_modules/@fontsource/montserrat/files/montserrat-latin-%d-normal.woff'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
AMBER = (255, 186, 48); WHITE = (255, 255, 255); GLOW = (70, 150, 255)
RED = (235, 70, 70); GREEN = (40, 200, 110); NAVY = (10, 20, 36)

_fc = {}
def F(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(FONT % w, s)
    return _fc[k]
D0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
def tl(t, f): return D0.textlength(t, font=f)

def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((90, 90), ch, font=f, embedded_color=True, anchor='mm')
    im = im.crop(im.getbbox()); r = size / max(im.size)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)

def glow_box(w, h, r=18, fill=(10, 20, 36, 215), glow=GLOW, gw=7, border=2):
    pad = gw * 3
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    g = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle([pad, pad, pad + w, pad + h], r, outline=glow + (190,), width=gw)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(gw)))
    ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + w, pad + h], r, fill=fill, outline=glow + (230,), width=border)
    return im, pad

def tglow(im, xy, txt, font, fill, anchor='lm', glow=(60, 140, 255), rad=5):
    g = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text(xy, txt, font=font, fill=glow + (150,), anchor=anchor)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(rad)))
    ImageDraw.Draw(im).text(xy, txt, font=font, fill=fill, anchor=anchor)

# ---------------- elementos ----------------
def el_badge():
    f = F(900, 27); txt = 'ACIDENTE DE TRABALHO'; e = emoji('⚠️', 30)
    w, h = int(tl(txt, f)) + e.width + 50, 50
    im, p = glow_box(w, h, r=25, fill=(10, 20, 36, 230), glow=AMBER, gw=5, border=2)
    im.alpha_composite(e, (p + 18, p + (h - e.height) // 2))
    ImageDraw.Draw(im).text((p + 18 + e.width + 11, p + h // 2 + 1), txt, font=f, fill=WHITE, anchor='lm')
    return im, p

def el_hook():
    l0, l1, l2 = 'Coluna, tendinite, audição, burnout...', 'DOENÇA DO TRABALHO', 'É ACIDENTE DE TRABALHO'
    f0, f1, f2 = F(700, 31), F(900, 48), F(900, 48)
    w = int(max(tl(l0, f0), tl(l1, f1), tl(l2, f2))) + 70; h = 40 + 56 + 56 + 38
    im, p = glow_box(w, h, r=22)
    cx = p + w // 2
    ImageDraw.Draw(im).text((cx, p + 34), l0, font=f0, fill=(215, 225, 240), anchor='mm')
    tglow(im, (cx, p + 86), l1, f1, WHITE, 'mm')
    tglow(im, (cx, p + 142), l2, f2, AMBER, 'mm', glow=(255, 150, 0))
    return im, p

def el_side(icon, l1, l2, col=WHITE, w=232):
    f1, f2 = F(900, 31), F(700, 25)
    while tl(l1, f1) > w - 24: f1 = F(900, f1.size - 1)
    while l2 and tl(l2, f2) > w - 24: f2 = F(700, f2.size - 1)
    e = emoji(icon, 54)
    h = 18 + e.height + 12 + 36 + (32 if l2 else 0) + 14
    im, p = glow_box(w, h, r=18)
    im.alpha_composite(e, (p + (w - e.width) // 2, p + 18))
    y = p + 18 + e.height + 12
    tglow(im, (p + w // 2, y + 16), l1, f1, col, 'mm', glow=(255, 150, 0) if col == AMBER else (60, 140, 255))
    if l2: ImageDraw.Draw(im).text((p + w // 2, y + 50), l2, font=f2, fill=(225, 232, 242), anchor='mm')
    return im, p

def el_stat(num='472 MIL', lines=('afastamentos por', 'saúde mental', 'em 2024'), fonte='Fonte: Ministério da Previdência'):
    w, h = 250, 300
    im, p = glow_box(w, h, r=18)
    d = ImageDraw.Draw(im)
    e = emoji('📊', 46); im.alpha_composite(e, (p + (w - e.width) // 2, p + 16))
    tglow(im, (p + w // 2, p + 112), num, F(900, 50), AMBER, 'mm', glow=(255, 150, 0))
    for i, l in enumerate(lines):
        d.text((p + w // 2, p + 160 + i * 30), l, font=F(800, 25), fill=WHITE, anchor='mm')
    d.text((p + w // 2, p + h - 16), fonte, font=F(600, 14), fill=(185, 198, 215), anchor='mm')
    return im, p

def el_line(icon, txt, sub=None, col=WHITE, fill=(10, 20, 36, 225), glow=GLOW, maxw=900):
    f = F(900, 34); fs = F(600, 22)
    while tl(txt, f) > maxw - 110: f = F(900, f.size - 1)
    e = emoji(icon, 44)
    w = int(max(tl(txt, f), tl(sub, fs) if sub else 0)) + e.width + 70
    h = 70 if not sub else 98
    im, p = glow_box(w, h, r=20, fill=fill, glow=glow)
    im.alpha_composite(e, (p + 20, p + (h - e.height) // 2))
    x = p + 20 + e.width + 16
    if sub:
        tglow(im, (x, p + 36), txt, f, col, 'lm')
        ImageDraw.Draw(im).text((x, p + 72), sub, font=fs, fill=(215, 228, 240), anchor='lm')
    else:
        tglow(im, (x, p + h // 2 + 1), txt, f, col, 'lm')
    return im, p

# ---------------- legendas ----------------
KEY = {'DOENÇA', 'TRABALHO', 'TRABALHO,', 'TRABALHO.', 'ACIDENTE', 'COLUNA', 'PESO,', 'TENDINITE', 'REPETITIVO,', 'AUDIÇÃO',
       'BARULHO,', 'BURNOUT', 'COBRANÇA,', 'ASSÉDIO', 'CAUSOU', 'PIOROU', 'LEI', 'RENDA', 'AFASTAMENTO,', 'FGTS', 'GARANTIA',
       'EMPREGO', 'INDENIZAÇÃO', 'EMPRESA.', 'WHATSAPP', 'PASSO', 'DIREITOS.'}
FIX = {'Whatsapp': 'WhatsApp', 'whatsapp': 'WhatsApp'}
WEAK = {'o', 'a', 'os', 'as', 'de', 'e', 'no', 'na', 'um', 'uma', 'que', 'pelos', 'pela', 'pelo', 'se', 'me', 'te', 'eu', 'do',
        'da', 'dos', 'pra', 'por', 'para', 'como', 'foi', 'tem', 'seu', 'seus', 'isso', 'lhe', 'quem', 'ou', 'ser'}

def chunks(words, t0):
    out = []; cur = []
    L = lambda c: sum(len(x[0]) for x in c) + len(c) - 1
    for x in words:
        if x['S'] < t0 - 0.05: continue
        w = FIX.get(x['w'], x['w'])
        if cur and L(cur) + 1 + len(w) > 18:
            out.append(cur); cur = []
        cur.append((w, x['S'], x['E']))
        if w[-1] in ',.?!':
            out.append(cur); cur = []
    if cur: out.append(cur)
    for i in range(len(out) - 1):
        while len(out[i]) > 1 and out[i][-1][0].lower().strip(',.') in WEAK and L(out[i + 1]) + 1 + len(out[i][-1][0]) <= 23:
            out[i + 1].insert(0, out[i].pop())
    i = 0
    while i < len(out) - 1:
        if out[i][-1][2] - out[i][0][1] < 0.35 and out[i][-1][0][-1] not in ',.?!' and L(out[i]) + 1 + L(out[i + 1]) <= 22:
            out[i] = out[i] + out.pop(i + 1)
        else: i += 1
    res = []
    for i, c in enumerate(out):
        s = c[0][1]; e = out[i + 1][0][1] if i + 1 < len(out) else c[-1][2] + 0.5
        res.append({'s': s, 'e': e, 'w': c})
    return res

def cap_img(ch):
    toks = [w.upper().rstrip(',.') for w, _, _ in ch['w']]; raw = [w.upper() for w, _, _ in ch['w']]
    sz = 48
    while sz > 36 and tl(' '.join(toks), F(900, sz)) > 860: sz -= 2
    f = F(900, sz); sp = tl(' ', f); ws = [tl(x, f) for x in toks]
    w = int(sum(ws) + sp * (len(toks) - 1)) + 56; h = 74
    im, p = glow_box(w, h, r=16, fill=(10, 20, 36, 205), gw=6, border=2)
    x = p + 28
    for tok, r_, tw in zip(toks, raw, ws):
        col = AMBER if (r_ in KEY or tok in KEY) else WHITE
        tglow(im, (x, p + h // 2 + 2), tok, f, col, 'lm', glow=(60, 140, 255) if col == WHITE else (255, 150, 0), rad=4)
        x += tw + sp
    return im, p

# ---------------- linha do tempo ----------------
# (início, fim, z_ini, z_fim, tx, ty) — tx/ty: onde o centro do rosto fica na tela
SEGS = [
    (0.000, 1.480, 1.02, 1.18, 540, 640), (1.480, 3.352, 1.24, 1.30, 540, 620),
    (3.352, 4.604, 1.16, 1.20, 540, 640),
    (4.604, 6.600, 1.08, 1.10, 610, 760), (6.600, 9.380, 1.08, 1.11, 470, 760),
    (9.380, 10.950, 1.10, 1.12, 610, 760), (10.950, 14.167, 1.00, 1.03, 540, 770),
    (14.167, 15.700, 1.22, 1.26, 540, 640), (15.700, 16.880, 1.34, 1.38, 540, 610),
    (16.880, 18.949, 1.06, 1.09, 640, 700),
    (18.949, 20.500, 1.18, 1.22, 540, 640), (20.500, 23.350, 1.05, 1.06, 485, 770),
    (23.350, 26.700, 1.05, 1.07, 490, 770),
    (26.700, 28.620, 1.06, 1.08, 520, 735), (28.620, 30.870, 1.00, 1.02, 560, 760),
    (30.870, 33.800, 1.03, 1.08, 530, 730)]
PUNCH = [(1.50, 0.06), (15.74, 0.05), (24.880, 0.0), (27.350, 0.0), (31.520, 0.0)]
WHIPS = [4.604, 14.167, 26.700]

def ease(x): return 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, x)))

def cam_at(t):
    for a, b, z0, z1, tx, ty in SEGS:
        if a <= t < b:
            z = z0 + (z1 - z0) * ease((t - a) / (b - a)); break
    else:
        a, b, z0, z1, tx, ty = SEGS[-1]; z = z1
    for tp, add in PUNCH:
        if tp <= t < tp + 1.0:
            z += add * min(1, (t - tp) / 0.12)
    return z, tx, ty

def cam_frame(i, face):
    t = i / FPS
    n = len(face); cx, cy, fw = face[min(i, n - 1)]
    z, tx, ty = cam_at(t)
    x0 = min(max(0, cx - tx / z), W - W / z); y0 = min(max(0, cy - ty / z), H - H / z)
    return z, x0, y0, cx, cy, fw

def face_box(i, face):
    """Retângulo do rosto na tela (testa ao queixo), já com zoom."""
    z, x0, y0, cx, cy, fw = cam_frame(i, face)
    l = (cx - 0.42 * fw - x0) * z; r = (cx + 0.42 * fw - x0) * z
    top = (cy - 0.55 * fw - y0) * z; chin = (cy + 0.63 * fw - y0) * z
    return l, top, r, chin

def sc(ip, f):
    img, pad = ip
    return img.resize((int(img.width * f), int(img.height * f)), Image.LANCZOS), int(pad * f)

CAP_Y, BADGE_Y, UNDER_CHIN_Y = 1072, 1345, 948
LX, RX = 62, 1080 - 62 - 232   # colunas laterais

FACE = None

def build_events(words):
    ev = []
    def add(img, t0, t1, x, y, anim='pop', name=''):
        ev.append(dict(img=img, t0=t0, t1=t1, x=x, y=y, anim=anim, name=name))
    add(el_badge(), 4.55, 99, 'c', BADGE_Y, 'fade', 'badge')
    add(el_hook(), 0.0, 4.55, 'c', 1225, 'none', 'hook')
    # doenças (laterais, alternando)
    add(el_side('🦴', 'COLUNA', 'quem carrega peso'), 5.10, 6.55, LX, 330, 'slideL', 'c1')
    add(el_side('✋', 'TENDINITE', 'esforço repetitivo'), 6.60, 9.35, RX, 330, 'slideR', 'c2')
    add(el_side('👂', 'AUDIÇÃO', 'perda por barulho'), 9.40, 10.92, LX, 330, 'slideL', 'c3')
    add(el_side('🧠', 'BURNOUT', 'excesso de cobrança'), 10.95, 12.90, LX, 330, 'slideL', 'c4')
    add(el_side('⚠️', 'ASSÉDIO', 'no trabalho'), 12.92, 14.15, LX, 330, 'slideL', 'c5')
    add(el_stat(), 10.98, 14.15, RX, 300, 'slideR', 'stat')
    # número sob o queixo
    add(el_stat('742 MIL', ('acidentes de', 'trabalho no Brasil', 'em 2024'), 'Fonte: SmartLab/MPT'), 17.00, 18.94, LX, 300, 'slideL', 'num')
    # direitos (laterais)
    add(el_side('💰', 'RENDA', 'no afastamento', col=AMBER), 20.50, 26.670, LX, 470, 'slideL', 'r1')
    add(el_side('🏦', 'FGTS', 'do tempo afastado', col=AMBER), 21.65, 26.670, RX, 470, 'slideR', 'r2')
    add(el_side('🛡️', '12 MESES', 'de garantia no emprego', col=AMBER), 23.35, 26.670, LX, 700, 'slideL', 'r3')
    add(el_side('⚖️', 'INDENIZAÇÃO', 'paga pela empresa', col=AMBER), 24.95, 26.670, RX, 700, 'slideR', 'r4')
    # chamada final sob o queixo
    add(el_line('💬', 'CHAME NO WHATSAPP', 'Conte o que aconteceu · Jackson Bueno Advogados', col=WHITE,
                fill=(8, 70, 45, 238), glow=GREEN), 27.320, 99, 'c', 1205, 'pop', 'cta')
    for c in chunks(words, 4.55):
        i0, i1 = int(c['s'] * FPS), int(c['e'] * FPS) + 1
        chin = max(face_box(i, FACE)[3] for i in range(i0, min(i1, len(FACE))))
        lim = 1205 - 92 if c['s'] >= 27.3 else BADGE_Y - 96
        y = int(min(max(CAP_Y, chin + 34), lim))
        add(('cap', c), c['s'], c['e'], 'c', y, 'cap', 'cap')
    return ev

def place(frame, img, pad, x, y, alpha=1.0, dx=0, scale=1.0):
    W0, H0 = img.width, img.height
    if x == 'c': bx = (W - W0) // 2
    else: bx = int(x) - pad
    by = int(y) - pad
    if scale != 1.0:
        img = img.resize((max(1, int(W0 * scale)), max(1, int(H0 * scale))), Image.BILINEAR)
        bx += (W0 - img.width) // 2; by += (H0 - img.height) // 2
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]; x0 = bx + dx; y0 = by
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya: return
    sub = a[ya - y0:yb - y0, xa - x0:xb - x0]
    al = sub[..., 3:4] / 255.0 * alpha
    reg = frame[ya:yb, xa:xb].astype(np.float32)
    frame[ya:yb, xa:xb] = (reg * (1 - al) + sub[..., :3] * al).astype(np.uint8)

def anim(e, t):
    d = t - e['t0']; r = e['t1'] - t
    if e['anim'] == 'none': return 1.0, 0, 1.0
    alpha = min(1, d / 0.12, max(0, r) / 0.12)
    dx, scale = 0, 1.0
    if e['anim'] == 'pop' and d < 0.22:
        k = d / 0.22; scale = 0.84 + 0.16 * (1 - (1 - k) ** 3) + 0.04 * math.sin(math.pi * k)
    if e['anim'] in ('slideL', 'slideR') and d < 0.24:
        k = 1 - (1 - d / 0.24) ** 3; dx = int((-1 if e['anim'] == 'slideL' else 1) * 160 * (1 - k))
    if e['anim'] == 'cap':
        alpha = min(1, d / 0.05 + 0.4); scale = 0.94 + 0.06 * min(1, d / 0.1)
    return max(0, min(1, alpha)), dx, scale

GRADE = ('eq=brightness=0.015:contrast=1.07:saturation=1.10:gamma=1.02,'
         'colorbalance=rs=0.05:gs=0.01:bs=-0.05:rm=0.04:gm=0.01:bm=-0.04:rh=0.02:bh=-0.02,vignette=PI/5')

def main():
    args = sys.argv[1:]
    prev = None; out = 'final.mp4'
    if '--preview' in args: prev = [float(x) for x in args[args.index('--preview') + 1].split(',')]
    if '--out' in args: out = args[args.index('--out') + 1]
    global FACE
    words = json.load(open('words2.json')); face = np.load('face.npy'); FACE = face
    events = build_events(words); cache = {}
    dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', BASE, '-vf', GRADE, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = None
    if not prev:
        enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                                '-i', '-', '-i', 'mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast',
                                '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                                '-shortest', out], stdin=subprocess.PIPE)
    n = len(face); i = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        t = i / FPS
        if prev and not any(abs(t - p) < 0.5 / FPS for p in prev): i += 1; continue
        src = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        cx, cy, _ = face[min(i, n - 1)]
        z, tx, ty = cam_at(t)
        cw, chh = W / z, H / z
        x0 = min(max(0, cx - tx / z), W - cw); y0 = min(max(0, cy - ty / z), H - chh)
        fr = cv2.warpAffine(src, np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]]), (W, H), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REFLECT)
        for b in WHIPS:
            if abs(t - b) < 0.1:
                dd = 1 - abs(t - b) / 0.1; L = int(80 * dd) * 2 + 1
                k = np.full((1, L), 1 / L, np.float32); fr = cv2.filter2D(fr, -1, k)
                sh = int(150 * dd) * (1 if t < b else -1)
                fr = cv2.warpAffine(fr, np.float32([[1, 0, sh], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        fr = np.ascontiguousarray(fr)
        for e in events:
            if not (e['t0'] <= t < e['t1']): continue
            a, dx, s = anim(e, t)
            if e['name'] == 'cap':
                key = id(e)
                if key not in cache: cache[key] = cap_img(e['img'][1])
                img, pad = cache[key]
            else:
                img, pad = e['img']
            place(fr, img, pad, e['x'], e['y'], a, dx, s)
        if prev: Image.fromarray(fr).save(f'prev_{t:05.2f}.jpg', quality=90)
        else: enc.stdin.write(fr.tobytes())
        i += 1
    if enc: enc.stdin.close(); enc.wait()
    dec.stdout.close(); dec.wait()
    print('quadros', i)

if __name__ == '__main__':
    main()
