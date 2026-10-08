"""TokenHub adapter tests that never contact COS or the generation API."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tokenhub


class FakeCos:
    def __init__(self):
        self.uploaded = []
        self.deleted = []

    def upload_file(self, **kwargs):
        self.uploaded.append(kwargs)

    def get_presigned_download_url(self, **kwargs):
        return f"https://cos.example/{kwargs['Key']}?signature=test"

    def delete_object(self, **kwargs):
        self.deleted.append(kwargs['Key'])


class TokenHubTests(unittest.TestCase):
    def test_generation_submits_small_url_payload_and_cleans_both_objects(self):
        cos = FakeCos()
        submitted = []

        def post(url, payload, api_key, timeout=60):
            if url == tokenhub.SUBMIT_URL:
                submitted.append(payload)
                return {"id": "job-1", "status": "queued"}
            return {"id": "job-1", "status": "completed", "data": {"url": "https://result.example/video.mp4"}}

        settings = {"TOKENHUB_API_KEY": "key", "TENCENT_COS_SECRET_ID": "id",
                    "TENCENT_COS_SECRET_KEY": "secret", "TENCENT_COS_REGION": "ap-guangzhou",
                    "TENCENT_COS_BUCKET": "bucket"}
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            image, audio, output = work / "portrait.png", work / "voice.wav", work / "output.mp4"
            image.write_bytes(b"png")
            audio.write_bytes(b"wav")
            with patch.object(tokenhub, "configuration", return_value=(settings, [])), \
                 patch.object(tokenhub, "_cos_client", return_value=cos), \
                 patch.object(tokenhub, "_post", side_effect=post), \
                 patch.object(tokenhub, "_download") as download, \
                 patch.object(tokenhub.time, "sleep"):
                tokenhub.generate(image, audio, output)

        self.assertEqual(len(cos.uploaded), 2)
        self.assertEqual(len(cos.deleted), 2)
        self.assertEqual(set(cos.deleted), {item["Key"] for item in cos.uploaded})
        self.assertIn("audio_url", submitted[0])
        self.assertIn("image_url", submitted[0])
        self.assertNotIn("image_base64", submitted[0])
        self.assertLess(len(str(submitted[0])), 3000)
        download.assert_called_once()


if __name__ == "__main__":
    unittest.main()
