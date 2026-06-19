import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.routers import commute, coverage, geocode, isochrone, meta, stops


def _allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="15menit API", version="0.1.0")

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(geocode.router)
app.include_router(isochrone.router)
app.include_router(commute.router)
app.include_router(stops.router)
app.include_router(coverage.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
