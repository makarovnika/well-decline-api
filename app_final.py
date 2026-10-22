"""Well Decline API — прогноз падения дебита скважин по Арпсу."""

import logging
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Well Decline API")
APP_AUTHOR = os.getenv("APP_AUTHOR", "Nikita Makarov")
APP_VERSION = "0.1.0"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("well_decline")

app = FastAPI(title=APP_NAME, version=APP_VERSION)
logger.info("Starting %s v%s (author: %s)", APP_NAME, APP_VERSION, APP_AUTHOR)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.get("/")
def root():
    return {"message": f"{APP_NAME} работает", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"name": APP_NAME, "version": APP_VERSION, "author": APP_AUTHOR}
