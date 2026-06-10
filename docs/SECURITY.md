# Security Policy

## Threat Model

Project protects **job execution state and administrative endpoints** for **backend systems and administrators**.

### In Scope

| Threat | Protection |
|--------|------------|
| Duplicate Execution | `SELECT ... FOR UPDATE SKIP LOCKED` guarantees zero duplicate processing. |
| Unauthorized Access | Protected administrative endpoints require a valid `X-Admin-Token` header. |
| SQL Injection | SQLAlchemy 2.0 ORM is used with parameterized queries. |
| Cross-Site Scripting (XSS) | Frontend relies on React's auto-escaping and sanitized REST outputs. |

### Out of Scope

- Root/administrator access to the underlying server/container.
- Physical access attacks to the database or servers.
- Social engineering attacks.

---

## Implementation

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database Locking | Postgres Row-Level Locks | Native and robust atomic job leasing across distributed worker nodes. |
| CORS Policy | Configurable origins | Restricts frontend access to known UI domains. |

---

## Known Limitations

1. **Denial of Service (DoS)**: The application currently lacks built-in rate limiting. A flood of job creation requests could exhaust database connections. This should be mitigated via an external reverse proxy (e.g., Nginx).
2. **Plaintext Admin Token**: The `X-Admin-Token` is currently transmitted as a plaintext header. Ensure the application is deployed behind HTTPS/TLS to encrypt traffic in transit.

---

## Vulnerability Disclosure

**Email:** security@example.com

Do not file public issues for security vulnerabilities.

| Stage | Timeline |
|-------|----------|
| Acknowledgment | 24 hours |
| Assessment | 72 hours |
| Fix | Severity-dependent |

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `fastapi` | Web Framework |
| `sqlalchemy` | ORM and Query Builder |
| `asyncpg` | Async PostgreSQL Driver |

Advisories tracked via `dependabot`/`pip-audit`.
