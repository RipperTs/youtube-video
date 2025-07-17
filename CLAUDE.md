# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于Flask框架的YouTube视频分析处理项目，用于通过Gemini模型对YouTube视频进行理解分析，然后将分析结果与指定时间段的美股股市数据进行对比分析，最终生成投资建议报告。项目采用前后端一体的架构，前端页面位于web目录下。

## 核心功能架构

1. **YouTube视频获取**：
   - 支持单个视频分析
   - 支持YouTube频道批量视频获取（最多10个视频）
   - 使用TikHub API获取频道视频列表

2. **Gemini模型分析**：
   - 通过Gemini 2.0 Flash模型分析视频内容
   - 支持视频转写和视觉描述
   - 免费层级每天限制8小时视频

3. **美股数据集成**：
   - 使用Tushare API获取美股历史数据
   - 支持指定日期范围的股票数据查询
   - 包含开盘价、收盘价、成交量等完整市场数据

4. **报告生成**：
   - 形成高盛和摩根大通风格的投资建议报告
   - 结合视频内容和股市数据的对比分析

## 环境设置

```bash
# 安装依赖
pip install -r requirements.txt

# 或者使用虚拟环境
source .venv/bin/activate  # 项目依赖包位于.venv目录
pip install -r requirements.txt
```

## 运行命令

```bash
# 启动Flask开发服务器
python main.py

# 或者使用Flask命令
flask run
```

## API配置要求

- **Gemini API Key**: 需要配置Google Gemini API密钥
- **TikHub API Key**: 用于获取YouTube频道视频列表
- **Tushare Token**: 用于获取美股数据

## 开发注意事项

- main.py为Flask应用入口文件，需要实现核心业务逻辑和路由
- 前端静态文件和模板放置在web目录下
- 项目仅有requests依赖，需要添加Flask及其他依赖包（如flask、google-generativeai、tushare等）
- 注意Gemini API的使用限制：免费层级每天8小时视频，2.5之前的模型每次只能处理1个视频
- YouTube视频必须为公开视频才能被API处理

## 项目结构

```
youtube-view/
├── main.py              # Flask应用入口
├── requirements.txt     # Python依赖
├── web/                 # 前端资源目录
│   ├── static/         # 静态文件(CSS, JS, 图片)
│   └── templates/      # HTML模板文件
└── CLAUDE.md           # 项目文档
```

## 技术栈

- **后端**: Python 3.x + Flask框架
- **前端**: HTML/CSS/JavaScript (位于web目录)
- **API集成**:
  - Google Gemini API (视频分析)
  - TikHub API (YouTube数据获取)
  - Tushare API (美股数据)
- **HTTP客户端**: requests