#!/usr/bin/env python3
"""Summarize repeated logos, header text and theme candidates in an existing PPTX.

This is a candidate detector, NOT a claim that a logo/master has been reproduced.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def shape_color(shape):
    try:
        if shape.fill.type is not None:
            c = shape.fill.fore_color
            if c.type is not None and c.rgb is not None:
                return str(c.rgb)
    except Exception:
        pass
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pptx')
    p.add_argument('--out', required=True)
    args=p.parse_args()
    input_file=Path(args.pptx).resolve()
    prs=Presentation(str(input_file))
    fonts=collections.Counter(); colors=collections.Counter()
    image_repeats=collections.defaultdict(list)
    text_repeats=collections.defaultdict(list)
    for si, slide in enumerate(prs.slides,1):
        for oi, shape in enumerate(slide.shapes,1):
            if shape.has_text_frame:
                content=shape.text.strip()
                if 0<len(content)<110:
                    text_repeats[content].append(si)
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.name: fonts[run.font.name]+=1
                        try:
                            if run.font.color.rgb: colors[str(run.font.color.rgb)]+=1
                        except Exception: pass
            sc=shape_color(shape)
            if sc: colors[sc]+=1
            if shape.shape_type==MSO_SHAPE_TYPE.PICTURE:
                data=shape.image.blob
                digest=hashlib.sha256(data).hexdigest()[:15]
                image_repeats[digest].append({'slide':si,'object':oi,'left':int(shape.left),
                                              'top':int(shape.top),'width':int(shape.width),
                                              'height':int(shape.height),'ext':shape.image.ext})
    n=len(prs.slides)
    common_text=[{'text':x,'slides':sorted(set(ss)),'count':len(set(ss))} for x,ss in text_repeats.items()
                 if len(set(ss))>1]
    common_text.sort(key=lambda v:-v['count'])
    recurring_images=[]
    for h,uses in image_repeats.items():
        repeated=len({u['slide'] for u in uses})
        if repeated>1:
            recurring_images.append({'sha_prefix':h,'appearances':uses,'slides_count':repeated,
                'candidate_logo':repeated>=max(2,int(n*0.5)) and
                    sum(u['left']>int(prs.slide_width*0.65) and u['top']<int(prs.slide_height*0.25) for u in uses)>=repeated*0.5})
    recurring_images.sort(key=lambda v:-v['slides_count'])
    report={'input_file':str(input_file),'slide_count':n,'slide_width_inches':round(prs.slide_width/914400,4),
            'slide_height_inches':round(prs.slide_height/914400,4),'fonts':fonts.most_common(),
            'colors':colors.most_common(15),'repeated_text_candidates':common_text[:30],
            'repeated_image_candidates':recurring_images[:20],
            'caveat':'Detects repeats, NOT the authorized logo, exact master, or complete styling; inspect original slide visually.'}
    dest=Path(args.out).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(dest),'slides':n,'repeated_image_candidates':len(recurring_images)},indent=2))

if __name__=='__main__': main()
