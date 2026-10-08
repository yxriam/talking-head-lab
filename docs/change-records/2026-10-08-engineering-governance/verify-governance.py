"""Reproducible lightweight governance checks; no Git init or business changes."""
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path('D:/project/cv')
EVIDENCE = ROOT / 'docs/change-records/2026-10-08-engineering-governance'


def git(*args):
    return subprocess.run(['git', '--git-dir=' + str(ROOT / 'facebook-scam/.git'),
                           '--work-tree=' + str(ROOT), *args], cwd=ROOT,
                          capture_output=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    initial = json.loads((EVIDENCE / 'before-manifest.json').read_text(encoding='utf-8-sig'))
    results = {'local_links': [], 'ignore_cases': [], 'failures': []}
    patch = []
    after = []
    for row in initial:
        name = row['path']
        path = ROOT / name
        old = EVIDENCE / 'before' / name
        if row['existed'] and sha(old) != row['sha256']:
            results['failures'].append('snapshot digest mismatch: ' + name)
        before_text = old.read_bytes().decode('utf-8') if row['existed'] else ''
        current_text = path.read_bytes().decode('utf-8')
        patch.extend(difflib.unified_diff(before_text.splitlines(keepends=True),
                                          current_text.splitlines(keepends=True),
                                          fromfile='a/' + name if row['existed'] else '/dev/null',
                                          tofile='b/' + name))
        after.append({'path': name, 'sha256': sha(path)})
        if path.suffix in {'.md', '.mdc'}:
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', current_text):
                target = target.strip('<>').split('#', 1)[0]
                if not target or re.match(r'[a-zA-Z]+:', target):
                    continue
                valid = (path.parent / unquote(target)).exists()
                results['local_links'].append({'from': name, 'to': target, 'exists': valid})
                if not valid:
                    results['failures'].append('missing link: ' + name + ' -> ' + target)
    (EVIDENCE / '变更.patch').write_text(''.join(patch), encoding='utf-8', newline='')
    (EVIDENCE / 'after-manifest.json').write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding='utf-8')

    original = (EVIDENCE / 'before/AGENTS.md').read_text(encoding='utf-8')
    current = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    results['original_agents_lines_preserved'] = all(line in current for line in original.splitlines())
    if not results['original_agents_lines_preserved']:
        results['failures'].append('original AGENTS rule removed')
    for name in ['CLAUDE.md', '.cursor/rules/project.mdc']:
        content = (ROOT / name).read_text(encoding='utf-8')
        if not all(token in content for token in ['AGENTS.md', 'PROJECT.md', 'docs/specs/']):
            results['failures'].append('shared entry references missing: ' + name)
    results['cursor_frontmatter'] = (ROOT / '.cursor/rules/project.mdc').read_text(encoding='utf-8').startswith('---\ndescription:') and 'alwaysApply: true' in (ROOT / '.cursor/rules/project.mdc').read_text(encoding='utf-8')
    package = json.loads((ROOT / 'facebook-scam/video-forensics-web/package.json').read_text(encoding='utf-8'))
    results['node_engine'] = package['engines']['node']

    ignored = ['.env', '.env.local', '.env.production', 'local-media/tokenhub.env',
               'test.cookies', 'test.token', 'id_ed25519', 'test.pem',
               'models/model.gguf', 'checkpoints/test.safetensors', 'test.pth',
               'local-media/.venv/Lib/test.py', 'node_modules/test.js',
               'local-media/test.log', '.pnpm-store/test',
               'local-media/data/test/result.json', 'local-media/facebook-browser/test',
               'facebook_capture/facebook_state.json', 'facebook-scam/data/accounts/test.json',
               'facebook-scam/crawler/targets.json', 'local-media/ray-prompt-eval/source-facts.json',
               'local-media/calibration-cache/test', 'local-media/example.mp4', 'example.wav',
               'local-media/inspection/test.png', 'tools/TinyTeX/test.tex', '\uf05c/lib/test.py']
    eligible = ['AGENTS.md', 'CLAUDE.md', '.cursor/rules/project.mdc',
                'docs/specs/engineering-governance.md', 'docs/WORKFLOW.md',
                'docs/change-records/2026-10-08-engineering-governance/记录.md',
                'local-media/account_llm.py', 'local-media/server.py',
                'local-media/requirements.txt', 'local-media/tokenhub.env.example',
                'local-media/truthscan.env.example', '.env.example',
                'facebook-scam/video-forensics-web/app/studio/Studio.tsx',
                'facebook-scam/video-forensics-web/package-lock.json',
                'facebook-scam/video-forensics-web/pnpm-lock.yaml',
                'facebook-scam/video-forensics-web/public/logo.png',
                'figures/pipeline_gptimage2.png', 'tools/create_experiment_report.py',
                'facebook_capture/README.md', 'facebook_intel_pipeline/README.md']
    paths = ignored + eligible
    check = subprocess.run(
        ['git', '--git-dir=' + str(ROOT / 'facebook-scam/.git'), '--work-tree=' + str(ROOT),
         'check-ignore', '--no-index', '-z', '--stdin'], cwd=ROOT,
        input=('\0'.join(paths) + '\0').encode(), capture_output=True)
    if check.returncode not in (0, 1):
        results['failures'].append('git check-ignore failed')
    matched = set(check.stdout.decode('utf-8').rstrip('\0').split('\0'))
    for name in paths:
        expected = name in ignored
        results['ignore_cases'].append({'path': name, 'expected_ignored': expected, 'actual_ignored': name in matched})
        if expected != (name in matched):
            results['failures'].append('ignore mismatch: ' + name)

    status = subprocess.run(['git', '-C', str(ROOT / 'facebook-scam'), 'status', '--porcelain=v1'], capture_output=True, text=True, check=True).stdout
    baseline = (EVIDENCE / 'nested-git-before.txt').read_text(encoding='utf-8-sig')
    results['nested_status_unchanged'] = status.rstrip() == baseline.rstrip()
    if not results['nested_status_unchanged']:
        results['failures'].append('nested Git status changed')
    staged = subprocess.run(['git', '-C', str(ROOT / 'facebook-scam'), 'diff', '--cached', '--name-only'], capture_output=True, text=True, check=True).stdout
    results['nested_index_unchanged'] = staged.strip() == (EVIDENCE / 'nested-staged-before.txt').read_text(encoding='utf-8-sig').strip()
    if not results['nested_index_unchanged']:
        results['failures'].append('nested index changed')

    with tempfile.TemporaryDirectory(prefix='governance-rollback-') as temporary:
        folder = Path(temporary)
        for row in after:
            target = folder / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / row['path'], target)
        command = ['git', '-c', 'core.autocrlf=false', 'apply', '--no-index', '--reverse']
        checked = subprocess.run(command + ['--check', str(EVIDENCE / '变更.patch')], cwd=folder, capture_output=True, text=True, encoding='utf-8', errors='replace')
        applied = subprocess.run(command + [str(EVIDENCE / '变更.patch')], cwd=folder, capture_output=True, text=True, encoding='utf-8', errors='replace') if checked.returncode == 0 else checked
        results['reverse_patch_check_exit'] = checked.returncode
        results['reverse_patch_apply_exit'] = applied.returncode
        results['reverse_patch_restored'] = applied.returncode == 0 and all(
            sha(folder / row['path']) == row['sha256'] if row['existed'] else not (folder / row['path']).exists()
            for row in initial)
        if not results['reverse_patch_restored']:
            results['failures'].append('reverse patch did not restore exact snapshot')
            results['reverse_patch_error'] = applied.stderr
    (EVIDENCE / 'verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in results.items() if key not in ['local_links', 'ignore_cases']}, ensure_ascii=False))
    print('links:', len(results['local_links']), 'ignore cases:', len(results['ignore_cases']))
    raise SystemExit(bool(results['failures']))


if __name__ == '__main__':
    main()
