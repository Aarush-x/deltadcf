import pytest

from settings import Settings


def test_production_rejects_wildcard_cors(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="Wildcard CORS"):
        Settings.from_env()


def test_production_rejects_ollama(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://example.vercel.app")

    with pytest.raises(RuntimeError, match="cloud provider"):
        Settings.from_env()


def test_cors_origins_are_normalized(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://one.vercel.app/, https://two.example.com",
    )

    loaded = Settings.from_env()

    assert loaded.cors_allowed_origins == (
        "https://one.vercel.app",
        "https://two.example.com",
    )
