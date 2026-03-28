# ui/main_window.py  
  
# -*- coding: utf-8 -*-  
  
import os  
  
import threading  
  
import logging  
  
import customtkinter as ctk  
import traceback  
import tkinter as tk  
  
from tkinter import filedialog, messagebox  
  
try:  
    from .role_library import RoleLibrary  
except Exception:  
    RoleLibrary = None  
  
from llm_adapters import create_llm_adapter  
  
  
  
from config_manager import load_config, save_config, test_llm_config, test_embedding_config  
  
from utils import read_file, save_string_to_txt, clear_file_content  
  
from tooltips import tooltips  
  
  
  
from ui.context_menu import TextWidgetContextMenu  
from ui.i18n import t  
  
from ui.main_tab import build_main_tab, build_left_layout, build_right_layout, save_main_editor_content  
  
from ui.config_tab import build_config_tabview, load_config_btn, save_config_btn  
  
from ui.novel_params_tab import build_novel_params_area, build_optional_buttons_area  
  
from ui.generation_handlers import (  

    generate_novel_architecture_ui,  

    generate_chapter_blueprint_ui,  

    generate_chapter_draft_ui,  

    finalize_chapter_ui,  

    do_consistency_check,  

    import_knowledge_handler,  

    clear_vectorstore_handler,  

    show_plot_arcs_ui,  

    generate_batch_ui,

    rebuild_full_vectorstore_ui  

    open_embed_dashboard_ui  

)  
  
from ui.setting_tab import build_setting_tab, load_novel_architecture, save_novel_architecture  
  
from ui.directory_tab import build_directory_tab, load_chapter_blueprint, save_chapter_blueprint  
  
from ui.character_tab import build_character_tab, load_character_state, save_character_state  
  
from ui.summary_tab import build_summary_tab, load_global_summary, save_global_summary  
  
from ui.chapters_tab import build_chapters_tab, refresh_chapters_list, on_chapter_selected, load_chapter_content, save_current_chapter, prev_chapter, next_chapter  
  
from ui.other_settings import build_other_settings_tab  
  
  
  
  
  
class NovelGeneratorGUI:  
  
    """主界面类"""  
  
    def __init__(self, master):  
  
        self.master = master  
  
        self.master.title("Novel Generator GUI")  
  
        try:  
  
            if os.path.exists("icon.ico"):  
  
                self.master.iconbitmap("icon.ico")  
  
        except Exception:  
  
            pass  
  
        self.master.geometry("1350x840")  
  
  
  
        # --------------- 配置文件路径 ---------------  
  
        self.config_file = "config.json"  
  
        self.loaded_config = load_config(self.config_file)  
  
  
  
        if self.loaded_config:  
  
            last_llm = next(iter(self.loaded_config["llm_configs"].values())).get("interface_format", "OpenAI")  
  
  
  
            last_embedding = self.loaded_config.get("last_embedding_interface_format", "OpenAI")  
  
        else:  
  
            last_llm = "OpenAI"  
  
            last_embedding = "OpenAI"  
  
  
  
        # if self.loaded_config and "llm_configs" in self.loaded_config and last_llm in self.loaded_config["llm_configs"]:  
  
        #     llm_conf = next(iter(self.loaded_config["llm_configs"]))  
  
        # else:  
  
        #     llm_conf = {  
  
        #         "api_key": "",  
  
        #         "base_url": "https://api.openai.com/v1",  
  
        #         "model_name": "gpt-4o-mini",  
  
        #         "temperature": 0.7,  
  
        #         "max_tokens": 8192,  
  
        #         "timeout": 600  
  
        #     }  
  
        llm_conf = next(iter(self.loaded_config["llm_configs"].values()))  
  
        choose_configs = self.loaded_config.get("choose_configs", {})  
  
  
  
  
  
        if self.loaded_config and "embedding_configs" in self.loaded_config and last_embedding in self.loaded_config["embedding_configs"]:  
  
            emb_conf = self.loaded_config["embedding_configs"][last_embedding]  
  
        else:  
  
            emb_conf = {  
  
                "api_key": "",  
  
                "base_url": "https://api.openai.com/v1",  
  
                "model_name": "text-embedding-ada-002",  
  
                "retrieval_k": 4  
  
            }  
  
  
  
        # PenBo 澧炲姞浠ｇ悊鍔熻兘鏀寔  
  
        proxy_url = self.loaded_config["proxy_setting"]["proxy_url"]  
  
        proxy_port = self.loaded_config["proxy_setting"]["proxy_port"]  
  
        if self.loaded_config["proxy_setting"]["enabled"]:  
  
            os.environ['HTTP_PROXY'] = f"http://{proxy_url}:{proxy_port}"  
  
            os.environ['HTTPS_PROXY'] = f"http://{proxy_url}:{proxy_port}"  
  
        else:  
  
            os.environ.pop('HTTP_PROXY', None)    
  
            os.environ.pop('HTTPS_PROXY', None)  
  
  
  
  
  
  
  
        # -- LLM閫氱敤参数 --  
  
        # self.llm_conf_name = next(iter(self.loaded_config["llm_configs"]))  
  
        self.api_key_var = ctk.StringVar(value=llm_conf.get("api_key", ""))  
  
        self.base_url_var = ctk.StringVar(value=llm_conf.get("base_url", "https://api.openai.com/v1"))  
  
        self.interface_format_var = ctk.StringVar(value=llm_conf.get("interface_format", "OpenAI"))  
  
        self.model_name_var = ctk.StringVar(value=llm_conf.get("model_name", "gpt-4o-mini"))  
  
        self.temperature_var = ctk.DoubleVar(value=llm_conf.get("temperature", 0.7))  
  
        self.max_tokens_var = ctk.IntVar(value=llm_conf.get("max_tokens", 8192))  
  
        self.timeout_var = ctk.IntVar(value=llm_conf.get("timeout", 600))  
  
        self.interface_config_var = ctk.StringVar(value=next(iter(self.loaded_config["llm_configs"])))  
  
  
  
  
  
  
  
        # -- Embedding鐩稿叧 --  
  
        self.embedding_interface_format_var = ctk.StringVar(value=last_embedding)  
  
        self.embedding_api_key_var = ctk.StringVar(value=emb_conf.get("api_key", ""))  
  
        self.embedding_url_var = ctk.StringVar(value=emb_conf.get("base_url", "https://api.openai.com/v1"))  
  
        self.embedding_model_name_var = ctk.StringVar(value=emb_conf.get("model_name", "text-embedding-ada-002"))  
  
        self.embedding_retrieval_k_var = ctk.StringVar(value=str(emb_conf.get("retrieval_k", 4)))  
  
  
  
  
  
        # -- 生成配置鐩稿叧 --  
  
        self.architecture_llm_var = ctk.StringVar(value=choose_configs.get("architecture_llm", "DeepSeek"))  
  
        self.chapter_outline_llm_var = ctk.StringVar(value=choose_configs.get("chapter_outline_llm", "DeepSeek"))  
  
        self.final_chapter_llm_var = ctk.StringVar(value=choose_configs.get("final_chapter_llm", "DeepSeek"))  
  
        self.consistency_review_llm_var = ctk.StringVar(value=choose_configs.get("consistency_review_llm", "DeepSeek"))  
  
        self.prompt_draft_llm_var = ctk.StringVar(value=choose_configs.get("prompt_draft_llm", "DeepSeek"))  
  
  
  
  
  
  
  
  
  
  
  
        # -- 小说参数鐩稿叧 --  
  
        if self.loaded_config and "other_params" in self.loaded_config:  
  
            op = self.loaded_config["other_params"]  
  
            self.topic_default = op.get("topic", "")  
  
            self.genre_var = ctk.StringVar(value=op.get("genre", "鐜勫够"))  
  
            self.num_chapters_var = ctk.StringVar(value=str(op.get("num_chapters", 10)))  
  
            self.word_number_var = ctk.StringVar(value=str(op.get("word_number", 3000)))  
  
            self.filepath_var = ctk.StringVar(value=op.get("filepath", ""))  
  
            self.chapter_num_var = ctk.StringVar(value=str(op.get("chapter_num", "1")))  
  
  
            self.draft_variants_var = ctk.StringVar(value=str(op.get('draft_variants', 3)))  
  
            self.characters_involved_var = ctk.StringVar(value=op.get("characters_involved", ""))  
  
            self.key_items_var = ctk.StringVar(value=op.get("key_items", ""))  
  
            self.scene_location_var = ctk.StringVar(value=op.get("scene_location", ""))  
  
            self.time_constraint_var = ctk.StringVar(value=op.get("time_constraint", ""))  
  
            self.user_guidance_default = op.get("user_guidance", "")  
  
            self.webdav_url_var = ctk.StringVar(value=op.get("webdav_url", ""))  
  
            self.webdav_username_var = ctk.StringVar(value=op.get("webdav_username", ""))  
  
            self.webdav_password_var = ctk.StringVar(value=op.get("webdav_password", ""))  
  
  
  
        else:  
  
            self.topic_default = ""  
  
            self.genre_var = ctk.StringVar(value="鐜勫够")  
  
            self.num_chapters_var = ctk.StringVar(value="10")  
  
            self.word_number_var = ctk.StringVar(value="3000")  
  
            self.filepath_var = ctk.StringVar(value="")  
  
            self.chapter_num_var = ctk.StringVar(value="1")  
            self.draft_variants_var = ctk.StringVar(value='3')
  
            self.characters_involved_var = ctk.StringVar(value="")  
  
            self.key_items_var = ctk.StringVar(value="")  
  
            self.scene_location_var = ctk.StringVar(value="")  
  
            self.time_constraint_var = ctk.StringVar(value="")  
  
            self.user_guidance_default = ""  
  
  
  
        # --------------- 鏁翠綋Tab甯冨眬 ---------------  
  
                # --- Choose configs StringVars (create if missing) ---  
        try:  
            choose_configs = self.loaded_config.get("choose_configs", {})  
        except Exception:  
            choose_configs = {}  
        try:  
            last_embedding = self.loaded_config.get("last_embedding_interface_format", "OpenAI")  
        except Exception:  
            last_embedding = "OpenAI"  
        if not hasattr(self, 'embedding_choice_var'):  
            self.embedding_choice_var = ctk.StringVar(value=choose_configs.get('embedding_choice', last_embedding))  
        self.tabview = ctk.CTkTabview(self.master)  
  
        self.tabview.pack(fill="both", expand=True)  
  
  
  
        # 鍒涘缓鍚勪釜标签页?  
  
        build_main_tab(self)  
  
        build_config_tabview(self)  
  
        build_novel_params_area(self, start_row=1)  
  
        build_optional_buttons_area(self, start_row=2)
        # 初始化向量库按钮文案/功能（根据当前保存路径与是否存在向量库）
        try:
            self.update_vectorstore_button()
        except Exception:
            pass
        build_setting_tab(self)  
  
        build_directory_tab(self)  
  
        build_character_tab(self)  
  
        build_summary_tab(self)  
  
        build_chapters_tab(self)  
  
        build_other_settings_tab(self)  
  
        try:  
            # 章节号变更 -> 刷新变体并加载对应内容  
            self.chapter_num_var.trace_add("write", lambda *a: self._on_chapter_num_changed())  
        except Exception:  
            pass  
        try:
            self.chapter_num_var.trace_add("write", lambda *a: self.update_finalized_status_label())
        except Exception:
            pass
        try:  
            # 保存路径变更 -> 重新计算最新章节  
            self.filepath_var.trace_add("write", lambda *a: self._on_filepath_changed())  
        except Exception:  
            pass  
        try:
            self.filepath_var.trace_add("write", lambda *a: self.update_finalized_status_label())
        except Exception:
            pass  
        try:  
            # 首次进入根据保存路径下 chapters/ 自动选中最新章节  
            self.master.after(0, self._apply_latest_chapter_on_start)  
        except Exception:  
            pass  
  
  
  
  
  
    # ----------------- 閫氱敤杈呭姪鍑芥暟 -----------------  
  
    def show_tooltip(self, key: str):  
  
        info_text = tooltips.get(key, "暂无说明")  
  
        messagebox.showinfo("参数说明", info_text)  
  
  
  
    def safe_get_int(self, var, default=1):  
  
        try:  
  
            val_str = str(var.get()).strip()  
  
            return int(val_str)  
  
        except:  
  
            var.set(str(default))  
  
            return default  
  
  
  
    def log(self, message: str):  
  
        self.log_text.configure(state="normal")  
  
        self.log_text.insert("end", message + "\n")  
  
        self.log_text.see("end")  
  
        self.log_text.configure(state="disabled")  
  
  
  
    def safe_log(self, message: str):  
  
        self.master.after(0, lambda: self.log(message))  
  
  
  
    def disable_button_safe(self, btn):  
  
        self.master.after(0, lambda: btn.configure(state="disabled"))  
  
  
  
    def enable_button_safe(self, btn):  
  
        self.master.after(0, lambda: btn.configure(state="normal"))  
  
  
  
    def handle_exception(self, context: str):  
  
        full_message = f"{context}\n{traceback.format_exc()}"  
  
        logging.error(full_message)  
  
        self.safe_log(full_message)  
  
  
  
    def show_chapter_in_textbox(self, text: str):  
  
        self.chapter_result.delete("0.0", "end")  
  
        self.chapter_result.insert("0.0", text)  
  
        self.chapter_result.see("end")  
  
  
    def _load_text_and_show(self, full_path: str):  
        try:  
            if os.path.exists(full_path):  
                text = read_file(full_path)  
                self.chapter_result.delete("0.0","end")  
                self.chapter_result.insert("0.0", text)  
                self.chapter_result.see("end")  
        except Exception:  
            pass  
  
    def _apply_latest_chapter_on_start(self):  
        try:  
            fp = (self.filepath_var.get() or '').strip()  
            chap_dir = os.path.join(fp, 'chapters')  
            latest = 0  
            if os.path.isdir(chap_dir):  
                for name in os.listdir(chap_dir):  
                    if name.startswith('chapter_') and name.endswith('.txt') and name.count('_') == 1:  
                        num = name.split('_')[1].split('.')[0]  
                        if num.isdigit():  
                            latest = max(latest, int(num))  
            if latest > 0:  
                # 设置章节号并触发联动  
                if str(self.chapter_num_var.get()).strip() != str(latest):  
                    self.chapter_num_var.set(str(latest))  
                else:  
                    self._on_chapter_num_changed()  
        except Exception:  
            pass  
  
    def _on_filepath_changed(self):
        try:
            self._apply_latest_chapter_on_start()
        except Exception:
            pass
        try:
            self.update_vectorstore_button()
        except Exception:
            pass  
  
    def _on_chapter_num_changed(self):  
        try:  
            # 刷新下拉选单  
            if hasattr(self, 'refresh_draft_variants_list'):  
                self.refresh_draft_variants_list()  
            chap = str(self.chapter_num_var.get()).strip()  
            fp = (self.filepath_var.get() or '').strip()  
            if not (chap and fp):  
                return  
            # 优先主稿，其次最新变体  
            main_name = f'chapter_{chap}.txt'  
            main_path = os.path.join(fp, 'chapters', main_name)  
            selected = None  
            if os.path.exists(main_path):  
                selected = main_name  
            else:  
                drafts_dir = os.path.join(fp, 'chapters', '_drafts')  
                if os.path.isdir(drafts_dir):  
                    prefix = f'chapter_{chap}_'  
                    draft_vals = sorted([f for f in os.listdir(drafts_dir) if f.startswith(prefix) and f.endswith('.txt')])  
                    if draft_vals:  
                        selected = draft_vals[-1]  
            if selected:  
                try:  
                    self.draft_variant_select_var.set(selected)  
                except Exception:  
                    pass  
                # 加载到编辑区  
                if selected.count('_') == 1:  
                    full = os.path.join(fp, 'chapters', selected)  # 主稿  
                else:  
                    full = os.path.join(fp, 'chapters', '_drafts', selected)  
                self._load_text_and_show(full)  
        except Exception:  
            pass  
      
  

    def update_finalized_status_label(self):
        try:
            fp = (self.filepath_var.get() or "").strip() if hasattr(self, "filepath_var") else ""
            chap = str(self.chapter_num_var.get()).strip() if hasattr(self, "chapter_num_var") else ""
            def _apply(label, finalized):
                try:
                    if label:
                        label.configure(text=("已定稿" if finalized else ""))
                except Exception:
                    pass
            if not (hasattr(self, "finalized_hint_label") or hasattr(self, "finalized_hint_label_params")):
                return
            if not (fp and chap):
                _apply(getattr(self, "finalized_hint_label", None), False)
                _apply(getattr(self, "finalized_hint_label_params", None), False)
                return
            import os, json
            status_file = os.path.join(fp, "chapters", "status.json")
            finalized = False
            if os.path.exists(status_file):
                try:
                    with open(status_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    info = data.get(chap)
                    finalized = bool(info and info.get("finalized"))
                except Exception:
                    finalized = False
            _apply(getattr(self, "finalized_hint_label", None), finalized)
            _apply(getattr(self, "finalized_hint_label_params", None), finalized)
        except Exception:
            pass
    
    def update_vectorstore_button(self):
        try:
            # 支持两个位置的按钮：Main 右侧(self.btn_clear_vectorstore) 与 Chapters 顶栏(self.btn_clear_vectorstore_chapters)
            btns = []
            for name in ('btn_clear_vectorstore', 'btn_clear_vectorstore_chapters'):
                try:
                    btn = getattr(self, name, None)
                    if btn is not None:
                        btns.append(btn)
                except Exception:
                    pass
            if not btns:
                return
            fp = (self.filepath_var.get() or '').strip() if hasattr(self, 'filepath_var') else ''
            if not fp:
                for b in btns:
                    try:
                        b.configure(text=t('清空向量库'), fg_color='red', command=self.clear_vectorstore_handler)
                    except Exception:
                        pass
                return
            from novel_generator.vectorstore_utils import vector_store_is_empty
            empty = vector_store_is_empty(fp)
            for b in btns:
                try:
                    if empty:
                        b.configure(text=t('重建向量库'), command=self.rebuild_full_vectorstore_ui)
                    else:
                        b.configure(text=t('清空向量库'), fg_color='red', command=self.clear_vectorstore_handler)
                except Exception:
                    pass
        except Exception:
            pass

    def test_llm_config(self):  
  
        """  
  
        娴嬭瘯褰撳墠鐨凩LM配置鏄惁敤  
  
        """  
  
        interface_format = self.interface_format_var.get().strip()  
  
        api_key = self.api_key_var.get().strip()  
  
        base_url = self.base_url_var.get().strip()  
  
        model_name = self.model_name_var.get().strip()  
  
        temperature = self.temperature_var.get()  
  
        max_tokens = self.max_tokens_var.get()  
  
        timeout = self.timeout_var.get()  
  
  
  
        test_llm_config(  
  
            interface_format=interface_format,  
  
            api_key=api_key,  
  
            base_url=base_url,  
  
            model_name=model_name,  
  
            temperature=temperature,  
  
            max_tokens=max_tokens,  
  
            timeout=timeout,  
  
            log_func=self.safe_log,  
  
            handle_exception_func=self.handle_exception  
  
        )  
  
  
  
    def test_embedding_config(self):  
  
        """  
  
        娴嬭瘯褰撳墠鐨凟mbedding配置鏄惁敤  
  
        """  
  
        api_key = self.embedding_api_key_var.get().strip()  
  
        base_url = self.embedding_url_var.get().strip()  
  
        interface_format = self.embedding_interface_format_var.get().strip()  
  
        model_name = self.embedding_model_name_var.get().strip()  
  
  
  
        test_embedding_config(  
  
            api_key=api_key,  
  
            base_url=base_url,  
  
            interface_format=interface_format,  
  
            model_name=model_name,  
  
            log_func=self.safe_log,  
  
            handle_exception_func=self.handle_exception  
  
        )  
  
      
  
    def browse_folder(self):  
  
        selected_dir = filedialog.askdirectory()  
  
        if selected_dir:  
  
            self.filepath_var.set(selected_dir)  
  
  
  
    def show_character_import_window(self):  
  
        """鏄剧ず角色导入绐楀彛"""  
  
        import_window = ctk.CTkToplevel(self.master)  
  
        import_window.title("导入角色淇℃伅")  
  
        import_window.geometry("600x500")  
  
        import_window.transient(self.master)  # 璁剧疆涓虹埗绐楀彛鐨勪复鏃剁獥?  
  
        import_window.grab_set()  # 淇濇寔绐楀彛鍦ㄩ《灞?  
  
          
  
        # 涓诲鍣?  
  
        main_frame = ctk.CTkFrame(import_window)  
  
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)  
  
          
  
        # 婊氬姩瀹瑰櫒  
  
        scroll_frame = ctk.CTkScrollableFrame(main_frame)  
  
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)  
  
          
  
        # 鑾峰彇角色库撹矾寰?  
  
        role_lib_path = os.path.join(self.filepath_var.get().strip(), "角色库")  
  
        self.selected_roles = []  # 瀛樺偍閫変腑鐨勮鑹插悕绉?  
  
          
  
        # 鍔ㄦ€佸姞杞借鑹插垎绫?  
  
        if os.path.exists(role_lib_path):  
  
            # 配置缃戞牸甯冨眬参数  
  
            scroll_frame.columnconfigure(0, weight=1)  
  
            max_roles_per_row = 4  
  
            current_row = 0  
  
              
  
            for category in os.listdir(role_lib_path):  
  
                category_path = os.path.join(role_lib_path, category)  
  
                if os.path.isdir(category_path):  
  
                    # 鍒涘缓分类瀹瑰櫒  
  
                    category_frame = ctk.CTkFrame(scroll_frame)  
  
                    category_frame.grid(row=current_row, column=0, sticky="w", pady=(10,5), padx=5)  
  
                      
  
                    # 娣诲姞分类鏍囩  
  
                    category_label = ctk.CTkLabel(category_frame, text=f"【{category}】",   
  
                                                font=("Microsoft YaHei", 12, "bold"))  
  
                    category_label.grid(row=0, column=0, padx=(0,10), sticky="w")  
  
                      
  
                    # 初始化栬鑹叉帓鍒楀弬鏁?  
  
                    role_count = 0  
  
                    row_num = 0  
  
                    col_num = 1  # 浠庣1鍒楀紑濮嬶紙第鍒楁槸分类鏍囩：  
  
                      
  
                    # 娣诲姞角色澶嶉€夋  
  
                    for role_file in os.listdir(category_path):  
  
                        if role_file.endswith(".txt"):  
  
                            role_name = os.path.splitext(role_file)[0]  
  
                            if not any(name == role_name for _, name in self.selected_roles):  
  
                                chk = ctk.CTkCheckBox(category_frame, text=role_name)  
  
                                chk.grid(row=row_num, column=col_num, padx=5, pady=2, sticky="w")  
  
                                self.selected_roles.append((chk, role_name))  
  
                                  
  
                                # 鏇存柊琛屽垪浣嶇疆  
  
                                role_count += 1  
  
                                col_num += 1  
  
                                if col_num > max_roles_per_row:  
  
                                    col_num = 1  
  
                                    row_num += 1  
  
                      
  
                    # 濡傛灉娌℃湁角色：岃皟鏁村垎绫绘爣绛惧崰婊℃暣琛?  
  
                    if role_count == 0:  
  
                        category_label.grid(columnspan=max_roles_per_row+1, sticky="w")  
  
                      
  
                    # 鏇存柊涓诲竷灞€鐨勮?  
  
                    current_row += 1  
  
                      
  
                    # 娣诲姞鍒嗛殧绾?  
  
                    separator = ctk.CTkFrame(scroll_frame, height=1, fg_color="gray")  
  
                    separator.grid(row=current_row, column=0, sticky="ew", pady=5)  
  
                    current_row += 1  
  
          
  
        # 搴曢儴按钮妗嗘灦  
  
        btn_frame = ctk.CTkFrame(main_frame)  
  
        btn_frame.pack(fill="x", pady=10)  
  
          
  
        # 閫夋嫨按钮  
  
        def confirm_selection():  
  
            selected = [name for chk, name in self.selected_roles if chk.get() == 1]  
  
            self.char_inv_text.delete("0.0", "end")  
  
            self.char_inv_text.insert("0.0", ", ".join(selected))  
  
            import_window.destroy()  
  
              
  
        btn_confirm = ctk.CTkButton(btn_frame, text=t("閫夋嫨"), command=confirm_selection)  
  
        btn_confirm.pack(side="left", padx=20)  
  
          
  
        # 取消按钮  
  
        btn_cancel = ctk.CTkButton(btn_frame, text=t("取消"), command=import_window.destroy)  
  
        btn_cancel.pack(side="right", padx=20)  
  
  
  
    def show_role_library(self):  
        global RoleLibrary  
        if RoleLibrary is None:  
            try:  
                from .role_library import RoleLibrary as _RL  
                RoleLibrary = _RL  
            except Exception as e:  
                messagebox.showerror(t("错误"), t("角色库模块加载失败：{err}").format(err=str(e)))  
                return  
        save_path = self.filepath_var.get().strip()  
  
        if not save_path:  
  
            messagebox.showwarning(t("警告"), t("请先配置保存文件路径"))  
  
            return  
  
          
  
        # 初始化朙LM閫傞厤鍣?  
  
        llm_adapter = create_llm_adapter(  
  
            interface_format=self.interface_format_var.get(),  
  
            base_url=self.base_url_var.get(),  
  
            model_name=self.model_name_var.get(),  
  
            api_key=self.api_key_var.get(),  
  
            temperature=self.temperature_var.get(),  
  
            max_tokens=self.max_tokens_var.get(),  
  
            timeout=self.timeout_var.get()  
  
        )  
  
          
  
        # 浼犻€扡LM閫傞厤鍣ㄥ疄渚嬪埌角色库?  
  
        if hasattr(self, '_role_lib'):  
  
            if self._role_lib.window and self._role_lib.window.winfo_exists():  
  
                self._role_lib.window.destroy()  
  
          
  
        self._role_lib = RoleLibrary(self.master, save_path, llm_adapter)  # 鏂板参数  
  
  
  
    # ----------------- 灏嗗鍏ョ殑鍚勬ā鍧楀嚱鏁扮洿鎺ヨ祴缁欑被鏂规硶 -----------------  
  
    generate_novel_architecture_ui = generate_novel_architecture_ui  
  
    generate_chapter_blueprint_ui = generate_chapter_blueprint_ui  
  
    generate_chapter_draft_ui = generate_chapter_draft_ui  
  
    finalize_chapter_ui = finalize_chapter_ui  
  
    do_consistency_check = do_consistency_check  
  
    generate_batch_ui = generate_batch_ui  
  
    import_knowledge_handler = import_knowledge_handler  
  
    clear_vectorstore_handler = clear_vectorstore_handler  
    show_plot_arcs_ui = show_plot_arcs_ui  

    rebuild_full_vectorstore_ui = rebuild_full_vectorstore_ui

    open_embed_dashboard_ui = open_embed_dashboard_ui  

    load_config_btn = load_config_btn  
  
    save_config_btn = save_config_btn  
  
    load_novel_architecture = load_novel_architecture  
  
    save_novel_architecture = save_novel_architecture  
  
    load_chapter_blueprint = load_chapter_blueprint  
  
    save_chapter_blueprint = save_chapter_blueprint  
  
    load_character_state = load_character_state  
  
    save_character_state = save_character_state  
  
    load_global_summary = load_global_summary  
  
    save_global_summary = save_global_summary  
  
    refresh_chapters_list = refresh_chapters_list  
  
    on_chapter_selected = on_chapter_selected  
  
    save_current_chapter = save_current_chapter  
  
    prev_chapter = prev_chapter  
  
    next_chapter = next_chapter  
  
    test_llm_config = test_llm_config  
  
    test_embedding_config = test_embedding_config  
  
    browse_folder = browse_folder
  
    save_main_editor_content = save_main_editor_content  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
    def save_all_config(self):  
        try:  
            def _safe_int(var, default):  
                try:  
                    return int(var.get())  
                except Exception:  
                    try:  
                        return int(str(var.get()).strip())  
                    except Exception:  
                        return default  
  
            cfg = self.loaded_config if isinstance(self.loaded_config, dict) else {}  
            if not cfg:  
                cfg = {}  
  
            cfg.setdefault('llm_configs', {})  
            cfg.setdefault('embedding_configs', {})  
            cfg.setdefault('choose_configs', {})  
            cfg.setdefault('other_params', {})  
  
            try:  
                llm_name = str(self.interface_config_var.get()).strip()  
                if not llm_name:  
                    llm_name = 'Default'  
            except Exception:  
                llm_name = 'Default'  
  
            llm_item = {  
                'api_key': (self.api_key_var.get() if hasattr(self, 'api_key_var') else '').strip(),  
                'base_url': (self.base_url_var.get() if hasattr(self, 'base_url_var') else '').strip(),  
                'model_name': (self.model_name_var.get() if hasattr(self, 'model_name_var') else '').strip(),  
                'temperature': float(self.temperature_var.get()) if hasattr(self, 'temperature_var') else 0.7,  
                'max_tokens': _safe_int(self.max_tokens_var, 8192) if hasattr(self, 'max_tokens_var') else 8192,  
                'timeout': _safe_int(self.timeout_var, 600) if hasattr(self, 'timeout_var') else 600,  
                'interface_format': (self.interface_format_var.get() if hasattr(self, 'interface_format_var') else 'OpenAI')  
            }  
            cfg['llm_configs'][llm_name] = llm_item  
            cfg['last_interface_format'] = llm_item['interface_format']  
  
            emb_if = (self.embedding_interface_format_var.get().strip() if hasattr(self, 'embedding_interface_format_var') else 'OpenAI')  
            emb_item = {  
                'api_key': (self.embedding_api_key_var.get() if hasattr(self,'embedding_api_key_var') else '').strip(),  
                'base_url': (self.embedding_url_var.get() if hasattr(self,'embedding_url_var') else '').strip(),  
                'model_name': (self.embedding_model_name_var.get() if hasattr(self,'embedding_model_name_var') else '').strip(),  
                'retrieval_k': _safe_int(self.embedding_retrieval_k_var, 4) if hasattr(self, 'embedding_retrieval_k_var') else 4,  
                'interface_format': emb_if  
            }  
            cfg['embedding_configs'][emb_if] = emb_item  
            cfg['last_embedding_interface_format'] = emb_if  
  
            other = {  
                'topic': self.topic_text.get('0.0','end').strip() if hasattr(self,'topic_text') else '',  
                'genre': self.genre_var.get() if hasattr(self,'genre_var') else '',  
                'num_chapters': _safe_int(self.num_chapters_var, 1) if hasattr(self,'num_chapters_var') else 1,  
                'word_number': _safe_int(self.word_number_var, 10000) if hasattr(self,'word_number_var') else 10000,  
                'filepath': self.filepath_var.get() if hasattr(self,'filepath_var') else '',  
                'chapter_num': str(self.chapter_num_var.get()) if hasattr(self,'chapter_num_var') else '1',  
                'user_guidance': self.user_guide_text.get('0.0','end').strip() if hasattr(self,'user_guide_text') else '',  
                'characters_involved': self.characters_involved_var.get() if hasattr(self,'characters_involved_var') else '',  
                'key_items': self.key_items_var.get() if hasattr(self,'key_items_var') else '',  
                'scene_location': self.scene_location_var.get() if hasattr(self,'scene_location_var') else '',  
                'time_constraint': self.time_constraint_var.get() if hasattr(self,'time_constraint_var') else '',
                'draft_variants': _safe_int(self.draft_variants_var, 3) if hasattr(self,'draft_variants_var') else 3
            }  
            cfg['other_params'] = other  
  
            self.loaded_config = cfg  
            if save_config(cfg, self.config_file):  
                try:  
                    messagebox.showinfo('Info', 'Config saved to config.json')  
                except Exception:  
                    pass  
                if hasattr(self,'safe_log'):  
                    self.safe_log('Config saved to config.json')  
            else:  
                try:  
                    messagebox.showerror('Error', 'Failed to save config')  
                except Exception:  
                    pass  
        except Exception:  
            try:  
                messagebox.showerror('Error', 'Exception occurred while saving config')  
            except Exception:  
                pass  
    def refresh_draft_variants_list(self):  
        try:  
            filepath = self.filepath_var.get().strip()  
            chap = str(self.chapter_num_var.get()).strip()  
            if not (filepath and chap):  
                return  
            drafts_dir = os.path.join(filepath, 'chapters', '_drafts')  
            values = []  
            main_name = 'chapter_' + chap + '.txt'  
            main_path = os.path.join(filepath, 'chapters', main_name)  
            if os.path.exists(main_path):  
                values.append(main_name)  
            if os.path.exists(drafts_dir):  
                prefix = 'chapter_' + chap + '_'  
                files = os.listdir(drafts_dir)  
                draft_vals = [f for f in sorted(files) if f.startswith(prefix) and f.endswith('.txt')]  
                values.extend(draft_vals)  
            self.draft_variant_select_menu.configure(values=values)  
            cur = self.draft_variant_select_var.get()  
            if cur not in values:  
                if values:  
                    self.draft_variant_select_var.set(values[-1])  
                else:  
                    self.draft_variant_select_var.set('')  
        except Exception:  
            pass  
    def on_draft_variant_selected(self, value: str):  
        try:  
            if not value:  
                return  
            filepath = self.filepath_var.get().strip()  
            full = os.path.join(filepath, 'chapters', '_drafts', value)  
            if os.path.exists(full):  
                text = read_file(full)  
                self.chapter_result.delete('0.0','end')  
                self.chapter_result.insert('0.0', text)  
                self.chapter_result.see('end')  
        except Exception:  
            pass  
  
  
  
  
  
  
  
  
  
  
  
  










