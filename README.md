# XPic-AI 医学影像智能分析系统

基于 Vue 3 + Flask 的医学影像辅助诊断系统，支持 X 光片等医学影像的 AI 分析与报告生成。

## 系统架构

```
前端 (Vue 3 + TailwindCSS v4)
  ↕ HTTP API
后端 (Flask)
  ├── 主分析：通义千问 VL (qwen3.5-plus) — 独立读片诊断
  └── 备用分析：BiomedCLIP — 零样本分类（千问不可用时自动回退）
```

## 功能特性

- **影像上传**：支持拖拽/点击上传 JPG/PNG 格式医学影像，移动端支持拍照上传
- **AI 智能读片**：通义千问 VL 大模型独立阅读影像，不限于预设疾病列表
- **BiomedCLIP 备用**：本地零样本分类，覆盖 45 种常见病症，千问不可用时自动启用
- **PDF 报告下载**：生成包含诊断结论、影像所见、诊断依据、医学建议的 PDF 报告
- **Markdown 渲染**：报告内容支持粗体、换行等格式化显示

## 快速开始

### 环境要求

- Node.js ≥ 20.19.0（前端）
- Python ≥ 3.8（后端）

### 1. 启动前端

```bash
npm install
npm run dev
```

### 2. 配置并启动后端

```bash
cd backend
pip install -r requirements.txt

# 配置通义千问 API Key（推荐）
export DASHSCOPE_API_KEY=你的key

python app.py
```

后端启动后监听 `http://localhost:5001`。

> 未配置 API Key 时将使用 BiomedCLIP 本地模型（首次运行需下载 ~600MB 模型权重）。

### 3. 使用

1. 打开网页，上传一张医学影像
2. 点击「开始智能分析」
3. 等待 AI 分析完成（通常 10-30 秒）
4. 查看诊断报告，可点击「下载报告」保存 PDF

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vite 7 |
| 样式 | TailwindCSS v4 |
| 后端 | Flask 3.0 + Flask-CORS |
| 主模型 | 通义千问 VL (qwen3.5-plus)，通过 DashScope API 调用 |
| 备用模型 | BiomedCLIP (microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224)，基于 open_clip |
| PDF 生成 | fpdf2（服务端生成，支持中文） |

## 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/predict` | POST | 上传影像进行 AI 分析，返回诊断报告 JSON |
| `/download-pdf` | POST | 根据报告数据生成 PDF 文件 |
| `/health` | GET | 健康检查，返回模型状态 |

## 项目结构

```
xpic-ai/
├── src/
│   ├── App.vue                    # 主页面（上传、结果展示、下载）
│   ├── components/
│   │   ├── AnalysisResult.vue     # 诊断报告展示组件
│   │   ├── AnalysisProgress.vue   # 分析进度动画组件
│   │   └── ImageUpload.vue        # 影像上传组件
│   └── services/
│       └── aiService.js           # 后端 API 调用封装
├── backend/
│   ├── app.py                     # Flask 后端（模型加载、分析、PDF 生成）
│   └── requirements.txt           # Python 依赖
├── index.html
├── vite.config.js
└── package.json
```

## 免责声明

⚠️ 本系统由 AI 自动生成分析结果，仅供科研参考，不可替代专业医生的临床诊断。如有不适请立即就医。
