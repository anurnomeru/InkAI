# -*- coding: utf-8 -*-

import threading


def run_parallel_indexed_tasks(
    task_count: int,
    worker_fn,
    progress_cb=None,
    stop_requested=None,
    log_cb=None,
    task_name: str = "并发任务",
):
    total = max(0, int(task_count or 0))
    results = {}
    errors = {}
    if total <= 0:
        if progress_cb:
            progress_cb(0, 0)
        return results

    lock = threading.Lock()
    done = 0
    if progress_cb:
        progress_cb(0, total)

    def worker(index: int):
        nonlocal done
        try:
            if stop_requested and stop_requested():
                if log_cb:
                    log_cb(f"{task_name}：任务 {index}/{total} 在启动前已停止。")
                return
            value = worker_fn(index)
            with lock:
                results[index] = value
        except Exception as exc:
            with lock:
                errors[index] = exc
            if log_cb:
                log_cb(f"{task_name}：任务 {index}/{total} 失败：{str(exc)}")
        finally:
            with lock:
                done += 1
                current_done = done
            if progress_cb:
                progress_cb(current_done, total)

    threads = []
    for index in range(1, total + 1):
        t = threading.Thread(target=worker, args=(index,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results
