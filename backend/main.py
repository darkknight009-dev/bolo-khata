"""Bolo Khata FastAPI app."""
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, telegram_bot
from .db import get_engine  # noqa: F401  (import creates tables)
from .routes import router

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Bolo Khata", version="0.1.0")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.SITE_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    config.ensure_dirs()
    get_engine()
    if telegram_bot.configured():
        asyncio.create_task(telegram_bot.poll_loop())
        logging.getLogger("bolo.main").info("telegram poll loop scheduled")


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "google": bool(config.GOOGLE_CLIENT_ID),
        "telegram": bool(config.TELEGRAM_BOT_TOKEN),
        "gnani": bool(config.GNANI_API_KEY),
        "llm": bool(config.LLM_API_KEY),
        "llm_mock": config.LLM_MOCK,
    }
