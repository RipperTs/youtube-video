# Repository Guidelines

本项目为基于 Flask 的 YouTube 投资分析系统，服务层解耦清晰，便于扩展与维护。

## 项目结构与模块组织
- 入口：`main.py`（注册路由与启动应用）
- 配置：`config/settings.py`（读取 `.env`，含限流与外部 API 配置）
- 服务：`services/`（`*_service.py`：YouTube/Gemini/股票/图表/报告/缓存）
- 工具：`utils/`
- 前端：`web/templates/` 与 `web/static/`
- 缓存：`cache/`（分析、下载、PDF）

## 构建、测试与开发命令
- 初始化环境（推荐 `.venv`）
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `cp .env.example .env` 并填写密钥
- 本地运行：`python main.py`（默认 `http://localhost:15000`）
- 可选格式化：`black .`（如使用）

## 代码风格与命名约定
- 遵循 PEP 8，4 空格缩进；模块/函数/变量用 `snake_case`，类用 `PascalCase`
- 服务模块命名统一为 `*_service.py`，示例：`report_service.py`
- 导入顺序：标准库 → 三方库 → 本地包；必要处添加简短 docstring

## 测试规范
- 测试目录：`tests/`；文件命名：`test_*.py`
- 推荐使用 `pytest`，运行：`pytest -q`
- 覆盖重点：`services/` 纯逻辑函数与边界条件；建议覆盖率 ≥70%

## 提交与 Pull Request
- 提交信息遵循 Conventional Commits：`feat: ...`、`fix: ...`、`docs: ...`
  - 示例：`feat: add language support for content-only reports`
- PR 要求：变更目的、主要修改点、影响的接口/配置、截图（涉及模板）、自测步骤
- 关联 Issue（如有），保持 PR 小而聚焦；避免混合重构与功能改动

## 安全与配置提示
- 密钥放置 `.env`，切勿提交；`config/settings.py` 通过 `dotenv` 加载
- 生产环境关闭调试：`FLASK_DEBUG=False`
- 留意限流与配额：`MAX_VIDEO_COUNT`、`MAX_VIDEO_DURATION`
- 不在日志中输出敏感信息；下载/缓存目录应具备写权限

## 架构简述
- 路由在 `main.py` 暴露接口，业务逻辑集中于 `services/`；前后端通过模板与静态资源渲染结果
