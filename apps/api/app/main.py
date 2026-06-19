from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.routers import commute, coverage, geocode, isochrone, meta, stops

app = FastAPI(title="15menit API", version="0.1.0")

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
