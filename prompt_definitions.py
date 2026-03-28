# prompt_definitions.py
# -*- coding: utf-8 -*-
"""
集中存放所有向大语言模型发送的提示词模板（UTF-8，无乱码）。
占位符全部使用 Python str.format 风格，并与调用处参数保持一致。
"""

# 1) 近期章节摘要（供本章写作参考）
summarize_recent_chapters_prompt = """\
你是一名严谨的长篇小说编辑。请基于最近三章的正文，提炼出“当前章节（第{novel_number}章）”应把握的关键信息，供后续写作参考。

最近三章正文（按时间顺序，可能为空）：
{combined_text}

当前章节设定：
- 章节标题：{chapter_title}
- 章节定位：{chapter_role}
- 章节用途：{chapter_purpose}
- 悬念强度：{suspense_level}
- 铺垫要点：{foreshadowing}
- 反转强度：{plot_twist_level}
- 本章概述：{chapter_summary}

下一章节（仅作连贯性参考）：
- 标题：{next_chapter_title}
- 概述：{next_chapter_summary}

请输出一段不超过 400 字的“当前章节摘要”，突出应承接与推进的线索，避免复述前文细节。只输出摘要文本。
"""

# 2) 检索关键词生成（向量库检索）
knowledge_search_prompt = """\
请根据当前章节的写作需求，生成若干组用于知识库检索的中文关键词（每组 2-5 个词，用逗号分隔）。

章节信息：
- 章节号：{chapter_number}
- 标题：{chapter_title}
- 章节定位：{chapter_role}
- 章节用途：{chapter_purpose}
- 核心人物：{characters_involved}
- 关键道具：{key_items}
- 场景地点：{scene_location}
- 铺垫要点：{foreshadowing}
- 时序/时间约束：{time_constraint}

前文摘要：
{short_summary}

用户指导（如有）：
{user_guidance}

输出要求：
- 每行一组关键词；
- 先给“设定/世界观”相关，再给“情节/事件”相关，最后给“写作技法/风格”相关；
- 不要解释或附加说明。
"""

# 3) 检索结果过滤（从向量库召回后精筛）
knowledge_filter_prompt = """\
以下是“本章信息摘要”和“检索返回的候选内容”。
请筛选出与本章写作直接相关的要点（可少量改写以提高清晰度），并按重要性由高到低合并为简明参考材料。

本章信息：
{chapter_info}

候选内容：
{retrieved_texts}

输出规则：
- 保留事实与设定，剔除模板化写作技巧陈述；
- 去重，去除与本章无关或会剧透未来的大段内容；
- 仅返回整理后的参考材料原文，不加标题。
"""

# 4) 第一章草稿提示词
first_chapter_draft_prompt = """\
参考信息：
- 小说总体设定（摘取要点）：
{novel_setting}

- 用户指导：
{user_guidance}

当前章节信息：
第{novel_number}章《{chapter_title}》
- 章节定位：{chapter_role}
- 章节用途：{chapter_purpose}
- 悬念强度：{suspense_level}
- 铺垫要点：{foreshadowing}
- 反转强度：{plot_twist_level}
- 本章概述：{chapter_summary}
- 目标字数：{word_number}
- 核心人物：{characters_involved}
- 关键道具：{key_items}
- 场景地点：{scene_location}
- 时间约束：{time_constraint}

写作要求：
1) 只输出本章完整正文，不要小标题，不要 Markdown；
2) 内容自洽、节奏清晰，适度铺垫核心矛盾；
3) 合理使用对话与描写推进情节，避免空洞总结。
"""

# 5) 非第一章草稿提示词（已在末尾追加“前章结尾段”）
next_chapter_draft_prompt = """\
参考信息：
- 全局摘要:
{global_summary}

- 用户指导:
{user_guidance}

- 角色状态:
{character_state}

当前章节信息：
第{novel_number}章《{chapter_title}》
- 章节定位: {chapter_role}
- 章节用途: {chapter_purpose}
- 悬念强度: {suspense_level}
- 铺垫要点: {foreshadowing}
- 反转强度: {plot_twist_level}
- 本章概述: {chapter_summary}
- 目标字数: {word_number}
- 核心人物: {characters_involved}
- 关键道具: {key_items}
- 场景地点: {scene_location}
- 时间约束: {time_constraint}

下一章节目录：
第{next_chapter_number}章《{next_chapter_title}》
- 章节定位: {next_chapter_role}
- 章节用途: {next_chapter_purpose}
- 悬念强度: {next_chapter_suspense_level}
- 铺垫要点: {next_chapter_foreshadowing}
- 反转强度: {next_chapter_plot_twist_level}
- 下一章概述: {next_chapter_summary}

知识库参考（如有）：
{filtered_context}

写作要求：
1) 只输出本章完整正文，不要小标题，不要 Markdown。
2) 内容连贯、节奏清晰，避免复述前文。
3) 合理使用对话与描写推进情节。

└── 前章结尾段：
{previous_chapter_excerpt}
（请承接上文继续描写）
"""

# 6) 全局摘要更新（定稿）
summary_prompt = """\
以下是新完成的章节正文：
{chapter_text}

下面是当前的全局摘要（可能为空）：
{global_summary}

请基于本章新增内容，更新全局摘要。
要求：
- 保留仍然重要的信息，并融入新的关键情节
- 语言简洁、连贯；不展开无关设想
- 总字数不超过 2000 字

只返回更新后的全局摘要，不要包含任何额外说明。
"""

# 7) 角色状态更新（定稿）
update_character_state_prompt = """\
以下是新完成的章节正文：
{chapter_text}

下面是当前的角色状态文本：
{old_state}

请更新主要角色状态，保持以下结构并覆盖或补充必要信息：
- 角色名：
  - 特征：……
  - 能力：……
  - 状态：
    - 身体状态：……
    - 心理状态：……
  - 主要角色关系：
    - [角色名]： [关系类型，如“同盟/对立/师徒/亲属”等]
  - 触发或新增的事件：
    - [事件名]： [简述及影响]

要求：
- 直接返回更新后的角色状态全文；不要标题或 Markdown
- 不删除仍然有效的信息；对过时内容以“已变化为 …”说明
- 使用简体中文，条理清晰
"""

# 8) 架构阶段提示词
core_seed_prompt = """\
请根据“主题/题材”和“体裁风格”生成故事核心种子，控制在 300-600 字：
- 主题/题材：{topic}
- 体裁风格：{genre}
- 计划篇幅：共 {number_of_chapters} 章（每章约 {word_number} 字）
- 用户指导：{user_guidance}
只返回核心种子正文。
"""

character_dynamics_prompt = """\
基于下述核心种子，梳理主要人物的动力学关系（目标、障碍、转变），500-800 字：
{core_seed}

用户指导：{user_guidance}
只返回人物动力学正文。
"""

world_building_prompt = """\
基于核心种子，构建世界观与关键设定（空间结构、历史脉络、规则系统、社会结构等），800-1200 字：
{core_seed}

用户指导：{user_guidance}
只返回世界观设定正文。
"""

plot_architecture_prompt = """\
综合核心种子、人物动力学与世界观，规划三幕式剧情结构，并标注关键转折与推进线：
- 核心种子：{core_seed}
- 人物动力学：{character_dynamics}
- 世界观设定：{world_building}
- 用户指导：{user_guidance}
只返回剧情结构正文，不要列表外说明。
"""

create_character_state_prompt = """\
请基于下述人物动力学内容，产出“初始角色状态”文档（用于后续写作追踪）：
{character_dynamics}

结构要求（每个角色一段）：
- 角色名：
  - 特征：……
  - 能力：……
  - 状态：身心状态简述
  - 主要角色关系：若干条 [对象-关系]
  - 触发或新增事件：若干条 [事件-影响]
只返回角色状态正文。
"""

# 9) 章节蓝图（目录）
chapter_blueprint_prompt = """\
请基于以下“小说总体设定/剧情结构”，输出全书章节目录，共 {number_of_chapters} 章：
{novel_architecture}

输出格式（示例）：
第1章 《标题》\n- 章节定位：……\n- 章节用途：……\n- 悬念强度：……\n- 铺垫要点：……\n- 反转强度：……\n- 本章概述：一句话提要

要求：
- 逐章给出上述要素；
- 语言简洁，避免写正文明细；
- 若已有用户指导：{user_guidance}，请酌情参考。
"""

# 10) 角色导入（供角色库解析，可选）
Character_Import_Prompt = """\
请从下面文本中提取角色信息，按如下结构输出：
- 角色名：
  - 特征：……
  - 能力：……
  - 状态：身心状态简述
  - 主要角色关系：若干条 [对象-关系]
  - 触发或新增事件：若干条 [事件-影响]

待分析文本：
{content}
"""
# 9.1) 分块生成章节蓝图（续写 n..m）
chunked_chapter_blueprint_prompt = """\
请在保持连贯的前提下，继续扩展章节目录（第{n}章至第{m}章）。

参考：
- 小说总体设定/剧情结构：
{novel_architecture}

- 已有章节目录（节选，可能为空）：
{chapter_list}

输出第{n}章至第{m}章的条目，格式同章节目录模板，每章包含：
- 章节定位
- 章节用途
- 悬念强度
- 铺垫要点
- 反转强度
- 本章概述（一句话）

要求：
- 与已给目录衔接一致，不重复已存在内容
- 语言简洁，避免写正文明细
- 若有用户指导：{user_guidance}，请酌情参考
"""
