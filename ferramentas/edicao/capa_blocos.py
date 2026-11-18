import subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
FONT='node_modules/@fontsource/montserrat/files/montserrat-latin-%d-normal.woff'
F=lambda w,s: ImageFont.truetype(FONT%w,s)
AM=(255,186,48); NAVY=(10,20,36)
grade='eq=brightness=0.02:contrast=1.07:saturation=1.10:gamma=1.02,colorbalance=rs=0.05:gs=0.01:bs=-0.05:rm=0.04:gm=0.01:bm=-0.04:rh=0.02:bh=-0.02,vignette=PI/5'
subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','34.3','-i','base.mov','-frames:v','1','-vf',grade,'cap_src.png'],check=True)
src=cv2.cvtColor(cv2.imread('cap_src.png'),cv2.COLOR_BGR2RGB)
face=np.load('face.npy'); cx,cy,_=face[min(len(face)-1,int(34.3*30))]
z=1.12; tx,ty=540,640
x0=min(max(0,cx-tx/z),1080-1080/z); y0=min(max(0,cy-ty/z),1920-1920/z)
fr=cv2.warpAffine(src,np.float32([[z,0,-x0*z],[0,z,-y0*z]]),(1080,1920),flags=cv2.INTER_CUBIC)
im=Image.fromarray(fr).convert('RGBA'); d=ImageDraw.Draw(im)
def block(y,h,fill,w):
    x0=(1080-w)//2
    sd=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(sd).rounded_rectangle([x0,y+8,x0+w,y+h+8],14,fill=(0,0,0,120))
    im.alpha_composite(sd.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle([x0,y,x0+w,y+h],14,fill=fill)
fa,fb=F(700,40),F(800,44)
la,lb='Doença causada pelo','trabalho também é'
w1=int(max(d.textlength(la,font=fa),d.textlength(lb,font=fb)))+80
block(1000,128,NAVY+(255,),w1)
dd=ImageDraw.Draw(im)
dd.text((540,1000+40),la,font=fa,fill=(225,232,242),anchor='mm')
dd.text((540,1000+90),lb,font=fb,fill=(255,255,255),anchor='mm')
t='ACIDENTE DE TRABALHO'; f=F(900,70)
while d.textlength(t,font=f)>860: f=F(900,f.size-2)
w2=int(d.textlength(t,font=f))+64
block(1146,108,AM+(255,),w2)
ImageDraw.Draw(im).text((540,1146+55),t,font=f,fill=NAVY,anchor='mm')
im.convert('RGB').save('capa.jpg',quality=94)
g=im.convert('RGB').crop((0,240,1080,1680)).resize((150,200))
p=im.convert('RGB').resize((540,960)); s=Image.new('RGB',(760,960),(255,255,255)); s.paste(p,(0,0)); s.paste(g,(575,380)); s.save('capa_check.jpg')
