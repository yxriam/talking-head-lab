"""Conservative, traceable account-risk assessment from collected visible text.

This is a deterministic evidence-rules report, not an LLM or a probability model.
Appearance, follows and likes do not infer susceptibility. Posted personal
descriptions are attributed to their source, never inferred from images or voices.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
import account_story


@dataclass(frozen=True)
class Rule:
    key: str
    focus: str
    pattern: str
    weak_point: str
    scenario: str
    action: str
    sentence: str
    impact: int = 1


RULES = (
    Rule('third_party_data', '内部或客户信息', r'(?:客户|员工|内部人员)(?:姓名|电话|手机|联系方式|身份证号)\s*[:：]\s*\S{2,}',
         '出现内部或客户字段样式；需核实是否为真实且不必要的第三方信息', '冒充客服、冒充机构人员',
         '若为真实资料，移除不必要的客户或内部字段；业务展示只保留必要信息，联系与异常处理走明确的官方渠道。',
         '客户或内部字段若属实，可能被借用于冒充客服或机构人员；减少不必要展示，业务联系走明确的官方渠道。', 3),
    Rule('credentials', '身份与验证凭据', r'(?:身份证(?:号|号码)?|银行卡号|护照号|验证码|一次性密码|OTP)\s*[:：=]?\s*[A-Z0-9][A-Z0-9 -]{3,22}',
         '出现敏感标识或验证凭据样式的内容；需核实是否是真实信息或示例', '冒充客服、账号冒用',
         '若为真实信息，先移除或遮盖；通过原服务渠道检查账号安全，验证码只用于本人正在发起的操作。',
         '凭据样式的内容需要先确认是否真实；若属实，及时遮盖，并从原服务渠道检查账号安全。', 3),
    Rule('contacts', '身份和联系方式', r'(?:私人手机号|手机|电话|微信|phone|mobile|email|邮箱)\s*[:：]\s*\S{4,}|[A-Za-z0-9.+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|\+\d[\d ()-]{7,18}',
         '联系方式可以成为身份核验的辅助线索，但其正常业务用途和归属需要区分', '冒充熟人、冒充客服',
         '减少非必要私人联系方式暴露；涉及付款或验证码的联系，使用自己保存的号码或原平台入口独立核实。',
         '私人联系方式可能被借用于冒充熟人或客服；涉及付款或验证码时，用自己保存的号码回拨核实。', 1),
    Rule('location', '位置与行程', r'(?:我家|家住|家庭住址|住宅地址|home address)\s*(?:在|是|[:：])|(?:明天|今晚|下周|本周).{0,25}(?:出发|离家|飞往|航班|入住)|(?:门牌|房号|航班号)\s*[:：]\s*\S+',
         '住宅或行程细节可能提供额外身份线索；位置、行程及其时效尚未核验', '冒充熟人、冒充旅行服务人员',
         '减少实时位置、住宅细节及行程公开；费用或安排变更通过原预订平台或已保存的联系人核实。',
         '住宅或行程细节可能被借用于冒充熟人或旅行服务人员；减少实时位置公开，变更安排时向原服务方核实。', 2),
    Rule('orders', '票据与订单', r'(?:订单号|快递单号|运单号|票据号|预订编号|booking reference|order number)\s*[:：#]?\s*[A-Z0-9-]{4,}',
         '可见编号样式可能提供订单线索；订单真实性和是否仍有效尚未核验', '冒充客服',
         '遮盖订单编号、条码及个人字段；售后或退款从原平台订单入口发起，独立核实来电。',
         '订单编号可能被借用于冒充客服；遮盖编号和个人字段，售后与退款只从原平台订单入口发起。', 2),
    Rule('relations', '家人和同事关系', r'(?:我的|我家|my\s+)(?:爸爸|妈妈|父亲|母亲|丈夫|妻子|女儿|儿子|同事|老板|mother|father|mum|mom|dad|wife|husband|daughter|son|sister|brother|colleague)',
         '出现关系称呼；只支持确认该表述存在，不能证明真实关系或信任程度', '冒充熟人',
         '减少可被拼接的关系与联系方式；紧急借款、代付款等请求，用既有联系方式向本人确认。',
         '关系称呼若确属本人，可能被借用于冒充熟人；遇到紧急借款或代付款，先用既有联系方式确认。', 1),
    Rule('job', '明确的求职需求', r'^(?:求职|找工作)[：:，, ]|(?:我|本人).{0,8}(?:正在|目前|近期|想|在|需要).{0,5}(?:找工作|找兼职|求职)|\b(?:I am|I.m|currently)\s+looking for (?:a job|work)\b',
         '出现求职需求表述；发布者归属与当前是否仍有需求需要核实', '虚假招聘',
         '若需求仍有效，从单位官方渠道核验岗位；警惕预付费用、垫资或与岗位无关的敏感资料请求。',
         '若求职需求仍有效，需要警惕虚假招聘；从单位官方渠道核验岗位，拒绝预付费用和无关敏感资料请求。', 2),
    Rule('rent', '明确的租房需求', r'^求租[：:，, 一两三套间房]|(?:我|本人).{0,8}(?:正在|目前|想|在|需要).{0,5}(?:找房|租房)|\blooking for (?:a room|a flat|accommodation)\b',
         '出现租房需求表述；无法仅凭帖子确认本人需求和当前状态', '虚假租房',
         '若需求仍有效，核验房源和发布者，确认实际看房安排；付款前独立核实收款方与交易渠道。',
         '若租房需求仍有效，需要警惕虚假房源；核验发布者和实际看房安排，付款前独立确认收款方。', 2),
    Rule('trade', '明确的交易需求', r'^(?:出售|求购)[：:，, ]|(?:我|本人).{0,8}(?:想|正在|准备|需要).{0,5}(?:出售|卖掉|购买|求购)',
         '出现交易需求表述；需求归属、交易是否发生及是否仍有效未知', '虚假交易',
         '核验商品与交易对象，优先使用有记录的可信交易渠道；对站外付款、垫资请求独立复核。',
         '若交易需求仍有效，需要警惕虚假交易；核验商品和对象，付款留在有记录的可信渠道。', 2),
    Rule('impersonation', '可见的冒充或可疑请求', r'(?:有人|陌生账号|假账号|可疑账号).{0,20}(?:冒充|要求我转账|索要验证码)|(?:冒充我的|假冒本店|假冒本公司|假冒客服)',
         '存在关于冒充或可疑请求的表述；不能据此确认所指账号已经构成诈骗', '冒充熟人、冒充客服',
         '保留原始链接及截图，独立核实身份和官方入口；可疑请求先停止回应，再向平台举报。',
         '材料提到疑似冒充或可疑请求，需要警惕身份混淆；保留链接和截图，独立核验并向平台举报。', 3),
    Rule('transaction', '资料提供或垫资行为的表述', r'我(?:已经|已|刚|曾).{0,12}(?:垫资|站外付款|提供验证码|提供身份证)',
         '出现资料提供或垫资的自述；行为是否发生、对象及当前状态均未核验', '冒充客服、虚假交易',
         '若表述属实，先暂停追加付款或资料提交；从原平台或服务渠道核实对象，保留原始往来记录。',
         '提供资料或垫资的自述若属实，需要警惕冒充客服或虚假交易；先暂停追加提交，再通过原渠道核实。', 3),
)

PROTECTION = re.compile(r'(?:先|务必|必须|请).{0,6}(?:核验|核实)|(?:已经|已)(?:举报|核实|停止转账)|拒绝.{0,8}(?:转账|借款|可疑|陌生|提供验证码)|(?:不要|勿|不向).{0,12}(?:提供|透露|分享|发送).{0,8}验证码|谨防冒充|防冒充提醒|verify before|never share.{0,15}(?:code|password)', re.I)
EXAMPLE = re.compile(r'例如|示例|假设|演示|举例|example|sample', re.I)
REPOST = re.compile(r'转发|转载|分享自|shared (?:a|from)|reposted|quoted', re.I)
PUBLIC = re.compile(r'官方账号|本店|本公司|本机构|营业时间|门店地址|official (?:account|page)|business hours', re.I)
PRIVATE = re.compile(r'私人账号|个人账号|个人生活记录|记录我的生活|personal account|personal diary', re.I)
OFFICIAL = re.compile(r'(?:官方|唯一)(?:网站|电话|客服|联系|入口)\s*[:：]|官网\s*[:：]|official (?:website|contact|support)\s*:', re.I)
NEGATIVE_NEED = re.compile(r'(?:不|没有|不再|无需|not |no longer ).{0,6}(?:找工作|求职|租房|找房|出售|购买|looking for)', re.I)
RELATION = re.compile(next(rule.pattern for rule in RULES if rule.key=='relations'),re.I)


def evidence_type(item):
    text = item['text']
    if item.get('context') == 'comment':
        return '评论内容；归属未核实'
    if item.get('reposted') or REPOST.search(text):
        return '转发或引用内容；不视为本人事实'
    if re.search(r'^(?:我|本人|我们|I\b|my\b)', text, re.I):
        return '自我描述；真实情况与归属未核实'
    if item.get('context') == 'post':
        return '发布的内容；文本可确认，现实事实与归属未核实'
    return '页面可见表述；真实情况与归属未核实'


def published_date(value):
    match = re.search(r'(?<!\d)(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})', value or '')
    if not match:
        return None
    try:
        return date(*map(int, match.groups()))
    except ValueError:
        return None


def quote(text, match=None):
    start = max(0, (match.start() if match else 0) - 45)
    snippet = text[start:start+180]
    # Display a traceable excerpt while masking long identifiers and OTP values.
    snippet = re.sub(r'(?<!\d)(\d{2})(\d{5,})(\d{2})(?!\d)', r'\1…\3', snippet)
    snippet = re.sub(r'((?:验证码|一次性密码|OTP)\s*[:：=]?\s*)[A-Z0-9]{4,8}', r'\1[已遮盖]', snippet, flags=re.I)
    snippet = re.sub(r'([A-Za-z0-9.+-]{2})[A-Za-z0-9.+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})',r'\1…@\2',snippet)
    return ('…' if start else '') + snippet + ('…' if start+180<len(text) else '')


def purpose(evidence, result=None):
    # Profile/page snippets only. A repost or somebody else's comment is not a bio.
    profile = [item for item in evidence if item.get('context') == 'profile_or_page' and not REPOST.search(item['text']) and not EXAMPLE.search(item['text'])]
    public = [item['id'] for item in profile if PUBLIC.search(item['text'])]
    private = [item['id'] for item in profile if PRIVATE.search(item['text'])]
    public_count = len({value.lower() for item in profile for value in PUBLIC.findall(item['text'])})
    private_count = len({value.lower() for item in profile for value in PRIVATE.findall(item['text'])})
    if public_count>=2 and not private:
        return {'label':'公共账号', 'reason':'主页可见表述显示业务或机构用途；用途判断不等于认证其身份。', 'evidence_ids':public[:3]}
    if private_count>=2 and not public:
        return {'label':'私人账号', 'reason':'主页明确自述个人记录或私人用途；不据外貌、粉丝或兴趣判断。', 'evidence_ids':private[:3]}
    inferred=account_story.infer_purpose(evidence,result or {})
    if inferred:
        return inferred
    creator = [item['id'] for item in evidence if re.match(r'^(?:数字内容创作者|内容创作者|digital creator)',item['text'],re.I)]
    reason = '可见材料有内容创作者字样，但不能仅凭标签或粉丝数确定账号用途；完整内容与归属上下文不足。' if creator else '缺少明确的主页用途信息，或业务与个人用途表述并存。'
    return {'label':'无法确定', 'reason':reason, 'evidence_ids':creator[:3]}


def visibility(evidence, scope):
    audiences = scope.get('audiences', [])
    public = any(value.lower() in {'public','公开','向公众分享','shared with public'} for value in audiences)
    limited = any(value.lower() in {'friends','only me','好友','朋友','仅自己'} for value in audiences)
    if public and not limited:
        return {'label':'公开', 'reason':'可见性标记原文：'+ '、'.join(audiences) +'。仅说明所采集内容，不能扩展至整个账号或全部历史内容。', 'evidence_ids':[]}
    if limited and not public:
        return {'label':'受限', 'reason':'可见性标记原文：'+ '、'.join(audiences) +'。无法评估未显示的内容。', 'evidence_ids':[]}
    return {'label':'无法确定', 'reason':'本机能访问页面不等于公开；没有一致、明确的可见性标记。', 'evidence_ids':[]}




def analyze(result, today=None):
    today = today or datetime.now(timezone.utc).date()
    evidence, seen = [], set()
    for item in result.get('text', []):
        text = ' '.join(str(item.get('text','')).split())[:1500]
        if not text or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        evidence.append({**item, 'id':f'E{len(evidence)+1}', 'text':text,
                         'claim_type':evidence_type({**item,'text':text})})
    account = purpose(evidence,result)
    rows, protections = [], []
    for rule in RULES:
        hits = [(item,re.search(rule.pattern,item['text'],re.I)) for item in evidence]
        hits = [(item,match) for item,match in hits if match]
        if rule.key in {'job','rent','trade'}:
            hits = [(item,match) for item,match in hits if not NEGATIVE_NEED.search(item['text'])]
        if rule.key == 'credentials':
            hits = [(item,match) for item,match in hits if not EXAMPLE.search(item['text'])]
        if rule.key == 'transaction':
            hits = [(item,match) for item,match in hits if not re.search(r'(?:拒绝|未|没有|停止).{0,6}(?:垫资|付款|提供)',item['text'])]
        if not hits:
            continue
        refs = [item['id'] for item,_ in hits[:3]]
        excerpts = [{'id':item['id'], 'quote':quote(item['text'],match), 'source_url':item.get('source_url') or result.get('source_url',''),
                     'date':item.get('date') or '日期不可见', 'claim_type':item['claim_type']} for item,match in hits[:3]]
        indirect = all(item.get('context')=='comment' or item.get('reposted') or REPOST.search(item['text']) or EXAMPLE.search(item['text']) for item,_ in hits)
        risk = not indirect
        personal_relation = rule.key == 'contacts' and any(RELATION.search(item['text']) for item,_ in hits)
        if rule.key == 'contacts' and (account['label'] != '私人账号') and not personal_relation and not any(re.search(r'私人|我的手机|personal phone',item['text'],re.I) for item,_ in hits):
            risk = False
        dates = [published_date(item.get('date','')) for item,_ in hits]
        stale = bool(dates and all(value and (today-value).days>30 for value in dates))
        active_profile = any(item.get('context') == 'profile_or_page' for item,_ in hits)
        level = '优先处理' if risk and rule.impact==3 and active_profile and not stale else '建议改善' if risk else '证据不足'
        effect = f'场景推断：若相关线索属实且仍有效，需要警惕{rule.scenario}；未证明该场景已发生。' if risk else '可能是正常业务联系信息；用途和归属未清楚前，不直接列为风险。'
        if indirect:
            effect = '依据来自评论、转发或示例，无法归因于账号使用者；本人对应风险无法评估。'
        row = {'key':rule.key, 'focus':rule.focus, 'evidence_ids':refs, 'excerpts':excerpts, 'effect':effect,
               'strength':'文本明确可见；现实情况未核验', 'recommendation':rule.action if risk else '先核对内容归属和正常业务用途，再确认是否需要调整。',
               'weak_point':rule.weak_point, 'scenario':rule.scenario if risk else '无法评估', 'risk':risk,
               'impact':rule.impact, 'level':level, 'sentence':rule.sentence,
               'stale':stale, 'active_profile':active_profile,
               'review':'可能是他人表述、转发或示例；不据此推断信任、支付意愿或本人防诈骗能力。' + ('已发现较早日期，当前是否仍有效无法确认。' if stale else '未核实当前状态；日期不可见时不推定为近期事件。')}
        if personal_relation and risk:
            row.update(personal_relation=True, contact_kind='邮箱' if any('@' in item['text'] for item,_ in hits) else '联系方式', scenario='冒充熟人',
                       effect='场景推断：亲友称呼和联系方式若属实，可能被借用于冒充熟人；不据技术能力表述判断亲友容易受骗。',
                       sentence='亲友联系信息若属实，可能被借用于冒充熟人；减少不必要的展示，涉及钱款或资料的请求用既有渠道确认本人。')
        rows.append(row)
    for key,focus,pattern in [('protection','核验、防冒充与纠错提醒',PROTECTION), ('official','官方渠道与业务入口说明',OFFICIAL)]:
        hits = [item for item in evidence if pattern.search(item['text'])]
        if key == 'protection':
            hits = [item for item in hits if not re.search(r'(?:无需|不必|不要|不需要|没有|未|not).{0,4}(?:核实|核验|举报)',item['text'],re.I)]
        if not hits:
            continue
        refs = [item['id'] for item in hits[:3]]
        description = '可见材料存在防范或渠道说明；不能仅据该表述确认本人已执行或有防诈骗能力。'
        protections.append({'text':description,'evidence_ids':refs})
        rows.append({'key':key,'focus':focus,'evidence_ids':refs,
                     'excerpts':[{'id':item['id'],'quote':quote(item['text']),'source_url':item.get('source_url') or result.get('source_url',''), 'date':item.get('date') or '日期不可见','claim_type':item['claim_type']} for item in hits[:3]],
                     'effect':description,'strength':'提醒或说明明确可见；实际执行未核验',
                     'recommendation':'保留清晰的核验提示及业务入口；对照原始来源确认渠道和异常处理记录。',
                     'risk':False,'review':'可能属于引用或他人的提醒；业务入口真实性未独立核验。'})
    for key,focus,pattern in [
        ('profile_labels','身份和资料自述',r'^(?:数字内容创作者|内容创作者|digital creator|已婚|married|The University of )'),
        ('city','城市与来源地自述',r'^(?:住在|来自)\S{2,}|^(?:Lives in|From)\s+\S{2,}')]:
        hits=[item for item in evidence if re.search(pattern,item['text'],re.I)]
        if hits:
            rows.append({'key':key,'focus':focus,'evidence_ids':[item['id'] for item in hits[:3]],
                         'excerpts':[{'id':item['id'],'quote':quote(item['text']),'source_url':item.get('source_url') or result.get('source_url',''),
                                      'date':item.get('date') or '日期不可见','claim_type':item['claim_type']} for item in hits[:3]],
                         'effect':'可确认页面出现相关自述或资料文字；真实性未核验，不能仅据这些标签或城市线索判断容易受骗。',
                         'strength':'文字明确可见；现实身份与居住情况未核验','recommendation':'按实际需要检查可见范围；详细地址、实时行程和内容归属需另有证据才能评估。',
                         'risk':False,'review':'城市级信息不等于详细地址或实时位置；职业、婚姻和创作者标签不用于推断防诈骗能力。'})
    checks = [('contacts','身份和联系方式'),('location','位置与行程'),('orders','票据与订单'),('relations','家人和同事关系'),('needs','求职、租房或交易需求'),('protection','核验、防冒充与纠错提醒')]
    if account['label']=='公共账号':
        checks += [('third_party_data','内部或客户信息'),('official','官方渠道与业务入口说明'),('impersonation','可见冒充与可疑引流'),('promotion','推广或转发的核验依据')]
    else:
        checks += [('transaction','资料提供、站外付款或垫资行为')]
    for key,focus in checks:
        present = any(row['key']==key or (key=='needs' and row['key'] in {'job','rent','trade'}) or (key=='location' and row['key']=='city') for row in rows)
        if not present:
            rows.append({'key':'unknown_'+key,'focus':focus,'evidence_ids':[],'excerpts':[], 'effect':'无法评估；未识别到明确文字依据，不代表此类信息或行为不存在。',
                         'strength':'证据不足','recommendation':'如需评估，补充可见的原文、日期与上下文。','risk':False,'review':'未采集到或无法识别，不作为负面判断。'})
    priorities = []
    used = set()
    for row in sorted((row for row in rows if row.get('risk')),key=lambda row:(-row['impact'],row['stale'],not row['active_profile'])):
        if set(row['evidence_ids']) <= used:
            continue
        used.update(row['evidence_ids'])
        timing = '可见日期较早，是否仍有效无法确认。' if row['stale'] else '本次主页或页面区域可见，实际归属与有效性仍需核实。' if row['active_profile'] else '仅确认帖子中出现表述，当前是否仍持续需核实。'
        impact = '涉及身份、资料或冒充线索，潜在影响较大。' if row['impact']==3 else '有明确的信息或需求线索。'
        priorities.append({'level':row['level'],'focus':row['focus'],'reason':impact+timing,
                           'action':row['recommendation'],'evidence_ids':row['evidence_ids']})
        if len(priorities)==3:
            break
    if not priorities:
        priorities=[{'level':'证据不足','focus':'核对账号用途和可见范围','reason':'现有材料不足以建立明确、仍有效的风险链条。',
                     'action':'先补充可核对的主页与内容上下文，再判断具体信息暴露风险。','evidence_ids':[]}]
    scope = result.get('scope',{})
    visible=visibility(evidence,scope)
    narrative,subjects=account_story.paragraphs(result,evidence,account,visible,rows)
    narrative_en,_=account_story.paragraphs(result,evidence,account,visible,rows,language='en')
    return {'version':'3','method':'基于可见证据的中英文信息摘要与具体防范；不生成人物攻击方案', 'generated_at':datetime.now(timezone.utc).isoformat(),
            'generation':{'kind':'rules','model':None},
            'account_purpose':account,'visibility':visible,
            'scope':f"本次采集 {len(evidence)} 条去重可见文字、{len(result.get('media',[]))} 条媒体记录；不代表完整账号历史。",
            'limits':['图片与视频内容未做识别，音频未转写；不从外貌推断身份或风险。','评论与公开互动未完整采集；关注、点赞及单次互动不用于推断信任或经济状况。',
                      '帖子表述不等于现实事实；发布者归属、未知日期与当前有效性需要复核。','信息暴露、可见防范表述与实际防诈骗能力分别处理；能力无法评估。',
                      '规则只覆盖明确文字线索；复杂语境与未识别信息无法评估，未识别到风险不等于安全。'],
            'rows':rows,'priorities':priorities,'protections':protections,
            'source_facts':[{'id':item['id'],'text':account_story.safe_text(item['text'])} for item in evidence],
            'subjects':subjects,'narrative':narrative,'conclusion':'\n\n'.join(narrative),
            'narrative_en':narrative_en,'conclusion_en':'\n\n'.join(narrative_en)}
