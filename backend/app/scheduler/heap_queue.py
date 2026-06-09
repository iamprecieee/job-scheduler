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
        self._REMOVED = "<removed-task>"

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
            if job_id == self._REMOVED:
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
            if job_id == self._REMOVED:
                heapq.heappop(self._heap)
                continue
            return job_id
        return None

    def remove(self, job_id: str) -> bool:
        entry = self._entry_finder.pop(job_id, None)
        if entry is not None:
            idx = self._heap.index(entry) if entry in self._heap else -1
            if idx != -1:
                self._heap[idx] = (entry[0], entry[1], entry[2], self._REMOVED)
            return True
        return False

    def __len__(self) -> int:
        return len(self._entry_finder)
