# 配置体系（Configuration）

配置文件：项目根目录 `config.json`。UI 负责读/写；`config_manager.py` 提供落盘、测试与装载。

核心结构：
- `llm_configs`: `{ name: { api_key, base_url, model_name, temperature, max_tokens, timeout, interface_format } }`
- `embedding_configs`: `{ name: { api_key, base_url, model_name, retrieval_k, interface_format } }`
- `choose_configs`: `{ architecture_llm, chapter_outline_llm, final_chapter_llm, consistency_review_llm, prompt_draft_llm }`
- `other_params`: `{ topic, genre, num_chapters, word_number, filepath, chapter_num, user_guidance, characters_involved, key_items, scene_location, time_constraint, draft_variants }`
- `proxy_setting`: `{ enabled, proxy_url, proxy_port }`

要点：
- UI 的“保存配置”会同步 llm/embedding/choose/other 等所有面板变量；保存后部分运行态（如代理）即时生效。
- choose_configs 决定各步骤所用的模型槽位；领域逻辑读取时仅根据 UI 传入的选项查找。
- temperature/max_tokens/timeout 等参数遵循“用户配置为准”，不在代码中擅自覆盖。
- 测试入口（UI→按钮）：`test_llm_config()` 与 `test_embedding_config()`，用于快速验证秘钥/URL/模型通不通。
