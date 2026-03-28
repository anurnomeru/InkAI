# 叙事图谱（Story Graph）——目标、结果与实现方案

更新时间：2026-03-28

## 1. 背景与目标（Why）
在长篇小说中，事件、伏笔与兑现、角色目标与冲突、线索与道具之间构成复杂的因果网络。如果仅靠“章节文本 + 简要摘要”，很难保障：
- 伏笔必有兑现、因果链不断裂；
- 角色弧线得到阶段性推动；
- 主题与线索有序铺陈，不自我矛盾。

叙事图谱是把“剧情要素→图节点，因果/伏笔/阻断/矛盾→图边”进行结构化表达的基础设施，用于：
- 在生成前为模型提供“硬约束/待办”，提升连贯性；
- 在生成后自动抽取并更新图谱，产出“缺口/矛盾”的检查清单；
- 在定稿时做门禁或强提醒，确保质量不随进度下滑。

## 2. 预期结果（What）
落地后，将得到以下交付与能力：
- 文件：`<filepath>/story_graph.json`（单文件图谱，UTF-8）
- 能力：
  1) 草稿生成前：根据图谱与章节号，汇总“必须延续/兑现”的约束，注入到 `build_chapter_prompt()`；
  2) 定稿后：从本章文本抽取事件与关系，合并进图谱；
  3) 日志：把约束与检查要点输出到 UI 日志；
  4) 扩展：后续可基于该文件做可视化或高级查询（非本迭代范围）。
    5）支持全量对已经定稿的章节重新生成图谱

## 3. 数据模型（Model）
- 顶层结构
```json
{
  "version": 1,
  "nodes": [ /* Event / Clue / Goal / Payoff 等 */ ],
  "edges": [ /* 有向边：因果/阻断/伏笔-兑现/矛盾 */ ]
}
```
- 节点 Node（最小可用 Event 型）
```json
{
  "id": "ev-12",
  "type": "event",               
  "chapter": 5,
  "scene": 2,                      
  "pov": "李沉舟",                 
  "summary": "李沉舟偷到钥匙却被守卫发现",
  "goal": "取得钥匙",
  "conflict": "守卫巡逻加强",
  "outcome": "部分成功，带来追捕",
  "tension_delta": +0.2,           
  "tags": ["潜入", "钥匙"],
  "status": "resolved"            
}
```
- 边 Edge
```json
{
  "src": "ev-10",
  "dst": "ev-12",
  "type": "cause|blocks|setup|payoff|contradict",
  "weight": 0.8,
  "note": "第3章的线索导致本章行动"
}
```
- 其他常见节点与属性（可增量支持）
  - `type: clue` 线索；`type: goal` 角色目标；`type: payoff` 兑现；
  - 节点可带 `due_by`（应在第 N 章前兑现），用于伏笔逾期检测。

## 4. 文件与路径（Storage）
- 主文件：`<filepath>/story_graph.json`
- 写入策略：读取→合并→原子写（先写临时文件再替换），避免并发损坏。
- 版本兼容：保留 `version`，后续迁移可做轻量适配。

## 5. 接入流程（How）
### 5.1 生成前（Pre-Generate）
- 入口：`build_chapter_prompt()`
- 步骤：
  1) 读取 `story_graph.json`；
  2) 根据 `chapter = 当前章节` 收集：
     - 未兑现且 `due_by <= chapter` 的 `setup`；
     - 上一章产生、状态为 `pending` 的事件/目标；
     - 关键因果链的“下一步”提示（如上一链的 `dst` 为空）。
  3) 生成“本章必须处理/至少回应”的约束清单，插入提示词专属段落，例如：
```
【叙事约束】
- 伏笔(#s-07) 应在本章前后兑现或明确延后；
- 事件链 ev-10 → ? 的空缺需推进；
- POV=李沉舟，不可泄露其他角色未得知信息。
```

### 5.2 生成后（Post-Generate）
- 入口：生成草稿完成后的回调（见 `ui/generation_handlers.py` 中相应线程任务末尾）。
- 步骤：
  1) 通过 LLM 抽取“事件/关系”JSON（定义一个稳健的提取 prompt），解析失败则回退启发式；
  2) 为新节点分配全局唯一 `id`（如 `ev-<auto>`），并与旧图谱合并（去重规则：`chapter+scene+summary` 相似度高时合并）；
  3) 写回 `story_graph.json`（原子写）。

### 5.3 定稿前（Pre-Finalize Check）
- 入口：`finalize_chapter_ui()` 开始处或保存主稿后；
- 检查项：
  - 伏笔逾期：存在 `setup(due_by<=chapter)` 且未被 `payoff` 连接；
  - 因果断链：上一章 `cause` 指向的 `dst` 仍为空；
  - 知识边界：本章 POV 报告跨 POV 的知识泄露；
  - 时间矛盾：同一线索在时间上前后不一致（基础规则+LLM 二次确认）。
- 结果：给出【阻断/警告】清单；策略可配（仅警告或阻断定稿）。

## 6. 模块与接口（API）
新增 `novel_generator/story_graph.py`：
- `load_story_graph(filepath) -> dict`
- `save_story_graph(graph: dict, filepath) -> None`（原子写）
- `collect_constraints(graph: dict, chapter: int) -> list[dict]`
- `extract_events_via_llm(text: str, chapter: int, adapter) -> dict`（返回 {nodes, edges}）
- `merge_graph(graph: dict, delta: dict) -> dict`
- `check_consistency(graph: dict, chapter: int) -> list[Issue]`
- `format_constraints_for_prompt(list) -> str`
- `format_issues_for_log(list) -> str`

LLM 抽取示例（要求 JSON 严格模式）：
```json
{
  "nodes": [
    {"type":"event","chapter":5,"scene":2,"pov":"李沉舟","summary":"……","goal":"……","conflict":"……","outcome":"……","tension_delta":0.2,"tags":["钥匙"]}
  ],
  "edges": [
    {"src":"<auto>ev_prev","dst":"<auto>ev_curr","type":"cause","weight":0.6}
  ]
}
```

## 7. UI 与用户体验（UX）
- 第一阶段不新增 Tab：
  - 约束与检查清单写入日志区（简洁版）；
  - 检查失败可选择“继续/取消”。
- 第二阶段（可选）：
  - 新增“叙事图谱”Tab，展示未兑现列表与因果链邻接视图，支持点击跳转到章节。

## 8. 迁移与补全（Backfill）
- 提供批处理命令：从 `chapters/` 逐章抽取事件，构建初始图谱：
  - 入口：`tools/backfill_story_graph.py`（可后续加入）
  - 策略：优先 LLM 抽取，失败回退启发式（基于“动词+受事”与段落标题）

## 9. 性能与健壮性（Perf & Robustness）
- 文件体量小（JSON），读写为 O(n) 简单操作；
- 原子写避免并发损坏；
- 所有异常吞吐到 UI 日志，不阻塞主路径；
- 在无图谱文件时自动创建骨架：`{"version":1,"nodes":[],"edges":[]}`。

## 10. 测试计划（QA）
- 单元测试：
  - 合并规则（去重/新增/更新）；
  - 伏笔逾期、因果断链检测；
  - 约束字符串格式化与提示词注入；
- 集成测试：
  - 生成→抽取→合并→检查的端到端流程；
  - 在异常 JSON 时的回退路径（启发式解析）。

## 11. 里程碑（Milestones）
- M1（本次）：读写 + 约束注入 + 抽取合并 + 检查→仅警告；
- M2：定稿门禁 + 批量补全工具 + UI 未兑现列表；
- M3：可视化 Tab + 因果路径追踪 + 与角色弧线/母题联动。
