"""
Centralized configuration for the Warehouse Storage backend.

Everything environment-specific (paths, CORS, warehouse grid dimensions)
is read here once, so the rest of the app never touches os.environ
directly.
"""
import os
from functools import lru_cache
from pathlib import Path


class Settings:
    # --- Storage locations (mounted as Docker volumes in production) ---
    data_dir: Path = Path(os.getenv("DATA_DIR", "/app/data"))
    labels_dir: Path = Path(os.getenv("LABELS_DIR", "/app/labels"))
    # Static assets (e.g. logo.png) used when rendering printable labels.
    assets_dir: Path = Path(os.getenv("ASSETS_DIR", "/app/assets"))

    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.getenv('DATA_DIR', '/app/data')}/warehouse.db"
    )

    # --- CORS ---
    cors_allow_origins: str = os.getenv("CORS_ALLOW_ORIGINS", "*")

    # --- Warehouse map grid dimensions ---
    # The physical layout is a grid of shelf numbers (1..N) x level letters
    # (A, B, C, ...). These are just the *default* grid shown on the map;
    # any item whose shelf_position falls outside this range still shows up
    # (the grid auto-expands to fit real data — see shelf_service.py).
    warehouse_shelf_count: int = int(os.getenv("WAREHOUSE_SHELF_COUNT", "20"))
    warehouse_levels: list[str] = [
        lvl.strip().upper()
        for lvl in os.getenv("WAREHOUSE_LEVELS", "A,B,C,D").split(",")
        if lvl.strip()
    ]

    # Quantity at/below this threshold is flagged as "low stock" everywhere
    # (map coloring, dashboard filter, table highlighting).
    low_stock_threshold: int = int(os.getenv("LOW_STOCK_THRESHOLD", "3"))

    # --- Auth (JWT) ---
    # In production set JWT_SECRET_KEY explicitly (env var); the random
    # fallback just means every restart invalidates existing sessions,
    # which is an acceptable default for small internal tooling.
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7)))  # 7 days

    # Seeded once, only if the users table is empty -- change immediately after first login.
    default_admin_username: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    default_admin_password: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    def __init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
