import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.generation_handlers as generation_handlers


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeButton:
    def __init__(self):
        self.text = ""
        self.command = None
        self.after_calls = []
        self.after_cancel_calls = []

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
        if "command" in kwargs:
            self.command = kwargs["command"]

    def after(self, delay, callback):
        token = f"after-{len(self.after_calls) + 1}"
        self.after_calls.append((delay, callback, token))
        return token

    def after_cancel(self, token):
        self.after_cancel_calls.append(token)


class FakeText:
    def __init__(self, value=""):
        self.value = value

    def get(self, start, end):
        return self.value


class FakeMaster:
    def after(self, delay, callback):
        callback()


class FakeDialog:
    def __init__(self):
        self.protocol_calls = []

    def title(self, *args, **kwargs):
        pass

    def geometry(self, *args, **kwargs):
        pass

    def protocol(self, *args, **kwargs):
        self.protocol_calls.append((args, kwargs))

    def grab_set(self):
        pass

    def destroy(self):
        pass


class FakeTextbox:
    def __init__(self, *args, **kwargs):
        self.value = ""

    def pack(self, **kwargs):
        pass

    def insert(self, start, value):
        self.value = value

    def get(self, start, end):
        return self.value

    def bind(self, *args, **kwargs):
        pass


class FakeLabel:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, **kwargs):
        pass

    def configure(self, **kwargs):
        pass


class FakeFrame:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, **kwargs):
        pass


class FakeDialogButton:
    auto_confirm = True
    instances = []

    def __init__(self, parent=None, text="", command=None, **kwargs):
        self.text = text
        self.command = command
        self.configure_calls = []
        FakeDialogButton.instances.append(self)

    def pack(self, **kwargs):
        if self.text == "确认使用" and self.command and self.auto_confirm:
            self.command()

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)


def test_generate_chapter_draft_ui_updates_progress_for_parallel_variants(monkeypatch):
    logs = []
    shown = []
    refreshed = []

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_self = SimpleNamespace(
            filepath_var=FakeVar(tmpdir),
            master=FakeMaster(),
            btn_generate_chapter=FakeButton(),
            loaded_config={
                "llm_configs": {
                    "OpenCode": {
                        "interface_format": "opencode",
                        "api_key": "",
                        "base_url": "",
                        "model_name": "packy/qwen3.5-flash",
                        "temperature": 0.7,
                        "max_tokens": 1024,
                        "timeout": 30,
                    }
                }
            },
            prompt_draft_llm_var=FakeVar("OpenCode"),
            chapter_num_var=FakeVar("1"),
            word_number_var=FakeVar("1200"),
            user_guide_text=FakeText(""),
            characters_involved_var=FakeVar(""),
            key_items_var=FakeVar(""),
            scene_location_var=FakeVar(""),
            time_constraint_var=FakeVar(""),
            embedding_api_key_var=FakeVar(""),
            embedding_url_var=FakeVar(""),
            embedding_interface_format_var=FakeVar(""),
            embedding_model_name_var=FakeVar(""),
            embedding_retrieval_k_var=FakeVar("4"),
            draft_variants_var=FakeVar("3"),
            char_inv_text=FakeText(""),
            safe_get_int=lambda var, default=0: int(var.get().strip()) if str(var.get()).strip() else default,
            safe_log=logs.append,
            refresh_draft_variants_list=lambda: refreshed.append("refresh"),
            show_chapter_in_textbox=lambda text: shown.append(text),
            handle_exception=lambda msg: (_ for _ in ()).throw(AssertionError(msg)),
        )
        fake_self.generate_chapter_draft_ui = lambda: generation_handlers.generate_chapter_draft_ui(fake_self)

        class ImmediateThread:
            def __init__(self, target=None, args=(), daemon=True):
                self._target = target
                self._args = args

            def start(self):
                self._target(*self._args)

            def join(self):
                return None

        monkeypatch.setattr(generation_handlers.messagebox, "showwarning", lambda *args, **kwargs: None)
        monkeypatch.setattr(generation_handlers.messagebox, "askyesno", lambda *args, **kwargs: True)
        monkeypatch.setattr(generation_handlers, "build_chapter_prompt", lambda **kwargs: "测试提示词")
        monkeypatch.setattr(generation_handlers.threading, "Thread", ImmediateThread)
        monkeypatch.setattr(generation_handlers.ctk, "CTkToplevel", lambda *args, **kwargs: FakeDialog())
        monkeypatch.setattr(generation_handlers.ctk, "CTkTextbox", FakeTextbox)
        monkeypatch.setattr(generation_handlers.ctk, "CTkLabel", FakeLabel)
        monkeypatch.setattr(generation_handlers.ctk, "CTkFrame", FakeFrame)
        monkeypatch.setattr(generation_handlers.ctk, "CTkButton", FakeDialogButton)

        progress_updates = []
        original_controller = generation_handlers.TaskButtonController

        class RecordingController(original_controller):
            def set_progress(self, done, total):
                progress_updates.append((done, total))
                super().set_progress(done, total)

        monkeypatch.setattr(generation_handlers, "TaskButtonController", RecordingController)

        def fake_generate_chapter_draft(**kwargs):
            target_file = kwargs["target_file"]
            text = f"草稿-{os.path.basename(target_file)}"
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(text)
            return text

        monkeypatch.setattr(
            "novel_generator.chapter.generate_chapter_draft",
            fake_generate_chapter_draft,
        )

        generation_handlers.generate_chapter_draft_ui(fake_self)

        assert progress_updates[0] == (0, 3)
        assert progress_updates[-1] == (3, 3)
        assert refreshed == ["refresh"]
        assert shown and shown[-1].startswith("草稿-")
        assert fake_self.btn_generate_chapter.text == "Step3. 生成草稿"


def test_generate_chapter_prompt_dialog_disables_buttons_after_confirm(monkeypatch):
    logs = []

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_self = SimpleNamespace(
            filepath_var=FakeVar(tmpdir),
            master=FakeMaster(),
            btn_generate_chapter=FakeButton(),
            loaded_config={
                "llm_configs": {
                    "OpenCode": {
                        "interface_format": "opencode",
                        "api_key": "",
                        "base_url": "",
                        "model_name": "packy/qwen3.5-flash",
                        "temperature": 0.7,
                        "max_tokens": 1024,
                        "timeout": 30,
                    }
                }
            },
            prompt_draft_llm_var=FakeVar("OpenCode"),
            chapter_num_var=FakeVar("1"),
            word_number_var=FakeVar("1200"),
            user_guide_text=FakeText(""),
            characters_involved_var=FakeVar(""),
            key_items_var=FakeVar(""),
            scene_location_var=FakeVar(""),
            time_constraint_var=FakeVar(""),
            embedding_api_key_var=FakeVar(""),
            embedding_url_var=FakeVar(""),
            embedding_interface_format_var=FakeVar(""),
            embedding_model_name_var=FakeVar(""),
            embedding_retrieval_k_var=FakeVar("4"),
            draft_variants_var=FakeVar("1"),
            char_inv_text=FakeText(""),
            safe_get_int=lambda var, default=0: int(var.get().strip()) if str(var.get()).strip() else default,
            safe_log=logs.append,
            refresh_draft_variants_list=lambda: None,
            show_chapter_in_textbox=lambda text: None,
            handle_exception=lambda msg: (_ for _ in ()).throw(AssertionError(msg)),
        )
        fake_self.generate_chapter_draft_ui = lambda: generation_handlers.generate_chapter_draft_ui(fake_self)

        class ImmediateThread:
            def __init__(self, target=None, args=(), daemon=True):
                self._target = target
                self._args = args

            def start(self):
                self._target(*self._args)

            def join(self):
                return None

        FakeDialogButton.instances = []
        FakeDialogButton.auto_confirm = True
        monkeypatch.setattr(generation_handlers.messagebox, "showwarning", lambda *args, **kwargs: None)
        monkeypatch.setattr(generation_handlers.messagebox, "askyesno", lambda *args, **kwargs: True)
        monkeypatch.setattr(generation_handlers, "build_chapter_prompt", lambda **kwargs: "测试提示词")
        monkeypatch.setattr(generation_handlers.threading, "Thread", ImmediateThread)
        monkeypatch.setattr(generation_handlers.ctk, "CTkToplevel", lambda *args, **kwargs: FakeDialog())
        monkeypatch.setattr(generation_handlers.ctk, "CTkTextbox", FakeTextbox)
        monkeypatch.setattr(generation_handlers.ctk, "CTkLabel", FakeLabel)
        monkeypatch.setattr(generation_handlers.ctk, "CTkFrame", FakeFrame)
        monkeypatch.setattr(generation_handlers.ctk, "CTkButton", FakeDialogButton)
        monkeypatch.setattr(
            "novel_generator.chapter.generate_chapter_draft",
            lambda **kwargs: "单稿内容",
        )

        generation_handlers.generate_chapter_draft_ui(fake_self)

        confirm_button = next(btn for btn in FakeDialogButton.instances if btn.text == "确认使用")
        cancel_button = next(btn for btn in FakeDialogButton.instances if btn.text == "取消请求")
        assert {"state": "disabled"} in confirm_button.configure_calls
        assert {"state": "disabled"} in cancel_button.configure_calls
