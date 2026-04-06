# llm_adapters.py
# -*- coding: utf-8 -*-
import logging
from typing import Optional, List
from langchain_openai import ChatOpenAI, AzureChatOpenAI
import google.generativeai as genai
from google.generativeai import types
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import SystemMessage, UserMessage
from openai import OpenAI
import requests
import os
import shutil
import subprocess
import json


def check_base_url(url: str) -> str:
    """
    处理base_url的规则：
    1. 如果url以#结尾，则移除#并直接使用用户提供的url
    2. 否则检查是否需要添加/v1后缀
    """
    import re

    url = url.strip()
    if not url:
        return url
    if url.endswith("#"):
        return url.rstrip("#")
    if not re.search(r"/v\d+$", url):
        if "/v1" not in url:
            url = url.rstrip("/") + "/v1"
    return url


# -------------------- 缓存工具 --------------------
_DEF_CACHE_DIR = os.path.expanduser("~/.local/share/opencode/cache")


def _ensure_cache_dir() -> str:
    try:
        os.makedirs(_DEF_CACHE_DIR, exist_ok=True)
    except Exception:
        pass
    return _DEF_CACHE_DIR


def _models_cache_path() -> str:
    return os.path.join(_ensure_cache_dir(), "models.json")


def _agents_cache_path() -> str:
    return os.path.join(_ensure_cache_dir(), "agents.json")


def _read_list_cache(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data if isinstance(x, (str, int))]
    except Exception:
        return []
    return []


def _write_list_cache(path: str, items: List[str]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(items or []), f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class BaseLLMAdapter:
    """
    统一的 LLM 接口基类，为不同后端（OpenAI、Ollama、ML Studio、Gemini等）提供一致的方法签名。
    """

    def invoke(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement .invoke(prompt) method.")


# -------------------- OpenCode Adapters --------------------
class OpenCodeHttpAdapter(BaseLLMAdapter):
    """
    适配 OpenCode OpenAI 兼容 /v1/chat 接口（HTTP）。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        env_base = os.environ.get("OPENCODE_BASE_URL", "").strip()
        _base = check_base_url(base_url) if base_url else check_base_url(env_base)
        if not _base:
            raise ValueError(
                "OpenCode base_url 为空，请在配置中填写 Base URL 或设置 OPENCODE_BASE_URL 环境变量"
            )
        self.base_url = _base
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY", "").strip()
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = OpenAI(
            base_url=self.base_url,
            api_key=(self.api_key or "opencode"),
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            if resp and getattr(resp, "choices", None):
                return resp.choices[0].message.content
            logging.warning("No response from OpenCodeHttpAdapter.")
            return ""
        except Exception as e:
            logging.error(f"OpenCode HTTP 调用失败: {e}")
            return ""


class OpenCodeCliAdapter(BaseLLMAdapter):
    """
    适配 OpenCode CLI：opencode run -m <model> <prompt>
    需要系统路径存在可执行的 `opencode`。
    """

    def __init__(self, model_name: str, timeout: Optional[int] = 600):
        self.model_name = model_name
        self.timeout = timeout
        if not shutil.which("opencode"):
            raise RuntimeError("未找到 opencode 命令，请确保已安装并在 PATH 中。")

    def invoke(self, prompt: str) -> str:
        try:
            agent = (os.environ.get("OPENCODE_AGENT") or "").strip()
            cmd = ["opencode", "run", "-m", self.model_name]
            if agent:
                cmd += ["--agent", agent]
            cmd.append(prompt)
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
            if res.returncode != 0:
                logging.error(
                    f"OpenCode CLI 调用失败: rc={res.returncode} stderr={res.stderr.strip()}"
                )
                return ""
            return (res.stdout or "").strip()
        except subprocess.TimeoutExpired:
            logging.error("OpenCode CLI 调用超时")
            return ""
        except Exception as e:
            logging.error(f"OpenCode CLI 调用异常: {e}")
            return ""


# -------------------- 列表（带缓存/刷新） --------------------
def get_cached_opencode_models() -> List[str]:
    return _read_list_cache(_models_cache_path())


def get_cached_opencode_agents() -> List[str]:
    return _read_list_cache(_agents_cache_path())


def refresh_opencode_models(base_url: str, api_key: str = "") -> List[str]:
    ids = list_opencode_models(base_url, api_key)
    if ids:
        _write_list_cache(_models_cache_path(), ids)
    return ids


def refresh_opencode_agents() -> List[str]:
    names = list_opencode_agents()
    if names:
        _write_list_cache(_agents_cache_path(), names)
    return names


# -------------------- 原始在线枚举实现 --------------------
def _list_opencode_models_http(base_url: str, api_key: str = "") -> List[str]:
    try:
        _base = (
            check_base_url(base_url)
            if base_url
            else check_base_url(os.environ.get("OPENCODE_BASE_URL", ""))
        )
        if not _base:
            return []
        url = _base.rstrip("/") + "/models"
        headers = {}
        token = api_key or os.environ.get("OPENCODE_API_KEY", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = data.get("data") or []
        ids = []
        for item in items:
            mid = item.get("id") if isinstance(item, dict) else None
            if mid:
                ids.append(str(mid))
        return ids
    except Exception as e:
        logging.warning(f"OpenCode /v1/models 列表失败: {e}")
        return []


def _list_opencode_models_cli() -> List[str]:
    try:
        if not shutil.which("opencode"):
            return []
        res = subprocess.run(
            ["opencode", "models"], capture_output=True, text=True, timeout=10
        )
        if res.returncode != 0:
            return []
        ids: List[str] = []
        for line in (res.stdout or "").splitlines():
            s = line.strip()
            if not s:
                continue
            if s.lower().startswith("usage:") or s.lower().startswith("opencode "):
                continue
            if "/" in s or s:
                ids.append(s)
        return ids
    except Exception:
        return []


def list_opencode_models(base_url: str, api_key: str = "") -> List[str]:
    ids = _list_opencode_models_cli()
    if ids:
        return ids
    return _list_opencode_models_http(base_url, api_key)


def list_opencode_agents() -> List[str]:
    try:
        if not shutil.which("opencode"):
            return []
        # 1) Prefer JSON config
        try:
            cfg = subprocess.run(
                ["opencode", "debug", "config"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if cfg.returncode == 0 and cfg.stdout.strip().startswith("{"):
                data = json.loads(cfg.stdout)
                agents_obj = data.get("agent") or {}
                if isinstance(agents_obj, dict) and agents_obj.keys():
                    return [str(k) for k in agents_obj.keys()]
        except Exception:
            pass
        # 2) Textual fallback
        variants = [
            ["opencode", "agent", "list"],
            ["opencode", "agents"],
            ["opencode", "agent"],
        ]
        out = ""
        for cmd in variants:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0 and res.stdout:
                    out = res.stdout
                    break
            except Exception:
                continue
        if not out:
            return []
        names: List[str] = []
        import re

        for raw in out.splitlines():
            s = raw.strip()
            if not s:
                continue
            low = s.lower()
            if low.startswith("usage:") or low.startswith("opencode "):
                continue
            if s[0] in '[{"}':
                continue
            m = re.match(r"^(.*?)\s*\((?:primary|subagent|.+)\)\s*$", s)
            if m:
                name = m.group(1).strip()
                if name:
                    names.append(name)
                continue
            if " " not in s and not any(ch in s for ch in ':,[]{}"'):
                names.append(s)
        seen = set()
        uniq: List[str] = []
        for n in names:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        return uniq
    except Exception:
        return []


# -------------- 其余适配器（保持原有实现） --------------
class DeepSeekAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from DeepSeekAdapter.")
            return ""
        return response.content


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from OpenAIAdapter.")
            return ""
        return response.content


class GeminiAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(model_name=self.model_name)

    def invoke(self, prompt: str) -> str:
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            response = self._model.generate_content(
                prompt, generation_config=generation_config
            )
            if response and response.text:
                return response.text
            else:
                logging.warning("No text response from Gemini API.")
                return ""
        except Exception as e:
            logging.error(f"Gemini API 调用失败: {e}")
            return ""


class AzureOpenAIAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        import re

        match = re.match(
            r"https://(.+?)/openai/deployments/(.+?)/chat/completions\?api-version=(.+)",
            base_url,
        )
        if match:
            self.azure_endpoint = f"https://{match.group(1)}"
            self.azure_deployment = match.group(2)
            self.api_version = match.group(3)
        else:
            raise ValueError("Invalid Azure OpenAI base_url format")
        self.api_key = api_key
        self.model_name = self.azure_deployment
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = AzureChatOpenAI(
            azure_endpoint=self.azure_endpoint,
            azure_deployment=self.azure_deployment,
            api_version=self.api_version,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from AzureOpenAIAdapter.")
            return ""
        return response.content


class OllamaAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        if self.api_key == "":
            self.api_key = "ollama"
        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from OllamaAdapter.")
            return ""
        return response.content


class MLStudioAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        try:
            response = self._client.invoke(prompt)
            if not response:
                logging.warning("No response from MLStudioAdapter.")
                return ""
            return response.content
        except Exception as e:
            logging.error(f"ML Studio API 调用超时或失败: {e}")
            return ""


class AzureAIAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        import re

        match = re.match(
            r"https://(.+?)\.services\.ai\.azure\.com(?:/models)?(?:/chat/completions)?(?:\?api-version=(.+))?",
            base_url,
        )
        if match:
            self.endpoint = f"https://{match.group(1)}.services.ai.azure.com/models"
            self.api_version = (
                match.group(2) if match.group(2) else "2024-05-01-preview"
            )
        else:
            raise ValueError(
                "Invalid Azure AI base_url format. Expected format: https://<endpoint>.services.ai.azure.com/models/chat/completions?api-version=xxx"
            )
        self.base_url = self.endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key),
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        try:
            response = self._client.complete(
                messages=[
                    SystemMessage("You are a helpful assistant."),
                    UserMessage(prompt),
                ]
            )
            if response and response.choices:
                return response.choices[0].message.content
            else:
                logging.warning("No response from AzureAIAdapter.")
                return ""
        except Exception as e:
            logging.error(f"Azure AI Inference API 调用失败: {e}")
            return ""


class VolcanoEngineAIAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)

    def invoke(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是DeepSeek，是一个 AI 人工智能助手",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=self.timeout,
            )
            if not response:
                logging.warning("No response from DeepSeekAdapter.")
                return ""
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"火山引擎API调用超时或失败: {e}")
            return ""


class SiliconFlowAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)

    def invoke(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是DeepSeek，是一个 AI 人工智能助手",
                    },
                    {"role": "user", "content": prompt},
                ],
                timeout=self.timeout,
            )
            if not response:
                logging.warning("No response from DeepSeekAdapter.")
                return ""
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"硅基流动API调用超时或失败: {e}")
            return ""


class GrokAdapter(BaseLLMAdapter):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout: Optional[int] = 600,
    ):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = OpenAI(
            base_url=self.base_url, api_key=self.api_key, timeout=self.timeout
        )

    def invoke(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are Grok, created by xAI."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            if response and response.choices:
                return response.choices[0].message.content
            else:
                logging.warning("No response from GrokAdapter.")
                return ""
        except Exception as e:
            logging.error(f"Grok API 调用失败: {e}")
            return ""


def create_llm_adapter(
    interface_format: str,
    base_url: str,
    model_name: str,
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> BaseLLMAdapter:
    """
    工厂函数：根据 interface_format 返回不同的适配器实例。
    遵循用户配置的 temperature；仅对 Moonshot/Kimi 在等于 1 时做整型归一化。
    """

    def _normalize_temp(url: str, model: str, temp):
        try:
            if (url and "moonshot.cn" in url) or (model and "kimi" in model.lower()):
                if isinstance(temp, float) and abs(temp - 1.0) < 1e-9:
                    return 1
                if temp in ("1", "1.0", 1.0):
                    return 1
            return temp
        except Exception:
            return temp

    fmt = (interface_format or "").strip().lower()
    temperature = _normalize_temp(base_url, model_name, temperature)

    if fmt == "deepseek":
        ret = DeepSeekAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "openai":
        ret = OpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "azure openai":
        ret = AzureOpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "azure ai":
        ret = AzureAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "ollama":
        ret = OllamaAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "ml studio":
        ret = MLStudioAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "gemini":
        ret = GeminiAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "阿里云百炼":
        ret = OpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "火山引擎":
        ret = VolcanoEngineAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "硅基流动":
        ret = SiliconFlowAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "grok":
        ret = GrokAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)
    elif fmt == "opencode":
        ret = OpenCodeCliAdapter(model_name=model_name, timeout=timeout)
        return _wrap_with_logging(ret)
    else:
        ret = OpenAIAdapter(
            api_key, base_url, model_name, max_tokens, temperature, timeout
        )
        return _wrap_with_logging(ret)


def _wrap_with_logging(adapter: BaseLLMAdapter) -> BaseLLMAdapter:
    class LoggingLLMAdapter(BaseLLMAdapter):
        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def invoke(self, prompt: str) -> str:
            try:
                import inspect, os as _os

                st = inspect.stack()
                caller = st[1] if len(st) > 1 else None
                caller_str = (
                    f"{_os.path.basename(caller.filename)}::{caller.function}"
                    if caller
                    else "unknown"
                )
            except Exception:
                caller_str = "unknown"
            info = {
                "adapter": type(self._inner).__name__,
                "base_url": getattr(self._inner, "base_url", None),
                "model": getattr(self._inner, "model_name", None),
                "temperature": getattr(self._inner, "temperature", None),
                "max_tokens": getattr(self._inner, "max_tokens", None),
                "timeout": getattr(self._inner, "timeout", None),
            }
            try:
                logging.info(f"[LLM Intent] {caller_str} | {info}")
                print("[LLM Intent]", caller_str, info)
            except Exception:
                pass
            return self._inner.invoke(prompt)

    return LoggingLLMAdapter(adapter)
