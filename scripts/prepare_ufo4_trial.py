"""Full-canvas mask assets for the visually inspected UFO 4 trial; not a template for other photos."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
W=H=3102
S=3
A=ROOT/'.retouch/assets/ufo4';A.mkdir(parents=True,exist_ok=True)
def shape(draw):
 im=Image.new('L',(W*S,H*S));d=ImageDraw.Draw(im);draw(d);return np.array(im.resize((W,H),Image.Resampling.LANCZOS))
def polygon(pts):return shape(lambda d:d.polygon([(x*S,y*S) for x,y in pts],fill=255))
def ellipse(b):return shape(lambda d:d.ellipse(tuple(v*S for v in b),fill=255))
def bezier(start,segments):
 pts=[start];p=np.array(start,dtype=float)
 for c1,c2,end in segments:
  a,b,q=map(lambda x:np.array(x,dtype=float),(c1,c2,end))
  for t in np.linspace(0,1,100)[1:]:pts.append(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*q))
  p=q
 return polygon(pts)
def union(*m):return np.maximum.reduce(m)
def sub(a,b):return np.clip(a.astype(float)-b.astype(float),0,255).astype(np.uint8)
def intersect(a,b):return np.minimum(a,b)
def save(name,m):
 p=A/(name+'.bin');m.tofile(p);Image.fromarray(m).save(A/(name+'.png'));return str(p)
a=np.fromfile(ROOT/'.retouch/inspection/UFO4-auto-full.bin',np.uint8).reshape(H,W)
# Trace the two photographed cables to their occlusion by the backing card. Red overpainting is retained for review.
upper=polygon([(1690,944),(1750,911),(1850,861),(1950,819),(2050,788),(2150,759),(2250,737),(2370,715),(2358,777),(2245,797),(2140,818),(2040,850),(1940,886),(1840,932),(1780,958)])
lower=polygon([(1785,963),(1850,930),(1950,890),(2050,854),(2150,824),(2245,800),(2358,775),(2349,825),(2240,850),(2140,878),(2040,910),(1940,948),(1870,978)])
wires=union(upper,lower)
subject=union(a,wires)
# Remove a tiny detached selection speck below the left edge; preserve the real continuous boundary.
subject[2200:2240,920:975]=np.minimum(subject[2200:2240,920:975],a[2200:2240,920:975])
face=ellipse((68,1458,3032,2230))
lens=bezier((1546,1502),[((2300,1484),(2858,1630),(2865,1815)),((2878,2017),(2320,2186),(1550,2192)),((792,2191),(235,2032),(237,1830)),((227,1645),(793,1513),(1546,1502))])
sensor=bezier((1548,1892),[((1720,1893),(1807,1921),(1815,1990)),((1821,2040),(1765,2110),(1645,2143)),((1571,2173),(1470,2169),(1390,2134)),((1314,2100),(1287,2046),(1291,1995)),((1290,1930),(1360,1893),(1548,1892))])
sensor=union(sensor,ellipse((1450,1848,1667,1940)))
controls=ellipse((1393,945,1705,1223))
labels=union(polygon([(1753,967),(1852,982),(1856,1110),(1758,1084)]),polygon([(1016,1050),(1075,1039),(1077,1195),(1005,1239)]),polygon([(2023,1051),(2071,1100),(2087,1268),(2034,1236)]))
hardware=ellipse((1378,608,1715,953))
hardware=intersect(hardware,subject)
for b in [(1124,1204,1175,1268),(1926,1202,1984,1268),(1281,1860,1344,1937),(1752,1868,1830,1943),(541,1590,608,1640),(2468,1578,2542,1631),(245,1855,306,1901),(2735,1860,2805,1908)]:hardware=union(hardware,ellipse(b))
hardware=union(hardware,ellipse((1186,1762,1911,1916)))
hardware=sub(hardware,sensor)
# A color-based selection of the visible warm LED chips, confined to the lens. LED colors are not changed.
rgb=np.array(Image.open(ROOT/'.retouch/inspection/UFO4-source.png').convert('RGB')).astype(np.int16)
led=((rgb[:,:,0]-rgb[:,:,2]>12)&(rgb[:,:,1]-rgb[:,:,2]>8)&(rgb[:,:,1]>90)).astype(np.uint8)*255
led=intersect(led,lens);led=intersect(led,ellipse((363,1553,2704,2151)));led=sub(led,union(sensor,hardware));led=sub(led,ellipse((1110,1780,2000,2250)))
led=np.array(Image.fromarray(led).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.45)))
rim=sub(face,lens)
parts={'Housing':sub(subject,union(face,hardware,labels,controls,wires)), 'Rim':rim,'Lens':sub(lens,union(sensor,hardware,led)),'LEDs':led,'Sensor':sensor,'Controls':controls,'Label':labels,'Hardware':hardware,'Wires':wires}
components=[{'name':name,'maskPath':save(name,intersect(m,subject))} for name,m in parts.items()]
subjectPath=save('Subject',subject)
# Small scratches on the matte control cap: sample neighboring undamaged cap pixels. Texture elsewhere is preserved.
cleanup=[{'method': 'clone', 'source': [1420, 1043, 1434, 1067], 'destination': [1441, 1043], 'feather': 1}, {'method': 'clone', 'source': [1480, 1049, 1492, 1071], 'destination': [1454, 1049], 'feather': 1}, {'method': 'clone', 'source': [1480, 1032, 1492, 1045], 'destination': [1463, 1032], 'feather': 1}, {'method': 'clone', 'source': [1472, 1143, 1535, 1176], 'destination': [1472, 1105], 'feather': 3}]
review=[{'area':'Photographed cables','bounds':[1900,705,2375,935],'note':'Two flattened red annotations cover cable pixels. Visible cable shape is retained; red overpainting is left for human review. The backing card also obscures cable ends.'}, {'area':'Mounting ring','bounds':[1380,610,1716,946],'note':'Cast metal texture and worn finish retained; these may be real surface characteristics.'}, {'area':'LEDs and clear lens','bounds':[240,1500,2870,2195],'note':'LED masks isolate visible warm chips beneath the translucent lens. Review mask overlap where the lens refracts diode light; original diode color is unchanged.'}]
base=ROOT/'outputs/UFO 4 - Editable Cleanup Trial v4'
job={'action':'apply','sourcePath':str(ROOT/'UFO  4 Unfinished.psd'),'name':'UFO 4 - Editable Cleanup Trial v4','subjectMaskPath':subjectPath,'components':components,'cleanup':cleanup,'review':review,'outputPath':str(base)+'.psd','whitePreviewPath':str(base)+' - White.png','transparentPreviewPath':str(base)+' - Transparent.png'}
(A/'apply-spec.json').write_text(json.dumps(job,indent=2))
print(json.dumps({'spec':str(A/'apply-spec.json'),'components':list(parts),'cleanupRegions':len(cleanup)},indent=2))
