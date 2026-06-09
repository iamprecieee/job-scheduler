def recalculate_effective_priority(
    base_priority: int, age_seconds: float, threshold_seconds: int = 300, weight: float = 1.0
) -> float:
    """Calculate effective priority to prevent starvation.

    Formula: effective_priority = base_priority - (age_seconds / threshold_seconds) * weight

    Lower numbers mean higher urgency. As a job ages past the threshold,
    its priority number decreases, moving it up the queue.

    Args:
        base_priority: The original priority (1=High, 2=Medium, 3=Low)
        age_seconds: How long the job has been pending or waiting to retry
        threshold_seconds: The unit of age that decreases priority by 1 * weight
        weight: How aggressively to apply aging

    Returns:
        float: The effective priority
    """
    if age_seconds <= 0:
        return float(base_priority)

    aging_bonus = (age_seconds / threshold_seconds) * weight
    return float(base_priority) - aging_bonus
