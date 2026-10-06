"""Photo-specific contours and native clone jobs for the second UFO 4 review."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
W=H=3102
S=3
A=ROOT/'.retouch/assets/ufo4-refined-v5'
A.mkdir(parents=True,exist_ok=True)
def polygon(points):
    im=Image.new('L',(W*S,H*S));ImageDraw.Draw(im).polygon([(x*S,y*S) for x,y in points],fill=255)
    return np.asarray(im.resize((W,H),Image.Resampling.LANCZOS)).copy()
def curve(start,segments):
    points=[start];p=np.array(start,float)
    for c1,c2,end in segments:
        a,b,q=map(lambda v:np.array(v,float),(c1,c2,end))
        for t in np.linspace(0,1,120)[1:]:points.append(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*q))
        p=q
    return polygon(points)
def union(*m):return np.maximum.reduce(m)
def sub(a,b):return np.clip(a.astype(np.int16)-b.astype(np.int16),0,255).astype(np.uint8)
def save(name,m):
    p=A/(name+'.bin');m.tofile(p);Image.fromarray(m).save(A/(name+'.png'));return str(p)

# Native Select Subject preserves the eye opening and excludes both loose cables.
subject=np.fromfile(ROOT/'.retouch/inspection/UFO4-auto-full.bin',np.uint8).reshape(H,W)
# Refit the sticker-side silhouettes after inspecting native-selection fraying at 400%.
left_edge=curve((1113,1005),[
    ((1078,1018),(1026,1056),(1020,1104)),((1018,1155),(1017,1205),(1013,1240)),
    ((1010,1260),(1010,1273),(1010,1276)),((1050,1276),(1090,1276),(1120,1276)),
    ((1120,1190),(1120,1080),(1120,1005)),((1118,1005),(1115,1005),(1113,1005))])
right_edge=curve((1997,1010),[
    ((2042,1025),(2080,1066),(2088,1103)),((2092,1153),(2094,1235),(2102,1276)),
    ((2060,1276),(2010,1276),(1980,1276)),((1980,1180),(1980,1080),(1980,1010)),
    ((1985,1010),(1990,1010),(1997,1010))])
subject[1006:1275,990:1119]=left_edge[1006:1275,990:1119]
subject[1011:1275,1981:2120]=right_edge[1011:1275,1981:2120]
label=polygon([(1750,958),(1856,976),(1860,1107),(1751,1088)])
controls=curve((1548,949),[
    ((1631,948),(1698,1006),(1699,1081)),((1702,1159),(1630,1218),(1550,1219)),
    ((1470,1220),(1403,1161),(1400,1088)),((1397,1010),(1459,950),(1548,949))])
sensor=curve((1548,1890),[
    ((1711,1891),(1808,1928),(1816,1991)),((1823,2051),(1759,2113),(1654,2140)),
    ((1577,2161),(1466,2159),(1395,2130)),((1326,2102),(1288,2052),(1292,1997)),
    ((1290,1938),(1386,1891),(1548,1890))])
stem=curve((1458,1850),[
    ((1489,1841),(1626,1841),(1659,1851)),((1673,1867),(1667,1887),(1668,1907)),
    ((1607,1900),(1513,1900),(1447,1911)),((1444,1886),(1444,1868),(1458,1850))])
sensor=union(sensor,stem)

# Trace screw heads, their occluded edges, and the two knurled screws. No mounting eye or plastic bosses.
screws={
    'mount-fastener':[(1523,923),(1526,916),(1532,911),(1540,907),(1548,905),(1556,907),(1565,912),(1571,918),(1575,925),(1562,923),(1546,922),(1532,923)],
    'left-knurled':[(1135,1218),(1139,1213),(1148,1209),(1162,1207),(1178,1206),(1176,1221),(1171,1237),(1166,1246),(1161,1253),(1152,1258),(1139,1259),(1135,1249),(1134,1239)],
    'right-knurled':[(1924,1205),(1939,1206),(1949,1210),(1957,1215),(1961,1221),(1961,1244),(1959,1256),(1952,1255),(1943,1252),(1939,1246),(1935,1236),(1930,1220)],
    'sensor-left':[(1289,1898),(1296,1893),(1307,1890),(1321,1889),(1333,1892),(1340,1898),(1341,1904),(1336,1910),(1328,1913),(1317,1918),(1311,1917),(1301,1912),(1295,1907)],
    'sensor-right':[(1769,1899),(1774,1894),(1786,1890),(1799,1889),(1811,1892),(1818,1897),(1820,1904),(1813,1911),(1805,1915),(1794,1918),(1786,1914),(1777,1909)],
    'rim-top-left':[(544,1620),(554,1616),(568,1612),(584,1608),(594,1608),(599,1612),(594,1619),(585,1626),(574,1631),(568,1633),(558,1628),(549,1625)],
    'rim-top-center':[(1515,1500),(1561,1500),(1558,1504),(1550,1507),(1543,1510),(1536,1511),(1530,1509),(1522,1505)],
    'rim-top-right':[(2477,1607),(2485,1606),(2498,1609),(2511,1614),(2523,1618),(2530,1621),(2522,1625),(2512,1625),(2504,1624),(2496,1622),(2487,1618),(2481,1613)],
    'rim-left':[(260,1866),(267,1863),(274,1863),(278,1870),(288,1876),(299,1880),(296,1883),(286,1885),(276,1884),(268,1881),(261,1876)],
    'rim-right':[(2806,1869),(2818,1865),(2828,1859),(2833,1856),(2845,1858),(2854,1863),(2853,1868),(2844,1874),(2834,1876),(2827,1877),(2819,1876),(2810,1874)],
    'rim-bottom-left':[(716,2096),(724,2095),(740,2095),(744,2096),(742,2099),(733,2101),(725,2100),(719,2099)],
    'rim-bottom-right':[(2383,2091),(2391,2090),(2403,2089),(2412,2089),(2415,2091),(2412,2094),(2406,2096),(2399,2095),(2394,2097),(2388,2095)],
    'rim-bottom-center':[(1558,2176),(1564,2175),(1571,2175),(1578,2175),(1580,2176),(1579,2179),(1571,2180),(1564,2179),(1559,2178)]
}
hardware=union(*(polygon(p) for p in screws.values()))
# The lens perimeter has screw scallops and a central housing opening, handled as separate parts below.
lens=curve((1546,1501),[
    ((2227,1481),(2802,1641),(2860,1791)),((2922,1974),(2374,2168),(1550,2184)),
    ((758,2190),(231,2028),(238,1826)),((229,1645),(804,1510),(1546,1501))])
hub=curve((1537,1763),[
    ((1724,1755),(1866,1796),(1913,1828)),((1890,1866),(1806,1881),(1710,1893)),
    ((1649,1910),(1433,1911),(1380,1899)),((1291,1891),(1206,1869),(1188,1827)),
    ((1257,1790),(1396,1769),(1537,1763))])
# Clear screw bosses belong to the lens, rather than to the black central housing.
bosses=union(
    polygon([(1273,1888),(1297,1863),(1318,1860),(1339,1864),(1340,1886),(1350,1895),(1347,1908),(1337,1919),(1287,1919),(1272,1905)]),
    polygon([(1760,1888),(1778,1864),(1802,1860),(1818,1865),(1819,1886),(1829,1896),(1827,1908),(1813,1919),(1775,1919),(1758,1905)]))
hub=sub(hub,bosses)
# Front housing ends at the inner perforated rim's upper edge; retain its textured front band in Housing.
front=curve((1548,1451),[
    ((2275,1446),(2958,1673),(3030,1875)),((3082,2079),(2390,2234),(1548,2231)),
    ((710,2231),(47,2093),(69,1861)),((121,1665),(810,1463),(1548,1451))])
rgb=np.asarray(Image.open(ROOT/'.retouch/inspection/UFO4-source.png').convert('RGB')).astype(np.int16)
led=((rgb[:,:,0]-rgb[:,:,2]>15)&(rgb[:,:,1]-rgb[:,:,2]>11)&(rgb[:,:,1]>105)).astype(np.uint8)*255
led=np.minimum(led,lens);led=sub(led,union(hub,sensor,hardware))
led[:1610]=0;led[2110:]=0;led[:,:345]=0;led[:,2735:]=0
# Only visible warm chip pixels; do not inflate the selection into surrounding lens.
led=np.asarray(Image.fromarray(led).filter(ImageFilter.GaussianBlur(.35)))
priority=union(label,controls,sensor,hardware,led)
parts={
    'Housing':sub(union(sub(subject,front),hub),priority),
    'Rim':sub(sub(front,lens),priority),
    'Lens':sub(lens,union(hub,sensor,hardware,led)),
    'LEDs':led,'Sensor':sub(sensor,hardware),'Controls':controls,'CCT Label':label,'Hardware':hardware,
}
components=[{'name':name,'maskPath':save(name,np.minimum(m,subject))} for name,m in parts.items()]
subject_path=save('Subject',subject)

# Silver sticker footprints plus a narrow blended border, following each curved fin.
left=curve((1079,1043),[
    ((1057,1054),(1028,1075),(1016,1095)),((1003,1121),(1009,1163),(995,1204)),
    ((989,1219),(991,1237),(993,1241)),((1013,1214),(1044,1192),(1070,1183)),
    ((1075,1147),(1076,1087),(1079,1043))])
right=curve((2026,1041),[
    ((2045,1044),(2080,1070),(2091,1096)),((2099,1125),(2098,1209),(2102,1275)),
    ((2086,1248),(2050,1226),(2036,1219)),((2023,1213),(2027,1134),(2021,1067)),
    ((2020,1054),(2020,1045),(2026,1041))])
def cleanup_mask(name,m):
    m=np.asarray(Image.fromarray(m).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))).copy()
    m=np.minimum(m,subject)
    return save(name,m)
left=union(left,polygon([(1003,1175),(1076,1175),(1076,1227),(1010,1260),(1003,1260)]))
left_path=cleanup_mask('Left Label Cleanup',left)
right_path=cleanup_mask('Right Label Cleanup',right)
cleanup=json.loads((ROOT/'.retouch/assets/ufo4/apply-spec-v4.json').read_text())['cleanup']
scratch_paths=[[(1444,1047),(1445,1052),(1446,1053)],[(1457,1054),(1457,1061),(1458,1065)],[(1466,1037),(1467,1039)],[(1483,1122),(1494,1120),(1502,1116),(1508,1111),(1511,1108)]]
for i,(patch,points) in enumerate(zip(cleanup,scratch_paths)):
    im=Image.new('L',(W*S,H*S));d=ImageDraw.Draw(im)
    d.line([(x*S,y*S) for x,y in points],fill=255,width=5*S,joint='curve')
    for x,y in points:d.ellipse(((x-2.5)*S,(y-2.5)*S,(x+2.5)*S,(y+2.5)*S),fill=255)
    m=np.asarray(im.resize((W,H),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.8)))
    patch.update(maskPath=save('Cap Scratch '+str(i+1),m),matchTone=True)
cleanup+=[
    {'method':'clone','source':[1082,1030,1092,1270],'destination':[982,1030],'destinationBounds':[982,1030,1085,1270],'repeatX':True,'maskPath':left_path},
    {'method':'clone','source':[2011,1030,2021,1285],'destination':[2013,1030],'destinationBounds':[2013,1030,2110,1285],'repeatX':True,'maskPath':right_path},
]
base=ROOT/'outputs/UFO 4 - Gold Standard Candidate v5'
job={'action':'apply','sourcePath':str(ROOT/'UFO  4 Unfinished.psd'),'name':base.name,
    'subjectMaskPath':subject_path,'components':components,'cleanup':cleanup,
    'whip':{'color':'black','width':950,'left':1800,'top':60,'angle':5},
    'outputPath':str(base)+'.psd','whitePreviewPath':str(base)+' - White.png',
    'transparentPreviewPath':str(base)+' - Transparent.png','whipPreviewPath':str(base)+' - Whip.png',
    'whipVerifiedPreviewPath':str(base)+' - Whip Reopened.png',
    'review':[
        {'area':'Silver-label removal','bounds':[982,1030,2110,1280],'note':'Both silver side stickers are cloned from nearby clean fin surfaces. Review the reconstructed surface lighting at the curved outer edges.'},
        {'area':'Hardware and CCT label','bounds':[220,900,2865,2185],'note':'Hardware contains thirteen traced visible screw portions, excluding the mounting eye, central housing and clear bosses. Inspect the partial heads through the clear lens and the CCT sticker contour.'},
        {'area':'LEDs and lens','bounds':[238,1500,2865,2185],'note':'Warm chips are selected from their visible color through the refractive lens; confirm this boundary is useful for your later adjustments.'},
        {'area':'Whip attachment','bounds':[1760,60,2830,1230],'note':'Both photographed cables and red marks are excluded. The layered black replacement whip sits below RT; review its upper-right connection and scale.'},
        {'area':'Mounting ring','bounds':[1380,610,1716,946],'note':'Cast metal texture and worn finish are retained as possible real surface details.'},
    ]}
(A/'apply-spec.json').write_text(json.dumps(job,indent=2))
(A/'screw-contours.json').write_text(json.dumps(screws,indent=2))
print(json.dumps({'spec':str(A/'apply-spec.json'),'components':list(parts),'screwContours':len(screws)},indent=2))
