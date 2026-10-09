"""Mirror only the user-provided Claude cleanup; preserve unrelated source candidates."""
import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

SOURCE = Path('D:/project/NZ/cv')
PUB = Path('D:/project/facebook/talking-head-lab')
RECORD = Path(__file__).resolve().parent
def git(*args):
    return subprocess.check_output(['git', *args], cwd=PUB, text=True, encoding='utf-8').strip()
assert git('rev-parse', 'HEAD') == '1488f63f1a5025ea85bcd1bd1b25c8e98e823c13'
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
before = RECORD / 'publication-before'
before.mkdir(exist_ok=True)
for rel in ['AGENTS.md', 'PROJECT.md', '.gitignore', 'tools/build_claude_handoff.py']:
    target = before / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PUB / rel, target)
archived = ['generate_ray_british_disclosed_recommendation_audio.py',
            'generate_ray_disclosed_recommendation_audio.py',
            'run_ray_british_head_recommendation_sadtalker.sh',
            'run_ray_disclosed_recommendation_sadtalker.sh',
            'run_ray_sadtalker_fullface.sh', 'tools/build_ray_methods_report.py']
archive = PUB / 'archive/legacy-demos'
archive.mkdir(parents=True, exist_ok=True)
for rel in archived:
    git('rm', '--cached', '--', rel)
    target = archive / Path(rel).name
    assert not target.exists()
    (PUB / rel).rename(target)
moves = []
for path in sorted((SOURCE / 'docs/proposal').iterdir()):
    if not path.is_file():
        continue
    git('ls-files', '--error-unmatch', '--', path.name)
    (PUB / 'docs/proposal').mkdir(parents=True, exist_ok=True)
    git('mv', '--', path.name, f'docs/proposal/{path.name}')
    # Most relocated files are unchanged. Apply only the independently checked path repair.
    if path.name in {'build_chinese_proposal_pdf.py', 'social_media_scam_awareness_proposal.tex'}:
        shutil.copy2(path, PUB / 'docs/proposal' / path.name)
    else:
        assert (PUB / 'docs/proposal' / path.name).read_bytes() == path.read_bytes()
    moves.append(path.name)
for rel in ['AGENTS.md', 'PROJECT.md']:
    path = PUB / rel
    text = path.read_text(encoding='utf-8')
    text = text.replace('Ray 的旧材料', '导师授权样本的旧材料').replace('旧 Ray 实测', '旧导师样本实测')
    assert 'Ray' not in text
    path.write_text(text, encoding='utf-8')
with (PUB / '.gitignore').open('a', encoding='utf-8') as handle:
    handle.write('\n# Archived one-off cloud demo scripts and media (kept locally, not published)\n/archive/\n')
path = PUB / 'tools/build_claude_handoff.py'
text = path.read_text(encoding='utf-8')
text = text.replace("'tools/build_ray_methods_report.py'", "'archive/legacy-demos/build_ray_methods_report.py'")
text = text.replace("'generate_ray_british_disclosed_recommendation_audio.py'", "'archive/legacy-demos/generate_ray_british_disclosed_recommendation_audio.py'")
ast.parse(text)
path.write_text(text, encoding='utf-8')
remaining = [rel for rel in git('ls-files').splitlines() if 'ray' in rel.lower()]
assert len(remaining) == 4 and all(rel.startswith('local-media/eval_ray_') for rel in remaining), remaining
for path in (PUB / 'docs/proposal').glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'))
for name in ['pipeline_gptimage2.png', 'evaluation_gptimage2.png']:
    assert (PUB / 'docs/proposal/../../figures' / name).is_file()
for rel in ['README.md', 'README.en.md']:
    text = (PUB / rel).read_text(encoding='utf-8')
    assert not any(name in text for name in moves + archived)
(RECORD / 'publication-mirror.json').write_text(json.dumps({
    'baseline': git('rev-parse', 'HEAD'), 'archived_source_files': archived,
    'relocated_proposals': moves, 'remaining_name_files': remaining,
    'path_repair': ['build_chinese_proposal_pdf.py ROOT', 'social_media_scam_awareness_proposal.tex figure paths'],
    'source_candidate_business_code_copied': False,
    'checks': 'AST, actual figure paths, original move bytes, README references, tracked name paths'},
    ensure_ascii=False, indent=2), encoding='utf-8')
print('CLAUDE_CLEANUP_MIRRORED_AND_INDEPENDENTLY_CHECKED')
