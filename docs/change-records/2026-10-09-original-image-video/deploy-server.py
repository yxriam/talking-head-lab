from pathlib import Path
import hashlib,shutil,json,urllib.request
status=json.load(urllib.request.urlopen('http://127.0.0.1:8002/health',timeout=10))
assert not status['busy'],'API has an active task; do not deploy'
source=Path('/mnt/d/project/NZ/cv/local-media/server.py')
target=Path('/opt/media-app/local-media/server.py')
backup=target.with_name('.server-before-original-image-20261009-01a11aec.py')
if backup.exists():
    raise RuntimeError('Runtime backup already exists; review before overwriting')
compile(source.read_text(encoding='utf-8'),str(source),'exec')
before=hashlib.sha256(target.read_bytes()).hexdigest()
shutil.copyfile(target,backup)
shutil.copyfile(source,target)
after=hashlib.sha256(target.read_bytes()).hexdigest()
assert after==hashlib.sha256(source.read_bytes()).hexdigest()
result={'file':str(target),'backup':str(backup),'before_sha256':before,'after_sha256':after,'only_file_synced':'server.py','busy_before':False}
Path('/mnt/d/project/NZ/cv/docs/change-records/2026-10-09-original-image-video/runtime-sync.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
