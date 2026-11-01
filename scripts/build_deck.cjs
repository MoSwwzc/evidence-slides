#!/usr/bin/env node
/*
 * Portable baseline PPTX builder. The agent prepares evidence-based deck_plan.json;
 * this CLI renders it into actual editable slides, not a montage.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');
const { imageSize } = require('image-size');

function die(message) { console.error('ERROR:', message); process.exit(1); }
function argsFrom(argv) {
  const o = { plan: argv[0], variant: 'A', output: '' };
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === '--variant') o.variant = argv[++i];
    else if (argv[i] === '--output') o.output = argv[++i];
    else if (argv[i] === '--help') {
      console.log('Usage: node scripts/build_deck.cjs PLAN.json --variant A --output file.pptx');
      process.exit(0);
    } else die('unknown argument: ' + argv[i]);
  }
  if (!o.plan || !o.output) die('plan and --output are required');
  return o;
}
const arg = argsFrom(process.argv.slice(2));
const planFile = path.resolve(arg.plan);
if (!fs.existsSync(planFile)) die('plan not found: ' + planFile);
const plan = JSON.parse(fs.readFileSync(planFile, 'utf8'));
const selected = plan.variants.find(v => v.id === arg.variant);
if (!selected) die('variant not in plan: ' + arg.variant);
const themeFile = path.resolve(__dirname, '../themes', selected.theme + '.json');
if (!fs.existsSync(themeFile)) die('theme not found: ' + selected.theme);
const theme = Object.assign({}, JSON.parse(fs.readFileSync(themeFile, 'utf8')), selected.theme_overrides || {});
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Evidence Slides';
pptx.subject = plan.meta.title;
pptx.title = plan.meta.title;
pptx.company = '';
pptx.lang = plan.meta.language || 'en-US';
pptx.theme = { headFontFace: theme.fontLatin, bodyFontFace: theme.fontLatin, lang: pptx.lang };
const W = 13.333333, H = 7.5, M = 0.65;
const accent = theme.accent, text = theme.text, secondary = theme.secondary, background = theme.background;
const assetMap = Object.fromEntries((plan.assets || []).map(a => [a.id, a]));
const sourceMap = Object.fromEntries((plan.sources || []).map(s => [s.id, s]));
const claimMap = Object.fromEntries((plan.claims || []).map(c => [c.id, c]));
const editorial = selected.style === 'editorial';
function tx(s) { return s == null ? '' : String(s); }
function scriptRuns(s, override = {}) {
  const pieces = tx(s).match(/[\u3000-\u303F\u3400-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF]+|[^\u3000-\u303F\u3400-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF]+/gu) || [];
  return pieces.map(v => ({ text: v, options: Object.assign({
    fontFace: /[\u3400-\u9FFF\uF900-\uFAFF]/u.test(v) ? theme.fontCJK : theme.fontLatin,
  }, override) }));
}
function put(slide, s, x, y, w, h, opts = {}) {
  const fontSize = opts.fontSize || 18;
  slide.addText(scriptRuns(s), Object.assign({ x, y, w, h, margin: 0, breakLine: false,
    color: text, fontSize, fontFace: theme.fontLatin, valign: 'mid',
    lineSpacingMultiple: 1.06, transparency: 0 }, opts));
}
function rule(slide, x, y, w, color = theme.line, weight = 1) {
  slide.addShape(pptx.ShapeType.line, { x, y, w, h: 0, line: { color, width: weight } });
}
function rect(slide, x, y, w, h, fill, line = fill) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w, h, line: {color:line, transparency:100}, fill: {color:fill}});
}
function imageInfo(assetId) {
  const a = assetMap[assetId];
  if (!a) return null;
  const fp = path.resolve(path.dirname(planFile), a.path);
  if (!fs.existsSync(fp)) return null;
  const ext = path.extname(fp).toLowerCase();
  if (!['.png','.jpg','.jpeg','.svg','.webp','.gif'].includes(ext)) return null;
  let dim;
  try {dim = imageSize(fs.readFileSync(fp));} catch (_) {return null;}
  return {path: fp, width: dim.width, height: dim.height, id: assetId};
}
function addImageFit(slide, aid, x, y, w, h) {
  const im = imageInfo(aid);
  if (!im || !im.width || !im.height) {
    console.warn('Image unavailable or unsupported:', aid);
    return false;
  }
  const scale = Math.min(w / im.width, h / im.height);
  const iw = im.width * scale, ih = im.height * scale;
  slide.addImage({path: im.path, x: x + (w-iw)/2, y: y + (h-ih)/2, w: iw, h: ih});
  return true;
}
function putBullets(slide, bullets, x, y, w, options = {}) {
  if (!bullets || !bullets.length) return;
  const h = options.height || 4.35;
  const sz = options.fontSize || 18;
  const itemHeight = Math.min(options.itemHeight || 0.82, h / bullets.length);
  bullets.slice(0, 8).forEach((b, idx) => {
    const yy = y + idx * itemHeight;
    rect(slide, x, yy + 0.18, 0.075, 0.075, accent);
    put(slide, b, x+0.22, yy, w-0.22, itemHeight-0.07, {
      fontSize: Math.max(13, bullets.length > 6 ? sz-2 : sz),
      valign:'mid', breakLine:false,
    });
  });
}
function regularHeader(slide, d) {
  slide.background = { color: background };
  put(slide, d.title, M, 0.36, 12.0, 0.61, {fontSize: editorial ? 25 : 29, bold:true, valign:'mid'});
  rule(slide, M, 1.10, 12.03, theme.line, 0.8);
  rule(slide, M, 1.10, editorial ? 0.95 : 1.8, accent, 2.0);
}
function addNotes(slide, d) {
  const refs = new Map();
  for (const sid of (d.sources || [])) {
    const s = sourceMap[sid]; if (s) refs.set(sid, `${s.file} | ${s.locator}`);
  }
  for (const aid of (d.image_ids || [])) {
    const a = assetMap[aid]; if (!a) continue;
    for (const sid of (a.source_ids || [])) {
      const source = sourceMap[sid];
      if (source) refs.set(sid, `${source.file} | ${source.locator}`);
    }
  }
  for (const cid of (d.claim_ids || [])) {
    const c = claimMap[cid]; if (!c) continue;
    for (const sid of (c.source_ids || [])) {
      const s = sourceMap[sid]; if (s) refs.set(sid, `${s.file} | ${s.locator}`);
    }
  }
  const notes = [d.notes || '', d.duration_sec ? `Suggested duration: ${d.duration_sec} seconds.` : '',
    '[Sources]', ...(Array.from(refs.values())), '[/Sources]'].filter(Boolean).join('\n');
  slide.addNotes(notes);
}
function titleSlide(slide, d) {
  slide.background = {color:background};
  const im = (d.image_ids || [])[0];
  if (im) addImageFit(slide, im, editorial?7.0:6.7, 0.7, 5.9, 5.9);
  rule(slide, M, editorial ? 4.86 : 5.05, editorial?2.0:1.5, accent, 3);
  put(slide, d.title, M, editorial?1.6:1.52, editorial?6.2:5.8, 2.0, {fontSize: editorial?35:39,bold:true,valign:'mid'});
  const sub = d.body || plan.meta.subtitle || '';
  if (sub) put(slide, sub, M, editorial?5.2:5.38, 7.0, 0.85, {fontSize:19, color:secondary});
}
function figureSlide(slide, d) {
  regularHeader(slide, d);
  const img = (d.image_ids || [])[0];
  if (editorial && (d.bullets || []).length) {
    addImageFit(slide,img,0.6,1.36,8.55,5.5);
    rule(slide, 9.34, 1.46, 0, theme.line, 1);
    putBullets(slide,d.bullets,9.5,1.75,3.2,{fontSize:16,height:4.7});
  } else {
    addImageFit(slide,img,0.77,1.33,11.85,4.82);
    if ((d.bullets || []).length) {
      const bl = d.bullets.slice(0,2).join('   |   ');
      put(slide,bl,1.0,6.26,11.45,0.55,{fontSize:17,color:secondary,align:'center'});
    } else if (d.body) {
      put(slide,d.body,1.0,6.23,11.4,0.53,{fontSize:16,color:secondary,align:'center'});
    }
  }
}
function splitSlide(slide,d) {
  regularHeader(slide,d);
  const imgs=d.image_ids||[];
  const imageOnRight = !editorial;
  if (imgs.length) {
    const xx=imageOnRight?6.65:0.75;
    addImageFit(slide,imgs[0],xx,1.43,5.9,5.12);
    const bx=imageOnRight?0.82:6.85;
    if (d.body) put(slide,d.body,bx,1.6,5.55,1.04,{fontSize:20,bold:true,valign:'top'});
    putBullets(slide,d.bullets||[],bx,2.85,5.5,{fontSize:18,height:3.54,itemHeight:0.85});
  } else {
    if (d.body) put(slide,d.body,0.82,1.52,11.6,0.8,{fontSize:23,bold:true});
    putBullets(slide,d.bullets||[],1.0,2.7,11.2,{fontSize:21,height:3.6,itemHeight:0.75});
  }
}
function comparisonSlide(slide,d) {
  regularHeader(slide,d);
  const imgs=d.image_ids||[];
  const xLeft=0.73,xRight=6.83, cw=5.74;
  if (imgs.length>=2) {
    addImageFit(slide,imgs[0],xLeft,1.57,cw,4.75);
    addImageFit(slide,imgs[1],xRight,1.57,cw,4.75);
    rule(slide,6.68,1.55,0,theme.line,0.6);
    const bb=d.bullets||[];
    if(bb[0]) put(slide,bb[0],xLeft,6.4,cw,0.45,{fontSize:16,color:secondary,align:'center'});
    if(bb[1]) put(slide,bb[1],xRight,6.4,cw,0.45,{fontSize:16,color:secondary,align:'center'});
  } else {
    const bb=d.bullets||[]; const half=Math.ceil(bb.length/2);
    const c1=bb.slice(0,half),c2=bb.slice(half);
    if(editorial) {
      put(slide,d.body||'Comparison',0.87,1.52,11.65,0.7,{fontSize:19,color:secondary});
      rule(slide,6.67,2.45,0,theme.line,0.7);
      putBullets(slide,c1,0.93,2.58,5.45,{fontSize:19,height:3.8});
      putBullets(slide,c2,7.0,2.58,5.4,{fontSize:19,height:3.8});
    } else {
      putBullets(slide,c1,0.94,1.7,5.3,{fontSize:20,height:4.7});
      putBullets(slide,c2,6.9,1.7,5.3,{fontSize:20,height:4.7});
      rule(slide,6.63,1.75,0,theme.line,0.6);
      if(d.body) put(slide,d.body,1.0,6.45,11.1,0.45,{fontSize:17,color:secondary});
    }
  }
}
function processSlide(slide,d) {
  regularHeader(slide,d);
  const steps=(d.bullets||[]).slice(0,6);
  if(!steps.length) {if(d.body)put(slide,d.body,1.0,2.4,11.1,2.0,{fontSize:25}); return;}
  if(editorial) {
    const gap=0.25;const w=(11.8-gap*(steps.length-1))/steps.length;
    steps.forEach((t,i)=>{
      const x=0.8+i*(w+gap);
      put(slide,String(i+1).padStart(2,'0'),x,1.8,w,0.9,{fontSize:38,color:accent,bold:true});
      rule(slide,x,2.73,w,theme.line,1.1);
      put(slide,t,x,3.03,w,2.5,{fontSize:steps.length>4?15:18,valign:'top'});
    });
    if(d.body)put(slide,d.body,0.83,6.13,11.65,0.65,{fontSize:17,color:secondary});
  } else {
    steps.forEach((t,i)=>{
      const y=1.43+i*(4.7/steps.length);
      put(slide,String(i+1).padStart(2,'0'),1.15,y,1.0,0.49,{fontSize:23,color:accent,bold:true});
      put(slide,t,2.35,y,9.7,0.53,{fontSize:20,bold:i===0});
      if(i<steps.length-1)rule(slide,1.12,y+0.63,11.1,theme.line,0.55);
    });
    if(d.body)put(slide,d.body,1.15,6.48,11.1,0.43,{fontSize:15,color:secondary});
  }
}
function tableSlide(slide,d) {
  regularHeader(slide,d);
  const table=d.table||{headers:[],rows:[]};
  if(!table.headers.length) return;
  const rows=[table.headers,...table.rows];
  const fsiz=Math.max(11,Math.min(17,17-table.headers.length*0.4,20-rows.length*0.6));
  slide.addTable(rows,{x:0.74,y:1.55,w:11.84,h:Math.min(4.85,rows.length*0.5+0.3),
    colW:Array(table.headers.length).fill(11.84/table.headers.length),
    fontFace:theme.fontLatin,fontSize:fsiz,color:text,
    margin:[0.12,0.12,0.12,0.12],
    border:{type:'solid',color:theme.line,pt:0.5},
    autoFit:false,breakLine:false,
    rowH:Math.max(0.38,Math.min(0.65,4.8/rows.length)),
    valign:'mid',
    bold:false,
    fill:{color:background},
    autoPage:false,
  });
  if(d.body)put(slide,d.body,0.76,6.58,11.8,0.38,{fontSize:15,color:secondary});
}
function summarySlide(slide,d) {
  regularHeader(slide,d);
  const bullets=d.bullets||[];
  if(editorial) {
    if(d.body)put(slide,d.body,0.87,1.6,11.7,1.15,{fontSize:24,bold:true});
    putBullets(slide,bullets,1.05,3.05,11.2,{fontSize:21,height:3.1,itemHeight:0.9});
  } else {
    if(d.body)put(slide,d.body,0.89,1.55,11.5,1.22,{fontSize:27,bold:true});
    bullets.slice(0,4).forEach((b,i)=>{
      const y=3.0+i*0.78;
      put(slide,String(i+1).padStart(2,'0'),0.96,y,0.85,0.45,{fontSize:22,color:accent,bold:true});
      put(slide,b,1.91,y,10.55,0.56,{fontSize:20});
    });
  }
}
for (const [index,original] of plan.slides.entries()) {
  const d = Object.assign({}, original);
  if (d.variant_layouts && d.variant_layouts[arg.variant]) {
    d.layout = d.variant_layouts[arg.variant];
  }
  const slide=pptx.addSlide();
  switch(d.layout) {
    case 'title':titleSlide(slide,d);break;
    case 'figure':figureSlide(slide,d);break;
    case 'split':splitSlide(slide,d);break;
    case 'comparison':comparisonSlide(slide,d);break;
    case 'process':processSlide(slide,d);break;
    case 'table':tableSlide(slide,d);break;
    case 'summary':summarySlide(slide,d);break;
    default: regularHeader(slide,d); if(d.body)put(slide,d.body,0.8,2.0,11.6,2.5);
  }
  addNotes(slide,d);
}
const dest=path.resolve(arg.output);
fs.mkdirSync(path.dirname(dest),{recursive:true});
pptx.writeFile({fileName:dest}).then(()=>console.log(JSON.stringify({output:dest,variant:arg.variant,slides:plan.slides.length})))
  .catch(e=>die(e && e.stack || e));
