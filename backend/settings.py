import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

LOCAL_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3001",
)
VALID_AI_PROVIDERS = {"auto", "gemini", "ollama"}


def _clean(value: str | None) -> str:
    return (value or "").strip().strip("'\"")


def _positive_int(name: str, default: int) -> int:
    raw_value = _clean(os.getenv(name))
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    port: int
    google_api_key: str | None
    ai_provider: str
    cors_allowed_origins: tuple[str, ...]
    ollama_model: str
    ollama_base_url: str
    reports_dir: Path
    external_request_timeout_seconds: int
    max_report_bytes: int
    sec_identity: str

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @classmethod
    def from_env(cls) -> "Settings":
        app_env = _clean(os.getenv("APP_ENV") or "development").lower()
        log_level = _clean(os.getenv("LOG_LEVEL") or "INFO").upper()
        api_key = _clean(os.getenv("GOOGLE_API_KEY")) or None
        provider_default = "gemini" if app_env == "production" else "auto"
        ai_provider = _clean(os.getenv("AI_PROVIDER") or provider_default).lower()

        if ai_provider not in VALID_AI_PROVIDERS:
            choices = ", ".join(sorted(VALID_AI_PROVIDERS))
            raise RuntimeError(f"AI_PROVIDER must be one of: {choices}")
        if app_env == "production" and ai_provider in {"auto", "ollama"}:
            raise RuntimeError("Production AI_PROVIDER must be a cloud provider (gemini)")

        origins_value = _clean(os.getenv("CORS_ALLOWED_ORIGINS"))
        if origins_value:
            origins = tuple(
                origin.strip().rstrip("/")
                for origin in origins_value.split(",")
                if origin.strip()
            )
        elif app_env == "production":
            origins = ()
        else:
            origins = LOCAL_CORS_ORIGINS

        if app_env == "production" and "*" in origins:
            raise RuntimeError("Wildcard CORS origins are not allowed in production")

        return cls(
            app_env=app_env,
            log_level=log_level,
            port=_positive_int("PORT", 8000),
            google_api_key=api_key,
            ai_provider=ai_provider,
            cors_allowed_origins=origins,
            ollama_model=_clean(os.getenv("OLLAMA_MODEL") or "gemma-4-12b-it-qat-q4_0"),
            ollama_base_url=_clean(os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/"),
            reports_dir=Path(_clean(os.getenv("REPORTS_DIR") or "reports")),
            external_request_timeout_seconds=_positive_int("EXTERNAL_REQUEST_TIMEOUT_SECONDS", 60),
            max_report_bytes=_positive_int("MAX_REPORT_BYTES", 25 * 1024 * 1024),
            sec_identity=_clean(
                os.getenv("SEC_IDENTITY") or "DeltaDCF support@example.com"
            ),
        )


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


settings = Settings.from_env()
configure_logging(settings)
