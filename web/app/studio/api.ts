// Only local backend requests. Generated files are reused by ID, never re-uploaded.
const BASE = '/api';
export type Media = { name: string; url: string; file?: File; id?: string; kind?: 'image'|'audio'|'video'; source_text?: string; model?: VideoModel; presentation?: 'square'|'portrait' };
export type Mode = 'voice' | 'video' | 'detect';
export type VideoModel = 'sadtalker'|'echomimic_v1'|'joyvasa'|'echomimic_v3_flash'|'tokenhub_humanactor';
export type Capability = { ready: boolean; name?: string; reason: string; models?: Record<VideoModel, Capability>; cloud?: { truthscan?: Capability } };
export type Health = { status: string; capabilities: Record<Mode, Capability> };
export type DetectionMethod = {
  id: string; name: string; status: string; verdict: string; score: number|null;
  decision?: 'pass'|'fail'|'uncertain'; passed?: boolean; primary?: boolean;
  ai_probability?: number|null; real_probability?: number|null; confidence?: number|null;
  thresholds?: { real: number; ai: number };
  threshold_text?: string;
  principle?: string; paper?: string;
  evidence?: {
    area: string; explanation: string;
    high: Array<{start_frame:number; end_frame:number; start_time:number; end_time:number; ai_probability:number}>;
    low: Array<{start_frame:number; end_frame:number; start_time:number; end_time:number; ai_probability:number}>;
  };
  metrics?: Record<string,number>; distribution?: number[];
};
export type DetectionReport = {
  media_type: 'image'|'video'; verdict: string; reason: string; note: string;
  ai_probability: number; real_probability: number; confidence: number;
  summary: { total: number; completed: number; passed: number; failed: number; uncertain: number };
  sampling: { sampled_frames: number; face_frames: number; sampling_strategy?: string; effective_sample_fps?: number };
  methods: DetectionMethod[];
  supporting_methods: DetectionMethod[];
};
type Job = { id: string; status: 'queued'|'running'|'done'|'failed'; message: string; progress?: number; model?: string; elapsed_seconds?: number; result?: Media | DetectionReport };
type ProgressHandler = (message: string, progress: number) => void;

export async function request<T>(path: string, options: RequestInit = {}, base = BASE): Promise<T> {
  let response: Response;
  try {
    response = await fetch(base + path, {...options, signal: AbortSignal.timeout(30000)});
  } catch {
    throw new Error('无法连接本地服务，请确认后端已启动。');
  }
  const data = await response.json();
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((item:{msg?:string})=>item.msg || '').join('；') : '提交失败，请检查输入。';
    throw new Error(detail);
  }
  return data;
}

export function health() { return request<Health>('/health'); }

export async function upload(media: Media): Promise<string> {
  if (media.id) return media.id;
  if (!media.file) throw new Error('素材已失效，请重新选择文件。');
  const body = new FormData();
  body.append('file', media.file);
  const result = await request<Media>('/media', { method: 'POST', body });
  return result.id!;
}

async function runJob(payload: Record<string, string>, onProgress: ProgressHandler) {
  let job = await request<Job>('/jobs', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  // Poll only the accepted job, never resubmit a generation on a network error.
  const deadline = Date.now() + 65 * 60 * 1000;
  while (job.status === 'queued' || job.status === 'running') {
    onProgress(job.message, job.progress ?? 0);
    if (Date.now() > deadline) throw new Error(`等待任务超时，任务编号：${job.id}。请检查本地日志。`);
    await new Promise(resolve=>setTimeout(resolve,1500));
    job = await request<Job>(`/jobs/${job.id}`);
  }
  if (job.status === 'failed') throw new Error(job.message);
  if (!job.result) throw new Error('任务没有返回结果。');
  return job.result;
}

export async function generate(payload: Record<string, string>, onProgress: ProgressHandler) {
  const result = await runJob(payload, onProgress);
  if (!('url' in result)) throw new Error('生成任务返回了错误的结果类型。');
  return {...result, url: BASE + result.url};
}

export async function analyze(payload: Record<string, string>, onProgress: ProgressHandler) {
  const result = await runJob(payload, onProgress);
  if (!('methods' in result)) throw new Error('检测任务没有返回分析报告。');
  return result;
}
