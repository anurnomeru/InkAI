# ui/shared_chapter_editor.py
# -*- coding: utf-8 -*-

import os
import re
import threading
import tkinter as tk

import customtkinter as ctk

from llm_adapters import create_llm_adapter
from novel_generator.common import invoke_with_cleaning
from ui.parallel_tasks import run_parallel_indexed_tasks
from ui.context_menu import TextWidgetContextMenu
from ui.running_button import TaskButtonController
from ui.text_shortcuts import install_text_shortcuts
from ui.theme import FONT_FAMILY, FONT_SIZES, SPACING, make_button
from ui.toast import show_toast


STYLE_GUIDANCE_FILENAME = "文风说明.txt"


def _read_widget_selection(widget):
    try:
        text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        start = widget.index(tk.SEL_FIRST)
        end = widget.index(tk.SEL_LAST)
        return (text or "").strip(), start, end
    except Exception:
        try:
            text = widget.selection_get()
            return (text or "").strip(), None, None
        except Exception:
            return "", None, None


def cache_widget_selection(widget) -> str:
    selected_text, start, end = _read_widget_selection(widget)
    if selected_text:
        setattr(widget, "_last_selected_text", selected_text)
        if start is not None:
            setattr(widget, "_last_selected_start", start)
        if end is not None:
            setattr(widget, "_last_selected_end", end)
    return selected_text


def get_cached_selection_text(widget) -> str:
    return (getattr(widget, "_last_selected_text", "") or "").strip()


def load_style_guidance_text(self) -> str:
    try:
        filepath = self.filepath_var.get().strip() if hasattr(self, "filepath_var") else ""
        if not filepath:
            return ""
        target_file = os.path.join(filepath, STYLE_GUIDANCE_FILENAME)
        if not os.path.exists(target_file):
            return ""
        with open(target_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def build_selection_polish_prompt(
    style_guidance: str,
    selected_text: str,
    user_extra_guidance: str = "",
) -> str:
    style_block = style_guidance.strip() if style_guidance else "未提供文风说明"
    selected_block = selected_text.strip()
    extra_block = user_extra_guidance.strip() if user_extra_guidance else "无"
    return f"""你是一个中文小说编辑助手。

任务：基于给定“文风说明”，只对下面选中的一段小说文字做润色改写。

要求：
1. 只参考“文风说明”和“选中文字”，不要引入额外剧情设定。
2. 保持原意大体一致，可以优化节奏、措辞、氛围、画面感。
3. 生成的内容必须是一段完整的、可直接替换原文的文本。
4. 不要解释，不要点评，不要输出任何额外说明。

【文风说明】
{style_block}

【补充说明】
{extra_block}

【选中文字】
{selected_block}
"""


def build_selection_polish_variant_prompt(
    base_prompt: str,
    variant_index: int,
    total_variants: int,
) -> str:
    return f"""{base_prompt}

补充要求：
1. 你现在只需要生成第{variant_index}/{total_variants}个候选版本。
2. 这个版本要与其他候选版本形成差异，可以在节奏、措辞、意象密度、情绪张力上有所偏重。
3. 只输出一个可直接替换原文的最终版本，不要加标题、编号、解释或引号。
"""


def parse_polish_variants(response_text: str) -> list[str]:
    if not response_text:
        return []

    variants = []
    pattern = re.compile(r"版本\s*([1-6])\s*[：:]\s*", re.MULTILINE)
    matches = list(pattern.finditer(response_text))

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(response_text)
        content = response_text[start:end].strip()
        if content:
            variants.append(content)

    if len(variants) == 6:
        return variants

    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    fallback = []
    for line in lines:
        cleaned = re.sub(r"^版本\s*[1-6]\s*[：:]\s*", "", line).strip()
        if cleaned:
            fallback.append(cleaned)
    return fallback[:6]


def replace_selected_text(widget, replacement_text: str) -> None:
    selected_text, current_start, current_end = _read_widget_selection(widget)
    if selected_text and current_start is not None and current_end is not None:
        start_index = current_start
        delete_start = current_start
        delete_end = current_end
    else:
        start_index = getattr(widget, "_last_selected_start", tk.SEL_FIRST)
        delete_start = getattr(widget, "_last_selected_start", tk.SEL_FIRST)
        delete_end = getattr(widget, "_last_selected_end", tk.SEL_LAST)
    widget.delete(delete_start, delete_end)
    widget.insert(start_index, replacement_text)
    setattr(widget, "_last_selected_text", replacement_text)


def _build_polish_dialog(master, variants: list[str], on_choose) -> None:
    dialog = ctk.CTkToplevel(master)
    dialog.title("选择润色版本")
    dialog.geometry("860x720")

    outer = ctk.CTkScrollableFrame(dialog)
    outer.pack(fill="both", expand=True, padx=10, pady=10)
    outer.columnconfigure(0, weight=1)

    for idx, variant in enumerate(variants, start=1):
        card = ctk.CTkFrame(outer)
        card.grid(row=idx - 1, column=0, sticky="ew", pady=(0, 10))
        card.columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            card,
            text=f"版本 {idx}",
            font=(FONT_FAMILY, FONT_SIZES["md"], "bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        text_box = ctk.CTkTextbox(
            card,
            wrap="word",
            height=110,
            font=(FONT_FAMILY, FONT_SIZES["md"]),
        )
        text_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        text_box.insert("1.0", variant)

        make_button(
            card,
            text="使用这个版本",
            command=lambda value=variant: on_choose(value, dialog),
            kind="primary",
            font=(FONT_FAMILY, FONT_SIZES["md"]),
        ).grid(row=2, column=0, sticky="e", padx=10, pady=(0, 10))

    bottom = ctk.CTkFrame(dialog)
    bottom.pack(fill="x", padx=10, pady=(0, 10))
    bottom.columnconfigure(0, weight=1)
    make_button(
        bottom,
        text="取消",
        command=lambda: on_choose(None, dialog),
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    ).grid(row=0, column=1, sticky="e")

    dialog.grab_set()


def _build_prompt_editor_dialog(master, initial_prompt: str, on_done) -> None:
    dialog = ctk.CTkToplevel(master)
    dialog.title("润色请求提示词（可编辑）")
    dialog.geometry("760x560")

    text_box = ctk.CTkTextbox(
        dialog,
        wrap="word",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    text_box.pack(fill="both", expand=True, padx=10, pady=10)
    text_box.insert("1.0", initial_prompt)

    wordcount_label = ctk.CTkLabel(
        dialog,
        text="字数：0",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    wordcount_label.pack(side="left", padx=(10, 0), pady=5)

    def update_word_count(event=None):
        text = text_box.get("1.0", "end-1c")
        wordcount_label.configure(text=f"字数：{len(text)}")

    text_box.bind("<KeyRelease>", update_word_count)
    text_box.bind("<ButtonRelease>", update_word_count)
    update_word_count()

    button_frame = ctk.CTkFrame(dialog)
    button_frame.pack(pady=10)
    action_state = {"done": False}
    buttons = []

    def _disable_actions():
        for btn in buttons:
            try:
                btn.configure(state="disabled")
            except Exception:
                pass

    def on_confirm():
        if action_state["done"]:
            return
        action_state["done"] = True
        _disable_actions()
        on_done(text_box.get("1.0", "end").strip(), dialog)

    def on_cancel():
        if action_state["done"]:
            return
        action_state["done"] = True
        _disable_actions()
        on_done(None, dialog)

    confirm_button = make_button(
        button_frame,
        text="确认生成",
        command=on_confirm,
        kind="primary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    cancel_button = make_button(
        button_frame,
        text="取消请求",
        command=on_cancel,
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    buttons.append(confirm_button)
    buttons.append(cancel_button)
    confirm_button.pack(side="left", padx=10)
    cancel_button.pack(side="left", padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.grab_set()


def open_selection_polish_prompt_dialog(self, initial_prompt: str):
    if not hasattr(self, "master") or self.master is None:
        return initial_prompt

    result = {"prompt": None}
    event = threading.Event()

    def _done(prompt_text, dialog):
        try:
            dialog.destroy()
        except Exception:
            pass
        result["prompt"] = prompt_text
        event.set()

    self.master.after(
        0,
        lambda: _build_prompt_editor_dialog(self.master, initial_prompt, _done),
    )
    event.wait()
    return result["prompt"]


def build_selection_polish_request(self, widget):
    selected_text, start, end = _read_widget_selection(widget)
    if selected_text:
        setattr(widget, "_last_selected_text", selected_text)
        if start is not None:
            setattr(widget, "_last_selected_start", start)
        if end is not None:
            setattr(widget, "_last_selected_end", end)
    else:
        selected_text = get_cached_selection_text(widget)
    if not selected_text:
        if hasattr(self, "safe_log"):
            self.safe_log("润色失败：请先选中一段文本。")
        return None

    style_guidance = load_style_guidance_text(self)
    prompt = build_selection_polish_prompt(
        style_guidance=style_guidance,
        selected_text=selected_text,
        user_extra_guidance="",
    )
    edited_prompt = open_selection_polish_prompt_dialog(self, prompt)
    if not edited_prompt:
        if hasattr(self, "safe_log"):
            self.safe_log("润色已取消：未发送生成请求。")
        return None

    chosen_name = self.prompt_draft_llm_var.get()
    llm_config = dict(self.loaded_config["llm_configs"][chosen_name])
    return {
        "selected_text": selected_text,
        "edited_prompt": edited_prompt,
        "llm_name": chosen_name,
        "llm_config": llm_config,
    }


def generate_selection_polish_variants(
    base_prompt: str,
    llm_invoke,
    variant_count: int = 6,
    progress_cb=None,
    stop_requested=None,
    log_cb=None,
) -> list[str]:
    def _worker(index: int):
        prompt = build_selection_polish_variant_prompt(
            base_prompt=base_prompt,
            variant_index=index,
            total_variants=variant_count,
        )
        response_text = llm_invoke(
            prompt,
            variant_index=index,
            total_variants=variant_count,
        )
        variants = parse_polish_variants(response_text)
        if variants:
            return variants[0]
        cleaned = (response_text or "").strip()
        if not cleaned:
            raise ValueError("LLM 返回空内容")
        return cleaned

    results = run_parallel_indexed_tasks(
        task_count=variant_count,
        worker_fn=_worker,
        progress_cb=progress_cb,
        stop_requested=stop_requested,
        log_cb=log_cb,
        task_name="润色并发任务",
    )
    return [
        results[index].strip()
        for index in range(1, variant_count + 1)
        if isinstance(results.get(index), str) and results[index].strip()
    ]


def polish_selected_text(self, widget, llm_invoke, choose_variant, progress_cb=None, stop_requested=None):
    request = build_selection_polish_request(self, widget)
    if not request:
        return None

    if hasattr(self, "safe_log"):
        self.safe_log("润色请求已确认，开始并发生成 6 个版本...")

    variants = generate_selection_polish_variants(
        base_prompt=request["edited_prompt"],
        llm_invoke=llm_invoke,
        variant_count=6,
        progress_cb=progress_cb,
        stop_requested=stop_requested,
        log_cb=getattr(self, "safe_log", None),
    )

    if len(variants) < 1:
        if hasattr(self, "safe_log"):
            self.safe_log("润色失败：未生成可用版本。")
        return None

    chosen = choose_variant(variants)
    if not chosen:
        if hasattr(self, "safe_log"):
            self.safe_log("润色已取消：未替换原文。")
        return None

    replace_selected_text(widget, chosen)
    if hasattr(self, "safe_log"):
        self.safe_log("润色完成：已替换选中文本。")
    return chosen


def _build_selection_polish_llm_invoke(llm_name: str, llm_config: dict, log_cb=None):
    adapter = create_llm_adapter(
        interface_format=llm_config["interface_format"],
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
        model_name=llm_config["model_name"],
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"],
        timeout=llm_config["timeout"],
    )
    if log_cb is not None:
        log_cb(
            f"润色选中文本：使用模型 {llm_name}/{llm_config['model_name']}，将并发生成 6 个版本..."
        )
    return lambda prompt, variant_index=None, total_variants=None: invoke_with_cleaning(adapter, prompt)


def _open_variant_choice_dialog(self, variants: list[str], on_done):
    def _on_choose(chosen, dialog):
        try:
            dialog.destroy()
        except Exception:
            pass
        on_done(chosen)

    self.master.after(0, lambda: _build_polish_dialog(self.master, variants, _on_choose))


def trigger_selection_polish(self, widget, controller=None):
    stop_state = {"requested": False}

    if controller and controller.running:
        return
    if widget is None:
        if hasattr(self, "safe_log"):
            self.safe_log("润色失败：未找到可用编辑器。")
        return

    def _confirm_stop():
        return tk.messagebox.askyesno("二次确认", "确定要停止当前润色任务吗？")

    def _request_stop():
        stop_state["requested"] = True
        if hasattr(self, "safe_log"):
            self.safe_log("已请求停止润色任务。当前步骤完成后会尽快停止。")

    if controller is not None:
        controller.confirm_stop = _confirm_stop
        controller.on_request_stop = _request_stop
        controller.start()

    request = build_selection_polish_request(self, widget)
    if not request:
        if controller is not None:
            controller.finish()
        return

    def task():
        try:
            if stop_state["requested"]:
                return
            result = {"choice": None}
            event = threading.Event()

            def choose_variant(variants):
                def _done(chosen):
                    result["choice"] = chosen
                    event.set()

                _open_variant_choice_dialog(self, variants, _done)
                event.wait()
                return result["choice"]

            llm_invoke = _build_selection_polish_llm_invoke(
                request["llm_name"],
                request["llm_config"],
                log_cb=getattr(self, "safe_log", None),
            )
            if hasattr(self, "safe_log"):
                self.safe_log("润色请求已确认，开始并发生成 6 个版本...")

            variants = generate_selection_polish_variants(
                base_prompt=request["edited_prompt"],
                llm_invoke=llm_invoke,
                variant_count=6,
                progress_cb=(
                    (lambda done, total: self.master.after(
                        0,
                        lambda d=done, t=total: controller.set_progress(d, t),
                    ))
                    if controller is not None and hasattr(self, "master")
                    else None
                ),
                stop_requested=lambda: stop_state["requested"],
                log_cb=getattr(self, "safe_log", None),
            )
            if len(variants) < 1:
                if hasattr(self, "safe_log"):
                    self.safe_log("润色失败：未生成可用版本。")
                return

            chosen = choose_variant(variants)
            if not chosen:
                if hasattr(self, "safe_log"):
                    self.safe_log("润色已取消：未替换原文。")
                return

            replace_selected_text(widget, chosen)
            if hasattr(self, "safe_log"):
                self.safe_log("润色完成：已替换选中文本。")
            replaced = chosen
            if replaced:
                try:
                    show_toast(widget, "已替换为润色版本", kind="success", duration_ms=1400)
                except Exception:
                    pass
        except Exception as e:
            if hasattr(self, "safe_log"):
                self.safe_log(f"润色失败：{str(e)}")
        finally:
            if controller is not None:
                try:
                    self.master.after(0, controller.finish)
                except Exception:
                    controller.finish()

    threading.Thread(target=task, daemon=True).start()


def create_selection_polish_button(self, parent, widget_getter):
    button = None
    controller = None

    def _run():
        widget = widget_getter()
        if widget is not None:
            cache_widget_selection(widget)
        trigger_selection_polish(self, widget, controller=controller)

    idle_command = _run
    button = make_button(
        parent,
        text="润色选中",
        command=idle_command,
        kind="secondary",
        font=(FONT_FAMILY, FONT_SIZES["md"]),
    )
    controller = TaskButtonController(
        button=button,
        idle_text="润色选中",
        running_text="润色中…",
        stop_text="停止润色",
        confirm_stop=lambda: tk.messagebox.askyesno("二次确认", "确定要停止当前润色任务吗？"),
        on_request_stop=lambda: None,
        idle_command=idle_command,
    )
    if not hasattr(self, "_selection_polish_button_controllers"):
        self._selection_polish_button_controllers = []
    self._selection_polish_button_controllers.append(controller)
    return button


def build_chapter_editor(
    self,
    parent,
    attribute_name: str,
    label_widget,
    label_template: str,
    save_handler,
    grid_row: int = 1,
    grid_column: int = 0,
    columnspan: int = 1,
    padx=None,
    pady=None,
):
    """构建章节正文编辑器，供主要功能页与章节管理页复用。"""
    if padx is None:
        padx = SPACING["sm"]
    if pady is None:
        pady = (0, SPACING["sm"])

    widget = ctk.CTkTextbox(
        parent,
        wrap="word",
        font=(FONT_FAMILY, FONT_SIZES["lg"]),
    )
    install_text_shortcuts(widget)
    TextWidgetContextMenu(widget)
    widget.grid(
        row=grid_row,
        column=grid_column,
        sticky="nsew",
        padx=padx,
        pady=pady,
        columnspan=columnspan,
    )

    def update_word_count(event=None):
        text = widget.get("0.0", "end")
        count = max(0, len(text) - 1)
        label_widget.configure(text=label_template.format(count=count))
        cache_widget_selection(widget)

    widget.bind("<KeyRelease>", update_word_count)
    widget.bind("<ButtonRelease>", update_word_count)
    widget.bind("<FocusOut>", lambda event=None: cache_widget_selection(widget))
    widget.bind("<Control-s>", lambda e: save_handler())

    setattr(self, attribute_name, widget)
    return widget
