import uuid


class CycleDetectedError(ValueError):
    """Raised when adding a dependency would create a cycle in the DAG."""


def detect_cycle(
    job_id: uuid.UUID,
    dependencies: list[uuid.UUID],
    existing_edges: list[tuple[uuid.UUID, uuid.UUID]],
) -> bool:
    if job_id in dependencies:
        return True

    # Build adjacency list: node -> list of nodes it depends on
    adj: dict[uuid.UUID, list[uuid.UUID]] = {}
    for src, dest in existing_edges:
        if src not in adj:
            adj[src] = []
        adj[src].append(dest)

    adj[job_id] = dependencies

    visited: set[uuid.UUID] = set()
    rec_stack: set[uuid.UUID] = set()

    def dfs(node: uuid.UUID) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    # Only adding edges from job_id, any new cycle must involve job_id.
    # So only need to start DFS from job_id.
    return dfs(job_id)
