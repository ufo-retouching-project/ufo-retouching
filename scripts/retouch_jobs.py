#!/usr/bin/env python3
"""Queue reviewed Photoshop work. Photoshop + the loaded UXP plugin execute the jobs."""
from pathlib import Path
import argparse, hashlib, json, struct, time, uuid
ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/'.retouch/queue';RESULTS=ROOT/'.retouch/results'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def inside(s):
 p=Path(s).expanduser().resolve()
 if ROOT not in p.parents:raise ValueError('Path must stay inside this project: '+str(p))
 return p
def submit(j):
 src=inside(j['sourcePath'])
 if not src.is_file() or src.suffix.lower()!='.psd':raise ValueError('Expected an existing source PSD')
 with src.open('rb') as f:header=f.read(26)
 if len(header)!=26:raise ValueError('Invalid PSD header')
 sig,version,_,channels,height,width,depth,mode=struct.unpack('>4sH6sHIIHH',header)
 if sig!=b'8BPS' or version!=1:raise ValueError('Expected a standard PSD')
 if j['action']=='apply' and (mode!=3 or depth not in [8,16]):raise ValueError('First version handles 8-bit or 16-bit RGB PSDs')
 j['sourcePath']=str(src);j['sourceSha256']=digest(src)
 output_keys=['outputPath','previewPath','selectionPath','whitePreviewPath','transparentPreviewPath','whipPreviewPath','whipVerifiedPreviewPath']
 outputs=[str(inside(j[k])) for k in output_keys if k in j]
 if len(set(outputs))!=len(outputs):raise ValueError('Output paths must be distinct')
 for k in output_keys:
  if k in j:
   p=inside(j[k]);p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists():raise ValueError('Refusing to overwrite '+str(p))
 if j['action'] in ('apply','layoutApply'):
  if not j.get('components'):raise ValueError('Reviewed component masks are required')
  names=[c['name'] for c in j['components']]
  if len(set(names))!=len(names):raise ValueError('Component names must be unique')
  mask_size=width*height
  if j['action']=='layoutApply':
   side=j.get('canvasSize')
   if not isinstance(side,int) or side<2000:raise ValueError('Layout canvas must be a square of at least 2000 px')
   mask_size=side*side
   pixels=inside(j.get('pixelsPath',''))
   if not pixels.is_file() or pixels.suffix.lower()!='.png':raise ValueError('A transformed RGBA PNG pixel asset is required')
   with pixels.open('rb') as f:png=f.read(26)
   if len(png)<26 or png[:8]!=b'\x89PNG\r\n\x1a\n' or png[12:16]!=b'IHDR':raise ValueError('Invalid transformed PNG pixel asset')
   pwidth,pheight=struct.unpack('>II',png[16:24])
   if (pwidth,pheight)!=(side,side) or png[25] not in (2,6):raise ValueError('Transformed pixel asset must be full-canvas RGB or RGBA at canvasSize')
  for m in [j['subjectMaskPath']]+[c['maskPath'] for c in j['components']]:
   p=inside(m)
   if not p.is_file() or p.stat().st_size!=mask_size:raise ValueError('Missing or incorrect full-canvas mask: '+str(p))
  for patch in j.get('cleanup',[]) if j['action']=='apply' else []:
   if patch.get('maskPath'):
    p=inside(patch['maskPath'])
    if not p.is_file() or p.stat().st_size!=width*height:raise ValueError('Missing or incorrect clone mask')
   if patch.get('destinationBounds'):
    b=patch['destinationBounds'];s=patch['source'];d=patch['destination']
    if len(b)!=4 or any(not isinstance(v,int) for v in b) or b[:2]!=d or not (0<=b[0]<b[2]<=width and 0<=b[1]<b[3]<=height) or b[3]-b[1]!=s[3]-s[1] or (not patch.get('repeatX') and b[2]-b[0]!=s[2]-s[0]):raise ValueError('Invalid clone destination bounds')
  if 'whip' in j:
   whip=j['whip']
   assets={'black':'Black_Whip copy.psd','white':'White_Whip copy.psd'}
   if whip.get('color') not in assets:raise ValueError('Whip color must be black or white')
   import math
   for k in ['width','left','top','angle']:
    value=whip.get(k,0 if k=='angle' else None)
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):raise ValueError('Invalid whip '+k)
   if whip['width']<=0 or whip['left']<0 or whip['top']<0:raise ValueError('Invalid whip placement')
   if not j.get('whipPreviewPath') or not j.get('whipVerifiedPreviewPath'):raise ValueError('Whip inspection paths are required')
   asset=ROOT/assets[whip['color']]
   if not asset.is_file():raise ValueError('Missing whip asset')
   j['whipSourcePath']=str(asset);j['whipSourceSha256']=digest(asset)
 name=time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
 QUEUE.mkdir(parents=True,exist_ok=True);tmp=QUEUE/(name+'.tmp');tmp.write_text(json.dumps(j,indent=2));tmp.rename(QUEUE/name)
 return name
ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
sub.add_parser('list');p=sub.add_parser('inspect');p.add_argument('source');p=sub.add_parser('apply');p.add_argument('spec');p=sub.add_parser('status');p.add_argument('job',nargs='?');p=sub.add_parser('wait');p.add_argument('job');p.add_argument('--seconds',type=int,default=20)
a=ap.parse_args()
if a.command=='list':
 done=set()
 for f in RESULTS.glob('*.json'):
  r=json.loads(f.read_text())
  if r.get('status')=='complete' and r.get('outputPath') and ROOT/'outputs' in Path(r['outputPath']).resolve().parents and not r.get('qaStatus','').startswith('failed'):
   q=QUEUE/f.name
   if q.exists():done.add(json.loads(q.read_text()).get('sourceSha256'))
 print(json.dumps([{'file':str(p),'processed':digest(p) in done} for p in sorted((ROOT/'input').glob('*')) if p.suffix.lower()=='.psd'],indent=2))
elif a.command=='inspect':
 src=inside(a.source);key=uuid.uuid4().hex[:10];base=ROOT/'.retouch/inspection'/key
 print(submit({'action':'inspect','sourcePath':str(src),'previewPath':str(base)+'.png','selectionPath':str(base)+'.bin'}))
elif a.command=='apply':print(submit(json.loads(inside(a.spec).read_text())))
elif a.command=='wait':
 stop=time.monotonic()+min(max(a.seconds,1),60);p=RESULTS/Path(a.job).name
 while not p.exists() and time.monotonic()<stop:time.sleep(.5)
 print(p.read_text() if p.exists() else json.dumps({'status':'pending','job':a.job}))
else:
 files=[RESULTS/Path(a.job).name] if a.job else sorted(RESULTS.glob('*.json'))
 for f in files:print(f.read_text() if f.exists() else json.dumps({'status':'pending','job':f.name}))
