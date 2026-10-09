# -*- coding: utf-8 -*-
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "pdf" / "social_media_scam_awareness_proposal_zh.pdf"
PIPELINE_FIG = ROOT / "figures" / "pipeline_gptimage2.png"
EVALUATION_FIG = ROOT / "figures" / "evaluation_gptimage2.png"


def scaled_image(path, max_width):
    image_width, image_height = ImageReader(str(path)).getSize()
    return Image(str(path), width=max_width, height=max_width * image_height / image_width)


def register_fonts():
    body_candidates = [
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ]
    bold_candidates = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for name, candidates in [("ZHBody", body_candidates), ("ZHBold", bold_candidates)]:
        for path in candidates:
            if Path(path).exists():
                pdfmetrics.registerFont(TTFont(name, path))
                break
        else:
            raise RuntimeError(f"No Chinese font found for {name}")


def para(text, style):
    return Paragraph(text, style)


class PipelineDiagram(Flowable):
    def __init__(self, width=500, height=92):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        boxes = [
            ("授权媒体", "用户提供/导出/API允许", colors.HexColor("#e9e7fb")),
            ("来源记录", "同意状态/路径/用途", colors.HexColor("#e7eefb")),
            ("特征提取", "人脸裁剪/声音片段", colors.whitesmoke),
            ("语音模型", "Chatterbox 生成语音", colors.HexColor("#e9f7e9")),
            ("视频模型", "A2H/ST/EM/MT 对比", colors.HexColor("#e9f7e9")),
            ("意识演示", "带标签输出/评估日志", colors.HexColor("#fff1df")),
        ]
        x0, y0 = 8, 42
        bw, bh, gap = 74, 32, 8
        for i, (title, sub, fill) in enumerate(boxes):
            x = x0 + i * (bw + gap)
            c.setStrokeColor(colors.HexColor("#555555"))
            c.setFillColor(fill)
            c.roundRect(x, y0, bw, bh, 4, stroke=1, fill=1)
            c.setFillColor(colors.black)
            c.setFont("ZHBold", 7.4)
            c.drawCentredString(x + bw / 2, y0 + 19, title)
            c.setFont("ZHBody", 5.8)
            c.drawCentredString(x + bw / 2, y0 + 9, sub)
            if i < len(boxes) - 1:
                ax = x + bw + 1
                ay = y0 + bh / 2
                c.setStrokeColor(colors.HexColor("#333333"))
                c.line(ax, ay, ax + gap - 3, ay)
                c.setFillColor(colors.HexColor("#333333"))
                c.line(ax + gap - 3, ay, ax + gap - 7, ay + 3)
                c.line(ax + gap - 3, ay, ax + gap - 7, ay - 3)
        c.setFont("ZHBody", 6)
        c.setFillColor(colors.HexColor("#333333"))
        c.drawCentredString(
            self.width / 2,
            18,
            "输入限定为授权、用户提供、用户导出或 API 允许的公开材料；系统先记录来源，再生成带标签的防诈骗意识演示。",
        )


class EvaluationDiagram(Flowable):
    def __init__(self, width=500, height=112):
        super().__init__()
        self.width = width
        self.height = height

    def draw_box(self, x, y, w, h, title, sub, fill):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#555555"))
        c.setFillColor(fill)
        c.roundRect(x, y, w, h, 4, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont("ZHBold", 7.5)
        c.drawCentredString(x + w / 2, y + h - 11, title)
        c.setFont("ZHBody", 6)
        c.drawCentredString(x + w / 2, y + 9, sub)

    def arrow(self, x1, y1, x2, y2):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#333333"))
        c.line(x1, y1, x2, y2)
        if x2 >= x1:
            c.line(x2, y2, x2 - 4, y2 + 3)
            c.line(x2, y2, x2 - 4, y2 - 3)
        else:
            c.line(x2, y2, x2 + 4, y2 + 3)
            c.line(x2, y2, x2 + 4, y2 - 3)

    def draw(self):
        w, h = 150, 32
        x1, x2 = 92, 258
        y_top, y_mid, y_bottom = 70, 34, 2
        self.draw_box(x1, y_top, w, h, "受控对比", "模型/裁剪/声音参考/源条件", colors.HexColor("#fff1df"))
        self.draw_box(x2, y_top, w, h, "自动指标", "ArcFace/ECAPA/SyncNet", colors.HexColor("#e9e7fb"))
        self.draw_box(x2, y_mid, w, h, "人工评分", "真实感/唇形/身份/声音", colors.HexColor("#e7eefb"))
        self.draw_box(x1, y_mid, w, h, "失败轴分析", "可见失败 vs 隐藏失败", colors.HexColor("#fff1df"))
        self.draw_box(174, y_bottom, 160, 28, "防范建议", "验证提示/源质量警告/用户教育", colors.HexColor("#e9f7e9"))
        self.arrow(x1 + w, y_top + h / 2, x2, y_top + h / 2)
        self.arrow(x2 + w / 2, y_top, x2 + w / 2, y_mid + h)
        self.arrow(x2, y_mid + h / 2, x1 + w, y_mid + h / 2)
        self.arrow(x1 + w / 2, y_mid, 254, y_bottom + 28)


def build():
    register_fonts()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.68 * inch,
        leftMargin=0.68 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.62 * inch,
        title="AI 生成说话头像诈骗意识项目 Proposal 中文版",
    )

    base = dict(fontName="ZHBody", fontSize=10, leading=15, wordWrap="CJK")
    styles = {
        "title": ParagraphStyle("title", fontName="ZHBold", fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=8),
        "author": ParagraphStyle("author", fontName="ZHBody", fontSize=10.5, leading=14, alignment=TA_CENTER, spaceAfter=14),
        "abstract_title": ParagraphStyle("abstract_title", fontName="ZHBold", fontSize=10.5, leading=14, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4),
        "abstract": ParagraphStyle("abstract", **base, alignment=TA_JUSTIFY, leftIndent=20, rightIndent=20),
        "keywords": ParagraphStyle("keywords", fontName="ZHBody", fontSize=9.5, leading=13, leftIndent=20, rightIndent=20, spaceAfter=10, wordWrap="CJK"),
        "h1": ParagraphStyle("h1", fontName="ZHBold", fontSize=13, leading=17, spaceBefore=12, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName="ZHBold", fontSize=11, leading=15, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", **base, alignment=TA_JUSTIFY, firstLineIndent=18, spaceAfter=5),
        "caption": ParagraphStyle("caption", fontName="ZHBody", fontSize=8.5, leading=12, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8, wordWrap="CJK"),
        "small": ParagraphStyle("small", fontName="ZHBody", fontSize=8.4, leading=11.5, wordWrap="CJK"),
        "ref": ParagraphStyle("ref", fontName="ZHBody", fontSize=8.4, leading=11.5, leftIndent=16, firstLineIndent=-16, wordWrap="CJK"),
    }

    story = []
    story.append(para("一个用于社交媒体诈骗意识提升与防范的 AI 生成说话头像内容端到端演示系统", styles["title"]))
    story.append(para("Alice / Xinran Yang<br/>AI Project Proposal Draft - 中文论文版", styles["author"]))
    story.append(para("摘要", styles["abstract_title"]))
    story.append(
        para(
            "AI 工具让身份转换变得越来越容易，攻击者可以把公开人像、短声音样本和生成文本组合成看似来自可信人物的视频，从而带来新的社交媒体诈骗风险。本项目开发一个受控演示系统，展示这类欺骗性内容如何被生成，并把演示转化为意识提升、技术评估和防范讨论。系统将结合声音生成模型、音频驱动说话头像模型、媒体预处理和来源记录机制，从静态人脸图像、声音参考和文本生成带标签的合成演示视频。项目的重点不是提供冒充工具，而是通过可控原型、四模型对比、失败案例分析和伦理边界说明，解释 AI 驱动身份转换的风险及其防范策略。",
            styles["abstract"],
        )
    )
    story.append(para("<b>关键词：</b>说话头像生成；声音克隆；社交媒体诈骗；合成媒体；防诈骗意识；负责任 AI", styles["keywords"]))

    story.append(para("1. 背景", styles["h1"]))
    story.append(
        para(
            "AI 生成的身份转换正在降低技术门槛。一个有说服力的诈骗信息不再只依赖文字；攻击者可以结合公开头像、短声音样本和生成脚本，制作一个看起来像来自熟人的视频。当用户把熟悉的脸和声音当作信任信号时，这类内容会显著增加社交媒体诈骗风险。",
            styles["body"],
        )
    )
    story.append(
        para(
            "本项目用受控演示系统研究这一风险。项目目标不是制造欺骗工具，而是说明攻击流程如何工作、技术在哪些条件下成功或失败，以及这些证据如何支持用户教育、内容验证和平台防范。项目因此包含两个部分：构建可运行的端到端原型，以及分析输出在何种条件下变得可信、脆弱或明显是合成的。",
            styles["body"],
        )
    )
    story.append(
        para(
            "已有系统提供了关键组件。Wav2Lip 关注唇形同步；Audio2Head 表示具有自然头部运动的一次性音频驱动生成路线；SadTalker 使用 3DMM 运动系数生成头部和表情；EchoMimic 提供 diffusion-style portrait animation 基线；MuseTalk 使用 latent-space inpainting 提升嘴部同步质量；Chatterbox 提供文本转语音和声音克隆能力。本项目在身份平衡的 HDTF-80x12 设置上对比 Audio2Head、SadTalker、EchoMimic 和 MuseTalk，并把这套四模型对比作为社交媒体诈骗意识提升工作流的技术评估基础。",
            styles["body"],
        )
    )

    story.append(para("2. 原创贡献与 AI 工具使用边界", styles["h1"]))
    story.append(
        para(
            "本部分明确说明项目中的学生原创设计、实现工作，以及 AI 系统和开源工具分别承担的作用。表 1 明确划分项目贡献。",
            styles["body"],
        )
    )
    data = [
        [para("<b>部分</b>", styles["small"]), para("<b>在项目中的作用</b>", styles["small"])],
        [para("自己的项目设计", styles["small"]), para("诈骗意识提升框架、端到端工作流、WebUI 结构、授权媒体采集计划、来源记录机制、对比实验设计、源条件压力分析、失败案例分析和防范讨论。", styles["small"])],
        [para("自己的实现工作", styles["small"]), para("把媒体上传、音频提取、声音生成、图像预处理、说话头像生成、参数日志和用户控制连接成可工作的原型。", styles["small"])],
        [para("AI / 开源模型", styles["small"]), para("Chatterbox 用于声音生成；Audio2Head、SadTalker、EchoMimic 和 MuseTalk 用于 talking-head generator 对比；ffmpeg 用于媒体处理；ArcFace、ECAPA-TDNN、SyncNet-style 工具用于评估。", styles["small"])],
        [para("AI 写作/编程辅助", styles["small"]), para("Codex/ChatGPT 可辅助脚本、调试、格式化和草稿撰写；最终设计选择、评估解释和提交责任仍属于学生。", styles["small"])],
    ]
    table = Table(data, colWidths=[1.4 * inch, 5.45 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "ZHBody"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(para("表 1. 项目原创工作与 AI/开源工具支持的边界。", styles["caption"]))

    story.append(para("3. Proposed Methodology", styles["h1"]))
    story.append(
        para(
            "系统是一个端到端演示与评估 pipeline。输入包括授权图片、声音/视频和文字；系统先记录来源和同意状态，再提取人脸与声音，生成目标语音，最后通过 talking-head generator 生成带标签的防诈骗意识演示。",
            styles["body"],
        )
    )
    story.append(scaled_image(PIPELINE_FIG, 6.85 * inch))
    story.append(para("图 1. 端到端演示 pipeline。采集阶段限制为授权、用户提供、用户导出或 API 允许的公开材料，不绕过登录，不抓取私人资料，不收集未经同意的个人媒体。", styles["caption"]))

    story.append(para("3.1 社交媒体媒体采集", styles["h2"]))
    story.append(
        para(
            "计划中的 Facebook/社交媒体组件只使用被允许的路径：用户提供的下载内容、用户自己的 Facebook data export，或官方/API 允许的公开页面媒体。系统不会绕过登录、不会抓取私人 profile，也不会收集未经同意的个人媒体。每个媒体项都会保存来源、媒体类型、同意状态、来源链接或导出路径，以及它是否适合做人脸或声音提取。",
            styles["body"],
        )
    )
    story.append(para("3.2 预处理与质量筛选", styles["h2"]))
    story.append(
        para(
            "系统使用 ffmpeg 从上传音频/视频中提取声音，并提供完整图像、中心裁剪和自动人脸裁剪等图像预处理方式。系统还会记录可能影响可靠性的源条件，包括人脸尺度、眼距、清晰度、姿态 proxy、嘴巴张开程度和可见遮挡。这使用 source-condition stress 的思想：平均质量可能掩盖困难源图像上的失败。",
            styles["body"],
        )
    )
    story.append(para("3.3 生成流程", styles["h2"]))
    story.append(
        para(
            "语音模块根据文本和声音参考生成目标语音，当前原型使用 Chatterbox 进行 zero-shot voice generation。说话头像评估基础比较 Audio2Head、SadTalker、EchoMimic 和 MuseTalk，这四个模型分别覆盖 audio-driven warping、3DMM-conditioned animation、diffusion-style portrait animation 和 latent-space inpainting。当前 WebUI 优先部署 SadTalker 和 MuseTalk，因为它们最适合展示整脸运动自然度和唇形精度之间的权衡。",
            styles["body"],
        )
    )

    story.append(para("3.4 评估与分析方法", styles["h2"]))
    story.append(scaled_image(EVALUATION_FIG, 6.55 * inch))
    story.append(para("图 2. 评估方法。系统同时报告平均性能与按源条件切分的结果，从而解释生成视频何时看起来可信但仍然不可靠。", styles["caption"]))

    story.append(para("4. Critical Functionalities (CF1-CF7)", styles["h1"]))
    story.append(
        para(
            "下面的 CF1-CF7 是项目的核心功能清单。它把当前原型从单纯的生成 demo，补强为一个可评估、可解释、面向防诈骗意识提升的系统。",
            styles["body"],
        )
    )
    cf_data = [
        [para("<b>ID</b>", styles["small"]), para("<b>核心功能</b>", styles["small"])],
        [para("CF1", styles["small"]), para("授权图片、音频/视频和文本输入，并记录来源、同意状态和使用状态。", styles["small"])],
        [para("CF2", styles["small"]), para("媒体提取与预处理，包括声音提取、视频帧提取、完整图像、中心裁剪、自动人脸裁剪和源质量检查。", styles["small"])],
        [para("CF3", styles["small"]), para("根据文本提示和声音参考生成目标语音，当前原型使用 Chatterbox 作为工作后端。", styles["small"])],
        [para("CF4", styles["small"]), para("根据生成语音和源人脸图像生成 talking-head 视频，WebUI 演示路径使用 SadTalker 和 MuseTalk，同时把 Audio2Head/EchoMimic 作为对比基线。", styles["small"])],
        [para("CF5", styles["small"]), para("进行受控模型对比和指标收集，包括 ArcFace 身份相似度、ECAPA-TDNN 说话人相似度、SyncNet-style 唇形同步指标和人工评价。", styles["small"])],
        [para("CF6", styles["small"]), para("分析失败案例，区分可见伪影和隐藏指标失败，并把每类失败映射到改进策略。", styles["small"])],
        [para("CF7", styles["small"]), para("提供安全和防范支持，包括合成内容标签、源质量警告、采集边界记录和面向用户的防诈骗提示。", styles["small"])],
    ]
    cf_table = Table(cf_data, colWidths=[0.65 * inch, 6.2 * inch], repeatRows=1)
    cf_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "ZHBody"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(cf_table)
    story.append(para("表 2. 项目的 CF1-CF7 核心功能。", styles["caption"]))

    story.append(para("5. Research Questions", styles["h1"]))
    story.append(
        para(
            "RQ1：如何通过一个授权的端到端 pipeline，把人脸图像、声音/视频参考和文字提示转换成带标签的 talking-head 防诈骗意识演示？",
            styles["body"],
        )
    )
    story.append(
        para(
            "RQ2：Audio2Head、SadTalker、EchoMimic 和 MuseTalk 在身份保持、唇形同步、声音自然度、视觉真实感和源条件鲁棒性上有什么差异？",
            styles["body"],
        )
    )
    story.append(
        para(
            "RQ3：哪些来源记录、质量警告、失败解释和面向用户的提示最能支持社交媒体诈骗意识提升与防范？",
            styles["body"],
        )
    )

    story.append(para("6. 对比实验", styles["h1"]))
    story.append(
        para(
            "本项目的模型对比不只限于当前 WebUI 后端。项目包含 Audio2Head、SadTalker、EchoMimic 和 MuseTalk 四个 talking-head generator 的对比，并在诈骗意识系统中继续使用同样的比较逻辑。",
            styles["body"],
        )
    )
    model_data = [
        [para("<b>模型</b>", styles["small"]), para("<b>机制代表</b>", styles["small"]), para("<b>对比意义</b>", styles["small"])],
        [para("Audio2Head", styles["small"]), para("audio-driven one-shot / warping", styles["small"]), para("用于观察可见身份崩塌和头部运动失败。", styles["small"])],
        [para("SadTalker", styles["small"]), para("3DMM-conditioned animation", styles["small"]), para("用于观察更丰富的头部和表情运动。", styles["small"])],
        [para("EchoMimic", styles["small"]), para("diffusion-style portrait animation", styles["small"]), para("用于代表 diffusion-style 生成路线和身份尾部风险。", styles["small"])],
        [para("MuseTalk", styles["small"]), para("latent-space inpainting", styles["small"]), para("用于观察高质量唇形同步和隐藏同步脆弱性。", styles["small"])],
    ]
    model_table = Table(model_data, colWidths=[1.25 * inch, 2.05 * inch, 3.55 * inch], repeatRows=1)
    model_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "ZHBody"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(model_table)
    story.append(para("表 3. 项目对比的四个 talking-head generator。", styles["caption"]))
    story.append(
        para(
            "除了模型后端对比，项目还会比较图像预处理模式、声音参考长度和源条件压力切片。图像预处理比较完整图像、中心裁剪和自动人脸裁剪；声音参考比较较短和较长的干净参考音频；源条件压力分析按小人脸尺度、低眼距、低清晰度、姿态变化和嘴巴张开程度切分输出。四模型结果显示，Audio2Head 更容易暴露可见 identity-collapse stress，而较新的模型可能保持身份可信但在 SyncNet 等隐藏同步轴上退化。",
            styles["body"],
        )
    )

    story.append(para("7. 评估指标", styles["h1"]))
    eval_data = [
        [para("<b>维度</b>", styles["small"]), para("<b>指标或方法</b>", styles["small"])],
        [para("唇形同步", styles["small"]), para("SyncNet-style score；必要时加入 1-5 分人工评分。", styles["small"])],
        [para("身份保持", styles["small"]), para("源图像与生成帧之间的 ArcFace similarity。", styles["small"])],
        [para("声音相似度", styles["small"]), para("ECAPA-TDNN speaker similarity；人工口音和自然度评分。", styles["small"])],
        [para("视觉自然度", styles["small"]), para("人工评价头部运动、表情、嘴部伪影和整体可信度。", styles["small"])],
        [para("鲁棒性", styles["small"]), para("按人脸尺度、清晰度、姿态、嘴巴张开、裁剪模式和后端模型切分结果。", styles["small"])],
        [para("安全/可用性", styles["small"]), para("来源记录完整性、同意检查、警告可见性和用户问卷。", styles["small"])],
    ]
    eval_table = Table(eval_data, colWidths=[1.55 * inch, 5.3 * inch], repeatRows=1)
    eval_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "ZHBody"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(eval_table)
    story.append(para("表 4. 评估指标。", styles["caption"]))

    story.append(para("8. 失败案例分析与改进策略", styles["h1"]))
    story.append(
        para(
            "失败分析是项目的一部分，而不是附录式补充。预期失败包括：嘴型准确但头部静止；头部运动自然但嘴部精度不足；微笑或低质量源图像导致嘴部变形；激进裁剪引起身份漂移；嘈杂声音参考降低 speaker similarity；长文本造成节奏不自然。报告会区分可见失败和隐藏失败，因为一个视频可能在视觉上可信，但在唇形同步或说话人相似度上已经退化。",
            styles["body"],
        )
    )
    story.append(
        para(
            "对应的改进策略包括：切换后端模型、调整 crop mode、降低 expression scale、使用更干净的 20-30 秒声音参考、拆分长文本，以及在源图像质量不足时向用户显示警告。四模型比较还说明，不能只用一个平均分选择模型；需要说明不同模型在哪个失败轴上更脆弱。",
            styles["body"],
        )
    )

    story.append(para("9. 伦理范围与防范重点", styles["h1"]))
    story.append(
        para(
            "本项目定位为诈骗意识提升与防范，不会作为公开冒充服务部署，也不会移除披露或警告机制。Facebook/社交媒体采集限制在授权或被允许的材料范围内。最终演示应明确标注为合成内容，用来解释风险，而不是欺骗真实用户。防范讨论包括用户教育、来源验证、平台举报、水印/披露设计，以及 AI 生成身份转换内容的警示信号。",
            styles["body"],
        )
    )

    story.append(para("10. 计划交付物", styles["h1"]))
    story.append(
        para(
            "最终提交将包括：(1) 可工作的 WebUI 演示；(2) 有文档记录的授权媒体采集和来源记录流程；(3) 生成的诈骗意识演示样例；(4) 基于 Audio2Head、SadTalker、EchoMimic 和 MuseTalk 的四模型对比结果，以及裁剪模式和声音参考设置对比；(5) 源条件压力分析和失败案例分析；(6) 简明的防范策略讨论。",
            styles["body"],
        )
    )

    story.append(para("11. 已完成工作", styles["h1"]))
    story.append(
        para(
            "下面内容集中说明 2026 年 11 月之前已经完成或已经建立的项目基础。核心系统和对比基础已经完成，后续时间线只保留人工评价、声音质量优化、结果分析和论文写作。",
            styles["body"],
        )
    )
    progress_data = [
        [para("<b>方向</b>", styles["small"]), para("<b>已完成或已建立内容</b>", styles["small"])],
        [para("系统原型", styles["small"]), para("已经建立本地 WebUI 演示路径，支持图片、音频/视频参考和文字提示输入，并生成 talking-head demo 输出。", styles["small"])],
        [para("声音模块", styles["small"]), para("已经创建 Chatterbox 环境，并验证基于文本和声音参考的语音生成流程。", styles["small"])],
        [para("头像生成模块", styles["small"]), para("已经打通 SadTalker 和 MuseTalk 作为可运行的演示后端，用于人脸与嘴部联合运动生成。", styles["small"])],
        [para("媒体流程", styles["small"]), para("已经把授权媒体流程限定为用户提供、用户导出或 API 允许的公开材料，并设计来源记录、源质量筛选、同意状态和使用状态记录。", styles["small"])],
        [para("对比基础", styles["small"]), para("已经把 Audio2Head、SadTalker、EchoMimic 和 MuseTalk 作为四模型对比基础，并将裁剪模式和源条件压力分析纳入项目。", styles["small"])],
        [para("文档与图示", styles["small"]), para("已经完成 IEEE 风格英文 proposal、中文对照版，以及端到端 pipeline 和评估流程两张图。", styles["small"])],
    ]
    progress_table = Table(progress_data, colWidths=[1.2 * inch, 5.65 * inch], repeatRows=1)
    progress_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "ZHBody"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(progress_table)
    story.append(para("表 5. 2026 年 11 月之前已经完成或建立的工作。", styles["caption"]))

    story.append(para("12. 后续时间计划", styles["h1"]))
    time_data = [
        [para("<b>阶段</b>", styles["small"]), para("<b>后续需要补充的工作</b>", styles["small"])],
        [para("2026年11月", styles["small"]), para("设计并运行人工评价，收集唇形可信度、身份一致性、视觉真实感、声音自然度和防诈骗意识效果评分。", styles["small"])],
        [para("2026年12月", styles["small"]), para("重点优化声音生成部分，包括参考音频清理、参考长度、英国口音/自然度、语速节奏，并重生成表现较弱的样例。", styles["small"])],
        [para("2027年1月", styles["small"]), para("分析人工评价和声音优化结果，整理失败案例、防范含义和伦理讨论，完成最终论文初稿。", styles["small"])],
        [para("2027年2月前", styles["small"]), para("最终完成论文、图表、对比表、失败案例分析、demo package 和提交材料。", styles["small"])],
    ]
    time_table = Table(time_data, colWidths=[1.3 * inch, 5.55 * inch], repeatRows=1)
    time_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "ZHBody"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#777777")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(time_table)
    story.append(para("表 6. 截止 2027 年 2 月前的后续项目时间计划。", styles["caption"]))

    story.append(para("13. 结论", styles["h1"]))
    story.append(
        para(
            "该项目适合作为一学年的 AI project，因为它不仅生成一个 talking-head demo，还包含模型集成、四模型对比、源条件压力分析、自动指标与人工评价、失败案例分析和负责任 AI 讨论。项目的价值在于把生成能力转化为诈骗风险解释和防范教育，而不是把能力本身作为终点。",
            styles["body"],
        )
    )

    story.append(para("参考文献", styles["h1"]))
    refs = [
        "K. R. Prajwal et al., “A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild,” arXiv:2008.10010, 2020.",
        "S. Wang et al., “Audio2Head: Audio-driven one-shot talking-head generation with natural head motion,” IJCAI, 2021.",
        "W. Zhang et al., “SadTalker: Learning Realistic 3D Motion Coefficients for Stylized Audio-Driven Single Image Talking Face Animation,” CVPR, 2023.",
        "Z. Chen et al., “EchoMimic: Lifelike Audio-Driven Portrait Animations through Editable Landmark Conditions,” arXiv:2407.08136, 2024.",
        "Y. Zhang et al., “MuseTalk: Real-Time High Quality Lip Synchronization with Latent Space Inpainting,” arXiv:2410.10122, 2024.",
        "Resemble AI, “Chatterbox TTS,” GitHub repository, 2026.",
        "J. Deng et al., “ArcFace: Additive Angular Margin Loss for Deep Face Recognition,” arXiv:1801.07698, 2018.",
        "J. S. Chung and A. Zisserman, “Out of Time: Automated Lip Sync in the Wild,” ACCV Workshops, 2016.",
    ]
    for idx, ref in enumerate(refs, 1):
        story.append(para(f"[{idx}] {ref}", styles["ref"]))

    def footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("ZHBody", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawCentredString(letter[0] / 2, 0.35 * inch, f"{doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
    print(OUT)
