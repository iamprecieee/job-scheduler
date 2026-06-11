# Architecture Document: Job Scheduler

## Overview

This document details the architectural decisions and internal design of the Background Job Scheduler. The system is built with Python 3.14 (FastAPI) for the backend, React 19 (Vite) for the frontend, and PostgreSQL as the primary datastore.

## Core Components

### 1. The HTTP API (FastAPI)
The FastAPI application serves REST endpoints for job lifecycle management and a Server-Sent Events (SSE) endpoint for real-time monitoring.

- **Endpoints:** `/jobs` (CRUD), `/dlq` (Dead Letter Queue management), `/inbox` (Processed emails), `/sse/queue` (real-time queue length), `/inbox/stream` (real-time email updates).
- **Middleware:** `RequestLoggingMiddleware` injects structured request context (`X-Request-ID`) into every log line.
- **Concurrency:** Uses `asyncio` for non-blocking I/O. Intensive endpoints (like `/benchmark`) run in the `concurrent.futures` threadpool via `asyncio.to_thread()` or synchronous `def` routes to prevent event loop blocking.

### 2. Job Execution Model
- **Worker Loop:** A background coroutine (`worker_loop`) polls the database using `SELECT ... FOR UPDATE SKIP LOCKED`. This guarantees zero duplicate processing across multiple concurrent workers.
- **Handlers:** Job execution logic (e.g., `EmailHandler`) is dispatched to a `ProcessPoolExecutor` or `ThreadPoolExecutor` depending on whether it's CPU-bound or I/O-bound. This ensures the main `asyncio` event loop remains perfectly responsive.
- **Cancellation:** Cooperative cancellation is used. If a job is cancelled while `processing`, the worker checks the cancellation flag in the database before committing the final `completed` status. We avoid SIGKILL on workers to prevent corrupted external state (e.g., partially sent emails).

### 3. Scheduling Algorithms
The system implements four distinct algorithms for job queuing. By default, the Min-Heap is used, but all conform to the `SchedulerQueue` protocol.

- **Min-Heap (Default):** Python's `heapq`. Provides O(log n) insertions and extractions. Best general-purpose balance of speed and memory footprint.
- **Timing Wheel:** A hierarchical 2-level wheel (fine + coarse buckets). Provides O(1) amortized insertions and extractions. Fixed memory footprint.
- **Indexed Priority Queue:** Augments the binary heap with an inverse index array (`qp[]`). Allows O(log n) `decrease-key` operations for highly efficient priority adjustments (used in starvation prevention).
- **Skip List:** A probabilistic data structure with O(log n) expected time for all operations. Allows O(n) sequential ordered iteration and range queries.

### 4. DAG Dependency Resolver
Jobs can define `dependencies` (a list of other Job UUIDs). We provide an interactive UI for designing workflows visually.
- **Cycle Detection:** A Depth-First Search (DFS) runs at workflow creation time. If a back-edge is found, the workflow is rejected (`422 Unprocessable Entity`), preventing deadlocks before jobs are even spawned.
- **Execution Barrier:** The `SKIP LOCKED` query ensures a job is never picked up unless all jobs in its `depends_on_job_id` relation have `status = 'completed'`.

### 5. Starvation Prevention (Aging)
A background loop (`aging_loop`) runs every 60 seconds. It decreases the `effective_priority` of pending jobs linearly based on their age:
`effective_priority = base_priority - (age_in_seconds / 300) * 1.0`
A Low priority job becomes effectively Medium after 5 minutes, and High after 10 minutes, ensuring all jobs eventually execute.

### 6. Retry & Dead Letter Queue (DLQ)
Jobs that raise exceptions are retried up to 3 times.
- **Jitter Backoff:** Retries are delayed exponentially (1s, 5s, 25s) with a randomized jitter (`±20%`) to prevent "thundering herd" database stampedes.
- **DLQ Threshold Alerts:** When a job fails 3 times, it moves to the DLQ. A background `alert_loop` monitors the DLQ size. If the size exceeds the threshold (10), a real SMTP email is dispatched via the local `aiosmtpd` mock server.

## Database Schema
- `jobs`: Stores the job state, payload, retry counts, priority, and timestamps.
- `job_dependencies`: A mapping table for DAG relations.
- `dead_letter_queue`: Stores failed jobs with full stack traces.

All schemas are managed via Alembic migrations.

## Frontend
- **Framework:** React 19 + TypeScript + Vite.
- **Styling:** Vanilla CSS with custom CSS variables. Deep dark mode, glassmorphism (`backdrop-filter`), and dynamic glows mapped to Job Statuses.
- **Architecture:** `client.ts` wraps the `fetch` API for typed endpoints. The UI implements a robust 1.5-second fast-polling loop for near-real-time status updates across Jobs, DLQ, and Dashboard. `useSSE.ts` provides a robust, auto-reconnecting `EventSource` wrapper for the Dashboard raw queue metrics. A dedicated `useInboxSSE.ts` provides global toast notifications and powers the real-time Inbox page.
