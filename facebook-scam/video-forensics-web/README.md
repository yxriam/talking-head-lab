# FrameTrace 视频生成痕迹实验室

一个本地优先的视频异常初筛网页。视频在浏览器内解码和计算，不上传到服务器。

## 当前实现

| 方法 | 当前计算 | 状态 |
|---|---|---|
| D3结构代理 | 透明帧描述向量、相邻余弦距离、距离二阶变化 | 可运行，未加载DINOv2 |
| ReStraV结构代理 | 帧向量步长、连续方向夹角、步长变异 | 可运行，未加载论文分类器 |
| 运动一致性 | 8×8图像块、邻域SAD匹配、运动向量离散度 | 可运行，传统算法 |
| 频域痕迹 | 8×8 DCT、低中高频能量、块边界强度 | 可运行，传统算法 |

所有分数都是视频内部的相对异常指数，不是AI生成概率。没有真实/AI参考库时，不能据此确认视频来源。

## 启动

需要 Node.js 22.13 或更高版本。

```powershell
npm install
npm run dev
```

浏览器打开终端显示的本地地址，选择MP4、MOV或WebM视频，然后点击“开始四项检查”。

## 处理过程

1. 均匀抽取12至36帧，缩放至64×48分析尺寸。
2. 为每帧计算颜色直方图、亮度网格和边缘统计组成的透明描述向量。
3. 同一组描述向量同时供D3结构代理与轨迹方法使用。
4. 相邻灰度帧用于块匹配运动估计。
5. 每帧执行8×8 DCT并统计频段能量。
6. 四项方法分别返回曲线、最高异常时间点、关键指标与局限说明。

抽样帧与指标只保存在当前浏览器标签页内。导出的JSON报告不包含视频或帧图像。

## 后续升级边界

- 使用DINOv2-small替换透明帧描述向量，需要另行下载约百MB级权重。
- 接入ReStraV分类器前，需要核对官方权重、许可证和编码器版本。
- MMD需要真实与AI参考视频库；代码不是主要困难，参考数据与校准才是。
- 如需公网多人使用，应将视频处理拆分为独立推理服务并补充上传、删除和隐私策略。

## 验证

```powershell
npm run build
npm test
```

## 方法来源

- [D3：Training-Free AI-Generated Video Detection Using Second-Order Features](https://openaccess.thecvf.com/content/ICCV2025/html/Zheng_D3_Training-Free_AI-Generated_Video_Detection_Using_Second-Order_Features_ICCV_2025_paper.html)
- [ReStraV：NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/1d9a43752c2819e03967c5c1b708169c-Abstract-Conference.html)
- [AIGVDet：RGB与光流双分支](https://arxiv.org/abs/2403.16638)
- [F3-Net：频率感知人脸伪造检测](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123570086.pdf)
