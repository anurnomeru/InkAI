# ui/progress.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from typing import Tuple


def show_progress(
    parent: ctk.CTkBaseClass, text: str = "处理中…"
) -> Tuple[ctk.CTkToplevel, ctk.CTkProgressBar]:
    try:
        root = parent
        while getattr(root, "master", None) is not None:
            root = root.master  # type: ignore
        top = ctk.CTkToplevel(root)  # type: ignore[arg-type]
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        frame = ctk.CTkFrame(
            top, corner_radius=10, border_width=1, border_color="#CBD5E1"
        )
        frame.pack(fill="both", expand=True)
        label = ctk.CTkLabel(frame, text=text, font=("Microsoft YaHei", 13))
        label.pack(padx=16, pady=(14, 8))
        bar = ctk.CTkProgressBar(frame, mode="indeterminate")
        bar.pack(fill="x", padx=16, pady=(0, 14))
        try:
            bar.start()
        except Exception:
            pass
        # position center of window
        try:
            root.update_idletasks()
            w = 320
            h = 96
            x = root.winfo_x() + (root.winfo_width() - w) // 2
            y = root.winfo_y() + (root.winfo_height() - h) // 2
            top.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass
        return top, bar
    except Exception:
        # best effort
        top = ctk.CTkToplevel()  # fallback
        bar = ctk.CTkProgressBar(top, mode="indeterminate")
        return top, bar


def hide_progress(top: ctk.CTkToplevel) -> None:
    try:
        top.destroy()
    except Exception:
        pass
