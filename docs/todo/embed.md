# 向量功能增强方案（Embedding/RAG Roadmap）

更新时间：2026-03-28

## 1. 目标（Goals）
- 支持“章节重新生成”的稳定向量更新：向量需明确标注来源章节与版本，能够对单章增量更新、回滚或全量重建。
- 提升检索质量：在不更换底层组件前提下，引入更稳健的切片与过滤、可选混合检索与多样化召回策略。
- 保证可观测性与可维护性：重建/增量过程可随时触发、可追踪、可恢复，失败不阻塞主逻辑。

## 2. 现状与问题（As-Is）
- 现有向量库：Chroma（通过 LangChain 封装）存储，按章节整段切片后写入；更新路径：
  - finalize_chapter → `update_vector_store(adapter, new_chapter, filepath)`（若不存在则 init，否则增量 add）。
- 问题：
  - 缺少“来源章节”标注与“版本”概念，章节重写会导致旧片段与新片段混杂；
  - 检索过滤无法按章节/版本维度做约束；
  - 全量重建/回收旧片段缺少统一流程与可观测性。

## 3. 元数据与清单（Metadata & Manifest）
- 文档级元数据（每个分片/Document）：
  - `source` = `chapter_<n>`（字符串）
  - `chapter` = <int>
  - `chapter_version` = <int>（从 1 开始；每次“定稿写入向量”+1）
  - `segment_idx` = <int>（分片序号）
  - `text_sha1` = <str>（分片内容 SHA1）
  - `created_at` = `YYYY-MM-DD HH:MM:SS`
  - `active` = true/false（软删除标记，便于回滚或比对）
- 向量库清单（manifest）：`<filepath>/vectorstore/manifest.json`
  - `schema_version`：1
  - `embedding_model`、`embedding_url` 等摘要（便于判断是否需重建）
  - `chapters`: `{ "<n>": { "current_version": <int>, "last_indexed_at": <ts> } }`
  - `last_full_rebuild_at`、`notes`

说明：优先使用“单集合 + metadata 版本字段”模式；不创建多集合，避免膨胀。

## 4. 版本化与更新策略（Versioning & Update）
- 单章定稿（Finalize）更新：
  1) 读取 `manifest.chapters[n].current_version`（默认 0），`next = current + 1`；
  2) 对 `chapter_n.txt` 重新切片，生成 Documents（带 metadata：chapter=n, chapter_version=next, …）；
  3) 将旧版本 `active=false`（软删），新版本 `active=true` 插入；
  4) 更新 manifest：`current_version = next`；
  5) 可选：开启“硬删”策略（物理删除旧版本分片）以减小体积。
- 章节回滚：将指定版本 `active=true`，其余版本 `active=false`，manifest 的 `current_version` 指向目标版本。
- 全量重建：清空目录或检测为空时，从 `chapter_*.txt` 扫描重建，并在 manifest 写入 `last_full_rebuild_at`。

## 5. 切片与去重（Chunking & De-dup）
- 切片策略：
  - 保留现有句子拼接法；新增“窗口重叠（overlap 50–100 字）”可选参数，减少跨句断裂；
  - 针对对话/长句，设置最大段长 `max_length` 与最小段长 `min_length` 双阈值。
- 去重：
  - 文档级 `text_sha1` 去重；
  - 可选“近似去重”方案（MinHash/SimHash）作为后续优化，默认关闭。

## 6. 检索增强（Retrieval）
- 过滤：检索时支持 `filter={"chapter": {"$lte": n}, "active": true}`，避免使用未来章节/失效版本。
- 排序：引入 MMR（多样性最大化）或“得分+覆盖率”混排（保持实现可选）。
- 混合（可选）：语义相似度 + 关键词/BM25（需要额外轻量索引，默认关闭）。
- 动态 k：根据提示词上下文预算（tokens/长度）自适应 k。
- 排除：保留对“当前章节文本”的排除逻辑（exclude_text）。

## 7. 触发与调用（Triggers）
- finalize 时：默认增量写入并版本+1；
- “清空向量库”后：如库为空自动全量重建（已实现）；
- 手动重建：`rebuild_full_vectorstore_ui()` 可随时调用；
- 配置变更：当嵌入模型/URL 变化且检测到与 manifest 不一致时，提示“建议全量重建”。

## 8. UI 与可观测性（UI/UX & Observability）
- 顶部日志输出：索引进度（章/片段）、总片段数、耗时、失败重试计数；
- 向量按钮当前状态：已接入“清空/重建”切换；
- （可选）向量库看板：
  - 每章：版本、活跃分片数、最后索引时间；
  - 一键“仅本章重建”/“回滚到上个版本”。

## 9. 性能与健壮性（Perf & Robustness）
- 批量插入：分批次（如 200）写入，避免一次调用过大；
- 重试：沿用 `call_with_retry`；
- 原子写：manifest 采用临时文件 + 替换；
- 并发：全量重建期间禁用并发写入，或给“写锁文件”。

## 10. 与章节重生（Regenerate）联动（必做）
- 在“章节重新生成/定稿”时：
  - 为该章节分配 `chapter_version = manifest.current_version + 1`；
  - 写入新分片为 `active=true`；
  - 将该章节旧版本全部置 `active=false`（或物理删除，受配置控制 `purge_old_versions`）。
- 检索时默认只看 `active=true`，同时允许“历史版本”检索用于对比（调试用途）。

## 11. 兼容与迁移（Compat & Migration）
- 旧库无 metadata：视为 `chapter_version=1, active=true`；
- 首次使用版本化时自动生成 manifest；
- 不引入破坏性结构（继续使用单集合）。

## 12. 对应改动点（Minimal Code Changes）
- vectorstore_utils.py：
  - Document(metadata=...) 填充上述字段；
  - 新增 manifest 读写：`load_manifest/save_manifest`；
  - 新增 `mark_chapter_inactive(chapter, filepath)` 与 `index_chapter_version(adapter, chapter, version, filepath)`；
  - `get_relevant_context_from_vector_store(..., filter)` 支持 `active=true` 与章节过滤；
- finalization.py：定稿路径改为“版本+1 → 置旧为 inactive → 写新 → 更新 manifest”。
- generation_handlers.py：日志与异常透传；全量重建/单章重建触发入口（UI 已有 rebuild_full_vectorstore_ui）。

## 13. 后续增强（Optional）
- 多源索引：把 `Novel_architecture.txt`、`Novel_directory.txt`、角色库也独立分组（source=architecture/directory/role）并可控召回。
- 评分器与再排序：引入轻量规则模型（对“一致性/设定匹配/角色”打分）再排序片段。
- 存储后端可选：支持 FAISS（本地）或外部托管（向量服务），通过适配层切换。
- 体积控制：旧版本硬删、片段压缩（清洗标点/空白）、基于阈值的“精简重建”。

## 14. 里程碑（Milestones）
- M1（本任务落地优先）：
  - 为分片添加最小元数据（chapter/chapter_version/segment_idx/text_sha1/active/created_at）；
  - finalize → 版本+1、旧版本 inactive、写新、manifest 更新；
  - 检索默认 `active=true`；
- M2：
  - 单章回滚、仅本章重建；
  - UI 展示每章当前版本与活跃分片数；
- M3：
  - 混合检索、MMR、多源索引、可选后端与压缩策略。
