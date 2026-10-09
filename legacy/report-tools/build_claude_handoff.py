"""Collect existing experimental evidence for Claude without running any models."""
from pathlib import Path
import csv
import hashlib
import json
import os
import shutil
import wave
import zipfile
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'handoff' / 'claude_2026-10-08'
DEST.mkdir(parents=True, exist_ok=True)
ALLOWED = {'.json','.csv','.txt','.log','.md','.py','.sh','.ps1','.js','.yaml','.yml','.png','.jpg','.jpeg','.wav','.mp3','.m4a','.mp4','.docx','.pdf','.html'}
inventory = []
excluded = []

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def walk(path):
    for folder, dirs, files in os.walk(path, followlinks=False):
        for n in files:
            p=Path(folder)/n
            try:
                if p.is_symlink():
                    excluded.append({'path':str(p.relative_to(ROOT)), 'reason':'symbolic link'})
                    continue
                p.stat()
            except OSError:
                excluded.append({'path':str(p.relative_to(ROOT)), 'reason':'unreadable link or file'})
                continue
            yield p

def clean_urls(value):
    if isinstance(value,dict):
        return {k:clean_urls(v) for k,v in value.items()}
    if isinstance(value,list):
        return [clean_urls(x) for x in value]
    if isinstance(value,str) and value.startswith(('https://','http://')):
        u=urlsplit(value)
        if u.query and ('facebook.com' in u.netloc or 'fbcdn.net' in u.netloc):
            return urlunsplit((u.scheme,u.netloc,u.path,'',''))
    return value

def collect(source, scope, target_rel=None, sanitise=False):
    if not source.exists():
        excluded.append({'path':str(source.relative_to(ROOT)), 'reason':'not present'})
        return
    rel=source.relative_to(ROOT)
    if source.suffix.lower() not in ALLOWED or source.name.lower() in {'facebook_state.json'}:
        excluded.append({'path':str(rel), 'reason':'model weights or out of scope file type'})
        return
    target=DEST/(target_rel or ('evidence/project/'+rel.as_posix()))
    target.parent.mkdir(parents=True,exist_ok=True)
    original_hash=digest(source)
    transformed=False
    if sanitise and source.suffix=='.json':
        data=json.loads(source.read_text(encoding='utf-8-sig'))
        cleaned=clean_urls(data)
        if cleaned!=data:
            target.write_text(json.dumps(cleaned,ensure_ascii=False,indent=2),encoding='utf-8')
            transformed=True
        else:
            shutil.copyfile(source,target)
    else:
        shutil.copyfile(source,target)
    inventory.append({'scope':scope,'original_path':str(source),'project_relative_path':rel.as_posix(),
        'bundle_path':target.relative_to(DEST).as_posix(),'original_bytes':source.stat().st_size,
        'bundle_bytes':target.stat().st_size,'original_sha256':original_hash,'bundle_sha256':digest(target),
        'transformation':'Facebook URL query strings removed' if transformed else 'none'})

groups=[
 ('benchmark-results/2026-09-23-equal-input','LOCAL_L0_SINGLE_INPUT'),
 ('benchmark-results/2026-09-24-multi-sample-v2','LOCAL_R2_FOURTEEN_INPUTS'),
 ('benchmark-results/2026-09-25-echomimic-v3-repair','LOCAL_V3_REPAIR_ATTEMPTS'),
 ('acceptance/ray','LOCAL_R1_PILOTS_AND_R3_DELIVERABLE'),
]
for rel,scope in groups:
    for path in walk(ROOT/rel):
        file_scope='CLOUD_C1_OUTPUT_ONLY' if path.name=='ray_alice_recommendation_tokenhub_30s.mp4' else scope
        collect(path,file_scope)

for path in walk(ROOT/'ray_hunt_facebook_package/media'):
    collect(path,'MEDIA_COLLECTION_PROVENANCE')
for rel in ['ray_hunt_facebook_package/README.md','ray_hunt_facebook_package/manifest.json',
            'facebook-scam/data/accounts/01_ray_hunt/original_media/original_media_manifest.json',
            'facebook-scam/data/accounts/01_ray_hunt/images/images.json']:
    collect(ROOT/rel,'MEDIA_COLLECTION_PROVENANCE',sanitise=True)
for path in walk(ROOT/'facebook-scam/data/accounts/01_ray_hunt/original_media/images'):
    collect(path,'MEDIA_COLLECTION_PROVENANCE')

local_sources=[
 'local-media/INSTALL-STATUS.md','local-media/README.md','PROJECT.md',
 'local-media/generate.py','local-media/video_profiles.py',
 'local-media/prepare_multi_benchmark.py','local-media/evaluate_benchmark.py',
 'local-media/evaluate_multi_benchmark.py','local-media/merge_v3_visual_results.py',
 'local-media/compile_benchmark_report.py','local-media/patch_echomimic_v3_memory.py',
 'tools/create_experiment_report.py','tools/create_compact_multisample_report.py',
 'archive/legacy-demos/build_ray_methods_report.py','tools/build_claude_handoff.py',
 'output/reports/facebook_voice_portrait_model_report_for_ray.md',
 'output/reports/facebook_voice_portrait_model_report_for_ray.docx',
 'output/multi-sample-report/video-gallery.html',
]
for rel in local_sources:
    scope='MIXED_SOURCE_DOCUMENT_READ_WITH_SCOPE' if rel in {'local-media/README.md','tools/create_experiment_report.py'} else 'LOCAL_SUPPORTING_RECORDS'
    collect(ROOT/rel,scope)
for path in walk(ROOT/'output/report-assets'):
    collect(path,'LOCAL_REPORT_VISUALS')
for rel in ['output/docx/audio-driven-portrait-evaluation-report-zh.docx',
            'output/pdf/audio-driven-portrait-evaluation-report-zh.pdf',
            'output/docx/audio-driven-portrait-multisample-metrics-report-zh.docx',
            'output/pdf/audio-driven-portrait-multisample-metrics-report-zh.pdf']:
    collect(ROOT/rel,'OLDER_REPORT_CONTEXT_NOT_SERVER_PROOF')

for rel in ['TALKING_HEAD_WEBUI_README.md','talking_head_webui_app.py',
            'talking_head_webui_chatterbox_generate.py',
            'archive/legacy-demos/generate_ray_british_disclosed_recommendation_audio.py',
            'generate_chatterbox_sample.py','generate_chatterbox_disclosure_audio.py']:
    collect(ROOT/rel,'SERVER_S1_IMPLEMENTATION_ONLY')
collect(ROOT/'local-media/tokenhub.py','CLOUD_C1_IMPLEMENTATION_ONLY')

# Include only the two relevant acquisition scripts from the historical archive.
archive=ROOT/'local-media/legacy-code-20261008.zip'
if archive.exists():
    with zipfile.ZipFile(archive) as z:
        for member in ['facebook-scam/crawler/download_original_media.js','facebook-scam/crawler/download_facebook_tracks.ps1']:
            if member in z.namelist():
                target=DEST/'evidence/historical_acquisition'/member
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(z.read(member))
                inventory.append({'scope':'HISTORICAL_ACQUISITION_SCRIPT','original_path':str(archive)+'!'+member,
                    'project_relative_path':member,'bundle_path':target.relative_to(DEST).as_posix(),
                    'original_bytes':target.stat().st_size,'bundle_bytes':target.stat().st_size,
                    'original_sha256':digest(target),'bundle_sha256':digest(target),'transformation':'extracted from archive'})

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}

def write_csv(rel,rows,fields=None):
    target=DEST/rel; target.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(dict.fromkeys(k for row in rows for k in row))
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

experiments=[]
for rel,scope in groups:
    for path in sorted(walk(ROOT/rel)):
        if path.name!='performance.json' and not path.name.startswith('final-performance'):
            continue
        data=read_json(path); parent=path.parent
        record={'dataset_scope':scope,'variant':parent.name,
                'case_id':parent.parent.name if scope=='LOCAL_R2_FOURTEEN_INPUTS' else '',
                'model':data.get('model',''),'exit_code':data.get('exit_code',''),
                'status':'success' if data.get('exit_code')==0 else ('failed' if data.get('exit_code') is not None else 'completion recorded without exit_code'),
                'execution_mode':data.get('execution_mode','not recorded'),
                'wall_seconds':data.get('wall_seconds',''),'max_rss_mb':data.get('max_rss_mb',''),
                'peak_gpu_memory_mb':data.get('peak_gpu_memory_mb',''),
                'configuration_json':json.dumps(data.get('configuration',{}),ensure_ascii=False),
                'performance_source':'evidence/project/'+path.relative_to(ROOT).as_posix(),
                'visual_source':'','syncnet_source':''}
        visual=parent/'visual-metrics.json'; sync=parent/'syncnet-metrics.json'
        if visual.exists():
            record['visual_source']='evidence/project/'+visual.relative_to(ROOT).as_posix()
            v=read_json(visual)
            for key in ['identity_mean','identity_p05','identity_min','face_detection_rate','landmark_jitter','geometry_outlier_rate','lip_aperture_range','lip_motion_jitter','lip_width_cv','face_sharpness','black_pixel_ratio']:
                record[key]=v.get(key,'')
        if sync.exists():
            record['syncnet_source']='evidence/project/'+sync.relative_to(ROOT).as_posix()
            s=read_json(sync)
            for key in ['lse_d','lse_c','av_offset_frames']:
                record[key]=s.get(key,'')
        probe=data.get('output',{})
        if not isinstance(probe,dict):
            probe=data.get('probe',{})
        if isinstance(probe,dict):
            record['output_duration_seconds']=probe.get('format',{}).get('duration','')
            for stream in probe.get('streams',[]):
                if stream.get('codec_type')=='video':
                    record['output_width']=stream.get('width',''); record['output_height']=stream.get('height',''); record['output_fps']=stream.get('r_frame_rate','')
        experiments.append(record)
write_csv('tables/local_experiments_all_attempts.csv',experiments)
write_csv('tables/local_ray_pilots_all_variants.csv',[r for r in experiments if r['dataset_scope']=='LOCAL_R1_PILOTS_AND_R3_DELIVERABLE' and r['variant']!='final'])
write_csv('tables/local_v3_repair_attempts.csv',[r for r in experiments if r['dataset_scope']=='LOCAL_V3_REPAIR_ATTEMPTS'])
agg=read_json(ROOT/'benchmark-results/2026-09-24-multi-sample-v2/aggregate-results.json')
write_csv('tables/local_R2_aggregate_only.csv',[{'dataset_scope':'LOCAL_R2_FOURTEEN_INPUTS','model':k,**v} for k,v in agg['models'].items()])
voice=read_json(ROOT/'acceptance/ray/voice_manifest.json')
write_csv('tables/local_R3_voice_chunks.csv',[{'dataset_scope':'LOCAL_R3_SPEECH','sample_rate':voice['sample_rate'],**row} for row in voice['chunks']])

media=[]
for row in inventory:
    path=DEST/row['bundle_path']
    if path.suffix.lower() not in {'.wav','.mp3','.m4a','.mp4','.png','.jpg','.jpeg'}:
        continue
    item={'scope':row['scope'],'bundle_path':row['bundle_path'],'bytes':row['bundle_bytes'],'sha256':row['bundle_sha256']}
    if path.suffix.lower()=='.wav':
        try:
            with wave.open(str(path)) as w:
                item.update(sample_rate=w.getframerate(),channels=w.getnchannels(),duration_seconds=round(w.getnframes()/w.getframerate(),6))
        except (wave.Error,EOFError):
            item['metadata_note']='WAV parser did not read this encoding; use preserved source probe'
    if path.suffix.lower() in {'.png','.jpg','.jpeg'}:
        from PIL import Image
        with Image.open(path) as im:
            item.update(width=im.width,height=im.height)
    media.append(item)
write_csv('tables/media_inventory.csv',media)
write_csv('tables/source_inventory.csv',inventory)
excluded=list({(row['path'],row['reason']):row for row in excluded}.values())
(DEST/'tables/exclusions.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2),encoding='utf-8')

scopes=[
 {'id':'LOCAL_L0_SINGLE_INPUT','environment':'RTX 5070 Ti Laptop about 12 GB VRAM; WSL Ubuntu','inputs':'one prepared portrait and approximately 2.4 second audio','source':'benchmark-results/2026-09-23-equal-input','compare_with':'within this dataset only'},
 {'id':'LOCAL_R1_PILOTS','environment':'local PC WSL','inputs':'same Ray portrait and approximately 4 second audio; all parameter variants retained','source':'acceptance/ray/pilots','compare_with':'within Ray pilot; preserve configuration differences'},
 {'id':'LOCAL_R2_FOURTEEN_INPUTS','environment':'local PC WSL','inputs':'seven portraits x two approximately 2.4 second audio clips; 56 generated model cases','source':'benchmark-results/2026-09-24-multi-sample-v2','compare_with':'within dataset; V3 cold and warm timings separated'},
 {'id':'LOCAL_R3_DELIVERABLE','environment':'local PC WSL','inputs':'long script generated in four speech chunks; continuous SadTalker video rendering','source':'acceptance/ray/final','compare_with':'two saved final video configurations only; speech and video timing are separate'},
 {'id':'LOCAL_V3_REPAIR_ATTEMPTS','environment':'local PC WSL','inputs':'repair variants with different memory configurations, successful and failed attempts','source':'benchmark-results/2026-09-25-echomimic-v3-repair','compare_with':'engineering repair evidence; do not use as independent population benchmark'},
 {'id':'SERVER_S1_IMPLEMENTATION_ONLY','environment':'earlier rented Linux GPU server; verified exact GPU not supplied in reviewed files','inputs':'uploaded portrait, voice reference, text; Chatterbox then SadTalker','source':'historical remote WebUI and scripts','compare_with':'no verified matched quantitative server benchmark currently identified'},
 {'id':'CLOUD_C1_OUTPUT_ONLY','environment':'TokenHub hosted HumanActor API','inputs':'image and driving audio; saved Ray output present','source':'local-media/tokenhub.py and saved MP4','compare_with':'no matched timing, cost or quality dataset supplied'},
 {'id':'REFERENCE_PAPER_REPORTED','environment':'external manuscript reported in older mixed report; original raw data not included','inputs':'HDTF and CelebV HQ; Audio2Head, SadTalker, EchoMimic','source':'older evaluation report and tools/create_experiment_report.py','compare_with':'literature context only; do not classify as local or rented-server measurement'},
]
(DEST/'dataset_scopes.json').write_text(json.dumps(scopes,ensure_ascii=False,indent=2),encoding='utf-8')
write_csv('tables/dataset_scopes.csv',scopes)

readme='''# Claude 交接说明

交接日期：2026-10-08。主题：为 Ray 整理 Facebook 声音及图片获取方法、实际使用模型、部署位置和模型比较。

## 先读这些文件

1. `CLAUDE_START_HERE.md`：可直接复制给 Claude 的任务与约束。
2. `dataset_scopes.json`：实验与来源边界。
3. `tables/local_experiments_all_attempts.csv`：逐次实验，包括失败，不合并条件不同的结果。
4. `tables/local_R2_aggregate_only.csv`：十四组本机实验原有汇总。
5. `tables/source_inventory.csv`：原文件路径、包内路径及原始和打包 SHA256。
6. `evidence/project/output/reports/facebook_voice_portrait_model_report_for_ray.md`：已修订的英文报告和中文摘要。

## 必须分开的来源

- **本地 L0**：2026-09-23 单输入旧基准。
- **本地 R1**：Ray 四秒样片，保留所有配置版本。
- **本地 R2**：七照片乘两声音的十四组输入，四模型，共五十六组结果。
- **本地 R3**：Ray 长语音与约五十一秒成片；语音合成时间、视频生成时间分开。
- **本地 V3 修复**：含失败和成功的工程尝试，不当作独立人群样本。
- **早期服务器 S1**：Chatterbox 加 SadTalker 的远程脚本与说明。未定位到具有可核验实验条件的三模型服务器结果原表。
- **云端 API C1**：TokenHub HumanActor，已保存视频但无同条件质量、完整耗时和费用记录；与早期租用服务器不同。
- **外部论文**：旧中文评估报告含 WACV 2027 匿名稿件所报告的 HDTF/CelebV-HQ 数据。该数据只算文献背景，不能改称本机或服务器实测。原稿与原始数据尚未在本次资料中定位。

## 已确认要点

历史 Ray Facebook 声音包记载 VB-CABLE 加 FFmpeg 录制浏览器播放声音。Facebook 图片下载脚本和 manifest 记载 Playwright 加页面/网络图片下载。Ray 本地实验使用 `ray.png`，但具体对应哪张下载图仍未建立一对一来源关系。头像准备脚本裁剪并缩放，不重绘脸部。

Chatterbox 是语音模型；SadTalker、EchoMimic V1、JoyVASA、EchoMimic V3 Flash 是视频/人像动画模型。Qwen3 1.7B 是文本 LLM，不直接接收 Ray 的声音或照片。不能写成三种 LLM 都直接输入同一声音、照片与文字。

R1 选定 SadTalker full pose 0：64.7 秒、身份均值 0.9561；EchoMimic V1：185.1 秒、0.9524；JoyVASA：22.9 秒、0.8365。身份分数是嵌入余弦相似度，不是准确率百分比。

R2 SadTalker 平均 22.4 秒、0.9195；EchoMimic V1 平均 52.8 秒、0.8867；JoyVASA 平均 21.7 秒、0.8430。V3 两次冷启动约 535 秒，十二次已加载模型约 235 秒；不能把这两种耗时混为十四次统一平均。

R3 自然版视频 51.52 秒，视频阶段约 667.5 秒。生成语音 51.48 秒，语音阶段约 155.3 秒。音频四段拼接与视频一次连续推理是不同处理步骤。

## 使用原始资料

`evidence/project/` 保持原项目相对结构。旧文件中 Windows 或 `/mnt/d/` 绝对路径可能已迁移；优先用 `source_inventory.csv` 找到包内文件，不能因旧路径不可打开而判定实验不存在。

CSV 空白表示缺失或未记载，不能填零。Ray 某些配置没有独立 SyncNet JSON，但 README 有摘要；引用时标注摘要来源，不能声称有逐帧原始同步记录。部分多样本视觉指标在顶层 `visual-results.json`，不要只看单模型目录。

所有可读的相关实验 sidecar、日志、资源 CSV、图片、音频和视频已保留；模型权重、不可访问符号链接、登录状态、无关账号资料没有纳入。Facebook manifest 中的 URL 查询签名已移除，原文件没有修改，清单分别保留原始和打包文件校验值。

本次只整理既有材料，没有重新运行模型或重新采集 Facebook。这是一份交接包，不代表已向某个 Claude 会话发送。
'''
(DEST/'README.md').write_text(readme,encoding='utf-8')
prompt='''# 给 Claude 的交接任务

你接手一个 talking-head 项目的资料整理与报告审查。请先读取本目录 README.md、dataset_scopes.json 和 tables/source_inventory.csv，再读取逐次结果表与原始 sidecar。

用户要求：为 Ray 写英文报告，附中文摘要，回答四点：Facebook 声音通过哪些工具取得；图片如何取得；哪些模型实际使用了声音、图片和文字，以及本机/服务器/在线运行位置；简要比较三个已试用模型。

用户特别强调：本地实验与此前服务器报告的数据必须分开。不要把模型名称相同当作实验条件相同，不要将外部论文数据误认为本地或服务器实测。

工作顺序：
1. 按 dataset_scopes.json 建立本地 L0、R1、R2、R3、V3 修复、早期服务器 S1、云端 API C1、外部论文八类证据。来源不明的项保持待确认。
2. 检查 tables/local_experiments_all_attempts.csv，返回原始 JSON 与日志核实。保留失败和配置版本，不只选最好结果。
3. 核查现有报告每个数字的来源、输入、运行环境、参数和计时范围。修订有误或表述过强之处。
4. 英文报告分别写本地实验、服务器历史、在线 API；本地不同数据组也分表。服务器原报告未明确定位时，请说明这一缺口，不从本地填入服务器数据。
5. 给出 SadTalker、EchoMimic V1、JoyVASA 的同条件本地比较，V3 单列；使用余弦相似度的正确解释。缺少云端匹配指标就不做定量排名。
6. 产出修订英文报告、中文摘要和四句英文 presentation 文案；附事实审查表及仍需用户确认的问题。

起始报告：evidence/project/output/reports/facebook_voice_portrait_model_report_for_ray.md。
旧中文报告与 tools/create_experiment_report.py 含外部论文和本地实验两类内容，仅作独立来源上下文，不能合并统计。

目前没有进行新的模型推理、Facebook 采集或外部发送。当前授权是整理和交接报告资料。不要自动登录账号、上传素材到模型服务或启动付费推理。
'''
(DEST/'CLAUDE_START_HERE.md').write_text(prompt,encoding='utf-8')

issues=[
 {'id':'SERVER_REPORT_NOT_IDENTIFIED','severity':'high','detail':'Exact earlier server report and matching raw server benchmark have not been identified. Retained scripts establish implementation only.'},
 {'id':'SOURCE_PORTRAIT_MAPPING','severity':'medium','detail':'ray.png is not explicitly mapped to one Facebook downloaded image in the reviewed records.'},
 {'id':'CLOUD_MATCHED_EVALUATION_MISSING','severity':'medium','detail':'Saved hosted API output exists without matched timing, cost and quality evidence.'},
 {'id':'REFERENCE_MANUSCRIPT_MISSING','severity':'medium','detail':'Older report cites an external WACV manuscript. Original manuscript and raw reference datasets were not located in this collection.'},
 {'id':'CONFIG_SPECIFIC_SYNC_SIDECARS','severity':'medium','detail':'Some Ray variants have video and README sync summaries but no independent syncnet-metrics.json.'},
 {'id':'DEFAULT_MODEL_HISTORY','severity':'low','detail':'INSTALL-STATUS and README describe changing defaults. Final and pilot configuration files take precedence for results.'},
]
(DEST/'open_questions.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')

# Validate the portable copies and link each derived row to a packaged source.
for row in inventory:
    assert digest(DEST/row['bundle_path'])==row['bundle_sha256'],row['bundle_path']
for row in experiments:
    for key in ['performance_source','visual_source','syncnet_source']:
        if row.get(key): assert (DEST/row[key]).is_file(),row[key]
assert agg['sample_count']==14
assert all(v['attempted']==14 and v['successes']==14 for v in agg['models'].values())
summary={'date':'2026-10-08','packaged_source_files':len(inventory),'media_files':len(media),
    'experiment_performance_records':len(experiments),'failed_attempts':sum(r['status']=='failed' for r in experiments),
    'raw_source_bytes':sum(r['original_bytes'] for r in inventory),'packaged_source_bytes':sum(r['bundle_bytes'] for r in inventory),
    'excluded_records':len(excluded),'source_hashes_verified':True,'new_inference_performed':False,'sent_to_claude':False}
(DEST/'validation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')

zip_path=DEST.with_suffix('.zip')
light_path=DEST.parent/(DEST.name+'_evidence_only.zip')
media_ext={'.wav','.mp3','.m4a','.mp4','.png','.jpg','.jpeg'}
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as full, zipfile.ZipFile(light_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as light:
    for path in sorted(walk(DEST)):
        arc=DEST.name+'/'+path.relative_to(DEST).as_posix()
        full.write(path,arc)
        if path.suffix.lower() not in media_ext:
            light.write(path,arc)
    light.writestr(DEST.name+'/LIGHTWEIGHT_PACKAGE.md',
        '本 ZIP 是轻量证据版，省略独立图片、音频和视频文件。表格、日志、脚本、报告及来源清单完整保留。'
        'source_inventory.csv 中媒体路径在完整版 ZIP 或原项目中可用；轻量版缺少媒体不表示原实验没有输出。'
        '需要观看或听取原始素材时，请使用 claude_2026-10-08.zip。')
for archive_path in [zip_path,light_path]:
    with zipfile.ZipFile(archive_path) as z:
        assert z.testzip() is None
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('FULL_ZIP',zip_path,zip_path.stat().st_size)
print('EVIDENCE_ONLY_ZIP',light_path,light_path.stat().st_size)
