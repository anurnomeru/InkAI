# ui/main_tab.py

# -*- coding: utf-8 -*-

import customtkinter as ctk
from tkinter import messagebox
import os

from ui.context_menu import TextWidgetContextMenu
from ui.i18n import t
from ui.text_shortcuts import install_text_shortcuts
from utils import save_string_to_txt, clear_file_content
from ui.theme import FONT_FAMILY, FONT_SIZES, SPACING, PRIMARY_COLOR, make_button
from ui.toast import show_toast
from ui.progress import show_progress, hide_progress
from config_manager import save_config


def _apply_split_ratio(self, r: float) -> None:
    try:
        r = max(0.2, min(0.8, float(r)))
    except Exception:
        r = 0.62
    self.split_ratio = r
    lw = int(r * 100)
    rw = max(1, 100 - lw)
    self.main_tab.columnconfigure(0, weight=lw)
    self.main_tab.columnconfigure(2, weight=rw)


def _with_progress(self, func, progress_text: str):
    def _inner():
        top = None
        try:
            top, _ = show_progress(self.left_frame, progress_text)
        except Exception:
            top = None
        try:
            func()
        finally:
            try:
                if top is not None:
                    hide_progress(top)
            except Exception:
                pass

    return _inner


def build_main_tab(self):
    """
    主要功能页：左侧编辑与操作，右侧参数/可选区（配置已抽离到“配置中心”顶层Tab）
    """
    self.main_tab = self.tabview.add(t("主要功能"))
    self.main_tab.rowconfigure(0, weight=1)

    # 初始比例：优先读取配置
    try:
        op = (
            self.loaded_config.get("other_params", {})
            if hasattr(self, "loaded_config")
            else {}
        )
        ratio = float(op.get("split_ratio", 0.62))
    except Exception:
        ratio = 0.62
    self.split_ratio = max(0.2, min(0.8, ratio))

    # 3列：左栏、分隔、右栏
    self.main_tab.columnconfigure(0, weight=int(self.split_ratio * 100))
    self.main_tab.columnconfigure(1, weight=0)
    self.main_tab.columnconfigure(2, weight=max(1, 100 - int(self.split_ratio * 100)))

    # 左侧与右侧容器
    self.left_frame = ctk.CTkFrame(self.main_tab)
    self.left_frame.grid(
        row=0, column=0, sticky="nsew", padx=SPACING["sm"], pady=SPACING["sm"]
    )

    self.split_handle = ctk.CTkFrame(self.main_tab, width=6)
    try:
        self.split_handle.configure(cursor="sb_h_double_arrow")
    except Exception:
        pass
    self.split_handle.grid(row=0, column=1, sticky="ns")

    self.right_frame = ctk.CTkFrame(self.main_tab)
    self.right_frame.grid(
        row=0, column=2, sticky="nsew", padx=SPACING["sm"], pady=SPACING["sm"]
    )

    # 拖拽更新 + 松手保存
    def _on_handle_drag(event):
        try:
            total = self.main_tab.winfo_width()
            if total <= 0:
                return
            x = self.main_tab.winfo_pointerx() - self.main_tab.winfo_rootx()
            _apply_split_ratio(self, x / total)
        except Exception:
            pass

    def _on_handle_release(event):
        try:
            if not isinstance(self.loaded_config, dict):
                return
            self.loaded_config.setdefault("other_params", {})
            self.loaded_config["other_params"]["split_ratio"] = float(self.split_ratio)
            save_config(self.loaded_config, self.config_file)
        except Exception:
            pass

    self.split_handle.bind("<B1-Motion>", _on_handle_drag)
    self.split_handle.bind("<ButtonRelease-1>", _on_handle_release)

    build_left_layout(self)
    build_right_layout(self)


def build_left_layout(self):
    """
    左侧：章节编辑 + Step流程 + 草稿变体 + 日志
    """
    self.left_frame.grid_rowconfigure(0, weight=0)
    self.left_frame.grid_rowconfigure(1, weight=2)
    self.left_frame.grid_rowconfigure(2, weight=0)
    self.left_frame.grid_rowconfigure(3, weight=0)
    self.left_frame.grid_rowconfigure(4, weight=0)
    self.left_frame.grid_rowconfigure(5, weight=1)

    # 顶部：标题 + 快捷键提示 + 保存
    header_frame = ctk.CTkFrame(self.left_frame)
    header_frame.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=SPACING["sm"],
        pady=(SPACING["sm"], SPACING["xs"]),
    )
    header_frame.columnconfigure(0, weight=1)
    self.left_frame.columnconfigure(0, weight=1)

    self.chapter_label = ctk.CTkLabel(
        header_frame,
        text=t("本章内容（可编辑） 字数："),
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    self.chapter_label.grid(row=0, column=0, sticky="w")

    self.save_hint_label = ctk.CTkLabel(
        header_frame,
        text=t("快捷键：Ctrl+S"),
        text_color="#6B7280",
        font=(FONT_FAMILY, FONT_SIZES["sm"]),
    )
    self.save_hint_label.grid(row=0, column=1, padx=(SPACING["sm"], 0), sticky="e")

    make_button(
        header_frame,
        text=t("保存草稿"),
        command=self.save_main_editor_content,
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=2, padx=SPACING["sm"], sticky="e")

    try:
        self.finalized_hint_label
    except Exception:
        self.finalized_hint_label = None
    if self.finalized_hint_label is None:
        self.finalized_hint_label = ctk.CTkLabel(
            header_frame,
            text="",
            text_color="green",
            font=(FONT_FAMILY, FONT_SIZES["md"]),
        )
    self.finalized_hint_label.grid(row=0, column=3, padx=(SPACING["sm"], 0), sticky="e")

    # 编辑区
    self.chapter_result = ctk.CTkTextbox(
        self.left_frame, wrap="word", font=(FONT_FAMILY, FONT_SIZES["lg"])
    )
    install_text_shortcuts(self.chapter_result)
    TextWidgetContextMenu(self.chapter_result)
    self.chapter_result.grid(
        row=1, column=0, sticky="nsew", padx=SPACING["sm"], pady=(0, SPACING["sm"])
    )

    def update_word_count(event=None):
        text = self.chapter_result.get("0.0", "end")
        count = len(text) - 1
        self.chapter_label.configure(
            text=t("本章内容（可编辑） 字数：{count}").format(count=count)
        )

    self.chapter_result.bind("<KeyRelease>", update_word_count)
    self.chapter_result.bind("<ButtonRelease>", update_word_count)
    self.chapter_result.bind("<Control-s>", lambda e: self.save_main_editor_content())

    # Step按钮（使用进度框包装长耗时）
    step = ctk.CTkFrame(self.left_frame)
    step.grid(row=2, column=0, sticky="ew", padx=SPACING["sm"], pady=SPACING["sm"])
    step.columnconfigure((0, 1, 2, 3, 4), weight=1)

    make_button(
        step,
        text=t("Step1. 生成架构"),
        command=_with_progress(
            self, self.generate_novel_architecture_ui, t("生成架构中…")
        ),
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=0, padx=5, pady=2, sticky="ew")
    make_button(
        step,
        text=t("Step2. 生成目录"),
        command=_with_progress(
            self, self.generate_chapter_blueprint_ui, t("生成目录中…")
        ),
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
    make_button(
        step,
        text=t("Step3. 生成草稿"),
        command=_with_progress(self, self.generate_chapter_draft_ui, t("生成草稿中…")),
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=2, padx=5, pady=2, sticky="ew")
    make_button(
        step,
        text=t("Step4. 定稿章节"),
        command=_with_progress(self, self.finalize_chapter_ui, t("定稿中…")),
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=3, padx=5, pady=2, sticky="ew")
    make_button(
        step,
        text=t("批量生成"),
        command=_with_progress(self, self.generate_batch_ui, t("批量生成中…")),
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=4, padx=5, pady=2, sticky="ew")

    # 草稿变体（选择）
    dv = ctk.CTkFrame(self.left_frame)
    dv.grid(row=3, column=0, sticky="ew", padx=SPACING["sm"], pady=(0, SPACING["sm"]))
    dv.columnconfigure(0, weight=0)
    dv.columnconfigure(1, weight=1)
    dv.columnconfigure(2, weight=0)

    self.draft_variant_select_var = ctk.StringVar(value="")
    ctk.CTkLabel(
        dv, text=t("草稿变体（选择）："), font=(FONT_FAMILY, FONT_SIZES["md"])
    ).grid(row=0, column=0, padx=SPACING["sm"], pady=SPACING["xs"], sticky="w")
    self.draft_variant_select_menu = ctk.CTkOptionMenu(
        dv,
        values=[],
        variable=self.draft_variant_select_var,
        command=self.on_draft_variant_selected,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    self.draft_variant_select_menu.grid(
        row=0, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="ew"
    )

    self.draft_empty_label = ctk.CTkLabel(
        dv,
        text=t("暂无草稿变体，点击上方按钮生成或先保存本章…"),
        text_color="#6B7280",
        font=(FONT_FAMILY, FONT_SIZES["sm"]),
    )
    self.draft_empty_label.grid(
        row=1,
        column=0,
        columnspan=3,
        padx=SPACING["sm"],
        pady=(SPACING["xs"], 0),
        sticky="w",
    )
    self.draft_empty_label.grid_remove()

    make_button(
        dv,
        text=t("刷新变体"),
        command=self.refresh_draft_variants_list,
        kind="text",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=2, padx=SPACING["sm"], pady=SPACING["xs"], sticky="e")

    # 日志
    ctk.CTkLabel(
        self.left_frame, text=t("输出日志 (只读)"), font=(FONT_FAMILY, FONT_SIZES["md"])
    ).grid(row=4, column=0, padx=SPACING["sm"], pady=(SPACING["sm"], 0), sticky="w")
    self.log_text = ctk.CTkTextbox(
        self.left_frame, wrap="word", font=(FONT_FAMILY, FONT_SIZES["md"])
    )
    install_text_shortcuts(self.log_text, enable_undo=False)
    TextWidgetContextMenu(self.log_text)
    self.log_text.grid(
        row=5, column=0, sticky="nsew", padx=SPACING["sm"], pady=(0, SPACING["sm"])
    )
    self.log_text.configure(state="disabled")


def build_right_layout(self):
    """
    右侧：参数区与可选操作区（配置已在“配置中心”顶层Tab）。
    """
    self.right_frame.grid_rowconfigure(0, weight=0)
    self.right_frame.grid_rowconfigure(1, weight=1)
    self.right_frame.grid_rowconfigure(2, weight=0)
    self.right_frame.columnconfigure(0, weight=1)

    if not getattr(self, "config_as_tab", False):
        self.config_frame = ctk.CTkFrame(
            self.right_frame, corner_radius=10, border_width=2, border_color="gray"
        )
        self.config_frame.grid(
            row=0, column=0, sticky="ew", padx=SPACING["sm"], pady=SPACING["sm"]
        )
        self.config_frame.columnconfigure(0, weight=1)


def save_main_editor_content(self):
    filepath = self.filepath_var.get().strip() if hasattr(self, "filepath_var") else ""
    if not filepath:
        try:
            messagebox.showwarning(t("警告"), t("请先配置保存文件路径"))
        except Exception:
            pass
        return
    try:
        chap_str = (
            str(self.chapter_num_var.get()).strip()
            if hasattr(self, "chapter_num_var")
            else "1"
        )
        chap_num = int(chap_str) if chap_str.isdigit() else 1
    except Exception:
        chap_num = 1
    try:
        os.makedirs(os.path.join(filepath, "chapters"), exist_ok=True)
        chapter_file = os.path.join(filepath, "chapters", f"chapter_{chap_num}.txt")
        content = self.chapter_result.get("0.0", "end").strip()
        clear_file_content(chapter_file)
        save_string_to_txt(content, chapter_file)
        if hasattr(self, "safe_log"):
            self.safe_log(t("已保存本章到：") + chapter_file)
        try:
            self.refresh_draft_variants_list()
        except Exception:
            pass
        try:
            show_toast(
                self.left_frame, t("已保存草稿"), kind="success", duration_ms=1300
            )
        except Exception:
            pass
    except Exception:
        try:
            messagebox.showerror(t("错误"), t("保存失败，请检查保存路径或权限。"))
            show_toast(self.left_frame, t("保存失败"), kind="error", duration_ms=1600)
        except Exception:
            pass
