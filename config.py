"""Environment-driven configuration. No secrets are ever hard-coded."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    telegram_token: str
    admin_id: int
    ai_api_key: str
    ai_base_url: str
    ai_model: str
    ai_timeout: float
    database_path: str
    webhook_url: str
    webhook_path: str
    port: int
    free_daily_limit: int
    premium_daily_limit: int
    free_audit_limit: int
    premium_audit_limit: int


def _int_env(key: str, default: int) -> int:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_config() -> Config:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")

    admin_id = _int_env("ADMIN_ID", 0)

    ai_key = os.environ.get("AI_API_KEY", "").strip()
    if not ai_key:
        raise RuntimeError("AI_API_KEY environment variable is required")

    base_url = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("AI_MODEL", "gpt-4o-mini").strip()

    webhook_url = os.environ.get("WEBHOOK_URL", "").strip()
    if not webhook_url:
        domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if domain:
            webhook_url = f"https://{domain}"

    return Config(
        telegram_token=token,
        admin_id=admin_id,
        ai_api_key=ai_key,
        ai_base_url=base_url,
        ai_model=model,
        ai_timeout=float(os.environ.get("AI_TIMEOUT", "60") or 60),
        database_path=os.environ.get("DATABASE_PATH", "data/bot.db"),
        webhook_url=webhook_url,
        webhook_path=os.environ.get("WEBHOOK_PATH", "/webhook") or "/webhook",
        port=_int_env("PORT", 8000),
        free_daily_limit=_int_env("FREE_DAILY_LIMIT", 15),
        premium_daily_limit=_int_env("PREMIUM_DAILY_LIMIT", 300),
        free_audit_limit=_int_env("FREE_AUDIT_LIMIT", 2),
        premium_audit_limit=_int_env("PREMIUM_AUDIT_LIMIT", 50),
    )
