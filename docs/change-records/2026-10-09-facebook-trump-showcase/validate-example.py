"""Read-only evidence and publication checks; never crawl or run a model."""
import ast
import hashlib
import io
import json
import re
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
RECORD = Path(__file__).resolve().parent
SOURCE = Path('D:/project/NZ/cv')
summary = json.loads((ROOT / 'docs/showcase/facebook-trump/collection-summary.json').read_text(encoding='utf-8'))
receipt = json.loads((RECORD / 'collection-receipt.json').read_text(encoding='utf-8'))
raw = json.loads((Path(receipt['raw_data']) / 'result.json').read_text(encoding='utf-8'))
shot = json.loads((RECORD / 'screenshot-receipt.json').read_text(encoding='utf-8'))
checks = {
    'real_source_and_job_match': summary['source_url'] == raw['source_url'] == receipt['options']['url'] and summary['job_id'] == receipt['job_id'],
    'actual_counts_match': summary['visible_text_fragments'] == len(raw['text']) == 45 and summary['visible_media_entries'] == len(raw['media']) == 18,
    'actual_text_excerpts_unchanged': all(item in raw['text'] for item in summary['text_excerpt']),
    'no_risk_model_called': receipt['account_model_called'] is False and summary['page_purpose_observation']['risk_model_called'] is False,
    'capture_actual_service_get_only': shot['collector_service_online_during_capture'] and all(call['method'] == 'GET' for call in shot['network_calls']),
    'screenshot_no_source_change_or_model': shot['source_changed_for_screenshots'] is False and shot['new_model_jobs'] is False,
    'collector_bytes_match_used_version': hashlib.sha256((SOURCE / 'facebook-scam/crawler/facebook.py').read_bytes()).hexdigest() == receipt['collector_sha256'],
}
for item in summary['media_metadata']:
    if item['status'] == 'downloaded':
        checks['actual_download_hash_' + item['id']] = hashlib.sha256((Path(receipt['raw_data']) / item['filename']).read_bytes()).hexdigest() == item['sha256']
public = json.dumps(summary, ensure_ascii=False)
checks['no_signed_urls_comment_ids_or_cookies'] = not any(term in public for term in ['fbcdn.net', '__cft__', 'comment_id', 'c_user', 'xs=', 'cookie'])
checks['no_commenter_text_or_names_published'] = all(item['context'] == 'profile_or_page' for item in summary['text_excerpt']) and not any(item['text'] in public for item in raw['text'] if item['context'] == 'comment')
links = []
for rel in ['docs/showcase/facebook-trump/EXAMPLE.md', 'docs/showcase/facebook-trump/EXAMPLE.en.md', 'docs/specs/facebook-trump-showcase.md']:
    path = ROOT / rel
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if re.match(r'[a-zA-Z]+:', target):
            continue
        destination = (path.parent / unquote(target.split('#')[0])).resolve()
        links.append({'from': rel, 'target': target, 'exists': destination.exists()})
checks['new_example_and_spec_links'] = all(item['exists'] for item in links)
images = []
for path in sorted((ROOT / 'docs/showcase/facebook-trump').glob('*.jpg')):
    with Image.open(path) as im:
        images.append({'file': path.name, 'bytes': path.stat().st_size, 'width': im.width, 'height': im.height,
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
checks['six_readable_screenshots_under_5mb'] = len(images) == 6 and all(i['width'] == 1440 and i['height'] <= 1000 and i['bytes'] < 5000000 for i in images)
for path in RECORD.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'))
checks['runner_scripts_parse'] = True
checks['business_source_and_dependencies_unchanged'] = not subprocess.check_output(['git', 'diff', '1488f63', '--', 'local-media', 'facebook-scam'], cwd=ROOT).strip()
zipinfo = []
for lang in ['zh', 'en']:
    content = urllib.request.urlopen(f"http://127.0.0.1:8003/crawl/jobs/{receipt['job_id']}/export?language={lang}", timeout=15).read()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert archive.testzip() is None
        zipinfo.append({'language': lang, 'bytes': len(content), 'files': archive.namelist()})
checks['actual_local_zip_export_both_languages'] = all(len(i['files']) == 6 for i in zipinfo)
result = {'checks': checks, 'links': links, 'screenshots': images, 'actual_zip_export': zipinfo,
          'failures': [key for key, passed in checks.items() if not passed]}
(RECORD / 'example-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'checks': checks, 'zip_files': zipinfo, 'failures': result['failures']}, ensure_ascii=True))
raise SystemExit(bool(result['failures']))
