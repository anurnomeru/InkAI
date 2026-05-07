import os
import sys
import threading
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.shared_chapter_editor as shared_editor


class FakeTextWidget:
    def __init__(self, content="", selection=""):
        self.content = content
        self.selection = selection
        self.replacements = []
        self.last_insert_index = None

    def selection_get(self):
        if not self.selection:
            raise shared_editor.tk.TclError("no selection")
        return self.selection

    def get(self, start, end=None):
        if start == shared_editor.tk.SEL_FIRST and end == shared_editor.tk.SEL_LAST:
            if not self.selection:
                raise shared_editor.tk.TclError("no selection")
            return self.selection
        return self.content

    def index(self, index_name):
        if index_name == shared_editor.tk.SEL_FIRST and self.selection in self.content:
            return self.content.index(self.selection)
        return 0

    def delete(self, start, end):
        if self.selection and self.selection in self.content:
            self.last_insert_index = self.content.index(self.selection)
            self.content = self.content.replace(self.selection, "", 1)
        elif isinstance(start, int) and isinstance(end, int):
            self.last_insert_index = start
            self.content = self.content[:start] + self.content[end:]

    def insert(self, index, value):
        if isinstance(index, int):
            self.content = self.content[:index] + value + self.content[index:]
        elif self.last_insert_index is not None:
            pos = self.last_insert_index
            self.content = self.content[:pos] + value + self.content[pos:]
        else:
            self.content += value
        self.replacements.append(value)


def test_build_polish_prompt_only_uses_style_guidance_and_selected_text():
    prompt = shared_editor.build_selection_polish_prompt(
        style_guidance="冷峻、压抑、克制。",
        selected_text="他推门走了进去。",
        user_extra_guidance="",
    )

    assert "冷峻、压抑、克制。" in prompt
    assert "他推门走了进去。" in prompt
    assert "可直接替换原文的文本" in prompt
    assert "全局摘要" not in prompt
    assert "章节大纲" not in prompt


def test_build_polish_variant_prompt_wraps_user_prompt_and_variant_index():
    prompt = shared_editor.build_selection_polish_variant_prompt(
        base_prompt="【文风说明】\n冷峻\n【选中文字】\n原句",
        variant_index=3,
        total_variants=6,
    )

    assert "第3/6个候选版本" in prompt
    assert "【文风说明】" in prompt
    assert "原句" in prompt
    assert "只输出一个可直接替换原文的最终版本" in prompt


def test_parse_polish_variants_extracts_six_versions():
    response = """版本1：第一版\n版本2：第二版\n版本3：第三版\n版本4：第四版\n版本5：第五版\n版本6：第六版"""

    variants = shared_editor.parse_polish_variants(response)

    assert variants == ["第一版", "第二版", "第三版", "第四版", "第五版", "第六版"]


def test_replace_selected_text_replaces_only_selection():
    widget = FakeTextWidget(content="前文[原句]后文", selection="[原句]")

    shared_editor.replace_selected_text(widget, "新句子")

    assert widget.content == "前文新句子后文"


def test_polish_selected_text_returns_none_when_no_selection(monkeypatch):
    logs = []
    fake_self = SimpleNamespace(
        safe_log=logs.append,
    )
    widget = FakeTextWidget(content="完整文本", selection="")

    monkeypatch.setattr(shared_editor, "load_style_guidance_text", lambda self: "文风")

    result = shared_editor.polish_selected_text(
        fake_self,
        widget,
        llm_invoke=lambda prompt: "不会被调用",
        choose_variant=lambda variants: variants[0],
    )

    assert result is None
    assert logs == ["润色失败：请先选中一段文本。"]


def test_polish_selected_text_replaces_selected_content_with_chosen_variant(monkeypatch):
    logs = []
    fake_self = SimpleNamespace(
        safe_log=logs.append,
    )
    widget = FakeTextWidget(content="前文原句后文", selection="原句")

    monkeypatch.setattr(shared_editor, "load_style_guidance_text", lambda self: "冷峻克制")

    prompts = []
    progress = []

    def fake_invoke(prompt, variant_index=None, total_variants=None):
        prompts.append(prompt)
        return f"版本{variant_index}：改写{variant_index}"

    result = shared_editor.polish_selected_text(
        fake_self,
        widget,
        llm_invoke=fake_invoke,
        choose_variant=lambda variants: variants[2],
        progress_cb=lambda done, total: progress.append((done, total)),
    )

    assert len(prompts) == 6
    assert all("冷峻克制" in prompt for prompt in prompts)
    assert all("原句" in prompt for prompt in prompts)
    assert result == "改写3"
    assert widget.content == "前文改写3后文"
    assert progress[0] == (0, 6)
    assert progress[-1] == (6, 6)
    assert logs[-1] == "润色完成：已替换选中文本。"


def test_polish_selected_text_uses_cached_selection_after_focus_loss(monkeypatch):
    logs = []
    fake_self = SimpleNamespace(
        safe_log=logs.append,
    )
    widget = FakeTextWidget(content="前文原句后文", selection="")
    widget._last_selected_text = "原句"
    widget._last_selected_start = 2
    widget._last_selected_end = 4

    monkeypatch.setattr(shared_editor, "load_style_guidance_text", lambda self: "冷峻克制")

    prompts = []

    def fake_invoke(prompt, variant_index=None, total_variants=None):
        prompts.append(prompt)
        return f"改写{variant_index}"

    result = shared_editor.polish_selected_text(
        fake_self,
        widget,
        llm_invoke=fake_invoke,
        choose_variant=lambda variants: variants[0],
    )

    assert result == "改写1"
    assert prompts
    assert "原句" in prompts[0]
    assert widget.content == "前文改写1后文"


def test_build_polish_prompt_includes_optional_user_guidance():
    prompt = shared_editor.build_selection_polish_prompt(
        style_guidance="冷峻、压抑、克制。",
        selected_text="他推门走了进去。",
        user_extra_guidance="要更锋利一点，减少解释。",
    )

    assert "要更锋利一点，减少解释。" in prompt
    assert "补充说明" in prompt


def test_polish_selected_text_uses_user_confirmed_prompt(monkeypatch):
    logs = []
    fake_self = SimpleNamespace(
        safe_log=logs.append,
    )
    widget = FakeTextWidget(content="前文原句后文", selection="原句")

    monkeypatch.setattr(shared_editor, "load_style_guidance_text", lambda self: "冷峻克制")
    monkeypatch.setattr(shared_editor, "open_selection_polish_prompt_dialog", lambda self, prompt: prompt + "\n\n【补充说明】\n保留狠劲")

    captured = []

    def fake_invoke(prompt, variant_index=None, total_variants=None):
        captured.append(prompt)
        return f"改写{variant_index}"

    result = shared_editor.polish_selected_text(
        fake_self,
        widget,
        llm_invoke=fake_invoke,
        choose_variant=lambda variants: variants[0],
    )

    assert result == "改写1"
    assert captured
    assert "保留狠劲" in captured[0]


def test_generate_selection_polish_variants_runs_in_parallel(monkeypatch):
    progress = []
    barrier = threading.Barrier(6, timeout=1.5)

    def fake_invoke(prompt, variant_index=None, total_variants=None):
        barrier.wait()
        return f"改写{variant_index}"

    variants = shared_editor.generate_selection_polish_variants(
        base_prompt="【文风说明】\n冷峻\n【选中文字】\n原句",
        llm_invoke=fake_invoke,
        variant_count=6,
        progress_cb=lambda done, total: progress.append((done, total)),
        stop_requested=lambda: False,
        log_cb=lambda msg: None,
    )

    assert variants == ["改写1", "改写2", "改写3", "改写4", "改写5", "改写6"]
    assert progress[0] == (0, 6)
    assert progress[-1] == (6, 6)


def test_polish_selected_text_returns_none_when_prompt_dialog_cancelled(monkeypatch):
    logs = []
    fake_self = SimpleNamespace(
        safe_log=logs.append,
    )
    widget = FakeTextWidget(content="前文原句后文", selection="原句")

    monkeypatch.setattr(shared_editor, "load_style_guidance_text", lambda self: "冷峻克制")
    monkeypatch.setattr(shared_editor, "open_selection_polish_prompt_dialog", lambda self, prompt: None)

    result = shared_editor.polish_selected_text(
        fake_self,
        widget,
        llm_invoke=lambda prompt: "不会被调用",
        choose_variant=lambda variants: variants[0],
    )

    assert result is None
    assert logs[-1] == "润色已取消：未发送生成请求。"
