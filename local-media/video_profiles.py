"""One small source of truth for model-specific presentation choices."""

VIDEO_PROFILES = {
    "sadtalker": {
        "runtime": "SadTalker",
        "portrait_layout": "square",
        "output_policy": "crop_generated_square",
        "max_seconds": 60,
        "presentation": "square",
    },
    "echomimic_v1": {
        "runtime": "EchoMimic",
        "portrait_layout": "square",
        "output_policy": "native",
        "max_seconds": 20,
        "presentation": "square",
    },
    "joyvasa": {
        "runtime": "JoyVASA",
        "portrait_layout": "square",
        "output_policy": "native",
        "max_seconds": 60,
        "presentation": "square",
    },
    "echomimic_v3_flash": {
        "runtime": "EchoMimicV3",
        "portrait_layout": "square",
        "output_policy": "native",
        "max_seconds": 4,
        "presentation": "square",
    },
    "tokenhub_humanactor": {
        "runtime": "TokenHub HumanActor",
        "portrait_layout": "portrait",
        "output_policy": "native",
        "max_seconds": 60,
        "presentation": "portrait",
    },
}


def video_profile(name):
    try:
        return VIDEO_PROFILES[name]
    except KeyError as error:
        raise ValueError("不支持此人像视频模型") from error
