# 适配层设计（Adapters）

## LLM 适配（llm_adapters.py）
- 目标：隐藏不同厂商/接口的差异，提供统一的 `create_llm_adapter()` 输出对象，具备 `invoke(prompt)` 或等价方法。
- 参数：`interface_format`、`base_url`、`model_name`、`api_key`、`temperature`、`max_tokens`、`timeout`。
- 规范：不在适配层修改“上层决定”的温度/长度，仅负责映射字段与异常转义。

## Embedding 适配（embedding_adapters.py）
- 提供统一的嵌入生成与检索参数封装；`retrieval_k` 控制召回条数。
- 与 `vectorstore_utils.py` 协同：生成/更新向量库，检索召回文本供提示词拼装。

## 一致性与测试
- UI “测试配置”按钮直连 `config_manager.py` 的 `test_llm_config()`/`test_embedding_config()`，通过适配器发起一次最小请求验证可用性。
