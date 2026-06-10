# Contributing

We welcome contributions to the Background Job Scheduler!

## Development Workflow

1. **Branching**: Create a feature branch from `main` (e.g., `feature/add-new-queue-type`).
2. **Setup**: Run `uv sync` in `backend/` and `npm install` in `frontend/`.
3. **Backend Standards**:
   - All code must conform to the `backend_standards.md` guide.
   - Run `uv run ruff check .` and `uv run ruff format .` before committing.
   - Run `uv run mypy .` for static type checking.
   - Ensure you use `loguru` for all logging with `X-Request-ID` context via `structlog`-style `.bind()`.
4. **Frontend Standards**:
   - Use CSS variables for all colors and spacing to maintain the glassmorphism dark-mode theme.
   - Keep components lightweight and avoid heavy external dependencies.
5. **Testing**: 
   - Add `pytest-asyncio` tests for backend logic.
   - Ensure database queries don't cause locking issues.

## Pull Requests
Submit your PR against `main`. Ensure all CI checks pass.
