"""Gerador de carrosseis @jacksonbueno.adv (1080x1350 JPEG), identidade do site jacksonbueno.adv.br.
Uso: python3 gerar.py spec.json pasta_saida
Requisitos: npm i @fontsource/playfair-display @fontsource/montserrat (na mesma pasta do script);
pip install playwright pillow; Chrome em /usr/bin/google-chrome (ou ajuste CHROME).
Marcacao nos textos: *texto* = destaque dourado em italico (titulos); **texto** = negrito.
Tipos de slide (campo "type"):
 cover    {kicker, title, sub, photo?}   photo = caminho de uma foto real (ex.: "fotos/obra-andaime.jpg", relativo à raiz do repositório)
 big      {kicker, big, big_label, paragraphs[], src}
 cards    {title, cards:[{code, tag, ok:bool, items:[{y:bool, text}]}], tip}   (2 cartoes; ok=true destaca em dourado)
 list     {kicker?, title, intro?, items:[{b, span}], src?}                     (2 a 4 itens numerados)
 options  {title, intro, options:[{b, span}], warn}                              (2 opcoes lado a lado + alerta)
 checklist{kicker, title, items:[{t, small}]}                                    (fundo claro; ate 4 itens)
 text     {kicker?, title, paragraphs[], src?}
 cta      {title, text, button}                                                  (sempre o ultimo; rodape com OAB)
Spec: {"oab": "OAB/MG 211.217", "story": true, "slides": [...]}
Com "story": true, gera também story.jpg (1080x1920) a partir da capa, para publicar nos Stories.
"""
import sys, json, re, pathlib, os
from playwright.sync_api import sync_playwright
from PIL import Image

spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
OAB = spec.get("oab", "OAB/MG 211.217")
BASE = pathlib.Path(__file__).resolve().parent
F = (BASE / "node_modules/@fontsource").as_uri()
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
TOTAL = len(spec["slides"])

CSS = f"""
@font-face{{font-family:PF;src:url({F}/playfair-display/files/playfair-display-latin-700-normal.woff2);font-weight:700}}
@font-face{{font-family:PF;src:url({F}/playfair-display/files/playfair-display-latin-800-normal.woff2);font-weight:800}}
@font-face{{font-family:PF;src:url({F}/playfair-display/files/playfair-display-latin-700-italic.woff2);font-weight:700;font-style:italic}}
@font-face{{font-family:PF;src:url({F}/playfair-display/files/playfair-display-latin-800-italic.woff2);font-weight:800;font-style:italic}}
@font-face{{font-family:MS;src:url({F}/montserrat/files/montserrat-latin-400-normal.woff2);font-weight:400}}
@font-face{{font-family:MS;src:url({F}/montserrat/files/montserrat-latin-500-normal.woff2);font-weight:500}}
@font-face{{font-family:MS;src:url({F}/montserrat/files/montserrat-latin-600-normal.woff2);font-weight:600}}
@font-face{{font-family:MS;src:url({F}/montserrat/files/montserrat-latin-700-normal.woff2);font-weight:700}}
@font-face{{font-family:MS;src:url({F}/montserrat/files/montserrat-latin-800-normal.woff2);font-weight:800}}
:root{{--toga:#0f1624;--gold:#daa843;--perg:#fbf8f2;--muted:#b9bdc7;--green:#1f9d63;--red:#e0605a}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1080px;height:1350px}} html:has(body.story){{height:1920px}}
body{{font-family:MS;color:var(--perg);background:linear-gradient(135deg,#080d19 0%,#141a29 55%,#242d42 100%);
 position:relative;overflow:hidden;padding:72px 84px}}
body.light{{background:linear-gradient(180deg,#fbf8f2 0%,#f4f0e7 100%);color:#0f1624}}
body.light .brand b{{color:#0f1624}} body.light .count,body.light .handle{{color:#5b6070}}
body.light .p{{color:#383d48}}
.glow{{position:absolute;right:-260px;top:-260px;width:720px;height:720px;border-radius:50%;
 background:radial-gradient(circle,rgba(218,168,67,.16),rgba(218,168,67,0) 65%)}}
.top{{display:flex;align-items:center;justify-content:space-between;position:relative}}
.brand{{display:flex;align-items:center;gap:20px}}
.mono{{width:78px;height:78px;border-radius:50%;border:2.5px solid var(--gold);display:flex;align-items:center;justify-content:center;
 font-family:PF;font-weight:700;font-size:34px;color:var(--gold);letter-spacing:-1px}}
.brand b{{display:block;font-family:PF;font-weight:700;font-size:30px;color:var(--perg)}}
.brand small{{display:block;font-size:17px;letter-spacing:4px;color:var(--gold);font-weight:600;margin-top:4px}}
.count{{font-size:24px;font-weight:600;color:var(--muted);letter-spacing:2px}}
.main{{position:absolute;left:84px;right:84px;top:210px;bottom:170px;display:flex;flex-direction:column;justify-content:center}}
.bottom{{position:absolute;left:84px;right:84px;bottom:64px;display:flex;justify-content:space-between;align-items:center}}
.handle{{font-size:24px;color:var(--muted);font-weight:500}}
.swipe{{font-size:24px;font-weight:700;color:var(--gold);letter-spacing:1px}}
.kicker{{display:inline-block;align-self:flex-start;border:2px solid rgba(218,168,67,.55);color:var(--gold);border-radius:999px;
 padding:12px 26px;font-size:22px;font-weight:700;letter-spacing:4px;margin-bottom:40px}}
h1{{font-family:PF;font-weight:800;font-size:92px;line-height:1.08;letter-spacing:-1px}}
h2{{font-family:PF;font-weight:800;font-size:72px;line-height:1.1;letter-spacing:-.5px;margin-bottom:40px}}
em{{font-style:italic;color:var(--gold)}}
.p{{font-size:37px;line-height:1.45;color:#e4e1da;font-weight:500}}
.p strong{{color:var(--perg);font-weight:700}} body.light .p strong{{color:#0f1624}}
.src{{margin-top:36px;font-size:24px;color:var(--gold);font-weight:600;letter-spacing:1px}}
.bar{{width:120px;height:6px;background:linear-gradient(135deg,#f1ba4b,#ba882e);border-radius:3px;margin:44px 0}}
.big{{font-family:PF;font-weight:800;font-size:250px;line-height:.9;color:var(--gold)}}
.big span{{font-size:90px;display:block;color:var(--perg);margin-top:10px}}
.cards{{display:flex;gap:30px}}
.card{{flex:1;border-radius:28px;padding:40px 36px;background:rgba(255,255,255,.05);border:2px solid rgba(255,255,255,.12)}}
.card.ok{{border-color:var(--gold);background:rgba(218,168,67,.09)}}
.code{{font-family:PF;font-weight:800;font-size:96px;line-height:1}}
.card.ok .code{{color:var(--gold)}}
.tag{{font-size:24px;font-weight:700;letter-spacing:2px;margin:10px 0 30px;color:var(--muted)}}
.li{{display:flex;gap:16px;font-size:29px;line-height:1.35;margin-bottom:22px;font-weight:500}}
.ic{{flex:none;width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:24px;margin-top:-2px}}
.y{{background:var(--green);color:#fff}} .n{{background:var(--red);color:#fff}}
.tip{{margin-top:40px;font-size:29px;line-height:1.4;color:#e4e1da;border-left:6px solid var(--gold);padding-left:26px}}
.list .row{{display:flex;gap:28px;align-items:flex-start;margin-bottom:40px}}
.num{{flex:none;width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#f1ba4b,#ba882e);color:#0f1624;
 font-family:PF;font-weight:800;font-size:36px;display:flex;align-items:center;justify-content:center}}
.row b{{display:block;font-size:38px;font-weight:700;margin-bottom:6px}}
.row span{{display:block;font-size:29px;line-height:1.4;color:#5b6070;font-weight:500}}
body:not(.light) .row span{{color:#c9ccd3}}
.opts{{display:flex;gap:28px;margin:10px 0 40px}}
.opt{{flex:1;border-radius:26px;padding:36px;background:rgba(218,168,67,.09);border:2px solid var(--gold)}}
.opt b{{font-family:PF;font-size:50px;color:var(--gold);display:block;margin-bottom:12px}}
.opt span{{font-size:30px;line-height:1.4;font-weight:500}}
.warn{{border-radius:22px;padding:28px 32px;background:rgba(224,96,90,.12);border:2px solid rgba(224,96,90,.6);font-size:30px;line-height:1.4;font-weight:600}}
.check .it{{display:flex;gap:24px;align-items:center;padding:30px 0;border-bottom:2px solid #dbd7cf;font-size:34px;font-weight:600}}
.check .it:last-child{{border-bottom:0}}
.box{{flex:none;width:52px;height:52px;border-radius:12px;border:3px solid #ba882e;display:flex;align-items:center;justify-content:center;color:#ba882e;font-weight:800;font-size:30px}}
.check small{{display:block;font-size:25px;font-weight:500;color:#5b6070;margin-top:4px}}
.cta{{margin-top:50px;display:inline-flex;align-self:flex-start;gap:16px;align-items:center;background:#006336;color:#fff;border-radius:999px;padding:26px 44px;font-size:32px;font-weight:700}}
.sign{{margin-top:56px;font-size:24px;color:var(--muted);line-height:1.5}}
.ph{{position:absolute;inset:0;background-size:cover;background-position:center;filter:saturate(.85)}}
.ph:after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(8,13,25,.55) 0%,rgba(8,13,25,.35) 30%,rgba(8,13,25,.88) 62%,#080d19 100%)}}
body.photo .main{{justify-content:flex-end}}
body.story{{height:1920px}} body.story .main{{top:300px;bottom:330px}}
.storytag{{position:absolute;left:84px;right:84px;bottom:150px;text-align:center;font-size:34px;font-weight:700;color:#0f1624;background:linear-gradient(135deg,#f1ba4b,#ba882e);border-radius:999px;padding:30px}}
"""

def md(s, em_style=""):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", rf"<em{em_style}>\1</em>", s)
    return s

REPO = BASE.parent  # raiz do repositório (fotos/ fica aqui)

def page(n, body, light=False, last=False, photo=None, story=False):
    swipe = "" if (last or story) else '<div class="swipe">Arraste →</div>'
    cls = " ".join(c for c in ["light" if light else "", "photo" if photo else "", "story" if story else ""] if c)
    bg = ""
    if photo:
        ph = (REPO / photo).resolve()
        if not ph.exists(): raise FileNotFoundError(f"foto não encontrada: {ph}")
        bg = f'<div class="ph" style="background-image:url({ph.as_uri()})"></div>'
    elif not light:
        bg = '<div class="glow"></div>'
    tag = '<div class="storytag">Novo post no perfil · @jacksonbueno.adv</div>' if story else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body class="{cls}">{bg}{tag}
<div class="top"><div class="brand"><div class="mono">JB</div><div><b>Jackson Bueno Advogados</b><small>DIREITO DO ACIDENTADO</small></div></div>
<div class="count">{"" if story else f"{n:02d}/{TOTAL:02d}"}</div></div>
<div class="main">{body}</div>
<div class="bottom"><div class="handle">@jacksonbueno.adv</div>{swipe}</div></body></html>"""

def kick(s, light=False):
    if not s.get("kicker"): return ""
    st = ' style="color:#ba882e;border-color:#ba882e"' if light else ""
    return f'<div class="kicker"{st}>{s["kicker"]}</div>'

def src(s): return f'<div class="src">{s["src"]}</div>' if s.get("src") else ""

def render(s, n, story=False):
    t = s["type"]
    if t == "cover":
        return page(n, f'{kick(s)}<h1>{md(s["title"])}</h1><div class="bar"></div><p class="p">{md(s.get("sub",""))}</p>', photo=s.get("photo"), story=story)
    if t == "big":
        ps = "".join(f'<p class="p"{" style=\"margin-top:24px\"" if i else ""}>{md(p)}</p>' for i,p in enumerate(s.get("paragraphs",[])))
        return page(n, f'{kick(s)}<div class="big">{s["big"]}<span>{s["big_label"]}</span></div><div class="bar"></div>{ps}{src(s)}')
    if t == "cards":
        cs = ""
        for c in s["cards"]:
            lis = "".join(f'<div class="li"><div class="ic {"y" if i["y"] else "n"}">{"✓" if i["y"] else "✕"}</div>{md(i["text"])}</div>' for i in c["items"])
            cs += f'<div class="card{" ok" if c.get("ok") else ""}"><div class="code">{c["code"]}</div><div class="tag">{c["tag"]}</div>{lis}</div>'
        tip = f'<div class="tip">{md(s["tip"])}</div>' if s.get("tip") else ""
        return page(n, f'<h2>{md(s["title"])}</h2><div class="cards">{cs}</div>{tip}')
    if t == "list":
        intro = f'<p class="p">{md(s["intro"])}</p>' if s.get("intro") else ""
        rows = "".join(f'<div class="row"><div class="num">{i+1}</div><div><b>{md(it["b"])}</b><span>{md(it["span"])}</span></div></div>' for i,it in enumerate(s["items"]))
        mt = ' style="margin-top:44px"' if intro else ""
        return page(n, f'{kick(s)}<h2>{md(s["title"])}</h2>{intro}<div class="list"{mt}>{rows}</div>{src(s)}')
    if t == "options":
        ops = "".join(f'<div class="opt"><b>{o["b"]}</b><span>{md(o["span"])}</span></div>' for o in s["options"])
        warn = f'<div class="warn">{md(s["warn"])}</div>' if s.get("warn") else ""
        return page(n, f'<h2>{md(s["title"])}</h2><p class="p" style="margin-bottom:36px">{md(s["intro"])}</p><div class="opts">{ops}</div>{warn}')
    if t == "checklist":
        its = "".join(f'<div class="it"><div class="box">✓</div><div>{md(i["t"])}<small>{md(i.get("small",""))}</small></div></div>' for i in s["items"])
        return page(n, f'{kick(s, True)}<h2 style="color:#0f1624">{md(s["title"], " style=\"color:#ba882e\"")}</h2><div class="check">{its}</div>', light=True)
    if t == "text":
        ps = "".join(f'<p class="p"{" style=\"margin-top:24px\"" if i else ""}>{md(p)}</p>' for i,p in enumerate(s["paragraphs"]))
        return page(n, f'{kick(s)}<h2>{md(s["title"])}</h2>{ps}{src(s)}')
    if t == "cta":
        return page(n, f'<h2>{md(s["title"])}</h2><p class="p">{md(s["text"])}</p><div class="cta">{s.get("button","Salve e compartilhe com quem precisa")}</div>'
                       f'<div class="sign">Conteúdo informativo. Não substitui a análise individual do seu caso.<br>Jackson Bueno Advogados · {OAB}</div>', last=True)
    raise ValueError(t)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    for i, s in enumerate(spec["slides"], 1):
        f = OUT / f"slide{i}.html"; f.write_text(render(s, i), encoding="utf-8")
        pg.goto(f.as_uri()); pg.wait_for_timeout(400); pg.evaluate("document.fonts.ready")
        ov = pg.evaluate("(()=>{const m=document.querySelector('.main');return m.scrollHeight-m.clientHeight})()")
        if ov > 2: print(f"AVISO: slide {i} transborda {ov}px — encurte o texto"); 
        png = OUT / f"slide{i}.png"; pg.screenshot(path=str(png))
        Image.open(png).convert("RGB").save(OUT / f"slide{i}.jpg", "JPEG", quality=90)
        png.unlink(); f.unlink()
    if spec.get("story"):
        pg.set_viewport_size({"width": 1080, "height": 1920})
        f = OUT / "story.html"; f.write_text(render(spec["slides"][0], 1, story=True), encoding="utf-8")
        pg.goto(f.as_uri()); pg.wait_for_timeout(400); pg.evaluate("document.fonts.ready")
        png = OUT / "story.png"; pg.screenshot(path=str(png))
        Image.open(png).convert("RGB").save(OUT / "story.jpg", "JPEG", quality=90)
        png.unlink(); f.unlink()
    b.close()
print("ok", TOTAL, OUT)
