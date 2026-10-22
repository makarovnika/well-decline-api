"""Well Decline API — прогноз падения дебита скважин по Арпсу."""

import logging
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request

import decline

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


@app.get("/decline/rate")
def decline_rate(
    qi: float = Query(..., gt=0, description="Начальный дебит, м³/сут"),
    di: float = Query(..., gt=0, le=1, description="Темп падения, 1/месяц"),
    b: float = Query(0.5, ge=0, le=1, description="Показатель Арпса"),
    t: float = Query(..., ge=0, le=600, description="Время, месяцы"),
):
    """Калькулятор: дебит и накопленная добыча через t месяцев."""
    q = decline.rate(qi, di, b, t)
    np_m3 = decline.cumulative(qi, di, b, t)
    logger.info("Rate calc: qi=%s di=%s b=%s t=%s -> q=%.2f", qi, di, b, t, q)
    return {
        "decline_type": decline.decline_type(b),
        "rate_m3_per_day": round(q, 3),
        "cumulative_m3": round(np_m3, 1),
    }
