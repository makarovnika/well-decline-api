"""Well Decline API — прогноз падения дебита скважин по Арпсу."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Well Decline API")
APP_AUTHOR = os.getenv("APP_AUTHOR", "Nikita Makarov")

app = FastAPI(title=APP_NAME)


@app.get("/")
def root():
    return {"message": f"{APP_NAME} работает", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
