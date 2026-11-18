"""Confere, quadro a quadro, se algum texto/cartão invade o rosto (testa ao queixo)."""
import json, numpy as np, importlib.util
from PIL import Image
sp=importlib.util.spec_from_file_location('r','anuncio_dinamico.py'); r=importlib.util.module_from_spec(sp); sp.loader.exec_module(r)
face=np.load('face.npy'); r.FACE=face
words=json.load(open('words2.json')); ev=r.build_events(words)
def bbox(e):
    if e['name']=='cap': img,pad=r.cap_img(e['img'][1])
    else: img,pad=e['img']
    w,h=img.width-2*pad, img.height-2*pad
    x0=(r.W-img.width)//2+pad if e['x']=='c' else int(e['x'])
    return x0, int(e['y']), x0+w, int(e['y'])+h
probs={}
for e in ev:
    if e['name']=='badge' and False: continue
    bx=bbox(e)
    i0=int(e['t0']*r.FPS); i1=min(len(face), int(min(e['t1'],40)*r.FPS))
    for i in range(i0,i1):
        l,top,rr,chin=r.face_box(i,face)
        if bx[0]<rr-10 and bx[2]>l+10 and bx[1]<chin-6 and bx[3]>top+10:
            key=(e['name'], round(e['t0'],2)); probs.setdefault(key,[]).append(round(i/30,2))
for k,v in probs.items(): print(k, 'de', v[0], 'a', v[-1], f'({len(v)} quadros)')
print('ok' if not probs else f'{len(probs)} elementos com sobreposição')
