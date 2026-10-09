from pathlib import Path
import json,hashlib
root=Path('/mnt/d/project/NZ/cv/docs/change-records/2026-10-09-original-image-video')
manifest=json.loads((root/'new-demo-inputs.json').read_text())
work=Path('/opt/media-app/local-media/data')/manifest['video_job_id']
request=json.loads((work/'request.json').read_text())
expected=Path('/opt/media-app/local-media/data')/manifest['input_image_id']/'input.png'
assert Path(request['image'])==expected
actual=hashlib.sha256(expected.read_bytes()).hexdigest()
assert actual==manifest['input_image_sha256']
absent=['generated-portrait.png','scene.json','scene-prompt.txt']
assert all(not (work/name).exists() for name in absent)
assert 'scene_text' not in request
result={'request_image':request['image'],'input_image_sha256':actual,'image_unmodified':True,'no_background_artifacts':absent,'scene_text_ignored':True,'runtime_server_sha256':hashlib.sha256(Path('/opt/media-app/local-media/server.py').read_bytes()).hexdigest()}
(root/'original-image-proof.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
