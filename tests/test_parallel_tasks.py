import os
import sys
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.parallel_tasks import run_parallel_indexed_tasks


def test_run_parallel_indexed_tasks_reports_progress_and_returns_results():
    progress = []
    barrier = threading.Barrier(3, timeout=1.5)

    def worker(index):
        barrier.wait()
        return f"result-{index}"

    results = run_parallel_indexed_tasks(
        task_count=3,
        worker_fn=worker,
        progress_cb=lambda done, total: progress.append((done, total)),
        task_name="测试任务",
    )

    assert results == {
        1: "result-1",
        2: "result-2",
        3: "result-3",
    }
    assert progress[0] == (0, 3)
    assert progress[-1] == (3, 3)
    assert len(progress) == 4
