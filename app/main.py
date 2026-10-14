from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.analyze import router

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
app = FastAPI(title="Meeting Intelligence", version="0.1.0")
app.include_router(router)
