# Job Scheduler

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-blue.svg)](https://react.dev/)

A highly concurrent, priority-based background job scheduler with real-time UI.

---

## Installation

<details open>
<summary><strong>Local Development</strong></summary>

```bash
# Clone the repository
git clone https://github.com/user/job-scheduler
cd job-scheduler

# Database Setup
createdb job_scheduler

# Backend Setup
cd backend
uv sync
uv run alembic upgrade head
cp .env.example .env

# Start mock SMTP
uv run python -m aiosmtpd -n -l localhost:8025 &

# Start Backend
uv run fastapi run

# Frontend Setup (in a new terminal)
cd ../frontend
npm install
npm run dev
```

</details>

---

## Usage

Visit `http://localhost:5173` to view the Dashboard.
Visit `http://localhost:8000/docs` to view the Swagger API Documentation.

<details>
<summary><strong>API Example</strong></summary>

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"type": "send_email", "payload": "{}", "priority": 1}'
```

</details>

---

## Features

| Feature | Description |
|---------|-------------|
| **Multiple Queue Algorithms** | Min-Heap (default), Timing Wheel, Indexed Priority Queue, and Skip List. |
| **DAG Workflow Engine** | Define jobs with dependencies that must complete before execution. |
| **Concurrency** | `FOR UPDATE SKIP LOCKED` guarantees zero duplicate processing across multiple concurrent workers. |
| **Real-Time UI** | Server-Sent Events (SSE) stream live queue lengths and job updates to a glassmorphism dashboard. |
| **Robust Retries & DLQ** | Jobs that fail 3 times are moved to a Dead Letter Queue and alert the `AlertService`. |

---

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `MAX_RETRIES` | `3` | Maximum number of times a job will be retried before DLQ. |
| `DLQ_ALERT_THRESHOLD` | `10` | Send an email alert when DLQ reaches this size. |
| `WORKER_POLL_INTERVAL_SECONDS` | `2.0` | How often the worker polls the database for new jobs. |
| `AGING_THRESHOLD_SECONDS` | `300` | Jobs waiting this long get a priority boost. |

---

## FAQ

<details>
<summary>How are overlapping recurring jobs handled?</summary>
The worker checks `job.scheduled_at` and computes the next interval. A new recurring job is only spawned once the current one completes successfully.
</details>
<details>
<summary>Can I scale the workers horizontally?</summary>
Yes! The `FOR UPDATE SKIP LOCKED` mechanism ensures multiple backend instances can pull from the same PostgreSQL table safely.
</details>

---

## License

[MIT](LICENSE)

---

[Contributing](CONTRIBUTING.md) | [Security](SECURITY.md) | [Code of Conduct](CODE_OF_CONDUCT.md)
