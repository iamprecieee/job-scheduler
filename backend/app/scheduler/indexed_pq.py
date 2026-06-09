import time


class IndexedPriorityQueue:
    """Indexed Priority Queue implementation.

    Maintains 3 parallel arrays to allow O(log n) decrease-key operations
    which is useful for in-place aging updates.
    """

    def __init__(self) -> None:
        self.pq: list[str] = [""]
        self.qp: dict[str, int] = {}
        self.keys: dict[str, tuple[float, float, float]] = {}
        self._size: int = 0

    def push(self, job_id: str, priority: float, scheduled_at: float, created_at: float) -> None:
        key = (priority, scheduled_at, created_at)

        if job_id in self.qp:
            self.keys[job_id] = key
            self._swim(self.qp[job_id])
            self._sink(self.qp[job_id])
        else:
            self._size += 1
            self.pq.append(job_id)
            self.qp[job_id] = self._size
            self.keys[job_id] = key
            self._swim(self._size)

    def pop(self) -> str | None:
        now = time.time()

        if self._size == 0:
            return None

        top_job = self.pq[1]
        top_key = self.keys[top_job]

        if top_key[1] > now:
            return None

        self._exch(1, self._size)
        self._size -= 1
        self._sink(1)

        del self.qp[top_job]
        del self.keys[top_job]
        self.pq.pop()

        return top_job

    def peek(self) -> str | None:
        if self._size == 0:
            return None
        return self.pq[1]

    def remove(self, job_id: str) -> bool:
        if job_id not in self.qp:
            return False

        idx = self.qp[job_id]
        self._exch(idx, self._size)
        self._size -= 1
        self._sink(idx)
        self._swim(idx)

        del self.qp[job_id]
        del self.keys[job_id]
        self.pq.pop()

        return True

    def __len__(self) -> int:
        return self._size

    def _greater(self, i: int, j: int) -> bool:
        return self.keys[self.pq[i]] > self.keys[self.pq[j]]

    def _exch(self, i: int, j: int) -> None:
        self.pq[i], self.pq[j] = self.pq[j], self.pq[i]
        self.qp[self.pq[i]] = i
        self.qp[self.pq[j]] = j

    def _swim(self, k: int) -> None:
        while k > 1 and self._greater(k // 2, k):
            self._exch(k, k // 2)
            k //= 2

    def _sink(self, k: int) -> None:
        while 2 * k <= self._size:
            j = 2 * k
            if j < self._size and self._greater(j, j + 1):
                j += 1
            if not self._greater(k, j):
                break
            self._exch(k, j)
            k = j
