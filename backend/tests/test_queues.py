import time
import pytest
from typing import Type

from app.scheduler import HeapQueue, IndexedPriorityQueue, SkipList, TimingWheel
from app.scheduler.base import SchedulerQueue


@pytest.fixture(params=[HeapQueue, IndexedPriorityQueue, SkipList, TimingWheel])
def queue(request: pytest.FixtureRequest) -> SchedulerQueue:
    """Fixture that provides an instance of each queue implementation."""
    return request.param()


def test_push_and_pop_ordering(queue: SchedulerQueue) -> None:
    """Test that jobs are popped in order of priority, then scheduled_at, then created_at."""
    # To avoid time-gating, schedule them all in the past
    past_time = time.time() - 1000

    # Push jobs in random order
    queue.push("job-3", priority=3.0, scheduled_at=past_time, created_at=10)
    queue.push("job-1", priority=1.0, scheduled_at=past_time, created_at=20)
    queue.push("job-2", priority=2.0, scheduled_at=past_time, created_at=30)
    
    # Priority tie-breaker
    queue.push("job-1b", priority=1.0, scheduled_at=past_time + 10, created_at=40)
    queue.push("job-1a", priority=1.0, scheduled_at=past_time, created_at=10)

    assert len(queue) == 5

    # Should pop: job-1a (p=1, early sched), job-1 (p=1, same sched, later created), job-1b (p=1, later sched), job-2, job-3
    assert queue.pop() == "job-1a"
    assert queue.pop() == "job-1"
    assert queue.pop() == "job-1b"
    assert queue.pop() == "job-2"
    assert queue.pop() == "job-3"
    assert queue.pop() is None
    assert len(queue) == 0


def test_time_gating(queue: SchedulerQueue, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that jobs scheduled in the future are not popped."""
    base_time = time.time()
    monkeypatch.setattr(time, "time", lambda: base_time)

    # Job scheduled in the past
    queue.push("job-past", priority=1.0, scheduled_at=base_time - 10, created_at=base_time)
    # Job scheduled in the future
    queue.push("job-future", priority=1.0, scheduled_at=base_time + 10, created_at=base_time)

    # Only past job should be ready
    assert queue.peek() == "job-past"
    assert queue.pop() == "job-past"
    
    # Future job is still in the queue but not ready to be popped
    # Note: peek() returns the top item regardless of scheduled_at
    assert queue.peek() == "job-future" or queue.peek() is None
    assert queue.pop() is None
    assert len(queue) == 1

    # Advance time
    monkeypatch.setattr(time, "time", lambda: base_time + 20)

    # Now future job is ready
    assert queue.peek() == "job-future"
    assert queue.pop() == "job-future"
    assert len(queue) == 0


def test_remove(queue: SchedulerQueue) -> None:
    """Test that removing a job works and prevents it from being popped."""
    past_time = time.time() - 1000

    queue.push("job-1", priority=1.0, scheduled_at=past_time, created_at=10)
    queue.push("job-2", priority=2.0, scheduled_at=past_time, created_at=20)
    queue.push("job-3", priority=3.0, scheduled_at=past_time, created_at=30)

    assert len(queue) == 3

    # Remove the middle job
    assert queue.remove("job-2") is True
    assert queue.remove("job-missing") is False

    assert len(queue) == 2

    assert queue.pop() == "job-1"
    assert queue.pop() == "job-3"
    assert queue.pop() is None


def test_duplicate_push(queue: SchedulerQueue) -> None:
    """Test that pushing an existing job ID updates its priority/schedule."""
    past_time = time.time() - 1000

    queue.push("job-1", priority=5.0, scheduled_at=past_time, created_at=10)
    queue.push("job-2", priority=2.0, scheduled_at=past_time, created_at=20)

    # Currently job-2 is higher priority (2 < 5)
    
    # Update job-1 to have higher priority than job-2
    queue.push("job-1", priority=1.0, scheduled_at=past_time, created_at=10)

    # Length should still be 2
    assert len(queue) == 2

    # job-1 should be popped first now
    assert queue.pop() == "job-1"
    assert queue.pop() == "job-2"
    assert queue.pop() is None
