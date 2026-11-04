"""High Value Market Bot — entry point.

Runs fine without AI configured. AI tools simply become unavailable and the
non-AI tools (Website Analysis, Competitor Analysis, Account, Admin) keep
working.
"""

import logging
import os
import sys

import uvicorn
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application

from ai_service import AIService
from config import load_config
from database import Database
from handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def build_application() -> tuple[FastAPI, Application, Database, object]:
    config = load_config()

    db = Database(config.database_path)

    ai = None
    if config.ai_enabled:
        ai = AIService(
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
            model=config.ai_model,
            timeout=config.ai_timeout,
        )
        logger.info("AI features: ENABLED (model=%s, base=%s)", config.ai_model, config.ai_base_url)
    else:
        logger.info("AI features: DISABLED — set AI_API_KEY, AI_BASE_URL and AI_MODEL to enable")
        partial = bool(config.ai_api_key or config.ai_base_url or config.ai_model)
        if partial:
            logger.warning(
                "Partial AI config detected (some but not all AI_* vars are set). "
                "Set all three or none. AI remains disabled."
            )

    ptb = Application.builder().token(config.telegram_token).build()
    ptb.bot_data["db"] = db
    ptb.bot_data["ai"] = ai
    ptb.bot_data["config"] = config

    register_handlers(ptb)

    fastapi_app = FastAPI(title="High Value Market Bot", version="1.0.0")

    @fastapi_app.on_event("startup")
    async def _on_startup() -> None:
        await db.initialize()
        await ptb.initialize()
        await ptb.start()

        if config.webhook_url:
            webhook = f"{config.webhook_url.rstrip('/')}{config.webhook_path}"
            await ptb.bot.set_webhook(url=webhook, allowed_updates=Update.ALL_TYPES)
            logger.info("Webhook set to %s", webhook)
        else:
            await ptb.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            logger.info("Polling mode started")

    @fastapi_app.on_event("shutdown")
    async def _on_shutdown() -> None:
        try:
            if ptb.updater and ptb.updater.running:
                await ptb.updater.stop()
            await ptb.stop()
            await ptb.shutdown()
        finally:
            await db.close()

    @fastapi_app.get("/health")
    async def _health():
        return {"status": "ok", "ai_enabled": config.ai_enabled}

    @fastapi_app.get("/")
    async def _root():
        return {"bot": "High Value Market Bot", "status": "running", "ai_enabled": config.ai_enabled}

    @fastapi_app.post(config.webhook_path)
    async def _webhook(request: Request):
        data = await request.json()
        update = Update.de_json(data, ptb.bot)
        await ptb.update_queue.put(update)
        return Response(content="ok", media_type="text/plain")

    return fastapi_app, ptb, db, config


def main() -> None:
    # Presence check — prints only presence, never secrets
    print(
        "ENV CHECK:",
        "TELEGRAM_BOT_TOKEN=" + ("set" if os.environ.get("TELEGRAM_BOT_TOKEN") else "MISSING"),
        "ADMIN_ID=" + ("set" if os.environ.get("ADMIN_ID") else "MISSING"),
        "AI_API_KEY=" + ("set" if os.environ.get("AI_API_KEY") else "MISSING"),
        "AI_BASE_URL=" + ("set" if os.environ.get("AI_BASE_URL") else "MISSING"),
        "AI_MODEL=" + ("set" if os.environ.get("AI_MODEL") else "MISSING"),
        flush=True,
    )

    try:
        app, _ptb, _db, config = build_application()
    except RuntimeError as exc:
        logger.error("Startup configuration error: %s", exc)
        sys.exit(1)

    port = int(os.environ.get("PORT", config.port))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
