# Warehouse Storage

A self-contained inventory tracking & withdrawal app built for barcode
scanner-gun workflows, with an interactive visual map of the warehouse.

```
warehouse-storage/
├── backend/                     FastAPI + SQLAlchemy + SQLite (Poetry)
│   ├── app/
│   │   ├── main.py                App factory, wires routers together
│   │   ├── core/
│   │   │   └── config.py          Env-driven settings (paths, CORS, grid size)
│   │   ├── db/
│   │   │   └── session.py         Engine, session factory, Base, get_db
│   │   ├── models/
│   │   │   ├── item.py            SQLAlchemy Item model + ItemSize enum
│   │   │   ├── shelf.py           SQLAlchemy Shelf model (a rack/"scaffale" on the map, with its levels)
│   │   │   └── zone.py            SQLAlchemy Zone model (delimited area drawn on the map)
│   │   ├── schemas/
│   │   │   ├── item.py            Item request/response schemas
│   │   │   ├── shelf.py           Warehouse-map / rack / mensola (level) schemas
│   │   │   └── zone.py            Zone schemas
│   │   ├── routers/
│   │   │   ├── health.py
│   │   │   ├── items.py           List (filterable), scan, create, withdraw
│   │   │   ├── labels.py          Printable Code128 label generation
│   │   │   ├── shelves.py         Grid layout, rack levels, per-mensola contents, rack layout CRUD
│   │   │   └── zones.py           Delimited-zone CRUD
│   │   └── services/
│   │       ├── label_generator.py Barcode label PNG rendering
│   │       ├── shelf_service.py    Aggregates items into the map + rack layout persistence
│   │       └── zone_service.py     Zone layout persistence
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                    Nuxt 3 (Vue 3), dark-mode, mobile-responsive
│   ├── pages/
│   │   ├── index.vue              Home: interactive warehouse map (zone → scaffale → mensola → items)
│   │   ├── scan.vue                Barcode-gun scan & withdraw workflow
│   │   ├── dashboard.vue           Search/filter dashboard + add item
│   │   └── map-config.vue          Drag-and-drop map builder: draw zones, then place racks
│   ├── components/
│   │   ├── map/WarehouseMap.vue        Clickable shelf grid (fallback, no custom layout)
│   │   ├── map/FreeformMap.vue         Clickable freeform map: zones + racks (custom layout)
│   │   ├── map/ZoneMapEditor.vue       Drag/resize/name canvas for delimiting zones
│   │   ├── map/ShelfMapEditor.vue      Drag/resize/rename canvas for placing racks + their mensole
│   │   ├── map/RackLevelsPanel.vue     Drill-down: a rack's mensole (levels) with stock counts
│   │   ├── map/ShelfDetailPanel.vue    Drill-down: a single mensola's items
│   │   └── dashboard/                  FilterBar, ItemTable, AddItemForm
│   ├── composables/
│   │   ├── useWarehouseApi.ts     Typed client for every backend endpoint
│   │   └── useToast.ts             Global success/error banner
│   ├── layouts/default.vue        Top nav (Map / Scan / Dashboard / Configure Map) + toast
│   └── Dockerfile
└── docker-compose.yml
```

## Quick start

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs (Swagger): http://localhost:8000/docs

The SQLite database and generated label images are stored in the named
Docker volumes `warehouse_db` and `warehouse_labels`, so `docker compose down`
(without `-v`) preserves all data.

## Frontend pages

- **`/` — Warehouse Map**: once a custom map has been drawn, an interactive
  canvas showing delimited **zones** (colored background areas, purely
  visual) and, on top, the **racks** ("scaffali") placed inside them.
  Clicking a rack opens a panel listing its **mensole** (shelf levels);
  clicking a mensola then shows exactly what's stored there, with a link
  to jump into the Dashboard pre-filtered to that shelf. Until a custom
  map is drawn, this falls back to an auto-generated grid (columns are
  shelf numbers, rows are levels).
- **`/map-config` — Configure Warehouse Map**: a two-step builder. First
  delimit **zones** (name + color, drag/resize rectangles) to represent
  physical areas of the warehouse. Then place **racks**: each gets a
  numeric code, one or more levels/mensole (e.g. "A,B,C,D"), and an
  optional zone. A rack's code + level must match the shelf codes used on
  items (e.g. rack "12" + level "B" → item shelf "12B"), so stock shows up
  correctly on the map.
- **`/scan` — Scanner workflow**: the barcode input auto-focuses on load and
  refocuses after every action, so a hardware scanner gun (types the code +
  presses Enter) works without touching the mouse. Enter looks the item up;
  a second Enter (or the Confirm button) submits the withdrawal.
- **`/dashboard` — Search & filters**: full-text search (name/P/N/barcode)
  plus category, size, shelf, and low-stock filters, backed directly by
  `GET /items` query params. Also hosts the "+ New Item" form.

## API

| Method | Path                             | Description                                          |
|--------|-----------------------------------|-------------------------------------------------------|
| GET    | `/items`                          | List items — filters: `search`, `category`, `size`, `shelf_position`, `low_stock` |
| GET    | `/items/categories`               | Distinct categories currently in use                   |
| GET    | `/items/scan?barcode=`            | Look up one item by barcode (404 if missing)           |
| POST   | `/items`                          | Create an item (409 if barcode already exists)         |
| POST   | `/items/withdraw`                 | Withdraw stock — body: `{barcode, quantity}`           |
| POST   | `/items/label/{id}`               | Generate & download a printable Code128 label          |
| GET    | `/shelves`                        | Full grid + zones + racks with aggregates (for the map) |
| GET    | `/shelves/{rack_code}/levels`     | A rack's mensole (levels) with stock aggregates         |
| GET    | `/shelves/{shelf_position}/items` | Items on one mensola, e.g. `12B` (drill-down)           |
| GET    | `/shelves/config`                 | Saved rack layout (raw rack boxes + levels + zone)      |
| PUT    | `/shelves/config`                 | Replace the whole rack layout — body: `{nodes: [...]}` |
| GET    | `/zones`                          | Saved zones (delimited map areas)                       |
| PUT    | `/zones`                          | Replace the whole set of zones — body: `{zones: [...]}` |
| GET    | `/health`                         | Health check                                            |

**Item fields:** `name`, `pn`, `barcode` (unique), `category` (free text),
`size` (`small` \| `big` \| `xl`), `shelf_position` (`<rack code><level>`,
e.g. `12B` or `3A`), `quantity`.

## Local development (without Docker)

**Backend**
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
NUXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

## Configuration

| Variable                  | Where     | Purpose                                                        |
|----------------------------|-----------|------------------------------------------------------------------|
| `DATA_DIR`                 | backend   | Directory for the SQLite file (default `/app/data`)              |
| `LABELS_DIR`                | backend   | Directory for generated label PNGs (`/app/labels`)                |
| `CORS_ALLOW_ORIGINS`        | backend   | Restrict CORS to your frontend's origin in production             |
| `WAREHOUSE_SHELF_COUNT`     | backend   | Default number of shelf columns shown on the map (default `20`)   |
| `WAREHOUSE_LEVELS`          | backend   | Comma-separated level letters, e.g. `A,B,C,D`                      |
| `LOW_STOCK_THRESHOLD`       | backend   | Quantity at/below which a shelf/item is flagged "low stock"       |
| `NUXT_PUBLIC_API_BASE`      | frontend  | Browser-reachable URL of the backend API                          |
