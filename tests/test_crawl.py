"""API boundaries and a real Playwright run on a local, clearly labelled fixture.

The fixture replaces Facebook/CDN responses; these are not real Facebook data.
"""

import base64
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import uuid
import zipfile
from pathlib import Path
from threading import Event
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
import _paths  # noqa: F401
import crawl_server as server

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jO1cAAAAASUVORK5CYII=')
FIXTURE = '''<html><head><meta charset="utf-8"><title>Local test fixture</title></head><body><main role="main">
<h1>本地测试页面</h1><article role="article"><time datetime="2026-10-08">2026-10-08</time><span aria-label="Public">🌐</span><p dir="auto">采集测试文字。</p></article><p style="display:none">隐藏文字</p>
<img width="128" height="128" alt="本地测试图片" src="https://scontent.fbcdn.net/test.png">
<img width="128" height="128" alt="重复图片" src="https://scontent.fbcdn.net/test.png">
<a href="https://www.facebook.com/videos/123/">视频来源</a></main></body></html>'''


class CrawlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.patches = [patch.object(server,'DATA',root/'data'), patch.object(server,'PROFILE',root/'profile'),
                        patch.object(server,'jobs',{}), patch.object(server,'stops',{}),
                        patch.object(server.account_llm,'status',return_value={'ready':False,'reason':'Test stub'}),
                        patch.object(server.account_llm,'rewrite',side_effect=lambda report:report)]
        for item in self.patches:
            item.start()
        self.client = TestClient(server.app)

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def wait(self,identifier):
        deadline = time.monotonic()+30
        while time.monotonic()<deadline:
            job = self.client.get('/crawl/jobs/'+identifier).json()
            if job['status'] in server.TERMINAL:
                return job
            time.sleep(.1)
        self.fail('Fixture task timed out')

    def test_rejects_external_origins_and_non_facebook_targets(self):
        self.assertEqual(self.client.post('/crawl/browser',headers={'Origin':'https://example.com'}).status_code,403)
        for url in ['https://facebook.com.evil.test/', 'http://www.facebook.com/', 'https://localhost/',
                    'https://www.facebook.com@127.0.0.1/', 'https://www.facebook.com:8002/']:
            self.assertEqual(self.client.post('/crawl/jobs',json={'url':url}).status_code,422,url)
        self.assertEqual(self.client.post('/crawl/jobs',json={'url':'https://www.facebook.com/','max_scrolls':999}).status_code,422)
        self.assertEqual(self.client.get('/crawl/jobs/not-an-id').status_code,404)

    def test_real_browser_extraction_download_history_and_export(self):
        original_context = server.collector.open_context
        def fixture_context(playwright,profile):
            context = original_context(playwright,profile,headless=True)
            context.route('https://www.facebook.com/**',lambda route:route.fulfill(status=200,content_type='text/html',body=FIXTURE))
            context.route('https://scontent.fbcdn.net/**',lambda route:route.fulfill(status=200,content_type='image/png',body=PNG))
            return context
        transport = httpx.MockTransport(lambda request:httpx.Response(200,headers={'content-type':'image/png'},content=PNG))
        download_client = httpx.Client(transport=transport)
        with patch.object(server.collector,'open_context',side_effect=fixture_context), patch.object(server.collector.httpx,'Client',return_value=download_client):
            response = self.client.post('/crawl/jobs',json={'url':'https://www.facebook.com/test/','max_scrolls':1})
            self.assertEqual(response.status_code,200)
            job = self.wait(response.json()['id'])
        self.assertEqual(job['status'],'done',job)
        self.assertEqual(job['result']['title'],'Local test fixture')
        self.assertEqual(job['result']['analysis']['account_purpose']['label'],'无法确定')
        self.assertIn('账号类型：无法确定',job['result']['analysis']['conclusion'])
        self.assertIn('account type undetermined',job['result']['analysis']['conclusion_en'])
        text = [item['text'] for item in job['result']['text']]
        self.assertEqual(text,['本地测试页面','采集测试文字。'])
        self.assertEqual(job['result']['text'][1]['context'],'post')
        self.assertEqual(job['result']['text'][1]['date'],'2026-10-08')
        self.assertEqual(job['result']['scope']['audiences'],['Public'])
        images = [item for item in job['result']['media'] if item['kind']=='image']
        self.assertEqual(len(images),1)
        self.assertEqual(images[0]['status'],'downloaded')
        self.assertNotIn('src',images[0])
        self.assertEqual(self.client.get(images[0]['url']).content,PNG)
        partial = self.client.get(images[0]['url'],headers={'Range':'bytes=0-7'})
        self.assertEqual(partial.status_code,206)
        self.assertEqual(partial.content,PNG[:8])
        archive = self.client.get(f"/crawl/jobs/{job['id']}/export")
        with zipfile.ZipFile(io.BytesIO(archive.content)) as bundle:
            self.assertEqual(set(bundle.namelist()),{'result.json','text.txt','account-analysis.txt','media/'+images[0]['filename']})
            self.assertEqual(bundle.read('account-analysis.txt').decode('utf-8'),job['result']['analysis']['conclusion'])
        english_archive=self.client.get(f"/crawl/jobs/{job['id']}/export?language=en")
        self.assertEqual(english_archive.status_code,200)
        with zipfile.ZipFile(io.BytesIO(english_archive.content)) as bundle:
            self.assertEqual(bundle.read('account-analysis.txt').decode('utf-8'),job['result']['analysis']['conclusion_en'])
        self.assertEqual(self.client.get(f"/crawl/jobs/{job['id']}/export?language=invalid").status_code,422)
        server.jobs.clear()
        self.assertEqual(self.client.get('/crawl/jobs/'+job['id']).json()['status'],'done')
        self.assertEqual(len(self.client.get('/crawl/jobs').json()),1)
        refreshed=self.client.post('/crawl/jobs/'+job['id']+'/analyze')
        self.assertEqual(refreshed.status_code,200)
        self.assertEqual(refreshed.json()['version'],'3')
        self.assertFalse((server.directory(job['id'])/'export.zip').exists())
        self.assertFalse((server.directory(job['id'])/'export-en.zip').exists())
        self.assertEqual(self.client.get('/crawl/jobs/'+job['id']).json()['result']['analysis'],refreshed.json())
        refreshed_archive=self.client.get(f"/crawl/jobs/{job['id']}/export")
        with zipfile.ZipFile(io.BytesIO(refreshed_archive.content)) as bundle:
            exported=json.loads(bundle.read('result.json').decode('utf-8'))
            self.assertEqual(exported['analysis'],refreshed.json())
        refreshed_english=self.client.get(f"/crawl/jobs/{job['id']}/export?language=en")
        with zipfile.ZipFile(io.BytesIO(refreshed_english.content)) as bundle:
            self.assertEqual(bundle.read('account-analysis.txt').decode('utf-8'),refreshed.json()['conclusion_en'])
        if os.environ.get('CRAWL_UI_FIXTURE') == '1':
            # Optional, labelled fixture for verifying the actual Studio handoff.
            destination = server.ROOT/'crawl-data'/job['id']
            destination.mkdir(parents=True)
            job['result']['title']='本地集成测试（非 Facebook 实采）'
            job['result']['warnings']=['仅用于测试预览和素材交接；不是 Facebook 真实采集结果。']
            job['result']['text']=[
                {'text':'私人账号，个人生活记录','context':'profile_or_page','source_url':'https://www.facebook.com/test/'},
                {'text':'我正在找工作，请先核实招聘单位。','context':'post','date':'2026-10-08','source_url':'https://www.facebook.com/test/posts/1'},
                {'text':'订单号：DEMO1234','context':'post','date':'2026-10-08','source_url':'https://www.facebook.com/test/posts/2'},
            ]
            job['result']['analysis']=server.account_risk.analyze(job['result'])
            job['result']['warnings']=['模拟文字仅用于验证界面，不是 Facebook 实采或真实人物的风险结论。']
            job['counts']['text']=3
            for asset in images:
                shutil.copyfile(server.directory(job['id'])/asset['filename'], destination/asset['filename'])
            (destination/'job.json').write_text(json.dumps(job,ensure_ascii=False),encoding='utf-8')
            (destination/'result.json').write_text(json.dumps(job['result'],ensure_ascii=False),encoding='utf-8')
            (destination/'text.txt').write_text('\n'.join(text),encoding='utf-8')
            print('UI_FIXTURE_ID='+job['id'],flush=True)

    def test_login_failure_and_busy_task_cancellation_are_explicit(self):
        def blocked(options,profile,directory,stop,update):
            update(stage='opening',progress=5,message='测试等待')
            stop.wait(5)
            server.collector.check_cancel(stop)
        with patch.object(server.collector,'collect',side_effect=blocked):
            first = self.client.post('/crawl/jobs',json={'url':'https://www.facebook.com/test/'}).json()
            self.assertEqual(self.client.post('/crawl/jobs',json={'url':'https://www.facebook.com/test/'}).status_code,409)
            self.client.post(f"/crawl/jobs/{first['id']}/cancel")
            self.assertEqual(self.wait(first['id'])['status'],'cancelled')
        with patch.object(server.collector,'collect',side_effect=server.collector.LoginRequired('请先登录')):
            second = self.client.post('/crawl/jobs',json={'url':'https://www.facebook.com/test/'}).json()
            self.assertEqual(self.wait(second['id'])['status'],'needs_login')
            self.assertEqual(self.client.post('/crawl/jobs/'+second['id']+'/analyze').status_code,409)

    def test_media_redirects_cannot_read_local_services(self):
        requests=[]
        def respond(request):
            requests.append(str(request.url))
            return httpx.Response(302,headers={'location':'http://127.0.0.1:8002/health'})
        client = httpx.Client(transport=httpx.MockTransport(respond))
        context=type('Context',(),{'cookies':lambda self,url:[]})()
        with patch.object(server.collector.httpx,'Client',return_value=client):
            with self.assertRaises(ValueError):
                server.collector.download(context,{'kind':'image','src':'https://scontent.fbcdn.net/test.png'},Path(self.temp.name),Event())
        self.assertEqual(len(requests),1)
        self.assertFalse(list(Path(self.temp.name).glob('*.part')))

    def test_interrupted_history_is_not_left_running(self):
        identifier = uuid.uuid4().hex
        server.directory(identifier).mkdir(parents=True)
        server.persist({'id':identifier,'kind':'crawl','status':'running','source_url':'https://www.facebook.com/'})
        self.assertEqual(self.client.get('/crawl/jobs/'+identifier).json()['status'],'cancelled')

    def test_legacy_report_requires_refresh_instead_of_exporting_chinese_as_english(self):
        identifier=uuid.uuid4().hex
        server.directory(identifier).mkdir(parents=True)
        item={'id':identifier,'kind':'crawl','status':'done',
              'result':{'source_url':'https://www.facebook.com/test/','text':[],'media':[],
                        'analysis':{'version':'2','conclusion':'旧中文报告'}}}
        server.persist(item)
        response=self.client.get(f'/crawl/jobs/{identifier}/export?language=en')
        self.assertEqual(response.status_code,409)
        self.assertIn('Refresh analysis',response.json()['detail'])
        self.assertFalse((server.directory(identifier)/'export-en.zip').exists())

    def test_model_failure_does_not_overwrite_a_completed_report(self):
        identifier=uuid.uuid4().hex
        server.directory(identifier).mkdir(parents=True)
        result={'source_url':'https://www.facebook.com/test/','text':[],'media':[],
                'analysis':{'generation':{'kind':'llm','model':'previous model'},'conclusion':'Previous verified result'}}
        server.persist({'id':identifier,'kind':'crawl','status':'done','result':result})
        with patch.object(server.account_llm,'rewrite',side_effect=server.account_llm.ModelError('模型暂不可用')):
            response=self.client.post(f'/crawl/jobs/{identifier}/analyze')
        self.assertEqual(response.status_code,503)
        self.assertEqual(self.client.get(f'/crawl/jobs/{identifier}').json()['result'],result)


if __name__=='__main__':
    if '--ui-fixture' in sys.argv:
        os.environ['CRAWL_UI_FIXTURE']='1'
        unittest.main(argv=[sys.argv[0],'CrawlTests.test_real_browser_extraction_download_history_and_export'])
    else:
        unittest.main()
