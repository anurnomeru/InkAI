# 线程与并发（Threading & Concurrency）

设计原则：
- UI 不阻塞：所有耗时操作（生成/导入/定稿/批量）均在线程中执行。
- UI 安全更新：统一通过 `self.master.after(0, ...)` 在主线程更新控件。
- 按钮防重入：`disable_button_safe/enable_button_safe` 在任务期间禁用对应按钮。
- 批量/并发：草稿并发生成通过多个 worker 线程各自请求 LLM、各自写文件；不会共享单一流。

关键方法（ui/main_window.py）：
- `safe_log(message)`：线程安全地把日志写到只读文本框。
- `handle_exception(context)`：捕捉异常堆栈、写日志并保持 UI 可用。
- `_apply_latest_chapter_on_start()`：启动推断最新章节并驱动联动。
- `_on_filepath_changed()` / `_on_chapter_num_changed()`：变量改变触发刷新变体列表与编辑区内容。
