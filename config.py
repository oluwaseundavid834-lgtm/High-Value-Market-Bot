"""Environment-driven configuration. No secrets are ever hard-coded.

Only TELEGRAM_BOT_TOKEN and ADMIN_ID are strictly required.
AI features activate automatically when AI_API_KEY + AI_BASE_URL + AI_MODEL
are all set. If any are missing, the bot runs in "no-AI" mode where only
non-AI tools (Website Analysis, Competitor Analysis, Account, Admin) work.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    telegram_token: str
    admin_id: int
    ai_enabled: bool
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
    missing: list[str] = []

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        missing.append("TELEGRAM_BOT_TOKEN")

    admin_raw = os.environ.get("ADMIN_ID", "").strip()
    if not admin_raw:
        missing.append("ADMIN_ID")

    if missing:
        raise RuntimeError(
            "Missing required environment variables on Railway:\n  - "
            + "\n  - ".join(missing)
        )

    try:
        admin_id = int(admin_raw)
    except ValueError:
        raise RuntimeError(f"ADMIN_ID must be a numeric Telegram user ID, got: {admin_raw!r}")

    # AI is fully optional
    ai_key = os.environ.get("AI_API_KEY", "").strip()
    base_url = os.environ.get("AI_BASE_URL", "").strip()
    model = os.environ.get("AI_MODEL", "").strip()
    ai_enabled = bool(ai_key and base_url and model)

    webhook_url = os.environ.get("WEBHOOK_URL", "").strip()
    if not webhook_url:
        domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if domain:
            webhook_url = f"https://{domain}"

    return Config(
        telegram_token=token,
        admin_id=admin_id,
        ai_enabled=ai_enabled,
        ai_api_key=ai_key,
        ai_base_url=base_url.rstrip("/") if base_url else "",
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
