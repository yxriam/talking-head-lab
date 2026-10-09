"use client";

import { useEffect, useRef, useState } from 'react';
import './studio.css';
import * as api from './api';
import type { DetectionMethod, Media, Mode, VideoModel } from './api';
import CrawlPanel from './CrawlPanel';

// Generated outputs use a local server URL; the same artifact is handed to detection.
type StudioProps = { generatedVideo?: Media | null; generatedVoice?: Media | null };
type Language = 'zh'|'en';
type StudioMode = Mode|'crawl';
const EN: Record<string,string> = {
  '爬取信息':'Collect information','Facebook 采集':'Facebook collection','采集可见文字、图片和视频，选好素材后带入生成或分析。':'Collect visible text, images, and video, then choose media for creation or analysis.','已带入采集素材':'Collected media ready',
  'AI 媒体实验室':'AI Media Lab','工作区':'Workspace','音色克隆':'Voice Cloning','AI 人像视频':'AI Portrait Video','媒体真伪检测':'Media Authenticity',
  '本地工作区':'Local workspace','素材在此设备处理':'Media is processed on this device','参考音频或视频':'Reference audio or video','上传参考音频或视频':'Upload reference audio or video','任务处理中':'Processing','TokenHub 已就绪':'TokenHub ready','本地模型已就绪':'Local models ready','服务已连接 · 模型待配置':'Service connected · setup required','本地服务未连接':'Local service unavailable',
  '将克隆后的语音与人像照片合成为视频。':'Combine a cloned voice with a portrait photo to create a video.','提供参考声音，用相同音色朗读新的文字。':'Provide a reference voice and read new text in the same voice.','上传图片或视频，查看各方法的逐帧判断与汇总结论。':'Upload an image or video to view per-frame evidence and the combined conclusion.',
  '准备素材':'Prepare media','使用腾讯云生成':'Generated with Tencent Cloud','仅在本地使用':'Local processing only','人像照片':'Portrait photo','驱动语音':'Driving audio','参考语音':'Reference audio','上传驱动语音':'Upload driving audio','上传参考语音':'Upload reference audio','人像模型':'Portrait model','本地 · 快速':'Local · Fast','本地 · 20 秒以内':'Local · Up to 20 seconds','本地 · 自动裁剪与头部动作':'Local · Auto crop and head motion','本地 · 高质量 · 很慢':'Local · High quality · Very slow','云端 · 动作更自然':'Cloud · More natural motion',
  '本地 · 身份稳定 · 方形':'Local · Stable identity · Square','本地 · 20 秒 · 方形':'Local · 20 seconds · Square','本地 · 快速动作 · 方形':'Local · Fast motion · Square','本地 · 4 秒实验 · 方形':'Local · 4-second experiment · Square','云端 · 自然动作 · 竖版':'Cloud · Natural motion · Portrait',
  '原图直接交给模型，不额外替换背景。':'The original image goes directly to the model without extra background replacement.','扩展人脸方形输出，不回贴原始大图。':'Expanded face-square output without pasting it back into the source image.','原生 512 方形输出，不重构画幅。':'Native 512-square output with no reframing.','保留模型原生方形头部动作，不进行二次裁剪。':'Keeps the model’s native square head motion without a second crop.','原生 384 方形短片，不分段拼接。':'Native 384-square short clip with no segment stitching.','保留完整竖版肖像，使用云端自然动作。':'Keeps the complete portrait composition with cloud-generated natural motion.',
  '需要说出的文字':'Text to speak','在这里输入希望人物说出的内容……':'Enter the text you want the person to say…','照片与驱动语音会提交至腾讯云生成；语音的 COS 临时文件会在任务结束后删除。':'The photo and driving audio are sent to Tencent Cloud. The temporary COS audio file is deleted when the job finishes.','请使用已获授权的照片与声音。生成内容仅用于授权演示与检测研究。':'Use only photos and voices you are authorized to use. Generated content is for authorized demonstrations and detection research.',
  '处理中':'Processing','生成视频':'Generate video','生成语音':'Generate voice','视频预览':'Video preview','语音预览':'Voice preview','已生成':'Generated','等待生成':'Waiting','生成的视频':'Generated video','克隆后的语音':'Cloned voice','让你的照片开口说话':'Bring your photo to life','听见你的文字':'Hear your text','生成的视频将在这里显示':'The generated video will appear here','生成后可在这里试听与下载':'Preview and download the result here','检测这个视频':'Detect this video','用这段语音生成人像视频':'Create a portrait video with this voice','生成完成后，直接带入检测，无需下载或重新上传':'Send the result directly to detection without downloading or uploading again','克隆完成后，直接带入人像视频，无需下载或重新上传':'Send the cloned voice directly to portrait video without downloading or uploading again',
  '使用 TruthScan 免费云端复核':'Use free TruthScan cloud check','视频会上传；每月免费 30 秒':'The video will be uploaded · 30 free seconds per month','开始检测':'Start detection','检测结果':'Detection result','分析完成':'Analysis complete','尚未分析':'Not analyzed','等待媒体检测':'Waiting for media','这里将汇总全部可用检测方法。':'All available detection methods will be summarized here.','方法通过':'Methods passed','方法未通过':'Methods failed','证据不足':'Insufficient evidence','辅助取证指标':'Supporting forensic measurements','查看测量值':'View measurements','查看研究来源':'View research source','检测结果仅供参考':'Detection results are for reference only','本地模型生成':'Local model generation','TokenHub 云端生成':'TokenHub cloud generation',
  'AI 概率':'AI probability','正常拍摄':'Authentic capture','方法':'Method','等待分析。':'Waiting for analysis.','单项结论':'Method conclusion','分类置信度':'Classification confidence','分析区域':'Analyzed region','AI 率较高':'Higher AI score','AI 率较低':'Lower AI score','查看方法来源':'View method source',
  '上传人像照片':'Upload portrait photo','上传检测图片或视频':'Upload image or video for detection','上传检测视频':'Upload video for detection','已选图片':'Selected image','替换':'Replace','移除文件':'Remove file','上传需要检测的图片或视频':'Upload an image or video to detect','上传需要检测的视频':'Upload a video to detect','点击选择，或拖放到这里':'Choose a file or drag it here','JPG、PNG、WebP · 清晰正脸':'JPG, PNG, WebP · Clear front-facing portrait','WAV、MP3 等 · 单人清晰语音':'WAV, MP3, etc. · Clear single-speaker audio','WAV、MP3、MP4、MOV 等 · 提取单人清晰语音':'WAV, MP3, MP4, MOV, etc. · Extract clear single-speaker audio','JPG、PNG、WebP、MP4、MOV 等 · 最大 500 MB':'JPG, PNG, WebP, MP4, MOV, etc. · 500 MB max','MP4、MOV、WebM 等 · 最大 500 MB':'MP4, MOV, WebM, etc. · 500 MB max','请选择正确类型的文件。':'Choose a supported file type.','文件需小于 500 MB。':'The file must be smaller than 500 MB.','生成输入':'Generation input','生成结果':'Generation result',
  '正在检查本地服务':'Checking the local service','频谱分布取证':'Frequency-spectrum forensics','视频时序连续性':'Video temporal continuity','压缩与噪声连续性':'Compression and noise continuity','对亮度通道加 Hann 窗后计算二维 FFT，并做径向功率分布；生成与缩放流程可能改变高频统计。':'Computes a windowed 2D FFT and radial power distribution; generation and resizing can alter high-frequency statistics.','对连续对齐人脸计算稠密光流、帧间变化及运动向量突变，覆盖静态分类器忽略的时间维度。':'Measures dense optical flow, frame changes, and motion-vector jumps on aligned faces.','比较 8×8 边界与内部差异，并测量局部高通残差的空间离散程度。':'Compares 8×8 boundaries with interiors and measures the spatial dispersion of local high-pass residuals.','高频能量占比':'High-frequency energy ratio','径向谱斜率':'Radial spectrum slope','帧间残差中位数':'Median frame residual','光流幅度中位数':'Median optical-flow magnitude','运动突变中位数':'Median motion jump','时间跨度秒':'Time span (seconds)','8×8 边界差异比':'8×8 boundary difference ratio','局部噪声离散系数':'Local noise dispersion coefficient','无法连接本地服务，请确认后端已启动。':'Cannot connect to the local service. Make sure the backend is running.','提交失败，请检查输入。':'Submission failed. Check the input.','素材已失效，请重新选择文件。':'The media is no longer available. Choose it again.','任务没有返回结果。':'The task returned no result.','检测任务没有返回分析报告。':'The detection task returned no report.','所选模型尚未就绪':'The selected model is not ready','正在将素材保存到本地服务':'Saving media to the local service','已完成':'Complete','处理失败，请重试':'Processing failed. Try again.','照片驱动时序静态性':'Photo-driven temporal staticness',
};
const titles = { video: 'AI 人像视频', voice: '音色克隆', detect: '媒体真伪检测', crawl: '爬取信息' } as const;
const VIDEO_OPTIONS: Array<{id:VideoModel; name:string; detail:string}> = [
  {id:'sadtalker',name:'SadTalker',detail:'本地 · 身份稳定 · 方形'},
  {id:'echomimic_v1',name:'EchoMimic V1',detail:'本地 · 20 秒 · 方形'},
  {id:'joyvasa',name:'JoyVASA',detail:'本地 · 快速动作 · 方形'},
  {id:'echomimic_v3_flash',name:'EchoMimic V3 Flash',detail:'本地 · 4 秒实验 · 方形'},
  {id:'tokenhub_humanactor',name:'YT HumanActor',detail:'云端 · 自然动作 · 竖版'},
];
const VIDEO_NOTES: Record<VideoModel,string> = {
  sadtalker:'扩展人脸方形输出，不回贴原始大图。',
  echomimic_v1:'原生 512 方形输出，不重构画幅。',
  joyvasa:'保留模型原生方形头部动作，不进行二次裁剪。',
  echomimic_v3_flash:'原生 384 方形短片，不分段拼接。',
  tokenhub_humanactor:'保留完整竖版肖像，使用云端自然动作。',
};
function localizedText(value: string|undefined, language: Language) {
  if (!value || language === 'zh') return value || '';
  const exact: Record<string,string> = {'AI 生成倾向':'AI-generated likely','真实拍摄倾向':'Authentic capture likely','模型分歧，结论不确定':'Inconclusive model disagreement','通过：真实倾向':'Pass: authentic leaning','未通过：AI 倾向':'Fail: AI leaning','证据不足：不参与视频真实性投票':'Insufficient evidence: excluded from the video vote','未通过：画面长期近静态':'Fail: prolonged static frame','通过：存在自然时序变化':'Pass: natural temporal variation','等待分析':'Waiting for analysis','云端复核未完成':'Cloud check unavailable','取证指标，需参考库校准':'Forensic measurement; reference calibration required','时序异常需结合剪辑与压缩解释':'Temporal anomaly; interpret with editing and compression context'};
  if (exact[value]) return exact[value];
  const summary = value.match(/(\d+) 项模型完成判断：(\d+) 项通过、(\d+) 项未通过(?:、(\d+) 项证据不足)?。(.+)/);
  if (summary) return `${summary[1]} methods completed: ${summary[2]} passed, ${summary[3]} failed${summary[4] ? `, ${summary[4]} insufficient` : ''}. ${summary[5].includes('任一') ? 'Any calibrated anomaly signal counts as AI evidence.' : ''}`;
  const progress: Record<string,string> = {'等待处理':'Waiting','正在准备语音模型':'Preparing the voice model','正在分析人像与语音':'Analyzing the portrait and audio','JoyVASA 正在生成人脸、表情与头部动作':'JoyVASA is generating facial expression and head motion','EchoMimic V3 正在分段加载模型':'EchoMimic V3 is loading in stages','EchoMimic V3 正在扩散渲染':'EchoMimic V3 is rendering','正在抽取人脸帧':'Extracting face frames','正在运行本地检测方法':'Running local detection methods','正在提交 TruthScan 免费云端复核':'Submitting the free TruthScan cloud check','TruthScan 正在分析视频':'TruthScan is analyzing the video','已完成':'Complete'};
  return progress[value] || EN[value] || value;
}
function useMedia() {
  const [value, setValue] = useState<Media|null>(null);
  useEffect(()=>()=>{if(value?.url.startsWith('blob:')) URL.revokeObjectURL(value.url)},[value]);
  return [value, setValue] as const;
}
function Icon({name, size = 22}: {name: string; size?: number}) {
  const paths: Record<string,string> = { video:'M4 5h12v14H4z M16 10l5-3v10l-5-3', voice:'M3 10v4 M7 6v12 M11 3v18 M15 7v10 M19 10v4', detect:'M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6z M8 12l3 3 5-6', upload:'M12 16V3 M7 8l5-5 5 5 M4 15v6h16v-6', photo:'M3 3h18v18H3z M3 17l6-6 4 4 3-3 5 5 M15 7h.01', arrow:'M5 12h14 M14 7l5 5-5 5', play:'M9 5l11 7-11 7z', check:'M5 12l4 4L19 6', file:'M6 3h8l4 4v14H6z M14 3v5h4', close:'M6 6l12 12 M18 6L6 18'};
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={name === 'crawl' ? 'M4 3h12l4 4v14H4z M16 3v5h4 M8 12h8 M8 16h5' : paths[name] || paths.file}/></svg>;
}
function Progress({value, label}: {value: number; label: string}) {
  const bounded = Math.max(0, Math.min(100, Math.round(value)));
  return <div className="st-progress" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={bounded}>
    <div className="st-progress-label"><span>{label}</span><strong>{bounded}%</strong></div>
    <div className="st-progress-track"><i style={{width:`${bounded}%`}}/></div>
  </div>;
}
function percentage(value?: number|null) {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`;
}
function ProbabilityPair({ai, real, language}: {ai?: number|null; real?: number|null; language: Language}) {
  const aiWidth = Math.max(0, Math.min(100, (ai ?? .5) * 100));
  const L = (value:string) => language === 'zh' ? value : EN[value] || value;
  return <div className="st-probabilities">
    <div><span>{L('AI 概率')}</span><strong>{percentage(ai)}</strong></div>
    <div className="st-probability-track" aria-hidden="true"><i style={{width:`${aiWidth}%`}}/></div>
    <div><span>{L('正常拍摄')}</span><strong>{percentage(real)}</strong></div>
  </div>;
}
function EvidenceWindow({item, language}: {item: NonNullable<DetectionMethod['evidence']>['high'][number]; language: Language}) {
  const frames = language === 'zh' ? (item.start_frame === item.end_frame ? `第 ${item.start_frame} 帧` : `第 ${item.start_frame}–${item.end_frame} 帧`) : (item.start_frame === item.end_frame ? `Frame ${item.start_frame}` : `Frames ${item.start_frame}–${item.end_frame}`);
  const times = item.start_time === item.end_time ? `${item.start_time.toFixed(2)} s` : `${item.start_time.toFixed(2)}–${item.end_time.toFixed(2)} s`;
  return <li><strong>{percentage(item.ai_probability)}</strong><span>{frames} · {times}</span></li>;
}
const methodEnglish: Record<string,{name?:string; principle?:string; area?:string; explanation?:string}> = {
  gend:{principle:'Adapts a pretrained CLIP visual encoder for stronger generalization across datasets and unseen manipulations.',area:'Aligned full-face region',explanation:'These times show the greatest or smallest departure from this model’s training distribution.'},
  npr:{principle:'Examines neighboring-pixel relationships introduced by generative-network upsampling.',area:'Aligned full-face region',explanation:'Nearly identical scores mean this model cannot separate high and low periods in this video.'},
  ucf:{principle:'Separates manipulation-specific features from features shared by different forgery methods.',area:'Aligned full-face region',explanation:'These times show where facial features depart most or least from this model’s training distribution.'},
  recce:{principle:'Uses joint reconstruction and classification learning to capture differences between forged regions and real-face distributions.',area:'Aligned full-face region',explanation:'These times show where reconstruction and classification evidence is strongest or weakest.'},
  f3net:{principle:'Combines frequency-aware decomposition and local frequency statistics to detect facial manipulation traces.',area:'Aligned full-face region',explanation:'These times show where frequency-domain manipulation evidence is strongest or weakest.'},
  temporal_static:{name:'Photo-driven temporal staticness',principle:'Compares sampled frames to identify a nearly static canvas common in single-photo-driven video.',area:'Full frame, especially the background, hair boundary, and areas outside the shoulders',explanation:'High-AI periods have very little change between frames, consistent with a single-photo canvas where only a small region is animated.'},
  truthscan:{principle:'Uses the TruthScan general video machine-learning model as an independent cloud check.',area:'Entire video',explanation:'The API returns one aggregate probability and does not provide verifiable frame-level timestamps.'},
};
function MethodCard({method, index, language}: {method: DetectionMethod; index: number; language: Language}) {
  const L = (value:string) => language === 'zh' ? value : EN[value] || value;
  const english = methodEnglish[method.id] || {};
  return <article className={`st-method-${method.decision || 'pending'}`}>
    <span className="st-method-number">{L('方法')} {String(index + 1).padStart(2,'0')}</span>
    <h3>{language === 'en' ? english.name || method.name : method.name}</h3>
    <p>{language === 'en' ? english.principle || method.principle || L('等待分析。') : method.principle || L('等待分析。')}</p>
    <ProbabilityPair ai={method.ai_probability} real={method.real_probability} language={language}/>
    {method.threshold_text && language === 'zh' && <p className="st-method-confidence">{method.threshold_text}</p>}
    <div className="st-method-result"><span>{L('单项结论')}</span><strong>{localizedText(method.verdict || '等待分析',language)}</strong></div>
    {method.confidence != null && <p className="st-method-confidence">{L('分类置信度')} {percentage(method.confidence)}</p>}
    {method.evidence && <div className="st-method-evidence">
      <p><strong>{L('分析区域')}</strong>{language === 'en' ? english.area || method.evidence.area : method.evidence.area}</p>
      {!!method.evidence.high.length && <><h4>{L('AI 率较高')}</h4><ul>{method.evidence.high.map((item,i)=><EvidenceWindow key={`h${i}`} item={item} language={language}/>)}</ul></>}
      {!!method.evidence.low.length && <><h4>{L('AI 率较低')}</h4><ul>{method.evidence.low.map((item,i)=><EvidenceWindow key={`l${i}`} item={item} language={language}/>)}</ul></>}
      <p>{language === 'en' ? english.explanation || method.evidence.explanation : method.evidence.explanation}</p>
      {method.paper && <a href={method.paper} target="_blank" rel="noreferrer">{L('查看方法来源')}</a>}
    </div>}
  </article>;
}
function Upload({kind, value, onChange, language, audioLabel, allowVideo = false}: {kind: 'photo'|'voice'|'video'|'media'; value: Media|null; onChange: (v: Media|null)=>void; language: Language; audioLabel?: string; allowVideo?: boolean}) {
  const L = (value:string) => language === 'zh' ? value : EN[value] || value;
  const voiceLabel = audioLabel || L('上传参考语音');
  const ref = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState('');
  const accept = kind === 'photo' ? 'image/jpeg,image/png,image/webp' : kind === 'voice' ? (allowVideo ? 'audio/*,video/*' : 'audio/*') : kind === 'media' ? 'image/jpeg,image/png,image/webp,video/*' : 'video/*';
  function pick(file?: File) {
    if(!file) return;
    const allowed = kind === 'media' ? file.type.startsWith('image/') || file.type.startsWith('video/') : kind === 'voice' ? file.type.startsWith('audio/') || (allowVideo && file.type.startsWith('video/')) : file.type.startsWith(kind === 'photo' ? 'image/' : 'video/');
    if(!allowed) { setError(L('请选择正确类型的文件。')); return; }
    if(file.size > 500 * 1024 * 1024) { setError(L('文件需小于 500 MB。')); return; }
    setError(''); onChange({name:file.name, url:URL.createObjectURL(file),file,kind:file.type.split('/')[0] as Media['kind']});
  }
  return <div className="st-upload-wrap">
    <input ref={ref} type="file" accept={accept} aria-label={L(kind === 'photo' ? '上传人像照片' : kind === 'voice' ? voiceLabel : kind === 'media' ? '上传检测图片或视频' : '上传检测视频')} onChange={e=>pick(e.target.files?.[0])} />
    <div className={`st-upload ${drag ? 'st-drag' : ''} ${value ? 'st-filled' : ''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);pick(e.dataTransfer.files[0])}}>
      {value ? <>
        {kind === 'photo' || (kind === 'media' && value.kind === 'image') ? <img className={`st-photo ${kind === 'photo' ? 'st-portrait' : ''}`} src={value.url} alt={L('已选图片')}/> : kind === 'voice' && value.kind !== 'video' ? <audio controls src={value.url}/> : <video controls src={value.url}/>} 
        <div className="st-file-row"><span title={value.name}>{value.name}</span><button type="button" onClick={()=>ref.current?.click()}>{L('替换')}</button><button type="button" aria-label={L('移除文件')} onClick={()=>onChange(null)}><Icon name="close" size={16}/></button></div>
      </> : <button className="st-upload-button" type="button" onClick={()=>ref.current?.click()}>
        <span className="st-upload-icon"><Icon name={kind === 'photo' ? 'photo' : 'upload'}/></span>
        <strong>{L(kind === 'photo' ? '上传人像照片' : kind === 'voice' ? voiceLabel : kind === 'media' ? '上传需要检测的图片或视频' : '上传需要检测的视频')}</strong>
        <span>{L('点击选择，或拖放到这里')}</span>
        <small>{L(kind === 'photo' ? 'JPG、PNG、WebP · 清晰正脸' : kind === 'voice' ? (allowVideo ? 'WAV、MP3、MP4、MOV 等 · 提取单人清晰语音' : 'WAV、MP3 等 · 单人清晰语音') : kind === 'media' ? 'JPG、PNG、WebP、MP4、MOV 等 · 最大 500 MB' : 'MP4、MOV、WebM 等 · 最大 500 MB')}</small>
      </button>}
    </div>{error && <p className="st-error" role="alert">{error}</p>}
  </div>;
}
export default function Studio({ generatedVideo: initialVideo = null, generatedVoice: initialVoice = null }: StudioProps) {
  const [language,setLanguage] = useState<Language>('zh');
  const L = (value:string) => language === 'zh' ? value : EN[value] || value;
  const [generatedVideo,setGeneratedVideo] = useState<Media|null>(initialVideo);
  const [generatedVoice,setGeneratedVoice] = useState<Media|null>(initialVoice);
  const [service,setService] = useState<api.Health|null>(null);
  const [busy,setBusy] = useState(false);
  const [serviceError,setServiceError] = useState('正在检查本地服务');
  const [mode, setMode] = useState<StudioMode>('crawl');
  const [photo,setPhoto] = useMedia();
  const [voice,setVoice] = useMedia();
  const [drivingVoice,setDrivingVoice] = useMedia();
  const [clip,setClip] = useMedia();
  const [analysis,setAnalysis] = useState<{input: Media; report: api.DetectionReport}|null>(null);
  const report = analysis?.input === clip ? analysis.report : null;
  const [text,setText] = useState('');
  const [notice,setNotice] = useState('');
  const [progress,setProgress] = useState(0);
  const [videoModel,setVideoModel] = useState<VideoModel>('sadtalker');
  const [useTruthScan,setUseTruthScan] = useState(false);
  useEffect(()=>{const requested=new URLSearchParams(location.search).get('lang');const saved=localStorage.getItem('studio-language');if(requested==='en'||(requested!=='zh'&&saved==='en'))setLanguage('en')},[]);
  useEffect(()=>{document.documentElement.lang=language==='zh'?'zh-CN':'en';localStorage.setItem('studio-language',language)},[language]);
  useEffect(()=>{
    let alive = true;
    const check = ()=>api.health().then(result=>{if(alive){setService(result);setServiceError('')}}).catch((error: Error)=>{if(alive){setService(null);setServiceError(error.message)}});
    void check();
    const timer = setInterval(check,15000);
    return()=>{alive=false;clearInterval(timer)};
  },[]);
  useEffect(()=>{const sync=()=>{const hash=location.hash.slice(1);setMode(hash==='video'||hash==='detect'||hash==='voice' ? hash : 'crawl');setNotice('')};sync();window.addEventListener('hashchange',sync);return()=>window.removeEventListener('hashchange',sync)},[]);
  const valid = mode === 'detect' ? !!clip : mode === 'voice' ? !!voice && !!text.trim() : !!photo && !!drivingVoice;
  const activeCapability = mode === 'crawl' ? undefined : mode === 'video' ? service?.capabilities.video.models?.[videoModel] || service?.capabilities.video : service?.capabilities[mode];
  const ready = activeCapability?.ready === true;
  const unavailable = localizedText(service ? activeCapability?.reason || L('所选模型尚未就绪') : serviceError,language);
  async function submit() {
    if (mode === 'crawl') return;
    if (!valid || !ready || busy) return;
    const kind = mode;
    const detectionInput = clip;
    if (kind === 'detect') setAnalysis(null);
    setBusy(true);
    setProgress(0);
    setNotice(L('正在将素材保存到本地服务'));
    const updateProgress = (message: string, value: number) => { setNotice(localizedText(message,language)); setProgress(value); };
    try {
      const payload: Record<string,string> = {kind};
      if(kind === 'detect') payload.media_id = await api.upload(clip!);
      else {
        payload.audio_id = await api.upload(kind === 'voice' ? voice! : drivingVoice!);
        if(kind === 'voice') payload.text = text;
        else {
          payload.image_id = await api.upload(photo!);
          payload.model = videoModel;
        }
      }
      if(kind === 'detect') {
        payload.use_truthscan = String(useTruthScan && service?.capabilities.detect.cloud?.truthscan?.ready === true);
        const result = await api.analyze(payload,updateProgress);
        setAnalysis({input:detectionInput!, report:result});
      } else {
        const result = await api.generate(payload,updateProgress);
        if(kind === 'voice') setGeneratedVoice(result);
        else setGeneratedVideo(result);
      }
      setNotice(L('已完成'));
    } catch(error) {
      setNotice(error instanceof Error ? localizedText(error.message,language) : L('处理失败，请重试'));
    } finally { setBusy(false); }
  }
  function useGeneratedVoice() {
    if (!generatedVoice) return;
    setDrivingVoice(generatedVoice);
    setNotice('');
    setMode('video');
    location.hash = 'video';
  }
  function detectGeneratedVideo() {
    if (!generatedVideo) return;
    setClip(generatedVideo);
    setNotice('');
    setMode('detect');
    location.hash = 'detect';
  }
  function useCollectedMedia(media:Media,next:Mode) {
    if(next==='voice') setVoice(media);
    else if(next==='video') setPhoto(media);
    else {setClip(media);setAnalysis(null)}
    setMode(next);
    location.hash=next;
  }
  return <div className="st-app">
    <aside className="st-sidebar">
      <a href="/studio" className="st-brand"><span className="st-logo"><Icon name="voice" size={21}/></span><span>{L('AI 媒体实验室')}</span></a>
      <div className="st-nav-label">{L('工作区')}</div>
      <nav aria-label={L('工作区')}>{(['crawl','voice','video','detect'] as StudioMode[]).map(m=><a key={m} href={`#${m}`} className={mode === m ? 'st-active' : ''} aria-current={mode === m ? 'page' : undefined}><Icon name={m}/><span>{L(titles[m])}</span>{mode===m && <span className="st-nav-dot"/>}</a>)}</nav>
      <div className="st-sidebar-bottom"><div className="st-device"><span className="st-device-dot"/>{L('本地工作区')}</div><p>RTX 5070 Ti · 12 GB</p><span className="st-small">{L('素材在此设备处理')}</span></div>
    </aside>
    <div className="st-body">
      <header className="st-top"><span>{L('工作区')} <span className="st-slash">/</span> <strong>{L(titles[mode])}</strong></span><div className="st-top-actions"><label className="st-language"><span>{language === 'zh' ? '语言' : 'Language'}</span><select value={language} onChange={event=>setLanguage(event.target.value as Language)} aria-label={language === 'zh' ? '选择语言' : 'Select language'}><option value="zh">中文</option><option value="en">English</option></select></label><span className="st-version">{L(mode === 'crawl' ? 'Facebook 采集' : busy ? '任务处理中' : service ? ready ? mode === 'video' && videoModel === 'tokenhub_humanactor' ? 'TokenHub 已就绪' : '本地模型已就绪' : '服务已连接 · 模型待配置' : '本地服务未连接')}</span></div></header>
      <main className="st-main">
        <div className="st-heading"><div className="st-eyebrow">{mode==='crawl' ? 'COLLECT' : mode==='detect' ? 'ANALYZE' : 'CREATE'}</div><h1>{L(titles[mode])}</h1><p>{L(mode === 'crawl' ? '采集可见文字、图片和视频，选好素材后带入生成或分析。' : mode === 'video' ? '将克隆后的语音与人像照片合成为视频。' : mode === 'voice' ? '提供参考声音，用相同音色朗读新的文字。' : '上传图片或视频，查看各方法的逐帧判断与汇总结论。')}</p></div>
        <div hidden={mode!=='crawl'}><CrawlPanel language={language} disabled={busy} onUse={useCollectedMedia}/></div>
        {mode === 'crawl' ? null : mode !== 'detect' ? <div className="st-work-grid">
          <section className="st-input-card" aria-label={L('生成输入')}>
            <div className="st-section-head"><h2>{L('准备素材')}</h2><span>{L(mode === 'video' && videoModel === 'tokenhub_humanactor' ? '使用腾讯云生成' : '仅在本地使用')}</span></div>
            <div className={mode==='video' ? 'st-input-media' : ''}>
              {mode==='video' && <div><label className="st-label">{L('人像照片')}</label><Upload kind="photo" value={photo} onChange={setPhoto} language={language}/></div>}
              <div><label className="st-label">{L(mode === 'video' ? '驱动语音' : '参考音频或视频')}</label><Upload key={mode} kind="voice" value={mode === 'video' ? drivingVoice : voice} onChange={mode === 'video' ? setDrivingVoice : setVoice} language={language} audioLabel={L(mode === 'video' ? '上传驱动语音' : '上传参考音频或视频')} allowVideo={mode === 'voice'}/></div>
            </div>
            {mode === 'video' && <p className="st-input-note">{L('原图直接交给模型，不额外替换背景。')} {L(VIDEO_NOTES[videoModel])}</p>}
            {mode === 'video' && <fieldset className="st-model-picker"><legend>{L('人像模型')}</legend>{VIDEO_OPTIONS.map(option=><label key={option.id} className={videoModel===option.id ? 'st-model-active' : ''}><input type="radio" name="video-model" value={option.id} checked={videoModel===option.id} onChange={()=>setVideoModel(option.id)}/><span><strong>{option.name}</strong><small>{L(option.detail)}</small></span></label>)}</fieldset>}
            {mode === 'voice' && <><div className="st-text-label"><label className="st-label" htmlFor="speak-text">{L('需要说出的文字')}</label><span>{text.length} / 500</span></div>
            <textarea id="speak-text" maxLength={500} value={text} onChange={e=>setText(e.target.value)} placeholder={L('在这里输入希望人物说出的内容……')}/></>}
            <p className="st-input-note">{L(mode === 'video' && videoModel === 'tokenhub_humanactor' ? '照片与驱动语音会提交至腾讯云生成；语音的 COS 临时文件会在任务结束后删除。' : '请使用已获授权的照片与声音。生成内容仅用于授权演示与检测研究。')}</p>
            {busy && <Progress value={progress} label={notice || L('处理中')}/>} 
            <button className="st-primary" disabled={!valid || !ready || busy} onClick={submit}><Icon name={mode}/>{busy ? `${L('处理中')}…` : L(mode==='video' ? '生成视频' : '生成语音')}<Icon name="arrow" size={18}/></button>
            {!ready && <p className="st-input-note" role="status">{unavailable}</p>}
            {notice && !busy && <p className="st-notice" role="status">{notice}</p>}
          </section>
          <section className="st-result-card" aria-label={L('生成结果')}><div className="st-section-head"><h2>{L(mode==='video' ? '视频预览' : '语音预览')}</h2><span className="st-pill">{L((mode === 'video' ? generatedVideo : generatedVoice) ? '已生成' : '等待生成')}</span></div>
            {mode === 'video' && generatedVideo ? <video className="st-generated-video" controls src={generatedVideo.url} aria-label={L('生成的视频')}/> : mode === 'voice' && generatedVoice ? <audio className="st-generated-audio" controls src={generatedVoice.url} aria-label={L('克隆后的语音')}/> : <div className={`st-preview-empty ${mode==='voice' ? 'st-audio-empty' : ''}`}>
              <span className="st-empty-symbol"><Icon name={mode==='video' ? 'play' : 'voice'} size={32}/></span>
              <h3>{L(mode==='video' ? '让你的照片开口说话' : '听见你的文字')}</h3><p>{L(mode==='video' ? '生成的视频将在这里显示' : '生成后可在这里试听与下载')}</p>
              {mode==='voice' && <div className="st-wave" aria-hidden="true">{[12,23,17,37,26,48,30,20,38,54,34,22,45,32,19,37,27,15,23,12].map((h,i)=><i key={i} style={{height:h}}/>)}</div>}
            </div>}
            {mode === 'video' && <button className="st-primary st-send-detect" disabled={!generatedVideo} onClick={detectGeneratedVideo} aria-describedby="st-transfer-note"><Icon name="detect" size={19}/>{L('检测这个视频')}<Icon name="arrow" size={18}/></button>}
            {mode === 'voice' && <button className="st-primary st-send-detect" disabled={!generatedVoice} onClick={useGeneratedVoice} aria-describedby="st-transfer-note"><Icon name="video" size={19}/>{L('用这段语音生成人像视频')}<Icon name="arrow" size={18}/></button>}
            <div className="st-result-footer" id="st-transfer-note"><Icon name="check" size={16}/><span>{L(mode==='video' ? '生成完成后，直接带入检测，无需下载或重新上传' : '克隆完成后，直接带入人像视频，无需下载或重新上传')}</span></div>
          </section>
        </div> : <div className="st-detect-layout">
          <section className="st-detect-input"><Upload kind="media" value={clip} onChange={setClip} language={language}/>{busy && <Progress value={progress} label={notice || '处理中'}/>}<div className="st-detect-action">{service?.capabilities.detect.cloud?.truthscan?.ready && clip?.kind === 'video' ? <label className="st-cloud-check"><input type="checkbox" checked={useTruthScan} onChange={event=>setUseTruthScan(event.target.checked)}/><span>{L('使用 TruthScan 免费云端复核')}<small>{L('视频会上传；每月免费 30 秒')}</small></span></label> : <span/>}<button className="st-primary" disabled={!valid || !ready || busy} onClick={submit}><Icon name="detect" size={19}/>{busy ? `${L('处理中')}…` : L('开始检测')}<Icon name="arrow" size={18}/></button></div>{!ready && <p className="st-input-note" role="status">{unavailable}</p>}{notice && !busy && <p className="st-notice" role="status">{notice}</p>}</section>
          <section className="st-detection-results"><div className="st-section-head"><h2>{L('检测结果')}</h2><span className="st-pill">{L(report ? '分析完成' : '尚未分析')}</span></div><div className="st-verdict"><span className="st-verdict-icon"><Icon name="detect" size={26}/></span><div className="st-verdict-copy"><h3>{report ? localizedText(report.verdict,language) : L('等待媒体检测')}</h3><p>{report ? localizedText(report.reason,language) : L('这里将汇总全部可用检测方法。')}</p>{report && <ProbabilityPair ai={report.ai_probability} real={report.real_probability} language={language}/>}</div></div>
            {report && <div className="st-vote-summary"><div><strong>{report.summary.passed}</strong><span>{L('方法通过')}</span></div><div><strong>{report.summary.failed}</strong><span>{L('方法未通过')}</span></div><div><strong>{report.summary.uncertain}</strong><span>{L('证据不足')}</span></div><p>{language === 'zh' ? `共 ${report.summary.total} 种方法，${report.summary.completed} 种完成判断` : `${report.summary.total} methods · ${report.summary.completed} completed`}</p></div>}
            <div className="st-methods">{(report?.methods || [
              {id:'gend',name:'GenD CLIP-L/14',status:'waiting',verdict:'等待分析',score:null},
              {id:'npr',name:'NPR',status:'waiting',verdict:'等待分析',score:null},
              {id:'ucf',name:'UCF',status:'waiting',verdict:'等待分析',score:null},
              {id:'recce',name:'RECCE',status:'waiting',verdict:'等待分析',score:null},
              {id:'f3net',name:'F3-Net',status:'waiting',verdict:'等待分析',score:null},
              {id:'temporal_static',name:L('照片驱动时序静态性'),status:'waiting',verdict:'等待分析',score:null}
            ]).map((method,index)=><MethodCard key={method.id} method={method} index={index} language={language}/>)}</div>
            {report?.supporting_methods?.length ? <><h3 className="st-support-title">{L('辅助取证指标')}</h3><div className="st-support-methods">{report.supporting_methods.map(method=><article key={method.id}><h3>{L(method.name)}</h3><p>{L(method.principle || '')}</p><strong>{localizedText(method.verdict,language)}</strong><details><summary>{L('查看测量值')}</summary>{method.metrics && Object.entries(method.metrics).map(([key,value])=><p key={key}>{L(key)}: {value}</p>)}{method.paper && <a href={method.paper} target="_blank" rel="noreferrer">{L('查看研究来源')}</a>}</details></article>)}</div></> : null}
          </section>
        </div>}
        <footer className="st-footer"><span>{L('本地工作区')}</span><i/> <span>{L(mode === 'crawl' ? 'Facebook 采集' : mode === 'video' && videoModel === 'tokenhub_humanactor' ? 'TokenHub 云端生成' : '本地模型生成')}</span>{mode==='detect' && <><i/><span>{L('检测结果仅供参考')}</span></>}</footer>
      </main>
    </div>
  </div>;
}
