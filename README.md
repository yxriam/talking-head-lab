# Talking Head Lab

[中文](README.md) · [English](README.en.md)

采集 Facebook 内容、生成语音与人像视频、查看媒体真伪检测线索。

## 有哪些功能

| 功能 | 你提供 | 得到什么 |
|---|---|---|
| Facebook 采集 | 主页、帖子或视频链接 | 可见文字、来源、可下载媒体与 ZIP |
| 音色克隆 | 参考声音 + 新台词 | 用参考音色朗读新台词 |
| 人像视频 | 照片 + 驱动音频 | 会说话的人像视频，原图直接进入模型 |
| 真伪检测 | 图片或视频 | 多方法评分、采样帧与判断依据 |

功能可独立使用；生成的语音可直接带入视频，视频可直接带入检测。

## 先看效果，再试样例

三组不同人物，均使用合成原图与声音，经 **SadTalker 实际生成**。点击原图下载；GIF 无声，MP4 带声。

<table>
  <tr><th></th><th>样例 1</th><th>样例 2</th><th>样例 3</th></tr>
  <tr><th>输入原图</th><td><a href="docs/showcase/synthetic-input.png"><img src="docs/showcase/gallery/portrait-01-thumb.jpg" width="180" alt="虚构女性原图" /></a></td><td><a href="docs/showcase/gallery/portrait-02.png"><img src="docs/showcase/gallery/portrait-02-thumb.jpg" width="180" alt="虚构男性原图" /></a></td><td><a href="docs/showcase/gallery/portrait-03.png"><img src="docs/showcase/gallery/portrait-03-thumb.jpg" width="180" alt="虚构年长女性原图" /></a></td></tr>
  <tr><th>实际视频</th><td><img src="docs/showcase/gallery/video-01.gif" width="180" alt="样例1实际视频" /></td><td><img src="docs/showcase/gallery/video-02.gif" width="180" alt="样例2实际视频" /></td><td><img src="docs/showcase/gallery/video-03.gif" width="180" alt="样例3实际视频" /></td></tr>
  <tr><th>带声播放</th><td><a href="docs/showcase/sadtalker-original-demo.mp4">MP4 ①</a></td><td><a href="docs/showcase/gallery/video-02.mp4">MP4 ②</a></td><td><a href="docs/showcase/gallery/video-03.mp4">MP4 ③</a></td></tr>
</table>

[下载驱动音频](docs/showcase/generated-voice.wav) · [听参考声音](docs/showcase/reference-voice.wav) · [样例说明与来源](docs/showcase/gallery/EXAMPLES.md)

**Facebook 实采：**[特朗普官方页面](docs/showcase/facebook-trump/EXAMPLE.md)，4 次滚动取得 45 条文字片段、下载 4 张图片；视频仅取得来源链接。本例只采集，未做个人风险分析。

<details>
<summary>展开查看工作台界面</summary>

![真实 Facebook 采集结果](docs/showcase/facebook-trump/images-zh.jpg)
![音色克隆](docs/showcase/voice-zh.jpg)
![人像视频](docs/showcase/video-original-zh.jpg)
![真伪检测](docs/showcase/detect-original-zh.jpg)

</details>

## 快速开始

### 先浏览界面（不需要 GPU）

需要 Node.js 22.13+。运行：

```powershell
git clone https://github.com/yxriam/talking-head-lab.git
Set-Location talking-head-lab/facebook-scam/video-forensics-web
npm ci
npm run dev -- --host 127.0.0.1 --port 3100
```

打开 **http://localhost:3100/studio**。这一步只启动界面；生成与检测需要后端模型。

### 开始生成

按[部署指南](docs/guides/SETUP.md)准备 Windows + WSL2 模型环境。已有环境从项目根目录启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\local-media\start-local.ps1
```

下载上面的任一原图与驱动音频 → 打开“AI 人像视频” → 上传两份文件 → 选择 SadTalker → 生成。体验视频不需要先采集 Facebook 或克隆声音。

<details>
<summary>其他用法、模型选择与常见问题</summary>

- 声音：参考音频/视频 + 台词 → 生成语音 → 带入人像视频。
- 检测：上传文件或复用生成视频 → 查看方法结果与采样帧；评分是模型线索。
- Facebook：先手工登录。公共页面使用[仅采集方式](docs/showcase/facebook-trump/EXAMPLE.md)；账号防范提醒目前只适用于私人账号，自动门控仍待验收。
- 视频支持 SadTalker、EchoMimic、JoyVASA 和腾讯 YT HumanActor，按部署状态显示可用性。
- [安装、启动、云端配置与限制](docs/guides/SETUP.md) · [详细启动排障](网站启动说明.md) · [素材来源](docs/showcase/PROVENANCE.md)

</details>

## 想修改项目

[项目结构与代码分布、二次开发](docs/guides/DEVELOPMENT.md) · [协作规范](AGENTS.md) · [当前项目状态](PROJECT.md)
