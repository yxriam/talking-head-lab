"""Prepare a small, source-linked public excerpt, never publish browser/raw data."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[3]
RECORD = Path(__file__).resolve().parent
PUB = Path('D:/project/facebook/talking-head-lab')
receipt = json.loads((RECORD / 'collection-receipt.json').read_text(encoding='utf-8'))
assert receipt['status'] == 'done' and receipt['account_model_called'] is False
work = Path(receipt['raw_data'])
raw = json.loads((work / 'result.json').read_text(encoding='utf-8'))
job = json.loads((work / 'job.json').read_text(encoding='utf-8'))
assert raw['source_url'] == 'https://www.facebook.com/DonaldTrump/'
assert raw['text'][0]['text'] == 'Donald J. Trump'
assert 'official Facebook page' in raw['text'][5]['text']
assert raw['text'][6]['text'] == '政治候选人'
out = PUB / 'docs/showcase/facebook-trump'
out.mkdir(parents=True, exist_ok=True)

def public_url(url):
    parts = urlsplit(url)
    # Keep only photo identity; remove Facebook tracking and commenter identifiers.
    query = urlencode([(k,v) for k,v in parse_qsl(parts.query) if k in {'fbid','set'}])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ''))

selected = [raw['text'][i] for i in [0,5,6,14]]
media = []
for asset in raw['media']:
    entry = {key: asset[key] for key in ['id','filename','kind','status','size','sha256','reason'] if key in asset}
    entry['source_url'] = public_url(asset['source_url'])
    entry['name'] = asset.get('filename', 'Facebook '+asset['kind'])
    if entry['status'] == 'downloaded':
        assert hashlib.sha256((work / entry['filename']).read_bytes()).hexdigest() == entry['sha256']
        entry['url'] = f"/crawl/media/{job['id']}/{entry['id']}"
    media.append(entry)
summary = {
    'source_url': raw['source_url'], 'collected_at_utc': receipt['created_at'],
    'finished_at_utc': receipt['finished_at'], 'job_id': job['id'],
    'collector_path': 'facebook-scam/crawler/facebook.py', 'collector_sha256': receipt['collector_sha256'],
    'method': receipt.get('runner', job['runner']), 'options': receipt['options'],
    'elapsed_seconds': receipt['elapsed_seconds'], 'collector_elapsed_seconds': raw['elapsed_seconds'],
    'visible_text_fragments': len(raw['text']), 'visible_media_entries': len(raw['media']),
    'media_types': dict(Counter(asset['kind'] for asset in raw['media'])),
    'downloaded_types': dict(Counter(asset['kind'] for asset in raw['media'] if asset['status']=='downloaded')),
    'text_excerpt': selected, 'media_metadata': media,
    'page_purpose_observation': {'category': 'official political public page',
                                 'evidence_excerpt_indices': [1,2], 'risk_model_called': False,
                                 'classification_model_called': False},
    'limitations': ['visible viewport only; not 45 posts', 'publication dates not extracted (all date=null)',
                   '7 video entries are links only, including repeated reel/comment variants',
                   'download cap 4 images/1 video; 0 video/audio files obtained',
                   'original captions, commenter names, tracking parameters, signed CDN URLs and raw media omitted',
                   'browser title notification count omitted',
                   'no official page endorsement or generated Trump voice/video'],
    'screenshot_method': 'actual localhost UI replay of this completed collector run; excerpt only; no new model run',
}
(out / 'collection-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
public_job = {k:v for k,v in job.items() if k != 'result'}
public_job['result'] = {'source_url': raw['source_url'], 'title': 'Facebook', 'text': selected,
                        'media': media, 'elapsed_seconds': raw['elapsed_seconds'],
                        'warnings': ['公开节选 4 条主页片段（原采集 45 条）；原图和评论者资料留本机。 Public excerpt: 4 of 45 text fragments; originals and commenter data remain local.']}
public_job['counts'] = {'text': len(raw['text']), 'media': len(raw['media']), 'scrolls': 4,
                        'image': 4, 'video': 0, 'audio': 0}
public_job['message'] = '已完成（仅采集，未运行风险分析）'
(RECORD / 'public-ui-job.json').write_text(json.dumps(public_job,ensure_ascii=False,indent=2),encoding='utf-8')
print('PUBLIC_EXCERPT_READY: 45 fragments, 18 media entries, 4 images, no risk/model call')
