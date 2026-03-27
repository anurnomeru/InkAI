# 核心设计：章节与草稿变体联动（Core Design）

本文件阐述项目在“章节号 ↔ 草稿（主稿/变体）”联动、启动默认行为、并发草稿与定稿流程、提示词上下文、配置与日志等方面的核心设计与约定。

## 目标（Goals）
- 启动即加载“最新章节”的主稿或变体，减少手动切换成本。
- “章节号”输入框与草稿展示强联动：改章节号 → 草稿下拉/Draft Variants 与编辑区同步刷新。
- 支持并发生成多个草稿变体，互不覆盖主稿；定稿只写入主稿文件。
- 仅文件系统存储，不使用数据库；所有路径/文件命名稳定可依赖。

## 目录与命名（Storage Layout & Naming）
- 基础保存路径：`<filepath>`（由 UI 配置）。
- 主稿目录：`<filepath>/chapters/`
  - 主稿文件：`chapter_<n>.txt`（仅单下划线）。
- 草稿变体目录：`<filepath>/chapters/_drafts/`
  - 变体文件：`chapter_<n>_<k>.txt`（n=章节号，k=变体序号，从 1 递增）。
- 其他资料（如人物/总结/蓝图/向量库等）在各自子目录，互不影响上述命名。

约定：
- 变体与主稿放在不同目录，天然隔离；无需清理历史变体。
- 定稿始终写回主稿 `chapter_<n>.txt`，不直接覆盖变体。

## 启动默认行为（Startup Defaults）
- 启动后扫描 `<filepath>/chapters/`，找到最大的 `chapter_<n>.txt`，将“章节号”自动设置为该 n。
- 设置章节号后，自动执行联动刷新（见下一节）。
- 若不存在主稿文件，则不改动“章节号”。
- 其他默认值：
  - “章节数（num_chapters）”默认 1（用作大纲/预期章节总数的参数）。
  - “每章字数（word_number）”默认 10000。
  - “Draft Variant Count”（并发草稿数）默认 3（仍可手动修改）。

## 联动规则（Linkages）
- 章节号变化（或保存路径变化）会触发：
  1) 刷新 Draft Variants 下拉：
     - 列表包含“主稿文件 + 该章节的所有变体（排序后追加）”。
  2) 选中默认项并加载文本到编辑框：
     - 优先主稿 `chapter_<n>.txt`；若主稿不存在，则选“最新变体”（文件名排序的最后一项）。
  3) 编辑框始终展示当前选择（主稿或变体）的内容。
- 变体下拉选择变化 → 立即加载对应文本到编辑框。
- 联动涉及的核心方法（ui/main_window.py）：
  - `_apply_latest_chapter_on_start()`：启动时选择最新章节并触发联动。
  - `_on_chapter_num_changed()`：章节号变更的统一入口，刷新下拉与编辑框。
  - `_on_filepath_changed()`：保存路径变更时重新计算最新章节并联动。
  - `refresh_draft_variants_list()`：生成“主稿 + 变体”的下拉列表。
  - `on_draft_variant_selected(value)`：加载所选文本到编辑框。

UI 文字与兼容：
- 为避免中文字体缺失显示“????”，关键控件使用英文常量：
  - 标签：`Draft Variants:`
  - 按钮：`Refresh Variants`
  - 参数项：`Draft Variant Count`

## 并发草稿（Concurrent Drafts）
- “生成草稿”允许并发生成 N 个变体（默认 3）：
  - 变体统一写入 `_drafts/` 子目录，不覆盖主稿。
  - 完成后刷新 Draft Variants 列表，便于快速挑选预览。
- 设计上并发仅影响变体数量与写入文件，LLM 请求参数完全“跟随”UI 配置（不私自修改）。

## 生成提示词与上下文（Prompt & Context）
- 构建章节草稿提示词时，末尾附加上一章“结尾三段（按换行划分）或≥200字”的片段，并追加固定语：“（请承接上文继续描写）”。
- 向量检索排除当前章节的“废稿/历史草稿”文本，避免对本次生成造成干扰（即检索不使用当前章节文本）。
- 字符编码统一 UTF-8，避免提示词出现乱码。

## 定稿流程（Finalize）
- 定稿始终以“当前编辑框内容”为准（无论来源是主稿、变体，还是人工编辑过）。
- 写入目标：`<filepath>/chapters/chapter_<n>.txt`。
- 定稿后可触发：
  - 更新全局总结/人物状态（如有启用）。
  - 更新向量库（分句切分：NLTK 存在则用 punkt；否则回退正则切分）。

## 配置与日志（Config & Logging）
- 配置文件：`config.json`
  - 包含 `llm_configs`、`embedding_configs`、`other_params` 等；提供“保存配置”按钮统一落盘。
  - 各步骤严格“读取并跟随”用户配置，特别是 `temperature` 之类参数；不会在代码中擅自覆盖。
- 调用日志：每次 LLM 调用前打印 INTENT 行（适配器、base_url、model、temperature、max_tokens、timeout），输出到“输出日志（只读）”。

## 错误与边界（Errors & Edge Cases）
- 若当前章节既无主稿也无变体，下拉为空并清空选择；编辑框不自动写入。
- 若保存路径为空或不可用，联动不执行；待路径有效后由 `_on_filepath_changed()` 重新计算。
- 模型特性限制（如某些模型必须 `temperature=1`），由适配器报错时在 UI 提示；仍以用户配置为准（UI 中应设为 1）。

## 为何这样设计（Rationale）
- 变体与主稿分目录，避免误覆盖；同时保留探索性草稿，利于对比挑选。
- 启动即定位“最新章节”，符合大多数连续创作场景的直觉；编辑效率更高。
- 章节号是“单一真相源（SSOT）”，联动下拉与编辑框，消除多处状态不一致问题。
- 提示词承接上一章末尾与检索排除当前草稿，提升连贯性并降低“自污染”。

## 后续可扩展（Future Work）
- Draft Variants 下拉增加“主稿/变体”分组与时间戳显示。
- 变体对比视图（diff）与快速合并工具。
- 可选策略：优先显示“最新变体”而非主稿（提供配置项切换）。

## 实现细节（Implementation Notes）
- 生成草稿时先弹出可编辑提示词对话框；确认后读取 Draft Variant Count。
- 当计数 > 1：并发创建 N 个 worker（Python threading），分别请求 LLM 并将结果写入 <filepath>/chapters/_drafts/chapter_<n>_<k>.txt。
- 并发完成后：
  - 输出日志包含：开始并发生成 {N} 个草稿版本...、OK Variant k saved/FAIL Variant k failed。
  - 刷新 Draft Variants 下拉，默认选最新项，并将其加载到编辑框。
- 当计数 = 1：按原有单次生成流程，直接把结果加载到编辑框。
- 所有请求参数（接口、模型、温度、超时、max_tokens）严格跟随 UI 与当前配置，不做代码侧覆盖。

