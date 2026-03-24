# ui/text_shortcuts.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from ui.i18n import t
import tkinter as tk
from typing import Optional, List, Tuple


def _get_text(widget: tk.Widget) -> str:
    try:
        return widget.get("1.0", "end-1c")
    except Exception:
        return ""


def _apply_text(widget: tk.Widget, text: str) -> None:
    try:
        state = widget.cget("state") if hasattr(widget, "cget") else None
        if state == "disabled":
            return  # do not mutate disabled widgets (e.g., log view)
        widget.delete("1.0", "end")
        if text:
            widget.insert("1.0", text)
    except Exception:
        pass


def _index_to_tk(text: str, pos: int) -> str:
    if pos <= 0:
        return "1.0"
    line = text.count("\n", 0, pos) + 1
    last_nl = text.rfind("\n", 0, pos)
    col = pos if last_nl < 0 else pos - (last_nl + 1)
    return f"{line}.{col}"


def _find_all(text: str, term: str, case: bool) -> List[Tuple[int, int]]:
    if not term:
        return []
    hay = text if case else text.lower()
    needle = term if case else term.lower()
    i = 0
    res: List[Tuple[int, int]] = []
    while True:
        j = hay.find(needle, i)
        if j == -1:
            break
        res.append((j, j + len(term)))
        i = j + (1 if len(term) == 0 else len(term))
    return res


def _ensure_tags(widget: tk.Widget) -> None:
    try:
        widget.tag_configure("_find_current", background="#ffcc66")
    except Exception:
        pass


def _clear_find_tags(widget: tk.Widget) -> None:
    try:
        widget.tag_remove("_find_current", "1.0", "end")
    except Exception:
        pass


def _jump_to(widget: tk.Widget, start: str, end: str) -> None:
    try:
        widget.see(start)
        _clear_find_tags(widget)
        widget.tag_add("_find_current", start, end)
    except Exception:
        pass


def _bind_once(widget: tk.Widget, sequence: str, func):
    # Avoid duplicate bindings if installed twice accidentally
    key = f"_bind_{sequence}"
    if getattr(widget, key, False):
        return
    widget.bind(sequence, func)
    setattr(widget, key, True)


def _snapshot(widget: tk.Widget):
    # Debounced push of current content into undo stack
    try:
        text = _get_text(widget)
        stack: list = getattr(widget, "_undo_stack", [])
        if not stack or stack[-1] != text:
            stack.append(text)
            setattr(widget, "_undo_stack", stack)
        # Any new change invalidates redo stack
        setattr(widget, "_redo_stack", [])
    except Exception:
        pass


def _schedule_snapshot(widget: tk.Widget, delay_ms: int = 400):
    try:
        prev = getattr(widget, "_snap_after_id", None)
        if prev is not None:
            try:
                widget.after_cancel(prev)
            except Exception:
                pass
        after_id = widget.after(delay_ms, lambda: _snapshot(widget))
        setattr(widget, "_snap_after_id", after_id)
    except Exception:
        pass


def _undo(widget: tk.Widget, event=None):
    try:
        stack: list = getattr(widget, "_undo_stack", [])
        if not stack:
            return "break"
        current = _get_text(widget)
        # If current equals top, pop it to get previous
        if stack and stack[-1] == current and len(stack) >= 2:
            stack.pop()
        if not stack:
            return "break"
        prev_text = stack.pop()
        redo: list = getattr(widget, "_redo_stack", [])
        redo.append(current)
        setattr(widget, "_redo_stack", redo)
        _apply_text(widget, prev_text)
        return "break"
    except Exception:
        return "break"


def _redo(widget: tk.Widget, event=None):
    try:
        redo: list = getattr(widget, "_redo_stack", [])
        if not redo:
            return "break"
        current = _get_text(widget)
        next_text = redo.pop()
        stack: list = getattr(widget, "_undo_stack", [])
        stack.append(current)
        setattr(widget, "_undo_stack", stack)
        _apply_text(widget, next_text)
        return "break"
    except Exception:
        return "break"

def _open_find_dialog(widget: tk.Widget, event=None):
    try:
        _ensure_tags(widget)
        root = widget.winfo_toplevel()
        dlg = ctk.CTkToplevel(root)
        dlg.title(t("查找"))
        dlg.geometry("360x130")
        dlg.transient(root)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        entry = ctk.CTkEntry(frame)
        entry.pack(fill="x", padx=2, pady=(0,6))
        last_term = getattr(widget, "_find_term", "")
        if last_term:
            entry.insert(0, last_term)
        entry.focus_set()

        opts = ctk.CTkFrame(frame)
        opts.pack(fill="x", padx=2, pady=2)

        case_var = tk.BooleanVar(value=getattr(widget, "_find_case", False))
        case_chk = ctk.CTkCheckBox(opts, text=t("区分大小写"), variable=case_var)
        case_chk.pack(side="left")

        def do_prev():
            setattr(widget, "_find_term", entry.get())
            setattr(widget, "_find_case", bool(case_var.get()))
            _find_prev(widget)

        def do_next():
            setattr(widget, "_find_term", entry.get())
            setattr(widget, "_find_case", bool(case_var.get()))
            _find_next(widget)

        btn_prev = ctk.CTkButton(opts, text=t("上一条"), width=80, command=do_prev)
        btn_prev.pack(side="right", padx=(6,0))
        btn_next = ctk.CTkButton(opts, text=t("下一条"), width=80, command=do_next)
        btn_next.pack(side="right")

        def on_return(e):
            do_next(); return "break"
        def on_shift_return(e):
            do_prev(); return "break"
        def on_esc(e):
            try:
                dlg.grab_release()
            except Exception:
                pass
            dlg.destroy(); return "break"
        entry.bind("<Return>", on_return)
        entry.bind("<Shift-Return>", on_shift_return)
        dlg.bind("<Escape>", on_esc)

        if last_term:
            do_next()
        return "break"
    except Exception:
        return "break"
def _find_next(widget: tk.Widget, event=None):
    try:
        term: str = getattr(widget, "_find_term", "")
        case: bool = getattr(widget, "_find_case", False)
        text = _get_text(widget)
        if not term:
            return "break"
        matches = _find_all(text, term, case)
        if not matches:
            return "break"
        idx = getattr(widget, "_find_idx", -1) + 1
        if idx >= len(matches):
            idx = 0
        setattr(widget, "_find_idx", idx)
        start, end = matches[idx]
        start_i = _index_to_tk(text, start)
        end_i = _index_to_tk(text, end)
        _jump_to(widget, start_i, end_i)
        return "break"
    except Exception:
        return "break"


def _find_prev(widget: tk.Widget, event=None):
    try:
        term: str = getattr(widget, "_find_term", "")
        case: bool = getattr(widget, "_find_case", False)
        text = _get_text(widget)
        if not term:
            return "break"
        matches = _find_all(text, term, case)
        if not matches:
            return "break"
        idx = getattr(widget, "_find_idx", 0) - 1
        if idx < 0:
            idx = len(matches) - 1
        setattr(widget, "_find_idx", idx)
        start, end = matches[idx]
        start_i = _index_to_tk(text, start)
        end_i = _index_to_tk(text, end)
        _jump_to(widget, start_i, end_i)
        return "break"
    except Exception:
        return "break"


def install_text_shortcuts(widget: tk.Widget, enable_undo: bool = True, enable_search: bool = True):
    """Install Ctrl+Z/Ctrl+Shift+Z (undo/redo) and Ctrl+F/F3 search on a CTkTextbox/tk.Text.

    This function is idempotent; calling it multiple times is safe.
    """
    if getattr(widget, "_shortcuts_installed", False):
        return

    # Initialize undo stack with current content
    if enable_undo:
        try:
            setattr(widget, "_undo_stack", [_get_text(widget)])
            setattr(widget, "_redo_stack", [])
            # Common typing/paste events to snapshot content
            for seq in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
                _bind_once(widget, seq, lambda e, w=widget: (_schedule_snapshot(w), None))
            _bind_once(widget, "<Control-z>", lambda e, w=widget: _undo(w, e))
            _bind_once(widget, "<Control-Z>", lambda e, w=widget: _undo(w, e))
            _bind_once(widget, "<Control-Shift-z>", lambda e, w=widget: _redo(w, e))
            _bind_once(widget, "<Control-Shift-Z>", lambda e, w=widget: _redo(w, e))
            _bind_once(widget, "<Control-y>", lambda e, w=widget: _redo(w, e))
            _bind_once(widget, "<Control-Y>", lambda e, w=widget: _redo(w, e))
        except Exception:
            pass

    if enable_search:
        try:
            _ensure_tags(widget)
            _bind_once(widget, "<Control-f>", lambda e, w=widget: _open_find_dialog(w, e))
            _bind_once(widget, "<Control-F>", lambda e, w=widget: _open_find_dialog(w, e))
            _bind_once(widget, "<F3>", lambda e, w=widget: _find_next(w, e))
            _bind_once(widget, "<Shift-F3>", lambda e, w=widget: _find_prev(w, e))
        except Exception:
            pass

    setattr(widget, "_shortcuts_installed", True)







