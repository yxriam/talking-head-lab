import unittest

from detect import learned_result, summarize_learned


def result(model, values, media_type="video"):
    return learned_result(model, model, values, "test", "test", media_type)


class ThresholdTests(unittest.TestCase):
    def test_low_gend_native_median_triggers_ai_vote(self):
        item = result("gend", [0.1, 0.2, 0.3])
        self.assertEqual(item["decision"], "fail")

    def test_gend_inside_real_envelope_votes_real(self):
        self.assertEqual(result("gend", [0.5, 0.5, 0.5])["decision"], "pass")

    def test_high_gend_minimum_triggers_ai_vote(self):
        self.assertEqual(result("gend", [0.9, 0.9, 0.9])["decision"], "fail")

    def test_npr_low_video_score_is_not_authenticity_evidence(self):
        self.assertEqual(result("npr", [0.0] * 20)["decision"], "uncertain")

    def test_any_calibrated_failure_triggers_video_verdict(self):
        methods = [
            result("gend", [0.5, 0.5, 0.5]),
            learned_result("ucf", "ucf", [0.1, 0.1, 0.1], "test", "test", "video"),
        ]
        self.assertEqual(summarize_learned(methods)["verdict"], "AI 生成倾向")

    def test_all_calibrated_passes_produce_real_verdict(self):
        methods = [result("gend", [0.5] * 8), result("ucf", [0.5] * 8)]
        self.assertEqual(summarize_learned(methods)["verdict"], "真实拍摄倾向")


if __name__ == "__main__":
    unittest.main()
