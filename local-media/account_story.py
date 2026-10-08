"""Concrete prose from visible account statements, never from inferred biometrics."""

import re
from urllib.parse import urlsplit


EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
KIN = (
    ('母亲', r'妈妈|母亲|妈', r'mum|mom|mother'),
    ('父亲', r'爸爸|父亲|爸', r'dad|father'),
    ('侄子', r'侄子', r'nephew'),
    ('侄女', r'侄女', r'niece'),
    ('外甥', r'外甥(?!女)', r'nephew'),
    ('外甥女', r'外甥女', r'niece'),
    ('女儿', r'女儿', r'daughter'),
    ('儿子', r'儿子', r'son'),
    ('妻子', r'妻子|老婆', r'wife'),
    ('丈夫', r'丈夫|老公', r'husband'),
    ('姐姐或妹妹', r'姐姐|妹妹', r'sister'),
    ('哥哥或弟弟', r'哥哥|弟弟', r'brother'),
    ('祖母', r'奶奶|祖母', r'grandmother|grandma'),
    ('祖父', r'爷爷|祖父', r'grandfather|grandpa'),
)
INTERESTS = (
    ('唱歌', r'喜欢(?:唱歌|歌唱)|爱唱歌|(?:likes?|loves?|enjoys?) singing'),
    ('跳舞', r'喜欢跳舞|爱跳舞|(?:likes?|loves?|enjoys?) dancing'),
    ('旅游', r'喜欢(?:旅游|旅行)|爱旅行|(?:likes?|loves?|enjoys?) travel(?:ling|ing)?'),
    ('园艺', r'喜欢(?:园艺|养花)|爱养花|(?:likes?|loves?|enjoys?) gardening'),
    ('阅读', r'喜欢(?:阅读|读书)|爱读书|(?:likes?|loves?|enjoys?) reading'),
    ('摄影', r'喜欢摄影|爱摄影|(?:likes?|loves?|enjoys?) photography'),
)
TRAITS = (
    ('活泼', r'(?:性格|是个?|很|十分|非常).{0,3}活泼|\b(?:is|seems) (?:very |a )?lively\b'),
    ('开朗', r'(?:性格|是个?|很|十分|非常).{0,3}开朗|\b(?:is|seems) (?:very )?cheerful\b'),
    ('外向', r'(?:性格|是个?|很|十分|非常).{0,3}外向|\b(?:is|seems) (?:very )?outgoing\b'),
    ('内向', r'(?:性格|是个?|很|十分|非常).{0,3}内向|\b(?:is|seems) (?:very )?introverted\b'),
    ('文静', r'(?:性格|是个?|很|十分|非常).{0,3}文静|\b(?:is|seems) (?:very )?quiet\b'),
    ('幽默', r'(?:性格|是个?|很|十分|非常).{0,3}幽默|\b(?:is|seems) (?:very )?humorous\b'),
)
VOICES = (
    ('低沉',r'(?:声音|嗓音)(?:很|比较|十分|非常|是)?低沉|voice is (?:very )?deep'),
    ('轻柔',r'(?:声音|嗓音)(?:很|比较|十分|非常|是)?(?:轻柔|柔和)|voice is (?:very )?soft'),
    ('洪亮',r'(?:声音|嗓音)(?:很|比较|十分|非常|是)?洪亮|voice is (?:very )?loud'),
    ('沙哑',r'(?:声音|嗓音)(?:很|比较|十分|非常|是)?沙哑|voice is (?:very )?hoarse'),
    ('清亮',r'(?:声音|嗓音)(?:很|比较|十分|非常|是)?(?:清亮|清脆)|voice is (?:very )?clear'),
)


def safe_text(text):
    """Do not let a profile field or source quote reveal credentials."""
    text=re.sub(r'(?<!\d)(\d{2})(\d{5,})(\d{2})(?!\d)',r'\1…\3',text)
    return re.sub(r'((?:验证码|一次性密码|OTP|身份证(?:号|号码)?|银行卡号|护照号)\s*[:：=]?\s*)[A-Z0-9][A-Z0-9 -]{3,22}',
                  r'\1[已遮盖]',text,flags=re.I)


def original(item):
    plain=EMAIL.sub('',item['text'])
    return (item.get('context')!='comment' and not item.get('reposted')
            and not re.search(r'^(?:转发|转载|分享自|reposted|shared from)',plain,re.I)
            and not re.search(r'比如|例如|示例|假设|演示|举例|\b(?:example|sample)\b',plain,re.I))


def account_name(result, evidence):
    if result.get('display_name'):
        return safe_text(str(result['display_name']))[:80]
    slug = urlsplit(result.get('source_url','')).path.casefold()
    for item in evidence[:3]:
        value = item['text'].strip()
        words = re.findall(r'[A-Za-z]{2,}',value)
        if 1<len(words)<=5 and len(value)<=60 and all(word.casefold() in slug for word in words):
            return value
    return '这个账号'


def relation_matches(text, owner=''):
    found=[]
    for label,zh,en in KIN:
        # English nephew/niece does not identify which side of the family.
        if label in {'外甥','外甥女'}:
            en = r'(?!)'
        pattern = r'(?:我的?|我家(?:的)?|本人(?:的)?)('+zh+r')|\bmy\s+('+en+r')\b'
        if owner and owner!='这个账号':
            pattern += '|'+re.escape(owner)+r'的('+zh+r')'
        for match in re.finditer(pattern,text,re.I):
            role=label
            literal=match.group(0).lower()
            if 'nephew' in literal:
                role='侄子或外甥'
            elif 'niece' in literal:
                role='侄女或外甥女'
            elif '姐姐' in literal:
                role='姐姐'
            elif '妹妹' in literal:
                role='妹妹'
            elif '哥哥' in literal:
                role='哥哥'
            elif '弟弟' in literal:
                role='弟弟'
            found.append((match.start(),match.end(),role,match.group(0)))
    # A longer explicit term wins over a short synonym in the same position.
    unique={}
    for value in found:
        if value[0] not in unique or value[1]>unique[value[0]][1]:
            unique[value[0]]=value
    return sorted(unique.values())


def nonnegated(pattern, text):
    for match in re.finditer(pattern,text,re.I):
        before=text[max(0,match.start()-12):match.start()]
        if not re.search(r'(?:不(?:太|怎么|再)?|没有|并非|不是|not|never|doesn.t|no longer)\s*$',before,re.I):
            return True
    return False


def subjects(evidence, result):
    owner=account_name(result,evidence)
    people={}
    for item in evidence:
        if not original(item):
            continue
        mentions=relation_matches(item['text'],owner)
        for index,(start,end,role,literal) in enumerate(mentions):
            stop=mentions[index+1][0] if index+1<len(mentions) else len(item['text'])
            segment=item['text'][start:min(stop,end+220)]
            # Stop before a different family member, even if the writer omitted
            # another "my". Singing must not imply the next person's personality.
            tail=segment[end-start:]
            another=re.search(r'同事|朋友|老师|老板|邻居|同学|\b(?:colleague|friend|teacher|neighbour|neighbor)\b',tail,re.I)
            if another:
                segment=segment[:end-start+another.start()]
                tail=segment[end-start:]
            for other,zh,en in KIN:
                if other!=role:
                    next_person=re.search(zh+r'|\b(?:'+en+r')\b',tail,re.I)
                    if next_person:
                        segment=segment[:end-start+next_person.start()]
                        tail=segment[end-start:]
            # Do not attach a later independent sentence about somebody else.
            sentence=re.split(r'[。!?！；;]',segment,maxsplit=1)[0]
            person=people.setdefault(role,{'relation':role,'literal':literal,'evidence_ids':[], 'emails':[], 'interests':[], 'traits':[], 'descriptions':[], 'voice_descriptions':[]})
            if item['id'] not in person['evidence_ids']:
                person['evidence_ids'].append(item['id'])
            for activity,pattern in INTERESTS:
                if nonnegated(pattern,sentence) and activity not in person['interests']:
                    person['interests'].append(activity)
            for trait,pattern in TRAITS:
                if nonnegated(pattern,sentence) and trait not in person['traits']:
                    person['traits'].append(trait)
            for description,pattern in VOICES:
                if nonnegated(pattern,sentence) and description not in person['voice_descriptions']:
                    person['voice_descriptions'].append(description)
            if re.search(r'not particularly tech savvy|不太熟悉技术|不太懂技术',sentence,re.I):
                person['descriptions'].append('不太熟悉技术')
            if re.search(r'can use email|会(?:使用|用)邮箱',sentence,re.I):
                person['descriptions'].append('能使用邮箱')
            for email in EMAIL.findall(segment):
                mine=re.search(r'(?:我的邮箱|my email)',segment,re.I)
                # A single named relative plus an explicit contact phrase binds
                # the address to that relative as a statement, not a verified fact.
                contact=re.search(r'邮箱|email\s*(?:is|[:：])|contact\s+(?:her|him|my)\s+(?:at|via)|联系(?:她|他|我妈|我爸)|[A-Za-z]+.s\s+email',segment,re.I)
                bound=re.search(re.escape(literal)+r"(?:['’]s|的)?\s*(?:邮箱|email\b)",segment,re.I)
                if contact and not mine and (len(mentions)==1 or bound) and email not in person['emails']:
                    person['emails'].append(email)
    return list(people.values())


def infer_purpose(evidence, result):
    name=account_name(result,evidence)
    creators=[item for item in evidence if original(item) and re.match(r'^(?:数字内容创作者|内容创作者|digital creator)',item['text'],re.I)]
    posts=[]
    if name!='这个账号':
        posts=[item for item in evidence if original(item) and re.match(re.escape(name)+r'\s+(?:添加|发布|上传|posted|added|uploaded)',item['text'],re.I)]
    if creators and len(posts)>=2:
        return {'label':'公共账号','subtype':'公共创作者账号',
                'reason':'主页有“数字内容创作者”标记，并有多条用同一显示名发布的照片或视频，综合判断是对外发布内容的创作者账号。',
                'evidence_ids':[creators[0]['id']]+[item['id'] for item in posts[:2]]}
    kin=[item for item in evidence if original(item) and relation_matches(item['text'],name)]
    education=[item for item in evidence if re.match(r'The University of |教育经历|就读于|毕业于|Studied at ',item['text'],re.I)]
    social=any(re.fullmatch(r'好友|添加好友|加好友|\d+\s*位好友|Friends',item['text'],re.I) for item in evidence)
    business=any(re.search(r'本店|本公司|本机构|官方账号|营业时间|business hours|official page',item['text'],re.I) for item in evidence)
    if kin and education and social and not creators and not business:
        return {'label':'私人账号','subtype':'私人社交账号',
                'reason':'这次可见内容包括个人资料、教育栏目和家庭相关文字，主要是个人生活与社交用途',
                'evidence_ids':[education[0]['id'],kin[0]['id']]}
    return None


def media_for_subject(person, media):
    faces,voices,video=0,0,0
    role=person['relation']
    for asset in media:
        if asset.get('status')!='downloaded':
            continue
        explicit=asset.get('subject_relation')==role
        label=' '.join(str(asset.get(key,'')) for key in ('name','caption','description'))
        literals=[value[3] for value in relation_matches(label) if value[2]==role]
        media_words=r'照片|肖像|人脸|头像|声音|录音|视频'
        labelled=any(re.search(re.escape(literal)+r'(?:的)?(?:'+media_words+r')',label)
                      or re.search(r'(?:照片|视频|录音|这是).{0,12}'+re.escape(literal),label)
                      or re.search(r'(?:photo|picture|portrait|voice|audio|video)(?: of)?\s+'+re.escape(literal),label,re.I)
                      or re.search(re.escape(literal)+r"['’]s\s+(?:photo|picture|portrait|voice|audio|video)",label,re.I)
                      for literal in literals)
        labelled=labelled or any(re.match(re.escape(role)+r'(?:的)?(?:'+media_words+r')',str(asset.get(key,''))) for key in ('name','caption','description'))
        photo_label=bool(re.search(r'照片|肖像|人脸|photo|picture|portrait',label,re.I))
        voice_label=bool(re.search(r'声音|录音|声线|voice|audio|recording',label,re.I))
        if asset['kind']=='image' and (explicit or labelled and photo_label):
            faces+=1
        if asset['kind']=='audio' and (explicit or labelled and voice_label):
            voices+=1
        if asset['kind']=='video' and (explicit or labelled):
            video+=1
            if asset.get('has_audio') is True and voice_label:
                voices+=1
    return {'labelled_images':faces,'labelled_audio':voices,'labelled_videos':video}


WORDS = {
    '母亲':'mother', '父亲':'father', '侄子':'nephew', '侄女':'niece',
    '外甥':'nephew', '外甥女':'niece', '侄子或外甥':'nephew', '侄女或外甥女':'niece',
    '女儿':'daughter', '儿子':'son', '妻子':'wife', '丈夫':'husband',
    '姐姐或妹妹':'sister', '哥哥或弟弟':'brother', '姐姐':'older sister', '妹妹':'younger sister',
    '哥哥':'older brother', '弟弟':'younger brother', '祖母':'grandmother', '祖父':'grandfather',
    '唱歌':'singing', '跳舞':'dancing', '旅游':'travel', '园艺':'gardening', '阅读':'reading', '摄影':'photography',
    '活泼':'lively', '开朗':'cheerful', '外向':'outgoing', '内向':'introverted', '文静':'quiet', '幽默':'humorous',
    '低沉':'deep', '轻柔':'soft', '洪亮':'loud', '沙哑':'hoarse', '清亮':'clear',
    '不太熟悉技术':'not particularly tech savvy', '能使用邮箱':'able to use email',
}


def paragraphs(result, evidence, account, visible, rows, language='zh'):
    """Source-grounded prose and concrete safeguards, without targeting advice.

    Both languages use the same evidence. Original excerpts stay untranslated;
    generated labels and recommendations are localized without external services.
    """
    en=language=='en'
    def t(zh, english):
        return english if en else zh
    def join(values):
        return (', ' if en else '、').join(WORDS.get(value,value) if en else value for value in values)
    def refs(ids):
        items=[item for item in evidence if item['id'] in ids]
        return ' ['+', '.join(item['id']+(' · '+str(item['date']) if item.get('date') else '') for item in items)+']' if items else ''

    name=account_name(result,evidence)
    if name=='这个账号':
        name=t(name,'This account')
    if account['label']=='私人账号':
        first=t(f'{name} 更像私人社交账号。',f'{name} appears to be a private social account. ')
        first+=t('判断依据是个人记录、教育栏目和家庭相关文字。' if account.get('subtype') else '主页明确写了个人记录或私人用途。',
                 'The evidence is personal profile content, education fields and family-related posts.' if account.get('subtype') else 'The profile explicitly describes personal records or private use.')
    elif account['label']=='公共账号':
        creator=account.get('subtype')=='公共创作者账号'
        first=t(f'{name} 按可见内容归为'+('公共创作者账号：创作者标记与多条同名发布记录相互印证。' if creator else '公共业务账号：主页有多项业务或机构用途说明。'),
                f'{name} appears to be a '+('public creator account: the creator label is supported by several posts under the same display name.' if creator else 'public business account: several profile statements describe business or institutional use.'))
    else:
        first=t(f'{name} 的账号类型：无法确定。现有内容不足以区分公共与私人用途。',f'{name}: account type undetermined; the collected content does not establish public or private use.')
    first+=refs(account.get('evidence_ids',[]))
    if visible['label']!='无法确定':
        first+=t(' 所采集内容的可见性标记为“'+visible['label']+'”。',
                 ' The collected content is labelled '+('public' if visible['label']=='公开' else 'restricted')+'.')
    parts=[first]
    actions=[]
    observations=[item for item in evidence if original(item) and re.match(r'^(?:数字内容创作者|内容创作者|住在|来自|已婚|Lives in|From|Married|The University of |就读于|毕业于|Studied at )',item['text'],re.I)]
    websites=[item for item in evidence if original(item) and re.fullmatch(r'(?:https?://)?(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?:/\S*)?',item['text'])]
    if observations:
        parts.append(t('资料栏写有：','Profile statements: ')+('；' if not en else '; ').join('“'+safe_text(item['text'])[:160]+'”'+refs([item['id']]) for item in observations[:5])+t('。这些是页面自述，不代表已核实的身份、学历或实时位置。',' These are profile statements, not verified identity, qualifications or current location.'))
    if websites:
        parts.append(t('页面列出的链接：','Links listed on the page: ')+(', '.join(item['text']+refs([item['id']]) for item in websites[:3]))+t('。','.') )

    people=subjects(evidence,result)
    for person in people[:4]:
        role=join([person['relation']])
        text=t(f'文字提到{role}（原文“{person["literal"]}”）。',f'The text mentions the {role} (original wording: “{person["literal"]}”). ')
        if person['emails']:
            emails=', '.join(person['emails'][:3])
            text+=t(f'文中给出的{role}联系邮箱是 {emails}。',f'The address given for the {role} is {emails}. ')
            actions.append(t(f'含 {emails} 的帖子把“{role}”称呼与联系地址放在了一起，但知道这些公开信息，不代表联系者真的认识家人。如果只因对方知道家事就转账，可能把钱付给未核实的收款人；如果交出验证码，相关账户可能失去控制。遇到这类请求，先停止付款和资料提交，用平时联系{role}的电话核实，不用消息里提供的新号码。若邮箱不用于公开联系，移除地址或限制该帖可见范围。',
                             f'The post containing {emails} links the {role} label to a contact address. Knowing published family details does not establish someone’s identity. Paying on that basis could send money to an unverified recipient; sharing a verification code could compromise the relevant account. Pause payment and disclosure, then verify using the phone number already used to contact the {role}, not a new number in the message. If the address is not for public contact, remove it or restrict the post.')+refs(person['evidence_ids']))
        if person['interests']:
            text+=t(f'帖子说{role}喜欢'+join(person['interests'])+'。',f'The post says the {role} enjoys '+join(person['interests'])+'. ')
        if person['traits']:
            text+=t(f'文字把{role}形容为“'+join(person['traits'])+'”，这是发帖者的描述。',f'The writer describes the {role} as “'+join(person['traits'])+'”. ')
        if person['descriptions']:
            text+=t(f'帖子还说{role}“'+join(dict.fromkeys(person['descriptions']))+'”。',f'The writer also describes the {role} as “'+join(dict.fromkeys(person['descriptions']))+'”. ')
        if person['voice_descriptions']:
            text+=t(f'原文形容{role}的声音“'+join(person['voice_descriptions'])+'”，这里引用文字描述，不是音频测量。',f'The text describes the {role}’s voice as “'+join(person['voice_descriptions'])+'”; this is a written description, not an audio measurement. ')
        media=media_for_subject(person,result.get('media',[]))
        person.update(media)
        if any(media.values()):
            labels=[]
            if media['labelled_images']:
                labels.append(t(f'{media["labelled_images"]} 张照片',f'{media["labelled_images"]} image(s)'))
            if media['labelled_audio']:
                labels.append(t(f'{media["labelled_audio"]} 段声音素材',f'{media["labelled_audio"]} audio item(s)'))
            if media['labelled_videos']:
                labels.append(t(f'{media["labelled_videos"]} 个视频',f'{media["labelled_videos"]} video(s)'))
            text+=t(f'配文或标注关联到{role}的素材有：'+join(labels)+'；人物身份未做识别。',f'Captions or labels associate '+join(labels)+f' with the {role}; identity has not been verified. ')
        parts.append(text.strip()+refs(person['evidence_ids']))

    assigned={email for person in people for email in person['emails']}
    remaining=list(dict.fromkeys(email for item in evidence if original(item) for email in EMAIL.findall(item['text']) if email not in assigned))
    for email in remaining[:5]:
        items=[item for item in evidence if original(item) and email in item['text']]
        own=any(re.search(r'我的邮箱|my email',item['text'],re.I) for item in items)
        parts.append(t('原文以“我的邮箱”给出 ' if own else '文字出现邮箱（归属未说明）：',
                       'The writer gives the address as “my email”: ' if own else 'An email appears without an explicit owner: ')+email+refs([item['id'] for item in items])+t('。','.'))

    safeguards={
        'credentials':'If these are genuine credentials, remove or mask them and check the account through the original service. Verification codes should only be used for an action you initiated.',
        'location':'Limit disclosure of home details and live travel plans. Confirm changes or charges with the original booking provider or an existing contact.',
        'orders':'Mask the order number, barcode and personal fields. Start refund or support requests from the original order page.',
        'job':'If the job search is still active, confirm the role through the employer’s official channel. Decline advance fees and unrelated sensitive-data requests.',
        'rent':'If the housing search is still active, verify the listing, the advertiser and viewing arrangements. Independently confirm the recipient before paying.',
        'trade':'Check the item and counterparty, and keep payment in a trusted channel with records. Independently verify requests to pay off-platform or advance funds.',
        'impersonation':'Preserve the source link and screenshots. Verify identity through an existing channel, stop responding to suspicious requests and report them to the platform.',
        'transaction':'If the statement is accurate, pause further payments or disclosure. Verify the counterparty through the original service and retain the correspondence.',
        'third_party_data':'If these are real customer or internal details, remove unnecessary fields. Use clearly identified official contact and incident-handling channels.',
    }
    outcomes={
        'credentials':('若这些是真实凭据，被他人使用可能造成账户失控或资金损失。','If these are genuine credentials, misuse could compromise an account or cause financial loss.'),
        'location':('住宅细节或实时行程会扩大隐私暴露；联系者知道这些信息，也不能证明其身份。','Home details or live travel plans increase privacy exposure; knowing them does not verify a contact’s identity.'),
        'orders':('知道订单细节不等于客服身份；向未核实的收款人支付所谓售后费用，可能造成额外损失。','Knowing order details does not establish customer-support identity. Paying an unverified recipient for supposed support could cause additional loss.'),
        'job':('若求职需求仍有效，向未核实的招聘方交费或提供证件，可能造成资金损失或资料被冒用。','If the job search is still active, paying fees or providing identity documents to an unverified recruiter could cause financial loss or misuse of personal data.'),
        'rent':('若租房需求仍有效，未核实房源和收款人就付定金，可能失去定金而没有获得住处。','If the housing search is still active, paying a deposit before verifying the property and recipient could leave you without the money or accommodation.'),
        'trade':('未核实交易对象就站外付款或垫资，可能付出款项却没有收到商品。','Paying off-platform or advancing funds without verifying the counterparty could leave you without the payment or the item.'),
        'impersonation':('把同名、头像或对方知道的资料当作身份凭证，可能把钱款或个人资料交给错误的人。','Treating a matching name, avatar or known details as proof of identity could send money or personal data to the wrong person.'),
        'transaction':('若自述属实，继续付款或提交敏感资料可能扩大已有损失；现有材料不能确认已发生的损失金额。','If the statement is accurate, further payment or disclosure could increase an existing loss. The material does not establish any actual loss amount.'),
        'third_party_data':('若字段属于真实客户或员工，不必要的公开会扩大他人的隐私暴露。','If the fields describe real customers or staff, unnecessary publication increases their privacy exposure.'),
    }
    seen=set()
    for row in rows:
        if not row.get('risk') or row['key'] not in safeguards:
            continue
        # One evidence item must not generate several repetitive paragraphs.
        if set(row['evidence_ids']) <= seen:
            continue
        seen.update(row['evidence_ids'])
        excerpt=row['excerpts'][0]
        prefix=(str(excerpt['date'])+' · ') if excerpt.get('date')!='日期不可见' else ''
        quote=t('可见原文：','Visible excerpt: ')+prefix+'“'+excerpt['quote']+'”'+refs(row['evidence_ids'])
        outcome=t(*outcomes[row['key']])
        safeguard=row['recommendation'] if not en else safeguards[row['key']]
        parts.append(quote+t('。可能的损失或暴露：',' Possible loss or exposure: ')+outcome+t(' 防范动作：',' What to do: ')+safeguard)
        if len(seen)>=3:
            break
    if actions:
        parts.append(t('具体防范：','Concrete safeguards: ')+(' '.join(actions[:3])))
    protections=[row for row in rows if row['key']=='protection']
    if protections:
        excerpt=protections[0]['excerpts'][0]
        parts.append(t('已有防范提醒：“','An existing safety reminder says: “')+excerpt['quote']+'”'+refs(protections[0]['evidence_ids'])+t('。','.') )
    return parts,people
