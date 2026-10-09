import unittest

import _paths  # noqa: F401
from video_profiles import VIDEO_PROFILES, video_profile


class VideoProfileTests(unittest.TestCase):
    def test_each_model_has_one_explicit_visual_path(self):
        self.assertEqual(set(VIDEO_PROFILES), {
            "sadtalker", "echomimic_v1", "joyvasa",
            "echomimic_v3_flash", "tokenhub_humanactor",
        })
        for profile in VIDEO_PROFILES.values():
            self.assertIn(profile["portrait_layout"], {"square", "portrait"})
            self.assertIn(profile["output_policy"], {"native", "crop_generated_square"})
            self.assertGreater(profile["max_seconds"], 0)

    def test_only_sadtalker_crops_renderer_padding(self):
        cropped = [name for name, profile in VIDEO_PROFILES.items()
                   if profile["output_policy"] == "crop_generated_square"]
        self.assertEqual(cropped, ["sadtalker"])
        self.assertEqual(video_profile("tokenhub_humanactor")["portrait_layout"], "portrait")

    def test_unknown_model_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "不支持"):
            video_profile("unknown")


if __name__ == "__main__":
    unittest.main()
