# Background Job Scheduler

A highly concurrent, priority-based background job scheduler with real-time UI. Built with Python 3.14 (FastAPI), React 19 (Vite), and PostgreSQL.

## Features

- **Multiple Queue Algorithms**: Min-Heap (default), Timing Wheel, Indexed Priority Queue, and Skip List.
- **DAG Workflow Engine**: Define jobs with dependencies that must complete before execution.
- **Concurrency**: `FOR UPDATE SKIP LOCKED` guarantees zero duplicate processing across multiple concurrent workers.
- **Real-Time UI**: Server-Sent Events (SSE) stream live queue lengths and job updates to a glassmorphism dashboard.
- **Robust Retries & DLQ**: Jobs that fail 3 times are moved to a Dead Letter Queue and alert the `AlertService` (which sends an email via `aiosmtpd`).

## Requirements
- Python 3.14
- Node.js 20+
- PostgreSQL 16
- `uv` package manager

## Quick Start

### 1. Database Setup
```bash
# Ensure PostgreSQL is running
createdb job_scheduler
```

### 2. Backend Setup
```bash
cd backend
uv sync
uv run alembic upgrade head

# Start the mock SMTP server (in a separate terminal)
uv run python -m aiosmtpd -n -l localhost:1025

# Start the FastAPI server
uv run fastapi run
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to view the Dashboard.
Visit `http://localhost:8000/docs` to view the Swagger API Documentation.
