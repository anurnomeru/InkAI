import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.style_tab as style_tab


class FakeTab:
    def __init__(self):
        self.rowconfigure_calls = []
        self.columnconfigure_calls = []

    def rowconfigure(self, row, weight):
        self.rowconfigure_calls.append((row, weight))

    def columnconfigure(self, column, weight):
        self.columnconfigure_calls.append((column, weight))


class FakeTabView:
    def __init__(self):
        self.add_calls = []

    def add(self, label):
        self.add_calls.append(label)
        return FakeTab()


class FakeButton:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_calls = []

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)


class FakeLabel(FakeButton):
    pass


class FakeTextbox:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_calls = []
        self.bound_events = []
        self.content = ""

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)

    def bind(self, event_name, callback):
        self.bound_events.append(event_name)

    def delete(self, start, end):
        self.content = ""

    def insert(self, start, value):
        self.content = value

    def get(self, start, end):
        return self.content


def test_build_style_tab_uses_expected_tab_title(monkeypatch):
    fake_self = SimpleNamespace(
        tabview=FakeTabView(),
        load_style_guidance=lambda: None,
        save_style_guidance=lambda: None,
    )
    monkeypatch.setattr(style_tab.ctk, "CTkButton", FakeButton)
    monkeypatch.setattr(style_tab.ctk, "CTkLabel", FakeLabel)
    monkeypatch.setattr(style_tab.ctk, "CTkTextbox", FakeTextbox)
    monkeypatch.setattr(style_tab, "install_text_shortcuts", lambda widget: None)
    monkeypatch.setattr(style_tab, "TextWidgetContextMenu", lambda widget: None)
    monkeypatch.setattr(style_tab, "t", lambda text: text)

    style_tab.build_style_tab(fake_self)

    assert fake_self.tabview.add_calls == ["文风说明"]
    assert isinstance(fake_self.style_text, FakeTextbox)


def test_load_and_save_style_guidance_reads_expected_file(monkeypatch, tmp_path):
    project_dir = tmp_path / "novel"
    project_dir.mkdir()
    target_file = project_dir / "文风说明.txt"
    target_file.write_text("冷峻克制，少解释。", encoding="utf-8")

    logs = []
    fake_self = SimpleNamespace(
        filepath_var=SimpleNamespace(get=lambda: str(project_dir)),
        style_text=FakeTextbox(None),
        log=logs.append,
    )

    monkeypatch.setattr(style_tab, "read_file", lambda filename: open(filename, "r", encoding="utf-8").read())
    monkeypatch.setattr(style_tab, "clear_file_content", lambda filename: open(filename, "w", encoding="utf-8").close())
    monkeypatch.setattr(style_tab, "save_string_to_txt", lambda content, filename: open(filename, "a", encoding="utf-8").write(content))
    monkeypatch.setattr(style_tab.messagebox, "showwarning", lambda *args, **kwargs: None)
    monkeypatch.setattr(style_tab, "t", lambda text: text)

    style_tab.load_style_guidance(fake_self)
    assert fake_self.style_text.content == "冷峻克制，少解释。"

    fake_self.style_text.content = "节奏利落，句子短。"
    style_tab.save_style_guidance(fake_self)

    assert target_file.read_text(encoding="utf-8") == "节奏利落，句子短。"
    assert logs == [
        "已加载 文风说明.txt 到编辑区",
        "已保存对 文风说明.txt 的修改",
    ]
