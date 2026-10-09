# Consent-Aware Personalized Talking-Head Video Generation with Voice Cloning and Visual Warning Design

**Student:** [Your Name]  
**Project type:** One-academic-year AI project proposal  

## 1. Introduction and Problem Statement

Recent progress in text-to-speech, voice cloning, and audio-driven facial animation makes it possible to generate personalized talking-head videos from only a face image, a short voice reference, and a text prompt. These systems are useful for accessibility, education, language learning, remote presentation, and personalized communication. However, the same technologies also create risks of impersonation, misleading endorsement, fraud, and non-consensual synthetic media. The technical challenge is therefore not only to generate realistic video, but to understand when the output is reliable, where it fails, and how an interface can enforce responsible use.

This project proposes a consent-aware talking-head generation system that accepts three inputs: a face image, a voice reference audio/video, and text. The system automatically extracts a speaker reference from the audio/video, synthesizes speech with a zero-shot TTS model, preprocesses/crops the face image, and renders a talking-head video. A WebUI prototype has already been implemented using Chatterbox for voice generation and SadTalker/MuseTalk as alternative talking-head backends. The project will extend this prototype into a research system by evaluating quality, failure modes, and safety controls rather than only demonstrating generation.

The main goal is to answer: **How can a personalized talking-head generation pipeline be designed and evaluated so that it produces useful videos for authorised users while making quality limitations and synthetic-media risks visible?**

## 2. Background and Related Work

Audio-driven talking-head generation has developed along two related directions. Lip-synchronisation methods such as Wav2Lip focus on accurately matching mouth movement to speech in unconstrained videos [1]. More recent systems such as MuseTalk perform high-quality lip synchronisation through latent-space inpainting and are suitable when lip accuracy is the main objective [2]. However, lip-focused approaches can appear unnatural in presentation-style scenarios if the face and head remain static.

Full-face animation approaches address a broader motion problem. SadTalker predicts 3D motion coefficients for expression and head pose, then renders a talking face from a single image [3]. This can produce more complete facial motion, but it may introduce artefacts when the source image has a strong smile, low resolution, occlusions, or unusual pose. VideoReTalking and other editing pipelines show that sequential face generation, lip synchronisation, and enhancement can improve realism, but such pipelines are more complex and still require careful evaluation [4].

Voice cloning and zero-shot TTS introduce another source of variation. Chatterbox provides open-source TTS and voice-cloning functionality using a short reference clip [5], but the quality depends strongly on prompt duration, noise level, language/accent, and text length. Speaker verification methods such as ECAPA-TDNN can be used to quantify speaker similarity between the reference and generated audio [6]. Face embedding methods such as ArcFace or FaceNet can similarly estimate identity preservation in generated frames [7], [8].

Prior work is strong at generating convincing samples, but a practical user-facing system still has limitations: model choice affects whether lips or full-face motion looks better; input quality strongly changes output quality; and synthetic media requires consent and disclosure mechanisms. This project focuses on these gaps through comparative evaluation and interface-level safeguards.

## 3. Critical Functionalities and Research Questions

**Critical Functionalities (CFs).**

CF1. A WebUI that accepts a face image, a video/audio voice reference, and a text prompt.  
CF2. Automatic extraction of a clean voice reference from uploaded video/audio using ffmpeg.  
CF3. Image preprocessing with full-image mode, centre crop, and automatic face crop options.  
CF4. Speech synthesis using Chatterbox with configurable prompt duration and generation parameters.  
CF5. Video generation using at least two backends or configurations, currently SadTalker and MuseTalk, to compare lip accuracy and full-face naturalness.  
CF6. A visual warning layer for synthetic-media output, designed so that a future icon/warning system can replace the current placeholder.  
CF7. Logging of input settings, model settings, runtime, and output paths for reproducible experiments.

**Research Questions (RQs).**

RQ1. How do model choice and preprocessing choices affect perceived realism, lip synchronisation, and identity preservation in personalised talking-head video?  
RQ2. How does voice prompt quality, prompt length, and accent affect generated speech similarity and naturalness?  
RQ3. What interface and warning design choices can reduce misuse risk while preserving usability for authorised creative and educational scenarios?

## 4. Proposed Method

The proposed pipeline has four stages. First, the user uploads an image and a voice source. If the voice source is a video, ffmpeg extracts a mono 24 kHz reference segment. Optional high-pass/low-pass filtering and loudness normalisation reduce background noise. Second, the text and voice reference are passed to Chatterbox to generate a synthetic speech waveform. Third, the face image is prepared using either full-image preservation, centre-square cropping, or automatic face cropping. Finally, SadTalker or MuseTalk generates the talking-head video. SadTalker will be used for full-face and head-motion generation, while MuseTalk will serve as a lip-synchronisation baseline.

The system will expose controlled parameters: reference start time, reference duration, image crop mode, SadTalker preprocess mode, pose style, expression scale, and TTS temperature/exaggeration. These controls allow systematic experiments rather than only subjective manual tuning.

## 5. Evaluation Plan and Expected Results

Evaluation will include both automatic and human-centred measures. A small authorised dataset will be built from 8-12 participants or public/consented samples. For each identity, the project will use one or more images, short reference audio/video clips, and fixed English text prompts. Generated videos will be compared across model/configuration variants.

The planned measures are:

| Aspect | Measurement |
|---|---|
| Lip synchronisation | SyncNet-style score where available, plus 1-5 human rating |
| Identity preservation | ArcFace/FaceNet embedding similarity between source image and generated frames |
| Speaker similarity | ECAPA-TDNN speaker embedding similarity between reference and generated speech |
| Accent/naturalness | Human rating of accent retention and speech naturalness |
| Visual naturalness | Human rating of face movement, head movement, and artefacts |
| Usability and safety | Short user questionnaire on clarity of warning/consent workflow |

Expected limitations will be reported explicitly. For example, MuseTalk may produce accurate lips but limited full-face movement; SadTalker may create more natural head motion but weaker lip precision; smiling or low-resolution images may create mouth artefacts; noisy voice references may reduce accent preservation. The final system will include recommended settings based on these findings, such as using 20-30 seconds of clean reference audio, lowering expression scale for smiling images, and warning users when face detection fails.

## 6. Scope

In scope: a working WebUI, automated audio extraction, image preprocessing, Chatterbox speech generation, SadTalker/MuseTalk comparison, evaluation metrics, user study, failure analysis, and warning/consent design.  

Out of scope: training a new foundation model from scratch, generating videos without consent, removing synthetic-media warnings, or deploying the system as a public production service.

## 7. Timeline

**Weeks 1-4:** Literature review, ethics/consent protocol, dataset plan, baseline pipeline documentation.  
**Weeks 5-8:** Improve WebUI, logging, image preprocessing, and configurable model settings.  
**Weeks 9-12:** Run model comparison experiments on SadTalker and MuseTalk; collect preliminary automatic metrics.  
**Weeks 13-18:** Human evaluation study; analyse lip-sync, identity, voice similarity, accent, and naturalness.  
**Weeks 19-22:** Failure case analysis and improvement strategies; refine warning/icon layer.  
**Weeks 23-26:** Final experiments, report writing, presentation preparation, and demo packaging.

## References

[1] K. R. Prajwal, R. Mukhopadhyay, V. Namboodiri, and C. V. Jawahar, "A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild," arXiv:2008.10010, 2020.  
[2] Y. Zhang et al., "MuseTalk: Real-Time High Quality Lip Synchronization with Latent Space Inpainting," arXiv:2410.10122, 2024.  
[3] W. Zhang et al., "SadTalker: Learning Realistic 3D Motion Coefficients for Stylized Audio-Driven Single Image Talking Face Animation," arXiv:2211.12194, 2022.  
[4] K. Cheng et al., "VideoReTalking: Audio-based Lip Synchronization for Talking Head Video Editing In the Wild," arXiv:2211.14758, 2022.  
[5] Resemble AI, "Chatterbox TTS," GitHub repository, 2026. Available: https://github.com/resemble-ai/chatterbox.  
[6] B. Desplanques, J. Thienpondt, and K. Demuynck, "ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification," arXiv:2005.07143, 2020.  
[7] J. Deng et al., "ArcFace: Additive Angular Margin Loss for Deep Face Recognition," arXiv:1801.07698, 2018.  
[8] F. Schroff, D. Kalenichenko, and J. Philbin, "FaceNet: A Unified Embedding for Face Recognition and Clustering," arXiv:1503.03832, 2015.  
[9] National Institute of Standards and Technology, "AI Risk Management Framework," 2023. Available: https://www.nist.gov/itl/ai-risk-management-framework.
