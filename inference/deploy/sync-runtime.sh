#!/usr/bin/env bash
set -euo pipefail

# Keep one Git working tree on Windows; deploy only required runtime files.
# This script never clones, fetches, pulls, or deletes files.
REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)" python3 - <<'PY'
import hashlib
import json
import os
import shutil
from pathlib import Path

repo = Path(os.environ['REPO'])
source = repo / 'inference'
# The GPU host keeps one flat runtime folder; the repository groups files by purpose.
target = Path('/opt/media-app/local-media')
target.mkdir(parents=True, exist_ok=True)
files = [repo / name for name in (
    # runtime
    'inference/server.py', 'inference/generate.py', 'inference/video_profiles.py', 'inference/detect.py',
    'inference/local_account_model.py', 'inference/tokenhub.py', 'inference/truthscan.py',
    'inference/prepare_scene.py', 'inference/local_scene.py', 'inference/requirements.txt', 'inference/run-api.sh',
    # configuration templates
    'inference/config/tokenhub.env.example', 'inference/config/truthscan.env.example',
    'inference/config/local-media-tokenhub.conf', 'inference/config/local-media-truthscan.conf',
    # tests that run on the GPU host
    'tests/_paths.py', 'tests/test_server.py', 'tests/test_video_profiles.py', 'tests/test_detect_thresholds.py',
    'tests/test_truthscan.py', 'tests/test_tokenhub.py',
    # installers and service configuration
    'inference/install/setup-models.sh', 'inference/install/install-generators.sh',
    'inference/install/install-sota-generators.sh', 'inference/install/patch_echomimic_v3_memory.py',
    'inference/install/patch-echomimic-lowmem.py',
    'inference/install/install-instantid.sh', 'inference/install/install-scene-llm.sh', 'inference/install/install-gend.sh',
    'inference/deploy/configure-tokenhub-service.sh', 'inference/deploy/configure-truthscan-service.sh',
    'inference/deploy/import_cos_credentials.py', 'inference/deploy/import_env_secret.py',
)]
flat = {original: original.name for original in files}
if len(set(flat.values())) != len(flat):
    raise RuntimeError('Runtime file names must stay unique because the target folder is flat')
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
    relative = Path(flat[original]) if original in flat else original.relative_to(source)
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
for name in ('runtime', 'chatterbox', 'SadTalker', 'EchoMimic', 'JoyVASA', 'EchoMimicV3', 'scene-llm', 'llama.cpp', 'DeepfakeBench', 'NPR', 'GenD'):
    path = Path('/opt/media-models') / name
    if not path.is_dir():
        raise RuntimeError(f'Missing existing model directory: {path}')
    print(f'REUSED {path}', flush=True)
print('RUNTIME_SYNC_VERIFIED', flush=True)
PY
