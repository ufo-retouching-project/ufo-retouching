"""Meaningful queue checks: invalid requests cannot reach Photoshop or overwrite results."""
from pathlib import Path
import copy,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'.retouch/assets/ufo4/apply-spec-v4.json').read_text())
folder=ROOT/'.retouch/safety-tests';folder.mkdir(exist_ok=True)
checks=[]
for label,change in [('existing_output',lambda j:None),('outside_project',lambda j:j.update(sourcePath='/tmp/source.psd')),('missing_source',lambda j:j.update(sourcePath=str(ROOT/'input/missing.psd'))),('duplicate_components',lambda j:j['components'].append(copy.deepcopy(j['components'][0]))),('bad_mask',lambda j:j.update(subjectMaskPath=str(ROOT/'input/README.md')))]:
 j=copy.deepcopy(base)
 if label not in ['existing_output']:
  for k in ['outputPath','whitePreviewPath','transparentPreviewPath']:j[k]=str(folder/(label+'-'+Path(j[k]).name))
 change(j);spec=folder/(label+'.json');spec.write_text(json.dumps(j));before=set((ROOT/'.retouch/queue').glob('*.json'))
 r=subprocess.run([sys.executable,str(ROOT/'scripts/retouch_jobs.py'),'apply',str(spec)],capture_output=True,text=True)
 assert r.returncode!=0,(label,r.stdout)
 assert before==set((ROOT/'.retouch/queue').glob('*.json')),label
 checks.append(label)
print('Passed: '+', '.join(checks))
for label,change in [
 ('invalid_whip_color',lambda j:j['whip'].update(color='red')),
 ('invalid_whip_width',lambda j:j['whip'].update(width=0)),
 ('missing_whip_preview',lambda j:j.pop('whipPreviewPath')),
 ('duplicate_whip_outputs',lambda j:j.update(whipVerifiedPreviewPath=j['whipPreviewPath']))
]:
 j=copy.deepcopy(base);j['whip']={'color':'black','width':950,'left':1800,'top':60,'angle':0}
 for k in ['outputPath','whitePreviewPath','transparentPreviewPath','whipPreviewPath','whipVerifiedPreviewPath']:j[k]=str(folder/(label+'-'+k+'.'+('psd' if k=='outputPath' else 'png')))
 change(j);spec=folder/(label+'.json');spec.write_text(json.dumps(j));before=set((ROOT/'.retouch/queue').glob('*.json'))
 r=subprocess.run([sys.executable,str(ROOT/'scripts/retouch_jobs.py'),'apply',str(spec)],capture_output=True,text=True)
 assert r.returncode!=0,(label,r.stdout)
 assert before==set((ROOT/'.retouch/queue').glob('*.json')),label
 print('Passed: '+label)
refined=json.loads((ROOT/'.retouch/assets/ufo4-refined-v5/apply-spec.json').read_text())
for label,change in [
 ('invalid_clone_mask',lambda j:j['cleanup'][-1].update(maskPath=str(ROOT/'input/README.md'))),
 ('invalid_clone_destination',lambda j:j['cleanup'][-1].update(destinationBounds=[2013,1030,4000,1280])),
 ('invalid_clone_height',lambda j:j['cleanup'][-1].update(destinationBounds=[2013,1030,2110,1281]))
]:
 j=copy.deepcopy(refined)
 for k in ['outputPath','whitePreviewPath','transparentPreviewPath','whipPreviewPath','whipVerifiedPreviewPath']:j[k]=str(folder/(label+'-'+k+'.'+('psd' if k=='outputPath' else 'png')))
 change(j);spec=folder/(label+'.json');spec.write_text(json.dumps(j));before=set((ROOT/'.retouch/queue').glob('*.json'))
 r=subprocess.run([sys.executable,str(ROOT/'scripts/retouch_jobs.py'),'apply',str(spec)],capture_output=True,text=True)
 assert r.returncode!=0,(label,r.stdout)
 assert before==set((ROOT/'.retouch/queue').glob('*.json')),label
 print('Passed: '+label)
