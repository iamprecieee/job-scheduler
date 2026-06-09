from typing import Protocol


class SchedulerQueue(Protocol):
    def push(self, job_id: str, priority: float, scheduled_at: float, created_at: float) -> None:
        """Insert a job into the queue.

        Args:
            job_id: Unique identifier for the job.
            priority: The effective priority (lower number = higher urgency).
            scheduled_at: Unix timestamp when the job should run.
            created_at: Unix timestamp when the job was created (for FIFO tie-breaking).
        """
        ...

    def pop(self) -> str | None:
        """Extract and return the ID of the highest priority job that is ready to run.

        Returns:
            The job_id, or None if the queue is empty or no jobs are ready.
        """
        ...

    def peek(self) -> str | None:
        """Return the ID of the highest priority job without removing it.

        Returns:
            The job_id, or None if empty.
        """
        ...

    def remove(self, job_id: str) -> bool:
        """Remove a specific job from the queue.

        Args:
            job_id: The ID of the job to remove.

        Returns:
            True if the job was found and removed, False otherwise.
        """
        ...

    def __len__(self) -> int:
        """Return the number of jobs currently in the queue."""
        ...
