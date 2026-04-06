# ui/character_select_dialog.py
# -*- coding: utf-8 -*-
import logging
import customtkinter as ctk
from tkinter import messagebox
from novel_generator.character_store import (
    ensure_structure,
    load_index,
    build_effective,
)
from ui.i18n import t

DEFAULT_FONT = ("Microsoft YaHei", 12)


def open_character_select_dialog(self):
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
    try:
        ensure_structure(save_path)
    except Exception:
        pass
    try:
        self.safe_log("[角色库] 打开选择弹窗")
    except Exception:
        pass
    logging.info("[角色库] 选择弹窗: open")

    top = ctk.CTkToplevel(self.master)
    top.title(t("从角色库选择"))
    top.geometry("560x520")
    top.grab_set()

    # 搜索框
    bar = ctk.CTkFrame(top)
    bar.pack(fill="x", padx=8, pady=8)
    ctk.CTkLabel(bar, text=t("搜索"), font=DEFAULT_FONT).pack(side="left")
    query_var = ctk.StringVar(value="")
    query_entry = ctk.CTkEntry(bar, textvariable=query_var, width=280)
    query_entry.pack(side="left", padx=6)

    # 列表
    list_frame = ctk.CTkScrollableFrame(top)
    list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    checks = {}

    def refresh_list():
        for w in list_frame.winfo_children():
            w.destroy()
        q = (query_var.get() or "").strip().lower()
        idx = load_index(save_path)
        items = list(idx.get("characters", [])) if isinstance(idx, dict) else []
        # 排序：最近更新在前
        items.sort(
            key=lambda it: (it.get("updated_at", ""), it.get("name", "")), reverse=True
        )
        for it in items:
            name = it.get("name") or it.get("id")
            if q and (q not in name.lower()):
                continue
            row = ctk.CTkFrame(list_frame)
            row.pack(fill="x", padx=4, pady=2)
            var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(row, text=name, variable=var, font=DEFAULT_FONT).pack(
                side="left", padx=4
            )

            # 预览按钮
            def _mk_preview(nm=name, cid=it.get("id") or name):
                def _show():
                    try:
                        eff = build_effective(save_path, cid)
                        txt = []
                        txt.append(f"ID: {eff.get('id')}")
                        txt.append(f"{t('姓名')}: {eff.get('name')}")
                        if eff.get("summary"):
                            txt.append(t("摘要: ") + str(eff.get("summary")))
                        if eff.get("attributes"):
                            txt.append(
                                t("属性: ") + ", ".join(eff.get("attributes").keys())
                            )
                        messagebox.showinfo(t("预览"), "\n".join(txt), parent=top)
                    except Exception:
                        messagebox.showinfo(t("预览"), f"{nm}", parent=top)

                return _show

            ctk.CTkButton(row, text=t("预览"), width=60, command=_mk_preview()).pack(
                side="right", padx=4
            )
            checks[it.get("id") or name] = (var, name)

    refresh_list()

    def do_confirm():
        sel = [nm for cid, (v, nm) in checks.items() if v.get()]
        try:
            if not sel:
                messagebox.showinfo(t("提示"), t("未选择任何角色"), parent=top)
                return
            # 回填至“参与角色”文本/变量
            joined = ",".join(sel)
            if (
                hasattr(self, "characters_involved_var")
                and self.characters_involved_var
            ):
                try:
                    self.characters_involved_var.set(joined)
                except Exception:
                    pass
            if hasattr(self, "char_inv_text") and self.char_inv_text:
                try:
                    self.char_inv_text.delete("0.0", "end")
                    self.char_inv_text.insert("0.0", joined)
                except Exception:
                    pass
            self.safe_log(f"[角色库] 已回填参与角色: {joined}")
            logging.info(f"[角色库] 选择回填: {joined}")
        finally:
            try:
                top.destroy()
            except Exception:
                pass

    btns = ctk.CTkFrame(top)
    btns.pack(fill="x", padx=8, pady=(0, 8))
    ctk.CTkButton(btns, text=t("刷新"), width=80, command=refresh_list).pack(
        side="left", padx=4
    )
    ctk.CTkButton(btns, text=t("确定"), width=80, command=do_confirm).pack(
        side="right", padx=4
    )
    ctk.CTkButton(btns, text=t("取消"), width=80, command=top.destroy).pack(
        side="right", padx=4
    )
