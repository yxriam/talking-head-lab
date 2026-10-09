"""Product gating: classify purpose before any personal-account risk analysis."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import _paths  # noqa: F401
import account_llm
import account_risk
import crawl_server
import eval_account_general


def personal():
    return {'text':[{'text':'私人账号，个人生活记录','context':'profile_or_page'},
                    {'text':'我的邮箱：hello@personal.example','context':'post'}], 'media':[]}


def business():
    return {'text':[{'text':'本店营业时间为9点至18点；本公司官方账号','context':'profile_or_page'},
                    {'text':'我的母亲的邮箱是 family@unit.test；我正在找工作。','context':'post'}], 'media':[]}


def unknown():
    return {'text':[{'text':'订单号：ORDER6789','context':'post'}], 'media':[],
            'scope':{'audiences':['Public']}}


class AccountScopeTests(unittest.TestCase):
    def test_personal_evidence_reaches_existing_risk_analysis(self):
        with patch.object(account_risk,'_analyze_evidence',wraps=account_risk._analyze_evidence) as engine:
            report=account_risk.analyze(personal())
        engine.assert_called_once()
        self.assertEqual(report['analysis_scope']['account_kind'],'personal')
        self.assertTrue(report['analysis_scope']['eligible'])
        self.assertEqual(report['generation']['kind'],'rules')

    def test_business_and_unknown_never_enter_risk_engine_or_model(self):
        for raw,kind in [(business(),'business'),(unknown(),'undetermined')]:
            with self.subTest(kind=kind),patch.object(account_risk,'_analyze_evidence') as engine,patch.object(account_llm,'call') as call:
                report=account_llm.rewrite(account_risk.analyze(raw))
            engine.assert_not_called()
            call.assert_not_called()
            self.assertEqual(report['analysis_scope']['account_kind'],kind)
            self.assertEqual(report['generation']['kind'],'classification')
            self.assertNotIn('fallback_reason',report['generation'])
            for field in ('rows','priorities','protections','subjects'):
                self.assertEqual(report[field],[])
            self.assertEqual(len(report['narrative']),1)
            self.assertEqual(len(report['narrative_en']),1)
            self.assertNotIn('family@unit.test',report['conclusion'])
            self.assertNotIn('ORDER6789',report['conclusion'])

    def test_mixed_purpose_is_not_assumed_personal(self):
        raw=personal()
        raw['text'].append(business()['text'][0])
        report=account_risk.analyze(raw)
        self.assertEqual(report['analysis_scope']['account_kind'],'undetermined')
        self.assertFalse(report['analysis_scope']['eligible'])

    def test_public_visibility_does_not_turn_a_personal_account_into_business(self):
        raw=personal()
        raw['scope']={'audiences':['Public']}
        report=account_risk.analyze(raw)
        self.assertEqual(report['visibility']['label'],'公开')
        self.assertEqual(report['analysis_scope']['account_kind'],'personal')

    def test_creator_is_not_automatically_business_or_personal(self):
        raw={'display_name':'Alex Taylor','text':[{'text':'数字内容创作者'},
             {'text':'Alex Taylor 添加了 2 张照片'}, {'text':'Alex Taylor 添加了 3 张照片'}], 'media':[]}
        report=account_risk.analyze(raw)
        self.assertEqual(report['account_purpose']['subtype'],'公共创作者账号')
        self.assertEqual(report['analysis_scope']['account_kind'],'undetermined')
        self.assertFalse(report['analysis_scope']['eligible'])

    def test_legacy_risk_prose_or_tampered_scope_cannot_bypass_bridge_gate(self):
        report={'account_purpose':{'label':'公共账号','evidence_ids':['E1']},
                'analysis_scope':{'eligible':True}, 'generation':{'kind':'llm'},
                'narrative':['旧企业类型','旧风险段'], 'narrative_en':['Old business type','Old risk'],
                'rows':[{'risk':True}], 'priorities':[{'action':'旧动作'}], 'subjects':[{}]}
        with patch.object(account_llm,'call') as call:
            output=account_llm.rewrite(report)
        call.assert_not_called()
        self.assertEqual(output['generation']['kind'],'classification')
        self.assertFalse(output['analysis_scope']['eligible'])
        self.assertNotIn('旧风险段',output['conclusion'])
        self.assertEqual(output['rows'],[])

    def test_generic_evaluator_skips_nonpersonal_names_without_running_qwen(self):
        cases=[dict(name='arbitrary_a',result=business()),dict(name='arbitrary_b',result=unknown())]
        with tempfile.TemporaryDirectory() as directory,patch.object(eval_account_general.local_account_model,'generate') as generate:
            data=eval_account_general.evaluate(cases,Path(directory)/'gate.json',Path('/unused'))
        generate.assert_not_called()
        self.assertTrue(all('skipped' in row and 'response' not in row for row in data['runs']))

    def test_evaluator_does_not_count_skipped_required_prose_as_a_pass(self):
        cases=[dict(name='needs_personal_prose',result=unknown(),
                    acceptance={'required':{'zh':[['ORDER6789']]}})]
        with tempfile.TemporaryDirectory() as directory,patch.object(eval_account_general.local_account_model,'generate') as generate:
            data=eval_account_general.evaluate(cases,Path(directory)/'gate.json',Path('/unused'))
        generate.assert_not_called()
        self.assertTrue(data['runs'][0]['check_failures'])

    def test_refresh_returns_classification_with_gpu_offline(self):
        for raw in (business(),unknown()):
            with tempfile.TemporaryDirectory() as directory:
                item={'id':'c'*32,'kind':'crawl','status':'done','result':raw}
                with patch.object(crawl_server,'job',return_value=item),patch.object(crawl_server,'directory',return_value=Path(directory)),patch.object(crawl_server,'persist'),patch.object(crawl_server,'jobs',{}),patch.object(account_llm,'call') as call,TestClient(crawl_server.app) as client:
                    response=client.post('/crawl/jobs/'+item['id']+'/analyze')
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(response.json()['generation']['kind'],'classification')
                call.assert_not_called()
                saved=json.loads((Path(directory)/'result.json').read_text(encoding='utf-8'))
                self.assertEqual(saved['analysis']['rows'],[])


if __name__=='__main__':
    unittest.main()

