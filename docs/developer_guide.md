# 开发者指南（Developer Guide）

## 快速开始
- 依赖：Python 3.10+
- 安装：`pip install -r requirements.txt`
- 运行：
  - Windows：双击 `run_debug.bat` 或 `python main.py`
- 首次配置：在右侧参数面板设置保存路径、选择模型与 API Key。

## 代码结构
- `ui/*`：GUI 与交互逻辑
- `novel_generator/*`：核心生成/检索/定稿逻辑
- `*adapters.py`：外部服务适配层
- `utils.py`、`config_manager.py`：工具与配置管理
- `tests/`：示例测试（如 `tests/test_config_manager.py`）

## 约定与风格
- 文本文件统一 UTF-8；路径/命名遵循 `storage.md`
- UI 更新一律通过 `after(0, ...)` 回主线程
- 长任务请使用线程；勿在 GUI 线程阻塞网络/IO
- 不在代码中覆盖用户的温度/长度/超时配置；一切以 UI 配置为准

## 调试与日志
- UI 日志：左侧“输出日志（只读）”
- 后端日志：`app.log`
- 运行日志：`run_debug.log`（Windows 批处理运行时）

## 测试
- 配置管理：`pytest tests/test_config_manager.py`
- 建议：新增模块时至少补一条 happy path 测试

## 发布/打包（可选）
- PyInstaller 方案可参考 `main.spec`（若存在更新）
