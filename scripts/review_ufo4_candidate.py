"""Inspection-only sheets from the saved native Photoshop output and its checked mask assets."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'.retouch/assets/ufo4-refined-v5'
base=ROOT/'outputs/UFO 4 - Gold Standard Candidate v5'
source=Image.open(ROOT/'.retouch/inspection/UFO4-source.png').convert('RGB')
final=Image.open(str(base)+' - Transparent.png').convert('RGBA')
white=Image.open(str(base)+' - White.png').convert('RGB')
def save(im,suffix):
    path=Path(str(base)+suffix)
    if path.exists():raise FileExistsError(path)
    im.save(path)
def overlay(box,path):
    photo=source.crop(box).convert('RGBA');mask=Image.open(path).crop(box)
    tint=Image.new('RGBA',photo.size,(255,35,110,0));tint.putalpha(mask.point(lambda x:round(x*.48)))
    return Image.alpha_composite(photo,tint).convert('RGB')
rows=[('Mounting eye: excluded from Hardware',(1355,588,1735,970),'Hardware','Hardware'),
      ('Knurled screw: visible contour',(1105,1185,1195,1280),'Hardware','Hardware'),
      ('Lens screw: clear support excluded',(1250,1840,1360,1940),'Hardware','Hardware'),
      ('CCT label: full sticker edge',(1725,940,1885,1125),'Label','CCT Label')]
sheet=Image.new('RGB',(1040,1320),'white');d=ImageDraw.Draw(sheet)
d.text((18,12),'Pink shows the editable component-mask coverage',fill='black')
d.text((190,38),'Reviewed first trial (v4)',fill='black');d.text((710,38),'Refined candidate',fill='black')
for i,(title,box,old,new) in enumerate(rows):
    y=65+i*310;d.text((18,y),title,fill='black')
    for x,path in [(0,ROOT/'.retouch/assets/ufo4'/(old+'.png')),(520,A/(new+'.png'))]:
        im=overlay(box,path);im.thumbnail((490,275))
        if im.width<250:im=im.resize((int(im.width*2),int(im.height*2)))
        im.thumbnail((490,275));sheet.paste(im,(x+(520-im.width)//2,y+25))
save(sheet,' - Mask Comparison.png')

contours=json.loads((A/'screw-contours.json').read_text());proof=Image.new('RGB',(1040,1000),'white');d=ImageDraw.Draw(proof)
d.text((15,10),'All 13 visible screw portions - Hardware mask shown in pink',fill='black')
for i,(name,points) in enumerate(contours.items()):
    x=(i%4)*260;y=40+(i//4)*235;d.text((x+8,y),name,fill='black')
    xx,yy=zip(*points);box=(min(xx)-15,min(yy)-15,max(xx)+16,max(yy)+16)
    im=overlay(box,A/'Hardware.png');scale=min(4,240/im.width,200/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)))
    proof.paste(im,(x+(260-im.width)//2,y+23))
save(proof,' - Screw Mask Detail.png')

bg=Image.new('RGBA',final.size,(215,215,215,255));d=ImageDraw.Draw(bg)
for y in range(0,bg.height,60):
    for x in range(0,bg.width,60):
        if (x//60+y//60)%2:d.rectangle((x,y,x+59,y+59),fill=(245,245,245,255))
checker=Image.alpha_composite(bg,final).convert('RGB')
dark=Image.alpha_composite(Image.new('RGBA',final.size,(35,38,42,255)),final).convert('RGB')
sheet=Image.new('RGB',(1500,540),'white');d=ImageDraw.Draw(sheet)
for x,name,im in [(0,'White',white),(500,'Dark',dark),(1000,'Checkerboard / transparency',checker)]:
    im=im.copy();im.thumbnail((500,500));sheet.paste(im,(x,40));d.text((x+15,12),name,fill='black')
save(sheet,' - Background Review.png')

boxes=[('Mount opening',(1360,590,1730,945)),('Removed left sticker',(995,1025,1110,1280)),
       ('Removed right sticker',(2000,1025,2110,1290)),('Whip connection',(1770,870,1930,1100)),
       ('Thin wire tips',(2570,40,2830,370)),('Left lens / rim',(215,1800,335,1920))]
sheet=Image.new('RGB',(1200,1870),'white');d=ImageDraw.Draw(sheet)
d.text((12,10),'Edge crops inspected on white, dark and checkerboard backgrounds',fill='black')
for row,(name,b) in enumerate(boxes):
    y=35+row*305;d.text((12,y),name,fill='black')
    for col,im in enumerate([white,dark,checker]):
        c=im.crop(b);scale=min(3,380/c.width,270/c.height);c=c.resize((round(c.width*scale),round(c.height*scale)))
        sheet.paste(c,(col*400+(400-c.width)//2,y+24))
save(sheet,' - Edge Detail.png')

# Larger before/after cleanup crops avoid compressing both side stickers into one small overview.
boxes=[('Left silver sticker',(980,1020,1120,1280)),('Right silver sticker',(2000,1020,2110,1300)),
       ('Cap scratches',(1405,1018,1555,1192))]
sheet=Image.new('RGB',(900,1190),'white');d=ImageDraw.Draw(sheet)
d.text((90,10),'Original',fill='black');d.text((545,10),'Retouched',fill='black')
for row,(name,b) in enumerate(boxes):
    y=35+row*380;d.text((12,y),name,fill='black')
    for col,im in enumerate([source,white]):
        c=im.crop(b);scale=min(3,425/c.width,345/c.height);c=c.resize((round(c.width*scale),round(c.height*scale)))
        sheet.paste(c,(col*450+(450-c.width)//2,y+24))
save(sheet,' - Cleanup Closeups.png')
print('Created mask comparison, screw detail, background review, edge detail, and cleanup closeups.')
