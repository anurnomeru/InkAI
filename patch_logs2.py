from pathlib import Path
p = Path(r'ui/generation_handlers.py')
s = p.read_text(encoding='utf-8')
# 1) Add '将启动 {variant_count} 个变体线程' log
s = s.replace(
    'self.safe_log(f"开始并发生成 {variant_count} 个草稿版本...")',
    'self.safe_log(f"开始并发生成 {variant_count} 个草稿版本...")\n                self.safe_log(f"将启动 {variant_count} 个变体线程，超时时间 {timeout_val}s")'
)
# 2) Import inside worker and log
s = s.replace(
    'def worker(k:int):\n                    try:\n                        self.safe_log(f"[Variant {k}] 启动")\n                        target_path = os.path.join(drafts_dir, f"chapter_{chap_num}_{k}.txt")\n                        self.safe_log(f"[Variant {k}] 调用LLM...")\n                        text = generate_chapter_draft(',
    'def worker(k:int):\n                    try:\n                        self.safe_log(f"[Variant {k}] 启动")\n                        target_path = os.path.join(drafts_dir, f"chapter_{chap_num}_{k}.txt")\n                        from novel_generator.chapter import generate_chapter_draft as _gen\n                        self.safe_log(f"[Variant {k}] 调用LLM...")\n                        text = _gen('
)
# 3) Logs on thread creation
s = s.replace(
    'for k in range(1, variant_count+1):\n                    t = threading.Thread(target=worker, args=(k,), daemon=True)\n                    threads.append(t)\n                    t.start()',
    'for k in range(1, variant_count+1):\n                    self.safe_log(f"准备启动线程 {k}/{variant_count}")\n                    t = threading.Thread(target=worker, args=(k,), daemon=True)\n                    threads.append(t)\n                    t.start()\n                    self.safe_log(f"线程 {k} 已启动")'
)
# 4) Logs around join
s = s.replace(
    'for t in threads:\n                    t.join()',
    'self.safe_log("等待所有变体线程完成...")\n                for t in threads:\n                    t.join()\n                self.safe_log("所有变体线程已结束")'
)
p.write_text(s, encoding='utf-8')
print('applied more logs')
