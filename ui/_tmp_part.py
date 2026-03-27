embedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_formatembedding_interface_format=emb_format,
                        embedding_model_name=emb_model,
                        file_path=temp_path,
                        filepath=self.filepath_var.get().strip()
                    )
                    self.safe_log("? 知识库文件导入完成。")
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

            except Exception:
                self.handle_exception("导入知识库时出错")
            finally:
                self.enable_button_safe(self.btn_import_knowledge)

        try:
            thread = threading.Thread(target=task, daemon=True)
            thread.start()
        except Exception as e:
            self.enable_button_safe(self.btn_import_knowledge)
            messagebox.showerror("错误", f"线程启动失败: {str(e)}")

def clear_vectorstore_handler(self):
    filepath = self.filepath_var.get().strip()
    if not filepath:
        messagebox.showwarning("警告", "请先配置保存文件路径。")
        return

    first_confirm = messagebox.askyesno("警告", "确定要清空本地向量库吗？此操作不可恢复！")
    if first_confirm:
        second_confirm = messagebox.askyesno("二次确认", "你确定真的要删除所有向量数据吗？此操作不可恢复！")
        if second_confirm:
            if clear_vector_store(filepath):
                self.log("已清空向量库。")
            else:
                self.log(f"未能清空向量库，请关闭程序后手动删除 {filepath} 下的 vectorstore 文件夹。")

def show_plot_arcs_ui(self):
    filepath = self.filepath_var.get().strip()
    if not filepath:
        messagebox.showwarning("警告", "请先在主Tab中设置保存文件路径")
        return

    plot_arcs_file = os.path.join(filepath, "plot_arcs.txt")
    if not os.path.exists(plot_arcs_file):
        messagebox.showinfo("剧情要点", "当前还未生成任何剧情要点或冲突记录。")
        return

    arcs_text = read_file(plot_arcs_file).strip()
    if not arcs_text:
        arcs_text = "当前没有记录的剧情要点或冲突。"

    top = ctk.CTkToplevel(self.master)
    top.title("剧情要点/未解决冲突")
    top.geometry("600x400")
    text_area = ctk.CTkTextbox(top, wrap="word", font=("Microsoft YaHei", 12))
    text_area.pack(fill="both", expand=True, padx=10, pady=10)
    text_area.insert("0.0", arcs_text)
    text_area.configure(state="disabled")






