import sys, numpy as np, wave
sys.path.insert(0,'/home/claude/jacksonbuenoadv-gif/instagram-midia/ferramentas')
import trilha as TR
SR=44100; T=34.3
mus,info=TR.trilha(T,'doenca-do-trabalho-2026-11-18'); print(info); TR.write_wav('music.wav',mus)
n=int(T*SR); fx=np.zeros(n); rng=np.random.default_rng(11)
def add(sig,t):
    s=int(t*SR); e=min(n,s+len(sig)); fx[s:e]+=sig[:e-s]
def lp_noise(L,c0,c1,p=1):
    x=rng.standard_normal(L); y=np.zeros(L); a=0
    for i in range(L):
        c=c0+(c1-c0)*(i/L)**p; a+=c*(x[i]-a); y[i]=a
    return y
def whoosh(d=0.32):
    L=int(d*SR); t=np.arange(L)/SR; return lp_noise(L,0.02,0.5)*np.sin(np.pi*t/d)**2*0.5
def pop(f0=900):
    L=int(0.09*SR); t=np.arange(L)/SR; f=f0*np.exp(-t*25)+300
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*45)*0.42
def ding(fq=1320):
    L=int(0.5*SR); t=np.arange(L)/SR
    return (np.sin(2*np.pi*fq*t)+0.4*np.sin(2*np.pi*fq*2.01*t))*np.exp(-t*7)*0.2
def impact():
    L=int(0.7*SR); t=np.arange(L)/SR; f=110*np.exp(-t*4)+40
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*5)+rng.standard_normal(L)*np.exp(-t*30)*0.3)*0.6
def riser(d=0.8):
    L=int(d*SR); t=np.arange(L)/SR
    return (lp_noise(L,0.01,0.25,2)*1.6+np.sin(2*np.pi*np.cumsum(200+600*(t/d)**2)/SR)*0.15)*(t/d)**2*0.45
def tick():
    L=int(0.04*SR); t=np.arange(L)/SR; return np.sin(2*np.pi*2400*t)*np.exp(-t*120)*0.25
add(impact(),0.02)
for t in [4.604,14.167,26.70]: add(whoosh(),t-0.16)
for t in [5.10,6.60,9.40,10.95,12.92]: add(pop(),t)
add(pop(600),11.0)
add(riser(),14.9); add(impact()*0.55,15.74)
add(pop(700),17.0)
for t,fq in [(20.50,1320),(21.65,1480),(23.35,1660),(24.95,1760)]: add(ding(fq),t)
add(ding(1760)*1.2,27.32)
fx=np.clip(fx,-1,1)
with wave.open('fx.wav','wb') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((fx*32767).astype(np.int16).tobytes())
