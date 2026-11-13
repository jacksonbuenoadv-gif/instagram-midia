"""Trilha instrumental original e inspiradora (sintetizada aqui, sem direitos de terceiros) + story em vídeo.

Uso:
  python3 ferramentas/trilha.py posts/AAAA-MM-DD            -> gera posts/AAAA-MM-DD/story.mp4 (12 s)
      a partir de posts/AAAA-MM-DD/story.jpg, com zoom lento e trilha que muda a cada dia
      (tom, andamento, progressão de acordes e timbre escolhidos pela data).
  python3 ferramentas/trilha.py --so-audio saida.wav 2026-11-13 [segundos]

O Instagram não aceita música em carrossel publicado por API; por isso a trilha vai no story do dia.
"""
import sys, os, wave, subprocess, hashlib, numpy as np

SR = 44100

def note(m): return 440.0 * 2 ** ((m - 69) / 12)

# progressões em graus (semitons a partir da tônica), todas em tom maior, clima de esperança
PROGS = [
    [(0, 4, 7), (7, 11, 14), (9, 12, 16), (5, 9, 12)],     # I  V  vi IV
    [(9, 12, 16), (5, 9, 12), (0, 4, 7), (7, 11, 14)],     # vi IV I  V
    [(0, 4, 7), (5, 9, 12), (9, 12, 16), (7, 11, 14)],     # I  IV vi V
    [(0, 4, 7), (9, 12, 16), (5, 9, 12), (7, 11, 14)],     # I  vi IV V
    [(5, 9, 12), (7, 11, 14), (4, 7, 11), (9, 12, 16)],    # IV V iii vi
]
KEYS = [60, 62, 63, 65, 67, 69]          # Dó, Ré, Mi bemol, Fá, Sol, Lá
ARPS = [[0, 1, 2, 1], [0, 2, 1, 2], [0, 1, 2, 3], [2, 1, 0, 1]]

def reverb(x, secs=2.2, mix=0.35, seed=0):
    rng = np.random.default_rng(seed); n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir[0] = 1.0
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    wet /= (np.abs(wet).max() or 1)
    return (1 - mix) * x / (np.abs(x).max() or 1) + mix * wet

def trilha(T, seed_text):
    h = int(hashlib.sha1(seed_text.encode()).hexdigest(), 16)
    key = KEYS[h % len(KEYS)]; prog = PROGS[(h // 7) % len(PROGS)]; arp = ARPS[(h // 31) % len(ARPS)]
    bpm = 74 + (h // 97) % 18; beat = 60 / bpm; bar = beat * 4
    bright = 0.25 + ((h // 193) % 5) * 0.08          # quantidade de harmônicos do "piano"
    n = int(T * SR); t = np.arange(n) / SR
    pad = np.zeros(n); pno = np.zeros(n); bass = np.zeros(n); shim = np.zeros(n)
    def add(arr, sig, s):
        s = int(s * SR); e = min(n, s + len(sig))
        if 0 <= s < n and e > s: arr[s:e] += sig[:e - s]
    for k, b0 in enumerate(np.arange(0, T, bar)):
        ch = [key + d for d in prog[k % 4]]
        L = int((bar + 1.2) * SR); tt = np.arange(L) / SR
        env = np.minimum(1, tt / 1.1) * np.clip((bar + 1.2 - tt) / 1.2, 0, 1)
        sig = sum(np.sin(2 * np.pi * note(m) * tt) + np.sin(2 * np.pi * note(m) * 1.003 * tt) * 0.8 for m in ch)
        add(pad, sig * env, b0)
        tb = np.arange(int(bar * SR)) / SR
        add(bass, np.sin(2 * np.pi * note(ch[0] - 24) * tb) * np.exp(-tb * 0.9), b0)
        notes = ch + [ch[0] + 12]
        for j in range(8):   # arpejo em colcheias
            m = notes[arp[j % 4]] + 12
            tp = np.arange(int(1.6 * SR)) / SR
            s = (np.sin(2 * np.pi * note(m) * tp) + bright * np.sin(2 * np.pi * note(m) * 2 * tp)
                 + bright * 0.5 * np.sin(2 * np.pi * note(m) * 3 * tp)) * np.exp(-tp * 3.2) * np.minimum(1, tp / 0.004)
            add(pno, s * (0.9 if j % 2 == 0 else 0.6), b0 + j * beat / 2)
        if k % 2 == 1:   # brilho suave a cada dois compassos
            ts = np.arange(int(2.5 * SR)) / SR
            add(shim, np.sin(2 * np.pi * note(ch[2] + 24) * ts) * np.exp(-ts * 1.5) * np.minimum(1, ts / 0.3), b0)
    mix = pad * 0.10 + pno * 0.22 + bass * 0.16 + shim * 0.05
    mix = reverb(mix, seed=h % 1000)
    mix *= np.minimum(1, t / 1.5) * np.clip((T - t) / 2.5, 0, 1)
    info = f"tom {['Dó','Ré','Mi bemol','Fá','Sol','Lá'][KEYS.index(key)]} maior, {bpm} bpm, progressão {PROGS.index(prog) + 1}"
    return mix, info

def write_wav(path, a):
    a = np.clip(a / (np.abs(a).max() or 1) * 0.85, -1, 1)
    st = np.stack([a, np.roll(a, int(0.012 * SR))], 1)   # leve abertura estéreo
    with wave.open(path, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((st * 32767).astype(np.int16).tobytes())

def story_video(pasta, secs=12):
    pasta = pasta.rstrip("/"); data = os.path.basename(pasta)
    img = os.path.join(pasta, "story.jpg"); out = os.path.join(pasta, "story.mp4"); wav = os.path.join(pasta, "_trilha.wav")
    if not os.path.exists(img): sys.exit(f"falta {img}")
    a, info = trilha(secs, data); write_wav(wav, a)
    fr = secs * 30
    vf = (f"scale=1188:2112,zoompan=z='1+0.07*on/{fr}':d={fr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-i", wav, "-vf", vf, "-t", str(secs),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    os.remove(wav)
    print(f"ok {out} ({info})")

if __name__ == "__main__":
    if sys.argv[1] == "--so-audio":
        a, info = trilha(float(sys.argv[4]) if len(sys.argv) > 4 else 12, sys.argv[3]); write_wav(sys.argv[2], a); print(info)
    else:
        story_video(sys.argv[1])
