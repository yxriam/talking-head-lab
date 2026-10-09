# 三组人像与视频样例

[中文](EXAMPLES.md) · [English](EXAMPLES.en.md) · [返回首页](../../../README.md)

三个人物均为虚构合成输入；视频均由项目 SadTalker 实际生成。三组共用同一段合成驱动音频，便于比较不同照片的效果。

| 样例 | 下载原图 | 带声视频 | 实际视频时长 | 视频任务耗时 |
|---|---|---|---|---|
| 1：女性 | [PNG](../synthetic-input.png) | [MP4](../sadtalker-original-demo.mp4) | 4.736 秒 | 61.9 秒 |
| 2：男性 | [PNG](portrait-02.png) | [MP4](video-02.mp4) | 4.736 秒 | 64.3 秒 |
| 3：年长女性 | [PNG](portrait-03.png) | [MP4](video-03.mp4) | 4.736 秒 | 57.6 秒 |

[驱动音频：Chatterbox 输出，4.68 秒](../generated-voice.wav) · [参考声音：系统合成](../reference-voice.wav)

台词：Welcome to Talking Head Lab. This is an AI generated demonstration.

## 最少步骤体验

1. 尚未部署：先打开带声 MP4 或首页 GIF 看结果。
2. 模型环境已就绪：下载任一原图与驱动音频，在工作台“AI 人像视频”上传两份文件，选择 SadTalker 后生成。
3. 想换台词：到“音色克隆”上传参考声音，生成新语音，再带入视频。

无需先采集 Facebook；[部署指南](../../guides/SETUP.md)说明模型环境与启动方式。

## 来源与限制

- 输入：样例1为既有imagegen合成图；样例2/3由本轮内置imagegen各生成一次，无真人参考。图片属于输入，不能当作项目视频模型的输出。
- 输出：样例1复用已验收原图任务；样例2/3各实际运行一次。每次均将原PNG直接交给模型，未更换背景；模型原生裁剪/缩放照常执行。
- 展示：JPEG只作缩略图；GIF从同一份MP4导出，240px、8fps、带合成标识且无声。原始PNG与带声MP4不改动。
- 耗时仅对应本机这三次任务，不是模型通用性能承诺。没有为本轮重新运行检测，也没有将旧换背景结果计入三组。

[任务、输入/输出SHA256与媒体信息](manifest.json) · [全部素材来源](../PROVENANCE.md) · [本轮实跑与发布记录](../../change-records/2026-10-09-progressive-gallery/记录.md)
