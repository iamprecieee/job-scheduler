# Security Policy

## Supported Versions

Currently, only the `main` branch (v1.0.0-beta) is supported with security updates.

## Reporting a Vulnerability

If you discover a security vulnerability within the Job Scheduler, please send an e-mail to security@example.com instead of using the issue tracker. All security vulnerabilities will be promptly addressed.

## Security Controls Implemented

- **CORS Policies**: Explicitly configured in `backend/app/config.py`.
- **Admin Tokens**: Protected endpoints (like `/benchmark`) require a valid `X-Admin-Token` header.
- **SQL Injection**: SQLAlchemy 2.0 ORM is used with parameterized queries to prevent SQL injection.
- **DDoS Protection**: Future deployment will incorporate Nginx rate limiting.
- **Data Access**: `SELECT ... FOR UPDATE SKIP LOCKED` ensures jobs cannot be hijacked by concurrent threads.
