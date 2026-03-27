# config_manager.py
# -*- coding: utf-8 -*-
import json
import os
import time
from typing import Dict, Tuple, Any

from llm_adapters import create_llm_adapter
from embedding_adapters import create_embedding_adapter

# -------- 默认配置（作为自愈基线） --------
DEFAULT_LLM_ITEM = {
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 8192,
    "timeout": 600,
    "interface_format": "OpenAI",
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "last_interface_format": "OpenAI",
    "last_embedding_interface_format": "OpenAI",
    "llm_configs": {
        # 至少有一个可用项，供 UI 直接取用
        "Default": dict(DEFAULT_LLM_ITEM),
    },
    "embedding_configs": {
        "OpenAI": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": "text-embedding-ada-002",
            "retrieval_k": 4,
            "interface_format": "OpenAI",
        }
    },
    "choose_configs": {
        # 将所有选择项都指向已存在的 llm_configs 键名
        "prompt_draft_llm": "Default",
        "chapter_outline_llm": "Default",
        "architecture_llm": "Default",
        "final_chapter_llm": "Default",
        "consistency_review_llm": "Default",
    },
    "other_params": {
        "topic": "",
        "genre": "",
        "num_chapters": 1,
        "word_number": 10000,
        "filepath": "",
        "chapter_num": "1",
        "user_guidance": "",
        "characters_involved": "",
        "key_items": "",
        "scene_location": "",
        "time_constraint": "",
    },
    "proxy_setting": {
        "proxy_url": "127.0.0.1",
        "proxy_port": "",
        "enabled": False,
    },
    "webdav_config": {
        "webdav_url": "",
        "webdav_username": "",
        "webdav_password": "",
    },
}


def _ensure_llm_item(item: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """补齐单个 LLM 配置项字段，返回(补齐后的项, 是否改变)"""
    changed = False
    if not isinstance(item, dict):
        return dict(DEFAULT_LLM_ITEM), True
    for k, v in DEFAULT_LLM_ITEM.items():
        if k not in item:
            item[k] = v
            changed = True
    return item, changed


def _merge_defaults(cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """将缺失的顶层键、内部字段按 DEFAULT_CONFIG 进行补全；必要时回填 choose->llm 的引用。"""
    changed = False
    if not isinstance(cfg, dict):
        return dict(DEFAULT_CONFIG), True

    # 顶层键补全
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v if not isinstance(v, dict) else dict(v)
            changed = True

    # llm_configs 补齐 + 规范化
    llms = cfg.get("llm_configs")
    if not isinstance(llms, dict) or not llms:
        cfg["llm_configs"] = {"Default": dict(DEFAULT_LLM_ITEM)}
        llms = cfg["llm_configs"]
        changed = True
    else:
        for name in list(llms.keys()):
            fixed, diff = _ensure_llm_item(llms[name])
            if diff:
                llms[name] = fixed
                changed = True

    # choose_configs 补齐；若引用了不存在的 llm 名称，则为该名称创建一个默认项
    choose = cfg.get("choose_configs")
    if not isinstance(choose, dict):
        choose = dict(DEFAULT_CONFIG["choose_configs"])
        cfg["choose_configs"] = choose
        changed = True
    else:
        for k, v in DEFAULT_CONFIG["choose_configs"].items():
            if k not in choose:
                choose[k] = v
                changed = True
    # 确保 choose 中的每个值都在 llm_configs 里
    for k, llm_name in list(choose.items()):
        if llm_name not in cfg["llm_configs"]:
            cfg["llm_configs"][llm_name] = dict(DEFAULT_LLM_ITEM)
            changed = True

    # embedding_configs 补齐
    emb = cfg.get("embedding_configs")
    if not isinstance(emb, dict) or not emb:
        cfg["embedding_configs"] = dict(DEFAULT_CONFIG["embedding_configs"])
        changed = True

    # other_params 补齐与默认值
    op = cfg.get("other_params")
    if not isinstance(op, dict):
        cfg["other_params"] = dict(DEFAULT_CONFIG["other_params"])
        changed = True
    else:
        for k, v in DEFAULT_CONFIG["other_params"].items():
            if k not in op or (k in ("num_chapters", "word_number") and (not op.get(k) or int(op.get(k) or 0) <= 0)):
                op[k] = v
                changed = True
        if not op.get("chapter_num"):
            op["chapter_num"] = "1"
            changed = True

    # proxy/webdav 补齐
    if not isinstance(cfg.get("proxy_setting"), dict):
        cfg["proxy_setting"] = dict(DEFAULT_CONFIG["proxy_setting"]) 
        changed = True
    if not isinstance(cfg.get("webdav_config"), dict):
        cfg["webdav_config"] = dict(DEFAULT_CONFIG["webdav_config"]) 
        changed = True

    # last_* 字段兜底
    if not cfg.get("last_interface_format"):
        cfg["last_interface_format"] = "OpenAI"; changed = True
    if not cfg.get("last_embedding_interface_format"):
        cfg["last_embedding_interface_format"] = "OpenAI"; changed = True

    return cfg, changed


def load_config(config_file: str) -> Dict[str, Any]:
    """
    加载配置：
    - 若文件不存在：创建默认配置
    - 若 JSON 损坏：备份为 .bak 并写入默认配置
    - 若键缺失：自动补齐并回写
    """
    if not os.path.exists(config_file):
        create_config(config_file)

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        # 备份坏文件
        try:
            if os.path.exists(config_file):
                ts = time.strftime('%Y%m%d%H%M%S')
                os.replace(config_file, f"{config_file}.{ts}.bak")
        except Exception:
            pass
        # 重建默认
        create_config(config_file)
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

    data, changed = _merge_defaults(data)
    if changed:
        save_config(data, config_file)
    return data


def create_config(config_file: str) -> Dict[str, Any]:
    """写入默认配置（若目录不存在则创建）。"""
    os.makedirs(os.path.dirname(config_file) or '.', exist_ok=True)
    save_config(dict(DEFAULT_CONFIG), config_file)
    return dict(DEFAULT_CONFIG)


def save_config(config_data: Dict[str, Any], config_file: str) -> bool:
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False


# ---------- 现有的配置测试函数，保持调用签名不变 ----------

def test_llm_config(interface_format, api_key, base_url, model_name, temperature, max_tokens, timeout, log_func, handle_exception_func):
    """测试当前的LLM配置是否可用（非阻塞）。"""
    import threading
    def task():
        try:
            log_func("开始测试LLM配置...")
            llm_adapter = create_llm_adapter(
                interface_format=interface_format,
                base_url=base_url,
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            test_prompt = "Please reply 'OK'"
            response = llm_adapter.invoke(test_prompt)
            if response:
                log_func("✅ LLM配置测试成功！")
                log_func(f"测试回复: {response}")
            else:
                log_func("❌ LLM配置测试失败：未获取到响应")
        except Exception as e:
            log_func(f"❌ LLM配置测试出错: {str(e)}")
            handle_exception_func("测试LLM配置时出错")
    threading.Thread(target=task, daemon=True).start()


def test_embedding_config(api_key, base_url, interface_format, model_name, log_func, handle_exception_func):
    """测试当前的Embedding配置是否可用（非阻塞）。"""
    import threading
    def task():
        try:
            log_func("开始测试Embedding配置...")
            embedding_adapter = create_embedding_adapter(
                interface_format=interface_format,
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
            )
            test_text = "测试文本"
            embeddings = embedding_adapter.embed_query(test_text)
            if embeddings and len(embeddings) > 0:
                log_func("✅ Embedding配置测试成功！")
                log_func(f"生成的向量维度: {len(embeddings)}")
            else:
                log_func("❌ Embedding配置测试失败：未获取到向量")
        except Exception as e:
            log_func(f"❌ Embedding配置测试出错: {str(e)}")
            handle_exception_func("测试Embedding配置时出错")
    threading.Thread(target=task, daemon=True).start()
