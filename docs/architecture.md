# 顶层架构（Architecture）

系统采用“前端 UI（CustomTkinter） + 领域逻辑（novel_generator/*）+ 适配层（*adapters.py）+ 工具层（utils/config）”的分层：

- UI 层（ui/*）
  - main_window.py：应用入口 GUI 类 `NovelGeneratorGUI`，负责 TabView 布局、变量初始化、事件绑定、日志/异常派发、与配置持久化的粘合。
  - main_tab.py：主功能区（左侧编辑 + 步骤按钮 + Draft 变体 + 日志）。
  - generation_handlers.py：各生成流程的 UI 侧入口（线程化执行，调用领域逻辑）。
  - 其他 Tab：setting_tab.py、directory_tab.py、character_tab.py、summary_tab.py、chapters_tab.py、novel_params_tab.py、role_library.py 等，分别对应不同资料的查看/编辑与保存。
  - i18n/menus/helpers：i18n（ui/i18n.py + locales）、上下文菜单、键盘快捷键等。

- 领域逻辑层（novel_generator/*）
  - architecture.py：生成小说总体架构（设定/世界观等）。
  - blueprint.py：生成章节目录/蓝图（章节标题、目的、悬念/伏笔等元信息）。
  - chapter.py：构建章节提示词、拉取知识、生成草稿、并负责将结果写入章节文件。
  - finalization.py：定稿流程（基于当前编辑文本产出最终章节，并更新全局状态/向量库）。
  - knowledge.py / vectorstore_utils.py：知识库导入、向量检索、过滤与上下文组织。
  - common.py：通用调用与清理规则。

- 适配层
  - llm_adapters.py：统一封装不同接口形态（OpenAI、兼容 OpenAI、其他供应商）的文本生成。
  - embedding_adapters.py：统一封装 Embedding 服务调用与参数（base_url、model、retrieval_k 等）。

- 工具与配置
  - utils.py：文件读写（UTF-8）、覆盖/清空写入、追加文本。
  - config_manager.py：config.json 的加载/保存、配置测试；UI 的“保存配置”按钮最终落到这里。
  - consistency_checker.py：一致性审校。

关键设计思想：
- 文件即数据模型：所有产物（蓝图、章节、摘要、角色状态、知识库等）落盘到用户指定目录，绕开数据库依赖。
- 单一真相源（SSOT）：章节号与保存路径驱动 UI 与文件联动；UI 仅做展示与触发，业务依据文件状态决定。
- 适配隔离：供应商/接口差异被适配层吸收，上层仅依赖统一 API；便于替换与并行测试。
- 线程化 UI 调用：所有长耗时操作在线程中运行，UI 更新通过 `after(0, ...)` 回主线程，确保界面无阻塞。
