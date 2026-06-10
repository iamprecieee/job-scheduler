import time


class TimingWheel:
    """Hierarchical timing wheel implementation.

    A 2-level hierarchy (fine: 60x1s, coarse: 60x60s) for O(1) inserts.
    Jobs are sorted within their buckets by priority when extracted.
    """

    def __init__(self) -> None:
        self.fine_slots = 60
        self.coarse_slots = 60

        self.fine_wheel: list[list[tuple[float, float, float, str]]] = [
            [] for _ in range(self.fine_slots)
        ]
        self.coarse_wheel: list[list[tuple[float, float, float, str]]] = [
            [] for _ in range(self.coarse_slots)
        ]

        self._entries: dict[str, tuple[str, int, tuple[float, float, float, str]]] = {}
        self.current_tick: int = int(time.time())
        self._ready_buffer: list[tuple[float, float, float, str]] = []

    def push(self, job_id: str, priority: float, scheduled_at: float, created_at: float) -> None:
        if job_id in self._entries:
            self.remove(job_id)

        delay = int(scheduled_at) - self.current_tick
        entry = (priority, scheduled_at, created_at, job_id)

        if delay <= 0:
            self._ready_buffer.append(entry)
            self._ready_buffer.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
            self._entries[job_id] = ("ready", -1, entry)
            return

        if delay < self.fine_slots:
            bucket_idx = (self.current_tick + delay) % self.fine_slots
            self.fine_wheel[bucket_idx].append(entry)
            self._entries[job_id] = ("fine", bucket_idx, entry)
        elif delay < self.fine_slots * self.coarse_slots:
            coarse_tick = (self.current_tick + delay) // self.fine_slots
            bucket_idx = coarse_tick % self.coarse_slots
            self.coarse_wheel[bucket_idx].append(entry)
            self._entries[job_id] = ("coarse", bucket_idx, entry)
        else:
            bucket_idx = (self.current_tick // self.fine_slots - 1) % self.coarse_slots
            self.coarse_wheel[bucket_idx].append(entry)
            self._entries[job_id] = ("coarse", bucket_idx, entry)

    def _advance_clock(self) -> None:
        """Advance the wheel to current time, cascading and buffering ready jobs."""
        now = int(time.time())
        ticks_to_advance = now - self.current_tick

        if ticks_to_advance <= 0:
            return

        ticks_to_advance = min(ticks_to_advance, self.fine_slots * self.coarse_slots)

        for _ in range(ticks_to_advance):
            self.current_tick += 1
            fine_idx = self.current_tick % self.fine_slots

            for entry in self.fine_wheel[fine_idx]:
                if entry[3] in self._entries:
                    self._ready_buffer.append(entry)
                    self._entries[entry[3]] = ("ready", -1, entry)
            self.fine_wheel[fine_idx].clear()

            if fine_idx == 0:
                coarse_idx = (self.current_tick // self.fine_slots) % self.coarse_slots
                cascading_jobs = self.coarse_wheel[coarse_idx]
                self.coarse_wheel[coarse_idx] = []

                for entry in cascading_jobs:
                    job_id = entry[3]
                    if job_id in self._entries:
                        del self._entries[job_id]
                        self.push(job_id, entry[0], entry[1], entry[2])

        self._ready_buffer.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

    def pop(self) -> str | None:
        self._advance_clock()
        if self._ready_buffer:
            job_id = self._ready_buffer.pop()[3]
            del self._entries[job_id]
            return job_id
        return None

    def peek(self) -> str | None:
        self._advance_clock()
        if self._ready_buffer:
            return self._ready_buffer[-1][3]
        return None

    def remove(self, job_id: str) -> bool:
        if job_id in self._entries:
            wheel, idx, entry = self._entries.pop(job_id)
            if wheel == "fine":
                if entry in self.fine_wheel[idx]:
                    self.fine_wheel[idx].remove(entry)
            elif wheel == "coarse":
                if entry in self.coarse_wheel[idx]:
                    self.coarse_wheel[idx].remove(entry)
            elif wheel == "ready":
                if entry in self._ready_buffer:
                    self._ready_buffer.remove(entry)
            return True

        return False

    def __len__(self) -> int:
        return len(self._entries)
