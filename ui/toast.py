# ui/toast.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from typing import Literal, Union

ToastKind = Literal["info", "success", "warning", "error"]

KIND_COLORS = {
    "info": "#2563EB",  # blue-600
    "success": "#059669",  # emerald-600
    "warning": "#D97706",  # amber-600
    "error": "#DC2626",  # red-600
}


def _resolve_root(widget: ctk.CTkBaseClass) -> ctk.CTk:
    w = widget
    while getattr(w, "master", None) is not None:
        w = w.master  # type: ignore
    return w  # type: ignore[return-value]


def show_toast(
    widget: ctk.CTkBaseClass,
    text: str,
    kind: ToastKind = "info",
    duration_ms: int = 1600,
) -> None:
    """Show a lightweight toast near top-right of the main window.
    widget: any widget inside the app (used to locate the root)
    kind: info|success|warning|error controls background color
    duration_ms: auto-close delay
    """
    try:
        root = _resolve_root(widget)
        top = ctk.CTkToplevel(root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        bg = KIND_COLORS.get(kind, KIND_COLORS["info"])
        frame = ctk.CTkFrame(
            top, corner_radius=8, border_width=1, border_color="#93C5FD", fg_color=bg
        )
        frame.pack(fill="both", expand=True)
        label = ctk.CTkLabel(
            frame, text=text, text_color="#FFFFFF", font=("Microsoft YaHei", 12)
        )
        label.pack(padx=12, pady=8)
        root.update_idletasks()
        # position: top-right with margin
        try:
            x = root.winfo_x() + root.winfo_width() - top.winfo_reqwidth() - 24
            y = root.winfo_y() + 24
        except Exception:
            x, y = 60, 60
        top.geometry(f"+{x}+{y}")

        def _close():
            try:
                top.destroy()
            except Exception:
                pass

        top.after(duration_ms, _close)
    except Exception:
        # Fallback: ignore if toast fails
        pass
