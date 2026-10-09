# These tests exercise the low-level evidence engine; product gating is tested in test_account_scope.py.
"""Concrete output should keep roles, full email addresses and attribution precise."""

import unittest
import _paths  # noqa: F401
import account_risk


def assess(*text,media=None,source='https://www.facebook.com/test/',name=None):
    items=[{'text':item,'source_url':source} if isinstance(item,str) else item for item in text]
    value={'source_url':source,'text':items,'media':media or [],'scope':{}}
    if name:
        value['display_name']=name
    return account_risk._analyze_evidence(value)


class SpecificStoryTests(unittest.TestCase):
    def test_private_social_account_and_specific_mother_contact(self):
        report=assess('Ray Hunt','32 位好友','教育经历','The University of Adelaide',
                      'My mum is not particularly tech savvy, but she can use email! Contact her at parent@unit.test',
                      source='https://www.facebook.com/ray.hunt.127')
        self.assertEqual(report['account_purpose']['label'],'私人账号')
        self.assertIn('Ray Hunt',report['narrative'][0])
        self.assertIn('母亲',report['conclusion'])
        self.assertIn('parent@unit.test',report['conclusion'])
        self.assertIn('含 parent@unit.test 的帖子',report['conclusion'])
        self.assertIn('平时联系母亲的电话',report['conclusion'])
        self.assertNotIn('容易受骗',report['conclusion'])

    def test_creator_type_uses_publishing_content_not_follower_count(self):
        report=assess('Gabriel Iancic','5,872 位粉丝','数字内容创作者 Toronto, ON',
                      'Gabriel Iancic 添加了 7 张照片和 1 个视频',
                      'Gabriel Iancic 添加了 2 张照片和 1 个视频',
                      source='https://www.facebook.com/gabriel.iancic')
        self.assertEqual(report['account_purpose']['label'],'公共账号')
        self.assertIn('公共创作者账号',report['narrative'][0])
        follower_only=assess('10万位粉丝')
        self.assertEqual(follower_only['account_purpose']['label'],'无法确定')

    def test_chinese_family_roles_and_separate_email_owners(self):
        report=assess('我父亲的邮箱 dad@unit.test；我母亲的邮箱 mum@unit.test；我的侄子喜欢摄影。')
        by_role={person['relation']:person for person in report['subjects']}
        self.assertEqual(by_role['父亲']['emails'],['dad@unit.test'])
        self.assertEqual(by_role['母亲']['emails'],['mum@unit.test'])
        self.assertIn('侄子',by_role)
        self.assertEqual(by_role['侄子']['interests'],['摄影'])
        self.assertIn('侄子',report['conclusion'])

    def test_nephew_does_not_fabricate_paternal_or_maternal_side(self):
        report=assess('My nephew enjoys photography.')
        self.assertEqual(report['subjects'][0]['relation'],'侄子或外甥')

    def test_singing_does_not_infer_lively_personality(self):
        report=assess('我妈妈喜欢唱歌。')
        mother=report['subjects'][0]
        self.assertEqual(mother['interests'],['唱歌'])
        self.assertEqual(mother['traits'],[])
        self.assertNotIn('活泼',report['conclusion'])

    def test_explicit_personality_is_attributed_not_visually_guessed(self):
        report=assess('我妈妈喜欢唱歌，是个活泼的人。')
        self.assertEqual(report['subjects'][0]['traits'],['活泼'])
        self.assertIn('帖子说母亲喜欢唱歌',report['conclusion'])
        self.assertIn('文字把母亲形容为“活泼”，这是发帖者的描述',report['conclusion'])

    def test_different_people_traits_are_not_mixed(self):
        report=assess('我妈妈喜欢唱歌，爸爸是个活泼的人。')
        self.assertEqual(report['subjects'][0]['traits'],[])
        explicit=assess('我妈妈喜欢唱歌，我父亲是个幽默的人。')
        people={person['relation']:person for person in explicit['subjects']}
        self.assertEqual(people['母亲']['traits'],[])
        self.assertEqual(people['父亲']['traits'],['幽默'])

    def test_negative_descriptions_and_examples_are_not_positive_facts(self):
        report=assess('我妈妈不喜欢唱歌，也不是很活泼。')
        self.assertEqual(report['subjects'][0]['interests'],[])
        self.assertEqual(report['subjects'][0]['traits'],[])
        example=assess('比如我妈妈喜欢唱歌，是个活泼的人。')
        self.assertEqual(example['subjects'],[])

    def test_unlabelled_photos_or_video_do_not_become_mother_biometrics(self):
        report=assess('My mum can use email.',media=[
            {'kind':'image','status':'downloaded','name':'Facebook image'},
            {'kind':'video','status':'downloaded','name':'Facebook video'},
        ])
        person=report['subjects'][0]
        self.assertEqual(person['labelled_images'],0)
        self.assertEqual(person['labelled_audio'],0)
        self.assertNotIn('母亲的照片',report['conclusion'])
        self.assertNotIn('声音素材',report['conclusion'])
        self.assertNotIn('本次没有能明确对应的记录',report['conclusion'])

    def test_explicit_media_labels_are_reported_without_identity_claim(self):
        report=assess('我的母亲喜欢唱歌。',media=[
            {'kind':'image','status':'downloaded','name':'母亲的照片'},
            {'kind':'audio','status':'downloaded','name':'母亲的录音'},
            {'kind':'video','status':'downloaded','name':'我妈妈的视频'},
        ])
        person=report['subjects'][0]
        self.assertEqual(person['labelled_images'],1)
        self.assertEqual(person['labelled_audio'],1)
        self.assertIn('配文或标注关联到母亲',report['conclusion'])
        self.assertIn('人物身份未做识别',report['conclusion'])

    def test_own_email_is_not_assigned_to_mother(self):
        report=assess('我妈妈喜欢唱歌，我的邮箱 owner@unit.test。')
        self.assertEqual(report['subjects'][0]['emails'],[])
        self.assertIn('owner@unit.test',report['conclusion'])
        self.assertIn('原文以“我的邮箱”给出 owner@unit.test',report['conclusion'])
        self.assertNotIn('母亲联系邮箱是 owner@unit.test',report['conclusion'])

    def test_comment_does_not_become_account_owner_family(self):
        report=assess({'text':'My mother loves singing.','context':'comment'})
        self.assertEqual(report['subjects'],[])

    def test_mothers_friend_is_not_mothers_personality_or_face(self):
        report=assess('我妈妈的朋友喜欢唱歌，是个活泼的人。',media=[
            {'kind':'image','status':'downloaded','name':'我妈妈的朋友的照片'}])
        mother=report['subjects'][0]
        self.assertEqual(mother['interests'],[])
        self.assertEqual(mother['traits'],[])
        self.assertEqual(mother['labelled_images'],0)

    def test_voice_description_does_not_fabricate_an_audio_recording(self):
        report=assess('我父亲声音低沉。')
        father=report['subjects'][0]
        self.assertEqual(father['voice_descriptions'],['低沉'])
        self.assertEqual(father['labelled_audio'],0)
        self.assertIn('引用文字描述，不是音频测量',report['conclusion'])
        self.assertNotIn('声音素材',report['conclusion'])

    def test_bilingual_text_uses_same_evidence_and_preserves_original_quotes(self):
        report=assess('示例作者','32 位好友','教育经历','The University of Adelaide',
                      {'text':'我母亲喜欢唱歌，是个活泼的人。我的邮箱 owner@unit.test。','date':'2026-10-08'},
                      name='示例作者')
        english=report['conclusion_en']
        self.assertIn('private social account',english)
        self.assertIn('mother',english)
        self.assertIn('singing',english)
        self.assertIn('lively',english)
        self.assertIn('The writer describes',english)
        self.assertIn('owner@unit.test',english)
        self.assertIn('2026-10-08',english)
        self.assertIn('我母亲',english)  # Original wording is deliberately not translated.
        self.assertEqual(english,'\n\n'.join(report['narrative_en']))
        self.assertEqual(len(report['narrative']),len(report['narrative_en']))

    def test_sparse_material_does_not_generate_missing_field_lists_or_scam_plans(self):
        report=assess('一条普通帖子')
        self.assertEqual(len(report['narrative']),1)
        self.assertEqual(len(report['narrative_en']),1)
        self.assertIn('account type undetermined',report['conclusion_en'])
        for filler in ('父亲','母亲','借款','性格','头像','声音','攻击路径','诈骗话术'):
            self.assertNotIn(filler,report['conclusion'])

    def test_credentials_in_a_profile_statement_stay_masked_in_both_languages(self):
        report=assess('数字内容创作者，验证码：654321，身份证号：DEMO123456789')
        self.assertNotIn('654321',str(report))
        self.assertNotIn('DEMO123456789',str(report))
        self.assertIn('已遮盖',report['conclusion'])
        self.assertIn('已遮盖',report['conclusion_en'])

    def test_english_safeguard_is_specific_without_targeting_instructions(self):
        report=assess({'text':'我正在找工作','date':'2018-04-03','context':'post'})
        english=report['conclusion_en']
        self.assertIn('2018-04-03',english)
        self.assertIn('If the job search is still active',english)
        self.assertIn('employer’s official channel',english)
        self.assertNotIn('is vulnerable',english)
        self.assertNotIn('impersonate the employer',english)

    def test_consequence_and_safeguard_are_paired_with_the_same_visible_evidence(self):
        report=assess('订单号：DEMO1234')
        paragraph=next(value for value in report['narrative'] if 'DEMO1234' in value)
        self.assertIn('知道订单细节不等于客服身份',paragraph)
        self.assertIn('可能造成额外损失',paragraph)
        self.assertIn('从原平台订单入口',paragraph)
        self.assertIn('E1',paragraph)
        english=next(value for value in report['narrative_en'] if 'DEMO1234' in value)
        self.assertIn('could cause additional loss',english)
        self.assertIn('original order page',english)

    def test_family_contact_warning_explains_loss_without_assuming_susceptibility(self):
        report=assess('My mum can use email. Contact her at parent@unit.test')
        self.assertIn('相关账户可能失去控制',report['conclusion'])
        self.assertIn('不代表联系者真的认识家人',report['conclusion'])
        self.assertIn('不太熟悉技术',assess('My mum is not particularly tech savvy.')['conclusion'])
        self.assertIn('could compromise the relevant account',report['conclusion_en'])
        self.assertNotIn('容易受骗',report['conclusion'])

    def test_generation_metadata_does_not_claim_model_inference(self):
        report=assess('普通资料')
        self.assertEqual(report['generation'],{'kind':'rules','model':None})


if __name__=='__main__':
    unittest.main()
