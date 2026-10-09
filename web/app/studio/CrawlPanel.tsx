"use client";

import { useEffect, useRef, useState } from 'react';
import * as crawl from './crawl-api';
import type { Media, Mode } from './api';
import './crawl.css';
import AccountRiskReport from './AccountRiskReport';

type Props = {language:'zh'|'en'; disabled:boolean; onUse:(media:Media,mode:Mode)=>void};
const active = (job:crawl.CrawlJob|null) => !!job && (job.status === 'queued' || job.status === 'running');
const labels:Record<string,string> = {
  queued:'Waiting',running:'Running',done:'Complete',failed:'Failed',cancelled:'Stopped',needs_login:'Login required',
  opening:'Opening Facebook',extracting:'Extracting visible content',downloading:'Saving original media',login:'Log in using the opened browser',
  analyzing:'Assessing visible account evidence',
  image:'Images',video:'Videos',audio:'Audio',text:'Text',downloaded:'Downloaded',link_only:'Link only',duplicate:'Duplicate',
};

export default function CrawlPanel({language,disabled,onUse}:Props) {
  const en = language === 'en';
  const T = (zh:string,english:string) => en ? english : zh;
  const [url,setUrl] = useState('');
  const [scrolls,setScrolls] = useState(8);
  const [download,setDownload] = useState(true);
  const [service,setService] = useState<crawl.CrawlHealth|null>(null);
  const [records,setRecords] = useState<crawl.CrawlJob[]>([]);
  const [job,setJob] = useState<crawl.CrawlJob|null>(null);
  const [error,setError] = useState('');
  const [pending,setPending] = useState(false);
  const [transferring,setTransferring] = useState(false);
  const [tab,setTab] = useState<'text'|'image'|'video'|'audio'>('text');
  const [textLimit,setTextLimit] = useState(50);
  const imported = useRef(new Map<string,Media>());
  const running = active(job);
  const result = job?.kind === 'crawl' ? job.result : undefined;
  useEffect(()=>{
    let alive = true;
    let initial = true;
    const refresh = async () => {
      try {
        const [health,history] = await Promise.all([crawl.health(),crawl.history()]);
        if (!alive) return;
        setService(health); setRecords(history);
        if(initial) {
          initial=false;
          const selected=history.find(item=>active(item)) || history.find(item=>item.kind==='crawl' && item.status==='done');
          if(selected) {
            const full=await crawl.status(selected.id);
            if(alive) setJob(previous=>previous || full);
          }
        } else setJob(previous=>previous || history.find(item=>active(item)) || null);
      } catch { if(alive) setService(null); }
    };
    void refresh();
    const timer = setInterval(refresh,10000);
    return()=>{alive=false;clearInterval(timer)};
  },[]);
  useEffect(()=>{
    if (!job || !active(job)) return;
    let alive = true;
    const id = job.id;
    const poll = async () => {
      try {
        const current = await crawl.status(id);
        if (!alive) return;
        setJob(current);
        if (!active(current)) setRecords(await crawl.history());
      } catch(error) { if(alive) setError(error instanceof Error ? error.message : '无法查询任务'); }
    };
    const timer = setInterval(poll,1500);
    return()=>{alive=false;clearInterval(timer)};
  },[job?.id,job?.status]);
  async function submit(login = false) {
    setPending(true);setError('');setTextLimit(50);
    try { setJob(login ? await crawl.login() : await crawl.start({url,max_scrolls:scrolls,download_media:download})); }
    catch(error) { setError(error instanceof Error ? error.message : '提交失败'); }
    finally { setPending(false); }
  }
  async function openRecord(id:string) {
    setError('');
    try {setJob(await crawl.status(id));setTextLimit(50)} catch(error) {setError(error instanceof Error ? error.message : '读取失败')}
  }
  async function analyzeAccount() {
    if (!job || job.kind!=='crawl' || job.status!=='done') return;
    const id = job.id;
    setPending(true);setError('');
    try {
      const analysis = await crawl.analyze(id);
      setJob(current=>current?.id===id && current.result ? {...current,result:{...current.result,analysis}} : current);
    } catch(error) { setError(error instanceof Error ? error.message : '账号分析失败'); }
    finally {setPending(false)}
  }
  async function use(asset:crawl.CrawlMedia,mode:Mode) {
    setError('');setTransferring(true);
    try {
      let media = imported.current.get(asset.url!);
      if (!media) {media = await crawl.importMedia(asset);imported.current.set(asset.url!,media)}
      onUse(media,mode);
    } catch(error) {setError(error instanceof Error ? error.message : '素材交接失败')}
    finally {setTransferring(false)}
  }
  const media = result?.media.filter(asset=>asset.kind===tab && asset.status!=='duplicate') || [];
  return <div className="st-crawl-layout">
    <section className="st-input-card">
      <div className="st-section-head"><h2>{T('采集设置','Collection settings')}</h2><span>{T('Facebook','Facebook')}</span></div>
      <p className="st-crawl-intro">{T('粘贴主页、帖子或视频链接，采集当前可见的文字和媒体。','Paste a profile, post, or video link to collect visible text and media.')}</p>
      <label className="st-label" htmlFor="crawl-url">{T('Facebook 链接','Facebook URL')}</label>
      <input id="crawl-url" className="st-crawl-input" type="url" value={url} placeholder="https://www.facebook.com/…" onChange={event=>setUrl(event.target.value)} disabled={running}/>
      <div className="st-crawl-settings"><label htmlFor="crawl-scrolls">{T('采集范围','Collection range')}</label><select id="crawl-scrolls" value={scrolls} disabled={running} onChange={event=>setScrolls(Number(event.target.value))}><option value={4}>{T('少量 · 4 次滚动','Small · 4 scrolls')}</option><option value={8}>{T('标准 · 8 次滚动','Standard · 8 scrolls')}</option><option value={20}>{T('更多 · 20 次滚动','More · 20 scrolls')}</option></select></div>
      <label className="st-crawl-check"><input type="checkbox" checked={download} disabled={running} onChange={event=>setDownload(event.target.checked)}/>{T('下载可获取的图片、视频与音频','Download available images, video, and audio')}</label>
      <div className="st-crawl-session"><span>{service?.ready ? T('采集服务已连接','Collector connected') : T('采集服务未连接','Collector unavailable')}</span><button className="st-crawl-secondary" type="button" disabled={!service?.ready || running || pending} onClick={()=>void submit(true)}>{T('打开 Facebook 登录窗口','Open Facebook login')}</button><small>{T('首次使用或会话失效时，在打开的浏览器中登录。','Log in using the opened browser on first use or when the session expires.')}</small></div>
      <button className="st-primary" disabled={!service?.ready || !url.trim() || running || pending} onClick={()=>void submit()}>{T('开始采集','Start collection')}</button>
      {!service && <p className="st-input-note">{T('运行 scripts/start-collector.ps1 启动采集服务。','Run scripts/start-collector.ps1 to start the collector.')}</p>}
      {job && <div className="st-crawl-task" role="status"><strong>{en ? labels[job.stage] || labels[job.status] || job.stage : job.message}</strong>{job.kind==='crawl' && <progress value={job.progress} max={100} aria-label={T('采集进度','Collection progress')}/>}<span>{Object.entries(job.counts).map(([key,value])=>`${en ? labels[key] || key : ({text:'文字',media:'媒体',image:'图片',video:'视频',audio:'音频',scrolls:'滚动'} as Record<string,string>)[key] || key} ${value}`).join(' · ')}</span>{job.elapsed_seconds != null && <small>{T('耗时','Elapsed')} {job.elapsed_seconds} s</small>}{running && <button className="st-crawl-secondary" onClick={()=>void crawl.cancel(job.id).catch(error=>setError(error.message))}>{T('停止任务','Stop task')}</button>}</div>}
      {error && <p className="st-error" role="alert">{error}</p>}
      <div className="st-crawl-history"><h3>{T('采集历史','Collection history')}</h3>{records.filter(item=>item.kind==='crawl').slice(0,10).map(item=><button key={item.id} disabled={running || pending} className={item.id===job?.id ? 'st-history-active' : ''} onClick={()=>void openRecord(item.id)}><span>{item.source_url.replace(/^https:\/\/(www\.)?facebook.com\//,'')}</span><small>{new Date(item.created_at).toLocaleString(en ? 'en-NZ' : 'zh-CN')} · {en ? labels[item.status] : ({done:'完成',failed:'失败',cancelled:'已停止',needs_login:'需要登录',running:'采集中',queued:'等待'} as Record<string,string>)[item.status]}</small></button>)}{!records.some(item=>item.kind==='crawl') && <p>{T('还没有采集记录','No collections yet')}</p>}</div>
    </section>
    <section className="st-result-card">
      <div className="st-section-head"><h2>{T('采集结果','Collection result')}</h2>{job?.status==='done' && job.kind==='crawl' && <a className="st-crawl-secondary" href={`/crawl/jobs/${job.id}/export?language=${language}`}>{T('导出 ZIP','Export ZIP')}</a>}</div>
      {result ? <>
        <h3 className="st-crawl-result-title">{result.title}</h3><a className="st-crawl-source" href={result.source_url} target="_blank" rel="noreferrer">{T('查看原页面','Open source page')}</a>
        {result.warnings.map(warning=><p key={warning} className="st-input-note">{warning}</p>)}
        <div className="st-crawl-tabs" role="tablist" aria-label={T('采集内容类型','Collected content types')}>{(['text','image','video','audio'] as const).map(kind=><button key={kind} role="tab" id={`crawl-tab-${kind}`} aria-controls="crawl-content" aria-selected={kind===tab} onClick={()=>setTab(kind)}>{en ? labels[kind] : ({text:'文字',image:'图片',video:'视频',audio:'音频'})[kind]} <small>{kind==='text' ? result.text.length : result.media.filter(asset=>asset.kind===kind && asset.status!=='duplicate').length}</small></button>)}</div>
        <div id="crawl-content" role="tabpanel" aria-labelledby={`crawl-tab-${tab}`}>
          {tab==='text' ? <div className="st-crawl-text">{result.text.slice(0,textLimit).map((item,index)=><article key={index}><p>{item.text}</p><a href={item.source_url} target="_blank" rel="noreferrer">{T('来源','Source')}</a></article>)}{result.text.length>textLimit && <button className="st-crawl-secondary" onClick={()=>setTextLimit(value=>value+50)}>{T('显示更多','Show more')}</button>}{!result.text.length && <p className="st-input-note">{T('没有提取到文字','No text extracted')}</p>}</div> : <div className="st-crawl-media">{media.map((asset,index)=><article key={asset.id || `${asset.source_url}-${index}`}>
            {asset.status==='downloaded' && asset.url ? asset.kind==='image' ? <img src={asset.url} alt={asset.name} loading="lazy"/> : asset.kind==='video' ? <video controls preload="metadata" src={asset.url}/> : <audio controls preload="metadata" src={asset.url}/> : <div className="st-crawl-link-placeholder">{T('仅来源链接或下载失败','Source link only or download failed')}</div>}
            <p title={asset.name}>{asset.name}</p><small>{en ? labels[asset.status] : ({downloaded:'已下载',link_only:'仅链接',failed:'下载失败',duplicate:'重复'})[asset.status]}{asset.size ? ` · ${(asset.size/1024/1024).toFixed(1)} MB` : ''}</small>
            {asset.reason && <small>{en ? 'Original file unavailable' : asset.reason}</small>}
            <a href={asset.source_url} target="_blank" rel="noreferrer">{T('查看来源','View source')}</a>
            {asset.status==='downloaded' && <div className="st-crawl-use">{asset.kind==='image' ? <button disabled={disabled || transferring} onClick={()=>void use(asset,'video')}>{T('用作人像照片','Use as portrait')}</button> : <button disabled={disabled || transferring} onClick={()=>void use(asset,'voice')}>{T('用作参考声音','Use as voice reference')}</button>}{asset.kind!=='audio' && <button disabled={disabled || transferring} onClick={()=>void use(asset,'detect')}>{T('分析此素材','Analyze media')}</button>}</div>}
          </article>)}{!media.length && <p className="st-input-note">{T('没有采集到此类素材','No media of this type')}</p>}</div>}
        </div>
      </> : <div className="st-preview-empty"><h3>{T('从一个 Facebook 链接开始','Start with a Facebook link')}</h3><p>{T('采集后可预览、导出并选择素材用于生成或分析。','Preview, export, and send collected media to creation or analysis.')}</p></div>}
    </section>
    <AccountRiskReport report={result?.analysis} language={language} canAnalyze={!!result && job?.status==='done' && !running && !!service?.ready} pending={pending} onAnalyze={()=>void analyzeAccount()}/>
  </div>;
}
