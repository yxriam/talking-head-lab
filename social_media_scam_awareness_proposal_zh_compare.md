# 中英对照直译版

## Title

**EN:** An End-to-End Demonstration System for AI-Generated Talking-Head Content in Social-Media Scam Awareness and Prevention

**ZH:** 一个用于社交媒体诈骗意识提升与防范的 AI 生成说话头像内容端到端演示系统

## Abstract

**EN:** The rise of AI tools has made identity shifting increasingly easy, allowing attackers to impersonate real people through synthesised faces and voices, thus raising new risks of social-media scams.

**ZH:** AI 工具的兴起使身份转换变得越来越容易，攻击者可以通过合成的人脸和声音冒充真实人物，因此带来了新的社交媒体诈骗风险。

**EN:** This project develops a system that shows how such deceptive content can be produced, thus raising public awareness and supporting prevention strategies.

**ZH:** 本项目开发一个系统，用于展示这类欺骗性内容如何被生成，从而提升公众意识并支持防范策略。

**EN:** This system will combine a voice conversion model with an audio-driven talking-head model to generate synthesised video content from a static facial image and a target voice sample.

**ZH:** 该系统将把语音转换模型与音频驱动的说话头像模型结合起来，从一张静态人脸图像和一个目标声音样本生成合成视频内容。

**EN:** The final system is designed to automatically collect facial and voice information from publicly available social-media content and use this material to generate a talking-head video that simulates a realistic scam scenario.

**ZH:** 最终系统被设计为从公开可用的社交媒体内容中自动收集人脸和声音信息，并使用这些材料生成一个说话头像视频，用于模拟真实的诈骗场景。

**EN:** The demonstration aims to improve awareness of AI-driven identity shifting and support discussion of possible countermeasures such as user education and content verification.

**ZH:** 该演示旨在提升人们对 AI 驱动身份转换的认识，并支持对可能防范措施的讨论，例如用户教育和内容验证。

## Keywords

**EN:** talking-head generation, voice cloning, social-media scams, synthetic media, scam awareness, responsible AI

**ZH:** 说话头像生成、声音克隆、社交媒体诈骗、合成媒体、诈骗意识、负责任 AI

## 1. Background

**EN:** AI-generated identity shifting is becoming easier for non-expert users.

**ZH:** 对非专业用户来说，AI 生成的身份转换正在变得更容易。

**EN:** A convincing scam message no longer needs only text: an attacker may combine a public profile image, a short voice sample, and a generated script to create a video that appears to come from a trusted person.

**ZH:** 一个有说服力的诈骗信息不再只需要文字：攻击者可以结合一张公开头像图片、一段短声音样本和一段生成脚本，创建一个看起来像来自可信人物的视频。

**EN:** This raises risks for social-media users, especially when people rely on familiar faces and voices as trust signals.

**ZH:** 这给社交媒体用户带来了风险，尤其是当人们把熟悉的脸和声音当作信任信号时。

**EN:** This project addresses that risk through a controlled demonstration system.

**ZH:** 本项目通过一个受控演示系统来应对这种风险。

**EN:** The purpose is not to create a tool for deception, but to show how the attack pipeline can work, evaluate where the technology succeeds or fails, and use the evidence to support awareness and prevention.

**ZH:** 本项目的目的不是创建一个用于欺骗的工具，而是展示攻击流程如何运作，评估技术在哪些地方成功或失败，并用这些证据支持意识提升和防范。

**EN:** The project therefore has two connected goals: building an end-to-end technical prototype and analysing the conditions under which the output becomes convincing, fragile, or clearly synthetic.

**ZH:** 因此，本项目有两个相互关联的目标：构建一个端到端技术原型，并分析输出在什么条件下会变得可信、脆弱或明显是合成的。

**EN:** Existing talking-head systems provide useful components but do not, by themselves, answer the project question.

**ZH:** 现有的说话头像系统提供了有用组件，但它们本身并不能回答本项目的问题。

**EN:** Wav2Lip focuses on lip synchronization; MuseTalk uses latent-space inpainting for high-quality mouth motion; SadTalker produces broader head and expression motion from a single image; Chatterbox provides text-to-speech and voice-cloning capability.

**ZH:** Wav2Lip 关注唇形同步；MuseTalk 使用潜空间修复来生成高质量嘴部运动；SadTalker 从单张图像生成更广泛的头部和表情运动；Chatterbox 提供文本转语音和声音克隆能力。

**EN:** The research contribution is the integration and evaluation of these tools in a social-media scam-awareness workflow, including data provenance, consent limits, comparison experiments, and failure analysis.

**ZH:** 本研究的贡献是在一个社交媒体诈骗意识提升工作流中整合并评估这些工具，包括数据来源、同意限制、对比实验和失败分析。

## 2. Original Contribution and Use of AI Tools

**EN:** Ray's main concern is addressed explicitly here: the project must distinguish the student's own work from AI systems and existing tools.

**ZH:** Ray 的主要关注点在这里被明确回应：项目必须区分学生自己的工作与 AI 系统和现有工具的工作。

**EN:** Own project design: Scam-awareness framing, end-to-end workflow, WebUI structure, data-provenance plan, comparison design, source-condition stress analysis, failure-case analysis, and prevention discussion.

**ZH:** 自己的项目设计：诈骗意识提升框架、端到端工作流、WebUI 结构、数据来源计划、对比实验设计、源条件压力分析、失败案例分析和防范讨论。

**EN:** Own implementation work: Connecting media upload, audio extraction, voice generation, image preprocessing, talking-head generation, parameter logging, and user-facing controls into a working prototype.

**ZH:** 自己的实现工作：把媒体上传、音频提取、语音生成、图像预处理、说话头像生成、参数日志记录和面向用户的控制连接成一个可工作的原型。

**EN:** AI / open-source models: Chatterbox for voice generation, SadTalker and MuseTalk for talking-head generation, ffmpeg for media processing, and metric models such as ArcFace, ECAPA-TDNN, and SyncNet-style tools for evaluation.

**ZH:** AI / 开源模型：Chatterbox 用于语音生成，SadTalker 和 MuseTalk 用于说话头像生成，ffmpeg 用于媒体处理，ArcFace、ECAPA-TDNN 和 SyncNet 风格工具等指标模型用于评估。

**EN:** AI coding/writing assistance: Codex/ChatGPT may assist with scripting, debugging, formatting, and drafting. The final design choices, evaluation plan, interpretation, and submission responsibility remain the student's.

**ZH:** AI 编程/写作辅助：Codex/ChatGPT 可能辅助脚本编写、调试、格式化和草稿撰写。最终的设计选择、评估计划、解释和提交责任仍属于学生。

## 3. Proposed Methodology

**EN:** The proposed system is an end-to-end demonstration and evaluation pipeline.

**ZH:** 所提出的系统是一个端到端的演示和评估流程。

**EN:** Figure 1 shows the system-level methodology.

**ZH:** 图 1 展示了系统级方法。

**EN:** Inputs are limited to authorised, user-provided, exported, or API-permitted public material.

**ZH:** 输入仅限于已授权、由用户提供、由用户导出或 API 允许的公开材料。

**EN:** The system records provenance before extracting face and voice material, then generates a labelled scam-awareness demonstration for evaluation rather than undisclosed impersonation.

**ZH:** 系统会在提取人脸和声音材料之前记录来源信息，然后生成带标签的诈骗意识演示内容用于评估，而不是用于未披露的冒充。

### 3.1 Social-media media collection

**EN:** The planned Facebook component will collect candidate face and voice material only through permitted routes: user-provided downloads, Facebook data export, or official/API-permitted public-page media where allowed.

**ZH:** 计划中的 Facebook 组件只会通过被允许的路径收集候选人脸和声音材料：用户提供的下载内容、Facebook 数据导出，或在允许情况下通过官方/API 许可的公开页面媒体。

**EN:** The system will not bypass login, scrape private profiles, or collect non-consented personal media.

**ZH:** 系统不会绕过登录、抓取私人主页，或收集未经同意的个人媒体。

**EN:** Each collected item will store provenance, media type, consent status, source link or export path, and whether it is suitable for face or voice extraction.

**ZH:** 每个被收集的项目都会保存来源、媒体类型、同意状态、来源链接或导出路径，以及它是否适合用于人脸或声音提取。

**EN:** This makes the system suitable for a prevention-focused demonstration rather than covert scraping.

**ZH:** 这使系统适合用于以防范为重点的演示，而不是隐蔽抓取。

### 3.2 Preprocessing and quality screening

**EN:** The system will extract voice from uploaded audio/video using ffmpeg and prepare images using full-image, centre-crop, and automatic face-crop modes.

**ZH:** 系统将使用 ffmpeg 从上传的音频/视频中提取声音，并使用完整图像、中心裁剪和自动人脸裁剪模式准备图像。

**EN:** It will also record source conditions that may affect reliability: face scale, eye distance, sharpness, pose proxy, mouth opening, and visible occlusion.

**ZH:** 它还会记录可能影响可靠性的源条件：人脸尺度、眼距、清晰度、姿态代理指标、嘴巴张开程度和可见遮挡。

**EN:** These measurements are adapted from the source-condition stress idea used in the attached talking-head benchmark: average output quality can hide failures that occur only for difficult source images.

**ZH:** 这些测量改编自附件说话头像基准中的源条件压力分析思想：平均输出质量可能掩盖只在困难源图像上出现的失败。

### 3.3 Generation pipeline

**EN:** The speech module will generate target speech from text and a voice reference.

**ZH:** 语音模块将根据文本和声音参考生成目标语音。

**EN:** The current prototype uses Chatterbox for zero-shot voice generation.

**ZH:** 当前原型使用 Chatterbox 进行零样本语音生成。

**EN:** The video module will compare SadTalker and MuseTalk.

**ZH:** 视频模块将比较 SadTalker 和 MuseTalk。

**EN:** SadTalker is expected to provide richer face and head movement, while MuseTalk is expected to provide stronger lip precision.

**ZH:** 预期 SadTalker 会提供更丰富的脸部和头部运动，而 MuseTalk 会提供更强的唇形精度。

**EN:** The output is a labelled demonstration video for awareness and evaluation, not an undisclosed impersonation tool.

**ZH:** 输出是用于意识提升和评估的带标签演示视频，而不是未披露的冒充工具。

### 3.4 Evaluation and analysis methodology

**EN:** The project will compare models and settings, measure output quality, identify failure cases, and translate findings into prevention strategies.

**ZH:** 本项目将比较模型和设置，测量输出质量，识别失败案例，并把发现转化为防范策略。

**EN:** The analysis reports both average performance and source-condition slices, so the project can explain when a generated video looks plausible but remains unreliable.

**ZH:** 分析会同时报告平均性能和按源条件切分的结果，因此项目可以解释生成视频何时看起来可信但仍然不可靠。

## 4. Comparison Experiments

**EN:** The project will include four comparison experiments.

**ZH:** 本项目将包括四个对比实验。

**EN:** Backend comparison. SadTalker and MuseTalk will be tested using the same source image, voice reference, and text. The expected trade-off is full-face naturalness versus lip precision.

**ZH:** 后端对比。SadTalker 和 MuseTalk 将使用相同的源图像、声音参考和文本进行测试。预期的权衡是整脸自然度与唇形精度之间的差异。

**EN:** Image preprocessing comparison. Full-image, centre-crop, and automatic face-crop modes will be tested. This evaluates whether cropping improves focus or causes identity drift and mouth artefacts.

**ZH:** 图像预处理对比。将测试完整图像、中心裁剪和自动人脸裁剪模式。该实验评估裁剪是否提升聚焦效果，或者导致身份漂移和嘴部伪影。

**EN:** Voice-reference comparison. Short and longer clean voice references will be compared. This tests whether speaker similarity, accent retention, and naturalness improve with more suitable reference audio.

**ZH:** 声音参考对比。将比较较短和较长的干净声音参考。该实验测试更合适的参考音频是否能提升说话人相似度、口音保留和自然度。

**EN:** Source-condition stress comparison. Outputs will be sliced by source conditions such as small face scale, low eye distance, low sharpness, pose variation, and mouth opening.

**ZH:** 源条件压力对比。输出将按照源条件切分，例如小人脸尺度、低眼距、低清晰度、姿态变化和嘴巴张开程度。

**EN:** This reuses the useful idea from the attached paper: a video can look plausible on average while failing under specific source conditions or on a hidden metric axis.

**ZH:** 这复用了附件论文中的有用思想：一个视频在平均情况下可能看起来可信，但在特定源条件下或某个隐藏指标维度上失败。

## 5. Evaluation Measures

**EN:** The project will not depend on one score, because talking-head realism is multi-dimensional.

**ZH:** 本项目不会依赖单一分数，因为说话头像的真实感是多维的。

**EN:** Lip synchronization: SyncNet-style score where available and 1-5 human rating.

**ZH:** 唇形同步：在可用时使用 SyncNet 风格分数，并使用 1-5 分人工评分。

**EN:** Identity preservation: ArcFace similarity between source image and generated frames.

**ZH:** 身份保持：源图像与生成帧之间的 ArcFace 相似度。

**EN:** Voice similarity: ECAPA-TDNN speaker similarity and human accent/naturalness rating.

**ZH:** 声音相似度：ECAPA-TDNN 说话人相似度，以及人工口音/自然度评分。

**EN:** Visual naturalness: Human rating of head motion, expression, mouth artefacts, and overall plausibility.

**ZH:** 视觉自然度：对头部运动、表情、嘴部伪影和整体可信度进行人工评分。

**EN:** Robustness: Performance slices by face scale, sharpness, pose, mouth opening, crop mode, and backend.

**ZH:** 鲁棒性：按照人脸尺度、清晰度、姿态、嘴巴张开程度、裁剪模式和后端模型切分性能。

**EN:** Safety/usability: Provenance completeness, consent checks, warning visibility, and user questionnaire.

**ZH:** 安全性/可用性：来源信息完整性、同意检查、警告可见性和用户问卷。

## 6. Failure Cases and Improvement Strategies

**EN:** Failure analysis is part of the project, not an afterthought.

**ZH:** 失败分析是本项目的一部分，而不是事后补充。

**EN:** Expected failures include: accurate lips with a static head; natural head movement with weak mouth precision; mouth distortion from smiling or low-quality source images; identity drift after aggressive cropping; noisy references reducing voice similarity; and long text causing unnatural rhythm.

**ZH:** 预期失败包括：嘴型准确但头部静止；头部运动自然但嘴部精度较弱；微笑或低质量源图像导致嘴部变形；激进裁剪后出现身份漂移；有噪声的参考音频降低声音相似度；长文本导致节奏不自然。

**EN:** The report will distinguish visible failures from hidden failures: a generated video may look plausible but still degrade in lip-sync or speaker similarity.

**ZH:** 报告会区分可见失败和隐藏失败：一个生成视频可能看起来可信，但在唇形同步或说话人相似度上仍然下降。

**EN:** Each failure will be linked to a mitigation such as changing the backend, adjusting crop mode, lowering expression scale, using cleaner 20-30 second reference audio, splitting long text, or warning the user when source quality is weak.

**ZH:** 每个失败都会对应一个缓解方法，例如更换后端、调整裁剪模式、降低表情尺度、使用更干净的 20-30 秒参考音频、拆分长文本，或在源质量较弱时警告用户。

## 7. Ethical Scope and Prevention Focus

**EN:** The project is framed as scam awareness and prevention.

**ZH:** 本项目被定位为诈骗意识提升和防范。

**EN:** The system will not be deployed as a public impersonation service and will not remove disclosure or warning mechanisms.

**ZH:** 系统不会作为公开冒充服务部署，也不会移除披露或警告机制。

**EN:** Facebook/social-media collection will be limited to authorised or permitted material.

**ZH:** Facebook/社交媒体收集将限制在已授权或被允许的材料范围内。

**EN:** The final demonstration should be labelled as synthetic and used to explain risk, not to deceive real users.

**ZH:** 最终演示应标注为合成内容，并用于解释风险，而不是欺骗真实用户。

**EN:** The countermeasure discussion will include user education, source verification, platform reporting, watermark/disclosure design, and warning signs of AI-generated identity-shifting content.

**ZH:** 防范措施讨论将包括用户教育、来源验证、平台举报、水印/披露设计，以及 AI 生成身份转换内容的警示信号。

## 8. Planned Deliverables

**EN:** The final submission will include: (1) a working WebUI demonstration; (2) a documented media collection and provenance workflow; (3) generated awareness examples; (4) comparison results across SadTalker/MuseTalk, crop modes, and voice-reference settings; (5) source-condition stress and failure-case analysis; and (6) a concise prevention discussion.

**ZH:** 最终提交将包括：(1) 一个可工作的 WebUI 演示；(2) 有文档记录的媒体收集和来源工作流；(3) 生成的意识提升示例；(4) SadTalker/MuseTalk、裁剪模式和声音参考设置之间的对比结果；(5) 源条件压力分析和失败案例分析；以及 (6) 简明的防范讨论。

## 9. Timeline

**EN:** Current prototype: WebUI, voice generation, image preprocessing, SadTalker/MuseTalk connection, and sample outputs.

**ZH:** 当前原型：WebUI、语音生成、图像预处理、SadTalker/MuseTalk 连接和样例输出。

**EN:** Next 3 days: Finalise proposal text, diagrams, contribution disclosure, and methodology.

**ZH:** 接下来 3 天：完成 proposal 文本、图表、贡献披露和方法部分。

**EN:** Project build: Add authorised Facebook/user-media collection and provenance logging.

**ZH:** 项目构建：加入授权的 Facebook/用户媒体收集和来源日志记录。

**EN:** Experiments: Run backend, crop, voice-reference, and source-condition comparisons.

**ZH:** 实验：运行后端、裁剪、声音参考和源条件对比。

**EN:** Final report: Present results, failure analysis, prevention strategies, and ethical reflection.

**ZH:** 最终报告：展示结果、失败分析、防范策略和伦理反思。

## 10. Conclusion

**EN:** This project is suitable as an AI project because it combines implementation, model integration, controlled comparison, evaluation, and responsible-AI analysis.

**ZH:** 该项目适合作为 AI 项目，因为它结合了实现、模型集成、受控对比、评估和负责任 AI 分析。

**EN:** Its main value is not simply producing a realistic talking-head video, but using that capability to demonstrate social-media scam risk, expose technical failure conditions, and support prevention strategies.

**ZH:** 它的主要价值并不只是生成一个真实感强的说话头像视频，而是利用这种能力展示社交媒体诈骗风险，揭示技术失败条件，并支持防范策略。

## References

**EN:** The references section is kept in the English IEEE format in the submission draft.

**ZH:** 参考文献部分在提交草稿中保留英文 IEEE 格式。
