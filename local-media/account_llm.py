"""Local-only bridge from Windows collection to the shared Ubuntu GPU service."""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import account_story


class ModelError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        raise HTTPError(request.full_url,code,'本地模型服务不允许重定向',headers,file)


opener=build_opener(NoRedirect())


def prose_draft(text):
    """Keep evidence, but remove UI labels a small model otherwise parrots."""
    ids=list(dict.fromkeys(re.findall(r'\bE[1-9]\d*\b',text)))
    text=re.sub(r'\s*\[E[1-9]\d*[^\]]*\]','',text)
    for label in ('可见原文：','可能的损失或暴露：','防范动作：','具体防范：',
                  'Visible excerpt:','Possible loss or exposure:','What to do:','Concrete safeguards:'):
        text=text.replace(label,'')
    text=re.sub(r'。{2,}','。',text).strip()
    return text+(' ['+', '.join(ids)+']' if ids else '')


def call(path, payload=None, timeout=3):
    base=os.environ.get('LOCAL_ACCOUNT_API','http://127.0.0.1:8002').rstrip('/')
    parsed=urlsplit(base)
    if parsed.scheme!='http' or parsed.hostname not in {'localhost','127.0.0.1','::1'} or parsed.username or parsed.password:
        raise ModelError('账号模型仅允许本机回环 HTTP 服务，不向外部地址发送资料')
    request=Request(base+path,data=json.dumps(payload,ensure_ascii=False).encode('utf-8') if payload is not None else None,
                    headers={'Content-Type':'application/json'})
    try:
        with opener.open(request,timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            detail=json.loads(error.read()).get('detail','本地模型请求失败')
        except (ValueError,UnicodeError):
            detail='本地模型请求失败'
        raise ModelError(str(detail)) from error
    except (URLError,TimeoutError,ValueError) as error:
        raise ModelError('无法连接本地账号 LLM 或推理超时；请确认 Ubuntu 服务已启动') from error


def status():
    try:
        return call('/health').get('account_analysis',{'ready':False,'reason':'本地服务尚未部署账号 LLM 接口'})
    except ModelError as error:
        return {'ready':False,'reason':str(error)}


def rewrite(report):
    draft,draft_en=[],[]
    # The fixed type paragraph is retained outside the model; do not ask a small
    # model to reclassify it or waste its context repeating the same statement.
    for paragraph,english in zip(report['narrative'][1:],report['narrative_en'][1:]):
        if sum(map(len,draft))+len(paragraph)+(sum(map(len,draft_en))+len(english))/3>3600:
            break
        draft.append(prose_draft(paragraph))
        draft_en.append(prose_draft(english))
    refs=sorted(set(re.findall(r'\bE[1-9]\d*\b','\n'.join(draft))),key=lambda value:int(value[1:]))
    if not draft or not refs:
        raise ModelError('现有材料没有可引用的具体资料，不能生成本地模型正文')
    response=call('/account-analysis',{'draft':draft,'draft_en':draft_en,'evidence_ids':refs,
        'facts':[item for item in report.get('source_facts',[]) if item['id'] in refs]},timeout=130)
    if not isinstance(response,dict) or not isinstance(response.get('model'),str) or not isinstance(response.get('elapsed_seconds'),(int,float)):
        raise ModelError('本地服务没有返回有效的模型来源信息；原分析保持不变')
    paragraphs=response.get('paragraphs',{})
    material='\n'.join(draft)
    allowed_emails=set(account_story.EMAIL.findall(material))
    output={}
    for language,first in [('zh',report['narrative'][0]),('en',report['narrative_en'][0])]:
        items=paragraphs.get(language)
        if not isinstance(items,list) or not 1<=len(items)<=3:
            raise ModelError('本地模型没有返回完整的中英文正文；原分析保持不变')
        prose=[first]
        for item in items:
            if not isinstance(item,dict):
                raise ModelError('本地模型正文格式无效；原分析保持不变')
            text=str(item.get('text','')).strip()
            ids=item.get('evidence_ids',[])
            if not text or '\ufffd' in text or len(text)>1800 or not isinstance(ids,list) or not ids or any(not isinstance(value,str) or value not in refs for value in ids):
                raise ModelError('本地模型正文或证据编号无效；原分析保持不变')
            if re.search(r'(?:^|\n)\s*(?:攻击路径|诈骗话术|操纵策略|attack steps|scam script)\s*[:：]',text,re.I):
                raise ModelError('模型输出了禁止的攻击或诈骗格式，已拒绝该输出')
            if set(account_story.EMAIL.findall(text))-allowed_emails:
                raise ModelError('模型添加了证据中不存在的邮箱，已拒绝该输出')
            if set(re.findall(r'\bE[1-9]\d*\b',text))-set(refs):
                raise ModelError('模型添加了证据中不存在的来源编号，已拒绝该输出')
            if any(value not in material for value in re.findall(r'\d[\d-]{4,}',text)):
                raise ModelError('模型添加了证据中不存在的日期或编号，已拒绝该输出')
            for role,zh,en in account_story.KIN:
                pattern=zh+r'|\b(?:'+en+r')\b'
                if re.search(pattern,text,re.I) and not re.search(pattern,material,re.I):
                    raise ModelError('模型添加了证据中不存在的亲属，已拒绝该输出')
            for value,pattern in account_story.INTERESTS+account_story.TRAITS+account_story.VOICES:
                translated=account_story.WORDS.get(value,value)
                if re.search(re.escape(value)+r'|\b'+re.escape(translated)+r'\b',text,re.I) and value not in material and not re.search(pattern,material,re.I):
                    raise ModelError('模型添加了证据中不存在的个人描述，已拒绝该输出')
            if language=='en':
                quotes=re.findall(r'“([^”]*)”|"([^"]*)"',text)
                for first_quote,second_quote in quotes:
                    value=first_quote or second_quote
                    if re.search(r'[\u4e00-\u9fff]',value) and value not in '\n'.join(draft_en):
                        raise ModelError('英文正文中出现无法核对的中文引用，已拒绝该输出')
                untranslated=re.sub(r'“[^”]*”|"[^"]*"','',text)
                if re.search(r'[\u4e00-\u9fff]',untranslated):
                    raise ModelError('英文正文未完整翻译，已拒绝该输出')
            text=re.sub(r'\s*\[E[1-9]\d*[^\]]*\]','',text).strip()
            text=re.sub(r'。{2,}','。',text)
            prose.append(text+' ['+', '.join(dict.fromkeys(ids))+']')
        output[language]=prose
    return {**report,'generation':{'kind':'llm','model':response['model'],'elapsed_seconds':response['elapsed_seconds']},
            'method':'本地 LLM 基于证据草稿生成双语防范正文；账号类型与证据规则保留，不识别图片或音频',
            'narrative':output['zh'],'conclusion':'\n\n'.join(output['zh']),
            'narrative_en':output['en'],'conclusion_en':'\n\n'.join(output['en'])}
