# 展示素材来源 / Showcase provenance

日期 / Date: 2026-10-09, Pacific/Auckland。

这些资源专门为中英文README制作，生成演示的输入人像和参考声音均为合成素材。最新 Facebook 示例使用用户指定的 DonaldTrump 公共页面实采节选与工作台截图，来源见下方；未公开真人声音、登录态、私人采集历史或密钥。

These assets were created for the bilingual README. The generation input person and reference voice are synthetic. The latest Facebook example uses selected real results and workbench screenshots from the user-specified DonaldTrump public page, documented below. Real-person voices, browser sessions, private collection history and secrets were not published.

## 输入与实际输出 / Inputs and actual outputs

| 文件 / File | 来源 / Provenance |
|---|---|
| [synthetic-input.png](synthetic-input.png) | 内置imagegen创建的虚构成年人物，仅作项目输入 / Fictional adult generated with the built-in imagegen tool as an input |
| [reference-voice.wav](reference-voice.wav) | 已安装Microsoft Zira Desktop系统合成声音 / Existing Microsoft Zira Desktop system speech synthesis |
| [generated-voice.wav](generated-voice.wav) | 项目Chatterbox实际输出，4.68秒；任务报告38.1秒 / Actual Chatterbox output, 4.68 s; job reports 38.1 s |
| [sadtalker-original-demo.mp4](sadtalker-original-demo.mp4) | 项目SadTalker原始最终输出，512×512，4.736秒，含AAC音轨；任务报告61.9秒，无额外背景前置 / Actual final SadTalker output with audio; job reports 61.9 s, with no added background stage |
| [sadtalker-original-demo.gif](sadtalker-original-demo.gif) | 由同一MP4导出，360px宽、10fps、循环、无音轨；增加AI生成/合成人物标识 / Derived from that MP4, resized, 10 fps, silent loop, with a synthetic/AI-generation label |
| [detection-original-report.json](detection-original-report.json) | 同一原始视频的真实本地检测报告，24.1秒，未调用TruthScan / Actual local report on that video; no TruthScan call |

参考文本 / Reference text:

> This is a synthetic voice created for a public software demonstration. No real person's voice is used.

项目生成台词 / Generated speech text:

> Welcome to Talking Head Lab. This is an AI generated demonstration.

真实任务各执行一次，采用当前服务与默认参数；没有挑选多次生成中的最好结果。GIF压缩与加标识是展示处理，不是新的模型生成。语音、肖像和视频输入/输出没有互相冒充。

Each actual job ran once using the existing service and defaults. No best-of-many output selection was used. GIF conversion and labeling are presentation processing, not new model inference.

## 界面截图 / Interface screenshots

- `voice-zh.jpg` / `voice-en.jpg`：本轮Chatterbox完成后的真实工作台 / Actual completed voice job.
- `video-original-zh.jpg` / `video-original-en.jpg`：本轮SadTalker完成后的真实工作台 / Actual completed video job.
- `detect-original-zh.jpg` / `detect-original-en.jpg`：同一视频本地检测结果，1通过、4未通过、1证据不足 / Actual local result: 1 pass, 4 fail, 1 insufficient.
- `crawl-zh.jpg` / `crawl-en.jpg`：真实界面中已有的“本地集成测试（非Facebook实采）”记录；截图在私人历史区域前截止 / Existing explicitly synthetic integration-test record; private history is outside the capture.
- `account-zh.jpg` / `account-en.jpg`：上述已有合成记录的文字排版，未在本轮重新执行或验收其Qwen账号生成 / Text layout from that existing synthetic record; its account-generation provenance was not re-executed or accepted in this task.

上述最初合成展示阶段截图使用computer-use的浏览器能力，直接读取真实页面；没有绘制虚假界面、篡改分数或清除真实历史。旧采集截图使用局部区域避免公开历史账号，账号分析截图仅截取合成记录区域。该阶段未访问真实Facebook目标，也未向云端提交人物或视频；最新真实采集单独记录如下。

The initial synthetic-showcase screenshots above use the browser computer-use capability against the real workbench. Scores and the UI were not fabricated. Cropped regions keep private history outside the images. That initial stage used no live Facebook target or cloud video submission; the later live collection is recorded separately below.

## 人像提示词 / Portrait prompt

Built-in tool mode, new generation, `transparent_background=false`; the returned image was copied into this repository. No external API key, CLI fallback, reference photograph, or known person was used.

```text
Use case: photorealistic-natural. Asset type: synthetic input portrait for a public open-source talking-head software demonstration, not a UI mockup. Create one completely fictional adult woman aged approximately 30, with short dark wavy hair, brown eyes, wearing a simple plain teal crew-neck shirt. Centered front-facing head-and-shoulders composition, looking straight at the camera, closed mouth, calm friendly neutral expression, both shoulders visible, leave margin above the head. Soft even studio light, realistic skin texture, plain light-gray background, square framing. No real-person reference, no celebrity likeness, no logos, no text, no watermark, no accessories hiding the face. The portrait is intended as an input to separate real lip-sync model inference.
```

## 证据与适用范围 / Evidence and scope

真实任务状态、耗时、构建失败与修复、资源SHA256和发布记录见 [本轮变更记录](../change-records/2026-10-09-readme-showcase/记录.md)。检测95.8%是本例界面汇总值，不是互联网视频准确率。新机器安装没有在本轮重新执行，模型展示也不代表所有模型的回归验收或新服务部署。

The [change record](../change-records/2026-10-09-readme-showcase/记录.md) preserves job status, timings, build fixes, asset hashes, and publication. The displayed 95.8% is a sample result, not a general accuracy claim. This showcase is not a fresh-machine installation test, an acceptance matrix for every model, or a new deployment.


## 用户纠正后的当前版本 / Current version after correction

用户明确取消背景替换。当前图库仅显示合成原图→原图直接生成的视频；模型输入路径和SHA256与原图一致，任务没有scene.json、scene-prompt.txt或generated-portrait.png。新SadTalker任务da4977bd616f46bd945a5188449571f0（61.9秒）和检测60a504e5caff45ce8fe3d1c945a1d00d（24.1秒）各实跑一次；输入、音频与模型参数不变。旧44e92f2演示与原本3ef任务留在Git历史/本机原任务记录，不冒充新流程。

The user explicitly removed background replacement. The current gallery shows the synthetic original image followed by actual output generated directly from it. Input path/hash match the original, and no background-preparation artifacts were created. Each corrected video/detection job ran once; the old version remains historical evidence.

新视频/检测双语截图使用用户明确允许的现有Playwright/Edge，在隔离localhost上下文回放上述真实已完成任务。图片、语音及任务结果是真实资源；没有为截图改变业务源码、安装工具或额外触发推理。第一次截图在解码器尚未绘制视频时出现黑画面，等待真实播放帧后重新截图；只调整截图脚本的播放/暂停时机，不改页面内容或模型结果。

The new bilingual video/detection screenshots replay those genuine completed jobs in an isolated local browser context. The user approved screenshot-only use of existing Playwright/Edge. No project-source changes, tool installation, or additional model jobs were made for capture. A decoder timing issue was resolved by waiting for a real playback frame.

视频原图约定及每次操作同步要求见 [共享协议](../../AGENTS.md) 与 [Codex/Claude共同交接](../AI-HANDOFF.md)，具体测试、运行版本差异与回退见 [背景纠正记录](../change-records/2026-10-09-original-image-video/记录.md)。文件交接已同步，Claude未实际调用，不称独立审查完成。

## 新增真实 Facebook 示例 / Later live Facebook example

用户指定 https://www.facebook.com/DonaldTrump/，使用唯一既有采集器于2026-10-09T06:41:36Z–06:41:49Z执行一次4次滚动采集：45条文字片段、11个图片条目、7个视频条目；4张图下载成功，视频/音频均0，13.0秒（collector内部12.2秒）。不是45篇帖子，也不是7个独立视频；date均缺失。官方简介与政治用途字段支持其公共政治页面用途，本例不调用分类模型或风险模型。

The user selected DonaldTrump's real public Facebook page. One existing-collector run returned 45 text fragments, 11 image entries and 7 video entries over 4 scrolls, saving 4 images and no video/audio in 13.0 s (12.2 s inside the collector). Fragments are not posts; video entries include repeated Reel variants. Dates were not extracted. The introduction/purpose field supports an official political public-page observation; no classification or risk model was invoked.

当前README使用 facebook-trump/text-zh/en.jpg 与 images-zh/en.jpg；video-links-zh/en.jpg在详情中显示真实“仅链接”。截图来自真实发布版工作台与现有采集API，读取本次真实任务的公开节选，API访问仅GET；首版离线回放已被此版替换。借用现有Playwright/Edge，用户授权仅截图，不修改业务源码/安装工具/重新采集或推理。原始图文件、评论者、登录态、CDN签名与追踪参数留本机。公开JSON仅选4条主页片段及媒体来源/状态/SHA256，不伪造缺失字段。

Current README screenshots use the real published workbench and existing collector API reading a public excerpt of this completed run; capture used GET only. These replace the first offline replay captures. Existing Playwright/Edge was used under the user's screenshot-only permission, with no business-source edits, tool installation, repeated collection or inference. Original image files, commenter data, browser sessions, signed CDN URLs and tracking parameters remain local. Public JSON includes only 4 profile excerpts and media source/status/SHA256 metadata.

[中文示例](facebook-trump/EXAMPLE.md) · [English example](facebook-trump/EXAMPLE.en.md) · [公开概览](facebook-trump/collection-summary.json) · [本轮变更记录](../change-records/2026-10-09-facebook-trump-showcase/记录.md)。特朗普图片/声音未用于生成、克隆或检测，页面方未认可或参与项目。

## 多组样例与首页分层 / Multiple examples and progressive home page

新增两张虚构原图及两次真实SadTalker输出；保留旧原图样例，共3组。首页缩略图与GIF为展示转换，完整原图/音频/带声视频可下载；没有更换背景。详情：[中文](gallery/EXAMPLES.md) · [English](gallery/EXAMPLES.en.md) · [真实任务与SHA](gallery/manifest.json)。New fictional input portraits and actual SadTalker outputs form three examples; thumbnails/GIFs are display derivatives, with original inputs and voiced videos available. No added background replacement.
