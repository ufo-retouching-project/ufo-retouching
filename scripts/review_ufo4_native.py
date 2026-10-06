"""Review saved UFO 4 component selections without modifying photograph pixels."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / '.retouch/assets/ufo4-native-v6'
OLD = ROOT / '.retouch/assets/ufo4-refined-v5'
final_assets = ROOT / '.retouch/assets/ufo4-native-v6b'
spec = json.loads((final_assets / 'apply-spec.json').read_text())
BASE = Path(spec['outputPath']).with_suffix('')
photo = Image.open(ROOT / 'outputs/UFO 4 - Gold Standard Candidate v5 - White.png').convert('RGB')
font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
font = ImageFont.truetype(font_path, 23)
small = ImageFont.truetype(font_path, 18)
title = ImageFont.truetype(font_path, 30)

def read(path):
    return np.fromfile(path, np.uint8).reshape(photo.height, photo.width)

def overlay(mask, box):
    pixels = np.asarray(photo.crop(box)).astype(float)
    weight = mask[box[1]:box[3], box[0]:box[2], None] / 255 * .48
    return Image.fromarray(np.rint(pixels * (1-weight) + np.array([255, 45, 55]) * weight).astype(np.uint8))

boxes = {
    'Housing': (45, 580, 3055, 1940),
    'Rim': (55, 1390, 3050, 2250),
    'Lens': (185, 1470, 2920, 2215),
    'LEDs': (315, 1590, 2790, 2160),
    'Sensor': (1260, 1810, 1840, 2190),
    'Controls': (1370, 915, 1740, 1255),
    'CCT Label': (1725, 935, 1885, 1130),
    'Hardware': (230, 900, 2870, 2210),
}
methods = {
    'Housing': 'Object Selection starts; subject silhouette and local seam/hub corrections; Select and Mask',
    'Rim': 'Magic Wand material/slot starts; local seam and opening corrections; Select and Mask',
    'Lens': 'Object Selection + Select and Mask; subtract hub, sensor, screws and visible LEDs',
    'LEDs': 'Sampled Photoshop Color Range; local warm-chip refinement and lens scope',
    'Sensor': 'Object Selection + light Select and Mask',
    'Controls': 'Object Selection + light Select and Mask',
    'CCT Label': 'Object Selection, two-pixel expansion and light Select and Mask',
    'Hardware': '13 local Magic Wand starts; preserve reviewed v5 shadow/occlusion contour repairs',
}
width, row_h, top_h = 1400, 460, 110
sheet = Image.new('RGB', (width, top_h + row_h*len(boxes) + 45), '#f1f2f4')
d = ImageDraw.Draw(sheet)
d.text((20, 12), 'UFO 4 — all component masks', fill='#20252b', font=title)
d.text((20, 52), 'Red overlay = selected area. Same photograph, crop and overlay strength in both columns.', fill='#30343b', font=small)
d.text((20, 80), 'Previous v5', fill='#30343b', font=font)
d.text((720, 80), 'Native selection trial v6b', fill='#30343b', font=font)
stats = {}
for i, component in enumerate(spec['components']):
    name = component['name']; mask = read(component['maskPath']); old = read(OLD/(name+'.bin'))
    y = top_h + i*row_h
    changed = int(np.count_nonzero(mask != old))
    stats[name] = {'selectedPixels': int(np.count_nonzero(mask > 127)), 'changedMaskPixelsVsV5': changed, 'method': methods[name], 'maskPath': component['maskPath']}
    label = name + (' — reviewed contour retained' if changed == 0 else '')
    d.text((20, y+8), label, fill='#20252b', font=font)
    for x, m in ((20, old), (720, mask)):
        im = overlay(m, boxes[name]); im.thumbnail((660, 392), Image.Resampling.LANCZOS)
        left = x+(660-im.width)//2; top = y+45+(392-im.height)//2
        sheet.paste(im, (left, top))
    d.line((15, y+row_h-1, width-15, y+row_h-1), fill='#cbd0d6', width=1)
d.text((20, sheet.height-32), 'Human review pending. Inspect shadowed rim openings and refracted LED boundaries closely.', fill='#30343b', font=small)
sheet.save(Path(str(BASE)+' - Mask Comparison.png'))

# Original-resolution overlays retain narrow contours for inspection.
details = {
    'Rim Top': ('Rim', (830, 1410, 2240, 1590)),
    'Rim Bottom': ('Rim', (530, 2070, 2590, 2250)),
    'Housing Seam': ('Housing', (830, 1310, 2240, 1570)),
    'Lens Detail': ('Lens', (1080, 1710, 1990, 2200)),
    'LED Detail': ('LEDs', (350, 1630, 1250, 2070)),
    'Sensor Detail': ('Sensor', boxes['Sensor']),
    'Controls Detail': ('Controls', boxes['Controls']),
    'CCT Label Detail': ('CCT Label', boxes['CCT Label']),
    'Screw Detail': ('Hardware', (1110, 1180, 1200, 1285)),
}
paths = {c['name']: c['maskPath'] for c in spec['components']}
for name, (component, box) in details.items():
    original = photo.crop(box); selected = overlay(read(paths[component]), box)
    pair = Image.new('RGB', (original.width, original.height*2+64), 'white')
    draw = ImageDraw.Draw(pair)
    draw.text((10, 6), name+' — photograph', fill='black', font=small)
    pair.paste(original, (0, 32))
    draw.text((10, original.height+38), 'Mask overlay — original pixel resolution', fill='black', font=small)
    pair.paste(selected, (0, original.height+64))
    pair.save(Path(str(BASE)+' - '+name+'.png'))
(final_assets/'final-mask-stats.json').write_text(json.dumps(stats, indent=2))
print(json.dumps({'comparison': str(BASE)+' - Mask Comparison.png', 'changedComponents': [n for n, s in stats.items() if s['changedMaskPixelsVsV5']], 'details': len(details)}, indent=2))
