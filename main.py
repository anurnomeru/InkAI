# main.py
# -*- coding: utf-8 -*-
import logging
import sys

logging.basicConfig(
    filename="app.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
import customtkinter as ctk
from ui import NovelGeneratorGUI

# --- Runtime patch: guard customtkinter CTkTextbox scrollbar checker from calling
# widget methods after destruction (prevents tight exception loops / UI freeze)
try:
    import tkinter as tk  # type: ignore
    from tkinter import TclError  # type: ignore

    if hasattr(ctk, "CTkTextbox"):
        _orig_check = getattr(ctk.CTkTextbox, "_check_if_scrollbars_needed", None)

        def _safe_check_if_scrollbars_needed(
            self, event=None, continue_loop: bool = False, *args, **kwargs
        ):  # type: ignore[override]
            try:
                tb = getattr(self, "_textbox", None)
                if tb is None:
                    return
                try:
                    if not tb.winfo_exists():  # 0 if destroyed
                        return
                except Exception:
                    return
                if callable(_orig_check):
                    return _orig_check(self, event=event, continue_loop=continue_loop)
            except (TclError, RuntimeError):
                return
            except Exception:
                return

        if callable(_orig_check):
            setattr(
                ctk.CTkTextbox,
                "_check_if_scrollbars_needed",
                _safe_check_if_scrollbars_needed,
            )

    # Patch ScalingTracker.check_dpi_scaling to handle destroyed windows gracefully
    from customtkinter.windows.widgets.scaling.scaling_tracker import (
        ScalingTracker as _ST,
    )  # type: ignore

    _orig_dpi = getattr(_ST, "check_dpi_scaling", None)
    if callable(_orig_dpi):

        def _safe_check_dpi_scaling():
            try:
                new_scaling_detected = False
                for window in list(_ST.window_widgets_dict):
                    try:
                        if window.winfo_exists() and not window.state() == "iconic":
                            current = _ST.get_window_dpi_scaling(window)
                            if current != _ST.window_dpi_scaling_dict.get(window):
                                _ST.window_dpi_scaling_dict[window] = current
                                if sys.platform.startswith("win"):
                                    window.attributes("-alpha", 0.15)
                                window.block_update_dimensions_event()
                                _ST.update_scaling_callbacks_for_window(window)
                                window.unblock_update_dimensions_event()
                                if sys.platform.startswith("win"):
                                    window.attributes("-alpha", 1)
                                new_scaling_detected = True
                    except Exception:
                        continue
                for app in list(_ST.window_widgets_dict.keys()):
                    try:
                        if new_scaling_detected:
                            app.after(
                                _ST.loop_pause_after_new_scaling,
                                _safe_check_dpi_scaling,
                            )
                        else:
                            app.after(_ST.update_loop_interval, _safe_check_dpi_scaling)
                        return
                    except Exception:
                        continue
                _ST.update_loop_running = False
            except Exception:
                _ST.update_loop_running = False
                return

        setattr(
            _ST,
            "check_dpi_scaling",
            classmethod(lambda cls=_ST: _safe_check_dpi_scaling()),
        )
except Exception:
    # Best-effort patch; if anything fails, continue with default behavior
    pass


def _force_show(app):
    try:
        app.deiconify()
    except Exception:
        pass
    try:
        app.lift()
    except Exception:
        pass
    try:
        app.attributes("-topmost", True)
        app.after(1200, lambda: app.attributes("-topmost", False))
    except Exception:
        pass
    try:
        app.focus_force()
    except Exception:
        pass
    try:
        app.update_idletasks()
        app.update()
    except Exception:
        pass


def main():
    logging.info("main(): creating CTk window...")
    app = ctk.CTk()
    try:
        app.geometry("900x650")
        splash = ctk.CTkLabel(app, text="Loading UI...", font=("Microsoft YaHei", 18))
        splash.pack(padx=24, pady=24)
        # 可见性与映射状态日志
        app.bind("<Map>", lambda e: logging.info("Tk window mapped"))
        app.bind(
            "<Visibility>",
            lambda e: logging.info(f"Tk visibility state: {app.state()}"),
        )
        _force_show(app)
        # 轻量心跳
        app.after(500, lambda: logging.info("Heartbeat: UI alive 0.5s"))
        app.after(2000, lambda: logging.info("Heartbeat: UI alive 2s"))
    except Exception:
        splash = None
    logging.info("main(): constructing NovelGeneratorGUI...")
    gui = NovelGeneratorGUI(app)
    try:
        if splash is not None:
            splash.destroy()
            app.update_idletasks()
    except Exception:
        pass
    logging.info("mainloop(): entering...")
    app.mainloop()
    logging.info("mainloop(): exited")


if __name__ == "__main__":
    main()
