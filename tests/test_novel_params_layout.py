import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.novel_params_tab as novel_params_tab


class FakeFrame:
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_calls = []
        self.columnconfigure_calls = []
        self.rowconfigure_calls = []
        self._grid_slaves = []

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)

    def columnconfigure(self, columns, weight):
        self.columnconfigure_calls.append((columns, weight))

    def grid_rowconfigure(self, row, weight):
        self.rowconfigure_calls.append((row, weight))

    def grid_slaves(self, column=None):
        return list(self._grid_slaves)


class FakeButton:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_calls = []

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)


def _build_fake_self():
    params_frame = FakeFrame()
    params_frame._grid_slaves = [object(), object(), object(), object()]
    return SimpleNamespace(
        right_frame=FakeFrame(),
        params_frame=params_frame,
        do_consistency_check=lambda: None,
        import_knowledge_handler=lambda: None,
        clear_vectorstore_handler=lambda: None,
        show_plot_arcs_ui=lambda: None,
        show_role_library=lambda: None,
        save_all_config=lambda: None,
        rebuild_full_vectorstore_ui=lambda: None,
        open_embed_dashboard_ui=lambda: None,
        open_character_review_dialog=lambda: None,
    )


def test_optional_buttons_attach_to_params_frame_when_params_frame_exists(monkeypatch):
    monkeypatch.setattr(novel_params_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(novel_params_tab, "make_button", lambda parent, **kwargs: FakeButton(parent, **kwargs))
    monkeypatch.setattr(novel_params_tab, "t", lambda text: text)

    fake_self = _build_fake_self()

    novel_params_tab.build_optional_buttons_area(fake_self, start_row=1)

    assert fake_self.optional_btn_frame.parent is fake_self.params_frame
    assert fake_self.optional_btn_frame.grid_calls[0]["row"] == 4
    assert (1, 0) in fake_self.right_frame.rowconfigure_calls


def test_optional_buttons_fallback_to_right_frame_without_params_frame(monkeypatch):
    monkeypatch.setattr(novel_params_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(novel_params_tab, "make_button", lambda parent, **kwargs: FakeButton(parent, **kwargs))
    monkeypatch.setattr(novel_params_tab, "t", lambda text: text)

    fake_self = SimpleNamespace(
        right_frame=FakeFrame(),
        do_consistency_check=lambda: None,
        import_knowledge_handler=lambda: None,
        clear_vectorstore_handler=lambda: None,
        show_plot_arcs_ui=lambda: None,
        show_role_library=lambda: None,
        save_all_config=lambda: None,
        rebuild_full_vectorstore_ui=lambda: None,
        open_embed_dashboard_ui=lambda: None,
        open_character_review_dialog=lambda: None,
    )

    novel_params_tab.build_optional_buttons_area(fake_self, start_row=1)

    assert fake_self.optional_btn_frame.parent is fake_self.right_frame
    assert fake_self.optional_btn_frame.grid_calls[0]["row"] == 2
