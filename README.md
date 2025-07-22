# YouTube 投资分析系统

## 🎯 项目概述

YouTube 投资分析系统是一个基于 Flask 和 Google Gemini AI 的智能视频分析平台，专注于对 YouTube 投资类视频进行深度分析，结合美股市场数据，生成专业的投资建议报告。

## ✨ 核心功能

### 🔍 视频分析模式

- **单视频内容分析**：深度分析投资理念和逻辑
- **单视频股票提取分析**：AI 智能提取股票信息并结合市场数据
- **手动指定股票分析**：分析特定股票与视频内容的关联度
- **批量视频分析**：支持频道视频批量分析（最多 10 个视频）

### 📊 数据集成

- **YouTube 数据**：通过 TikHub API 获取频道视频列表
- **AI 视频理解**：使用 Google Gemini 2.0 Flash 模型进行视频内容分析
- **美股数据**：集成 Tushare API 获取实时股票数据
- **图表生成**：自动生成股票走势图和技术分析图表

### 📋 报告生成

- **投资建议报告**：高盛和摩根大通风格的专业报告
- **准确性分析**：AI 智能评估投资建议的准确性
- **多格式导出**：支持 Markdown 和 PDF 格式下载

## 🚀 快速开始

### 环境要求

- Python 3.8+
- conda 环境管理工具

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd youtube-view
```

2. **创建并激活虚拟环境**
```bash
conda create -n youtube-view python=3.9
conda activate youtube-view
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置 API 密钥**

创建 `.env` 文件并配置以下 API 密钥：

```env
# Google Gemini AI API Key
GEMINI_API_KEY=your_gemini_api_key

# TikHub API Key (YouTube 数据获取)
TIKHUB_API_KEY=your_tikhub_api_key

# Tushare Token (美股数据)
TUSHARE_TOKEN=your_tushare_token

# Flask 配置
SECRET_KEY=your_secret_key
FLASK_DEBUG=True
```

5. **启动应用**
```bash
python main.py
```

应用将在 `http://localhost:15000` 启动。

## 📁 项目结构

```
youtube-view/
├── main.py                 # Flask 应用入口文件
├── requirements.txt        # Python 依赖包
├── .env                    # 环境变量配置（需要创建）
├── CLAUDE.md              # AI 助手项目说明文档
├── config/                # 配置模块
│   ├── __init__.py
│   └── settings.py        # 应用配置类
├── services/              # 核心服务模块
│   ├── __init__.py
│   ├── youtube_service.py    # YouTube 数据服务
│   ├── gemini_service.py     # Gemini AI 分析服务  
│   ├── stock_service.py      # 股票数据服务
│   ├── chart_service.py      # 图表生成服务
│   ├── report_service.py     # 报告生成服务
│   └── cache_service.py      # 缓存管理服务
├── utils/                 # 工具模块
│   └── __init__.py
├── web/                   # 前端资源
│   ├── static/           # 静态资源
│   │   ├── css/         # 样式文件
│   │   ├── js/          # JavaScript 文件
│   │   ├── images/      # 图片资源
│   │   └── charts/      # 图表文件存储
│   └── templates/        # HTML 模板
│       ├── index.html        # 首页
│       ├── analyze.html      # 单视频分析页面
│       └── batch_analyze.html # 批量分析页面
└── cache/                 # 缓存文件夹
    ├── analysis/         # 分析结果缓存
    ├── download/         # 下载文件缓存
    └── pdf/             # PDF 报告缓存
```

## 🔧 核心服务说明

### YouTube 服务 (youtube_service.py)
- 频道视频列表获取
- 视频元数据提取
- 视频有效性验证

### Gemini AI 服务 (gemini_service.py)
- 视频内容分析和理解
- 股票信息智能提取
- 批量视频分析
- 流式处理支持

### 股票数据服务 (stock_service.py)
- 美股历史数据获取
- 技术指标计算
- 股票基本信息查询

### 图表服务 (chart_service.py)
- 股票走势图生成
- 技术分析图表
- 图片文件管理

### 报告服务 (report_service.py)
- Markdown 格式报告生成
- PDF 报告生成
- 多种报告模板支持

### 缓存服务 (cache_service.py)
- 分析结果缓存管理
- 文件下载缓存
- 缓存清理机制

## 🌐 API 接口

### 核心分析接口

- `POST /analyze-stream` - 流式视频分析
- `POST /batch-analyze` - 批量视频分析
- `GET /api/channel-videos` - 获取频道视频列表
- `POST /api/batch-analyze-selected` - 分析选定视频

### 数据接口

- `GET /api/stock-data` - 获取股票数据
- `POST /api/extract-stocks-chart` - 提取股票并生成图表
- `GET /api/download-pdf/<cache_key>` - 下载 PDF 报告

### 外部 API

- `POST /api/analyze-channel-first-video` - 分析频道第一个视频（外部调用）

## ⚙️ 配置说明

### API 限制

- **Gemini API**：免费层级每天最多分析 8 小时视频内容
- **批量分析**：单次最多处理 10 个视频
- **视频要求**：仅支持 YouTube 公开视频

### 环境变量

查看 `config/settings.py` 了解所有可配置的环境变量。

## 🔒 安全注意事项

- 所有 API 密钥应存储在 `.env` 文件中，不要提交到版本控制
- 生产环境建议关闭 DEBUG 模式
- 建议配置适当的访问限制和速率限制

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持与反馈

如果您在使用过程中遇到问题或有任何建议，请：

1. 查看项目文档和 CLAUDE.md
2. 检查 GitHub Issues
3. 创建新的 Issue 描述问题

## 🎯 更新日志

查看 [GitHub Releases](../../releases) 了解最新更新和版本历史。