# 展示素材来源 / Showcase provenance

日期 / Date: 2026-10-09, Pacific/Auckland。

这些资源专门为中英文README制作，输入人像和参考声音均为合成素材。没有公开既有人物照片、真人声音、登录态、私人采集历史或密钥。

These assets were created for the bilingual README. The input person and reference voice are synthetic. Existing personal portraits, real-person voices, browser sessions, private collection history, and secrets were not published.

## 输入与实际输出 / Inputs and actual outputs

| 文件 / File | 来源 / Provenance |
|---|---|
| [synthetic-input.png](synthetic-input.png) | 内置imagegen创建的虚构成年人物，仅作项目输入 / Fictional adult generated with the built-in imagegen tool as an input |
| [reference-voice.wav](reference-voice.wav) | 已安装Microsoft Zira Desktop系统合成声音 / Existing Microsoft Zira Desktop system speech synthesis |
| [generated-voice.wav](generated-voice.wav) | 项目Chatterbox实际输出，4.68秒；任务报告38.1秒 / Actual Chatterbox output, 4.68 s; job reports 38.1 s |
| [prepared-portrait.png](prepared-portrait.png) | 同一视频任务实际产生的背景准备后肖像 / Actual prepared portrait from the same video job |
| [sadtalker-demo.mp4](sadtalker-demo.mp4) | 项目SadTalker原始最终输出，512×512，4.736秒，含AAC音轨；渲染报告64.1秒，不含肖像准备 / Actual final SadTalker output with audio; reported rendering time excludes portrait preparation |
| [sadtalker-demo.gif](sadtalker-demo.gif) | 由同一MP4导出，360px宽、10fps、循环、无音轨；增加AI生成/合成人物标识 / Derived from that MP4, resized, 10 fps, silent loop, with a synthetic/AI-generation label |
| [detection-report.json](detection-report.json) | 同一原始视频的真实本地检测报告，21.5秒，未调用TruthScan / Actual local report on that video; no TruthScan call |

参考文本 / Reference text:

> This is a synthetic voice created for a public software demonstration. No real person's voice is used.

项目生成台词 / Generated speech text:

> Welcome to Talking Head Lab. This is an AI generated demonstration.

真实任务各执行一次，采用当前服务与默认参数；没有挑选多次生成中的最好结果。GIF压缩与加标识是展示处理，不是新的模型生成。语音、肖像和视频输入/输出没有互相冒充。

Each actual job ran once using the existing service and defaults. No best-of-many output selection was used. GIF conversion and labeling are presentation processing, not new model inference.

## 界面截图 / Interface screenshots

- `voice-zh.jpg` / `voice-en.jpg`：本轮Chatterbox完成后的真实工作台 / Actual completed voice job.
- `video-zh.jpg` / `video-en.jpg`：本轮SadTalker完成后的真实工作台 / Actual completed video job.
- `detect-zh.jpg` / `detect-en.jpg`：同一视频本地检测结果，1通过、4未通过、1证据不足 / Actual local result: 1 pass, 4 fail, 1 insufficient.
- `crawl-zh.jpg` / `crawl-en.jpg`：真实界面中已有的“本地集成测试（非Facebook实采）”记录；截图在私人历史区域前截止 / Existing explicitly synthetic integration-test record; private history is outside the capture.
- `account-zh.jpg` / `account-en.jpg`：上述已有合成记录的文字排版，未在本轮重新执行或验收其Qwen账号生成 / Text layout from that existing synthetic record; its account-generation provenance was not re-executed or accepted in this task.

截图使用computer-use的浏览器能力，直接读取真实页面；没有绘制虚假界面、篡改分数或清除真实历史。采集截图使用局部区域避免公开历史账号，账号分析截图仅截取合成记录区域。未访问真实Facebook目标，也未向云端提交人物或视频。

Screenshots use the browser computer-use capability against the real workbench. Scores and the UI were not fabricated. Cropped regions keep private history outside the images. No live Facebook target or cloud video submission was used.

## 人像提示词 / Portrait prompt

Built-in tool mode, new generation, `transparent_background=false`; the returned image was copied into this repository. No external API key, CLI fallback, reference photograph, or known person was used.

```text
Use case: photorealistic-natural. Asset type: synthetic input portrait for a public open-source talking-head software demonstration, not a UI mockup. Create one completely fictional adult woman aged approximately 30, with short dark wavy hair, brown eyes, wearing a simple plain teal crew-neck shirt. Centered front-facing head-and-shoulders composition, looking straight at the camera, closed mouth, calm friendly neutral expression, both shoulders visible, leave margin above the head. Soft even studio light, realistic skin texture, plain light-gray background, square framing. No real-person reference, no celebrity likeness, no logos, no text, no watermark, no accessories hiding the face. The portrait is intended as an input to separate real lip-sync model inference.
```

## 证据与适用范围 / Evidence and scope

真实任务状态、耗时、构建失败与修复、资源SHA256和发布记录见 [本轮变更记录](../change-records/2026-10-09-readme-showcase/记录.md)。检测95.8%是本例界面汇总值，不是互联网视频准确率。新机器安装没有在本轮重新执行，模型展示也不代表所有模型的回归验收或新服务部署。

The [change record](../change-records/2026-10-09-readme-showcase/记录.md) preserves job status, timings, build fixes, asset hashes, and publication. The displayed 95.8% is a sample result, not a general accuracy claim. This showcase is not a fresh-machine installation test, an acceptance matrix for every model, or a new deployment.
