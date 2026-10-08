# Consent-Aware Personalized Talking-Head Video Generation with Voice Cloning

**One-academic-year AI project proposal draft**  
**Student:** Xinran Yang

## 1. Introduction and Problem Statement

Recent text-to-speech, voice-cloning, and audio-driven face-animation systems can create a talking-head video from a single face image, a short voice reference, and a text prompt. This is useful for accessibility, education, language learning, and personalised presentation. The same capability also creates risks: impersonation, misleading endorsement, fraud, and non-consensual synthetic media. Therefore, this project treats talking-head generation as both a technical and responsible-AI problem.

The project will extend an existing prototype WebUI that already connects Chatterbox voice cloning with SadTalker and MuseTalk video generation. The research aim is to make the pipeline reproducible, evaluate when it succeeds or fails, compare backend choices, and design visible safeguards for authorised use. The central question is: **How can a personalised talking-head generation pipeline be designed and evaluated so that it is useful for authorised users while making quality limitations and synthetic-media risks visible?**

## 2. Background and Related Work

Lip-synchronisation methods such as Wav2Lip focus on matching mouth motion to speech in unconstrained video [1]. MuseTalk improves real-time lip synchronisation through latent-space inpainting [2]. These methods can provide accurate lips, but may look unnatural when the rest of the face and head remain static. Full-face animation systems such as SadTalker predict 3D motion coefficients for expression and head pose from audio, then render motion from a single image [3]. This can produce more complete face movement, but may create artefacts with low-resolution images, strong smiles, occlusions, or unusual pose.

Voice cloning introduces another variable. Chatterbox can generate speech from short reference audio, but quality depends on reference duration, noise, accent, and prompt length [4]. Speaker-verification methods such as ECAPA-TDNN can estimate whether generated speech remains close to the reference speaker [5]. Face-embedding models such as ArcFace can estimate identity preservation across generated frames [6]. Prior work is strong at generating demos; the gap addressed here is systematic comparison, failure analysis, and interface-level safeguards.

## 3. Critical Functionalities and Research Questions

**Critical functionalities.** CF1: WebUI accepting a face image, audio/video voice reference, and text. CF2: automatic ffmpeg extraction of a clean voice segment from uploaded media. CF3: image preprocessing with full image, centre crop, and automatic face crop modes. CF4: zero-shot speech synthesis with configurable reference duration and generation settings. CF5: video generation using SadTalker and MuseTalk as comparable backends. CF6: visible synthetic-media warning layer that can later be replaced by a stronger icon/warning design. CF7: experiment logging for settings, runtime, and output paths.

**Research questions.** RQ1: How do backend choice and image preprocessing affect perceived realism, lip synchronisation, and identity preservation? RQ2: How do voice-reference quality, duration, and accent affect generated speech similarity and naturalness? RQ3: What warning and consent-interface choices reduce misuse risk while preserving usability for authorised educational or creative scenarios?

## 4. Proposed Method

The pipeline has four stages. First, the user uploads a face image and a voice source. If the source is video, ffmpeg extracts mono 24 kHz reference audio; optional filtering and loudness normalisation reduce noise. Second, Chatterbox synthesises the requested text using the extracted voice reference. Third, the face image is prepared using the selected crop mode. Fourth, SadTalker or MuseTalk generates the output video. SadTalker is the full-face/head-motion branch; MuseTalk is the lip-synchronisation baseline. The WebUI exposes controlled parameters such as reference start time, reference duration, crop mode, preprocess mode, pose style, expression scale, TTS temperature, and exaggeration. These controls allow repeatable experiments rather than manual one-off tuning.

## 5. Evaluation Plan

Experiments will use a small authorised dataset of 8-12 identities or public/consented samples. Each identity will include one or more face images, reference audio/video, and fixed English text prompts. The project will compare SadTalker and MuseTalk, full-image versus crop modes, and short versus longer voice references.

| Aspect | Measurement |
|---|---|
| Lip synchronisation | SyncNet-style score where available; 1-5 human rating |
| Identity preservation | ArcFace similarity between source image and generated frames |
| Speaker similarity | ECAPA-TDNN similarity between reference and generated speech |
| Naturalness | Human ratings of accent, speech quality, face motion, and artefacts |
| Usability/safety | Short questionnaire on consent flow and warning visibility |

## 6. Comparison Experiments, Failure Analysis, and Improvement Strategy

**Comparison experiments.** The project will run paired outputs for the same identity, voice reference, and text. The first comparison will test SadTalker versus MuseTalk: SadTalker is expected to produce more visible head and facial movement, while MuseTalk is expected to be stronger for lip accuracy. The second comparison will test image-preprocessing options: full-image preservation, centre crop, and automatic face crop. The third comparison will test short voice prompts against longer clean voice prompts.

**Failure cases.** The report will include examples where the system fails, not only successful videos. Likely failures include: accurate lips but static head movement, natural head motion but weak mouth precision, distorted mouth shapes from smiling source images, identity drift after aggressive cropping, noisy voice references causing poor accent retention, and long text prompts causing unnatural speech rhythm.

**Improvement strategy.** Each failure will be linked to a practical mitigation: choose a different backend, change crop mode, lower expression scale, use a cleaner 20-30 second reference clip, warn the user when face detection is unreliable, or split long text into shorter sentences. This turns the project from a demo into an evaluated system with evidence-based recommendations.

## 7. Expected Results, Scope, and Timeline

The expected result is a working WebUI plus a research report showing which model/configuration is best for different scenarios. The project will not train a new foundation model, generate non-consensual synthetic videos, remove warning mechanisms, or deploy a public production service. Success will be measured by a runnable system, reproducible logs, quantitative metrics, human evaluation, and clear responsible-use recommendations.

| Weeks | Milestone |
|---|---|
| 1-4 | Literature review, ethics/consent plan, dataset design, baseline documentation |
| 5-8 | Improve WebUI, logging, crop modes, and configurable model settings |
| 9-12 | Run SadTalker/MuseTalk comparisons and collect preliminary metrics |
| 13-18 | Human evaluation of realism, lip sync, identity, voice similarity, and accent |
| 19-22 | Failure-case analysis; improve settings recommendations and warning design |
| 23-26 | Final experiments, report writing, presentation, and demo packaging |

## References

[1] K. R. Prajwal et al., "A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild," arXiv:2008.10010, 2020.

[2] Y. Zhang et al., "MuseTalk: Real-Time High Quality Lip Synchronization with Latent Space Inpainting," arXiv:2410.10122, 2024.

[3] W. Zhang et al., "SadTalker: Learning Realistic 3D Motion Coefficients for Stylized Audio-Driven Single Image Talking Face Animation," arXiv:2211.12194, 2022.

[4] Resemble AI, "Chatterbox TTS," GitHub repository, 2026. Available: https://github.com/resemble-ai/chatterbox.

[5] B. Desplanques et al., "ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification," arXiv:2005.07143, 2020.

[6] J. Deng et al., "ArcFace: Additive Angular Margin Loss for Deep Face Recognition," arXiv:1801.07698, 2018.

[7] National Institute of Standards and Technology, "AI Risk Management Framework," 2023.
