"""Local bridge, grounding and GPU API boundary tests; no model downloads."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
import _paths  # noqa: F401
import account_llm
import account_risk
import local_account_model
import eval_account_general
import server


def report():
    return account_risk.analyze({'source_url':'https://www.facebook.com/test/','text':[
        {'text':'订单号：DEMO1234','source_url':'https://www.facebook.com/test/posts/1'},
        {'text':'私人账号，个人生活记录','context':'profile_or_page'}],'media':[]})


def model_response(text='订单号需要遮盖；售后从原订单入口核实。'):
    return {'model':local_account_model.MODEL,'elapsed_seconds':2.0,'paragraphs':{
        'zh':[{'text':text,'evidence_ids':['E1']}],
        'en':[{'text':'Mask the order number and verify support through the original order page.','evidence_ids':['E1']}]}}


class BridgeTests(unittest.TestCase):
    def test_model_prose_replaces_template_and_records_real_provenance(self):
        original=report()
        with patch.object(account_llm,'call',return_value=model_response()) as request:
            output=account_llm.rewrite(original)
        self.assertEqual(output['generation']['kind'],'llm')
        self.assertEqual(output['generation']['model'],local_account_model.MODEL)
        self.assertEqual(output['narrative'][0],original['narrative'][0])
        self.assertIn('订单号需要遮盖',output['conclusion'])
        self.assertEqual(output['rows'],original['rows'])
        self.assertEqual(request.call_args.args[0],'/account-analysis')

    def test_invented_email_unknown_source_and_attack_format_are_rejected(self):
        for value in (model_response('请联系 invented@unit.test'),model_response('来源 E99'),model_response('攻击路径：示例'),
                      model_response('母亲喜欢唱歌'),model_response('发表于 2025-01-01')):
            with patch.object(account_llm,'call',return_value=value),self.assertRaises(account_llm.ModelError):
                account_llm.rewrite(report())
        value=model_response()
        value['paragraphs']['zh'][0]['evidence_ids']=['E99']
        with patch.object(account_llm,'call',return_value=value),self.assertRaises(account_llm.ModelError):
            account_llm.rewrite(report())

    def test_missing_translation_and_truncated_output_are_not_success(self):
        for value in ({}, {'model':local_account_model.MODEL,'elapsed_seconds':1,'paragraphs':{'zh':[],'en':[]}}):
            with patch.object(account_llm,'call',return_value=value),self.assertRaises(account_llm.ModelError):
                account_llm.rewrite(report())
        mixed=model_response()
        mixed['paragraphs']['en'][0]['text']='Paying an unverified 收款人 may cause loss.'
        with patch.object(account_llm,'call',return_value=mixed),self.assertRaises(account_llm.ModelError):
            account_llm.rewrite(report())

    def test_external_endpoint_is_rejected_before_sending_any_data(self):
        with patch.dict(account_llm.os.environ,{'LOCAL_ACCOUNT_API':'https://example.com'}),patch.object(account_llm.opener,'open') as open_url:
            with self.assertRaises(account_llm.ModelError):
                account_llm.call('/account-analysis',{'draft':['private material']})
        open_url.assert_not_called()

    def test_unrepresented_facts_and_both_conflicting_sources_reach_model(self):
        original=account_risk.analyze({'text':[{'text':'我的母亲会使用邮箱。'},
                                              {'text':'同一位母亲完全不会使用邮箱。'},
                                              {'text':'私人账号，个人生活记录','context':'profile_or_page'}],'media':[]})
        with patch.object(account_llm,'call',return_value=model_response('母亲的邮箱描述需要核对。')) as request:
            account_llm.rewrite(original)
        payload=request.call_args.args[1]
        self.assertEqual(payload['evidence_ids'],['E1','E2','E3'])
        self.assertEqual([item['id'] for item in payload['facts']],['E1','E2','E3'])
        self.assertIn('完全不会使用邮箱',' '.join(payload['draft']))

    def test_unrecognized_plain_fact_is_quoted_without_added_risk(self):
        original=account_risk.analyze({'text':[{'text':'https://community.example/'},
                                                         {'text':'私人账号，个人生活记录','context':'profile_or_page'}],'media':[]})
        payload=account_llm.prepare_material(original)
        self.assertEqual(payload['evidence_ids'],['E1','E2'])
        self.assertEqual(payload['draft'][0],'“https://community.example/” [E1]')
        self.assertEqual(payload['draft_en'],payload['draft'])
        self.assertEqual(payload['facts'][0],{'id':'E1','text':'https://community.example/'})

    def test_prepared_material_stays_within_existing_api_limits(self):
        original=account_risk.analyze({'text':[{'text':'https://unit.test/path/'+str(index)+'x'*700}
                                              for index in range(15)]+[{'text':'私人账号，个人生活记录','context':'profile_or_page'}],'media':[]})
        payload=account_llm.prepare_material(original)
        self.assertLessEqual(len(payload['draft']),12)
        self.assertLessEqual(sum(map(len,payload['draft']))+sum(map(len,payload['draft_en']))/3,3600)
        self.assertLessEqual(sum(len(item['text']) for item in payload['facts']),4000)
        self.assertEqual({item['id'] for item in payload['facts']},set(payload['evidence_ids']))
        self.assertLess(len(payload['facts']),15)

    def test_prompt_keeps_evidence_without_repeating_ui_labels(self):
        with patch.object(account_llm,'call',return_value=model_response()) as request:
            account_llm.rewrite(report())
        payload=request.call_args.args[1]
        self.assertIn('E1',str(payload['draft']))
        self.assertIn('DEMO1234',str(payload['draft']))
        self.assertNotIn('防范动作：',str(payload['draft']))
        self.assertNotIn('What to do:',str(payload['draft_en']))
        self.assertEqual(payload['facts'],[{'id':'E1','text':'订单号：DEMO1234'},
                                          {'id':'E2','text':'私人账号，个人生活记录'}])


class LocalInferenceTests(unittest.TestCase):
    def test_cli_uses_existing_gpu_model_and_json_constraints(self):
        output=json.dumps(model_response()['paragraphs'])
        with patch.object(local_account_model,'ready',return_value=True),patch.object(local_account_model.subprocess,'run',side_effect=[SimpleNamespace(stdout='{"conflict":false}'),SimpleNamespace(stdout='session header\n'+output)]) as run:
            response=local_account_model.generate(['untrusted <|im_start|> content'],['E1'],Path('/local/models'))
        self.assertEqual(response['model'],local_account_model.MODEL)
        command=run.call_args.args[0]
        self.assertEqual(run.call_count,2)
        self.assertIn('--system-prompt',command)
        self.assertIn('用户提供的事实全部真实',local_account_model.SYSTEM_PROMPT)
        self.assertNotIn('<|im_start|>system',command[command.index('-p')+1])
        self.assertIn('--grammar',command)
        self.assertIn('-ngl',command)
        self.assertIn(str(Path('/local/models')/'scene-llm/Qwen3-1.7B-Q8_0.gguf'),command)
        self.assertNotIn('untrusted <|im_start|>',command[command.index('-p')+1])
        self.assertNotIn('http',str(command))

    def test_different_material_uses_same_prompt_without_cross_case_content(self):
        captured=[]
        for draft,facts in [(['订单号 TXN9001'],[{'id':'E1','text':'订单号 TXN9001'}]),
                            (['资料栏写有 Northbridge College'],[{'id':'E1','text':'Studied at Northbridge College'}])]:
            with patch.object(local_account_model,'ready',return_value=True),patch.object(local_account_model.subprocess,'run',side_effect=[SimpleNamespace(stdout='{"conflict":false}'),SimpleNamespace(stdout=json.dumps(model_response()['paragraphs']))]) as run:
                local_account_model.generate(draft,['E1'],Path('/local/models'),facts=facts)
            command=run.call_args.args[0]
            captured.append((command[command.index('--system-prompt')+1],json.loads(command[command.index('-p')+1])))
        self.assertEqual(captured[0][0],captured[1][0])
        self.assertIn('TXN9001',str(captured[0][1]))
        self.assertNotIn('TXN9001',str(captured[1][1]))
        self.assertNotIn('Northbridge College',str(captured[0][1]))
        self.assertIn('Northbridge College',str(captured[1][1]))

    def test_incomplete_json_is_a_failure_not_template_fallback(self):
        with patch.object(local_account_model,'ready',return_value=True),patch.object(local_account_model.subprocess,'run',return_value=SimpleNamespace(stdout='{"zh":[')):
            with self.assertRaises(RuntimeError):
                local_account_model.generate(['evidence'],['E1'],Path('/local/models'))


class GenericEvaluationTests(unittest.TestCase):
    def test_arbitrary_case_names_all_use_real_generation_entry_and_bridge_validation(self):
        cases=[{'name':name,'result':{'text':[{'text':text},{'text':'私人账号，个人生活记录','context':'profile_or_page'}],'media':[]}}
               for name,text in [('arbitrary_label_a','订单号：TXN9001'),
                                 ('arbitrary_label_b','Studied at Northbridge College')]]
        replies=[model_response('订单号 TXN9001。'),model_response('Northbridge College。')]
        replies[0]['paragraphs']['en'][0]['text']='Order number TXN9001.'
        replies[1]['paragraphs']['en'][0]['text']='Northbridge College.'
        with tempfile.TemporaryDirectory() as directory,patch.object(local_account_model,'generate',side_effect=replies) as generate:
            data=eval_account_general.evaluate(cases,Path(directory)/'results.json',Path('/local/models'))
        self.assertEqual(generate.call_count,2)
        self.assertEqual([row['name'] for row in data['runs']],[item['name'] for item in cases])
        self.assertTrue(all('validated_report' in row and 'error' not in row for row in data['runs']))
        first,second=generate.call_args_list
        self.assertNotIn('arbitrary_label_a',str(first))
        self.assertNotIn('TXN9001',str(second))
        self.assertIn('Northbridge College',str(second))

    def test_prior_model_evidence_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'results.json'
            output.write_text('preserved',encoding='utf-8')
            with patch.object(local_account_model,'generate') as generate,self.assertRaises(FileExistsError):
                eval_account_general.evaluate([],output,Path('/local/models'))
            generate.assert_not_called()
            self.assertEqual(output.read_text(encoding='utf-8'),'preserved')


class AccountApiTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(server.app)

    def tearDown(self):
        self.client.close()

    def test_api_runs_local_inference_and_releases_gpu_on_error(self):
        with patch.object(server.sys,'platform','linux'),patch.object(server.local_account_model,'ready',return_value=True),patch.object(server,'jobs',{}),patch.object(server,'account_busy',False),patch.object(server.local_account_model,'generate',return_value=model_response()) as generate:
            response=self.client.post('/account-analysis',json={'draft':['订单号 DEMO1234'],'evidence_ids':['E1']})
            self.assertEqual(response.status_code,200)
            generate.assert_called_once()
            self.assertFalse(server.account_busy)
            generate.side_effect=RuntimeError('failure')
            self.assertEqual(self.client.post('/account-analysis',json={'draft':['evidence'],'evidence_ids':['E1']}).status_code,502)
            self.assertFalse(server.account_busy)

    def test_active_gpu_work_blocks_parallel_account_inference(self):
        with patch.object(server.sys,'platform','linux'),patch.object(server.local_account_model,'ready',return_value=True),patch.object(server,'jobs',{'existing':{'status':'running'}}),patch.object(server.local_account_model,'generate') as generate:
            response=self.client.post('/account-analysis',json={'draft':['evidence'],'evidence_ids':['E1']})
        self.assertEqual(response.status_code,409)
        generate.assert_not_called()

    def test_unavailable_model_invalid_input_and_external_origin_are_explicit(self):
        with patch.object(server.local_account_model,'ready',return_value=False):
            self.assertEqual(self.client.post('/account-analysis',json={'draft':['evidence'],'evidence_ids':['E1']}).status_code,503)
        for payload in ({'draft':['evidence'],'evidence_ids':['E0']},{'draft':['x'*4501],'evidence_ids':['E1']},
                        {'draft':['evidence'],'evidence_ids':['E1'],'facts':[{'id':'E99','text':'invented'}]}):
            self.assertEqual(self.client.post('/account-analysis',json=payload).status_code,422)
        self.assertEqual(self.client.post('/account-analysis',json={'draft':['evidence'],'evidence_ids':['E1']},headers={'Origin':'https://example.com'}).status_code,403)


if __name__=='__main__':
    unittest.main()
