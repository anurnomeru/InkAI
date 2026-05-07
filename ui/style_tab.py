# ui/style_tab.py
# -*- coding: utf-8 -*-

import os

import customtkinter as ctk

from tkinter import messagebox

from utils import read_file, save_string_to_txt, clear_file_content

from ui.context_menu import TextWidgetContextMenu
from ui.i18n import t

from ui.text_shortcuts import install_text_shortcuts


STYLE_GUIDANCE_FILENAME = "文风说明.txt"


def build_style_tab(self):
    self.style_tab = self.tabview.add(t("文风说明"))
    self.style_tab.rowconfigure(0, weight=0)
    self.style_tab.rowconfigure(1, weight=1)
    self.style_tab.columnconfigure(0, weight=1)

    load_btn = ctk.CTkButton(
        self.style_tab,
        text=t("加载 文风说明.txt"),
        command=self.load_style_guidance,
        font=("Microsoft YaHei", 12),
    )
    load_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self.style_word_count_label = ctk.CTkLabel(
        self.style_tab, text=t("字数："), font=("Microsoft YaHei", 12)
    )
    self.style_word_count_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    save_btn = ctk.CTkButton(
        self.style_tab,
        text=t("保存修改"),
        command=self.save_style_guidance,
        font=("Microsoft YaHei", 12),
    )
    save_btn.grid(row=0, column=2, padx=5, pady=5, sticky="e")

    self.style_text = ctk.CTkTextbox(
        self.style_tab, wrap="word", font=("Microsoft YaHei", 12)
    )
    install_text_shortcuts(self.style_text)

    def update_word_count(event=None):
        text = self.style_text.get("0.0", "end")
        count = len(text) - 1
        self.style_word_count_label.configure(text=t("字数：{n}").format(n=count))

    self.style_text.bind("<KeyRelease>", update_word_count)
    self.style_text.bind("<ButtonRelease>", update_word_count)
    TextWidgetContextMenu(self.style_text)
    self.style_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)


def load_style_guidance(self):
    filepath = self.filepath_var.get().strip()

    if not filepath:
        messagebox.showwarning(t("警告"), t("请先配置保存文件路径"))
        return

    filename = os.path.join(filepath, STYLE_GUIDANCE_FILENAME)
    content = read_file(filename)

    self.style_text.delete("0.0", "end")
    self.style_text.insert("0.0", content)

    self.log(f"已加载 {STYLE_GUIDANCE_FILENAME} 到编辑区")


def save_style_guidance(self):
    filepath = self.filepath_var.get().strip()

    if not filepath:
        messagebox.showwarning(t("警告"), t("请先配置保存文件路径"))
        return

    content = self.style_text.get("0.0", "end").strip()
    filename = os.path.join(filepath, STYLE_GUIDANCE_FILENAME)

    clear_file_content(filename)
    save_string_to_txt(content, filename)

    self.log(f"已保存对 {STYLE_GUIDANCE_FILENAME} 的修改")
