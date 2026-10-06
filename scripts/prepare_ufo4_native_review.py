"""UFO 4 trial only: refine saved Photoshop selections; never retouch RGB here.

Native selection commands and their outcomes are retained in .retouch/queue
and .retouch/results. The rim needs a localized seam correction after Object
Selection selected the lens and Quick Selection crossed material boundaries.
"""
from pathlib import Path
from collections import deque
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / '.retouch/assets/ufo4-native-v6'
OLD = ROOT / '.retouch/assets/ufo4-refined-v5'
W = H = 3102

def load(name, folder=A):
    return np.fromfile(folder / (name + '.bin'), np.uint8).reshape(H, W)

def union(*m):
    return np.maximum.reduce(m)

def sub(a, b):
    return np.maximum(a.astype(np.int16) - b.astype(np.int16), 0).astype(np.uint8)

def save(name, m):
    m.tofile(A / (name + '.bin'))
    Image.fromarray(m).save(A / (name + '.png'))
    return str(A / (name + '.bin'))

def polygon(points):
    s = 3
    im = Image.new('L', (W*s, H*s))
    ImageDraw.Draw(im).polygon([(x*s, y*s) for x, y in points], fill=255)
    return np.asarray(im.resize((W, H), Image.Resampling.LANCZOS)).copy()

subject = load('Subject', OLD)
lens_total = load('Lens-refined')
sensor = load('Sensor-refined')
controls = load('Controls-object')
label = load('CCT Label-complete')
hub = load('Hub')

# These two transparent bosses were incorrectly included in the native hub
# selection. Correct those local occlusions; retain the selected hub contour.
bosses = union(
    polygon([(1273,1888),(1297,1863),(1318,1860),(1339,1864),
             (1340,1886),(1350,1895),(1347,1908),(1337,1919),
             (1287,1919),(1272,1905)]),
    polygon([(1760,1888),(1778,1864),(1802,1860),(1818,1865),
             (1819,1886),(1829,1896),(1827,1908),(1813,1919),
             (1775,1919),(1758,1905)]))
hub = sub(hub, bosses)

# Thirteen independently sampled, locally constrained native screw selections.
# Their shadowed and partly occluded portions need the already-reviewed local
# contour repairs. Preserve that precision, rather than accepting wand spots.
native_screws = union(*[np.fromfile(p,np.uint8).reshape(H,W)
                       for p in sorted(A.glob('screw-*.bin'))])
save('Hardware-native-start', native_screws)
hardware = load('Hardware', OLD).copy()

# Correct the missed rim/housing seam only. The previous rim boundary is a
# local search seed; the new boundary follows the photographed gray lip.
# Bottom and side silhouettes come from the approved native subject mask.
old_rim = load('Rim', OLD)
seed = np.full(W, np.nan)
for x in range(W):
    ys = np.flatnonzero(old_rim[:,x] > 127)
    if len(ys): seed[x] = ys[0]
valid = np.flatnonzero(np.isfinite(seed))
seed = np.interp(np.arange(W), valid, seed[valid])
rgb_image = Image.open(ROOT/'.retouch/inspection/UFO4-source.png').convert('RGB')
rgb = np.asarray(rgb_image).astype(np.int16)
gray = np.asarray(rgb_image.convert('L').filter(ImageFilter.GaussianBlur(.7))).astype(float)
gradient = gray[2:] - gray[:-2]
top = seed.copy()
for x in range(85, 3020):
    center = int(seed[x]); ys = np.arange(max(1,center-11), min(H-1,center+12))
    scores = gradient[ys-1,x] - .8*np.abs(ys-center)
    top[x] = ys[np.argmax(scores)]
top[85:3020] = np.median(np.lib.stride_tricks.sliding_window_view(
    np.pad(top[85:3020],(10,10),mode='edge'),21),axis=1)
top[85:3020] = np.convolve(np.pad(top[85:3020],(2,2),mode='edge'),
                           np.ones(5)/5,mode='valid')
rows = np.arange(H)[:,None]
face = np.clip((rows - top[None,:] + .5)*255,0,255).astype(np.uint8)
face = np.minimum(face,subject)
raw_rim = sub(face,lens_total)

# Preserve native perforation contours and reject dark outer-frame spill.
# A small erosion separates narrow color-selection leaks; expansion recovers
# the original native edge pixels of accepted enclosed slot components.
native_holes = load('Rim-openings')
window = (slice(1380,2250),slice(45,3055))
candidate = ((native_holes[window]>127)&(raw_rim[window]>127)).astype(np.uint8)*255
eroded = np.asarray(Image.fromarray(candidate).filter(ImageFilter.MinFilter(3))).copy()
visited = np.zeros(eroded.shape,bool)
accepted = np.zeros_like(eroded)
holes = []
for yy,xx in zip(*np.nonzero(eroded)):
    if visited[yy,xx]: continue
    todo=deque([(int(yy),int(xx))]);visited[yy,xx]=True;points=[]
    while todo:
        y,x=todo.popleft();points.append((y,x))
        for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
            if 0<=ny<eroded.shape[0] and 0<=nx<eroded.shape[1] and eroded[ny,nx] and not visited[ny,nx]:
                visited[ny,nx]=True;todo.append((ny,nx))
    ys,xs=zip(*points);bw=max(xs)-min(xs)+1;bh=max(ys)-min(ys)+1
    if 80<=len(points) and 24<=bw<=280 and 6<=bh<=150 and len(points)/(bw*bh)>.3:
        for y,x in points:accepted[y,x]=255
        holes.append([min(xs)+45,min(ys)+1380,max(xs)+46,max(ys)+1381])
hole_support=np.asarray(Image.fromarray(accepted).filter(ImageFilter.MaxFilter(3)))
hole_mask=np.zeros((H,W),np.uint8)
hole_mask[window]=np.minimum(hole_support,native_holes[window])
# Some shadowed slot selections connect to the neighboring dark frame.
# Constrain those already-selected native pixels to the local slot regions;
# these boxes scope color selections rather than define the hole contours.
slot_regions=[
    (840,1490,1055,1555),(615,1530,825,1595),(435,1570,625,1640),
    (1778,1460,1985,1520),(2005,1480,2220,1550),
    (2225,1515,2435,1600),(2430,1550,2605,1640),
    (95,1892,248,1940),(130,1946,300,1995),(205,1997,400,2045),
    (315,2046,520,2090),(455,2088,675,2129),(630,2120,865,2160),
    (840,2151,1080,2188),(1060,2172,1295,2213),
    (2280,2120,2480,2170),(2120,2150,2325,2198),
]
for x,y,X,Y in slot_regions:
    scoped=np.minimum(native_holes[y:Y,x:X],raw_rim[y:Y,x:X])
    hole_mask[y:Y,x:X]=np.maximum(hole_mask[y:Y,x:X],scoped)
save('Perforation corrections',hole_mask)
rim=sub(raw_rim,hole_mask)

# The sampled native Lab range isolates bright warm chips. Remove very faint
# color-range tails and keep antialiased boundaries, without selecting white
# lens ridges or extending the chips into their reflections.
led=load('LEDs-range-14')
led=np.clip((led.astype(float)-48)*255/112,0,255).astype(np.uint8)
warm=(rgb[:,:,0]-rgb[:,:,2]>=13)&(rgb[:,:,1]-rgb[:,:,2]>=9)&(rgb[:,:,1]>130)
led=np.where(warm,led,0).astype(np.uint8)
led=np.minimum(led,lens_total)
led=sub(led,union(hub,sensor,hardware))
led[:1600]=0;led[2120:]=0;led[:,:340]=0;led[:,2760:]=0

# Native upper housing, front band and hub selections were inspected. Fill
# missed band ends within the photographed subject above the corrected seam.
housing=sub(union(sub(subject,face),hub),union(label,controls,sensor,hardware,led))
lens=sub(lens_total,union(hub,sensor,hardware,led))
parts={'Housing':housing,'Rim':sub(rim,hardware),'Lens':lens,'LEDs':led,
       'Sensor':sub(sensor,hardware),'Controls':controls,
       'CCT Label':label,'Hardware':hardware}
components=[{'name':n,'maskPath':save(n,np.minimum(m,subject))} for n,m in parts.items()]

job=json.loads((OLD/'apply-spec.json').read_text())
base=ROOT/'outputs/UFO 4 - Native Selection Trial v6'
job.update(name=base.name,components=components,
    outputPath=str(base)+'.psd',whitePreviewPath=str(base)+' - White.png',
    transparentPreviewPath=str(base)+' - Transparent.png',
    whipPreviewPath=str(base)+' - Whip.png',
    whipVerifiedPreviewPath=str(base)+' - Whip Reopened.png')
job['review']=[
    {'area':'All component masks','bounds':[65,600,3045,2240],
     'note':'Native Photoshop component selections replaced the geometry-based starts. Review every independently editable CC mask; cleanup and RT/whip appearance intentionally match the approved v5.'},
    {'area':'Rim and housing seam','bounds':[65,1390,3045,2240],
     'note':'Object Selection selected the lens instead of the rim; Quick Selection crossed material boundaries. Native Magic Wand material/opening selections needed a localized seam correction and enclosed-slot refinement. Review the dark lower rim openings closely.'},
    {'area':'Hardware and clear bosses','bounds':[250,900,2865,2185],
     'note':'Thirteen native screw selections were locally constrained. Shadowed/occluded portions retain the previously reviewed contour repairs. Clear plastic bosses were removed from the native black-hub selection and belong to Lens.'},
    {'area':'Visible LED chips','bounds':[340,1600,2760,2120],
     'note':'Native Color Range samples the bright warm chip shades. The ordinary Yellows preset and an initial lens-color sample were rejected. Review refracted chip boundaries and partial highlights.'},
]
(A/'apply-spec.json').write_text(json.dumps(job,indent=2))
stats={n:{'selectedPixels':int(np.count_nonzero(m>127)),
          'changedMaskPixelsVsV5':int(np.count_nonzero(m!=load(n,OLD)))}
       for n,m in parts.items()}
stats['rimOpenings']={'count':len(holes),'bounds':holes}
stats['hardwareNativeCoveragePixels']=int(np.count_nonzero(native_screws>127))
(A/'mask-stats.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=2))

# Full-resolution inspection crops; these are evidence, never retouched RGB.
photo=Image.open(ROOT/'outputs/UFO 4 - Gold Standard Candidate v5 - White.png').convert('RGB')
arr=np.asarray(photo).astype(float)
crops={'Housing':(970,590,2140,1485),'Rim':(70,1400,3040,2245),
       'Lens':(195,1480,2915,2200),'LEDs':(350,1630,1250,2070),
       'Sensor':(1260,1810,1840,2190),'Controls':(1370,915,1740,1255),
       'CCT Label':(1725,935,1885,1130),'Hardware':(1120,1190,1195,1275)}
for n,b in crops.items():
    m=load(n);t=m[:,:,None]/255*.45
    overlay=Image.fromarray((arr*(1-t)+np.array([255,40,30])*t).astype(np.uint8)).crop(b)
    if n in ['Lens','Rim']:overlay=overlay.resize((overlay.width//2,overlay.height//2))
    overlay.save(A/(n+'-final-inspect.png'))
