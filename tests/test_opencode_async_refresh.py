import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.config_tab as config_tab


class FakeButton:
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_calls = []
        self.configure_calls = []
        self.command = kwargs.get("command")

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)

    def pack(self, **kwargs):
        self.grid_calls.append(kwargs)

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)
        if "command" in kwargs:
            self.command = kwargs["command"]


class FakeEntry(FakeButton):
    def grid_forget(self):
        pass

    def grid_remove(self):
        pass


class FakeOptionMenu(FakeButton):
    def grid_forget(self):
        pass

    def grid_remove(self):
        pass


class FakeFrame(FakeButton):
    def columnconfigure(self, *args, **kwargs):
        pass

    def grid_rowconfigure(self, *args, **kwargs):
        pass

    def grid_columnconfigure(self, *args, **kwargs):
        pass


class FakeVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def trace_add(self, *args, **kwargs):
        pass


def _build_fake_self():
    logs = []
    after_calls = []

    class FakeMaster:
        def after(self, delay, callback):
            after_calls.append((delay, callback))

    return SimpleNamespace(
        loaded_config={"llm_configs": {"OpenCode": {}}, "embedding_configs": {}},
        ai_config_tab=FakeFrame(),
        embeddings_config_tab=FakeFrame(),
        config_choose=FakeFrame(),
        proxy_setting_tab=FakeFrame(),
        master=FakeMaster(),
        safe_log=logs.append,
        logs=logs,
        after_calls=after_calls,
        api_key_var=FakeVar(""),
        base_url_var=FakeVar(""),
        interface_format_var=FakeVar("OpenCode"),
        model_name_var=FakeVar("cached-model"),
        temperature_var=FakeVar(0.7),
        max_tokens_var=FakeVar(1024),
        timeout_var=FakeVar(60),
        interface_config_var=FakeVar("OpenCode"),
        opencode_agent_var=FakeVar(""),
        test_llm_config=lambda: None,
    )


def test_build_ai_config_tab_uses_background_refresh_for_opencode_models(monkeypatch):
    fake_self = _build_fake_self()
    thread_targets = []

    monkeypatch.setattr(config_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(config_tab.ctk, "CTkLabel", FakeButton)
    monkeypatch.setattr(config_tab.ctk, "CTkButton", FakeButton)
    monkeypatch.setattr(config_tab.ctk, "CTkEntry", FakeEntry)
    monkeypatch.setattr(config_tab.ctk, "CTkOptionMenu", FakeOptionMenu)
    monkeypatch.setattr(config_tab.ctk, "CTkSlider", FakeButton)
    monkeypatch.setattr(config_tab.ctk, "StringVar", FakeVar)
    monkeypatch.setattr(config_tab.ctk, "DoubleVar", FakeVar)
    monkeypatch.setattr(config_tab.ctk, "IntVar", FakeVar)
    monkeypatch.setattr(config_tab, "create_label_with_help", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_tab, "t", lambda text: text)
    monkeypatch.setattr(config_tab, "threading", SimpleNamespace(Thread=lambda target, daemon=True: SimpleNamespace(start=lambda: thread_targets.append(target))))

    monkeypatch.setattr(config_tab, "build_embeddings_config_tab", lambda self: None)
    monkeypatch.setattr(config_tab, "build_config_choose_tab", lambda self: None)
    monkeypatch.setattr(config_tab, "build_proxy_setting_tab", lambda self: None)

    monkeypatch.setattr("llm_adapters.get_cached_opencode_models", lambda: ["cached-model"])
    monkeypatch.setattr("llm_adapters.get_cached_opencode_agents", lambda: [])
    monkeypatch.setattr("llm_adapters.refresh_opencode_models", lambda base, api: ["fresh-model"])
    monkeypatch.setattr("llm_adapters.refresh_opencode_agents", lambda: [])

    config_tab.build_ai_config_tab(fake_self)

    assert hasattr(fake_self, "opencode_refresh_btn")
    fake_self.opencode_refresh_btn.command()

    assert len(thread_targets) == 1


def test_build_ai_config_tab_uses_background_refresh_for_opencode_agents(monkeypatch):
    fake_self = _build_fake_self()
    thread_targets = []

    monkeypatch.setattr(config_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(config_tab.ctk, "CTkLabel", FakeButton)
    monkeypatch.setattr(config_tab.ctk, "CTkButton", FakeButton)
    monkeypatch.setattr(config_tab.ctk, "CTkEntry", FakeEntry)
    monkeypatch.setattr(config_tab.ctk, "CTkOptionMenu", FakeOptionMenu)
    monkeypatch.setattr(config_tab.ctk, "CTkSlider", FakeButton)
    monkeypatch.setattr(config_tab.ctk, "StringVar", FakeVar)
    monkeypatch.setattr(config_tab.ctk, "DoubleVar", FakeVar)
    monkeypatch.setattr(config_tab.ctk, "IntVar", FakeVar)
    monkeypatch.setattr(config_tab, "create_label_with_help", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_tab, "t", lambda text: text)
    monkeypatch.setattr(config_tab, "threading", SimpleNamespace(Thread=lambda target, daemon=True: SimpleNamespace(start=lambda: thread_targets.append(target))))

    monkeypatch.setattr("llm_adapters.get_cached_opencode_models", lambda: ["cached-model"])
    monkeypatch.setattr("llm_adapters.get_cached_opencode_agents", lambda: ["cached-agent"])
    monkeypatch.setattr("llm_adapters.refresh_opencode_models", lambda base, api: ["fresh-model"])
    monkeypatch.setattr("llm_adapters.refresh_opencode_agents", lambda: ["fresh-agent"])

    config_tab.build_ai_config_tab(fake_self)

    assert hasattr(fake_self, "opencode_agent_refresh_btn")
    fake_self.opencode_agent_refresh_btn.command()

    assert len(thread_targets) >= 1
