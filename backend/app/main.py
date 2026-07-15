"""
Warehouse Storage — FastAPI backend entrypoint.

Route modules live in app/routers/:
    health.py    -> GET  /health
    items.py     -> GET  /items (filterable), GET /items/categories,
                    GET  /items/scan, POST /items, POST /items/withdraw
    labels.py    -> POST /items/label/{id}
    shelves.py   -> GET  /shelves, GET /shelves/{rack_code}/levels,
                    GET  /shelves/{shelf_position}/items, /shelves/config CRUD
    zones.py     -> GET/PUT /zones (delimited map areas)
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.db import Base, engine
from app.routers import health, items, labels, shelves, zones

settings = get_settings()

# Create tables on startup (simple approach suitable for SQLite; a real
# multi-environment project would use Alembic migrations instead).
Base.metadata.create_all(bind=engine)


def _add_missing_columns() -> None:
    """
    `create_all` never alters an already-existing table, so a rack layout
    saved before the `rotation` column existed would otherwise crash on
    read. Add it in place for SQLite if it's missing; harmless no-op on a
    freshly created database.
    """
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.connect() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(shelves)"))}
        if "rotation" not in columns:
            conn.execute(text("ALTER TABLE shelves ADD COLUMN rotation FLOAT NOT NULL DEFAULT 0"))
            conn.commit()


_add_missing_columns()

app = FastAPI(
    title="Warehouse Storage API",
    description="Inventory tracking, withdrawal, and warehouse-map API for barcode-driven warehouse operations.",
    version="1.1.0",
)

cors_raw = settings.cors_allow_origins

if cors_raw == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in cors_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(items.router)
app.include_router(labels.router)
app.include_router(shelves.router)
app.include_router(zones.router)
