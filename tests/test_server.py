"""API boundary tests; these do not claim to test GPU inference."""

import io
import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import _paths  # noqa: F401
import server


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = patch.object(server, "DATA", Path(self.temporary.name))
        self.root.start()
        self.client = TestClient(server.app)

    def tearDown(self):
        self.client.close()
        self.root.stop()
        self.temporary.cleanup()

    def audio(self):
        data = io.BytesIO()
        with wave.open(data, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 1600)
        return data.getvalue()

    def test_upload_reuse_and_range_playback(self):
        content = self.audio()
        response = self.client.post('/media', files={'file': ('voice.wav',content,'audio/wav')})
        self.assertEqual(response.status_code,200)
        artifact = response.json()
        self.assertEqual(self.client.get(artifact['url']).content,content)
        partial = self.client.get(artifact['url'],headers={'Range':'bytes=0-15'})
        self.assertEqual(partial.status_code,206)
        self.assertEqual(partial.content,content[:16])
        # An unavailable model must fail explicitly, never return a fake result.
        unavailable = {kind: {'ready':False,'reason':'模型未安装'} for kind in ['voice','video','detect']}
        with patch.object(server,'capabilities',return_value=unavailable):
            result = self.client.post('/jobs',json={'kind':'voice','audio_id':artifact['id'],'text':'你好'})
        self.assertEqual(result.status_code,503)
        self.assertNotIn('result',result.json())

    def test_reject_external_origin_and_paths(self):
        result = self.client.post('/media',headers={'Origin':'https://example.com'},files={'file':('voice.wav',self.audio(),'audio/wav')})
        self.assertEqual(result.status_code,403)
        self.assertEqual(self.client.get('/media/not-an-id').status_code,404)
        self.assertEqual(self.client.post('/jobs',json={'kind':'voice','audio_id':'../../secret','text':'test'}).status_code,404)

    def test_reject_empty_unsupported_and_oversized_files(self):
        self.assertEqual(self.client.post('/media',files={'file':('voice.wav',b'','audio/wav')}).status_code,400)
        self.assertEqual(self.client.post('/media',files={'file':('page.html',b'test','text/html')}).status_code,415)
        with patch.object(server,'MAX_BYTES',10):
            self.assertEqual(self.client.post('/media',files={'file':('voice.wav',self.audio(),'audio/wav')}).status_code,413)
        self.assertEqual(list(server.DATA.iterdir()),[])

    def test_progress_is_derived_from_real_model_output(self):
        self.assertEqual(server.progress_from_log('voice', 'Sampling: 42%'), 50)
        self.assertEqual(server.progress_from_log('video', 'Face Renderer:: 50%'), 68)
        self.assertEqual(server.progress_from_log('video', ' 50%|#####| 3/6', 'echomimic_v1'), 56)
        self.assertEqual(server.progress_from_log('video', ' 50%|#####| 3/6', 'joyvasa'), 59)
        self.assertEqual(server.progress_from_log('video', ' 50%|#####| 3/6', 'echomimic_v3_flash'), 58)
        self.assertEqual(server.progress_from_log('detect', 'DETECTOR_PROGRESS 70'), 70)

    def test_video_model_is_validated_and_selected(self):
        ready = {kind:{'ready':True,'reason':''} for kind in ['voice','video','detect']}
        ready['video']['models'] = {name:{'ready':True,'reason':''} for name in ['sadtalker','echomimic_v1','joyvasa','echomimic_v3_flash']}
        with patch.object(server, 'capabilities', return_value=ready):
            image = self.client.post('/media', files={'file':('face.jpg',b'jpg','image/jpeg')}).json()
            audio = self.client.post('/media', files={'file':('voice.wav',self.audio(),'audio/wav')}).json()
            bad = self.client.post('/jobs', json={'kind':'video','image_id':image['id'],'audio_id':audio['id'],'model':'unknown'})
        self.assertEqual(bad.status_code, 400)
        self.assertIn('人像视频模型', bad.json()['detail'])

    def test_voice_accepts_video_and_records_reference_kind(self):
        video = self.client.post('/media', files={'file': ('reference.mp4', b'video-with-audio', 'video/mp4')}).json()
        ready = {kind: {'ready': True, 'reason': ''} for kind in ['voice', 'video', 'detect']}
        with patch.object(server, 'capabilities', return_value=ready), patch.object(server.pool, 'submit') as submit:
            response = self.client.post('/jobs', json={'kind': 'voice', 'audio_id': video['id'], 'text': '你好'})
        self.assertEqual(response.status_code, 200)
        submit.assert_called_once()
        request = json.loads((server.DATA / response.json()['id'] / 'request.json').read_text(encoding='utf-8'))
        self.assertEqual(request['reference_kind'], 'video')
        self.assertTrue(request['audio'].endswith('input.mp4'))

    def test_detection_accepts_images_but_rejects_audio(self):
        audio = self.client.post('/media', files={'file':('voice.wav',self.audio(),'audio/wav')}).json()
        ready = {kind:{'ready':True,'reason':''} for kind in ['voice','video','detect']}
        with patch.object(server,'capabilities',return_value=ready):
            response = self.client.post('/jobs',json={'kind':'detect','media_id':audio['id']})
        self.assertEqual(response.status_code,400)
        self.assertIn('图片或视频',response.json()['detail'])


    def test_video_readiness_does_not_require_background_models(self):
        models = server.DATA / "models"
        for name, marker in [('SadTalker', 'READY'), ('EchoMimic', 'READY'),
                             ('JoyVASA', 'READY'), ('EchoMimicV3', 'INFERENCE_VERIFIED')]:
            executable = models / name / '.venv/bin/python'
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'test fixture')
            (models / name / marker).write_bytes(b'')
        with patch.object(server, 'runtime', return_value=models), \
             patch.object(server.sys, 'platform', 'linux'), \
             patch.object(server.tokenhub, 'ready', return_value=(True, '')), \
             patch.object(server.truthscan, 'ready', return_value=(False, 'not configured')):
            result = server.capabilities()['video']
        self.assertTrue(result['ready'])
        self.assertTrue(all(model['ready'] for model in result['models'].values()))
        self.assertFalse((models / 'InstantID').exists())
        self.assertFalse((models / 'scene-llm').exists())
        with patch.object(server, 'runtime', return_value=models), \
             patch.object(server.sys, 'platform', 'win32'), \
             patch.object(server.tokenhub, 'ready', return_value=(True, '')):
            self.assertFalse(server.capabilities()['video']['ready'])

    def test_all_video_workers_receive_original_image_and_ignore_legacy_scene_text(self):
        original_bytes = b'synthetic unit-test image bytes'
        image = self.client.post('/media', files={'file': ('source.png', original_bytes, 'image/png')}).json()
        audio = self.client.post('/media', files={'file': ('voice.wav', self.audio(), 'audio/wav')}).json()
        original_path = server.DATA / image['id'] / 'input.png'
        ready = {'video': {'ready': True, 'models': {
            name: {'ready': True} for name in server.VIDEO_PROFILES}}}

        class CompletedProcess:
            returncode = 0
            def poll(self):
                return 0

        def render(command, **kwargs):
            self.assertEqual(Path(command[1]).name, 'generate.py')
            self.assertEqual(command[2], 'video')
            work = Path(command[3])
            request = json.loads((work / 'request.json').read_text(encoding='utf-8'))
            self.assertEqual(request['image'], str(original_path))
            self.assertEqual(Path(request['image']).read_bytes(), original_bytes)
            (work / 'output.mp4').write_bytes(b'simulated unit-test video')
            return CompletedProcess()

        def normalize_audio(command, **kwargs):
            self.assertEqual(command[0], 'ffmpeg')
            Path(command[-1]).write_bytes(b'simulated normalized audio')

        def cloud(image_path, audio_path, output_path, on_progress):
            self.assertEqual(Path(image_path), original_path)
            self.assertEqual(Path(image_path).read_bytes(), original_bytes)
            Path(output_path).write_bytes(b'simulated unit-test cloud video')

        with patch.dict(server.jobs, {}, clear=True), \
             patch.object(server, 'capabilities', return_value=ready), \
             patch.object(server.pool, 'submit'), \
             patch.object(server.subprocess, 'Popen', side_effect=render), \
             patch.object(server.subprocess, 'run', side_effect=normalize_audio), \
             patch.object(server.subprocess, 'check_output', return_value=b'4.68'), \
             patch.object(server.tokenhub, 'generate', side_effect=cloud):
            for name in server.VIDEO_PROFILES:
                with self.subTest(model=name):
                    response = self.client.post('/jobs', json={
                        'kind': 'video', 'image_id': image['id'], 'audio_id': audio['id'],
                        'model': name, 'text': 'Legacy background text must be ignored.',
                    })
                    self.assertEqual(response.status_code, 200)
                    identifier = response.json()['id']
                    work = server.DATA / identifier
                    request = json.loads((work / 'request.json').read_text(encoding='utf-8'))
                    self.assertEqual(request['image'], str(original_path))
                    self.assertNotIn('scene_text', request)
                    server.run_job(identifier, 'video')
                    self.assertEqual(server.jobs[identifier]['status'], 'done')
                    self.assertEqual(server.jobs[identifier]['result']['scene'], 'original')
                    for unused in ['generated-portrait.png', 'scene.json', 'scene-prompt.txt']:
                        self.assertFalse((work / unused).exists(), unused)


if __name__ == '__main__':
    unittest.main()
