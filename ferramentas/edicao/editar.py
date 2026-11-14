#!/usr/bin/env python3
"""
Edição ilustrada dos vídeos gravados pelo Dr. Jackson Bueno (Reels/TikTok 1080x1920).
Segue o guia ferramentas/edicao/SKILL.md (skill "edicao-ilustrada-jackson-bueno").

USO
    python3 ferramentas/edicao/editar.py videos/AAAA-MM-DD-tema                 # render final -> final.mp4
    python3 ferramentas/edicao/editar.py videos/AAAA-MM-DD-tema --preview 0.5,3,12.4   # quadros em conf/prev_*.jpg
    python3 ferramentas/edicao/editar.py videos/AAAA-MM-DD-tema --antes-depois 47,77,140  # retoque lado a lado (tempos da fonte)
    python3 ferramentas/edicao/editar.py videos/AAAA-MM-DD-tema --capa            # capa.jpg

ENTRADA (na pasta): bruto.mp4 (1080x1920), transcricao_vad.json (faster-whisper com tempos por palavra), plano.json:
  velocidade        1.0–1.2 (acelera vídeo e voz sem mudar o tom)
  congelar_final    segundos de quadro parado no fim (com a chamada)
  cortes            [[ini, fim], ...] em segundos da fonte (ordem de exibição)
  zooms             [{z0, z1}] um por corte (zoom no início e no fim do corte; push-in lento quando z1 > z0)
  punch             tempos da fonte com punch-in rápido (+8% em 0,15 s)
  palavras_chave    palavras que ficam âmbar na legenda quando ditas
  correcoes         {"errado": "certo"} aplicado à transcrição
  eventos           [{tipo, t, fim, ...}] tempos da fonte. tipos:
                    pill {texto, emoji}           etiqueta no topo
                    gancho {linhas, emoji}        pergunta grande (as legendas somem enquanto ele aparece)
                    texto {texto, emoji, cor}     palavra em destaque (âmbar sobre faixa escura; cor "vermelho")
                    lei {texto}                   cartão discreto com a base legal
                    checklist {titulo, itens:[{t, texto, emoji}]}
                    broll {clip, inicio}          vídeo de banco em tela cheia (voz continua)
                    virada {linhas, emoji}        frase da virada, grande
                    riser                         efeito sonoro que sobe e termina em t
                    cta                           site + link da bio + mandar pra alguém
  capa              {t, linhas, pill}
Retoque do rosto (SKILL.md 4.1): MediaPipe Face Landmarker (modelo em ~/.cache/edicao/face_landmarker.task ou
EDICAO_FACE_MODEL), suavização seletiva da pele com textura, olheiras, afinamento leve de bochecha/mandíbula, luz e cor.
"""
import os, sys, json, math, subprocess, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
STOCK = os.path.join(ROOT, "ferramentas", "reels", "stock")
W, H, FPS = 1080, 1920, 30
NAVY = (10, 20, 36); AMBER = (255, 186, 48); WHITE = (250, 250, 246); RED = (214, 58, 48); SOFT = (205, 212, 222)
MX = 150
SITE = "jacksonbueno.adv.br"; HANDLE = "@jacksonbueno.adv"

# ---------------- fontes e emoji ----------------
MS = os.path.join(ROOT, "ferramentas", "node_modules", "@fontsource", "montserrat", "files", "montserrat-latin-%d-normal.woff")
PP = "/usr/share/fonts/truetype/google-fonts/Poppins-%s.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
if not os.path.exists(MS % 800):
    subprocess.run(["npm", "i", "-s", "@fontsource/montserrat"], cwd=os.path.join(ROOT, "ferramentas"), check=True, stdout=subprocess.DEVNULL)
_fc = {}
def M(w, s):
    k = ("m", w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(MS % w, s)
    return _fc[k]
def P(w, s):
    k = ("p", w, s)
    if k not in _fc:
        try: _fc[k] = ImageFont.truetype(PP % w, s)
        except OSError: _fc[k] = M(600, s)
    return _fc[k]
_d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
def tl(text, f): return _d0.textlength(text, font=f)
def fit(text, wt, maxw, start, minimo=30):
    s = start
    while s > minimo and tl(text, M(wt, s)) > maxw: s -= 2
    return M(wt, s)
_em = {}
def emoji(ch, size):
    ch = (ch or "").replace("️", "")
    if not ch or not os.path.exists(EMOJI_FONT): return None
    k = (ch, size)
    if k not in _em:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((100, 100), ch, font=f, embedded_color=True, anchor="mm")
        bb = im.getbbox()
        if not bb: _em[k] = None; return None
        im = im.crop(bb); r = size / max(im.size)
        _em[k] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _em[k]

# ---------------- easing ----------------
def cl(x): return max(0.0, min(1.0, x))
def eo(t): t = cl(t); return 1 - (1 - t) ** 3
def eio(t): t = cl(t); return t * t * (3 - 2 * t)
def eb(t):
    t = cl(t); c1 = 2.0; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ======================================================================
#                           RETOQUE DO ROSTO
# ======================================================================
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
             172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
EYE_L = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
EYE_R = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]
BROW_L = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_R = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
LID_L = [133, 155, 154, 153, 145, 144, 163, 7, 33]
LID_R = [362, 382, 381, 380, 374, 373, 390, 249, 263]
NOSTRILS = [98, 97, 2, 326, 327, 294, 278, 344, 440, 275, 4, 45, 220, 115, 48, 64]
# contorno que afina (índice, peso): parte de baixo das bochechas e mandíbula; nada na altura dos óculos
SLIM = [(132, 0.55), (58, 0.85), (172, 1.0), (136, 1.0), (150, 0.8), (149, 0.55), (176, 0.3),
        (361, 0.55), (288, 0.85), (397, 1.0), (365, 1.0), (379, 0.8), (378, 0.55), (400, 0.3)]

class Retocador:
    def __init__(self, forca=1.0):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        self.mp = mp
        model = os.environ.get("EDICAO_FACE_MODEL") or os.path.expanduser("~/.cache/edicao/face_landmarker.task")
        if not os.path.exists(model):
            os.makedirs(os.path.dirname(model), exist_ok=True)
            for url in ["https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                        "https://huggingface.co/Skulleton12/mediapipe-face-landmarker/resolve/main/face_landmarker.task"]:
                subprocess.run(["curl", "-sSL", "--fail", "-o", model, url])
                if os.path.exists(model) and os.path.getsize(model) > 1_000_000: break
        opt = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=model),
                                           running_mode=vision.RunningMode.VIDEO, num_faces=1,
                                           min_face_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.lm = vision.FaceLandmarker.create_from_options(opt)
        self.ts = 0; self.prev = None; self.forca = forca

    def reset(self): self.prev = None

    def pontos(self, bgr):
        small = cv2.resize(bgr, (bgr.shape[1] // 2, bgr.shape[0] // 2), interpolation=cv2.INTER_AREA)
        self.ts += 33
        r = self.lm.detect_for_video(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB)), self.ts)
        if not r.face_landmarks: self.prev = None; return None
        p = np.array([[q.x * bgr.shape[1], q.y * bgr.shape[0]] for q in r.face_landmarks[0]], np.float32)
        if self.prev is not None:
            mov = np.median(np.linalg.norm(p - self.prev, axis=1))
            a = 0.35 if mov < 3 else (0.6 if mov < 10 else 1.0)   # suaviza tremor; acompanha movimento real
            p = self.prev + a * (p - self.prev)
        self.prev = p
        return p

    def aplicar(self, bgr, p=None):
        if p is None: p = self.pontos(bgr)
        if p is None: return bgr, None
        return retocar(bgr, p, self.forca), p

def _poly(mask, pts, val=255):
    cv2.fillPoly(mask, [np.round(pts).astype(np.int32)], val, lineType=cv2.LINE_AA)

def retocar(img, p, forca=1.0):
    fw = float(np.linalg.norm(p[234] - p[454]))
    if fw < 60: return img
    oval = p[FACE_OVAL]
    x0, y0 = oval.min(0) - fw * 0.28; x1, y1 = oval.max(0) + fw * 0.28
    x0, y0 = int(max(0, x0)), int(max(0, y0)); x1, y1 = int(min(img.shape[1], x1)), int(min(img.shape[0], y1))
    if x1 - x0 < 40 or y1 - y0 < 40: return img
    crop = img[y0:y1, x0:x1].astype(np.float32); q = p - np.array([x0, y0], np.float32)
    h, w = crop.shape[:2]

    # 1) afinamento leve (deformação local suave, máx. ~2,5% da largura do rosto)
    X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    dx = np.zeros_like(X); dy = np.zeros_like(Y)
    cen = q[[1, 152, 168]].mean(0)
    r = fw * 0.20; r2 = r * r
    for idx, wt in SLIM:
        c = q[idx]; v = cen - c; v = v / (np.linalg.norm(v) + 1e-6) * fw * 0.024 * wt * forca
        d2 = (X - c[0]) ** 2 + (Y - c[1]) ** 2
        inside = d2 < r2
        f = np.where(inside, (1 - d2 / r2) ** 2, 0)                 # queda suave até a borda do círculo
        dx -= f * v[0]; dy -= f * v[1]
    crop = cv2.remap(crop, X + dx, Y + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    # máscaras
    def m_of(groups, dil=0):
        m = np.zeros((h, w), np.uint8)
        for g in groups: _poly(m, q[g])
        if dil: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dil, dil)))
        return m
    k = int(fw * 0.07) | 1
    pele = m_of([FACE_OVAL]).astype(np.float32)
    tira = np.maximum.reduce([m_of([EYE_L, EYE_R], k), m_of([BROW_L, BROW_R], k // 2 | 1), m_of([LIPS], k // 2 | 1), m_of([NOSTRILS], 3)])
    pele = np.clip(pele - tira, 0, 255)
    pele = cv2.erode(pele, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k // 2 | 1, k // 2 | 1)))
    pele = cv2.GaussianBlur(pele, (0, 0), fw * 0.02) / 255.0

    # 2) pele: suaviza linhas finas e manchas, devolve parte da textura (poros)
    c8 = np.clip(crop, 0, 255).astype(np.uint8)
    bil = cv2.bilateralFilter(c8, d=0, sigmaColor=26, sigmaSpace=max(3, fw * 0.022)).astype(np.float32)
    bil = cv2.bilateralFilter(np.clip(bil, 0, 255).astype(np.uint8), d=0, sigmaColor=18, sigmaSpace=max(3, fw * 0.015)).astype(np.float32)
    det = crop - cv2.GaussianBlur(crop, (0, 0), 0.9)
    lisa = bil + det * 0.55
    a = (0.72 * forca) * pele[..., None]
    crop = crop * (1 - a) + lisa * a

    # 3) olheiras: clareia e neutraliza a cor escura sob os olhos
    lab = cv2.cvtColor(np.clip(crop, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    om = np.zeros((h, w), np.float32)
    for lid, outer, inner in ((LID_L, 33, 133), (LID_R, 263, 362)):
        lidp = q[lid]; ew = float(np.linalg.norm(q[outer] - q[inner]))
        low = lidp + np.array([0, ew * 0.42], np.float32)
        low[0] += np.array([0, -ew * 0.15]); low[-1] += np.array([0, -ew * 0.15])
        m = np.zeros((h, w), np.uint8); _poly(m, np.vstack([lidp + np.array([0, ew * 0.06]), low[::-1]]))
        om = np.maximum(om, m.astype(np.float32))
    om = cv2.GaussianBlur(om, (0, 0), fw * 0.03) / 255.0 * (1 - cv2.GaussianBlur(tira.astype(np.float32), (0, 0), 2) / 255.0)
    refp = q[[205, 425, 50, 280]].astype(int)
    refs = [lab[max(0, y - 6):y + 6, max(0, x - 6):x + 6].reshape(-1, 3) for x, y in refp if 0 <= x < w and 0 <= y < h]
    if refs:
        ref = np.median(np.vstack(refs), axis=0)
        Lb = cv2.GaussianBlur(lab[..., 0], (0, 0), 4)
        lift = np.clip(ref[0] - Lb, 0, 40) * 0.42 * forca
        lab[..., 0] += lift * om
        for ch in (1, 2): lab[..., ch] += (ref[ch] - lab[..., ch]) * 0.3 * forca * om
    # 4) luz e cor do rosto: um pouco mais de luz, tom levemente quente
    lm = cv2.GaussianBlur(m_of([FACE_OVAL]).astype(np.float32), (0, 0), fw * 0.06) / 255.0
    lab[..., 0] += (lab[..., 0] * 0.035 + 2.5) * lm * forca
    lab[..., 2] += 1.6 * lm * forca
    # brilho dos olhos
    em = cv2.GaussianBlur(m_of([EYE_L, EYE_R]).astype(np.float32), (0, 0), 2) / 255.0
    Lm = lab[..., 0]; lab[..., 0] = Lm + ((Lm - 128) * 0.08 + 3) * em * forca
    crop = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

    out = img.copy(); out[y0:y1, x0:x1] = crop
    return out

# ======================================================================
#                               PLANO
# ======================================================================
class Plano:
    def __init__(self, pasta):
        self.pasta = pasta
        self.p = json.load(open(os.path.join(pasta, "plano.json")))
        self.src = os.path.join(pasta, self.p.get("fonte", "bruto.mp4"))
        self.spd = float(self.p.get("velocidade", 1.0))
        self.cuts = [tuple(c) for c in self.p["cortes"]]
        self.cum = [0.0]
        for a, b in self.cuts: self.cum.append(self.cum[-1] + (b - a) / self.spd)
        self.TV = self.cum[-1]; self.T = self.TV + float(self.p.get("congelar_final", 0))
        self.N = int(round(self.T * FPS))
        self.ev = []
        for e in self.p["eventos"]:
            e = dict(e); e["o"] = self.s2o(e["t"]); e["of"] = self.s2o(e["fim"]) if "fim" in e else e["o"]
            if e.get("fim", 0) >= 999: e["of"] = self.T + 1
            if e["tipo"] == "checklist":
                for it in e["itens"]: it["o"] = self.s2o(it["t"])
            self.ev.append(e)
        self.palavras = self._palavras()
        self.chunks = self._chunks()
        kws = set(w.lower().strip(".,?!:;") for w in self.p.get("palavras_chave", []))
        self.kw = kws
        self.punch = [self.s2o(t) for t in self.p.get("punch", [])]

    def s2o(self, t):
        for k, (a, b) in enumerate(self.cuts):
            if t < a: return self.cum[k]
            if t <= b: return self.cum[k] + (t - a) / self.spd
        return self.TV
    def o2s(self, o):
        for k, (a, b) in enumerate(self.cuts):
            if o < self.cum[k + 1] or k == len(self.cuts) - 1:
                return k, min(b, a + (o - self.cum[k]) * self.spd)
        return len(self.cuts) - 1, self.cuts[-1][1]

    def _palavras(self):
        tr = json.load(open(os.path.join(self.pasta, self.p.get("transcricao", "transcricao_vad.json"))))
        cor = self.p.get("correcoes", {})
        out = []
        for seg in tr:
            for w in seg["words"]:
                mid = (w["s"] + w["e"]) / 2
                if not any(a <= mid <= b for a, b in self.cuts): continue
                txt = w["w"].strip()
                for k, v in cor.items(): txt = txt.replace(k, v)
                s = self.s2o(max(w["s"], next(a for a, b in self.cuts if a <= mid <= b)))
                e = self.s2o(min(w["e"], next(b for a, b in self.cuts if a <= mid <= b)))
                out.append([txt, s, e])
        return out

    def _chunks(self):
        out, cur = [], []
        for i, w in enumerate(self.palavras):
            cur.append(w)
            nxt = self.palavras[i + 1] if i + 1 < len(self.palavras) else None
            n = len(cur); chars = sum(len(x[0]) for x in cur)
            if (w[0][-1] in ".,:?!" or n >= 4 or (n >= 3 and chars > 14) or nxt is None or nxt[1] - w[2] > 0.25):
                out.append(cur); cur = []
        if cur: out.append(cur)
        return out

    def ativos(self, o, tipo=None):
        return [e for e in self.ev if (tipo is None or e["tipo"] == tipo) and e["o"] <= o < e["of"]]

# ======================================================================
#                          LEITURA DE QUADROS
# ======================================================================
def ler_trecho(src, a, b):
    """gerador (t_fonte, quadro BGR) do trecho [a, b] do vídeo, na resolução 1080x1920"""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", src, "-t", f"{b - a + 0.2:.3f}", "-f", "rawvideo", "-pix_fmt", "bgr24",
           "-vf", f"scale={W}:{H}", "-"]
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    j = 0
    while True:
        buf = pr.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        yield a + j / FPS, np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        j += 1
    pr.stdout.close(); pr.wait()

def quadro_em(src, t):
    cmd = ["ffmpeg", "-v", "quiet", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-vf", f"scale={W}:{H}", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw[:W * H * 3], np.uint8).reshape(H, W, 3).copy() if len(raw) >= W * H * 3 else None

_broll = {}
def broll_frames(clip, inicio, dur):
    k = (clip, inicio)
    if k not in _broll:
        cmd = ["ffmpeg", "-v", "error", "-ss", str(inicio), "-i", os.path.join(STOCK, clip + ".mp4"), "-t", f"{dur + 0.3:.2f}",
               "-vf", f"fps=30,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},unsharp=5:5:0.5,eq=contrast=1.05:saturation=1.05",
               "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        n = len(raw) // (W * H * 3)
        _broll[k] = [np.frombuffer(raw[i * W * H * 3:(i + 1) * W * H * 3], np.uint8).reshape(H, W, 3) for i in range(n)]
    return _broll[k]

# ======================================================================
#                          ZOOM E ENQUADRAMENTO
# ======================================================================
def centros_rosto(pl, ret):
    """centro do rosto (mediana) de cada corte, para o zoom ficar centrado sem tremer"""
    out = []
    for a, b in pl.cuts:
        pts = []
        for t in np.linspace(a + 0.1, b - 0.1, 4):
            f = quadro_em(pl.src, float(t))
            if f is None: continue
            small = cv2.resize(f, (W // 2, H // 2))
            ret.ts += 1000
            r = ret.lm.detect_for_video(ret.mp.Image(image_format=ret.mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB)), ret.ts)
            if r.face_landmarks:
                p = np.array([[q.x * W, q.y * H] for q in r.face_landmarks[0]])
                pts.append(p[FACE_OVAL].mean(0))
        out.append(np.median(pts, 0) if pts else np.array([W / 2, H * 0.32]))
    ret.reset()
    return out

def zoom_em(pl, k, o):
    z = pl.p["zooms"][k] if k < len(pl.p.get("zooms", [])) else {"z0": 1.0, "z1": 1.0}
    a, b = pl.cum[k], pl.cum[k + 1]
    zz = z["z0"] + (z["z1"] - z["z0"]) * eio((o - a) / max(0.01, b - a))
    for pt in pl.punch:
        d = o - pt
        if 0 <= d < 0.15: zz *= 1 + 0.08 * eo(d / 0.15)
        elif 0.15 <= d < 0.75: zz *= 1.08
        elif 0.75 <= d < 1.1: zz *= 1 + 0.08 * (1 - eio((d - 0.75) / 0.35))
    return zz

def enquadrar(img, z, centro):
    if z <= 1.001: return img
    cw, ch = W / z, H / z
    cx = min(max(centro[0], cw / 2), W - cw / 2)
    cy = centro[1] - 0.34 * H / z + ch / 2           # rosto fica a ~34% da altura
    cy = min(max(cy, ch / 2), H - ch / 2)
    M_ = np.array([[z, 0, -(cx - cw / 2) * z], [0, z, -(cy - ch / 2) * z]], np.float32)
    return cv2.warpAffine(img, M_, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# ======================================================================
#                              GRÁFICOS
# ======================================================================
def faixa(d, box, fill, r=26): d.rounded_rectangle(box, r, fill=fill)

def g_pill(lay, d, e, o):
    k = eo((o - e["o"]) / 0.25); out = cl((e["of"] - o) / 0.2)
    if k <= 0 or out <= 0: return
    a = int(255 * min(k, out))
    f = fit(e["texto"], 900, W - 2 * MX - 90, 36, 24); h = 78
    em = emoji(e.get("emoji"), 50); ew = em.width + 14 if em else 0
    pw = tl(e["texto"], f) + ew + 56; x = W / 2 - pw / 2; y = 250 - (1 - k) * 30
    sub = Image.new("RGBA", (int(pw) + 4, h + 4), (0, 0, 0, 0)); sd = ImageDraw.Draw(sub)
    sd.rounded_rectangle((0, 0, pw, h), h // 2, fill=AMBER + (255,))
    if em: sub.paste(em, (28, h // 2 - em.height // 2), em)
    sd.text((28 + ew, h / 2 + 1), e["texto"], font=f, fill=NAVY, anchor="lm")
    if a < 255: sub.putalpha(sub.split()[3].point(lambda v: v * a // 255))
    lay.alpha_composite(sub, (int(x), int(y)))

def bloco_texto(linhas, cores, tam, emj=None, maxw=W - 2 * MX, banda=NAVY + (225,), gap=14):
    """imagem RGBA com linhas sobre faixas escuras (cada linha uma faixa)"""
    fs = [fit(l, 900, maxw - 60 - (110 if (emj and i == 0) else 0), tam, 40) for i, l in enumerate(linhas)]
    fs = [min(fs, key=lambda f: f.size)] * len(linhas) if len(linhas) > 1 else fs
    sz = fs[0].size; lh = int(sz * 1.22)
    em = emoji(emj, int(sz * 1.05)) if emj else None
    ws = [tl(l, fs[i]) + 60 + ((em.width + 18) if (em and i == len(linhas) - 1) else 0) for i, l in enumerate(linhas)]
    BW = int(max(ws)) + 10; BH = len(linhas) * (lh + gap)
    img = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, l in enumerate(linhas):
        y = i * (lh + gap); x = (BW - ws[i]) / 2
        bfill = banda if not isinstance(banda, list) else banda[i]
        d.rounded_rectangle((x, y, x + ws[i], y + lh), 22, fill=bfill)
        d.text((x + 30, y + lh / 2 + 2), l, font=fs[i], fill=cores[i], anchor="lm")
        if em and i == len(linhas) - 1:
            img.paste(em, (int(x + 30 + tl(l, fs[i]) + 18), int(y + lh / 2 - em.height / 2)), em)
    return img

_cache_blk = {}
def blk(key, fn):
    if key not in _cache_blk: _cache_blk[key] = fn()
    return _cache_blk[key]

def colar(lay, img, cx, cy, escala=1.0, alpha=1.0):
    if alpha <= 0.01 or escala <= 0.01: return
    if abs(escala - 1) > 0.01:
        img = img.resize((max(1, int(img.width * escala)), max(1, int(img.height * escala))), Image.BILINEAR)
    if alpha < 0.99:
        img = img.copy(); img.putalpha(img.split()[3].point(lambda v: int(v * alpha)))
    lay.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def g_texto(lay, e, o):
    p = (o - e["o"]); out = cl((e["of"] - o) / 0.15)
    if p < 0 or out <= 0: return
    verm = e.get("cor") == "vermelho"
    img = blk(("t", e["texto"]), lambda: bloco_texto([e["texto"]], [WHITE if verm else AMBER], 92, e.get("emoji"),
                                                       banda=(RED + (240,)) if verm else NAVY + (228,)))
    colar(lay, img, W / 2, 1150, eb(p / 0.2), out)

def g_gancho(lay, e, o):
    p = o - e["o"]; out = cl((e["of"] - o) / 0.18)
    ls = e["linhas"]
    for i, l in enumerate(ls):
        pi = p - i * 0.12
        if pi < 0: continue
        img = blk(("g", i, l), lambda: bloco_texto([l], [AMBER if i == len(ls) - 1 else WHITE], 100,
                                                   e.get("emoji") if i == len(ls) - 1 else None))
        colar(lay, img, W / 2 + (1 - eo(pi / 0.25)) * 60, 1000 + i * 135, eb(pi / 0.22), out * cl(pi / 0.12))

def g_virada(lay, e, o):
    p = o - e["o"]; out = cl((e["of"] - o) / 0.15)
    if p < 0: return
    ls = e["linhas"]
    for i, l in enumerate(ls):
        pi = p - i * 0.15
        if pi < 0: continue
        img = blk(("v", i, l), lambda: bloco_texto([l], [WHITE if i == 0 else NAVY], 116, e.get("emoji") if i == len(ls) - 1 else None,
                                                   banda=NAVY + (230,) if i == 0 else AMBER + (255,)))
        colar(lay, img, W / 2, 1060 + i * 160, eb(pi / 0.22) * (1 + 0.04 * cl(p / 1.5)), out)

def g_lei(lay, e, o):
    k = eo((o - e["o"]) / 0.3); out = cl((e["of"] - o) / 0.2)
    if k <= 0 or out <= 0: return
    def mk():
        f = P("Medium", 30); em = emoji("⚖", 34); tw = tl(e["texto"], f) + 40 + em.width + 12
        im = Image.new("RGBA", (int(tw), 58), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, tw - 1, 57), 29, fill=NAVY + (215,), outline=AMBER + (200,), width=2)
        im.paste(em, (20, 29 - em.height // 2), em); d.text((20 + em.width + 12, 30), e["texto"], font=f, fill=SOFT, anchor="lm")
        return im
    img = blk(("l", e["texto"]), mk)
    colar(lay, img, W / 2, 1335 + (1 - k) * 20, 1.0, min(k, out))

def g_check(lay, e, o):
    p = o - e["o"]; out = cl((e["of"] - o) / 0.2)
    if p < 0 or out <= 0: return
    k = eo(p / 0.3); x0, x1 = MX - 40, W - MX + 40; y0 = 760; rowh = 92
    n = len(e["itens"]); y1 = y0 + 110 + n * rowh + 20
    pan = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0)); d = ImageDraw.Draw(pan)
    d.rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), 34, fill=NAVY + (226,), outline=AMBER + (230,), width=3)
    ft = fit(e["titulo"], 900, x1 - x0 - 70, 46)
    d.text(((x1 - x0) / 2, 62), e["titulo"], font=ft, fill=AMBER, anchor="mm")
    for i, it in enumerate(e["itens"]):
        pi = o - it["o"]; feito = pi >= 0
        y = 110 + i * rowh + rowh / 2; bx = 54
        d.rounded_rectangle((bx, y - 28, bx + 56, y + 28), 12, outline=(120, 134, 154), width=4)
        if feito:                                   # marca quando ele fala o item
            s = eb(pi / 0.2); bs = int(56 * s)
            d.rounded_rectangle((bx + 28 - bs / 2, y - bs / 2, bx + 28 + bs / 2, y + bs / 2), 12, fill=AMBER)
            if pi > 0.08: d.line([(bx + 14, y + 1), (bx + 25, y + 13), (bx + 44, y - 13)], fill=NAVY, width=8, joint="curve")
        em = emoji(it.get("emoji"), 54)
        tx = bx + 80
        if em:
            if not feito: em = em.copy(); em.putalpha(em.split()[3].point(lambda v: v * 2 // 5))
            pan.paste(em, (int(tx), int(y - em.height / 2)), em); tx += em.width + 18
        d.text((tx, y + 2), it["texto"], font=M(800, 56), fill=WHITE if feito else (120, 134, 154), anchor="lm")
    colar(lay, pan, W / 2, (y0 + y1) / 2 + (1 - k) * 40, 0.92 + 0.08 * k, min(k, out))

def g_cta(lay, e, o, T):
    p = o - e["o"]
    if p < 0: return
    def bloco():
        x0, x1 = MX - 50, W - MX + 50; h = 470
        im = Image.new("RGBA", (x1 - x0, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cw = x1 - x0
        d.rounded_rectangle((0, 0, cw - 1, h - 1), 36, fill=NAVY + (232,), outline=AMBER + (235,), width=3)
        em = emoji("💬", 46); t1 = "ME CONTA O SEU CASO"; f1 = fit(t1, 900, cw - 140, 44)
        w1 = tl(t1, f1) + em.width + 14; xx = cw / 2 - w1 / 2
        im.paste(em, (int(xx), 70 - em.height // 2), em); d.text((xx + em.width + 14, 72), t1, font=f1, fill=WHITE, anchor="lm")
        f2 = fit(SITE, 900, cw - 80, 64); d.text((cw / 2, 165), SITE, font=f2, fill=AMBER, anchor="mm")
        pb = "LINK NA BIO"; f3 = M(900, 40); em3 = emoji("👉", 44); pw = tl(pb, f3) + em3.width + 70
        d.rounded_rectangle((cw / 2 - pw / 2, 225, cw / 2 + pw / 2, 301), 38, fill=AMBER)
        im.paste(em3, (int(cw / 2 - pw / 2 + 26), 263 - em3.height // 2), em3)
        d.text((cw / 2 - pw / 2 + 26 + em3.width + 14, 265), pb, font=f3, fill=NAVY, anchor="lm")
        t4 = "MANDA PRA QUEM SE ACIDENTOU"; em4 = emoji("📲", 42); f4 = fit(t4, 800, cw - 150, 36)
        w4 = tl(t4, f4) + em4.width + 14; xx = cw / 2 - w4 / 2
        im.paste(em4, (int(xx), 375 - em4.height // 2), em4); d.text((xx + em4.width + 14, 377), t4, font=f4, fill=WHITE, anchor="lm")
        d.text((cw / 2, 435), "Dr. Jackson Bueno · OAB/MG 211.217", font=P("Medium", 26), fill=SOFT, anchor="mm")
        return im
    img = blk(("cta",), bloco)
    colar(lay, img, W / 2, 1080 + (1 - eo(p / 0.35)) * 60, eb(p / 0.3), cl(p / 0.15))

def g_legenda(lay, d, pl, o):
    if pl.ativos(o, "gancho") or pl.ativos(o, "cta"): return
    cur = None
    for c in pl.chunks:
        if c[0][1] <= o + 0.03: cur = c
    if cur is None: return
    nxt_i = pl.chunks.index(cur) + 1
    fim = pl.chunks[nxt_i][0][1] if nxt_i < len(pl.chunks) else cur[-1][2] + 0.6
    if o > min(fim, cur[-1][2] + 0.7): return
    words = [w[0] for w in cur]
    f = fit(" ".join(words), 800, W - 2 * MX + 60, 54)
    sp = tl(" ", f); ws = [tl(w, f) for w in words]; tw = sum(ws) + sp * (len(words) - 1)
    pop = eb((o - cur[0][1]) / 0.16); y = 1440 + (1 - pop) * 12; x = W / 2 - tw / 2
    for (w, s, e), wd in zip(cur, ws):
        kw = w.lower().strip(".,?!:;") in pl.kw
        cor = AMBER if (kw and s - 0.05 <= o) else WHITE
        d.text((x, y), w, font=f, fill=cor, anchor="lm", stroke_width=7, stroke_fill=NAVY)
        x += wd + sp

# ======================================================================
#                                 QUADRO
# ======================================================================
def compor(pl, o, base_bgr):
    """recebe o quadro já retocado e enquadrado (BGR) e devolve RGB com b-roll e gráficos"""
    img = base_bgr
    for e in pl.ativos(o, "broll"):
        fr = broll_frames(e["clip"], e.get("inicio", 0), e["of"] - e["o"])
        i = min(len(fr) - 1, int((o - e["o"]) * FPS))
        b = fr[i]; z = 1.07 - 0.07 * eo((o - e["o"]) / max(0.3, e["of"] - e["o"]))
        img = enquadrar(b, z, (W / 2, H * 0.34))
    if o > pl.TV:                       # congelado do fim: escurece um pouco por trás da chamada
        img = (img.astype(np.float32) * 0.62 + np.array(NAVY[::-1], np.float32) * 0.38).astype(np.uint8)
    rgb = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # leve escurecimento embaixo para as legendas lerem bem
    for e in pl.ativos(o):
        t = e["tipo"]
        if t == "pill": g_pill(lay, d, e, o)
        elif t == "gancho": g_gancho(lay, e, o)
        elif t == "texto": g_texto(lay, e, o)
        elif t == "virada": g_virada(lay, e, o)
        elif t == "lei": g_lei(lay, e, o)
        elif t == "checklist": g_check(lay, e, o)
        elif t == "cta": g_cta(lay, e, o, pl.T)
    g_legenda(lay, d, pl, o)
    rgb.alpha_composite(lay)
    return np.array(rgb.convert("RGB"))

# ======================================================================
#                                  ÁUDIO
# ======================================================================
SR = 44100
def wav(path, a):
    import wave
    a = np.clip(a, -1, 1); x = (a * 32767).astype(np.int16)
    if a.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())

def sfx_track(pl):
    T = pl.T; n = int((T + 1) * SR); out = np.zeros(n); rng = np.random.default_rng(7)
    def add(sig, t, g):
        s = int(t * SR)
        if s < 0: sig = sig[-s:]; s = 0
        e = min(n, s + len(sig)); out[s:e] += sig[:e - s] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def impacto():
        t = tt(0.9); return np.sin(2 * np.pi * (38 + 70 * np.exp(-t * 18)) * t) * np.exp(-t * 4.5) + rng.standard_normal(len(t)) * np.exp(-t * 30) * 0.25
    def pop():
        t = tt(0.09); return np.sin(2 * np.pi * (700 + 900 * t / 0.09) * t) * np.exp(-t * 45)
    def whoosh():
        t = tt(0.42); x = rng.standard_normal(len(t))
        y = np.convolve(x, np.ones(5) / 5, "same") - np.convolve(x, np.ones(48) / 48, "same")
        return y * np.sin(np.pi * t / 0.42) ** 2
    def ding():
        t = tt(0.6); return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * np.exp(-t * 7) * 0.6
    def riser():
        t = tt(1.0); x = rng.standard_normal(len(t))
        hp = x - np.convolve(x, np.ones(30) / 30, "same")
        return (hp * 0.5 + np.sin(2 * np.pi * (200 + 900 * t ** 2) * t) * 0.3) * (t / 1.0) ** 2
    lista = [(0.0, "impacto", 9)]
    for e in pl.ev:
        if e["tipo"] in ("texto", "lei") and e["tipo"] == "texto": lista.append((e["o"], "pop", 3))
        if e["tipo"] == "broll": lista.append((e["o"] - 0.25, "whoosh", 4))
        if e["tipo"] == "riser": lista.append((e["o"] - 1.0, "riser", 8))
        if e["tipo"] == "virada": lista.append((e["o"], "impacto_leve", 8))
        if e["tipo"] == "cta": lista.append((e["o"], "pop", 5))
        if e["tipo"] == "pill" and e["o"] > 1: lista.append((e["o"], "pop", 2))
        if e["tipo"] == "checklist":
            for it in e["itens"]: lista.append((it["o"], "ding", 3))
    lista.sort()
    ultimo = -9; usados = []
    for t, k, pri in lista:
        if pri < 8 and t - ultimo < 1.9: continue
        usados.append((t, k)); ultimo = t if k != "riser" else t + 1.0
        g = {"impacto": 0.55, "impacto_leve": 0.35, "pop": 0.16, "whoosh": 0.22, "ding": 0.13, "riser": 0.22}[k]
        sig = {"impacto": impacto, "impacto_leve": impacto, "pop": pop, "whoosh": whoosh, "ding": ding, "riser": riser}[k]()
        add(sig, t, g)
    return out[:int(T * SR)], usados

def trilha(pl, virada_o):
    """instrumental original: tenso (alerta) até a virada; depois firme e mais aberto ("você tem direito")"""
    T = pl.T; n = int(T * SR); t = np.arange(n) / SR; mus = np.zeros(n); rng = np.random.default_rng(3)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def add(sig, s):
        s = int(s * SR); e = min(n, s + len(sig))
        if 0 <= s < n: mus[s:e] += sig[:e - s]
    bpm = 98; beat = 60 / bpm; bar = beat * 4
    tenso = [[45, 48, 52], [41, 45, 48], [43, 47, 50], [40, 44, 47]]        # Am  F  G  E
    firme = [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]]        # C  G  Am  F
    for k, b0 in enumerate(np.arange(0, T, beat)):
        dep = b0 >= virada_o
        tt = np.arange(int(0.3 * SR)) / SR
        if k % 2 == 0 or dep:
            add(np.sin(2 * np.pi * (46 + 80 * np.exp(-tt * 32)) * tt) * np.exp(-tt * 10) * (0.9 if dep else 0.7), b0)
        if dep and k % 2 == 1:
            t2 = np.arange(int(0.16 * SR)) / SR; add(rng.standard_normal(len(t2)) * np.exp(-t2 * 28) * 0.18, b0)
        c = (firme if dep else tenso)[int(b0 / bar) % 4]
        t4 = np.arange(int(beat * 0.45 * SR)) / SR
        for h in (0, 0.5):
            add(np.tanh(2.2 * np.sin(2 * np.pi * note(c[0] - 12) * t4)) * 0.16 * np.exp(-t4 * 6), b0 + h * beat)
        if dep or k % 4 in (1, 3):
            for j, m in enumerate([c[0], c[2], c[1], c[2]] if dep else [c[0], c[1]]):
                ts = np.arange(int(0.2 * SR)) / SR
                add(np.sin(2 * np.pi * note(m + 24) * ts) * np.exp(-ts * 16) * 0.10, b0 + j * beat / (4 if dep else 2))
    for k, b0 in enumerate(np.arange(0, T, bar)):
        dep = b0 >= virada_o
        c = (firme if dep else tenso)[k % 4]; tt = np.arange(int((bar + 0.4) * SR)) / SR
        env = np.minimum(1, tt / 0.5) * np.minimum(1, np.maximum(0, (bar + 0.4 - tt) / 0.5))
        add(sum(np.sin(2 * np.pi * note(m + 12) * tt) + 0.3 * np.sin(2 * np.pi * note(m + 12) * 2.003 * tt) for m in c) * env * 0.05, b0)
    mus *= np.minimum(1, t / 0.4) * np.minimum(1, (T - t) / 1.2)
    mus *= 1 + 0.25 * cl(1) * ((t >= virada_o) & (t < virada_o + 4))       # sobe um pouco na virada
    return mus / (np.abs(mus).max() + 1e-9) * 0.8

def montar_audio(pl, wd):
    # voz: cortes com micro-fades, acelerada sem mudar o tom, tratada
    parts = []; fl = []
    for i, (a, b) in enumerate(pl.cuts):
        d = b - a
        fl.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d - 0.015:.3f}:d=0.015[a{i}]")
        parts.append(f"[a{i}]")
    fl.append("".join(parts) + f"concat=n={len(parts)}:v=0:a=1,atempo={pl.spd},highpass=f=80,afftdn=nf=-28,"
              f"equalizer=f=3200:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,"
              f"loudnorm=I=-15:TP=-2:LRA=9,aresample={SR},apad=whole_dur={pl.T:.3f}[v]")
    voz = os.path.join(wd, "voz.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pl.src, "-filter_complex", ";".join(fl), "-map", "[v]", "-ac", "2", "-ar", str(SR), voz], check=True)
    vir = [e["o"] for e in pl.ev if e["tipo"] == "virada"]
    wav(os.path.join(wd, "trilha.wav"), trilha(pl, vir[0] if vir else pl.T * 0.75))
    s, usados = sfx_track(pl); wav(os.path.join(wd, "sfx.wav"), s)
    final = os.path.join(wd, "audio_final.wav")
    fc = ("[0:a]asplit=2[v1][v2];"
          "[1:a]volume=-27dB[m];[m][v2]sidechaincompress=threshold=0.02:ratio=5:attack=15:release=450:makeup=1[md];"
          "[2:a]volume=-6dB[s];"
          "[v1][md][s]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.93:level=false[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voz, "-i", os.path.join(wd, "trilha.wav"), "-i", os.path.join(wd, "sfx.wav"),
                    "-filter_complex", fc, "-map", "[o]", "-t", f"{pl.T:.3f}", final], check=True)
    return final, usados

# ======================================================================
#                                RENDER
# ======================================================================
def render(pasta, so_tempos=None):
    pl = Plano(pasta); wd = os.path.join(pasta, "_trabalho"); os.makedirs(wd, exist_ok=True)
    ret = Retocador()
    centros = centros_rosto(pl, ret)
    if so_tempos:
        os.makedirs(os.path.join(pasta, "conf"), exist_ok=True)
        for o in so_tempos:
            k, ts = pl.o2s(o); f = quadro_em(pl.src, ts)
            ret.reset(); f2, _ = ret.aplicar(f)
            img = compor(pl, o, enquadrar(f2, zoom_em(pl, k, o), centros[k]))
            Image.fromarray(img).save(os.path.join(pasta, "conf", f"prev_{o:05.1f}.jpg"), quality=88)
        return
    audio, usados = montar_audio(pl, wd)
    print("efeitos sonoros:", [(round(t, 2), k) for t, k in usados])
    out = os.path.join(pasta, "final.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", out], stdin=subprocess.PIPE)
    i = 0; ultimo = None
    for k, (a, b) in enumerate(pl.cuts):
        ret.reset(); gen = ler_trecho(pl.src, a, b); cur_t, cur_f = next(gen)
        while i < pl.N and (i / FPS < pl.cum[k + 1] or k == len(pl.cuts) - 1):
            o = i / FPS
            if o >= pl.TV: break
            _, ts = pl.o2s(o)
            try:
                while cur_t + 0.5 / FPS < ts: cur_t, cur_f = next(gen)
            except StopIteration: pass
            f2, _ = ret.aplicar(cur_f)
            base = enquadrar(f2, zoom_em(pl, k, o), centros[k]); ultimo = (base, k)
            enc.stdin.write(compor(pl, o, base).tobytes()); i += 1
            if i % 150 == 0: print(f"  {i}/{pl.N} quadros", flush=True)
    while i < pl.N:                                  # final congelado com a chamada
        enc.stdin.write(compor(pl, i / FPS, ultimo[0]).tobytes()); i += 1
    enc.stdin.close(); enc.wait()
    print("ok:", out, f"{pl.T:.1f}s")

def antes_depois(pasta, tempos):
    pl = Plano(pasta); ret = Retocador(); os.makedirs(os.path.join(pasta, "conf"), exist_ok=True)
    for t in tempos:
        f = quadro_em(pl.src, t); ret.reset(); g, p = ret.aplicar(f)
        if p is None: print("sem rosto em", t); continue
        x0, y0 = (p.min(0) - 120).astype(int).clip(0); x1, y1 = (p.max(0) + 120).astype(int)
        a = f[y0:y1, x0:x1]; b = g[y0:y1, x0:x1]
        lado = np.hstack([a, np.full((a.shape[0], 8, 3), 255, np.uint8), b])
        s = 900 / lado.shape[0]; lado = cv2.resize(lado, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(os.path.join(pasta, "conf", f"antes_depois_{t:.1f}.jpg"), lado, [cv2.IMWRITE_JPEG_QUALITY, 92])

def capa(pasta):
    pl = Plano(pasta); c = pl.p["capa"]; ret = Retocador()
    f = quadro_em(pl.src, c["t"]); ret.reset(); g, p = ret.aplicar(f)
    cen = p[FACE_OVAL].mean(0) if p is not None else (W / 2, H * 0.3)
    z = 1.32; cw, ch = W / z, H / z
    cx = min(max(cen[0], cw / 2), W - cw / 2); cy = min(max(cen[1] - 0.30 * H / z + ch / 2, ch / 2), H - ch / 2)
    M_ = np.array([[z, 0, -(cx - cw / 2) * z], [0, z, -(cy - ch / 2) * z]], np.float32)
    g = cv2.warpAffine(g, M_, (W, H), flags=cv2.INTER_CUBIC)
    img = Image.fromarray(cv2.cvtColor(g, cv2.COLOR_BGR2RGB)).convert("RGBA")
    # degradê azul-marinho na parte de baixo
    ramp = np.clip((np.arange(H) - 860) / 520, 0, 1) ** 1.2
    al = Image.fromarray(np.repeat((ramp * 240).astype(np.uint8)[:, None], W, 1))
    img = Image.composite(Image.new("RGBA", (W, H), NAVY + (255,)), img, al)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # selo no topo (dentro do recorte 3:4: y 240–1680)
    g_pill(lay, d, {"texto": c.get("pill", "ACIDENTE DE TRABALHO"), "emoji": "📄", "o": -9, "of": 9}, 1.0)
    ls = c["linhas"]; f = min((fit(l, 900, W - 2 * 110, 124) for l in ls), key=lambda x: x.size)
    y = 1130
    for i, l in enumerate(ls):
        cor = AMBER if i == len(ls) - 1 else WHITE
        d.text((W / 2, y + i * int(f.size * 1.12)), l, font=f, fill=cor, anchor="mm", stroke_width=6, stroke_fill=NAVY)
    yb = y + len(ls) * int(f.size * 1.12) + 10
    d.rectangle((W / 2 - 40, yb, W / 2 + 40, yb + 5), fill=AMBER)
    d.text((W / 2, yb + 50), "Dr. Jackson Bueno · Advogado de acidente de trabalho", font=P("Medium", 32), fill=SOFT, anchor="mm")
    img.alpha_composite(lay)
    img.convert("RGB").save(os.path.join(pasta, "capa.jpg"), quality=92)
    print("ok: capa.jpg")

if __name__ == "__main__":
    pasta = sys.argv[1]
    if "--preview" in sys.argv:
        render(pasta, [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")])
    elif "--antes-depois" in sys.argv:
        antes_depois(pasta, [float(x) for x in sys.argv[sys.argv.index("--antes-depois") + 1].split(",")])
    elif "--capa" in sys.argv:
        capa(pasta)
    else:
        render(pasta)
