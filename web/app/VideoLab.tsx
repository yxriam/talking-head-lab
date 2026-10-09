"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type SampleFrame = {
  time: number;
  descriptor: number[];
  gray: Float32Array;
  dct: DctStats;
  thumb: string;
};

type DctStats = {
  low: number;
  mid: number;
  high: number;
  blockiness: number;
};

type FlowStats = {
  magnitude: number;
  inconsistency: number;
  residual: number;
};

type SeriesPoint = { time: number; value: number };

type MethodResult = {
  id: "d3" | "trajectory" | "flow" | "dct";
  number: string;
  title: string;
  label: string;
  score: number;
  headline: string;
  explanation: string;
  limitation: string;
  formula: string;
  seriesLabel: string;
  series: SeriesPoint[];
  accent: string;
  topTime: number;
  topThumb: string;
  facts: { name: string; value: string }[];
};

type AnalysisResult = {
  duration: number;
  width: number;
  height: number;
  samples: number;
  generatedAt: string;
  methods: MethodResult[];
  flagged: number;
};

const METHOD_INTRO = [
  { number: "01", title: "向量二阶变化", tag: "D3结构代理", copy: "看相邻帧变化的速度是否忽快忽慢。" },
  { number: "02", title: "特征轨迹", tag: "ReStraV结构代理", copy: "看帧向量前进路线是否频繁急转。" },
  { number: "03", title: "运动一致性", tag: "传统块匹配光流", copy: "看局部像素运动是否互相矛盾。" },
  { number: "04", title: "频域痕迹", tag: "8×8 DCT", copy: "看高频纹理、网格和压缩波动。" },
];

const clamp = (value: number, min = 0, max = 100) => Math.min(max, Math.max(min, value));
const mean = (values: number[]) => values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
const standardDeviation = (values: number[]) => {
  const avg = mean(values);
  return Math.sqrt(mean(values.map((value) => (value - avg) ** 2)));
};
const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.max(0, seconds - mins * 60);
  return `${mins}:${secs.toFixed(1).padStart(4, "0")}`;
};

function normalize(vector: number[]) {
  const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0)) || 1;
  return vector.map((value) => value / norm);
}

function cosineDistance(a: number[], b: number[]) {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return 1 - dot / (Math.sqrt(normA * normB) || 1);
}

function makeDescriptor(data: Uint8ClampedArray, width: number, height: number) {
  const bins = 12;
  const hist = new Array(bins * 3).fill(0);
  const gridW = 8;
  const gridH = 6;
  const grid = new Array(gridW * gridH).fill(0);
  const counts = new Array(gridW * gridH).fill(0);
  let horizontal = 0;
  let vertical = 0;
  let diagonalA = 0;
  let diagonalB = 0;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const index = (y * width + x) * 4;
      const r = data[index];
      const g = data[index + 1];
      const b = data[index + 2];
      hist[Math.min(bins - 1, Math.floor(r / (256 / bins)))] += 1;
      hist[bins + Math.min(bins - 1, Math.floor(g / (256 / bins)))] += 1;
      hist[bins * 2 + Math.min(bins - 1, Math.floor(b / (256 / bins)))] += 1;
      const gray = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      const gx = Math.min(gridW - 1, Math.floor((x / width) * gridW));
      const gy = Math.min(gridH - 1, Math.floor((y / height) * gridH));
      const cell = gy * gridW + gx;
      grid[cell] += gray;
      counts[cell] += 1;

      if (x > 0 && y > 0) {
        const left = (y * width + x - 1) * 4;
        const up = ((y - 1) * width + x) * 4;
        const leftGray = (0.299 * data[left] + 0.587 * data[left + 1] + 0.114 * data[left + 2]) / 255;
        const upGray = (0.299 * data[up] + 0.587 * data[up + 1] + 0.114 * data[up + 2]) / 255;
        const dx = gray - leftGray;
        const dy = gray - upGray;
        horizontal += Math.abs(dx);
        vertical += Math.abs(dy);
        diagonalA += Math.abs(dx + dy);
        diagonalB += Math.abs(dx - dy);
      }
    }
  }

  const pixels = width * height;
  const histNorm = hist.map((value) => value / pixels);
  const gridNorm = grid.map((value, index) => value / Math.max(1, counts[index]));
  const edgeNorm = [horizontal, vertical, diagonalA, diagonalB].map((value) => value / pixels);
  return normalize([...histNorm, ...gridNorm, ...edgeNorm]);
}

const COS_TABLE = Array.from({ length: 8 }, (_, u) =>
  Array.from({ length: 8 }, (_, x) => Math.cos(((2 * x + 1) * u * Math.PI) / 16)),
);

function dctStats(gray: Float32Array, width: number, height: number): DctStats {
  let low = 0;
  let mid = 0;
  let high = 0;
  let boundary = 0;
  let internal = 0;
  let boundaryCount = 0;
  let internalCount = 0;

  for (let by = 0; by <= height - 8; by += 8) {
    for (let bx = 0; bx <= width - 8; bx += 8) {
      for (let v = 0; v < 8; v += 1) {
        for (let u = 0; u < 8; u += 1) {
          if (u === 0 && v === 0) continue;
          let coefficient = 0;
          for (let y = 0; y < 8; y += 1) {
            for (let x = 0; x < 8; x += 1) {
              coefficient += (gray[(by + y) * width + bx + x] - 128) * COS_TABLE[u][x] * COS_TABLE[v][y];
            }
          }
          const energy = coefficient * coefficient;
          const band = u + v;
          if (band <= 3) low += energy;
          else if (band <= 7) mid += energy;
          else high += energy;
        }
      }
    }
  }

  for (let y = 1; y < height; y += 1) {
    for (let x = 1; x < width; x += 1) {
      const here = gray[y * width + x];
      const dx = Math.abs(here - gray[y * width + x - 1]);
      const dy = Math.abs(here - gray[(y - 1) * width + x]);
      if (x % 8 === 0 || y % 8 === 0) {
        boundary += dx + dy;
        boundaryCount += 2;
      } else {
        internal += dx + dy;
        internalCount += 2;
      }
    }
  }

  const total = low + mid + high || 1;
  const boundaryAvg = boundary / Math.max(1, boundaryCount);
  const internalAvg = internal / Math.max(1, internalCount);
  return {
    low: low / total,
    mid: mid / total,
    high: high / total,
    blockiness: boundaryAvg / Math.max(0.01, internalAvg),
  };
}

function blockMotion(previous: Float32Array, current: Float32Array, width: number, height: number): FlowStats {
  const block = 8;
  const radius = 2;
  const vectors: { dx: number; dy: number; residual: number }[] = [];

  for (let by = radius; by <= height - block - radius; by += block) {
    for (let bx = radius; bx <= width - block - radius; bx += block) {
      let best = Number.POSITIVE_INFINITY;
      let bestDx = 0;
      let bestDy = 0;
      for (let dy = -radius; dy <= radius; dy += 1) {
        for (let dx = -radius; dx <= radius; dx += 1) {
          let error = 0;
          let count = 0;
          for (let y = 0; y < block; y += 2) {
            for (let x = 0; x < block; x += 2) {
              const a = previous[(by + y) * width + bx + x];
              const b = current[(by + y + dy) * width + bx + x + dx];
              error += Math.abs(a - b);
              count += 1;
            }
          }
          const averageError = error / Math.max(1, count);
          if (averageError < best) {
            best = averageError;
            bestDx = dx;
            bestDy = dy;
          }
        }
      }
      vectors.push({ dx: bestDx, dy: bestDy, residual: best / 255 });
    }
  }

  const meanDx = mean(vectors.map((vector) => vector.dx));
  const meanDy = mean(vectors.map((vector) => vector.dy));
  const magnitude = mean(vectors.map((vector) => Math.hypot(vector.dx, vector.dy)));
  const spread = mean(vectors.map((vector) => Math.hypot(vector.dx - meanDx, vector.dy - meanDy)));
  return {
    magnitude,
    inconsistency: spread / (magnitude + 0.5),
    residual: mean(vectors.map((vector) => vector.residual)),
  };
}

function angleBetween(a: number[], b: number[]) {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denominator = Math.sqrt(normA * normB);
  if (denominator < 1e-9) return 0;
  return (Math.acos(clamp(dot / denominator, -1, 1)) * 180) / Math.PI;
}

function subtract(a: number[], b: number[]) {
  return a.map((value, index) => value - b[index]);
}

function buildResults(frames: SampleFrame[], flows: FlowStats[], video: HTMLVideoElement): AnalysisResult {
  const descriptors = frames.map((frame) => frame.descriptor);
  const distances = descriptors.slice(1).map((descriptor, index) => cosineDistance(descriptors[index], descriptor));
  const acceleration = distances.slice(1).map((distance, index) => distance - distances[index]);
  const absAcceleration = acceleration.map(Math.abs);
  const d3Ratio = standardDeviation(acceleration) / (mean(distances) + 1e-6);
  const d3Score = Math.round(100 * d3Ratio / (d3Ratio + 1.6));
  const d3Top = absAcceleration.indexOf(Math.max(...absAcceleration, 0)) + 1;

  const deltas = descriptors.slice(1).map((descriptor, index) => subtract(descriptor, descriptors[index]));
  const steps = deltas.map((delta) => Math.sqrt(delta.reduce((sum, value) => sum + value * value, 0)));
  const angles = deltas.slice(1).map((delta, index) => angleBetween(deltas[index], delta));
  const stepCv = standardDeviation(steps) / (mean(steps) + 1e-6);
  const avgAngle = mean(angles);
  const trajectoryScore = Math.round(100 * (0.55 * (avgAngle / 180) + 0.45 * (stepCv / (stepCv + 1))));
  const trajectoryTop = angles.indexOf(Math.max(...angles, 0)) + 1;

  const flowValues = flows.map((flow) => 0.65 * flow.inconsistency + 0.35 * flow.residual * 3);
  const flowMean = mean(flowValues);
  const flowScore = Math.round(100 * flowMean / (flowMean + 1.2));
  const flowTop = flowValues.indexOf(Math.max(...flowValues, 0)) + 1;

  const highRatios = frames.map((frame) => frame.dct.high);
  const blockiness = frames.map((frame) => frame.dct.blockiness);
  const highVolatility = standardDeviation(highRatios) / (mean(highRatios) + 1e-6);
  const blockExcess = Math.max(0, mean(blockiness) - 1);
  const dctRaw = 0.68 * highVolatility + 0.32 * blockExcess;
  const dctScore = Math.round(100 * dctRaw / (dctRaw + 0.8));
  const dctChanges = highRatios.map((value, index) => index ? Math.abs(value - highRatios[index - 1]) : 0);
  const dctTop = dctChanges.indexOf(Math.max(...dctChanges, 0));

  const thumbAt = (index: number) => frames[Math.min(frames.length - 1, Math.max(0, index))]?.thumb || "";
  const timeAt = (index: number) => frames[Math.min(frames.length - 1, Math.max(0, index))]?.time || 0;

  const methods: MethodResult[] = [
    {
      id: "d3", number: "01", title: "向量二阶变化", label: "D3结构代理", score: d3Score,
      headline: d3Score >= 60 ? "帧间变化速度存在明显起伏" : "帧间变化速度相对平稳",
      explanation: "先把每帧表示为颜色、亮度网格和边缘组成的透明向量，再计算相邻距离及其二阶变化。",
      limitation: "当前使用轻量帧描述符，不是DINOv2语义向量，因此只能验证D3的计算结构，不能复现论文准确率。",
      formula: "dₜ = 1 − cos(zₜ, zₜ₊₁)；aₜ = dₜ₊₁ − dₜ",
      seriesLabel: "二阶变化幅度", accent: "#ff6b4a", topTime: timeAt(d3Top + 1), topThumb: thumbAt(d3Top + 1),
      series: absAcceleration.map((value, index) => ({ time: timeAt(index + 2), value })),
      facts: [
        { name: "平均帧距", value: mean(distances).toFixed(4) },
        { name: "二阶波动", value: standardDeviation(acceleration).toFixed(4) },
        { name: "最高异常点", value: formatTime(timeAt(d3Top + 1)) },
      ],
    },
    {
      id: "trajectory", number: "02", title: "特征轨迹", label: "ReStraV结构代理", score: trajectoryScore,
      headline: trajectoryScore >= 60 ? "特征路线出现较多急转或变速" : "特征路线未见强烈急转",
      explanation: "把相邻帧向量之差视为移动方向，同时观察每一步的长度以及连续两步之间的夹角。",
      limitation: "当前展示轨迹证据，未加载ReStraV论文分类器，也没有把指数解释为AI概率。",
      formula: "Δzₜ = zₜ₊₁ − zₜ；θₜ = angle(Δzₜ, Δzₜ₊₁)",
      seriesLabel: "转角（度）", accent: "#6d5efc", topTime: timeAt(trajectoryTop + 1), topThumb: thumbAt(trajectoryTop + 1),
      series: angles.map((value, index) => ({ time: timeAt(index + 2), value })),
      facts: [
        { name: "平均转角", value: `${avgAngle.toFixed(1)}°` },
        { name: "步长变异系数", value: stepCv.toFixed(2) },
        { name: "最高异常点", value: formatTime(timeAt(trajectoryTop + 1)) },
      ],
    },
    {
      id: "flow", number: "03", title: "运动一致性", label: "传统块匹配光流", score: flowScore,
      headline: flowScore >= 60 ? "局部运动方向存在较强分歧" : "局部运动总体保持一致",
      explanation: "将画面分成小块，在下一帧附近寻找最相似位置，得到局部运动向量并统计方向分歧与匹配残差。",
      limitation: "镜头切换、快速运动、遮挡和强压缩都可能提高该指数；它不是完整RAFT或AIGVDet模型。",
      formula: "vᵢ = argmin SAD(blockₜ, blockₜ₊₁)；检查局部vᵢ的离散程度",
      seriesLabel: "运动不一致度", accent: "#04a777", topTime: timeAt(flowTop), topThumb: thumbAt(flowTop),
      series: flowValues.map((value, index) => ({ time: timeAt(index + 1), value })),
      facts: [
        { name: "平均位移", value: `${mean(flows.map((flow) => flow.magnitude)).toFixed(2)} px` },
        { name: "平均匹配残差", value: mean(flows.map((flow) => flow.residual)).toFixed(3) },
        { name: "最高异常点", value: formatTime(timeAt(flowTop)) },
      ],
    },
    {
      id: "dct", number: "04", title: "频域痕迹", label: "8×8 DCT", score: dctScore,
      headline: dctScore >= 60 ? "高频能量或块边界波动较强" : "频率能量变化相对稳定",
      explanation: "对每帧的8×8图像块执行离散余弦变换，统计低、中、高频能量与块边界强度。",
      limitation: "社交平台二次编码、缩放和锐化会改变频谱，DCT异常不能单独证明视频由AI生成。",
      formula: "Xᵤᵥ = ΣₓΣᵧ fₓᵧ cos[·]cos[·]；比较不同频段能量",
      seriesLabel: "高频能量比例", accent: "#e6a91a", topTime: timeAt(dctTop), topThumb: thumbAt(dctTop),
      series: highRatios.map((value, index) => ({ time: timeAt(index), value })),
      facts: [
        { name: "平均高频占比", value: `${(mean(highRatios) * 100).toFixed(1)}%` },
        { name: "块边界比", value: mean(blockiness).toFixed(2) },
        { name: "最高异常点", value: formatTime(timeAt(dctTop)) },
      ],
    },
  ];

  return {
    duration: video.duration,
    width: video.videoWidth,
    height: video.videoHeight,
    samples: frames.length,
    generatedAt: new Date().toISOString(),
    methods,
    flagged: methods.filter((method) => method.score >= 60).length,
  };
}

function waitForSeek(video: HTMLVideoElement, time: number) {
  return new Promise<void>((resolve, reject) => {
    if (video.readyState >= 2 && Math.abs(video.currentTime - time) < 0.01) {
      resolve();
      return;
    }
    const timeout = window.setTimeout(() => reject(new Error("视频定位超时，请尝试较短或标准MP4视频。")), 9000);
    const done = () => {
      window.clearTimeout(timeout);
      resolve();
    };
    video.addEventListener("seeked", done, { once: true });
    video.currentTime = Math.min(Math.max(0, time), Math.max(0, video.duration - 0.03));
  });
}

function waitForVideoReady(video: HTMLVideoElement) {
  return new Promise<void>((resolve, reject) => {
    if (video.readyState >= 2 && Number.isFinite(video.duration)) {
      resolve();
      return;
    }
    const timeout = window.setTimeout(() => reject(new Error("视频载入超时，请确认浏览器支持这个编码格式。")), 9000);
    const done = () => {
      window.clearTimeout(timeout);
      resolve();
    };
    video.addEventListener("loadeddata", done, { once: true });
  });
}

function ScoreRing({ score, accent }: { score: number; accent: string }) {
  return (
    <div className="score-ring" style={{ "--score": `${score * 3.6}deg`, "--accent": accent } as React.CSSProperties}>
      <span>{score}</span>
      <small>/100</small>
    </div>
  );
}

function SeriesChart({ points, accent, label }: { points: SeriesPoint[]; accent: string; label: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, rect.width * ratio);
      canvas.height = Math.max(1, rect.height * ratio);
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.scale(ratio, ratio);
      const width = rect.width;
      const height = rect.height;
      const pad = { top: 18, right: 14, bottom: 28, left: 12 };
      const plotW = width - pad.left - pad.right;
      const plotH = height - pad.top - pad.bottom;
      ctx.clearRect(0, 0, width, height);
      ctx.strokeStyle = "rgba(36, 43, 53, 0.10)";
      ctx.lineWidth = 1;
      for (let line = 0; line <= 3; line += 1) {
        const y = pad.top + (plotH * line) / 3;
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
      }
      if (!points.length) return;
      const max = Math.max(...points.map((point) => point.value), 1e-6);
      const min = Math.min(...points.map((point) => point.value), 0);
      const range = max - min || 1;
      const xAt = (index: number) => pad.left + (plotW * index) / Math.max(1, points.length - 1);
      const yAt = (value: number) => pad.top + plotH - ((value - min) / range) * plotH;

      const gradient = ctx.createLinearGradient(0, pad.top, 0, height - pad.bottom);
      gradient.addColorStop(0, `${accent}42`);
      gradient.addColorStop(1, `${accent}03`);
      ctx.beginPath();
      points.forEach((point, index) => {
        const x = xAt(index); const y = yAt(point.value);
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.lineTo(xAt(points.length - 1), height - pad.bottom);
      ctx.lineTo(xAt(0), height - pad.bottom);
      ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();

      ctx.beginPath();
      points.forEach((point, index) => {
        const x = xAt(index); const y = yAt(point.value);
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = accent; ctx.lineWidth = 2.4; ctx.lineJoin = "round"; ctx.stroke();
      const maxIndex = points.findIndex((point) => point.value === max);
      ctx.beginPath(); ctx.arc(xAt(maxIndex), yAt(max), 4.5, 0, Math.PI * 2); ctx.fillStyle = accent; ctx.fill();

      ctx.fillStyle = "#747b84"; ctx.font = "11px Arial";
      ctx.textAlign = "left"; ctx.fillText(formatTime(points[0].time), pad.left, height - 8);
      ctx.textAlign = "right"; ctx.fillText(formatTime(points[points.length - 1].time), width - pad.right, height - 8);
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [points, accent]);

  return <canvas ref={canvasRef} className="series-chart" aria-label={`${label}随时间变化图`} />;
}

export default function VideoLab() {
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState("等待选择视频");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeMethod, setActiveMethod] = useState<MethodResult["id"]>("d3");
  const [error, setError] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const chooseFile = useCallback((next: File | undefined) => {
    if (!next) return;
    if (!next.type.startsWith("video/")) {
      setError("请选择MP4、MOV或WebM视频文件。");
      return;
    }
    if (url) URL.revokeObjectURL(url);
    setFile(next);
    setUrl(URL.createObjectURL(next));
    setResult(null);
    setProgress(0);
    setPhase("视频已就绪");
    setError("");
  }, [url]);

  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);

  const active = useMemo(() => result?.methods.find((method) => method.id === activeMethod) || result?.methods[0], [result, activeMethod]);
  const reportDownload = useMemo(() => {
    if (!result || !file) return null;
    const payload = {
      notice: "本报告是未校准的视频异常初筛，不是对真实来源的司法鉴定。",
      file: { name: file.name, size: file.size, type: file.type },
      video: { duration: result.duration, width: result.width, height: result.height, samples: result.samples },
      methods: result.methods.map(({ topThumb: _topThumb, ...method }) => method),
      generatedAt: result.generatedAt,
    };
    return {
      href: `data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(payload, null, 2))}`,
      name: `${file.name.replace(/\.[^.]+$/, "")}-frametrace.json`,
    };
  }, [result, file]);

  const analyze = async () => {
    const video = videoRef.current;
    if (!video || !file) return;
    setAnalyzing(true);
    setError("");
    setResult(null);
    try {
      await waitForVideoReady(video);
      if (!Number.isFinite(video.duration) || video.duration <= 0) throw new Error("无法读取视频时长。请换用标准MP4文件。 ");
      const count = Math.min(36, Math.max(12, Math.ceil(video.duration * 1.5)));
      const times = Array.from({ length: count }, (_, index) => {
        if (count === 1) return 0;
        return (index / (count - 1)) * Math.max(0, video.duration - 0.05);
      });
      const frameCanvas = document.createElement("canvas");
      frameCanvas.width = 64; frameCanvas.height = 48;
      const frameContext = frameCanvas.getContext("2d", { willReadFrequently: true });
      const thumbCanvas = document.createElement("canvas");
      thumbCanvas.width = 256; thumbCanvas.height = 144;
      const thumbContext = thumbCanvas.getContext("2d");
      if (!frameContext || !thumbContext) throw new Error("浏览器无法创建视频分析画布。 ");
      const frames: SampleFrame[] = [];

      setPhase("正在抽取代表帧");
      for (let index = 0; index < times.length; index += 1) {
        await waitForSeek(video, times[index]);
        frameContext.drawImage(video, 0, 0, 64, 48);
        const image = frameContext.getImageData(0, 0, 64, 48);
        const gray = new Float32Array(64 * 48);
        for (let pixel = 0; pixel < gray.length; pixel += 1) {
          const offset = pixel * 4;
          gray[pixel] = 0.299 * image.data[offset] + 0.587 * image.data[offset + 1] + 0.114 * image.data[offset + 2];
        }
        thumbContext.drawImage(video, 0, 0, 256, 144);
        frames.push({
          time: times[index],
          descriptor: makeDescriptor(image.data, 64, 48),
          gray,
          dct: dctStats(gray, 64, 48),
          thumb: thumbCanvas.toDataURL("image/jpeg", 0.68),
        });
        setProgress(Math.round(((index + 1) / times.length) * 62));
        await new Promise((resolve) => window.setTimeout(resolve, 0));
      }

      setPhase("正在比较局部运动");
      const flows: FlowStats[] = [];
      for (let index = 1; index < frames.length; index += 1) {
        flows.push(blockMotion(frames[index - 1].gray, frames[index].gray, 64, 48));
        setProgress(62 + Math.round((index / (frames.length - 1)) * 28));
        await new Promise((resolve) => window.setTimeout(resolve, 0));
      }
      setPhase("正在整理四条证据链");
      const analysis = buildResults(frames, flows, video);
      setResult(analysis);
      setActiveMethod("d3");
      setProgress(100);
      setPhase("分析完成");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "分析过程中出现未知错误。 ");
      setPhase("分析未完成");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <main>
      <nav className="nav-shell">
        <a className="brand" href="#top" aria-label="FrameTrace 首页"><span className="brand-mark">FT</span><span>FrameTrace</span></a>
        <div className="nav-note"><span className="status-dot" /> 本地浏览器运行 · 视频不上传</div>
        <a className="nav-link" href="#methods">方法说明</a>
      </nav>

      <section className="hero" id="top">
        <div className="eyebrow">AI VIDEO FORENSICS · EXPLAINABLE BY DESIGN</div>
        <h1>四条证据链，<br /><em>查看视频哪里不自然。</em></h1>
        <p className="hero-copy">把抽象的“真假分数”拆成帧间变化、特征轨迹、局部运动和频域痕迹。结果始终指向具体时间点，也明确告诉你哪里可能被压缩和剪辑干扰。</p>
        <div className="hero-proof">
          <div><strong>4</strong><span>种互补方法</span></div>
          <div><strong>0</strong><span>次云端上传</span></div>
          <div><strong>100%</strong><span>可查看原始指标</span></div>
        </div>
      </section>

      <section className="lab-shell" aria-label="视频分析工作区">
        <div className="lab-heading">
          <div><span className="section-index">01 / INPUT</span><h2>选择待检查视频</h2></div>
          <p>建议先使用30秒至3分钟的片段。较长视频会均匀抽取最多36帧，不会逐帧保存。</p>
        </div>
        <div className="workspace-grid">
          <div
            className={`drop-zone ${dragging ? "is-dragging" : ""} ${file ? "has-file" : ""}`}
            onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]); }}
          >
            <input ref={fileInputRef} type="file" accept="video/mp4,video/quicktime,video/webm" onChange={(event) => chooseFile(event.target.files?.[0])} />
            <div className="upload-symbol"><span /><span /><span /></div>
            <h3>{file ? file.name : "拖入一个视频开始"}</h3>
            <p>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB · 文件仅保留在当前浏览器标签页` : "支持 MP4、MOV、WebM；也可以从 final_accounts 文件夹选择"}</p>
            <button className="secondary-button" type="button" onClick={() => fileInputRef.current?.click()}>{file ? "更换视频" : "浏览文件"}</button>
          </div>
          <div className="preview-card">
            {url ? <video ref={videoRef} key={url} src={url} controls preload="metadata" /> : <div className="empty-preview"><span>00:00</span><p>视频预览将显示在这里</p></div>}
            <div className="preview-footer">
              <div><span className="mini-label">处理方式</span><strong>最多36帧均匀采样</strong></div>
              <div><span className="mini-label">隐私</span><strong>本机内存计算</strong></div>
            </div>
          </div>
        </div>
        {error && <div className="error-box" role="alert">{error}</div>}
        <div className="action-row">
          <button className="primary-button" type="button" disabled={!file || analyzing} onClick={analyze}>
            {analyzing ? "正在分析…" : result ? "重新分析" : "开始四项检查"}<span>→</span>
          </button>
          <div className="progress-shell" aria-live="polite">
            <div className="progress-copy"><span>{phase}</span><strong>{progress}%</strong></div>
            <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
          </div>
        </div>
      </section>

      {result && active && (
        <section className="results-shell" aria-label="分析结果">
          <div className="result-summary">
            <div><span className="section-index">02 / EVIDENCE</span><h2>{result.flagged ? `${result.flagged}项指标出现较高内部波动` : "未发现强烈的内部异常波动"}</h2></div>
            <p>这是一份<strong>未校准的异常初筛</strong>。它不能单独证明视频真实或由AI生成，必须结合来源、压缩情况和参考视频。</p>
            {reportDownload && <a className="download-button" href={reportDownload.href} download={reportDownload.name}>下载JSON报告 ↓</a>}
          </div>
          <div className="method-tabs" role="tablist" aria-label="选择检测方法">
            {result.methods.map((method) => (
              <button key={method.id} role="tab" aria-selected={activeMethod === method.id} className={activeMethod === method.id ? "active" : ""} onClick={() => setActiveMethod(method.id)}>
                <span>{method.number}</span><strong>{method.title}</strong><small>{method.score}</small>
              </button>
            ))}
          </div>
          <article className="method-detail" style={{ "--accent": active.accent } as React.CSSProperties}>
            <div className="method-lead">
              <div><span className="method-tag">{active.label}</span><h3>{active.headline}</h3><p>{active.explanation}</p></div>
              <ScoreRing score={active.score} accent={active.accent} />
            </div>
            <div className="chart-panel">
              <div className="chart-title"><span>{active.seriesLabel}</span><small>最高点位于 {formatTime(active.topTime)}</small></div>
              <SeriesChart points={active.series} accent={active.accent} label={active.seriesLabel} />
            </div>
            <div className="evidence-grid">
              <div className="frame-evidence">
                <span className="mini-label">最高异常时间点</span>
                {active.topThumb && <img src={active.topThumb} alt={`${formatTime(active.topTime)}的视频帧`} />}
                <strong>{formatTime(active.topTime)}</strong>
              </div>
              <div className="fact-list">
                {active.facts.map((fact) => <div key={fact.name}><span>{fact.name}</span><strong>{fact.value}</strong></div>)}
              </div>
              <div className="method-notes">
                <div><span className="mini-label">计算方式</span><code>{active.formula}</code></div>
                <div className="warning-note"><span>!</span><p>{active.limitation}</p></div>
              </div>
            </div>
          </article>
        </section>
      )}

      <section className="methods-section" id="methods">
        <div className="section-heading"><span className="section-index">03 / METHODS</span><h2>每一项分数，都能回到计算过程。</h2><p>四种方法观察不同层面的信号。单独一项异常很常见，多项方法在同一时间段共同异常才更值得复核。</p></div>
        <div className="method-intro-grid">
          {METHOD_INTRO.map((method) => <article key={method.number}><span>{method.number}</span><div><small>{method.tag}</small><h3>{method.title}</h3><p>{method.copy}</p></div></article>)}
        </div>
        <div className="boundary-card">
          <div className="boundary-mark">≠</div>
          <div><span className="mini-label">重要边界</span><h3>异常指数不是“AI概率”</h3><p>当前版本没有真实/AI参考库，也没有加载DINOv2或论文分类器。它适合学习方法、寻找异常时间点和比较同类视频；不适合身份认定、执法或法律结论。</p></div>
          <div className="boundary-list"><span>下一步可升级</span><strong>DINOv2共享向量</strong><strong>真实/AI参考库</strong><strong>MMD分布比较</strong></div>
        </div>
      </section>

      <footer><div className="brand"><span className="brand-mark">FT</span><span>FrameTrace</span></div><p>Explainable video screening · Local-first</p><a href="#top">返回顶部 ↑</a></footer>
    </main>
  );
}
