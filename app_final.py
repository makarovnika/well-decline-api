"""Well Decline API — прогноз падения дебита скважин по Арпсу."""

import logging
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

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


class WellIn(BaseModel):
    """Параметры скважины для добавления в реестр."""

    name: str = Field(..., min_length=1, max_length=50, examples=["W-104"])
    field: str = Field(..., min_length=1, max_length=50, examples=["Северное"])
    qi: float = Field(..., gt=0, description="Начальный дебит, м³/сут")
    di: float = Field(..., gt=0, le=1, description="Темп падения, 1/месяц")
    b: float = Field(0.5, ge=0, le=1, description="Показатель Арпса")


class Well(WellIn):
    id: int


# Учебные (вымышленные) скважины; хранение в памяти процесса,
# после перезапуска сервиса реестр возвращается к этому набору.
WELLS: dict[int, Well] = {
    1: Well(id=1, name="W-101", field="Северное", qi=120, di=0.06, b=0.4),
    2: Well(id=2, name="W-102", field="Северное", qi=85, di=0.09, b=0),
    3: Well(id=3, name="W-201", field="Южное", qi=150, di=0.05, b=1),
}


def get_well_or_404(well_id: int) -> Well:
    well = WELLS.get(well_id)
    if well is None:
        logger.warning("Well %s not found", well_id)
        raise HTTPException(status_code=404, detail=f"Скважина {well_id} не найдена")
    return well
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


@app.get("/wells")
def list_wells(field: str | None = Query(None, description="Фильтр по месторождению")):
    """Список скважин, при необходимости — только одного месторождения."""
    wells = list(WELLS.values())
    if field:
        wells = [w for w in wells if w.field.lower() == field.lower()]
    return {"count": len(wells), "wells": wells}


@app.get("/wells/{well_id}")
def get_well(well_id: int):
    return get_well_or_404(well_id)


@app.post("/wells", status_code=201)
def create_well(data: WellIn):
    """Добавить скважину в реестр."""
    well_id = max(WELLS, default=0) + 1
    well = Well(id=well_id, **data.model_dump())
    WELLS[well_id] = well
    logger.info("Well created: id=%s name=%s field=%s", well_id, well.name, well.field)
    return well
