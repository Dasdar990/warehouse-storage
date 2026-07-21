"""
Warehouse Storage — FastAPI backend entrypoint.

Route modules live in app/routers/:
    health.py      -> GET  /health
    items.py       -> GET  /items (filterable), GET /items/categories,
                      GET  /items/scan, GET /items/barcode/next,
                      POST /items, POST /items/withdraw
    labels.py      -> POST /items/label/{id} (raw PNG), GET /items/{id}/label (auto-print HTML)
    shelves.py     -> GET  /shelves, GET /shelves/positions,
                      GET  /shelves/{rack_code}/levels,
                      GET  /shelves/{shelf_position}/items, /shelves/config CRUD
    zones.py       -> GET/PUT /zones (delimited map areas)
    room.py        -> GET/PUT /room-layout (walls + door, purely visual orientation aid)
    categories.py  -> GET/POST /categories, DELETE /categories/{id}
    movements.py   -> GET /movements (live deposit/withdraw audit log)
    auth.py        -> POST /auth/login, GET /auth/me
    users.py       -> GET/POST/PATCH/DELETE /users (admin-only user management)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.routers import auth, categories, health, items, labels, movements, room, shelves, users, zones
from app.services.user_service import seed_default_admin

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


def _seed_default_admin() -> None:
    """
    If the users table is empty (fresh DB, or upgrading from a pre-auth
    version), create a default admin so there's a way to log in at all.
    Credentials: settings.default_admin_username / default_admin_password
    (admin / admin123 unless overridden) -- change the password immediately.
    """
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()


_seed_default_admin()

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
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(labels.router)
app.include_router(shelves.router)
app.include_router(zones.router)
app.include_router(room.router)
app.include_router(categories.router)
app.include_router(movements.router)

# Serves generated label PNGs for the auto-print HTML page (GET /items/{id}/label)
# so the browser always fetches the freshest file straight off disk.
# NOTE: intentionally left unauthenticated -- only exposes label PNGs (name,
# P/N, shelf, barcode), not stock levels or user data. Locking it down would
# mean replacing StaticFiles with a per-request token-checked endpoint, which
# felt like a lot of complexity for a low-value target. Happy to add it if
# you'd rather be strict about it.
app.mount("/labels_static", StaticFiles(directory=str(settings.labels_dir)), name="labels_static")
