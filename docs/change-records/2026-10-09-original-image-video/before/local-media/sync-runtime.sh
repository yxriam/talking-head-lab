#!/usr/bin/env bash
set -euo pipefail

# Keep one Git working tree on Windows; deploy only required runtime files.
# This script never clones, fetches, pulls, or deletes files.
python3 - <<'PY'
import hashlib
import json
import shutil
from pathlib import Path

source = Path('/mnt/d/project/NZ/cv/local-media')
target = Path('/opt/media-app/local-media')
target.mkdir(parents=True, exist_ok=True)
files = [source / name for name in (
    'server.py', 'generate.py', 'prepare_scene.py', 'video_profiles.py', 'local_scene.py', 'local_account_model.py', 'tokenhub.py', 'truthscan.py', 'tokenhub.env.example', 'truthscan.env.example',
    'local-media-tokenhub.conf', 'local-media-truthscan.conf',
    'detect.py', 'requirements.txt', 'test_server.py', 'test_video_profiles.py', 'test_detect_thresholds.py', 'test_truthscan.py', 'test_tokenhub.py',
    'setup-models.sh', 'install-generators.sh', 'install-sota-generators.sh', 'patch_echomimic_v3_memory.py', 'install-instantid.sh', 'install-scene-llm.sh', 'install-gend.sh', 'run-api.sh', 'configure-tokenhub-service.sh',
    'configure-truthscan-service.sh',
    'import_cos_credentials.py', 'import_env_secret.py', 'README.md',
)]
# Uploaded media are immutable; don't transfer old Windows job paths/status.
data = source / 'data'
for metadata in sorted(data.glob('*/media.json')):
    info = json.loads(metadata.read_text(encoding='utf-8'))
    filename = info['filename']
    if Path(filename).name != filename or '\\' in filename:
        raise ValueError(f'Invalid media filename in {metadata}')
    files.extend([metadata, metadata.parent / filename])

def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()

manifest = []
for original in files:
    relative = original.relative_to(source)
    destination = target / relative
    expected = digest(original)
    changed = not destination.exists() or digest(destination) != expected
    if changed:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + '.sync-part')
        shutil.copyfile(original, temporary)
        if digest(temporary) != expected:
            raise RuntimeError(f'Copy verification failed: {relative}')
        temporary.replace(destination)
    if destination.suffix == '.sh':
        destination.chmod(0o755)
    manifest.append({'file':str(relative), 'sha256':expected})
    print(('COPIED ' if changed else 'UNCHANGED ') + str(relative), flush=True)

(target / 'data').mkdir(exist_ok=True)
(target / 'sync-manifest.json').write_text(json.dumps(manifest, indent=2))
# Verify syntax without importing uninstalled model packages.
for file in target.glob('*.py'):
    compile(file.read_text(encoding='utf-8'), str(file), 'exec')
for name in ('runtime', 'chatterbox', 'SadTalker', 'EchoMimic', 'JoyVASA', 'EchoMimicV3', 'InstantID', 'scene-llm', 'llama.cpp', 'DeepfakeBench', 'NPR', 'GenD'):
    path = Path('/opt/media-models') / name
    if not path.is_dir():
        raise RuntimeError(f'Missing existing model directory: {path}')
    print(f'REUSED {path}', flush=True)
print('RUNTIME_SYNC_VERIFIED', flush=True)
PY
