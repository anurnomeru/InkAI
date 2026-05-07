# ui/running_button.py
# -*- coding: utf-8 -*-

class TaskButtonController:
    def __init__(
        self,
        button,
        idle_text: str,
        running_text: str,
        stop_text: str,
        confirm_stop,
        on_request_stop,
        idle_command=None,
    ):
        self.button = button
        self.idle_text = idle_text
        self.running_text = running_text
        self.stop_text = stop_text
        self.confirm_stop = confirm_stop
        self.on_request_stop = on_request_stop
        self.idle_command = idle_command
        self._running = False
        self._progress = None
        self._spinner_job = None
        self._spinner_index = 0
        self._spinner_frames = ("|", "/", "-", "\\")

    @property
    def running(self) -> bool:
        return self._running

    def start(self):
        self._running = True
        self._progress = None
        self._spinner_index = 0
        self.button.configure(command=self._handle_click)
        self._apply_running_text()
        self._schedule_spinner()

    def finish(self):
        self._running = False
        self._progress = None
        self._cancel_spinner()
        kwargs = {"text": self.idle_text}
        if self.idle_command is not None:
            kwargs["command"] = self.idle_command
        self.button.configure(**kwargs)

    def set_progress(self, done: int, total: int):
        self._progress = (max(0, int(done)), max(0, int(total)))
        if self._running:
            self._apply_running_text()

    def _handle_click(self):
        if not self._running:
            return
        if not self.confirm_stop():
            self._apply_running_text()
            return
        self.button.configure(text=self.stop_text)
        self.on_request_stop()

    def _format_running_text(self) -> str:
        frame = self._spinner_frames[self._spinner_index % len(self._spinner_frames)]
        text = f"{self.running_text} {frame}"
        if self._progress:
            done, total = self._progress
            if total > 0:
                text += f" {done}/{total}"
        return text

    def _apply_running_text(self):
        self.button.configure(text=self._format_running_text(), command=self._handle_click)

    def _schedule_spinner(self):
        if not self._running or not hasattr(self.button, "after"):
            return
        self._cancel_spinner()

        def _tick():
            if not self._running:
                return
            self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
            self._apply_running_text()
            self._schedule_spinner()

        self._spinner_job = self.button.after(160, _tick)

    def _cancel_spinner(self):
        if self._spinner_job and hasattr(self.button, "after_cancel"):
            try:
                self.button.after_cancel(self._spinner_job)
            except Exception:
                pass
        self._spinner_job = None
