"""
Warehouse Storage — FastAPI backend entrypoint.

Route modules live in app/routers/:
    health.py      -> GET  /health
    items.py       -> GET  /items (filterable), GET /items/categories,
                      GET  /items/scan, GET /items/barcode/next,
                      POST /items, POST /items/withdraw
    labels.py      -> POST /items/label/{id}
    shelves.py     -> GET  /shelves, GET /shelves/positions,
                      GET  /shelves/{rack_code}/levels,
                      GET  /shelves/{shelf_position}/items, /shelves/config CRUD
    zones.py       -> GET/PUT /zones (delimited map areas)
    room.py        -> GET/PUT /room-layout (walls + door, purely visual orientation aid)
    categories.py  -> GET/POST /categories, DELETE /categories/{id}
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.db import Base, engine
from app.routers import categories, health, items, labels, room, shelves, zones

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

        # The `walls` table's very first shape (two endpoints, x1/y1/x2/y2)
        # turned out to be fiddly to drag/reshape reliably, so it was
        # replaced with the same "rectangle you drag/resize/rotate" model
        # already used for racks. This is a brand-new, purely-visual table
        # with nothing worth preserving, so just drop and let create_all's
        # sibling call above (already run) recreate it with the new columns.
        wall_columns = {row[1] for row in conn.execute(text("PRAGMA table_info(walls)"))}
        if wall_columns and "width" not in wall_columns:
            conn.execute(text("DROP TABLE walls"))
            conn.commit()
            Base.metadata.tables["walls"].create(bind=engine)


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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(items.router)
app.include_router(labels.router)
app.include_router(shelves.router)
app.include_router(zones.router)
app.include_router(room.router)
app.include_router(categories.router)
