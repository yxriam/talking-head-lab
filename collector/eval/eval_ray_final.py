"""Run the final production generate function against Ray and control drafts."""
import json,re,time,argparse
from pathlib import Path
from unittest.mock import patch
import _paths  # noqa: F401
import account_risk,account_llm,local_account_model
ROOT=Path('/opt/media-models');FOLDER=Path(__file__).parent/'ray-prompt-eval'
def main():
 raw=json.loads((Path(__file__).parent/'crawl-data/e873f078b1b74fbd9229eaea779a11da/result.json').read_text(encoding='utf-8'))
 report=account_risk.analyze(raw)
 draft=[account_llm.prose_draft(v) for v in report['narrative'][1:]];english=[account_llm.prose_draft(v) for v in report['narrative_en'][1:]]
 ids=sorted(set(re.findall(r'\bE[1-9]\d*\b','\n'.join(draft))),key=lambda v:int(v[1:]))
 cases=[dict(name='ray',draft=draft,draft_en=english,ids=ids),
 dict(name='contradiction',draft=['我的母亲会使用邮箱。 [E1]','同一位母亲完全不会使用邮箱。 [E2]'],draft_en=['My mother can use email. [E1]','The same mother cannot use email at all. [E2]'],ids=['E1','E2']),
 dict(name='no_risk',draft=['官方联系邮箱是 support@shop.example。 [E1]'],draft_en=['The official contact email is support@shop.example. [E1]'],ids=['E1'])]
 data=dict(system=local_account_model.SYSTEM_PROMPT,runs=[])
 for case in cases:
  row=dict(case=case)
  try:
   facts=[f for f in report['source_facts'] if f['id'] in ids] if case['name']=='ray' else [{'id':identifier,'text':text} for identifier,text in zip(case['ids'],case['draft'])]
   response=local_account_model.generate(case['draft'],case['ids'],ROOT,case['draft_en'],facts=facts);row['response']=response
   if case['name']=='ray':
    with patch.object(account_llm,'call',return_value=response):row['report']=account_llm.rewrite(report)
  except Exception as e:row['error']=str(e)
  data['runs'].append(row);(FOLDER/'production-final.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in row.items() if k not in {'case','report'}},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
