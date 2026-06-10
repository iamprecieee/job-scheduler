import heapq
import time


class HeapQueue:
    """Min-heap implementation of the SchedulerQueue.

    Maintains jobs in a binary heap ordered by:
    1. priority (lower = higher urgency)
    2. scheduled_at (earlier = higher urgency)
    3. created_at (earlier = higher urgency, FIFO tie-breaker)
    """

    def __init__(self) -> None:
        self._heap: list[tuple[float, float, float, str]] = []
        self._entry_finder: dict[str, tuple[float, float, float, str]] = {}

    def push(self, job_id: str, priority: float, scheduled_at: float, created_at: float) -> None:
        if job_id in self._entry_finder:
            self.remove(job_id)

        entry = (priority, scheduled_at, created_at, job_id)
        self._entry_finder[job_id] = entry
        heapq.heappush(self._heap, entry)

    def pop(self) -> str | None:
        now = time.time()

        while self._heap:
            priority, scheduled_at, created_at, job_id = self._heap[0]

            if job_id not in self._entry_finder:
                heapq.heappop(self._heap)
                continue

            if scheduled_at > now:
                return None

            heapq.heappop(self._heap)
            del self._entry_finder[job_id]
            return job_id

        return None

    def peek(self) -> str | None:
        while self._heap:
            priority, scheduled_at, created_at, job_id = self._heap[0]
            if job_id not in self._entry_finder:
                heapq.heappop(self._heap)
                continue
            return job_id
        return None

    def remove(self, job_id: str) -> bool:
        return self._entry_finder.pop(job_id, None) is not None

    def __len__(self) -> int:
        return len(self._entry_finder)
