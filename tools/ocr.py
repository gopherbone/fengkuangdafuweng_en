import os as _os; _R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import numpy as np, json
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
d=open(_R + '/orig/fkdfw.gbc','rb').read()
def glyph(idx):
    p,x=idx>>8,idx&0xff
    o=(9+(p>>1))*0x4000+(p&1)*0x2000+1+x*32
    g=d[o:o+32]; a=np.zeros((16,16))
    for col in range(2):
        for r in range(16):
            for bit in range(8):
                if g[col*16+r]&(0x80>>bit): a[r,col*8+bit]=1
    return a
def norm(a):
    ys,xs=np.nonzero(a>0.5)
    if len(ys)==0: return None
    a=a[ys.min():ys.max()+1, xs.min():xs.max()+1]
    im=Image.fromarray((a*255).astype(np.uint8)).resize((24,24),Image.BILINEAR)
    v=gaussian_filter(np.asarray(im,dtype=float)/255,1.0).ravel()
    v-=v.mean(); n=np.linalg.norm(v); return v/n if n else None
# candidates: big5 chars + punctuation
cands=set()
for hi in range(0xA1,0xFA):
    for lo in list(range(0x40,0x7F))+list(range(0xA1,0xFF)):
        try: cands.add(bytes([hi,lo]).decode('big5'))
        except: pass
cands=sorted(cands)
fonts=[ImageFont.truetype(f,15,index=i) for f,i in [('/System/Library/Fonts/STHeiti Medium.ttc',0),('/System/Library/Fonts/STHeiti Light.ttc',0),('/System/Library/Fonts/Supplemental/Songti.ttc',0)]]
mats=[]
for f in fonts:
    vs=[]; ok=[]
    for c in cands:
        im=Image.new('L',(20,20),0); ImageDraw.Draw(im).text((2,1),c,fill=255,font=f)
        a=(np.asarray(im)>100).astype(float)
        v=norm(a); vs.append(v if v is not None else np.zeros(576))
    mats.append(np.array(vs))
res={}
for idx in range(0,10*256):
    v=norm(glyph(idx))
    if v is None: continue
    sc=np.max([m@v for m in mats],axis=0)
    top=np.argsort(-sc)[:5]
    res[idx]=[(cands[t],round(float(sc[t]),3)) for t in top]
json.dump(res,open(_R + '/font/ocr.json','w'),ensure_ascii=False)
print(len(res))
