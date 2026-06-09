import random
import time
from collections.abc import Callable
from typing import Any

from app.scheduler.base import SchedulerQueue
from app.scheduler.heap_queue import HeapQueue
from app.scheduler.indexed_pq import IndexedPriorityQueue
from app.scheduler.skip_list import SkipList
from app.scheduler.timing_wheel import TimingWheel

NUM_ITEMS = 10000


def benchmark_structure(name: str, queue_cls: Callable[[], SchedulerQueue]) -> dict[str, Any]:
    """Run suite of performance tests on a single queue implementation."""

    results: dict[str, Any] = {"structure": name}

    # 1. Sequential Insert
    q = queue_cls()
    now = time.time()

    start = time.perf_counter()
    for i in range(NUM_ITEMS):
        q.push(f"job-{i}", priority=random.uniform(1.0, 3.0), scheduled_at=now, created_at=now)
    results["insert_ms"] = (time.perf_counter() - start) * 1000

    # 2. Sequential Extract (Min)
    start = time.perf_counter()
    for _ in range(NUM_ITEMS):
        q.pop()
    results["extract_ms"] = (time.perf_counter() - start) * 1000

    # 3. Mixed Workload (5000 inserts interleaved with 5000 pops)
    q = queue_cls()
    start = time.perf_counter()
    for i in range(NUM_ITEMS // 2):
        q.push(f"mixed-{i}", priority=random.uniform(1.0, 3.0), scheduled_at=now, created_at=now)
        q.pop()
    results["mixed_ms"] = (time.perf_counter() - start) * 1000

    # 4. Cancel / Remove by ID
    q = queue_cls()
    ids_to_cancel = []
    for i in range(NUM_ITEMS):
        job_id = f"cancel-{i}"
        q.push(job_id, priority=random.uniform(1.0, 3.0), scheduled_at=now, created_at=now)
        if random.random() < 0.5:
            ids_to_cancel.append(job_id)

    start = time.perf_counter()
    for job_id in ids_to_cancel:
        q.remove(job_id)
    results["cancel_ms"] = (time.perf_counter() - start) * 1000

    return results


def run_all_benchmarks() -> list[dict[str, Any]]:
    """Execute benchmarks across all 4 implementations."""
    return [
        benchmark_structure("HeapQueue", HeapQueue),
        benchmark_structure("TimingWheel", TimingWheel),
        benchmark_structure("IndexedPriorityQueue", IndexedPriorityQueue),
        benchmark_structure("SkipList", SkipList),
    ]
