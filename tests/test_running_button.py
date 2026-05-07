import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ui.running_button as running_button


class FakeButton:
    def __init__(self):
        self.configure_calls = []
        self.command = None
        self.state = "normal"
        self.text = ""
        self.after_calls = []
        self.after_cancel_calls = []

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)
        if "command" in kwargs:
            self.command = kwargs["command"]
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "text" in kwargs:
            self.text = kwargs["text"]

    def after(self, delay, callback):
        token = f"after-{len(self.after_calls) + 1}"
        self.after_calls.append((delay, callback, token))
        return token

    def after_cancel(self, token):
        self.after_cancel_calls.append(token)


def test_task_button_controller_start_and_finish_updates_button_text():
    button = FakeButton()
    idle_calls = []
    ctl = running_button.TaskButtonController(
        button=button,
        idle_text="生成草稿",
        running_text="生成草稿中…",
        stop_text="停止生成",
        confirm_stop=lambda: True,
        on_request_stop=lambda: None,
        idle_command=lambda: idle_calls.append("idle"),
    )

    ctl.start()
    assert "生成草稿中…" in button.text

    ctl.finish()
    assert button.text == "生成草稿"
    assert button.command is not None
    button.command()
    assert idle_calls == ["idle"]


def test_task_button_controller_second_click_requests_stop():
    button = FakeButton()
    stop_requests = []
    ctl = running_button.TaskButtonController(
        button=button,
        idle_text="润色选中",
        running_text="润色中…",
        stop_text="停止润色",
        confirm_stop=lambda: True,
        on_request_stop=lambda: stop_requests.append("stop"),
    )

    ctl.start()
    assert button.command is not None

    button.command()

    assert stop_requests == ["stop"]
    assert button.text == "停止润色"


def test_task_button_controller_set_progress_updates_running_text():
    button = FakeButton()
    ctl = running_button.TaskButtonController(
        button=button,
        idle_text="生成草稿",
        running_text="生成草稿中…",
        stop_text="停止生成",
        confirm_stop=lambda: True,
        on_request_stop=lambda: None,
    )

    ctl.start()
    ctl.set_progress(2, 5)

    assert "生成草稿中…" in button.text
    assert "2/5" in button.text


def test_task_button_controller_cancelled_stop_keeps_running_text():
    button = FakeButton()
    ctl = running_button.TaskButtonController(
        button=button,
        idle_text="润色选中",
        running_text="润色中…",
        stop_text="停止润色",
        confirm_stop=lambda: False,
        on_request_stop=lambda: None,
    )

    ctl.start()
    button.command()

    assert "润色中…" in button.text
