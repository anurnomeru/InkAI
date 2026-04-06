# ui/main_tab.py

# -*- coding: utf-8 -*-

import customtkinter as ctk

from tkinter import messagebox
from ui.context_menu import TextWidgetContextMenu
from ui.i18n import t
from ui.text_shortcuts import install_text_shortcuts
from utils import save_string_to_txt, clear_file_content
import os


def build_main_tab(self):
    """

    涓籘ab鍖呭惈宸︿晶鐨?本章内容"编辑妗嗗拰输出日志：屼互婂彸渚х殑涓昏鎿嶄綔鍜屽弬鏁拌缃尯

    """

    self.main_tab = self.tabview.add(t("主要功能"))

    self.main_tab.rowconfigure(0, weight=1)

    self.main_tab.columnconfigure(0, weight=1)

    self.main_tab.columnconfigure(1, weight=0)

    self.left_frame = ctk.CTkFrame(self.main_tab)

    self.left_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    self.right_frame = ctk.CTkFrame(self.main_tab)

    self.right_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

    build_left_layout(self)

    build_right_layout(self)


def build_left_layout(self):
    """

    宸︿晶鍖哄煙：氭湰绔犲唴瀹?可编辑? + Step娴佺▼按钮 + 输出日志(只读)

    """

    self.left_frame.grid_rowconfigure(0, weight=0)

    self.left_frame.grid_rowconfigure(1, weight=2)

    self.left_frame.grid_rowconfigure(2, weight=0)

    self.left_frame.grid_rowconfigure(3, weight=0)

    self.left_frame.grid_rowconfigure(4, weight=0)
    self.left_frame.grid_rowconfigure(5, weight=1)

    # Header: label + save button
    header_frame = ctk.CTkFrame(self.left_frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
    header_frame.columnconfigure(0, weight=1)
    self.left_frame.columnconfigure(0, weight=1)

    self.chapter_label = ctk.CTkLabel(
        header_frame, text=t("本章内容（可编辑） 字数："), font=("Microsoft YaHei", 12)
    )

    self.chapter_label.grid(row=0, column=0, padx=0, pady=0, sticky="w")
    # 保存草稿按钮
    self.btn_save_main = ctk.CTkButton(
        header_frame,
        text=t("保存草稿"),
        command=self.save_main_editor_content,
        font=("Microsoft YaHei", 12),
    )
    self.btn_save_main.grid(row=0, column=1, padx=5, pady=0, sticky="e")
    # 已定稿提示标签
    try:
        self.finalized_hint_label
    except Exception:
        self.finalized_hint_label = None
    if self.finalized_hint_label is None:
        self.finalized_hint_label = ctk.CTkLabel(
            header_frame, text="", text_color="green", font=("Microsoft YaHei", 12)
        )
    self.finalized_hint_label.grid(row=0, column=2, padx=(10, 0), pady=0, sticky="e")

    # 章节文本编辑妗?

    self.chapter_result = ctk.CTkTextbox(
        self.left_frame, wrap="word", font=("Microsoft YaHei", 14)
    )

    install_text_shortcuts(self.chapter_result)

    TextWidgetContextMenu(self.chapter_result)

    self.chapter_result.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

    def update_word_count(event=None):
        text = self.chapter_result.get("0.0", "end")

        count = len(text) - 1  # 鍑忓幓鏈€最后一涓崲琛岀

        self.chapter_label.configure(
            text=t("本章内容（可编辑） 字数：{count}").format(count=count)
        )

    self.chapter_result.bind("<KeyRelease>", update_word_count)

    self.chapter_result.bind("<ButtonRelease>", update_word_count)
    self.chapter_result.bind("<Control-s>", lambda e: self.save_main_editor_content())

    # Step 按钮区域

    self.step_buttons_frame = ctk.CTkFrame(self.left_frame)

    self.step_buttons_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

    self.step_buttons_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

    self.btn_generate_architecture = ctk.CTkButton(
        self.step_buttons_frame,
        text=t("Step1. 生成架构"),
        command=self.generate_novel_architecture_ui,
        font=("Microsoft YaHei", 12),
    )

    self.btn_generate_architecture.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

    self.btn_generate_directory = ctk.CTkButton(
        self.step_buttons_frame,
        text=t("Step2. 生成目录"),
        command=self.generate_chapter_blueprint_ui,
        font=("Microsoft YaHei", 12),
    )

    self.btn_generate_directory.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

    self.btn_generate_chapter = ctk.CTkButton(
        self.step_buttons_frame,
        text=t("Step3. 生成草稿"),
        command=self.generate_chapter_draft_ui,
        font=("Microsoft YaHei", 12),
    )

    self.btn_generate_chapter.grid(row=0, column=2, padx=5, pady=2, sticky="ew")

    self.btn_finalize_chapter = ctk.CTkButton(
        self.step_buttons_frame,
        text=t("Step4. 定稿章节"),
        command=self.finalize_chapter_ui,
        font=("Microsoft YaHei", 12),
    )

    self.btn_finalize_chapter.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

    self.btn_batch_generate = ctk.CTkButton(
        self.step_buttons_frame,
        text=t("批量生成"),
        command=self.generate_batch_ui,
        font=("Microsoft YaHei", 12),
    )

    self.btn_batch_generate.grid(row=0, column=4, padx=5, pady=2, sticky="ew")

    # ????????
    self.draft_variant_frame = ctk.CTkFrame(self.left_frame)
    self.draft_variant_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))
    self.draft_variant_frame.columnconfigure(1, weight=1)
    self.draft_variant_select_var = ctk.StringVar(value="")
    ctk.CTkLabel(self.draft_variant_frame, text="Draft Variants:").grid(
        row=0, column=0, padx=5, pady=2, sticky="w"
    )
    self.draft_variant_select_menu = ctk.CTkOptionMenu(
        self.draft_variant_frame,
        values=[],
        variable=self.draft_variant_select_var,
        command=self.on_draft_variant_selected,
    )
    self.draft_variant_select_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
    ctk.CTkButton(
        self.draft_variant_frame,
        text="Refresh Variants",
        command=self.refresh_draft_variants_list,
        width=100,
    ).grid(row=0, column=2, padx=5, pady=2, sticky="e")

    # 日志文本框

    log_label = ctk.CTkLabel(
        self.left_frame, text=t("输出日志 (只读)"), font=("Microsoft YaHei", 12)
    )

    log_label.grid(row=4, column=0, padx=5, pady=(5, 0), sticky="w")

    self.log_text = ctk.CTkTextbox(
        self.left_frame, wrap="word", font=("Microsoft YaHei", 12)
    )

    install_text_shortcuts(self.log_text, enable_undo=False)

    TextWidgetContextMenu(self.log_text)

    self.log_text.grid(row=5, column=0, sticky="nsew", padx=5, pady=(0, 5))

    self.log_text.configure(state="disabled")


def build_right_layout(self):
    """

    右侧区域：氶厤缃尯(tabview) + 小说涓诲弬鏁?+ €夊姛鑳芥寜閽?

    """

    self.right_frame.grid_rowconfigure(0, weight=0)

    self.right_frame.grid_rowconfigure(1, weight=1)

    self.right_frame.grid_rowconfigure(2, weight=0)

    self.right_frame.columnconfigure(0, weight=1)

    # 配置区（AI/Embedding：

    self.config_frame = ctk.CTkFrame(
        self.right_frame, corner_radius=10, border_width=2, border_color="gray"
    )

    self.config_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    self.config_frame.columnconfigure(0, weight=1)

    # 其余部分在 config_tab.py 涓?novel_params_tab.py 涓瀯寤?


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
    except Exception:
        try:
            messagebox.showerror(t("错误"), t("保存失败，请检查保存路径或权限。"))
        except Exception:
            pass
