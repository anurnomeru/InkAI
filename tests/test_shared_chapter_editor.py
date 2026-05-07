import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.main_tab as main_tab
import ui.chapters_tab as chapters_tab
import ui.shared_chapter_editor as shared_editor


class FakeFrame:
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_calls = []
        self.columnconfigure_calls = []
        self.rowconfigure_calls = []

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)

    def pack(self, **kwargs):
        self.grid_calls.append(kwargs)

    def grid_remove(self):
        self.grid_calls.append({"removed": True})

    def columnconfigure(self, column, weight):
        self.columnconfigure_calls.append((column, weight))

    def rowconfigure(self, row, weight):
        self.rowconfigure_calls.append((row, weight))

    def grid_rowconfigure(self, row, weight):
        self.rowconfigure_calls.append((row, weight))

    def bind(self, event_name, callback):
        pass

    def configure(self, **kwargs):
        self.kwargs.update(kwargs)


class FakeLabel(FakeFrame):
    pass


class FakeTextbox:
    def __init__(self, parent=None, **kwargs):
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

    def see(self, index):
        pass

    def configure(self, **kwargs):
        self.kwargs.update(kwargs)


def test_shared_editor_builder_installs_main_editor_bindings(monkeypatch):
    installed = []
    context_menus = []

    monkeypatch.setattr(shared_editor.ctk, "CTkTextbox", FakeTextbox)
    monkeypatch.setattr(shared_editor, "install_text_shortcuts", lambda widget, **kwargs: installed.append((widget, kwargs)))
    monkeypatch.setattr(shared_editor, "TextWidgetContextMenu", lambda widget: context_menus.append(widget))

    fake_self = SimpleNamespace()
    container = FakeFrame()
    label = FakeLabel()
    save_calls = []

    widget = shared_editor.build_chapter_editor(
        fake_self,
        parent=container,
        attribute_name="chapter_result",
        label_widget=label,
        label_template="本章内容（可编辑） 字数：{count}",
        save_handler=lambda: save_calls.append("saved"),
    )

    assert widget is fake_self.chapter_result
    assert widget.kwargs["font"] == (shared_editor.FONT_FAMILY, shared_editor.FONT_SIZES["lg"])
    assert "<Control-s>" in widget.bound_events
    assert installed and installed[0][0] is widget
    assert context_menus == [widget]


def test_chapters_tab_uses_shared_editor_builder(monkeypatch):
    calls = []

    def fake_builder(self, **kwargs):
        calls.append(kwargs)
        widget = FakeTextbox(kwargs["parent"], font=kwargs.get("font"))
        setattr(self, kwargs["attribute_name"], widget)
        return widget

    monkeypatch.setattr(chapters_tab, "build_chapter_editor", fake_builder)
    monkeypatch.setattr(chapters_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(chapters_tab.ctk, "CTkButton", FakeFrame)
    monkeypatch.setattr(chapters_tab.ctk, "CTkOptionMenu", FakeFrame)
    monkeypatch.setattr(chapters_tab.ctk, "CTkLabel", FakeLabel)
    monkeypatch.setattr(chapters_tab.ctk, "StringVar", lambda value="": SimpleNamespace(get=lambda: value, set=lambda new: None))
    monkeypatch.setattr(chapters_tab, "refresh_chapters_list", lambda self: None)
    monkeypatch.setattr(chapters_tab, "t", lambda text: text)

    fake_self = SimpleNamespace(
        tabview=SimpleNamespace(add=lambda label: FakeFrame()),
        prev_chapter=lambda: None,
        next_chapter=lambda: None,
        on_chapter_selected=lambda value: None,
        save_current_chapter=lambda: None,
        refresh_chapters_list=lambda: None,
        clear_vectorstore_handler=lambda: None,
        update_vectorstore_button=lambda: None,
    )

    chapters_tab.build_chapters_tab(fake_self)

    assert len(calls) == 1
    assert calls[0]["attribute_name"] == "chapter_view_text"
    assert calls[0]["label_template"] == "本章内容（可编辑） 字数：{count}"


def test_main_tab_uses_shared_editor_builder(monkeypatch):
    calls = []
    polish_buttons = []
    made_buttons = []

    def fake_builder(self, **kwargs):
        calls.append(kwargs)
        widget = FakeTextbox(kwargs["parent"], font=kwargs.get("font"))
        setattr(self, kwargs["attribute_name"], widget)
        return widget

    def fake_polish_button(self, parent, widget_getter):
        polish_buttons.append(widget_getter)
        return FakeFrame(parent)

    monkeypatch.setattr(main_tab, "build_chapter_editor", fake_builder)
    monkeypatch.setattr(main_tab, "create_selection_polish_button", fake_polish_button)
    monkeypatch.setattr(main_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(main_tab.ctk, "CTkLabel", FakeLabel)
    monkeypatch.setattr(main_tab.ctk, "CTkTextbox", FakeTextbox)
    monkeypatch.setattr(main_tab.ctk, "StringVar", lambda value="": SimpleNamespace(get=lambda: value, set=lambda new: None))
    monkeypatch.setattr(main_tab.ctk, "CTkOptionMenu", FakeFrame)
    monkeypatch.setattr(main_tab, "make_button", lambda parent, **kwargs: made_buttons.append(FakeFrame(parent, **kwargs)) or made_buttons[-1])
    monkeypatch.setattr(main_tab, "install_text_shortcuts", lambda widget, **kwargs: None)
    monkeypatch.setattr(main_tab, "TextWidgetContextMenu", lambda widget: None)
    monkeypatch.setattr(main_tab, "t", lambda text: text)

    fake_self = SimpleNamespace(
        left_frame=FakeFrame(),
        save_main_editor_content=lambda: None,
        generate_novel_architecture_ui=lambda: None,
        generate_chapter_blueprint_ui=lambda: None,
        generate_chapter_draft_ui=lambda: None,
        finalize_chapter_ui=lambda: None,
        generate_batch_ui=lambda: None,
        on_draft_variant_selected=lambda value: None,
        refresh_draft_variants_list=lambda: None,
    )

    main_tab.build_left_layout(fake_self)

    assert len(calls) == 1
    assert calls[0]["attribute_name"] == "chapter_result"
    assert calls[0]["label_template"] == "本章内容（可编辑） 字数：{count}"
    assert len(polish_buttons) == 1
    assert hasattr(fake_self, "btn_generate_chapter")


def test_chapters_tab_adds_selection_polish_button(monkeypatch):
    polish_buttons = []

    def fake_builder(self, **kwargs):
        widget = FakeTextbox(kwargs["parent"], font=kwargs.get("font"))
        setattr(self, kwargs["attribute_name"], widget)
        return widget

    def fake_polish_button(self, parent, widget_getter):
        polish_buttons.append(widget_getter)
        return FakeFrame(parent)

    monkeypatch.setattr(chapters_tab, "build_chapter_editor", fake_builder)
    monkeypatch.setattr(chapters_tab, "create_selection_polish_button", fake_polish_button)
    monkeypatch.setattr(chapters_tab.ctk, "CTkFrame", FakeFrame)
    monkeypatch.setattr(chapters_tab.ctk, "CTkButton", FakeFrame)
    monkeypatch.setattr(chapters_tab.ctk, "CTkOptionMenu", FakeFrame)
    monkeypatch.setattr(chapters_tab.ctk, "CTkLabel", FakeLabel)
    monkeypatch.setattr(chapters_tab.ctk, "StringVar", lambda value="": SimpleNamespace(get=lambda: value, set=lambda new: None))
    monkeypatch.setattr(chapters_tab, "refresh_chapters_list", lambda self: None)
    monkeypatch.setattr(chapters_tab, "t", lambda text: text)

    fake_self = SimpleNamespace(
        tabview=SimpleNamespace(add=lambda label: FakeFrame()),
        prev_chapter=lambda: None,
        next_chapter=lambda: None,
        on_chapter_selected=lambda value: None,
        save_current_chapter=lambda: None,
        refresh_chapters_list=lambda: None,
        clear_vectorstore_handler=lambda: None,
        update_vectorstore_button=lambda: None,
    )

    chapters_tab.build_chapters_tab(fake_self)

    assert len(polish_buttons) == 1


def test_create_selection_polish_button_installs_running_controller(monkeypatch):
    created = []

    def fake_make_button(parent, **kwargs):
        btn = FakeFrame(parent, **kwargs)
        created.append(btn)
        return btn

    monkeypatch.setattr(shared_editor, "make_button", fake_make_button)

    fake_self = SimpleNamespace()
    button = shared_editor.create_selection_polish_button(
        fake_self,
        parent=FakeFrame(),
        widget_getter=lambda: FakeTextbox(),
    )

    assert button is created[0]
    assert hasattr(fake_self, "_selection_polish_button_controller")
