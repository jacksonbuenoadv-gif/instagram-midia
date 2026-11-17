"""Post do feed em vídeo com trilha (pedido do titular em 17/11/2026: "trilha nas postagens, instrumental, suave, motivacional").

O Instagram não aceita música em carrossel publicado por API. Por isso o post diário vira um vídeo vertical
(1080x1920, 30 fps) em que os slides do carrossel passam um a um, com zoom lento, transição suave e a
trilha instrumental original de ferramentas/trilha.py (muda de tom e andamento a cada dia). Publicado com
create_video_post, ele aparece no feed e na aba Reels.

Uso:
  python3 ferramentas/video_post.py posts/AAAA-MM-DD
Saídas em posts/AAAA-MM-DD/:
  video.mp4        vídeo com trilha
  capa_video.jpg   capa (slide 1 sobre fundo desfocado; o slide inteiro fica dentro da área 3:4 da grade)

Tempo de cada slide: proporcional à quantidade de texto do spec.json (capa 4 s; demais 5 a 8,5 s).
"""
import sys, os, re, json, glob, subprocess, tempfile
from PIL import Image, ImageFilter, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trilha import trilha, write_wav  # noqa: E402

W, H, FPS, XF = 1080, 1920, 30, 0.6   # XF = duração da transição (s)


def compor(slide_path, out_path):
    s = Image.open(slide_path).convert("RGB")
    sw, sh = s.size
    sc = W / sw
    s = s.resize((W, round(sh * sc)), Image.LANCZOS)
    bg = s.resize((round(H * s.width / s.height), H), Image.LANCZOS)
    left = (bg.width - W) // 2
    bg = bg.crop((left, 0, left + W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    bg.paste(s, (0, (H - s.height) // 2))
    bg.save(out_path, quality=93)


def duracoes(pasta, n):
    try:
        slides = json.load(open(os.path.join(pasta, "spec.json")))["slides"]
    except Exception:
        slides = []
    out = []
    for i in range(n):
        if i == 0:
            out.append(4.0); continue
        txt = " ".join(re.findall(r'"([^"]*)"', json.dumps(slides[i], ensure_ascii=False))) if i < len(slides) else ""
        palavras = len(txt.split())
        out.append(max(5.0, min(8.5, 2.5 + 0.075 * palavras)) if palavras else 6.0)
    return out


def main(pasta):
    pasta = pasta.rstrip("/"); data = os.path.basename(pasta)
    slides = sorted(glob.glob(os.path.join(pasta, "slide*.jpg")), key=lambda p: int(re.findall(r"\d+", os.path.basename(p))[0]))
    if len(slides) < 2: sys.exit(f"faltam slides em {pasta}")
    durs = duracoes(pasta, len(slides))
    with tempfile.TemporaryDirectory() as wd:
        clips = []
        for i, (sp, d) in enumerate(zip(slides, durs)):
            img = f"{wd}/c{i}.jpg"; compor(sp, img)
            if i == 0: Image.open(img).save(os.path.join(pasta, "capa_video.jpg"), quality=92)
            fr = int(round(d * FPS))
            vf = (f"scale={int(W*1.1)}:{int(H*1.1)},zoompan=z='1+0.035*on/{fr}':d={fr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                  f":s={W}x{H}:fps={FPS},format=yuv420p")
            clip = f"{wd}/c{i}.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-vf", vf, "-frames:v", str(fr),
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", clip], check=True)
            clips.append(clip)
        # transições suaves entre os slides
        ins = sum((["-i", c] for c in clips), [])
        fc, prev, off = [], "[0:v]", 0.0
        for i in range(1, len(clips)):
            off += durs[i - 1] - XF
            lab = f"[x{i}]"
            fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{lab}")
            prev = lab
        total = sum(durs) - XF * (len(clips) - 1)
        a, info = trilha(total, data)
        wav = f"{wd}/trilha.wav"; write_wav(wav, a)
        out = os.path.join(pasta, "video.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-i", wav, "-filter_complex", ";".join(fc),
                        "-map", prev, "-map", f"{len(clips)}:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"ok {out} ({total:.1f}s, {len(slides)} slides, {info}) e capa_video.jpg")


if __name__ == "__main__":
    main(sys.argv[1])
