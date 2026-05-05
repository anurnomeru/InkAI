# ui/novel_params_tab.py

# -*- coding: utf-8 -*-

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.context_menu import TextWidgetContextMenu
from ui.i18n import t

from ui.text_shortcuts import install_text_shortcuts

from tooltips import tooltips
from ui.theme import (
    FONT_FAMILY,
    FONT_SIZES,
    SPACING,
    CONTROL_HEIGHT,
    DANGER_COLOR,
    apply_card_style,
    make_button,
)
from ui.progress import show_progress, hide_progress


def build_novel_params_area(self, start_row=1):
    # 右侧顶层：上部参数区填充（weight=1），下部按钮不填充
    try:
        self.right_frame.grid_rowconfigure(start_row, weight=1)
    except Exception:
        pass

    self.params_frame = ctk.CTkScrollableFrame(self.right_frame, orientation="vertical")
    self.params_frame.grid(
        row=start_row, column=0, sticky="nsew", padx=SPACING["sm"], pady=SPACING["sm"]
    )  # 上部填充
    self.params_frame.columnconfigure(0, weight=1)

    # 1) 基础信息卡片
    basic_card = ctk.CTkFrame(self.params_frame)
    apply_card_style(basic_card)
    basic_card.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, SPACING["sm"]))
    basic_card.columnconfigure(0, weight=0)
    basic_card.columnconfigure(1, weight=1)

    basic_header = ctk.CTkLabel(
        basic_card, text=t("基础信息"), font=(FONT_FAMILY, FONT_SIZES["xl"], "bold")
    )
    basic_header.grid(
        row=0,
        column=0,
        columnspan=2,
        padx=SPACING["sm"],
        pady=(SPACING["sm"], SPACING["xs"]),
        sticky="w",
    )

    # 主题(Topic)
    create_label_with_help_for_novel_params(
        self,
        parent=basic_card,
        label_text=t("主题(Topic):"),
        tooltip_key="topic",
        row=1,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        sticky="ne",
    )

    self.topic_text = ctk.CTkTextbox(
        basic_card,
        height=140,
        wrap="word",
        font=(FONT_FAMILY, FONT_SIZES["md"]),  # ↑增大高度
    )
    install_text_shortcuts(self.topic_text)
    TextWidgetContextMenu(self.topic_text)
    self.topic_text.grid(
        row=1, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="nsew"
    )
    if hasattr(self, "topic_default") and self.topic_default:
        self.topic_text.insert("0.0", self.topic_default)

    # 类型(Genre)
    create_label_with_help_for_novel_params(
        self,
        parent=basic_card,
        label_text=t("类型(Genre):"),
        tooltip_key="genre",
        row=2,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    genre_entry = ctk.CTkEntry(
        basic_card,
        textvariable=self.genre_var,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    genre_entry.grid(
        row=2, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="ew"
    )

    # 2) 章节设置卡片
    chapter_card = ctk.CTkFrame(self.params_frame)
    apply_card_style(chapter_card)
    chapter_card.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, SPACING["sm"]))
    chapter_card.columnconfigure(0, weight=0)
    chapter_card.columnconfigure(1, weight=1)

    chapter_header = ctk.CTkLabel(
        chapter_card, text=t("章节设置"), font=(FONT_FAMILY, FONT_SIZES["xl"], "bold")
    )
    chapter_header.grid(
        row=0,
        column=0,
        columnspan=2,
        padx=SPACING["sm"],
        pady=(SPACING["sm"], SPACING["xs"]),
        sticky="w",
    )

    # 章节数 + 每章字数（同一行小面板）
    row_for_chapter_and_word = 1
    chapter_word_frame = ctk.CTkFrame(chapter_card)
    chapter_word_frame.grid(
        row=row_for_chapter_and_word,
        column=1,
        padx=SPACING["sm"],
        pady=SPACING["xs"],
        sticky="ew",
    )
    chapter_word_frame.columnconfigure((0, 1, 2, 3), weight=0)

    num_chapters_label = ctk.CTkLabel(
        chapter_word_frame, text=t("章节数:"), font=(FONT_FAMILY, FONT_SIZES["md"])
    )
    num_chapters_label.grid(
        row=0, column=0, padx=SPACING["sm"], pady=SPACING["xs"], sticky="e"
    )

    num_chapters_entry = ctk.CTkEntry(
        chapter_word_frame,
        textvariable=self.num_chapters_var,
        width=90,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    num_chapters_entry.grid(
        row=0, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="w"
    )

    word_number_label = ctk.CTkLabel(
        chapter_word_frame, text=t("每章字数:"), font=(FONT_FAMILY, FONT_SIZES["md"])
    )
    word_number_label.grid(
        row=0,
        column=2,
        padx=(SPACING["lg"], SPACING["sm"]),
        pady=SPACING["xs"],
        sticky="e",
    )

    word_number_entry = ctk.CTkEntry(
        chapter_word_frame,
        textvariable=self.word_number_var,
        width=90,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    word_number_entry.grid(
        row=0, column=3, padx=SPACING["sm"], pady=SPACING["xs"], sticky="w"
    )

    # 保存路径
    create_label_with_help_for_novel_params(
        self,
        parent=chapter_card,
        label_text=t("保存路径:"),
        tooltip_key="filepath",
        row=row_for_chapter_and_word + 1,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    self.filepath_frame = ctk.CTkFrame(chapter_card)
    self.filepath_frame.grid(
        row=row_for_chapter_and_word + 1,
        column=1,
        padx=SPACING["sm"],
        pady=SPACING["xs"],
        sticky="nsew",
    )
    self.filepath_frame.columnconfigure(0, weight=1)

    filepath_entry = ctk.CTkEntry(
        self.filepath_frame,
        textvariable=self.filepath_var,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    filepath_entry.grid(
        row=0, column=0, padx=SPACING["sm"], pady=SPACING["xs"], sticky="ew"
    )

    browse_btn = make_button(
        self.filepath_frame,
        text=t("浏览..."),
        command=self.browse_folder,
        kind="secondary",
        width=90,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    browse_btn.grid(row=0, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="e")

    # 章节号
    create_label_with_help_for_novel_params(
        self,
        parent=chapter_card,
        label_text=t("章节号:"),
        tooltip_key="chapter_num",
        row=row_for_chapter_and_word + 2,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    chapter_num_entry = ctk.CTkEntry(
        chapter_card,
        textvariable=self.chapter_num_var,
        width=100,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    chapter_num_entry.grid(
        row=row_for_chapter_and_word + 2,
        column=1,
        padx=SPACING["sm"],
        pady=SPACING["xs"],
        sticky="w",
    )

    # 草稿变体个数
    create_label_with_help_for_novel_params(
        self,
        parent=chapter_card,
        label_text=t("草稿变体个数:"),
        tooltip_key="draft_variants",
        row=row_for_chapter_and_word + 3,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    draft_variants_entry = ctk.CTkEntry(
        chapter_card,
        textvariable=self.draft_variants_var,
        width=100,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    draft_variants_entry.grid(
        row=row_for_chapter_and_word + 3,
        column=1,
        padx=SPACING["sm"],
        pady=SPACING["xs"],
        sticky="w",
    )

    # 3) 本章指导卡片
    guide_card = ctk.CTkFrame(self.params_frame)
    apply_card_style(guide_card)
    guide_card.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, SPACING["sm"]))
    guide_card.columnconfigure(0, weight=0)
    guide_card.columnconfigure(1, weight=1)

    guide_header = ctk.CTkLabel(
        guide_card, text=t("本章指导"), font=(FONT_FAMILY, FONT_SIZES["xl"], "bold")
    )
    guide_header.grid(
        row=0,
        column=0,
        columnspan=2,
        padx=SPACING["sm"],
        pady=(SPACING["sm"], SPACING["xs"]),
        sticky="w",
    )

    create_label_with_help_for_novel_params(
        self,
        parent=guide_card,
        label_text=t("本章指导:"),
        tooltip_key="user_guidance",
        row=1,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        sticky="ne",
    )

    self.user_guide_text = ctk.CTkTextbox(
        guide_card, height=120, wrap="word", font=(FONT_FAMILY, FONT_SIZES["md"])
    )
    install_text_shortcuts(self.user_guide_text)
    TextWidgetContextMenu(self.user_guide_text)
    self.user_guide_text.grid(
        row=1, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="nsew"
    )
    if hasattr(self, "user_guidance_default") and self.user_guidance_default:
        self.user_guide_text.insert("0.0", self.user_guidance_default)

    # 4) 本章要素卡片
    meta_card = ctk.CTkFrame(self.params_frame)
    apply_card_style(meta_card)
    meta_card.grid(row=3, column=0, sticky="nsew", padx=0, pady=(0, SPACING["sm"]))
    meta_card.columnconfigure(0, weight=0)
    meta_card.columnconfigure(1, weight=1)

    meta_header = ctk.CTkLabel(
        meta_card, text=t("本章要素"), font=(FONT_FAMILY, FONT_SIZES["xl"], "bold")
    )
    meta_header.grid(
        row=0,
        column=0,
        columnspan=2,
        padx=SPACING["sm"],
        pady=(SPACING["sm"], SPACING["xs"]),
        sticky="w",
    )

    # 涉及角色
    create_label_with_help_for_novel_params(
        self,
        parent=meta_card,
        label_text=t("涉及角色:"),
        tooltip_key="characters_involved",
        row=1,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        sticky="ne",
    )

    char_inv_frame = ctk.CTkFrame(meta_card)
    char_inv_frame.grid(
        row=1, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="nsew"
    )
    char_inv_frame.columnconfigure(0, weight=1)
    char_inv_frame.columnconfigure(1, weight=0)
    char_inv_frame.columnconfigure(2, weight=0)

    self.char_inv_text = ctk.CTkTextbox(
        char_inv_frame, height=70, wrap="word", font=(FONT_FAMILY, FONT_SIZES["md"])
    )
    install_text_shortcuts(self.char_inv_text)
    self.char_inv_text.grid(
        row=0, column=0, padx=(0, SPACING["sm"]), pady=SPACING["xs"], sticky="nsew"
    )
    if hasattr(self, "characters_involved_var"):
        self.char_inv_text.insert("0.0", self.characters_involved_var.get())

    import_btn = make_button(
        char_inv_frame,
        text=t("导入"),
        command=self.show_character_import_window,
        kind="secondary",
        width=90,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    import_btn.grid(
        row=0, column=1, padx=(0, SPACING["sm"]), pady=SPACING["xs"], sticky="e"
    )

    select_btn = make_button(
        char_inv_frame,
        text=t("从角色库选择"),
        command=self.open_character_select_dialog,
        kind="secondary",
        width=120,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    select_btn.grid(
        row=0, column=2, padx=(SPACING["xs"], 0), pady=SPACING["xs"], sticky="e"
    )

    # 关键道具/要点
    create_label_with_help_for_novel_params(
        self,
        parent=meta_card,
        label_text=t("关键道具/要点:"),
        tooltip_key="key_items",
        row=2,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    key_items_entry = ctk.CTkEntry(
        meta_card,
        textvariable=self.key_items_var,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    key_items_entry.grid(
        row=2, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="ew"
    )

    # 场景地点
    create_label_with_help_for_novel_params(
        self,
        parent=meta_card,
        label_text=t("场景地点:"),
        tooltip_key="scene_location",
        row=3,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    scene_loc_entry = ctk.CTkEntry(
        meta_card,
        textvariable=self.scene_location_var,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    scene_loc_entry.grid(
        row=3, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="ew"
    )

    # 时间限制
    create_label_with_help_for_novel_params(
        self,
        parent=meta_card,
        label_text=t("时间限制:"),
        tooltip_key="time_constraint",
        row=4,
        column=0,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    time_const_entry = ctk.CTkEntry(
        meta_card,
        textvariable=self.time_constraint_var,
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    )
    time_const_entry.grid(
        row=4, column=1, padx=SPACING["sm"], pady=SPACING["xs"], sticky="ew"
    )


def build_optional_buttons_area(self, start_row=2):
    parent = getattr(self, "params_frame", None)
    if parent is not None:
        try:
            self.right_frame.grid_rowconfigure(start_row, weight=0)
        except Exception:
            pass
        target_row = len(parent.grid_slaves(column=0))
        self.optional_btn_frame = ctk.CTkFrame(parent)
        self.optional_btn_frame.grid(
            row=target_row,
            column=0,
            sticky="ew",
            padx=0,
            pady=(0, SPACING["sm"]),
        )
    else:
        # 兜底：若参数滚动区尚未创建，则保持原有右侧底部布局
        try:
            self.right_frame.grid_rowconfigure(start_row, weight=1)
        except Exception:
            pass

        self.optional_btn_frame = ctk.CTkFrame(self.right_frame)
        self.optional_btn_frame.grid(
            row=start_row + 1,
            column=0,
            sticky="sew",
            padx=SPACING["sm"],
            pady=SPACING["sm"],
        )
    self.optional_btn_frame.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

    def wrap_progress(label_text, fn):
        def _run():
            top = None
            try:
                top, _ = show_progress(self.optional_btn_frame, label_text)
            except Exception:
                top = None
            try:
                fn()
            finally:
                try:
                    if top is not None:
                        hide_progress(top)
                except Exception:
                    pass

        return _run

    make_button(
        self.optional_btn_frame,
        text=t("一致性检查"),
        command=wrap_progress(t("一致性检查中…"), self.do_consistency_check),
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=0, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("导入知识库"),
        command=wrap_progress(t("导入知识库中…"), self.import_knowledge_handler),
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=1, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("清空向量库"),
        command=wrap_progress(t("清空向量库中…"), self.clear_vectorstore_handler),
        kind="danger",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=2, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("查看剧情要点"),
        command=self.show_plot_arcs_ui,
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=3, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("角色库"),
        command=self.show_role_library,
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=4, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("保存配置"),
        command=self.save_all_config,
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=5, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("打开向量工作台"),
        command=wrap_progress(t("打开工作台…"), self.open_embed_dashboard_ui),
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=6, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")
    make_button(
        self.optional_btn_frame,
        text=t("角色审阅"),
        command=self.open_character_review_dialog,
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
        height=CONTROL_HEIGHT,
    ).grid(row=0, column=7, padx=SPACING["sm"], pady=SPACING["sm"], sticky="ew")


def create_label_with_help_for_novel_params(
    self,
    parent,
    label_text,
    tooltip_key,
    row,
    column,
    font=None,
    sticky="e",
    padx=5,
    pady=5,
):
    frame = ctk.CTkFrame(parent)
    frame.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
    frame.columnconfigure(0, weight=0)

    label = ctk.CTkLabel(frame, text=t(label_text), font=font)
    label.pack(side="left")

    btn = ctk.CTkButton(
        frame,
        text=t("?"),
        width=22,
        height=22,
        font=(FONT_FAMILY, FONT_SIZES["sm"]),
        command=lambda: messagebox.showinfo(
            t("参数说明"), tooltips.get(tooltip_key, t("暂无说明"))
        ),
    )
    btn.pack(side="left", padx=SPACING["xs"])

    return frame
