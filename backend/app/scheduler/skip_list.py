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

    def _traverse(
        self, key: tuple[float, float, float] | None
    ) -> tuple[SkipListNode, list[SkipListNode]]:
        """Walk the skip list top-down, returning the landing node and an update array.

        Each update[i] holds the last node at level i whose forward pointer
        should be patched during an insert or delete.
        """
        update: list[SkipListNode] = [self.header] * (self.max_level + 1)
        current: SkipListNode = self.header

        for idx in range(self.level, -1, -1):
            fwd = current.forward[idx]
            while fwd is not None and fwd.key is not None and key is not None and fwd.key < key:
                current = fwd
                fwd = current.forward[idx]
            update[idx] = current

        return current, update

    def push(self, job_id: str, priority: float, scheduled_at: float, created_at: float) -> None:
        if job_id in self._lookup:
            self.remove(job_id)

        key = (priority, scheduled_at, created_at)
        _, update = self._traverse(key)

        lvl = self._random_level()

        if lvl > self.level:
            for idx in range(self.level + 1, lvl + 1):
                update[idx] = self.header
            self.level = lvl

        new_node = SkipListNode(key, job_id, lvl)
        self._lookup[job_id] = new_node

        for idx in range(lvl + 1):
            new_node.forward[idx] = update[idx].forward[idx]
            update[idx].forward[idx] = new_node

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

        _, update = self._traverse(key)

        node: SkipListNode | None = update[0].forward[0]

        # Walk forward at level 0 to find the exact node when keys collide.
        while node is not None and node.key == key and node.job_id != job_id:
            for idx in range(self.level, -1, -1):
                if update[idx].forward[idx] is node:
                    update[idx] = node
            node = node.forward[0]

        if node is not None and node.job_id == job_id:
            for idx in range(self.level + 1):
                if update[idx].forward[idx] is not node:
                    break
                update[idx].forward[idx] = node.forward[idx]

            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1

            del self._lookup[job_id]
            self._size -= 1
            return True

        return False

    def __len__(self) -> int:
        return self._size
