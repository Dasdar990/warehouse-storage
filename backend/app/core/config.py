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

    def __init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
