# -*- coding: utf-8 -*-
import os
import customtkinter as ctk
from tkinter import messagebox

def open_role_library_hub(self):
    try:
        save_path = (self.filepath_var.get() or '').strip()
    except Exception:
        save_path = ''
    if not save_path:
        try:
            messagebox.showwarning('警告','请先配置保存文件路径')
        except Exception:
            pass
        return
    try:
        self.safe_log('[角色库] 打开角色库工作台')
    except Exception:
        pass

    top = ctk.CTkToplevel(self.master)
    top.title('角色库工作台')
    top.geometry('420x260')
    top.grab_set()

    frm = ctk.CTkFrame(top)
    frm.pack(fill='both', expand=True, padx=12, pady=12)

    # 说明
    ctk.CTkLabel(frm, text='选择要执行的角色库操作：', font=("Microsoft YaHei", 12)).pack(anchor='w', pady=(4,10))

    def _open_review():
        try:
            self.open_character_review_dialog()
        finally:
            try:
                top.destroy()
            except Exception:
                pass
    def _open_select():
        try:
            self.open_character_select_dialog()
        finally:
            try:
                top.destroy()
            except Exception:
                pass
    def _open_folder():
        try:
            path = os.path.join(save_path, '角色库')
            os.makedirs(path, exist_ok=True)
            if os.name == 'nt':
                os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(['open', path])
            try:
                self.safe_log(f'[角色库] 已打开目录: {path}')
            except Exception:
                pass
        except Exception:
            try:
                self.handle_exception('[角色库] 打开目录出错')
            except Exception:
                pass

    # 按钮区
    btn1 = ctk.CTkButton(frm, text='角色审阅（采纳自动抽取）', width=240, command=_open_review)
    btn1.pack(pady=6)
    btn2 = ctk.CTkButton(frm, text='从角色库选择（回填参与角色）', width=240, command=_open_select)
    btn2.pack(pady=6)
    btn3 = ctk.CTkButton(frm, text='打开角色库文件夹', width=240, command=_open_folder)
    btn3.pack(pady=6)

    # 关闭
    ctk.CTkButton(frm, text='关闭', width=120, command=top.destroy).pack(pady=(12,0))
