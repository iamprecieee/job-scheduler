import random
import time


class SkipListNode:
    def __init__(self, key: tuple[float, float, float] | None, job_id: str, level: int):
        self.key = key
        self.job_id = job_id
        self.forward: list[SkipListNode | None] = [None] * (level + 1)


class SkipList:
    def __init__(self, max_level: int = 16, prob: float = 0.5):
        self.max_level = max_level
        self.prob = prob

        self.header = SkipListNode(None, "", self.max_level)
        self.level = 0
        self._size = 0

        self._lookup: dict[str, SkipListNode] = {}

    def _random_level(self) -> int:
        lvl = 0
        while random.random() < self.prob and lvl < self.max_level:
            lvl += 1
        return lvl

    def push(self, job_id: str, priority: float, scheduled_at: float, created_at: float) -> None:
        if job_id in self._lookup:
            self.remove(job_id)

        key = (priority, scheduled_at, created_at)
        update: list[SkipListNode | None] = [None] * (self.max_level + 1)
        current = self.header

        for i in range(self.level, -1, -1):
            while (
                current.forward[i]
                and current.forward[i].key is not None
                and current.forward[i].key < key
            ):
                current = current.forward[i]
            update[i] = current

        lvl = _random_level = self._random_level()

        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.header
            self.level = lvl

        new_node = SkipListNode(key, job_id, lvl)
        self._lookup[job_id] = new_node

        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]  # type: ignore
            update[i].forward[i] = new_node  # type: ignore

        self._size += 1

    def pop(self) -> str | None:
        if self._size == 0:
            return None

        now = time.time()

        first_node = self.header.forward[0]
        if not first_node or first_node.key is None or first_node.key[1] > now:
            return None

        job_id = first_node.job_id
        self.remove(job_id)
        return job_id

    def peek(self) -> str | None:
        if self._size == 0:
            return None

        first_node = self.header.forward[0]
        if not first_node:
            return None

        return first_node.job_id

    def remove(self, job_id: str) -> bool:
        if job_id not in self._lookup:
            return False

        target_node = self._lookup[job_id]
        key = target_node.key

        update: list[SkipListNode | None] = [None] * (self.max_level + 1)
        current = self.header

        for i in range(self.level, -1, -1):
            while (
                current.forward[i]
                and current.forward[i].key is not None
                and current.forward[i].key < key
            ):
                current = current.forward[i]  # type: ignore
            update[i] = current

        current = current.forward[0]  # type: ignore

        while current and current.key == key and current.job_id != job_id:
            for i in range(self.level, -1, -1):
                if update[i].forward[i] == current:
                    update[i] = current
            current = current.forward[0]

        if current and current.job_id == job_id:
            for i in range(self.level + 1):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]

            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1

            del self._lookup[job_id]
            self._size -= 1
            return True

        return False

    def __len__(self) -> int:
        return self._size
