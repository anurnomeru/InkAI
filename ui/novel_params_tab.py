# ui/novel_params_tab.py

# -*- coding: utf-8 -*-

import customtkinter as ctk

from tkinter import filedialog, messagebox

from ui.context_menu import TextWidgetContextMenu
from ui.i18n import t

from ui.text_shortcuts import install_text_shortcuts

from tooltips import tooltips



def build_novel_params_area(self, start_row=1):

    self.params_frame = ctk.CTkScrollableFrame(self.right_frame, orientation="vertical")

    self.params_frame.grid(row=start_row, column=0, sticky="nsew", padx=5, pady=5)

    self.params_frame.columnconfigure(1, weight=1)



    # 1) 主题(Topic)

    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text=t("主题(Topic):"), tooltip_key="topic", row=0, column=0, font=("Microsoft YaHei", 12), sticky="ne")

    self.topic_text = ctk.CTkTextbox(self.params_frame, height=80, wrap="word", font=("Microsoft YaHei", 12))

    install_text_shortcuts(self.topic_text)

    TextWidgetContextMenu(self.topic_text)

    self.topic_text.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    if hasattr(self, 'topic_default') and self.topic_default:

        self.topic_text.insert("0.0", self.topic_default)
    if hasattr(self, 'topic_default') and self.topic_default:

        self.topic_text.insert("0.0", self.topic_default)



    # 2) 缁鐎?Genre)


    genre_entry = ctk.CTkEntry(self.params_frame, textvariable=self.genre_var, font=("Microsoft YaHei", 12))

    genre_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")



    # 3) 绔犺妭鏁? 濮ｅ繒鐝峰瓧鏁?

    row_for_chapter_and_word = 2


    chapter_word_frame = ctk.CTkFrame(self.params_frame)

    chapter_word_frame.grid(row=row_for_chapter_and_word, column=1, padx=5, pady=5, sticky="ew")

    chapter_word_frame.columnconfigure((0, 1, 2, 3), weight=0)

    num_chapters_label = ctk.CTkLabel(chapter_word_frame, text=t("章节数:"), font=("Microsoft YaHei", 12))

    num_chapters_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

    num_chapters_entry = ctk.CTkEntry(chapter_word_frame, textvariable=self.num_chapters_var, width=60, font=("Microsoft YaHei", 12))

    num_chapters_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    word_number_label = ctk.CTkLabel(chapter_word_frame, text=t("每章字数:"), font=("Microsoft YaHei", 12))

    word_number_label.grid(row=0, column=2, padx=(15, 5), pady=5, sticky="e")

    word_number_entry = ctk.CTkEntry(chapter_word_frame, textvariable=self.word_number_var, width=60, font=("Microsoft YaHei", 12))

    word_number_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")



    # 4) 淇濆瓨璺緞

    row_fp = 3


    self.filepath_frame = ctk.CTkFrame(self.params_frame)

    self.filepath_frame.grid(row=row_fp, column=1, padx=5, pady=5, sticky="nsew")

    self.filepath_frame.columnconfigure(0, weight=1)

    filepath_entry = ctk.CTkEntry(self.filepath_frame, textvariable=self.filepath_var, font=("Microsoft YaHei", 12))

    filepath_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    browse_btn = ctk.CTkButton(self.filepath_frame, text=t("娴忚..."), command=self.browse_folder, width=60, font=("Microsoft YaHei", 12))

    browse_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")



    # 5) 绔犺妭鍙?

    row_chap_num = 4

    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text=t("章节号:"), tooltip_key="chapter_num", row=row_chap_num, column=0, font=("Microsoft YaHei", 12))

    chapter_num_entry = ctk.CTkEntry(self.params_frame, textvariable=self.chapter_num_var, width=80, font=("Microsoft YaHei", 12))

    chapter_num_entry.grid(row=row_chap_num, column=1, padx=5, pady=5, sticky="w")



    # 5.1) ?????
    row_draft_variants = row_chap_num + 1
    # Draft Variant Count label + input (raw English, no i18n/font)
    label_draft_variants = ctk.CTkLabel(self.params_frame, text="Draft Variant Count")
    label_draft_variants.grid(row=row_draft_variants, column=0, padx=5, pady=5, sticky="e")
    draft_variants_entry = ctk.CTkEntry(self.params_frame, textvariable=self.draft_variants_var, width=80)
    draft_variants_entry.grid(row=row_draft_variants, column=1, padx=5, pady=5, sticky="w")

    # 6) 閸愬懎顔愰幐鍥ь嚤

    row_user_guide = 6


    

    self.user_guide_text = ctk.CTkTextbox(self.params_frame, height=80, wrap="word", font=("Microsoft YaHei", 12))

    install_text_shortcuts(self.user_guide_text)

    TextWidgetContextMenu(self.user_guide_text)

    self.user_guide_text.grid(row=row_user_guide, column=1, padx=5, pady=5, sticky="nsew")

    if hasattr(self, 'user_guidance_default') and self.user_guidance_default:

        self.user_guide_text.insert("0.0", self.user_guidance_default)



    # 7) 顖炩偓澶婂帗缁辩媴绱伴弽绋跨妇娴滆櫣澧?鍏抽敭閬撳叿/缁屾椽妫块崸鎰垼/閺冨爼妫块崢瀣

    row_idx = 7


    

    # 閺嶇绺炬禍铏瑰⒖鏉堟挸鍙嗗?鎸夐挳鐎圭懓娅?

    char_inv_frame = ctk.CTkFrame(self.params_frame)

    char_inv_frame.grid(row=row_idx, column=1, padx=5, pady=5, sticky="nsew")

    char_inv_frame.columnconfigure(0, weight=1)

    char_inv_frame.rowconfigure(0, weight=1)

    

    # 娑撳顢戞枃鏈潏鎾冲弳濡?

    

    self.char_inv_text = ctk.CTkTextbox(char_inv_frame, height=60, wrap="word", font=("Microsoft YaHei", 12))

    install_text_shortcuts(self.char_inv_text)

    self.char_inv_text.grid(row=0, column=0, padx=(0,5), pady=5, sticky="nsew")

    if hasattr(self, 'characters_involved_var'):

        self.char_inv_text.insert("0.0", self.characters_involved_var.get())

    

    # 瀵煎叆鎸夐挳

    import_btn = ctk.CTkButton(char_inv_frame, text=t("瀵煎叆"), width=60, 

                             command=self.show_character_import_window,

                             font=("Microsoft YaHei", 12))

    import_btn.grid(row=0, column=1, padx=(0,5), pady=5, sticky="e")

    row_idx += 1


    key_items_entry = ctk.CTkEntry(self.params_frame, textvariable=self.key_items_var, font=("Microsoft YaHei", 12))

    key_items_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")

    row_idx += 1


    scene_loc_entry = ctk.CTkEntry(self.params_frame, textvariable=self.scene_location_var, font=("Microsoft YaHei", 12))

    scene_loc_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")

    row_idx += 1


    time_const_entry = ctk.CTkEntry(self.params_frame, textvariable=self.time_constraint_var, font=("Microsoft YaHei", 12))

    time_const_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")



def build_optional_buttons_area(self, start_row=2):

    self.optional_btn_frame = ctk.CTkFrame(self.right_frame)

    self.optional_btn_frame.grid(row=start_row, column=0, sticky="ew", padx=5, pady=5)

    self.optional_btn_frame.columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)



    self.btn_check_consistency = ctk.CTkButton(

        self.optional_btn_frame, text=t("一致性检查"), command=self.do_consistency_check, 

        font=("Microsoft YaHei", 12), width=100  # 閸ュ搫鐣剧€硅棄瀹?

    )

    self.btn_check_consistency.grid(row=0, column=0, padx=5, pady=5, sticky="ew")



    self.btn_import_knowledge = ctk.CTkButton(

        self.optional_btn_frame, text=t("导入知识库"), command=self.import_knowledge_handler,

        font=("Microsoft YaHei", 12), width=100

    )

    self.btn_import_knowledge.grid(row=0, column=1, padx=5, pady=5, sticky="ew")



    self.btn_clear_vectorstore = ctk.CTkButton(

        self.optional_btn_frame, text=t("清空向量库"), fg_color="red", 

        command=self.clear_vectorstore_handler, font=("Microsoft YaHei", 12), width=100

    )

    self.btn_clear_vectorstore.grid(row=0, column=2, padx=5, pady=5, sticky="ew")



    self.plot_arcs_btn = ctk.CTkButton(

        self.optional_btn_frame, text=t("鏌ョ湅鍓ф儏瑕佺偣"), command=self.show_plot_arcs_ui,

        font=("Microsoft YaHei", 12), width=100

    )

    self.plot_arcs_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")



    # 閺傛澘顤冭鑹插簱鎾村瘻闁?

    self.role_library_btn = ctk.CTkButton(

        self.optional_btn_frame, text=t("角色库"), command=self.show_role_library,

        font=("Microsoft YaHei", 12), width=100

    )

    self.role_library_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
    # 鍏ㄥ眬淇濆瓨閰嶇疆鎸夐挳锛堝叕鍏卞叆鍙ｏ級
    self.btn_save_all_config = ctk.CTkButton(
        self.optional_btn_frame, text=t("保存配置"), command=self.save_all_config,
        font=("Microsoft YaHei", 12), width=100
    )
    self.btn_save_all_config.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

    # 打开向量工作台（Streamlit）
    self.btn_open_embed_dashboard = ctk.CTkButton(
        self.optional_btn_frame, text=t("打开向量工作台"), command=self.open_embed_dashboard_ui,
        font=("Microsoft YaHei", 12), width=120
    )
    self.btn_open_embed_dashboard.grid(row=0, column=6, padx=5, pady=5, sticky="ew")



def create_label_with_help_for_novel_params(self, parent, label_text, tooltip_key, row, column, font=None, sticky="e", padx=5, pady=5):

    frame = ctk.CTkFrame(parent)

    frame.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)

    frame.columnconfigure(0, weight=0)

    label = ctk.CTkLabel(frame, text=t(label_text), font=font)

    label.pack(side="left")

    btn = ctk.CTkButton(frame, text=t("?"), width=22, height=22, font=("Microsoft YaHei", 10),

                        command=lambda: messagebox.showinfo("鍙傛暟璇存槑", tooltips.get(tooltip_key, "鏆傛棤璇存槑")))

    btn.pack(side="left", padx=3)

    return frame





























