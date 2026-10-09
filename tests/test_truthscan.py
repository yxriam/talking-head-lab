import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _paths  # noqa: F401
import truthscan


class Response:
    def __init__(self, data): self.data = data
    def raise_for_status(self): return None
    def json(self): return self.data


class Client:
    def __init__(self, *args, **kwargs): self.queries = 0
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def post(self, url, **kwargs):
        if url.endswith("/detect-file"):
            return Response({"id":"dry-run-job", "status":"pending"})
        self.queries += 1
        return Response({"id":"dry-run-job", "status":"done", "result":0.82,
                         "result_details":{"ml":{"aggregate":{"prob_fake":0.82, "n_frames":24}}}})


class TruthScanTests(unittest.TestCase):
    def test_ready_only_when_key_is_present(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(truthscan.ready()[0])
        with patch.dict(os.environ, {"TRUTHSCAN_API_KEY":"test"}, clear=True):
            self.assertTrue(truthscan.ready()[0])

    def test_submit_poll_and_parse_without_network_or_credits(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "sample.mp4"
            video.write_bytes(b"0" * 2048)
            with patch.dict(os.environ, {"TRUTHSCAN_API_KEY":"dry-run"}), patch.object(truthscan.httpx, "Client", Client):
                result = truthscan.detect(video)
        self.assertEqual(result["id"], "truthscan")
        self.assertEqual(result["decision"], "fail")
        self.assertAlmostEqual(result["ai_probability"], 0.82)
        self.assertEqual(result["metrics"]["云端采样帧数"], 24)


if __name__ == "__main__":
    unittest.main()
