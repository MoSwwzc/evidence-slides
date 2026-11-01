#!/usr/bin/env python3
"""Generate an original, synthetic non-experimental demo figure (for tests)."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
p=Path(__file__).with_name('sample_figure.png')
im=Image.new('RGB',(1500,720),'white')
d=ImageDraw.Draw(im)
try:
    title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',42)
    text=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',32)
except OSError:
    title=text=ImageFont.load_default()
stages=[('Read source',(70,160,450,520)),('Check claims',(550,160,930,520)),('Build slides',(1030,160,1410,520))]
for i,(s,xy) in enumerate(stages):
    d.rectangle(xy,outline='#B22D36',width=4)
    d.text((xy[0]+32,xy[1]+140),s,fill='#222222',font=text)
    if i<2:
        y=(xy[1]+xy[3])//2
        d.line((xy[2]+20,y,xy[2]+75,y),fill='#777777',width=8)
        d.polygon([(xy[2]+70,y-14),(xy[2]+96,y),(xy[2]+70,y+14)],fill='#777777')
d.text((60,55),'Synthetic workflow illustration (not experimental data)',fill='#555555',font=title)
im.save(p)
print(p)
