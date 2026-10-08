"""Freeze eligible source files; never copy Git metadata or runtime data.

Run with the existing local-media Python; no packages required.
Inventory only by default. --copy requires an existing Git checkout.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

SOURCE = Path('D:/project/cv')
TARGET = Path('D:/project/facebook/talking-head-lab')
EVIDENCE = SOURCE / 'docs/change-records/2026-10-08-engineering-governance'
SKIP_NAMES = {'.git', '.venv', 'venv', 'node_modules', '__pycache__',
              '.pnpm-store', '.next', '.vinext', '.cache', '.npm-cache',
              '.pytest_cache', '.mypy_cache', '.ruff_cache', 'dist', 'build'}
SKIP_ROOTS = {'output', 'acceptance', 'benchmark-results', 'calibration-preview',
              'gfpgan', 'verify_facebook_scam_clone', '.codex', '.agents', '\uf05c'}
SKIP_RELATIVE = {'tools/TinyTeX', 'tools/tectonic_pkg', 'tools/tinytex_pkg',
                 'local-media/ray-prompt-eval', 'local-media/warning-eval',
                 'handoff', 'facebook_capture/output', 'facebook_intel_pipeline/runs'}
TEXT_EXTENSIONS = {'.py', '.ps1', '.sh', '.cmd', '.md', '.mdc', '.txt', '.tex',
                   '.bib', '.ts', '.tsx', '.js', '.mjs', '.cjs', '.html', '.css',
                   '.json', '.yaml', '.yml', '.toml', '.lock', '.example',
                   '.conf', '.service', '.svg', '.csv', '.xml', '.patch'}
BINARY_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.ico', '.woff', '.woff2'}
SECRET_PATTERNS = {
    'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'github-token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'aws-access-key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'openai-style-key': r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b',
    'credential-url': r'https?://[^\s/\"\']+:[^\s/@\"\']+@',
    'secret-literal': r'''(?im)^[ \t]*(?:["']?(?:[A-Z_]*(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|PASSWORD|SECRET_ID))["']?)[ \t]*[:=][ \t]*["']?([A-Za-z0-9_+/=-]{20,})''',
}


def export_content(path):
    data = path.read_bytes()
    if path.suffix.lower() not in TEXT_EXTENSIONS and path.name != '.gitignore':
        return data
    content = data.decode('utf-8-sig')
    # Only historical, private local sample paths are redacted in the export.
    content = re.sub(r'D:\\xwechat_files\\[^"\n]+', r'D:\\project\\data\\reference.m4a', content)
    content = re.sub(r'/root/chatterbox_refs/[A-Za-z0-9_]+[.]m4a', '/root/chatterbox_refs/reference.m4a', content)
    content = re.sub(r'[\u4e00-\u9fff]{2,}路[0-9]+号', '示例地址', content)
    return content.encode('utf-8') if content != data.decode('utf-8-sig') else data


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    paths = []
    for folder, directories, files in os.walk(SOURCE, followlinks=False):
        relative_folder = Path(folder).relative_to(SOURCE).as_posix()
        directories[:] = [name for name in directories
                          if name not in SKIP_NAMES
                          and not (Path(folder) / name / 'pyvenv.cfg').is_file()
                          and not (relative_folder == '.' and name in SKIP_ROOTS)
                          and (Path(relative_folder) / name).as_posix() not in SKIP_RELATIVE]
        paths.extend((Path(folder) / name).relative_to(SOURCE).as_posix() for name in files)
    paths.sort()
    check = subprocess.run(['git', '--git-dir=' + str(SOURCE / 'facebook-scam/.git'),
                            '--work-tree=' + str(SOURCE), 'check-ignore', '--no-index',
                            '-z', '--stdin'], input=('\0'.join(paths) + '\0').encode(),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=SOURCE)
    if check.returncode not in (0, 1):
        raise RuntimeError(check.stderr.decode(errors='replace'))
    ignored = set(check.stdout.decode('utf-8').rstrip('\0').split('\0'))
    included, excluded, findings = [], [], []
    for name in paths:
        if name in ignored or name == 'docs/change-records/2026-10-08-engineering-governance/publication-manifest.json':
            continue
        path = SOURCE / name
        extension = path.suffix.lower()
        binary_asset = extension in BINARY_EXTENSIONS and (
            name.startswith('facebook-scam/video-forensics-web/public/') or
            name.startswith('figures/'))
        if extension not in TEXT_EXTENSIONS and path.name != '.gitignore' and not binary_asset:
            excluded.append({'path': name, 'reason': 'not a reviewed source/document/static-asset format'})
            continue
        if path.stat().st_size > 5_000_000:
            excluded.append({'path': name, 'reason': 'requires explicit large-file review'})
            continue
        if not binary_asset:
            content = export_content(path).decode('utf-8-sig')
            for label, pattern in SECRET_PATTERNS.items():
                for match in re.finditer(pattern, content):
                    findings.append({'path': name, 'line': content.count('\n', 0, match.start()) + 1,
                                     'kind': label})
        included.append({'path': name, 'bytes': path.stat().st_size, 'sha256': digest(path),
                         'export_sha256': hashlib.sha256(export_content(path)).hexdigest(),
                         'redacted': digest(path) != hashlib.sha256(export_content(path)).hexdigest()})
    return {'source': str(SOURCE), 'target': str(TARGET), 'files': included,
            'excluded_other_formats': excluded, 'secret_findings': findings,
            'ignored_file_count': len(ignored - {''}),
            'pruned_areas': sorted(SKIP_NAMES | SKIP_ROOTS | SKIP_RELATIVE)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--copy', action='store_true')
    args = parser.parse_args()
    result = inventory()
    (EVIDENCE / 'publication-manifest.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'files': len(result['files']),
                      'bytes': sum(row['bytes'] for row in result['files']),
                      'excluded_other_formats': result['excluded_other_formats'],
                      'secret_findings': result['secret_findings']}, ensure_ascii=False))
    if args.copy:
        if result['secret_findings']:
            raise SystemExit('Content findings must be reviewed before copying')
        top = subprocess.run(['git', '-C', str(TARGET), 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, check=True).stdout.strip()
        if Path(top).resolve() != TARGET.resolve():
            raise SystemExit('Target is not the expected Git checkout')
        for row in result['files']:
            source = SOURCE / row['path']
            destination = TARGET / row['path']
            if digest(source) != row['sha256']:
                raise SystemExit('Source changed after inventory: ' + row['path'])
            if destination.exists() and digest(destination) != row['export_sha256']:
                raise SystemExit('Target already differs; review before overwriting: ' + row['path'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(export_content(source))
            if digest(destination) != row['export_sha256']:
                raise SystemExit('Copy digest mismatch: ' + row['path'])
        print('SOURCE_COPY_SHA256_VERIFIED')


if __name__ == '__main__':
    main()
