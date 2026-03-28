# UI 设计与交互（UI Design）

主界面采用 `CTkTabview` 分区，左侧“Main Functions”聚合日常创作操作，右侧为参数与配置。

- 左侧（Main Functions）
  - Header 行：
    - 标签：`本章内容（可编辑） 字数：{n}`（动态更新字数）
    - 按钮：`保存草稿`（贴右侧，支持 Ctrl+S）
  - 编辑框：`self.chapter_result`（可编辑）
  - Step 按钮行：Step1 生成架构 / Step2 生成目录 / Step3 生成草稿 / Step4 定稿 / 批量生成
  - Draft 变体区：
    - 下拉：`Draft Variants:`（列出主稿和所有变体）
    - 按钮：`Refresh Variants`（重载列表）
  - 日志：只读文本框（`self.log_text`），通过 `safe_log()` 线程安全写入

- 右侧（参数与配置）
  - novel_params_tab：主题/类型/章节数/每章字数/保存路径/章节号/用户引导/人物要素/关键物件/场景/时间
  - config_tab：LLM/Embedding 接口参数、选择的模型槽位、代理等
  - setting/directory/character/summary/chapters：分别编辑各资料并“保存修改”

- 联动规则
  - 更改“保存路径”或“章节号”会触发：刷新 Draft Variants 列表→优先加载主稿，否则加载最新变体→展示到编辑框
  - 选择下拉项会立即加载对应文本到编辑框（不自动保存）

- 键鼠快捷
  - Ctrl+S：保存当前编辑文本为主稿
  - 文本框支持常见编辑快捷键；右键菜单见 `TextWidgetContextMenu`
