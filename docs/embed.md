# 向量（Embedding）设计与使用说明

本说明解释当前项目内“向量库”的作用、结构、触发时机、UI交互与日志、以及相关配置与测试，帮助你理解什么时候会用到它、如何重建/清空，以及后续可以扩展的方向。

## 概述
- 目标：把“章节文本（以及可扩展的知识片段）”切分成小段并向量化，存入本地 Chroma 向量库，供生成下一章时检索相关内容，减少设定冲突、提升连贯性。
- 存储位置：`<保存路径>/vectorstore`，使用 Chroma 持久化，集合名固定为 `novel_collection`。
- 管理文件：`<保存路径>/vectorstore/manifest.json` 记录每个章节的 `current_version`，用于标识“当前有效版本”。

## 数据模型
- 文档结构（章节片段）
  - `page_content`: 文本片段内容（默认按约 500 字拼句切段）。
  - `metadata`:
    - `chapter`: 章节号（int）。
    - `chapter_version`: 该章当前版本号（int）。
    - `segment_idx`: 片段在该章内的序号（int）。
    - `active`: 是否参与检索（bool，当前恒为 `True`）。
- 清单（manifest.json）
  - 结构：`{"schema_version": 1, "chapters": {"<chapter>": {"current_version": <int>}, ...}}`
  - 作用：记录每章的最新版本号。当前实现仅保留“当前版本”的片段；旧版本不在向量库中保留，后续如需“按版本检索”可基于 manifest 扩展回溯逻辑。

## 向量库在什么时候起作用
- 章节生成（最重要的使用点）
  - 位置：`novel_generator/chapter.py::build_chapter_prompt`
  - 流程：
    1) 基于章节信息生成“检索关键词”（通过 LLM）。
    2) 对每组关键词调用 `get_relevant_context_from_vector_store(...)` 从向量库检索相似片段。
    3) 将检索结果做规则处理/过滤后，拼入最终提示词，辅助生成当前章节草稿。
  - 检索策略（见下文“检索细节”）。

- 章节定稿（入库/更新向量）
  - 位置：`novel_generator/finalization.py::finalize_chapter`
  - 行为：调用 `index_chapter_version(...)`
    - 先删除该章旧片段（硬删除）。
    - 重新切片并写入当前文本，`chapter_version` 自动+1，并更新 manifest。

- 知识文件导入（可选）
  - 位置：`novel_generator/knowledge.py::import_knowledge_file`
  - 行为：把外部知识文本切段后写入同一 Chroma 集合（目前未添加章节元数据）。
  - 说明：当前默认检索对章节片段设置了 `filter={'active': True}`，而知识片段未带该字段，默认不会被检索返回；后续若需要混合检索，可在导入时补充 `metadata.active=True` 或放宽检索过滤条件（见“未来扩展”）。

## 检索细节（相似度搜索）
- 调用：`get_relevant_context_from_vector_store(embedding_adapter, query, filepath, k, exclude_text=None, chapter_lte=None)`
- 过滤：
  - 固定 `active=True`，仅返回标记为有效的片段（即章节片段）。
  - 若传入 `chapter_lte`，仅检索“章节号 ≤ chapter_lte”的片段，避免引用“未来章节”的信息（例如生成第 N 章时限制为 ≤ N-1）。
  - `exclude_text`：用于排除与当前章节全文完全匹配的片段，避免“拿自己当上下文”。
- 召回数量：`k`（来自 UI 配置 `retrieval_k`），会根据向量库总量进行保护下限/上限。
- 返回格式：按相关度拼接为一段字符串，最长 2000 字（超出则截断）。

## 切片与入库
- 切片：`split_text_for_vectorstore(text, max_length=500)`
  - 先按句（NLTK 或正则）聚合，再按长度拼句，得到约 500 字的片段。
- 入库：
  - 首次/初始化：创建 Chroma 存储并写入。
  - 更新：`index_chapter_version` 会先删除该章旧片段，再写入新片段，最后更新 manifest 的 `current_version`。

## 清空/重建与 UI 交互
- 清空向量库
  - 入口：主界面右侧与“章节管理”顶栏各一个按钮，联动切换；清空后按钮变为“重建向量库”。
  - 行为：删除 `<保存路径>/vectorstore` 整个目录；不会自动重建。
  - 适用：更换 Embedding 服务/模型后，希望彻底重算；或存储损坏、需要重置。
- 全量重建
  - 入口：清空后出现“重建向量库”。
  - 行为：扫描 `<保存路径>/chapters` 下的 `chapter_*.txt`，按章节号排序，逐章切片并写入，统一标记为 `chapter_version=1`，然后生成 manifest。
  - 保护：若库不为空则跳过（避免误操作覆盖）。

## 日志与可观测性
- 界面日志（progress_cb 直达 UI）与文件日志（`app.log`）同步输出：
  - 清空：目标路径、预删除统计、耗时、异常。
  - 重建：
    - [重建] 目标向量库: <dir>
    - [重建] 章节目录: <chapters>
    - [切片] 第X章 → 段数=N 累计=M
    - [Chroma] persist=... collection=novel_collection 首批=K 追加=R
    - [向量] 已写入全部文档，共 T 段
    - [向量] manifest 已更新
    - [完成] 章节=C 分片=T 路径=<dir>

## 配置与依赖
- 配置入口：主界面“Embedding/向量设置”，对应 `config.json` 中 `embedding_configs`：
  - `interface_format`：服务类型（如 OpenAI/SiliconFlow 等）。
  - `base_url`、`api_key`、`model_name`：向量模型访问参数（例如 `Qwen/Qwen3-Embedding-8B`）。
  - `retrieval_k`：每次检索返回的片段数量上限。
- 运行依赖：`langchain-chroma`、`chromadb` 等；Windows 下默认使用本地持久化目录。

## 与“定稿状态”的关系
- 当你在 UI 中对某章“定稿”时：
  - 会调用 `finalize_chapter`，自动把该章最新文本写入向量库（删除旧片段、版本号+1、更新 manifest）。
  - 这保证了后续章节的检索上下文总是基于“已定稿”的内容。

## 典型问题与建议
- “重建卡住/无结果”：
  - 检查 Embedding 服务连通性/密钥是否正确；UI 日志会打印 `IF/MODEL/URL`；同时查看 `app.log`。
- “换了模型想全量更新”：
  - 清空 → 重建。重建后按钮会自动恢复为“清空向量库”。
- “想把导入的知识也用于检索”：
  - 现状：知识片段没有 `active=True`，默认检索不到。
  - 方案 A：导入时为知识片段添加 `metadata={'active': True, 'source': 'knowledge'}`。
  - 方案 B：检索放宽过滤条件，允许 `active` 缺省时也返回；并在上层通过 `source` 字段做二次过滤。

## 测试与质量保障
- 单元测试（已通过）：
  - manifest 版本递增与一致性（重建/再入库后 `current_version` 正确）。
  - 检索仅返回“有效且不超前章节”的片段。
- 性能：重建时先写入首批 200 段再追加，可避免初始化阶段大批量写入导致的阻塞；如需更细粒度进度，可按批（例如 500 段/批）追加并打印进度。

## 小结
- 向量库的核心价值：把“已定稿的既有内容”结构化地变成“可检索的上下文”，在生成新章节时即取即用，杜绝前后矛盾、细节遗失。
- 操作心智模型：
  - 写作推进 → 检索既有上下文（自动）。
  - 章节定稿 → 入库更新（自动）。
  - 配置重大变更/库损坏 → 清空后手动重建（手动）。
