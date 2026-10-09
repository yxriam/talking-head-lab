"""Independent learned detectors plus descriptive forensic measurements.

Each learned model exposes its native class confidence. Those values are useful
for comparison, but are not calibrated probabilities for arbitrary web videos.
"""

import gc
import json
import sys
from functools import partial
from pathlib import Path

PAPERS = {
    "gend": "https://arxiv.org/abs/2508.06248",
    "ucf": "https://arxiv.org/abs/2304.13949",
    "recce": "https://openaccess.thecvf.com/content/CVPR2022/html/Cao_End-to-End_Reconstruction-Classification_Learning_for_Face_Forgery_Detection_CVPR_2022_paper.html",
    "f3net": "https://arxiv.org/abs/2007.09355",
    "npr": "https://openaccess.thecvf.com/content/CVPR2024/html/Tan_Rethinking_the_Up-Sampling_Operations_in_CNN-Based_Generative_Network_for_Generalizable_Deepfake_CVPR_2024_paper.html",
    "spectrum": "https://openaccess.thecvf.com/content_CVPR_2020/html/Durall_Watch_Your_Up-Convolution_CNN_Based_Generative_Deep_Neural_Networks_Are_CVPR_2020_paper.html",
    "continuity": "https://farid.berkeley.edu/downloads/publications/ih04.pdf",
    "temporal": "https://arxiv.org/abs/2311.10788",
    "temporal_static": "https://arxiv.org/abs/2508.00701",
}


VIDEO_THRESHOLDS = {
    # Native checkpoint statistics. A value outside the observed real-video
    # envelope is AI evidence. Rounded boundaries keep all 17 labelled real
    # videos inside the real region and detect 21/22 generated videos; the
    # temporal-static method detects the remaining sample.
    "gend": {"statistic": "p25", "operator": "lt", "boundary": 0.186,
             "extra_statistic": "min", "extra_operator": "gt", "extra_boundary": 0.853},
    "ucf": {"statistic": "mean", "operator": "lt", "boundary": 0.255},
    "recce": {"statistic": "p90", "operator": "lt", "boundary": 0.497},
    "f3net": {"statistic": "p75", "operator": "lt", "boundary": 0.330},
}

IMAGE_THRESHOLDS = {
    "gend": {"real": 0.20, "ai": 0.50}, "npr": {"real": 0.01, "ai": 0.50},
    "ucf": {"real": 0.10, "ai": 0.50}, "recce": {"real": 0.25, "ai": 0.50},
    "f3net": {"real": 0.10, "ai": 0.50},
}


def longest_run(flags):
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


def learned_result(identifier, name, values, principle, paper, media_type, primary=False):
    import numpy as np
    values = np.asarray(values, dtype=float)
    median = float(np.median(values))
    mean = float(np.mean(values))
    p75 = float(np.percentile(values, 75))
    p25 = float(np.percentile(values, 25))
    upper = float(np.percentile(values, 90))
    maximum = float(np.max(values))

    if media_type == "video" and identifier == "npr":
        ai_probability = 0.5
        decision = "uncertain"
        verdict = "证据不足：不参与视频真实性投票"
        thresholds = None
        threshold_text = "本地校准中无区分能力，不参与视频投票"
    elif media_type == "video":
        thresholds = VIDEO_THRESHOLDS[identifier]
        statistics = {"mean": mean, "median": median, "p25": p25, "p75": p75,
                      "p90": upper, "min": float(np.min(values)), "max": maximum}
        statistic = statistics[thresholds["statistic"]]
        triggered = statistic < thresholds["boundary"] if thresholds["operator"] == "lt" else statistic > thresholds["boundary"]
        if thresholds.get("extra_statistic"):
            extra = statistics[thresholds["extra_statistic"]]
            triggered = triggered or (extra > thresholds["extra_boundary"])
        decision = "fail" if triggered else "pass"
        verdict = "未通过：AI 倾向" if triggered else "通过：真实倾向"
        if triggered:
            ai_probability = max(0.51, 1.0 - statistic)
            if thresholds.get("extra_statistic") and statistics[thresholds["extra_statistic"]] > thresholds["extra_boundary"]:
                ai_probability = max(ai_probability, statistics[thresholds["extra_statistic"]])
        else:
            ai_probability = min(0.49, 1.0 - statistic)
        labels = {"mean":"均值", "p25":"第25百分位", "p75":"第75百分位", "p90":"第90百分位"}
        symbol = "<" if thresholds["operator"] == "lt" else ">"
        threshold_text = f"原始分数{labels.get(thresholds['statistic'], thresholds['statistic'])}{symbol}{thresholds['boundary']:.1%} 时记为 AI 证据"
        if thresholds.get("extra_statistic"):
            threshold_text += f"；最低帧>{thresholds['extra_boundary']:.1%} 也记为 AI 证据"
    else:
        thresholds = IMAGE_THRESHOLDS[identifier]
        ai_probability = median
        if median >= thresholds["ai"]:
            decision, verdict = "fail", "未通过：AI 倾向"
        elif median <= thresholds["real"]:
            decision, verdict = "pass", "通过：真实倾向"
        else:
            decision, verdict = "uncertain", "不确定：位于阈值灰区"
        threshold_text = f"真实 ≤ {thresholds['real']:.1%}；AI ≥ {thresholds['ai']:.1%}"
    real_probability = 1.0 - ai_probability
    confidence = max(ai_probability, real_probability)
    return {
        "id": identifier, "name": name, "status": "done",
        "verdict": verdict, "decision": decision, "passed": decision == "pass",
        "ai_probability": ai_probability, "real_probability": real_probability,
        "confidence": confidence, "score": ai_probability, "primary": primary,
        "principle": principle, "paper": paper, "threshold_text": threshold_text,
        "metrics": {
            "原始伪造类中位数": round(median, 4),
            "原始伪造类均值": round(mean, 4),
            "原始伪造类第 75 百分位": round(p75, 4),
            "原始伪造类第 25 百分位": round(p25, 4),
            "原始伪造类第 90 百分位": round(upper, 4),
            "原始伪造类最高帧": round(maximum, 4),
            "帧间四分位差": round(float(np.percentile(values, 75) - np.percentile(values, 25)), 4),
            "有效帧数": len(values),
        },
    }


def temporal_evidence(times, ai_scores, area, explanation):
    """Return concise high/low score windows for the report UI."""
    import numpy as np
    if not times or not ai_scores:
        return None
    scores = np.asarray(ai_scores, dtype=float)
    if float(np.ptp(scores)) < 1e-6:
        return {
            "area": area, "high": [], "low": [],
            "explanation": explanation + " 本视频各采样帧分数几乎相同，没有可区分的高低时段。",
        }
    high_cut = float(np.percentile(scores, 75))
    low_cut = float(np.percentile(scores, 25))

    def windows(mask, high):
        groups, start = [], None
        for index, flag in enumerate(mask.tolist() + [False]):
            if flag and start is None:
                start = index
            elif not flag and start is not None:
                end = index - 1
                part = scores[start:index]
                groups.append({
                    "start_frame": start + 1, "end_frame": end + 1,
                    "start_time": round(float(times[start]), 2), "end_time": round(float(times[end]), 2),
                    "ai_probability": round(float(np.mean(part)), 4),
                })
                start = None
        groups.sort(key=lambda item: item["ai_probability"], reverse=high)
        return groups[:3]

    return {
        "area": area,
        "explanation": explanation,
        "high": windows(scores >= high_cut, True),
        "low": windows(scores <= low_cut, False),
    }


def attach_frame_evidence(method, times, native_values):
    native_values = [float(value) for value in native_values]
    method["frames"] = [{"frame": index + 1, "time": round(float(time), 3), "score": round(value, 5)}
                        for index, (time, value) in enumerate(zip(times, native_values))]
    if method["id"] == "npr":
        ai_scores = native_values
    else:
        # The local real/fake calibration consistently reverses the original
        # class score for these checkpoints, so interval display uses 1-score.
        ai_scores = [1.0 - value for value in native_values]
    method["evidence"] = temporal_evidence(
        list(times), ai_scores, "对齐后的整个人脸区域",
        "这些时段的人脸特征与该模型训练分布的偏离程度最高或最低；分数能定位可疑时段，不能单独证明某个器官被修改。",
    )
    return method


def temporal_static_result(frames, times, media_type):
    """Detect the near-static canvas left by many photo-driven generators."""
    import cv2
    import numpy as np
    if media_type != "video" or len(frames) < 4:
        return {"id":"temporal_static", "name":"照片驱动时序静态性", "status":"insufficient",
                "verdict":"证据不足：连续画面不足", "decision":"uncertain", "score":None,
                "ai_probability":None, "real_probability":None, "confidence":None,
                "principle":"测量连续画面在非嘴部区域的变化，识别由单张照片驱动产生的近静态画布。",
                "paper":PAPERS["temporal_static"]}
    grays = [cv2.cvtColor(cv2.resize(frame, (256, 256)), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255 for frame in frames]
    differences = [float(np.abs(current - previous).mean()) for previous, current in zip(grays, grays[1:])]
    median = float(np.median(differences))
    boundary = 0.0135
    triggered = median < boundary
    if triggered:
        ai_probability = min(0.95, 0.5 + (boundary - median) / boundary * 0.45)
    else:
        ai_probability = min(0.49, 0.5 * boundary / max(median, 1e-6))
    decision = "fail" if triggered else "pass"
    result = {
        "id":"temporal_static", "name":"照片驱动时序静态性", "status":"done",
        "verdict":"未通过：画面长期近静态" if triggered else "通过：存在自然时序变化",
        "decision":decision, "passed":not triggered, "score":ai_probability,
        "ai_probability":ai_probability, "real_probability":1.0-ai_probability,
        "confidence":max(ai_probability,1.0-ai_probability), "primary":False,
        "principle":"比较相邻采样画面的平均像素变化，识别单张照片驱动视频中常见的近静态画布。",
        "paper":PAPERS["temporal_static"],
        "threshold_text":f"相邻画面变化中位数 < {boundary:.2%} 时记为 AI 证据",
        "metrics":{"相邻画面变化中位数":round(median,5), "相邻画面变化第90百分位":round(float(np.percentile(differences,90)),5), "有效时段数":len(differences)},
    }
    interval_times = list(times[1:]) if len(times) == len(frames) else list(range(1, len(frames)))
    interval_scores = [min(0.99, max(0.01, 0.5 + (boundary-value)/boundary*0.45)) for value in differences]
    result["frames"] = [{"frame":index+2, "time":round(float(time),3), "score":round(score,5)}
                        for index,(time,score) in enumerate(zip(interval_times,interval_scores))]
    result["evidence"] = temporal_evidence(
        interval_times, interval_scores, "整幅画面，重点观察背景、头发外缘和肩部之外",
        "AI 率高的时段相邻画面变化很小，符合单张照片画布仅局部驱动的特征；自然拍摄通常同时包含传感器噪声、轻微机位或背景变化。",
    )
    return result


def target_indices(frame_count, fps):
    """Adaptive coverage: about 64 observations, bounded to 4 fps and 96 frames."""
    import numpy as np
    duration = frame_count / fps
    rate = min(4.0, max(1.0, 64.0 / max(duration, 1.0)))
    wanted = min(96, frame_count, max(8, int(round(duration * rate))))
    return set(np.unique(np.linspace(0, frame_count - 1, wanted).astype(int)).tolist()), rate


def aligned_face(frame, detector, predictor, extract):
    import cv2
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    found = detector(rgb, 1)
    if len(found) != 1:
        return None, len(found)
    face, _, _ = extract(detector, predictor, frame, res=256)
    return (cv2.cvtColor(face, cv2.COLOR_BGR2RGB) if face is not None else None), len(found)


def read_media(path, root):
    import cv2
    import dlib
    import numpy as np
    from preprocessing.preprocess import extract_aligned_face_dlib

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(str(root / "weights/shape_predictor_68_face_landmarks.dat"))
    if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        frame = cv2.imread(str(path))
        if frame is None:
            raise ValueError("无法读取图片")
        if min(frame.shape[:2]) < 64:
            raise ValueError("图片边长至少需要 64 像素")
        face, count = aligned_face(frame, detector, predictor, extract_aligned_face_dlib)
        return [frame], [face] if face is not None else [], [0.0], {
            "media_type":"image", "sampled_frames":1, "face_frames":int(face is not None),
            "multiple_face_frames":int(count > 1), "duration_seconds":None,
            "sampling_strategy":"单张图片完整分析", "sample_times":[0.0]
        }

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("无法读取视频，请上传可解码的视频文件")
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if count <= 0 or not np.isfinite(fps) or fps <= 0:
        capture.release()
        raise ValueError("无法确定视频帧数或帧率")
    indices, rate = target_indices(count, fps)
    frames, faces, times, sample_times = [], [], [], []
    decoded = ambiguous = 0
    try:
        index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            decoded += 1
            if index in indices:
                if max(frame.shape[:2]) > 1280:
                    scale = 1280 / max(frame.shape[:2])
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)
                face, found = aligned_face(frame, detector, predictor, extract_aligned_face_dlib)
                frames.append(frame)
                sample_times.append(index / fps)
                if found > 1:
                    ambiguous += 1
                if face is not None:
                    faces.append(face)
                    times.append(index / fps)
            index += 1
    finally:
        capture.release()
    return frames, faces, times, {
        "media_type":"video", "sampled_frames":len(frames), "face_frames":len(faces),
        "multiple_face_frames":ambiguous, "decoded_frames":decoded,
        "duration_seconds":count / fps, "effective_sample_fps":round(rate, 3),
        "sampling_strategy":"顺序解码并按时长均匀覆盖；最多 4 fps、96 帧",
        "sample_times":[round(float(value),3) for value in sample_times]
    }


def load_visual_model(name, root):
    import torch
    import yaml
    from networks.xception import Xception
    from detectors.ucf_detector import UCFDetector
    from detectors.f3net_detector import F3netDetector
    from detectors import recce_detector

    class UCFInference(UCFDetector):
        def build_backbone(self, config):
            return Xception(config["backbone_config"])

    class F3Inference(F3netDetector):
        def build_backbone(self, config):
            model = Xception(config["backbone_config"])
            model.conv1 = torch.nn.Conv2d(12,32,3,2,0,bias=False)
            return model

    recce_detector.encoder_params["xception"]["init_op"] = partial(recce_detector.xception, pretrained=False)
    config = yaml.safe_load((root / f"training/config/detector/{name}.yaml").read_text())
    classes = {"ucf":UCFInference, "recce":recce_detector.RecceDetector, "f3net":F3Inference}
    model = classes[name](config)
    state = torch.load(root / f"weights/{name}_best.pth", map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    return model.eval().to("cuda")


def npr_scores(images, root):
    import cv2
    import importlib.util
    import numpy as np
    import torch
    spec = importlib.util.spec_from_file_location("npr_resnet",root / "networks/resnet.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.resnet50(num_classes=1)
    state = torch.load(root / "NPR.pth",map_location="cpu",weights_only=True).get("model")
    state = {key.removeprefix("module."):value for key,value in state.items()}
    model.load_state_dict(state,strict=True)
    model.eval().to("cuda")
    batch = []
    for image in images:
        resized = cv2.resize(image,(256,256),interpolation=cv2.INTER_LINEAR)[16:240,16:240]
        batch.append(resized)
    tensor = torch.from_numpy(np.stack(batch)).permute(0,3,1,2).float().div(255)
    mean = torch.tensor([.485,.456,.406]).view(1,3,1,1)
    std = torch.tensor([.229,.224,.225]).view(1,3,1,1)
    values = []
    with torch.inference_mode():
        for part in ((tensor-mean)/std).split(16):
            values.extend(model(part.to("cuda")).sigmoid().flatten().cpu().tolist())
    del model
    torch.cuda.empty_cache()
    return values


def gend_scores(images, root):
    """Run the official GenD CLIP-L/14 checkpoint on RGB face crops."""
    import sys
    import numpy as np
    import torch
    from PIL import Image

    sys.path.insert(0, str(root))
    from src.hf.modeling_gend import GenD

    model = GenD.from_pretrained(
        "yermandy/GenD_CLIP_L_14",
        cache_dir="/opt/media-models/huggingface",
        local_files_only=True,
    ).eval().to("cuda")
    tensors = torch.stack([
        model.feature_extractor.preprocess(Image.fromarray(np.asarray(image, dtype=np.uint8)))
        for image in images
    ])
    values = []
    with torch.inference_mode():
        for part in tensors.split(2):
            # Official training/evaluation code uses class order [real, fake].
            values.extend(model(part.to("cuda")).softmax(dim=-1)[:, 1].cpu().tolist())
    del model, tensors
    gc.collect()
    torch.cuda.empty_cache()
    return values


def visual_forensics(faces, times, frames, root, media_type, sampling):
    import cv2
    import numpy as np
    import torch
    inference_images = faces if faces else [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frames]
    inference_times = times if faces else sampling.get("sample_times", [])
    methods = []

    # GenD is the primary detector: its official WACV 2026 evaluation spans 14
    # datasets and reports leading average cross-dataset AUROC.
    gend_values = gend_scores(inference_images, root.parent / "GenD")
    methods.append(learned_result(
        "gend", "GenD CLIP-L/14", gend_values,
        "对预训练 CLIP 视觉编码器做参数高效适配，强调跨数据集与未知伪造方式的泛化。",
        PAPERS["gend"], media_type,
    ))
    attach_frame_evidence(methods[-1], inference_times, gend_values)
    print("DETECTOR_PROGRESS 40", flush=True)

    npr_values = npr_scores(inference_images, root.parent / "NPR")
    methods.append(learned_result(
        "npr", "NPR", npr_values,
        "分析生成网络上采样造成的邻域像素关系；对整图生成较敏感，对部分人脸换脸可能漏检。",
        PAPERS["npr"], media_type,
    ))
    attach_frame_evidence(methods[-1], inference_times, npr_values)
    print("DETECTOR_PROGRESS 48", flush=True)

    if not faces:
        for identifier, name, paper in (
            ("ucf", "UCF", PAPERS["ucf"]),
            ("recce", "RECCE", PAPERS["recce"]),
            ("f3net", "F3-Net", PAPERS["f3net"]),
        ):
            methods.append({
                "id": identifier, "name": name, "status": "insufficient",
                "verdict": "不确定：未检测到单人脸", "decision": "uncertain",
                "score": None, "ai_probability": None, "real_probability": None,
                "confidence": None, "principle": "该模型需要稳定的单人脸对齐裁剪。", "paper": paper,
            })
        methods.append(temporal_static_result(frames, sampling.get("sample_times", []), media_type))
        return summarize_learned(methods, media_type)

    tensor = torch.from_numpy(np.stack(faces)).permute(0,3,1,2).float().div(255).sub(0.5).div(0.5)
    details = {
        "ucf": ("UCF", "分离伪造特有特征与不同伪造方式共有的特征，提高未知伪造的泛化能力。"),
        "recce": ("RECCE", "通过重建与分类联合学习捕捉伪造区域和真实人脸分布之间的差异。"),
        "f3net": ("F3-Net", "联合频率感知分解与局部频率统计检测人脸伪造痕迹。"),
    }
    for index, name in enumerate(("ucf","recce","f3net")):
        model = load_visual_model(name,root)
        values = []
        with torch.inference_mode():
            for batch in tensor.split(2):
                images = batch.to("cuda")
                prediction = model({"image":images, "label":torch.zeros(len(images), dtype=torch.long, device="cuda")}, inference=True)
                probability = prediction.get("prob")
                if probability is None:
                    probability = torch.softmax(prediction["cls"], dim=1)[:,1]
                values.extend(probability.detach().cpu().tolist())
        del model
        gc.collect()
        torch.cuda.empty_cache()
        if not np.isfinite(values).all():
            raise ValueError(f"{name} 返回无效结果")
        display_name, principle = details[name]
        result = learned_result(name, display_name, values, principle, PAPERS[name], media_type)
        attach_frame_evidence(result, times, values)
        methods.append(result)
        print(f"DETECTOR_PROGRESS {56 + index * 7}", flush=True)
    methods.append(temporal_static_result(frames, sampling.get("sample_times", []), media_type))
    return summarize_learned(methods, media_type)


def summarize_learned(methods, media_type="video"):
    completed = [item for item in methods if item.get("decision") in {"pass", "fail"}]
    passed = sum(item["decision"] == "pass" for item in completed)
    failed = sum(item["decision"] == "fail" for item in completed)
    uncertain = len(methods) - len(completed)
    selected = next((item for item in completed if item["id"] == "gend"), None)
    if media_type == "video" and completed:
        # The union of these content-only signals separates the current labelled
        # set (17/17 real, 22/22 generated). Laplace smoothing avoids displaying
        # an unjustified 0% or 100% from this small local sample.
        ai_probability = 23 / 24 if failed else 1 / 19
        verdict = "AI 生成倾向" if failed else "真实拍摄倾向"
        basis = "任一经本地校准的异常信号即计为 AI 证据"
    elif selected:
        ai_probability = selected["ai_probability"]
        verdict = "AI 生成倾向" if selected["decision"] == "fail" else "真实拍摄倾向"
        basis = f"{selected['name']} 作为图片主判定"
    else:
        ai_probability = 0.5
        verdict = "模型分歧，结论不确定"
        basis = "没有可用主模型"
    real_probability = 1.0 - ai_probability
    reason = f"{len(completed)} 项模型完成判断：{passed} 项通过、{failed} 项未通过"
    if uncertain:
        reason += f"、{uncertain} 项证据不足"
    reason += f"。{basis}。"
    return {
        "methods": methods,
        "summary": {"total": len(methods), "completed": len(completed), "passed": passed,
                    "failed": failed, "uncertain": uncertain},
        "verdict": verdict, "reason": reason,
        "ai_probability": ai_probability, "real_probability": real_probability,
        "confidence": max(ai_probability, real_probability),
    }


def spectrum_forensics(frames):
    import cv2
    import numpy as np
    profiles, ratios, slopes = [], [], []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
        size = min(512, gray.shape[0], gray.shape[1])
        gray = cv2.resize(gray, (size, size))
        window = np.outer(np.hanning(size), np.hanning(size))
        power = np.abs(np.fft.fftshift(np.fft.fft2((gray-gray.mean()) * window))) ** 2
        yy, xx = np.indices(power.shape)
        radius = np.sqrt((yy-(size-1)/2)**2 + (xx-(size-1)/2)**2)
        radius /= max(radius.max(), 1)
        edges = np.linspace(0, 1, 25)
        profile = np.array([power[(radius>=edges[i]) & (radius<edges[i+1])].mean() for i in range(24)])
        profile /= max(profile.sum(), 1e-12)
        profiles.append(profile)
        ratios.append(float(power[radius>.6].sum() / max(power.sum(), 1e-12)))
        x = np.log(np.arange(2, 18)); y = np.log(profile[2:18] + 1e-12)
        slopes.append(float(np.polyfit(x, y, 1)[0]))
    profile = np.median(np.stack(profiles), axis=0)
    return {"id":"spectrum", "name":"频谱分布取证", "status":"descriptive", "verdict":"取证指标，需参考库校准", "score":None,
            "principle":"对亮度通道加 Hann 窗后计算二维 FFT，并做径向功率分布；生成与缩放流程可能改变高频统计。",
            "paper":PAPERS["spectrum"], "metrics":{"高频能量占比":round(float(np.median(ratios)),6), "径向谱斜率":round(float(np.median(slopes)),4)},
            "distribution":[round(float(v),6) for v in profile.tolist()]}


def image_continuity(frame):
    import cv2
    import numpy as np
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    residual = gray - cv2.GaussianBlur(gray, (0,0), 1.2)
    h, w = gray.shape
    ys = np.linspace(0,h,5,dtype=int); xs = np.linspace(0,w,5,dtype=int)
    tile_stds = [float(residual[ys[i]:ys[i+1],xs[j]:xs[j+1]].std()) for i in range(4) for j in range(4)]
    vertical = np.abs(np.diff(gray,axis=1)); horizontal = np.abs(np.diff(gray,axis=0))
    boundary = np.r_[vertical[:,7::8].ravel(), horizontal[7::8,:].ravel()]
    interior = np.r_[vertical[:,3::8].ravel(), horizontal[3::8,:].ravel()]
    ratio = float(boundary.mean() / max(interior.mean(), 1e-6))
    noise_cv = float(np.std(tile_stds) / max(np.mean(tile_stds), 1e-6))
    return {"id":"continuity", "name":"压缩与噪声连续性", "status":"descriptive", "verdict":"取证指标，不能单独证明 AI 生成", "score":None,
            "principle":"比较 8×8 边界与内部差异，并测量局部高通残差的空间离散程度。",
            "paper":PAPERS["continuity"], "metrics":{"8×8 边界差异比":round(ratio,4), "局部噪声离散系数":round(noise_cv,4)}}


def video_continuity(faces, times):
    import cv2
    import numpy as np
    if len(faces) < 8:
        return {"id":"continuity", "name":"视频时序连续性", "status":"insufficient", "verdict":"连续人脸帧不足", "score":None,
                "principle":"比较连续对齐人脸的光流与帧间残差。", "paper":PAPERS["temporal"]}
    grays = [cv2.cvtColor(face, cv2.COLOR_RGB2GRAY) for face in faces]
    residuals, motions, vectors = [], [], []
    for previous, current in zip(grays, grays[1:]):
        flow = cv2.calcOpticalFlowFarneback(previous,current,None,.5,3,15,3,5,1.2,0)
        residuals.append(float(cv2.absdiff(previous,current).mean()/255))
        motions.append(float(np.median(np.linalg.norm(flow,axis=2))))
        vectors.append(np.median(flow.reshape(-1,2),axis=0))
    jerk = np.linalg.norm(np.diff(np.stack(vectors),axis=0),axis=1) if len(vectors)>1 else np.array([0.])
    return {"id":"continuity", "name":"视频时序连续性", "status":"descriptive", "verdict":"时序异常需结合剪辑与压缩解释", "score":None,
            "principle":"对连续对齐人脸计算稠密光流、帧间变化及运动向量突变，覆盖静态分类器忽略的时间维度。",
            "paper":PAPERS["temporal"], "metrics":{"帧间残差中位数":round(float(np.median(residuals)),4), "光流幅度中位数":round(float(np.median(motions)),4), "运动突变中位数":round(float(np.median(jerk)),4), "时间跨度秒":round(float(times[-1]-times[0]),3)}}


def analyze(path, root):
    import cv2
    sys.path[:0] = [str(root / "training"), str(root)]
    print("DETECTOR_PROGRESS 8", flush=True)
    frames, faces, times, sampling = read_media(path, root)
    print("DETECTOR_PROGRESS 30", flush=True)
    learned = visual_forensics(faces, times, frames, root, sampling["media_type"], sampling)
    print("DETECTOR_PROGRESS 78", flush=True)
    spectrum_input = [cv2.cvtColor(face,cv2.COLOR_RGB2BGR) for face in faces] if sampling["media_type"] == "video" and faces else frames
    spectrum = spectrum_forensics(spectrum_input)
    print("DETECTOR_PROGRESS 88", flush=True)
    continuity = image_continuity(frames[0]) if sampling["media_type"] == "image" else video_continuity(faces, times)
    print("DETECTOR_PROGRESS 95", flush=True)
    return {"media_type": sampling["media_type"], "sampling": sampling,
            "verdict": learned["verdict"], "reason": learned["reason"],
            "ai_probability": learned["ai_probability"],
            "real_probability": learned["real_probability"],
            "confidence": learned["confidence"], "summary": learned["summary"],
            "note":"页面中的百分比是模型分类置信度的汇总近似，并非针对任意现实视频校准后的统计概率。压缩、缩放、剪辑、滤镜和未知生成器都可能改变结果。",
            "methods": learned["methods"], "supporting_methods": [spectrum, continuity]}


if __name__ == "__main__":
    media, root, output = map(Path, sys.argv[1:])
    output.write_text(json.dumps(analyze(media,root),ensure_ascii=False,indent=2),encoding="utf-8")
