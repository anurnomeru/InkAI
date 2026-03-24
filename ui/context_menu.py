# ui/context_menu.py
# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk
from ui.i18n import t
class TextWidgetContextMenu:
    """
    娑?customtkinter.TextBox 閹?tkinter.Text 閹绘劒绶垫娊鏁鍒?鍓垏/绮樿创/閸忋劑鈧娈戦崝鐔诲厴?
    """
    def __init__(self, widget):
        self.widget = widget
        self.menu = tk.Menu(widget, tearoff=0)
        self.menu.add_command(label="复制", command=self.copy)
        self.menu.add_command(label="粘贴", command=self.paste)
        self.menu.add_command(label="剪切", command=self.cut)
        self.menu.add_separator()
        self.menu.add_command(label="全选", command=self.select_all)
        
        # 缂佹垵鐣炬娊鏁禍瀣╂
        self.widget.bind("<Button-3>", self.show_menu)
        
    def show_menu(self, event):
        if isinstance(self.widget, ctk.CTkTextbox):
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()
            
    def copy(self):
        try:
            text = self.widget.get("sel.first", "sel.last")
            self.widget.clipboard_clear()
            self.widget.clipboard_append(text)
        except tk.TclError:
            pass  # 濞屸剝婀侀柅澶夎厬鏂囨湰閺冭泛鎷烽悾銉╂晩鐠?

    def paste(self):
        try:
            text = self.widget.clipboard_get()
            self.widget.insert("insert", text)
        except tk.TclError:
            pass  # 閸擃亣鍒涢弶澶歌礋缁岀儤妞傝箛鐣屾殣閿欒

    def cut(self):
        try:
            text = self.widget.get("sel.first", "sel.last")
            self.widget.delete("sel.first", "sel.last")
            self.widget.clipboard_clear()
            self.widget.clipboard_append(text)
        except tk.TclError:
            pass  # 濞屸剝婀侀柅澶夎厬鏂囨湰閺冭泛鎷烽悾銉╂晩鐠?

    def select_all(self):
        self.widget.tag_add("sel", "1.0", "end")










