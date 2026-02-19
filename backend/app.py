import io
import os
import datetime
import random
import base64
import json
import logging
import traceback
import torch
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import open_clip

# ── 日志配置 ──
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('xpic')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# ── 全局变量 ──
_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None

# ── 通义千问 VL API 配置 ──
QWEN_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
QWEN_API_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
QWEN_MODEL = 'qwen3.5-plus'

# ── 45 种候选疾病 ──
CANDIDATE_LABELS = [
    ("Atelectasis", "肺不张", "肺组织塌陷导致体积缩小，表现为密度增高影及纵隔移位"),
    ("Consolidation", "肺实变", "肺泡腔内充满渗出物，呈均匀致密影，可见支气管气像"),
    ("Infiltration", "肺部浸润", "肺实质内炎性渗出，表现为模糊的密度增高影"),
    ("Pneumothorax", "气胸", "胸膜腔内积气，肺组织受压萎缩"),
    ("Edema", "肺水肿", "肺间质及肺泡内液体积聚，双肺蝶翼状模糊影"),
    ("Emphysema", "肺气肿", "肺组织过度充气，透亮度增加，膈肌低平"),
    ("Fibrosis", "肺纤维化", "肺组织纤维组织增生，网状条索状影"),
    ("Pneumonia", "肺炎", "肺实质炎症，表现为斑片状或大片状密度增高影"),
    ("Lung Nodule", "肺结节", "肺内类圆形密度增高影，直径≤3cm"),
    ("Lung Mass", "肺部肿块", "肺内占位性病变，直径>3cm，边缘可不规则"),
    ("Tuberculosis", "肺结核", "结核分枝杆菌感染，好发上叶尖后段，斑点条索钙化灶"),
    ("COPD", "慢性阻塞性肺病", "气道慢性炎症导致气流受限，肺过度充气"),
    ("Bronchitis", "支气管炎", "支气管壁增厚，肺纹理增多增粗"),
    ("Lung Opacity", "肺部阴影", "泛指肺内各种密度增高影"),
    ("Cardiomegaly", "心脏增大", "心影增大，心胸比>0.5，提示心脏器质性病变"),
    ("Aortic Enlargement", "主动脉增宽", "主动脉迂曲扩张，提示动脉硬化或高血压"),
    ("Calcification", "血管钙化", "血管壁或瓣膜钙质沉着"),
    ("Pericardial Effusion", "心包积液", "心包腔内液体积聚，心影呈烧瓶样增大"),
    ("Pleural Effusion", "胸腔积液", "胸膜腔内液体积聚，肋膈角变钝消失"),
    ("Pleural Thickening", "胸膜增厚", "胸膜纤维化增厚，可呈板状致密影"),
    ("Mediastinal Widening", "纵隔增宽", "纵隔影增宽，需排除淋巴结肿大或肿瘤"),
    ("Hernia", "膈疝", "腹腔脏器经膈肌缺损突入胸腔"),
    ("Fracture", "骨折", "骨质连续性中断，可见骨折线或碎骨片"),
    ("Dislocation", "关节脱位", "关节面失去正常对合关系"),
    ("Osteoporosis", "骨质疏松", "骨密度弥漫性减低，骨皮质变薄"),
    ("Osteoarthritis", "骨关节炎", "关节间隙狭窄，骨赘形成，软骨下骨硬化"),
    ("Scoliosis", "脊柱侧弯", "脊柱偏离中线，呈C形或S形弯曲"),
    ("Spondylosis", "脊椎病", "椎体骨赘增生，椎间隙变窄"),
    ("Bone Tumor", "骨肿瘤", "骨质破坏或异常骨质增生，边界可不规则"),
    ("Osteomyelitis", "骨髓炎", "骨质破坏伴骨膜反应及软组织肿胀"),
    ("Subcutaneous Emphysema", "皮下气肿", "皮下软组织内积气，呈条状透亮影"),
    ("Foreign Body", "异物", "气道或消化道内异常致密影"),
    ("Normal", "正常", "未见明显异常表现"),
    ("ILD", "间质性肺病", "肺间质弥漫性病变，网格影、磨玻璃影"),
    ("Bronchiectasis", "支气管扩张", "支气管管腔不可逆性扩张"),
    ("Lung Abscess", "肺脓肿", "肺实质化脓性坏死，厚壁空洞伴液平"),
    ("Pulmonary Hypertension", "肺动脉高压", "肺动脉段突出，右心室增大"),
    ("Rib Fracture", "肋骨骨折", "肋骨皮质连续性中断"),
    ("Cervical Rib", "颈肋", "第七颈椎横突过长或发育为肋骨"),
    ("Spinal Compression Fracture", "脊椎压缩骨折", "椎体高度减低，楔形变"),
    ("Soft Tissue Mass", "软组织肿块", "软组织内占位性病变"),
    ("Lymphadenopathy", "淋巴结肿大", "纵隔或肺门淋巴结增大"),
    ("Pneumomediastinum", "纵隔气肿", "纵隔内积气，沿筋膜间隙分布"),
    ("Diaphragm Elevation", "膈肌抬高", "单侧或双侧膈肌位置高于正常"),
    ("Tracheal Deviation", "气管移位", "气管偏离中线，提示纵隔或胸腔病变"),
]


def get_clip_model():
    """加载 BiomedCLIP 模型（~600MB，首次自动下载）"""
    global _clip_model, _clip_preprocess, _clip_tokenizer
    if _clip_model is None:
        log.info('[BiomedCLIP] 正在加载模型 …')
        model, preprocess_train, preprocess_val = open_clip.create_model_and_transforms(
            'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
        )
        tokenizer = open_clip.get_tokenizer(
            'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
        )
        _clip_model = model.eval()
        _clip_preprocess = preprocess_val
        _clip_tokenizer = tokenizer
        log.info(f'[BiomedCLIP] 加载完成，共 {len(CANDIDATE_LABELS)} 种候选疾病。')
    return _clip_model, _clip_preprocess, _clip_tokenizer


def clip_analyze(image_bytes):
    """Layer 1: BiomedCLIP 零样本分类"""
    model, preprocess, tokenizer = get_clip_model()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_tensor = preprocess(image).unsqueeze(0)

    text_descriptions = [
        f"An X-ray showing {eng}: {desc}" for eng, chn, desc in CANDIDATE_LABELS
    ]
    text_tokens = tokenizer(text_descriptions)

    with torch.no_grad():
        img_features = model.encode_image(img_tensor)
        txt_features = model.encode_text(text_tokens)
        img_features /= img_features.norm(dim=-1, keepdim=True)
        txt_features /= txt_features.norm(dim=-1, keepdim=True)
        similarity = (img_features @ txt_features.T).squeeze(0)
        probs = similarity.softmax(dim=-1).cpu().numpy()

    ranked = sorted(
        [(CANDIDATE_LABELS[i], float(probs[i])) for i in range(len(CANDIDATE_LABELS))],
        key=lambda x: x[1], reverse=True
    )
    return ranked


def qwen_vl_analyze(image_bytes):
    """通义千问 VL 独立读片诊断"""
    import requests as req

    if not QWEN_API_KEY:
        return None

    # 压缩图片：保持清晰度（最大 2048px + JPEG 质量85）减小上传体积
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        max_size = 2048
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        compressed = buf.getvalue()
        log.info(f'[Qwen-VL] 图片压缩: {len(image_bytes)//1024}KB → {len(compressed)//1024}KB')
    except Exception:
        compressed = image_bytes  # 压缩失败则用原图

    b64_image = base64.b64encode(compressed).decode('utf-8')

    # 提示词：千问独立读片
    prompt = (
        "你是一位资深放射科医生，拥有 20 年读片经验。请直接阅读这张医学影像，做出独立、全面的诊断分析。\n\n"
        "请不限于任何预设疾病列表，从影像中观察到的所有异常表现出发，进行全面分析。\n\n"
        "请严格按以下格式输出：\n"
        "【影像所见】详细描述影像中的解剖结构、密度变化、异常表现等\n"
        "【诊断结论】给出主要诊断和鉴别诊断（不限数量）\n"
        "【诊断依据】说明做出判断的影像学依据\n"
        "【医学建议】给出具体的进一步检查或治疗建议\n"
        "【综合置信度】一个 0-100 的整数，表示你对该诊断结论的确信程度\n"
    )

    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        log.info('[Qwen-VL] 正在调用通义千问 VL API …')
        log.info(f'[Qwen-VL] URL={QWEN_API_URL} MODEL={QWEN_MODEL}')
        resp = req.post(QWEN_API_URL, json=payload, headers=headers, timeout=60)
        log.info(f'[Qwen-VL] HTTP 状态码: {resp.status_code}')
        if resp.status_code != 200:
            log.error(f'[Qwen-VL] 错误响应: {resp.text[:500]}')
        resp.raise_for_status()
        result = resp.json()
        content = result['choices'][0]['message']['content']
        log.info(f'[Qwen-VL] 报告生成完成（{len(content)} 字）')
        return content
    except Exception as e:
        log.error(f'[Qwen-VL] API 调用失败: {e}')
        log.error(traceback.format_exc())
        return None


def extract_section(text, section_name):
    """从生成文本中提取指定章节"""
    markers = [f'【{section_name}】', f'{section_name}：', f'{section_name}:',
               f'## {section_name}', f'**{section_name}**']
    for marker in markers:
        if marker in text:
            start = text.index(marker) + len(marker)
            end = len(text)
            for next_marker in ['【', '##', '\n**']:
                pos = text.find(next_marker, start + 1)
                if pos != -1 and pos < end:
                    end = pos
            result = text[start:end].strip()
            if result:
                return result
    return None


def build_template_report(clip_results):
    """当通义千问不可用时，用 BiomedCLIP 结果生成模板报告"""
    top = clip_results[:5]
    primary = top[0]
    primary_label, primary_prob = primary[0], primary[1]

    # 影像所见：始终列出 top5
    findings_parts = []
    for (eng, chn, desc), prob in top:
        findings_parts.append(f"• {chn}（{eng}）— {prob*100:.1f}%：{desc}")
    findings = "\n".join(findings_parts)

    # 诊断结论：始终给出 top1 诊断
    diagnosis = f"主要诊断：{primary_label[1]}（{primary_label[0]}）— 可能性 {primary_prob*100:.1f}%\n"
    diff_items = [f"{label[1]}（{prob*100:.1f}%）" for (label, prob) in top[1:4]]
    if diff_items:
        diagnosis += f"鉴别诊断：{'、'.join(diff_items)}"

    reasoning = (
        f"基于 BiomedCLIP 医学影像模型，对 {len(CANDIDATE_LABELS)} 种常见病症进行综合评估。\n"
        f"排名第一：{primary_label[1]}，相对可能性 {primary_prob*100:.1f}%。\n"
        f"注意：由于同时对比 {len(CANDIDATE_LABELS)} 种病症，单项概率值偏低属正常现象，应关注相对排名。"
    )
    recommendation = '本结果由AI辅助生成，仅供参考。建议将此报告交给专业医生做进一步判读。'

    return findings, diagnosis, reasoning, recommendation


@app.route('/health')
def health():
    qwen_status = '已配置' if QWEN_API_KEY else '未配置（仅用 BiomedCLIP）'
    return jsonify(
        status='ok',
        layer1='BiomedCLIP (本地)',
        layer2=f'通义千问 VL ({qwen_status})',
        diseases=len(CANDIDATE_LABELS),
    )

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """生成中文 PDF 诊断报告（含影像图片）"""
    try:
        return _generate_pdf()
    except Exception as e:
        log.error(f'[PDF] 生成失败: {e}')
        log.error(traceback.format_exc())
        return jsonify(error=f'PDF 生成失败: {str(e)}'), 500

def _generate_pdf():
    from fpdf import FPDF
    from flask import send_file
    import json as json_mod
    import tempfile

    # 接收数据：支持 multipart (带图片)、form-urlencoded 或 JSON
    if request.content_type and 'multipart' in request.content_type:
        data = json_mod.loads(request.form.get('report', '{}'))
        image_file = request.files.get('image')
    elif request.content_type and 'form-urlencoded' in request.content_type:
        data = json_mod.loads(request.form.get('report', '{}'))
        image_file = None
    else:
        data = request.get_json() or {}
        image_file = None

    if not data:
        return jsonify(error='缺少报告数据'), 400

    # 自动检测中文字体（macOS / Linux）
    import platform
    import subprocess
    font_candidates = [
        # macOS
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        # Linux 常见路径
        '/usr/share/fonts/chinese/simsun.ttc',
        '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',
        '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansSC-Regular.otf',
        # CentOS / RHEL
        '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttf',
        '/usr/share/fonts/wqy-microhei/wqy-microhei.ttf',
        '/usr/share/fonts/google-noto-cjk/NotoSansSC-Regular.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]
    # 动态搜索：用 fc-list 找任意中文字体
    if not any(os.path.exists(f) for f in font_candidates):
        try:
            result = subprocess.run(
                ['fc-list', ':lang=zh', 'file'], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split('\n'):
                path = line.split(':')[0].strip()
                if path and os.path.exists(path):
                    font_candidates.insert(0, path)
                    log.info(f'[PDF] fc-list 找到中文字体: {path}')
                    break
        except Exception:
            pass

    bold_candidates = [
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
    ]
    FONT_PATH = None
    FONT_BOLD = None
    for f in font_candidates:
        if os.path.exists(f):
            FONT_PATH = f
            break
    for f in bold_candidates:
        if os.path.exists(f):
            FONT_BOLD = f
            break
    if not FONT_PATH:
        log.error(f'[PDF] 未找到中文字体！已检查: {font_candidates}')
        return jsonify(error='服务器未安装中文字体，请运行: yum install -y wqy-zenhei-fonts'), 500
    log.info(f'[PDF] 使用字体: {FONT_PATH}')
    if not FONT_BOLD:
        FONT_BOLD = FONT_PATH  # fallback: 正常体替代粗体

    class ReportPDF(FPDF):
        def __init__(self):
            super().__init__()
            self.add_font('CN', '', FONT_PATH)
            self.add_font('CN', 'B', FONT_BOLD)

        def header(self):
            self.set_font('CN', 'B', 18)
            self.cell(0, 12, 'XPic-AI 医学影像诊断报告', new_x='LMARGIN', new_y='NEXT', align='C')
            self.set_font('CN', '', 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 6, '—— AI 智能辅助分析 ——', new_x='LMARGIN', new_y='NEXT', align='C')
            self.set_text_color(0, 0, 0)
            self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
            self.ln(6)

        def footer(self):
            self.set_y(-20)
            self.set_font('CN', '', 7)
            self.set_text_color(180, 60, 60)
            self.multi_cell(0, 4,
                '⚠ 免责声明：本报告由 AI 系统自动生成，仅供科研参考。不可替代专业医生的临床诊断。如有不适请立即就医。',
                align='C')

        def section_title(self, title):
            self.set_font('CN', 'B', 12)
            self.set_fill_color(240, 245, 255)
            self.cell(0, 9, f'  {title}', new_x='LMARGIN', new_y='NEXT', fill=True)
            self.ln(2)

        def section_body(self, text):
            self.set_font('CN', '', 10)
            self.multi_cell(0, 6, text or '暂无')
            self.ln(3)

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # ── 基本信息 ──
    pdf.set_font('CN', '', 9)
    pdf.set_text_color(100, 100, 100)
    info_items = [
        f"报告编号：{data.get('id', '-')}",
        f"分析时间：{data.get('timestamp', '-')}",
        f"置 信 度：{round(data.get('confidence', 0) * 100)}%",
    ]
    for item in info_items:
        pdf.cell(0, 5, item, new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ── 嵌入影像图片 ──
    tmp_img_path = None
    if image_file:
        try:
            img_bytes = image_file.read()
            suffix = '.png'
            if image_file.filename:
                ext = os.path.splitext(image_file.filename)[1].lower()
                if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                    suffix = ext
            tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            tmp.write(img_bytes)
            tmp.close()
            tmp_img_path = tmp.name

            pdf.section_title('影像原图')
            page_w = pdf.w - pdf.l_margin - pdf.r_margin
            # 限制图片最大高度 80mm
            pdf.image(tmp_img_path, x=pdf.l_margin + 20, w=page_w - 40)
            pdf.ln(4)
        except Exception as e:
            print(f'[PDF] 图片嵌入失败: {e}')

    # ── 各章节 ──
    pdf.section_title('诊断结论')
    pdf.set_font('CN', 'B', 11)
    pdf.multi_cell(0, 7, data.get('diagnosis', ''))
    pdf.ln(3)

    pdf.section_title('影像所见')
    pdf.section_body(data.get('findings', ''))

    pdf.section_title('诊断依据')
    pdf.section_body(data.get('reasoning', ''))

    pdf.section_title('医学建议')
    pdf.section_body(data.get('recommendation', ''))

    # 完整报告
    full_report = data.get('full_report', '')
    if full_report:
        pdf.section_title('完整 AI 报告')
        pdf.section_body(full_report)

    # ── 输出 ──
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    # 清理临时图片
    if tmp_img_path and os.path.exists(tmp_img_path):
        os.unlink(tmp_img_path)

    filename = f"XPic-AI-Report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify(error='缺少文件'), 400
    f = request.files['file']
    if not f.filename:
        return jsonify(error='文件为空'), 400

    ts = datetime.datetime.now().isoformat()
    img_bytes = f.read()

    try:
        import time
        start = time.time()

        # ── 优先：通义千问 VL 独立读片 ──
        qwen_report = None
        if QWEN_API_KEY:
            log.info(f'[分析] 调用通义千问 VL ({QWEN_MODEL}) 独立读片 …')
            qwen_report = qwen_vl_analyze(img_bytes)
            qwen_time = time.time() - start
            if qwen_report:
                log.info(f'[分析] 千问读片完成，耗时 {qwen_time:.1f}s')
            else:
                log.warning('[分析] 千问读片失败，回退到 BiomedCLIP')
        else:
            log.info('[分析] 未配置 API Key，使用 BiomedCLIP')

        # ── 回退：BiomedCLIP（仅千问不可用时）──
        clip_results = None
        if not qwen_report:
            log.info('[分析] BiomedCLIP 零样本分类 …')
            clip_results = clip_analyze(img_bytes)
            clip_time = time.time() - start
            log.info(f'[分析] BiomedCLIP 完成，耗时 {clip_time:.1f}s，Top1: {clip_results[0][0][1]} ({clip_results[0][1]*100:.1f}%)')

        total_time = time.time() - start

        # 构建响应
        if qwen_report:
            findings = extract_section(qwen_report, '影像所见') or qwen_report
            diagnosis = extract_section(qwen_report, '诊断结论') or '请见详细报告'
            reasoning = extract_section(qwen_report, '诊断依据') or ''
            recommendation = extract_section(qwen_report, '医学建议') or '请咨询专业医生'
            model_info = f'AI 智能分析 · 耗时 {total_time:.0f} 秒'

            confidence_val = 0.5
            conf_text = extract_section(qwen_report, '综合置信度')
            if conf_text:
                import re
                m = re.search(r'(\d+)', conf_text)
                if m:
                    confidence_val = min(int(m.group(1)), 99) / 100.0

            raw_data = []  # 千问模式无筛查数据
        else:
            findings, diagnosis, reasoning, recommendation = build_template_report(clip_results)
            model_info = f'AI 快速分析 · 耗时 {total_time:.1f} 秒'

            raw_top = clip_results[0][1]
            top5_sum = sum(p for _, p in clip_results[:5])
            dominance = raw_top / top5_sum if top5_sum > 0 else 0.5
            confidence_val = 0.55 + dominance * 0.40

            raw_data = [
                {"name": f"{label[1]}（{label[0]}）", "probability": round(prob, 4)}
                for (label, prob) in clip_results[:15]
            ]

        report = {
            'id': f"XP-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(100,999)}",
            'timestamp': ts,
            'scan_type': '综合智能分析',
            'model_info': model_info,
            'diagnosis': diagnosis,
            'confidence': round(confidence_val, 4),
            'findings': findings,
            'reasoning': reasoning,
            'recommendation': recommendation,
            'raw_data': raw_data,
            'model_used': 'AI 深度分析' if qwen_report else 'AI 快速分析（BiomedCLIP）',
            'full_report': qwen_report or '',
        }

        return jsonify(report)

    except Exception as exc:
        log.error(f'[分析] 出错: {exc}')
        log.error(traceback.format_exc())
        return jsonify(error=str(exc)), 500


if __name__ == '__main__':
    print(f'\n  XPic-AI 后端 · http://localhost:5001')
    if QWEN_API_KEY:
        print(f'  主模型: 通义千问 VL API（独立读片）✅')
        print(f'  备用:   BiomedCLIP（仅千问不可用时启用）')
    else:
        print(f'  主模型: BiomedCLIP 本地分析（{len(CANDIDATE_LABELS)} 种病症）')
        print(f'  提示: export DASHSCOPE_API_KEY=你的key 可启用千问 VL')
    print()

    # 仅在无 API Key 时预加载 BiomedCLIP（有千问时按需加载）
    if not QWEN_API_KEY:
        print('[启动] 预加载 BiomedCLIP …')
        get_clip_model()
    else:
        print('[启动] 千问 VL 已就绪，BiomedCLIP 按需加载')

    app.run(host='0.0.0.0', port=5001)
