#!/usr/bin/env python3
"""Faithfully crop a rendered PDF region specified in normalized page coordinates."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf')
    p.add_argument('--page',type=int,required=True,help='1-based PDF page index')
    p.add_argument('--box',nargs=4,type=float,required=True,metavar=('X0','Y0','X1','Y1'),
                   help='normalized left/top/right/bottom region, each between 0 and 1')
    p.add_argument('--dpi',type=int,default=240)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    x0,y0,x1,y1=a.box
    if not(0<=x0<x1<=1 and 0<=y0<y1<=1):p.error('--box must be a valid normalized region')
    if a.page<1 or a.dpi<72:p.error('page must be >=1 and dpi >=72')
    if not shutil.which('pdftoppm'):p.error('pdftoppm is required')
    src=Path(a.pdf).resolve()
    if not src.is_file():p.error('source PDF missing')
    with tempfile.TemporaryDirectory() as d:
        prefix=Path(d)/'page'
        cmd=['pdftoppm','-f',str(a.page),'-l',str(a.page),'-singlefile',
             '-png','-r',str(a.dpi),str(src),str(prefix)]
        subprocess.run(cmd,check=True,timeout=120,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        with Image.open(str(prefix)+'.png') as im:
            w,h=im.size
            crop=im.crop((int(w*x0),int(h*y0),int(w*x1),int(h*y1)))
            dest=Path(a.out).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
            crop.save(dest)
    print(dest)

if __name__=='__main__':main()
