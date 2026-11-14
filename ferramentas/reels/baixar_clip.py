#!/usr/bin/env python3
"""
Baixa um vídeo gratuito do Pexels, converte para o padrão do banco (720x1280, 30 fps, sem áudio)
e registra a linha em ferramentas/reels/stock/README.md.

USO
    python3 ferramentas/reels/baixar_clip.py <link-ou-id-do-pexels | link-direto-.mp4> <nome_do_clipe> "<o que mostra>" "<bom para>"

EXEMPLO
    python3 ferramentas/reels/baixar_clip.py https://www.pexels.com/video/a-man-riding-a-motorcycle-1234567/ \
        moto_transito_cidade "motoboy no trânsito da cidade" "acidente de trajeto, moto"

Regras: nome em minúsculas_com_sublinhado, sem repetir um nome existente. Depois de baixar, confira um quadro
com Read (ferramentas/reels/stock/_conferir_<nome>.jpg, apagado no fim): sem marca d'água, sem logotipo
em destaque, combina com o tema. Se não servir, apague o .mp4 e a linha do README.
"""
import os, re, sys, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = os.path.join(HERE, "stock")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def curl(url, out=None, text=False):
    cmd = ["curl", "-sSL", "--fail", "--max-time", "180", "-A", UA, url]
    if out: cmd += ["-o", out]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"falha ao baixar {url}: {r.stderr.decode(errors='ignore').strip()[:200]}")
    return r.stdout.decode(errors="ignore") if text else None


def pexels_id(s):
    m = re.search(r"(\d{5,})/?$", s.strip().rstrip("/")) or re.search(r"-(\d{5,})", s)
    return m.group(1) if m else (s if s.isdigit() else None)


def main():
    if len(sys.argv) < 5: sys.exit(__doc__)
    src, nome, mostra, bom = sys.argv[1:5]
    if not re.fullmatch(r"[a-z0-9_]+", nome): sys.exit("nome inválido: use minúsculas, números e _")
    dest = os.path.join(STOCK, nome + ".mp4")
    if os.path.exists(dest): sys.exit(f"já existe {dest}")
    tmp = tempfile.mkdtemp()
    raw = os.path.join(tmp, "orig.mp4")
    pid = None
    if src.lower().split("?")[0].endswith(".mp4"):
        curl(src, raw)
        pid = pexels_id(src.split("/video-files/")[1].split("/")[0]) if "/video-files/" in src else ""
    else:
        pid = pexels_id(src)
        if not pid: sys.exit("não reconheci o id do Pexels no link")
        try:
            curl(f"https://www.pexels.com/download/video/{pid}/", raw)   # redireciona para videos.pexels.com
        except RuntimeError:
            # plano B: procura os arquivos de vídeo na página e prefere o vertical 720x1280 / 1080x1920
            page = curl(src if src.startswith("http") else f"https://www.pexels.com/video/{pid}/", text=True)
            links = sorted(set(re.findall(r"https://videos\.pexels\.com/video-files/[^\"'\s]+?\.mp4", page)))
            if not links: raise
            pref = [l for l in links if re.search(r"(720_1280|1080_1920)", l)] or links
            curl(pref[0], raw)
    if os.path.getsize(raw) < 50_000: sys.exit("arquivo baixado pequeno demais (provável bloqueio)")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-vf",
                    "fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
                    "-an", "-crf", "25", "-t", "20", dest], check=True)
    conf = os.path.join(STOCK, f"_conferir_{nome}.jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", dest, "-frames:v", "1", "-vf", "scale=360:640", conf], check=True)
    readme = os.path.join(STOCK, "README.md")
    linhas = open(readme, encoding="utf-8").read().split("\n")
    pos = max(i for i, l in enumerate(linhas) if l.startswith("| "))   # depois da última linha da tabela
    linhas.insert(pos + 1, f"| {nome} | {mostra} | {bom} | {pid or '-'} |")
    open(readme, "w", encoding="utf-8").write("\n".join(linhas))
    print(f"ok: {dest} ({os.path.getsize(dest) // 1024} KB). Confira o quadro: {conf}")


if __name__ == "__main__":
    main()
