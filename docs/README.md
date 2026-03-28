# 项目设计总览（Overview）

本索引汇总本项目（AI Novel Generator）的整体设计文档，帮助开发者、贡献者和使用者快速理解系统结构与关键流程。

- architecture.md —— 顶层架构与模块边界
- storage.md —— 存储与文件命名、数据流
- configuration.md —— 配置体系与 schema
- workflow.md —— 生成流水线（架构→目录→草稿→定稿）
- ui.md —— UI 设计与交互联动
- adapters.md —— LLM/Embedding 适配层
- prompts.md —— 提示词构建与知识检索/过滤
- threading.md —— 线程模型、UI 安全与并发
- error_handling.md —— 日志、异常与健壮性
- i18n.md —— 国际化策略
- developer_guide.md —— 开发者指南（运行、调试、测试、风格）
- future.md —— 后续演进方向

阅读顺序建议：Overview → Architecture → Workflow → Storage → Configuration → UI → Adapters → Prompts → Threading → Error Handling → i18n → Developer Guide → Future。
