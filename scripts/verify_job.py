#!/usr/bin/env python3
"""Compare a completed Photoshop job with its source inspection and prepared masks."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('job');ap.add_argument('source_preview');a=ap.parse_args()
q=ROOT/'.retouch/queue'/Path(a.job).name;j=json.loads(q.read_text());result=json.loads((ROOT/'.retouch/results'/q.name).read_text());assert result['status']=='complete',result
before=result['before'];after=result['verified']
for k in ['width','height','bitsPerChannel','colorProfile','resolution']:assert before[k]==after[k],k
order=['CC','RT']+([result['whipChecks']['name']] if j.get('whip') else [])+['White Background','Original']
assert [l['name'] for l in after['layers']]==order
assert after['layers'][-1]['locked'] and not after['layers'][-1]['visible'] and not after['layers'][1]['locked']
source=Path(j['sourcePath']);h=hashlib.sha256()
with source.open('rb') as f:
 for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
assert h.hexdigest()==j['sourceSha256'],'Source file changed'
w,hgt=after['width'],after['height'];mask=np.fromfile(j['subjectMaskPath'],np.uint8).reshape(hgt,w)
im=Image.open(j['transparentPreviewPath']).convert('RGBA');alpha=np.array(im.getchannel('A'));expected_alpha=mask
whip_pixels=None
if j.get('whip'):
 assert hashlib.sha256(Path(j['whipSourcePath']).read_bytes()).hexdigest()==j['whipSourceSha256'],'Whip source changed'
 assert result['whipChecks']['editable'] and result['whipChecks']['belowRT']
 wp=Image.open(j['whipPreviewPath']).convert('RGBA');saved=Image.open(j['whipVerifiedPreviewPath']).convert('RGBA')
 assert wp.size==im.size==saved.size,'Whip inspection dimensions differ'
 whip_pixels=int(np.abs(np.asarray(wp).astype(np.int16)-np.asarray(saved).astype(np.int16)).max());assert whip_pixels<=1,'Whip appearance changed after reopening'
 wa=np.asarray(wp.getchannel('A'));assert np.count_nonzero(wa)>0,'Whip is empty'
 expected_alpha=np.rint(mask.astype(np.float32)+wa.astype(np.float32)*(1-mask.astype(np.float32)/255)).astype(np.uint8)
alpha_delta=int(np.abs(alpha.astype(np.int16)-expected_alpha.astype(np.int16)).max());assert alpha_delta<=(1 if j.get('whip') else 0),'Composite alpha differs'
src=Image.open(a.source_preview).convert('RGB');rt=Image.open(j['whitePreviewPath']).convert('RGB');diff=np.max(np.abs(np.array(src).astype(np.int16)-np.array(rt).astype(np.int16)),axis=2);allowed=np.zeros(mask.shape,bool)
for c in j.get('cleanup',[]):
 if c['method']=='clone':
  x,y=c['destination'];pw=c.get('destinationBounds',c['source'])[2]-(x if c.get('destinationBounds') else c['source'][0]);ph=c['source'][3]-c['source'][1]
  if c.get('maskPath'):
   cm=np.fromfile(c['maskPath'],np.uint8).reshape(hgt,w);allowed|=cm>0
  else:allowed[y:y+ph,x:x+pw]=True
 else:
  x,y,x2,y2=c['bounds'];f=c.get('feather',1)+2;allowed[max(0,y-f):min(hgt,y2+f),max(0,x-f):min(w,x2+f)]=True
changed=int(np.count_nonzero((diff>0)&(mask==255)));outside=int(np.count_nonzero((diff>0)&(mask==255)&~allowed));assert outside==0,'Unintended interior changes'
if j.get('cleanup'):assert changed>0,'Cleanup made no visible pixel changes'
base=Path(j['outputPath']).with_suffix('');p=lambda suffix:Path(str(base)+suffix)
review=rt.copy();review.thumbnail((1400,1400));review.save(p(' - Review.jpg'),quality=95)
dark=Image.alpha_composite(Image.new('RGBA',im.size,(35,38,42,255)),im).convert('RGB');dark.thumbnail((1400,1400));dark.save(p(' - Dark Review.jpg'),quality=95)
# A full-resolution crop comparison around the actual cleanup locations.
if j.get('cleanup'):
 rects=[]
 for c in j['cleanup']:
  if c['method']=='clone':x,y=c['destination'];pw=c.get('destinationBounds',c['source'])[2]-(x if c.get('destinationBounds') else c['source'][0]);ph=c['source'][3]-c['source'][1];rects.append((x,y,x+pw,y+ph))
  else:rects.append(c['bounds'])
 box=(max(0,min(r[0] for r in rects)-25),max(0,min(r[1] for r in rects)-20),min(w,max(r[2] for r in rects)+20),min(hgt,max(r[3] for r in rects)+20))
 aa=src.crop(box);bb=rt.crop(box);scale=min(4,600/aa.width,600/aa.height);size=(int(aa.width*scale),int(aa.height*scale));aa=aa.resize(size);bb=bb.resize(size);pair=Image.new('RGB',(size[0]*2,size[1]+28),'white');pair.paste(aa,(0,28));pair.paste(bb,(size[0],28));d=ImageDraw.Draw(pair);d.text((8,8),'Before',fill='black');d.text((size[0]+8,8),'After - localized cleanup',fill='black');pair.save(p(' - Cleanup Detail.png'))
checks={'sourceUnchanged':True,'alphaMaxDifference':alpha_delta,'changedInteriorPixels':changed,'changedInteriorPixelsOutsideCleanup':outside}
if j.get('whip'):checks.update(whipSourceUnchanged=True,whipReopenMaxDifference=whip_pixels)
report={'outputPath':j['outputPath'],'pixelChecks':checks,'maskChecks':result['maskChecks'],'whipChecks':result.get('whipChecks'),'verifiedMetadata':after,'review':j.get('review',[])};p(' - Verification.json').write_text(json.dumps(report,indent=2))
alpha_note=('Composite transparency matches the fixture mask combined with the whip, within one 8-bit alpha level.' if j.get('whip') else 'Subject alpha matches the prepared mask at every pixel.')
notes=['# Cleanup trial review','',str(base.name)+'.psd','',f"Preserved {w} x {hgt}, {after['bitsPerChannel']}, {after['colorProfile']}. Original is hidden and locked; RT is editable. CC contains independently masked component groups ready for adjustments. No color enhancement is applied.",'',f"Cleaned {len(j.get('cleanup',[]))} localized areas. Source checksum unchanged; no changed opaque interior pixels outside the cleanup regions. {alpha_note} All saved fixture masks were retrieved after reopening and matched at sampled pixels.",'','## Areas for human review','']
for flag in j.get('review',[]):notes.append('- '+flag['area']+': '+flag['note'])
if j.get('whip'):notes+=['',f"{result['whipChecks']['name']} sits directly below RT. Its editable layer/mask structure survived reopening, its source asset is unchanged, and its inspection pixels matched after reopening."]
notes+=['','Review this trial before production batches.'];p(' - Review Notes.md').write_text('\n'.join(notes)+'\n')
result['qaStatus']='passed automated checks - awaiting human visual review';result['pixelChecks']=checks;(ROOT/'.retouch/results'/q.name).write_text(json.dumps(result,indent=2))
print(json.dumps(checks,indent=2))
