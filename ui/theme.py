# ui/theme.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import customtkinter as ctk

# Design tokens (basic)
FONT_FAMILY = "Microsoft YaHei"
FONT_SIZES = {
    "xs": 10,
    "sm": 12,
    "md": 13,
    "lg": 14,
    "xl": 16,
    "xxl": 18,
}

SPACING = {
    "xs": 4,
    "sm": 6,
    "md": 8,
    "lg": 12,
    "xl": 16,
}

RADIUS = 8
BORDER_COLOR = "#D1D5DB"  # neutral-300
PRIMARY_COLOR = "#3B82F6"  # blue-500
DANGER_COLOR = "#EF4444"  # red-500
SUCCESS_COLOR = "#10B981"  # emerald-500
WARNING_COLOR = "#F59E0B"  # amber-500

CONTROL_HEIGHT = 36  # unified height for Entry/Button/OptionMenu


def init_appearance(mode: str = "system", theme: str = "blue") -> None:
    """Initialize global appearance and default theme for customtkinter.
    mode: "light" | "dark" | "system"
    theme: built-in CTk themes: "blue", "dark-blue", "green" (or path)
    """
    try:
        ctk.set_appearance_mode(mode)
    except Exception:
        pass
    try:
        ctk.set_default_color_theme(theme)
    except Exception:
        pass


def apply_card_style(frame: ctk.CTkFrame) -> None:
    """Apply a simple 'card' style to a CTkFrame."""
    try:
        frame.configure(corner_radius=RADIUS, border_width=1, border_color=BORDER_COLOR)
    except Exception:
        pass


def make_button(
    parent, text: str, command, kind: str = "primary", **kwargs
) -> ctk.CTkButton:
    """Factory for CTkButton with semantic styles: primary|secondary|danger|text."""
    fg = kwargs.pop("fg_color", None)
    if kind == "primary":
        fg = fg or PRIMARY_COLOR
    elif kind == "danger":
        fg = fg or DANGER_COLOR
    elif kind == "secondary":
        # keep framework default background
        fg = fg or None
    elif kind == "text":
        # text-like button: transparent background
        fg = fg or "transparent"
    btn = ctk.CTkButton(parent, text=text, command=command, fg_color=fg, **kwargs)
    return btn

    try:
        ctk.set_default_color_theme(theme)
    except Exception:
        pass


def apply_card_style(frame: ctk.CTkFrame) -> None:
    """Apply a simple 'card' style to a CTkFrame."""
    try:
        frame.configure(corner_radius=RADIUS, border_width=1, border_color=BORDER_COLOR)
    except Exception:
        pass
