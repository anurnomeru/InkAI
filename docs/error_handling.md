# 日志与异常（Logging & Errors）

- 日志输出：
  - UI 日志：`self.log_text`（只读）；通过 `safe_log()` 在主线程刷新。
  - 后端日志：`novel_generator/chapter.py` 等模块使用 `logging` 写入 `app.log`（追加模式）。
- 异常处理：
  - UI 层：`handle_exception(context)` 汇总 traceback 并记录；必要时弹窗。
  - 读写容错：文件读/写/编码失败时打印友好信息并继续（尽量不阻塞主流程）。
- 交互提示：
  - 关键步骤前 `askyesno` 二次确认（如清空向量库）。
  - 配置缺失或路径为空：`messagebox.showwarning` 引导用户先设置保存路径。
