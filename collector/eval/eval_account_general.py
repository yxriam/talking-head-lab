"""Evaluate the same local generation pipeline on caller-supplied account cases.

Inputs and rule-generated drafts are recorded separately from actual Qwen output.
The HTTP mock only feeds that real output to the existing bridge validator.
"""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import _paths  # noqa: F401
import account_llm
import account_risk
import local_account_model


def prepare(case):
    report = account_risk.analyze(case['result'])
    return report, account_llm.prepare_material(report) if report['analysis_scope']['eligible'] else None


def checks(case, response):
    failures = []
    paragraphs = response.get('paragraphs', {})
    refs = []
    for language in ('zh', 'en'):
        items = paragraphs.get(language, [])
        if not 1 <= len(items) <= 2:
            failures.append(language + ': paragraph count')
        text = '\n'.join(item.get('text', '') for item in items).casefold()
        refs.append(set(value for item in items for value in item.get('evidence_ids', [])))
        for alternatives in case.get('acceptance', {}).get('required', {}).get(language, []):
            if not any(value.casefold() in text for value in alternatives):
                failures.append(language + ': missing ' + repr(alternatives))
        for value in case.get('acceptance', {}).get('forbidden', []):
            if value.casefold() in text:
                failures.append(language + ': unexpected ' + value)
    if refs[0] != refs[1]:
        failures.append('bilingual evidence mismatch')
    return failures


def evaluate(cases, output, root):
    if output.exists():
        raise FileExistsError('Refusing to overwrite prior model evidence: ' + str(output))
    # Freeze every input before any inference; case names never enter generation.
    prepared = [(case, *prepare(case)) for case in cases]
    data = dict(system=local_account_model.SYSTEM_PROMPT,
                model=local_account_model.MODEL,
                parameters=dict(temperature=0, thinking=False, context=6144, output_tokens=1500),
                input_sha256=hashlib.sha256(json.dumps(cases, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                semantic_review='pending; keyword checks do not establish semantic correctness', runs=[])
    output.parent.mkdir(parents=True, exist_ok=True)
    for case, report, material in prepared:
        row = dict(name=case['name'], raw_input=case['result'], material=material,
                   analysis_scope=report['analysis_scope'], acceptance=case.get('acceptance', {}))
        expected = case.get('acceptance', {}).get('account_kind')
        row['check_failures'] = [] if expected in (None, report['analysis_scope']['account_kind']) else ['account kind mismatch']
        if material is None:
            row['skipped'] = report['analysis_scope']['reason']
            row['validated_report'] = account_llm.rewrite(report)
            if case.get('acceptance', {}).get('required'):
                row['check_failures'].append('case expects model prose but account is not classified as personal')
            data['runs'].append(row)
            output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({key: row[key] for key in ('name', 'analysis_scope', 'skipped', 'check_failures')}, ensure_ascii=False), flush=True)
            continue
        try:
            response = local_account_model.generate(material['draft'], material['evidence_ids'], root,
                                                    material['draft_en'], facts=material['facts'])
            row['response'] = response
            row['check_failures'].extend(checks(case, response))
            # Actual Qwen inference has already completed. Only the HTTP transport is mocked.
            with patch.object(account_llm, 'call', return_value=response):
                row['validated_report'] = account_llm.rewrite(report)
        except Exception as error:
            row['error'] = str(error)
        data['runs'].append(row)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({key: value for key, value in row.items()
                          if key in {'name', 'error', 'check_failures', 'response'}}, ensure_ascii=False), flush=True)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--cases', type=Path, help='JSON list of name/result/acceptance cases')
    source.add_argument('--result', type=Path, help='Any collected account result JSON')
    parser.add_argument('--output', type=Path, required=True, help='New result file; existing files are never overwritten')
    parser.add_argument('--root', type=Path, default=Path('/opt/media-models'))
    args = parser.parse_args()
    if args.cases:
        cases = json.loads(args.cases.read_text(encoding='utf-8'))
    else:
        cases = [dict(name=args.result.stem, result=json.loads(args.result.read_text(encoding='utf-8')))]
    if not isinstance(cases, list) or not cases:
        parser.error('Expected a nonempty case list')
    data = evaluate(cases, args.output, args.root)
    return int(any(row.get('error') or row.get('check_failures') for row in data['runs']))


if __name__ == '__main__':
    raise SystemExit(main())
