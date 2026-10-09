from pathlib import Path
import json,time,httpx,hashlib
root=Path('D:/project/facebook/talking-head-lab')
e=Path('D:/project/NZ/cv/docs/change-records/2026-10-09-original-image-video')
client=httpx.Client(base_url='http://localhost:3100/api',timeout=30,trust_env=False)
image=root/'docs/showcase/synthetic-input.png'
with image.open('rb') as photo:
    response=client.post('/media',files={'file':('synthetic-input.png',photo,'image/png')})
response.raise_for_status();image_id=response.json()['id']
voice_id='2dc507869ece42bf883596b90c1a1973'
voice=client.get('/media/'+voice_id);voice.raise_for_status()
assert hashlib.sha256(voice.content).hexdigest()==hashlib.sha256((root/'docs/showcase/generated-voice.wav').read_bytes()).hexdigest()
payload={'kind':'video','image_id':image_id,'audio_id':voice_id,'model':'sadtalker','text':'Welcome to Talking Head Lab. This is an AI generated demonstration.'}
response=client.post('/jobs',json=payload);response.raise_for_status();job=response.json()
manifest={'input_image_id':image_id,'input_image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'audio_id':voice_id,'video_job_id':job['id'],'model':'sadtalker','background_replacement':False,'single_new_generation':True,'payload':payload}
(e/'new-demo-inputs.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('ORIGINAL_IMAGE_VIDEO_JOB '+job['id'],flush=True)
started=time.monotonic();last=None
while job['status'] in {'queued','running'}:
    if time.monotonic()-started>600:raise RuntimeError('Frozen demo timed out; do not resubmit')
    message=(job['progress'],job['message'])
    if message!=last:print(json.dumps({'progress':job['progress'],'message':job['message']},ensure_ascii=False),flush=True);last=message
    time.sleep(2)
    response=client.get('/jobs/'+job['id']);response.raise_for_status();job=response.json()
(e/'video-job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
assert job['status']=='done',job['message']
video=client.get(job['result']['url']);video.raise_for_status();(e/'original-image-demo.mp4').write_bytes(video.content)
print(json.dumps({'video_status':job['status'],'elapsed_seconds':job['elapsed_seconds'],'scene':job['result'].get('scene')},ensure_ascii=False),flush=True)
response=client.post('/jobs',json={'kind':'detect','media_id':job['result']['id'],'use_truthscan':False});response.raise_for_status();detect=response.json()
print('ORIGINAL_IMAGE_DETECTION_JOB '+detect['id'],flush=True)
started=time.monotonic()
while detect['status'] in {'queued','running'}:
    if time.monotonic()-started>600:raise RuntimeError('Frozen detection timed out; do not resubmit')
    time.sleep(2);response=client.get('/jobs/'+detect['id']);response.raise_for_status();detect=response.json()
(e/'detection-job.json').write_text(json.dumps(detect,ensure_ascii=False,indent=2),encoding='utf-8')
assert detect['status']=='done',detect['message']
print(json.dumps({'detection_status':detect['status'],'elapsed_seconds':detect['elapsed_seconds'],'summary':detect['result']['summary'],'score':detect['result']['ai_probability']},ensure_ascii=False),flush=True)
