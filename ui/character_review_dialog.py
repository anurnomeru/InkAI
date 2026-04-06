# ui/character_review_dialog.py
# -*- coding: utf-8 -*-
import logging
import customtkinter as ctk
from tkinter import messagebox
from novel_generator.character_store import ensure_structure, list_auto, load_manual
from novel_generator.character_adopt import adopt_auto_entry
from ui.i18n import t

DEFAULT_FONT = ("Microsoft YaHei", 12)

FIELDS = [
    "name",
    "aliases",
    "tags",
    "summary",
    "attributes",
    "relationships",
    "timeline",
]


def open_character_review_dialog(self):
    try:
        save_path = (self.filepath_var.get() or "").strip()
    except Exception:
        save_path = ""
    if not save_path:
        try:
            messagebox.showwarning(t("警告"), t("请先配置保存文件路径"))
        except Exception:
            pass
        return
    ensure_structure(save_path)
    try:
        self.safe_log("[角色库] 打开审阅面板")
    except Exception:
        pass
    logging.info("[角色库] 审阅面板: open")

    top = ctk.CTkToplevel(self.master)
    top.title(t("角色审阅（从自动抽取采纳到手动层）"))
    top.geometry("720x560")
    top.grab_set()

    # 顶部：选择章节
    bar = ctk.CTkFrame(top)
    bar.pack(fill="x", padx=8, pady=8)
    ctk.CTkLabel(bar, text=t("选择章节"), font=DEFAULT_FONT).pack(side="left")

    chapters_map = list_auto(save_path)
    chap_values = [str(c) for c in sorted(chapters_map.keys())]
    chap_var = ctk.StringVar(value=(chap_values[-1] if chap_values else ""))
    chap_menu = ctk.CTkOptionMenu(
        bar, values=chap_values or [""], variable=chap_var, width=120
    )
    chap_menu.pack(side="left", padx=6)

    # 主区：条目 + 字段勾选
    list_frame = ctk.CTkScrollableFrame(top)
    list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    entries_vars = {}  # char_id -> {field: BooleanVar}

    def render():
        for w in list_frame.winfo_children():
            w.destroy()
        sel = chap_var.get().strip()
        if not sel or not sel.isdigit():
            ctk.CTkLabel(list_frame, text=t("无可审阅条目"), font=DEFAULT_FONT).pack(
                pady=12
            )
            return
        chap = int(sel)
        ids = chapters_map.get(chap, [])
        if not ids:
            ctk.CTkLabel(
                list_frame,
                text=t("第{n}章：无自动抽取条目").format(n=chap),
                font=DEFAULT_FONT,
            ).pack(pady=12)
            return
        for cid in ids:
            card = ctk.CTkFrame(list_frame)
            card.pack(fill="x", padx=4, pady=4)
            title = ctk.CTkLabel(
                card, text=t("角色：{id}").format(id=cid), font=("Microsoft YaHei", 13)
            )
            title.pack(anchor="w", padx=6, pady=4)
            manual = load_manual(save_path, cid) or {}
            # 字段勾选行
            row = ctk.CTkFrame(card)
            row.pack(fill="x", padx=6, pady=4)
            per = {}
            for f in FIELDS:
                var = ctk.BooleanVar(
                    value=(f in ("relationships", "timeline"))
                )  # 默认推荐采纳关系/时间线
                ctk.CTkCheckBox(row, text=f, variable=var).pack(side="left", padx=6)
                per[f] = var
            entries_vars[cid] = per
            # 说明
            tip = ctk.CTkLabel(
                card,
                text=t("手动已有摘要：{has_summary}；手动属性数：{count}").format(
                    has_summary=(t("是") if manual.get("summary") else t("否")),
                    count=len((manual.get("attributes") or {}).keys()),
                ),
                font=("Microsoft YaHei", 11),
            )
            tip.pack(anchor="w", padx=6, pady=(0, 6))

    render()

    def do_reload():
        nonlocal chapters_map
        chapters_map = list_auto(save_path)
        try:
            self.safe_log("[角色库] 审阅面板：已刷新章节列表")
        except Exception:
            pass
        render()

    def do_adopt():
        sel = chap_var.get().strip()
        if not sel or not sel.isdigit():
            messagebox.showwarning(t("提示"), t("请选择章节"), parent=top)
            return
        chap = int(sel)
        adopted = 0
        for cid, per in entries_vars.items():
            fields = [k for k, v in per.items() if v.get()]
            if not fields:
                continue
            ok = adopt_auto_entry(save_path, cid, chapter_num=chap, fields=fields)
            if ok:
                adopted += 1
        try:
            self.safe_log(f"[角色库] 采纳完成：章节={chap} 角色数={adopted}")
        except Exception:
            pass
        logging.info(f"[角色库] 审阅采纳完成: chapter={chap} adopted={adopted}")
        messagebox.showinfo(
            t("完成"), t("已采纳 {n} 个角色的所选字段").format(n=adopted), parent=top
        )

    # 底部按钮
    btns = ctk.CTkFrame(top)
    btns.pack(fill="x", padx=8, pady=(0, 8))
    ctk.CTkButton(btns, text=t("刷新"), width=80, command=do_reload).pack(
        side="left", padx=4
    )
    ctk.CTkButton(btns, text=t("采纳所选"), width=100, command=do_adopt).pack(
        side="right", padx=4
    )
    ctk.CTkButton(btns, text=t("关闭"), width=80, command=top.destroy).pack(
        side="right", padx=4
    )
