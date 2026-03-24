# tooltips.py
# -*- coding: utf-8 -*-

# 统一的中文提示文案（简体），仅文案调整，不影响逻辑

tooltips = {
    "api_key": "在这里填写你的 LLM API Key。若使用 OpenAI 官方接口，请前往官网控制台获取。",
    "base_url": "模型接口的 Base URL。OpenAI 官方为 https://api.openai.com/v1；本地 Ollama 通常为 http://localhost:11434/v1。",
    "interface_format": "选择所用接口的兼容格式：OpenAI / DeepSeek / Ollama / ML Studio 等。OpenAI 兼容格式指遵循 OpenAI 风格的 API。",
    "model_name": "要使用的模型名称，例如 deepseek-reasoner、gpt-4o、gpt-4o-mini 等。Ollama 需填写已下载的本地模型名称。",
    "temperature": "随机性（0-2）。数值越大输出越发散，越小越稳健。建议 0.2~1.0。",
    "max_tokens": "单次生成的最大 token 数上限。不同模型上限不同，请按需要设置。",
    "embedding_api_key": "调用 Embedding 模型所需的 API Key。",
    "embedding_interface_format": "Embedding 接口的兼容格式（如 OpenAI / Ollama）。",
    "embedding_url": "Embedding 模型的 Base URL。",
    "embedding_model_name": "Embedding 模型名，如 text-embedding-3-large。",
    "embedding_retrieval_k": "检索时返回的 Top-K 数量（越大召回越多，越慢）。",
    "topic": "小说的大致主题或主旨背景描述。",
    "genre": "小说题材类别，如都市、科幻、悬疑等。",
    "num_chapters": "期望的章节数量。",
    "word_number": "每章目标字数。",
    "filepath": "生成文件存储的根目录路径。所有 txt 与向量库等会放在此目录下。",
    "chapter_num": "当前操作的章节编号，用于生成草稿或定稿。",
    "user_guidance": "对本章/本书的写作指引或补充说明。",
    "characters_involved": "本章需要重点描写/涉及的角色清单（逗号分隔）。",
    "key_items": "本章中的关键道具/线索/物品。",
    "scene_location": "主要场景或地点。",
    "time_constraint": "时间线约束或时长限制。",
    "interface_config": "选择要使用的接口配置名称（在左侧配置区中维护）。",
    # WebDAV 相关（若页面有显示）
    "webdav_url": "WebDAV 服务器地址（以 / 结尾）。",
    "webdav_username": "WebDAV 用户名。",
    "webdav_password": "WebDAV 密码。",
}
