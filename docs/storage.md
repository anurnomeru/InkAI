# 存储与数据流（Storage & Data Flow）

所有数据基于“保存路径（filepath）”组织：

- 根：`<filepath>/`
  - Novel_architecture.txt —— 小说总体架构
  - Novel_directory.txt —— 章节目录蓝图
  - global_summary.txt —— 全局剧情摘要
  - character_state.txt —— 角色状态
  - plot_arcs.txt —— 剧情要点/冲突
  - chapters/ —— 章节主目录
    - chapter_<n>.txt —— 第 n 章主稿
    - _drafts/ —— 草稿变体（不覆盖主稿）
      - chapter_<n>_<k>.txt —— 第 n 章第 k 个变体
  - vectorstore/ —— 本地向量库数据（实现细节由 vectorstore_utils 决定）

文件命名约定：
- 主稿与变体分目录，主稿始终在 chapters/；变体统一在 chapters/_drafts/，命名带两段下划线（<n>_<k>）。
- 定稿仅覆盖主稿，不处理变体；变体仅用于人工挑选与合并参考。

数据流概览：
1) 生成架构 → 写入 Novel_architecture.txt。
2) 生成目录 → 写入 Novel_directory.txt。
3) 生成草稿 → 写入 chapters/_drafts/chapter_<n>_<k>.txt（并发时 k=1..N；单次可直接显示到编辑区）。
4) 定稿 → 以当前编辑文本为准，覆盖写入 chapters/chapter_<n>.txt，并更新摘要/角色/向量库。
5) 导入知识 → 写入/更新向量库；必要时产生临时 UTF-8 文件以规避编码问题。

读写规则：
- 统一 UTF-8；`utils.py` 提供 `read_file`、`clear_file_content`、`save_string_to_txt`。
- 所有路径由 UI 右侧“保存路径”变量驱动，必填；否则流程会弹窗告警。
