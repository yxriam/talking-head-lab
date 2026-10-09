import { request, upload } from './api';
import type { Media } from './api';

export type CrawlMedia = {
  id?: string; filename?: string; name: string; kind: 'image'|'video'|'audio';
  source_url: string; status: 'downloaded'|'link_only'|'failed'|'duplicate';
  url?: string; size?: number; reason?: string;
};
export type CrawlResult = {
  source_url: string; title: string; text: Array<{text:string; source_url:string; date?:string; context?:string; reposted?:boolean}>;
  media: CrawlMedia[]; warnings: string[]; elapsed_seconds: number;
  analysis?: AccountRiskReport;
};
export type AccountRiskReport = {
  version:string; method:string; generated_at:string;
  generation?:{kind:'rules'|'llm'; model:string|null; elapsed_seconds?:number; fallback_reason?:string};
  account_purpose:{label:string; reason:string; evidence_ids:string[]};
  visibility:{label:string; reason:string; evidence_ids:string[]};
  scope:string; limits:string[];
  narrative?:string[];
  conclusion:string;
  narrative_en?:string[];
  conclusion_en?:string;
};
export type CrawlJob = {
  id:string; kind:'crawl'|'login'; status:'queued'|'running'|'done'|'failed'|'cancelled'|'needs_login';
  stage:string; progress:number; message:string; created_at:string; source_url:string;
  counts:Record<string,number>; result?:CrawlResult; elapsed_seconds?:number;
};
export type CrawlHealth = {ready:boolean; session_saved:boolean; browser:string; account_analysis?:{ready:boolean; model?:string; reason?:string}};
const call = <T,>(path:string, options:RequestInit = {}) => request<T>(path,options,'/crawl');
const post = <T,>(path:string, body?:unknown) => call<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:body ? JSON.stringify(body) : undefined});
export const health = () => call<CrawlHealth>('/health');
export const history = () => call<CrawlJob[]>('/jobs');
export const status = (id:string) => call<CrawlJob>(`/jobs/${id}`);
export const login = () => post<CrawlJob>('/browser');
export const cancel = (id:string) => post(`/jobs/${id}/cancel`);
export async function analyze(id:string):Promise<AccountRiskReport> {
  // Local generation may take longer than the shared API's 30-second timeout.
  const response=await fetch(`/crawl/jobs/${id}/analyze`,{method:'POST',signal:AbortSignal.timeout(150000)});
  const data=await response.json();
  if(!response.ok) throw new Error(typeof data.detail==='string' ? data.detail : '本地账号 LLM 分析失败');
  return data;
}
export const start = (options:{url:string; max_scrolls:number; download_media:boolean}) => post<CrawlJob>('/jobs',options);

export async function importMedia(asset:CrawlMedia):Promise<Media> {
  if (asset.status !== 'downloaded' || !asset.url?.startsWith('/crawl/media/')) throw new Error('素材未下载');
  const response = await fetch(asset.url,{signal:AbortSignal.timeout(120000)});
  if (!response.ok) throw new Error('无法读取采集素材');
  const file = new File([await response.blob()],asset.filename || asset.name,{type:response.headers.get('Content-Type') || `${asset.kind}/*`});
  const id = await upload({name:file.name,url:asset.url,file,kind:asset.kind});
  return {id,name:asset.name || file.name,url:`/api/media/${id}`,kind:asset.kind};
}
