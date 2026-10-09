from pathlib import Path
import urllib.request,json,hashlib,shutil
status=json.load(urllib.request.urlopen('http://127.0.0.1:8002/health',timeout=10))
assert not status['busy']
source=Path('/mnt/d/project/NZ/cv/docs/change-records/2026-10-09-original-image-video/runtime-server-deployed.py')
target=Path('/opt/media-app/local-media/server.py')
compile(source.read_text(),str(source),'exec')
shutil.copyfile(source,target)
assert hashlib.sha256(source.read_bytes()).hexdigest()==hashlib.sha256(target.read_bytes()).hexdigest()
print(json.dumps({'runtime_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'account_block':'preserved from runtime before snapshot','background_flow':'removed','only_file_synced':'server.py'}))
