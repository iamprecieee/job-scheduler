from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    project_name: str = "job-scheduler"
    api_v1_str: str = "/api/v1"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://localhost:5173",
    ]

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/job_scheduler"

    # SMTP (aiosmtpd local mock)
    smtp_host: str = "localhost"
    smtp_port: int = 8025
    alert_email_to: str = "admin@localhost"
    alert_email_from: str = "scheduler@localhost"

    # Scheduler
    max_retries: int = 3
    dlq_alert_threshold: int = 10
    aging_threshold_seconds: int = 300
    aging_weight: float = 1.0
    worker_poll_interval_seconds: float = 2.0
    scheduled_job_check_interval_seconds: float = 5.0
    aging_recalc_interval_seconds: float = 60.0

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
