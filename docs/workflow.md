# 生成流水线（Workflow）

整体流程分四步（UI 左侧 Step 按钮）：

1) 生成架构（Architecture）
   - 入口：`generate_novel_architecture_ui()`
   - 读取：主题/类型/章节数/每章字数/用户引导等
   - 调用：`novel_generator.Novel_architecture_generate()`
   - 写入：`<filepath>/Novel_architecture.txt`

2) 生成目录（Chapter Blueprint）
   - 入口：`generate_chapter_blueprint_ui()`
   - 读取：章节数、用户引导
   - 调用：`novel_generator.Chapter_blueprint_generate()`
   - 写入：`<filepath>/Novel_directory.txt`

3) 生成草稿（Chapter Draft）
   - 入口：`generate_chapter_draft_ui()`
   - 读取：章节号/每章字数/用户引导/人物要素/关键物件/场景/时间限制、Embedding 配置
   - 提示词：由 `build_chapter_prompt()` 组装，融合蓝图、前文摘要、向量检索等
   - 调用：`novel_generator.generate_chapter_draft()`
   - 落盘：并发时写入 `_drafts/` 作为变体；也可直接加载编辑框

4) 定稿（Finalize）
   - 入口：`finalize_chapter_ui()`
   - 文本源：当前编辑框内容（不区分来自主稿或变体）
   - 写入：覆盖 `chapters/chapter_<n>.txt`
   - 后处理：更新全局摘要、角色状态、向量库

辅助流程：
- 一致性审校：`do_consistency_check()` → `consistency_checker.check_consistency()`
- 知识导入：`import_knowledge_handler()` → `import_knowledge_file()`
- 批量生成：`generate_batch_ui()`
