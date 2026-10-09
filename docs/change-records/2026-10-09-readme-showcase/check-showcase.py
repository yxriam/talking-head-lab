"""Read-only README/media validation using the bundled Python + Pillow."""
import ast
import argparse
import hashlib
import json
import re
import subprocess
import wave
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def headings(path):
    content = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
    return re.findall(r'^#{1,6}\s+(.+)$', content, re.M)


def slug(value):
    return re.sub(r'[^\w\- ]', '', value.lower()).replace(' ', '-')


def main(output=None):
    result = {'links': [], 'media': [], 'checks': {}, 'failures': []}
    docs = ['README.md', 'README.en.md', 'AGENTS.md', 'PROJECT.md',
            'docs/showcase/PROVENANCE.md', 'docs/specs/readme-showcase.md',
            'docs/change-records/2026-10-09-readme-showcase/记录.md']
    progressive = '## 快速开始' in (ROOT / 'README.md').read_text(encoding='utf-8')
    if progressive:
        docs += ['docs/guides/SETUP.md','docs/guides/SETUP.en.md',
                 'docs/guides/DEVELOPMENT.md','docs/guides/DEVELOPMENT.en.md',
                 'docs/showcase/gallery/EXAMPLES.md','docs/showcase/gallery/EXAMPLES.en.md']
    for name in docs:
        path = ROOT / name
        content = path.read_text(encoding='utf-8')
        if b'\r\r\n' in path.read_bytes():
            result['failures'].append('doubled Windows line endings break Markdown: ' + name)
        if progressive and name.startswith('docs/guides/') and content.count('```') % 2:
            result['failures'].append('unbalanced guide code fence: ' + name)
        targets = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', content)
        targets += re.findall(r'<img\s+[^>]*src="([^"]+)"', content)
        targets += re.findall(r'<a\s+[^>]*href="([^"]+)"', content)
        for target in targets:
            if re.match(r'[a-zA-Z]+:', target):
                continue
            target, _, fragment = target.partition('#')
            destination = path.parent / unquote(target) if target else path
            valid = destination.exists()
            if valid and fragment and destination.suffix == '.md':
                valid = fragment in {slug(h) for h in headings(destination)}
            result['links'].append({'from': name, 'target': target, 'fragment': fragment, 'valid': valid})
            if not valid:
                result['failures'].append('invalid local link: ' + name + ' -> ' + target + '#' + fragment)

    zh = (ROOT / 'README.md').read_text(encoding='utf-8')
    en = (ROOT / 'README.en.md').read_text(encoding='utf-8')
    for name, content, sequence in [
        ('zh', zh, ['## 有哪些功能','## 先看效果，再试样例','## 快速开始','## 想修改项目'] if progressive else ['## 功能与效果展示', '## 部署', '## 使用', '## 项目结构与代码分布', '## 二次开发']),
        ('en', en, ['## What you can do','## See the results, then try the inputs','## Quick start','## Make changes'] if progressive else ['## Features and results', '## Deployment', '## Usage', '## Project structure and code map', '## Further development']),
    ]:
        indexes = [content.find(value) for value in sequence]
        valid = all(i >= 0 for i in indexes) and indexes == sorted(indexes)
        result['checks'][name + '_requested_order'] = valid
        if not valid:
            result['failures'].append(name + ' section order mismatch')
    result['checks']['language_cross_links'] = '(README.en.md)' in zh and '(README.md)' in en
    commands_zh = re.findall(r'```powershell\n(.*?)\n```', zh, re.S)
    commands_en = re.findall(r'```powershell\n(.*?)\n```', en, re.S)
    result['checks']['same_deployment_usage_development_commands'] = commands_zh == commands_en
    result['powershell_blocks_per_language'] = len(commands_zh)
    for token in ([] if progressive else ['4.736', '4.68', '38.1', '61.9', '24.1', '95.8%', 'yt-video-humanactor', 'RAYON_NUM_THREADS']):
        if token not in zh or token not in en:
            result['failures'].append('bilingual fact mismatch: ' + token)
    result['checks']['private_gate_version_boundary'] = ('自动门控仍待验收' in zh and 'automatic gating still awaits acceptance' in en) if progressive else ('当前GitHub版本没有完成自动门控' in zh and 'This GitHub version has not completed automatic gating' in en)
    result['checks']['generation_source_marked_synthetic'] = ('合成原图与声音' in zh and 'synthetic people and synthetic speech' in en) if progressive else ('新的账号分析推理' in zh and 'new account-analysis inference' in en)

    assets = ROOT / 'docs/showcase'
    for path in sorted(assets.rglob('*')):
        if not path.is_file():
            continue
        row = {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)}
        if path.stat().st_size > 5_000_000:
            result['failures'].append('showcase asset exceeds frozen 5MB limit: ' + path.name)
        if path.suffix in {'.png', '.jpg', '.gif'}:
            with Image.open(path) as picture:
                row.update(width=picture.width, height=picture.height, format=picture.format,
                           frames=getattr(picture, 'n_frames', 1))
                if path.name == 'sadtalker-original-demo.gif' and (row['frames'] < 2 or picture.info.get('loop') != 0):
                    result['failures'].append('GIF must contain actual animated frames and loop')
        if path.suffix == '.wav':
            with wave.open(str(path)) as sound:
                row['duration_seconds'] = sound.getnframes() / sound.getframerate()
        result['media'].append(row)
    current_zh = set(re.findall(r'docs/showcase/([^\s)]+-zh[.]jpg)', zh))
    current_en = set(re.findall(r'docs/showcase/([^\s)]+-en[.]jpg)', en))
    result['checks']['bilingual_current_screenshot_pairs'] = (
        len(current_zh) >= (4 if progressive else 5) and len(current_zh) == len(current_en)
        and {name.replace('-zh.jpg', '-en.jpg') for name in current_zh} == current_en
        and all((assets / name).exists() for name in current_zh | current_en))
    result['checks']['reference_and_generated_audio_distinct'] = sha(assets / 'reference-voice.wav') != sha(assets / 'generated-voice.wav')
    result['checks']['actual_voice_job_done'] = json.loads((EVIDENCE / 'voice-job.json').read_text(encoding='utf-8'))['status'] == 'done'
    video_job = json.loads((ROOT / 'docs/change-records/2026-10-09-original-image-video/video-job.json').read_text(encoding='utf-8'))
    detection_job = json.loads((ROOT / 'docs/change-records/2026-10-09-original-image-video/detection-job.json').read_text(encoding='utf-8'))
    report = json.loads((assets / 'detection-original-report.json').read_text(encoding='utf-8'))
    result['checks']['actual_video_job_done'] = video_job['status'] == 'done' and video_job['model'] == 'sadtalker' and video_job['result']['scene'] == 'original'
    result['checks']['no_prepared_portrait_in_current_readme'] = 'prepared-portrait.png' not in zh and 'prepared-portrait.png' not in en
    result['checks']['shared_protocol_and_handoff'] = all((ROOT / name).exists() for name in ['docs/AI-HANDOFF.md','CLAUDE.md','AGENTS.md'])
    original = json.loads((ROOT / 'docs/change-records/2026-10-09-original-image-video/original-image-proof.json').read_text(encoding='utf-8'))
    result['checks']['actual_input_image_unmodified'] = original['image_unmodified'] and original['scene_text_ignored']
    result['checks']['report_matches_actual_job'] = detection_job['status'] == 'done' and detection_job['result'] == report
    result['checks']['actual_report_summary'] = report['summary'] == {'total': 6, 'completed': 5, 'passed': 1, 'failed': 4, 'uncertain': 1}
    result['checks']['no_cloud_result_in_demo'] = all(method['id'] != 'truthscan' for method in report['methods'])

    restored = ['facebook-scam/video-forensics-web/build/sites-vite-plugin.ts',
                'local-media/detector-runtime/networks-init.py',
                'local-media/detector-runtime/detectors-init.py',
                'local-media/detector-runtime/loss-init.py']
    result['checks']['restored_source_matches_original'] = all(
        (ROOT / name).read_bytes() == (Path('D:/project/NZ/cv') / name).read_bytes() for name in restored)
    for name in restored:
        if name.endswith('.py'):
            ast.parse((ROOT / name).read_text(encoding='utf-8'))
    test_paths = restored + ['docs/showcase/sadtalker-original-demo.mp4', 'docs/showcase/reference-voice.wav',
                             '.env.local', 'local-media/tokenhub.env', 'models/private.gguf',
                             'local-media/data/private/output.mp4', 'local-media/facebook-browser/state.json',
                             'facebook-scam/video-forensics-web/build/unrelated-output.json',
                             'local-media/detector-runtime/unrelated-output.json']
    ignored = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '--no-index', '-z', '--stdin'],
                             input=('\0'.join(test_paths) + '\0').encode(), capture_output=True)
    if ignored.returncode not in (0, 1):
        raise RuntimeError(ignored.stderr.decode(errors='replace'))
    matched = set(ignored.stdout.decode().rstrip('\0').split('\0'))
    result['checks']['targeted_ignore_exceptions_only'] = not any(name in matched for name in test_paths[:6]) and all(name in matched for name in test_paths[6:])
    dependency_paths = ['facebook-scam/video-forensics-web/package.json',
                        'facebook-scam/video-forensics-web/package-lock.json',
                        'facebook-scam/video-forensics-web/pnpm-lock.yaml']
    result['checks']['dependency_files_unchanged'] = all(
        subprocess.run(['git', '-C', str(ROOT), 'show', '3da4be09aaaed90714dfdbe144dbfc137b163f80:' + name],
                       capture_output=True, check=True).stdout == (ROOT / name).read_bytes()
        for name in dependency_paths)
    build = json.loads((EVIDENCE / 'build-check.json').read_text(encoding='utf-8'))
    result['checks']['frontend_build_passed_with_failure_retained'] = build['first_build']['exit'] != 0 and build['second_build']['exit'] == 0

    private_strings = ['ray.hunt.127', 'gabriel.iancic', 'raysmum@gmail.com', 'wxid_']
    for name in ['README.md', 'README.en.md', 'docs/showcase/PROVENANCE.md', 'docs/showcase/detection-report.json']:
        content = (ROOT / name).read_text(encoding='utf-8')
        if any(value in content for value in private_strings):
            result['failures'].append('private source material in public README/showcase text: ' + name)
        if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}', content):
            result['failures'].append('credential-like content: ' + name)
    for name, passed in result['checks'].items():
        if not passed:
            result['failures'].append('failed check: ' + name)
    result['visual_qa'] = ('Three actual video previews inspected; workbench screenshots remain the earlier accepted captures, not new screenshots of all three jobs.' if progressive else 'Real current video/detection UI captured with user-approved existing Playwright/Edge and genuine completed-job replay; no source changes or extra inference for capture. Collection captures exclude private history.')
    (Path(output) if output else EVIDENCE / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checks': result['checks'], 'links': len(result['links']), 'assets': len(result['media']), 'failures': result['failures']}, ensure_ascii=False))
    raise SystemExit(bool(result['failures']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='Save current checks separately from historical acceptance evidence')
    main(parser.parse_args().output)
