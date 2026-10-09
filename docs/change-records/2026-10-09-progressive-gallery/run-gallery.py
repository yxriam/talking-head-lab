"""Two frozen, real original-image SadTalker examples; resumes existing jobs only."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path('D:/project/facebook/talking-head-lab')
RECORD = Path(__file__).resolve().parent
ASSETS = ROOT / 'docs/showcase/gallery'
ip = subprocess.check_output(['wsl','-d','Ubuntu-22.04','--','hostname','-I'],text=True).strip().split()[0]
client = httpx.Client(base_url=f'http://{ip}:8002',headers={'Host':'localhost'},timeout=40,trust_env=False)
assert not client.get('/health').raise_for_status().json()['busy']
audio_id = '2dc507869ece42bf883596b90c1a1973'
audio = client.get('/media/'+audio_id).raise_for_status().content
assert hashlib.sha256(audio).hexdigest() == hashlib.sha256((ROOT/'docs/showcase/generated-voice.wav').read_bytes()).hexdigest()
for number in [2,3]:
    record = RECORD/f'case-{number:02d}.json'
    image = ASSETS/f'portrait-{number:02d}.png'
    if record.exists():
        state=json.loads(record.read_text(encoding='utf-8'))
    else:
        with image.open('rb') as photo:
            uploaded=client.post('/media',files={'file':(image.name,photo,'image/png')}).raise_for_status().json()
        stored=client.get('/media/'+uploaded['id']).raise_for_status().content
        assert stored == image.read_bytes()
        payload={'kind':'video','model':'sadtalker','image_id':uploaded['id'],'audio_id':audio_id}
        job=client.post('/jobs',json=payload).raise_for_status().json()
        state={'case':number,'input_image':image.name,'input_sha256':hashlib.sha256(stored).hexdigest(),
               'image_id':uploaded['id'],'audio_id':audio_id,'audio_sha256':hashlib.sha256(audio).hexdigest(),
               'payload':payload,'job_id':job['id'],'original_image_byte_match':True,'new_submission_count':1}
        record.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(f"CASE_{number:02d}_JOB {state['job_id']}",flush=True)
    started=time.monotonic();last=None
    while True:
        job=client.get('/jobs/'+state['job_id']).raise_for_status().json()
        if job['status'] not in {'queued','running'}:break
        current=(job['progress'],job['message'])
        if current != last:
            print(json.dumps({'case':number,'progress':job['progress']},ensure_ascii=False),flush=True);last=current
        if time.monotonic()-started>600:raise RuntimeError('Frozen job timeout; do not resubmit')
        time.sleep(3)
    state['actual_job']=job
    record.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    assert job['status']=='done',job
    assert job['result']['scene']=='original'
    output=client.get(job['result']['url']).raise_for_status().content
    (ASSETS/f'video-{number:02d}.mp4').write_bytes(output)
    state['output_sha256']=hashlib.sha256(output).hexdigest()
    state['no_background_artifacts']=subprocess.check_output(['wsl','-d','Ubuntu-22.04','--','find',
        f"/opt/media-app/local-media/data/{state['job_id']}",'-name','generated-portrait.png','-o','-name','scene.json','-o','-name','scene-prompt.txt'],text=True).strip()==''
    assert state['no_background_artifacts']
    record.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'case':number,'status':job['status'],'seconds':job['elapsed_seconds'],'scene':job['result']['scene']}),flush=True)
