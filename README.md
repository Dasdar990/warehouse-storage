# Warehouse Storage

Nuxt 3 + FastAPI per la gestione dell'inventario di magazzino, ottimizzata per
operazioni sul campo tramite etichette adesive Code128 (28×89mm / 712×224px).

## Novità di questo refactoring

### 1. Ricerca & Localizzazione ("dove si trova?")
Nella home (`/`), la barra di ricerca unificata (`UnifiedSearchBar.vue`)
accetta sia digitazione manuale (Nome / P/N / Categoria, con autocompletamento)
sia input da lettore barcode nello stesso campo. Alla selezione di un
articolo, la mappa esegue automaticamente pan/zoom animato sullo scaffale di
destinazione, con un effetto glow pulsante verde sullo scaffale target.

### 2. Scan & Confirm ("prelevo e traccio")
Il campo di ricerca distingue una scansione da lettore barcode (sequenza di
tasti molto rapida + Invio) da una digitazione manuale, misurando il tempo
medio tra i tasti (`useBarcodeScanner.ts`). Una scansione barcode riconosciuta
esegue **automaticamente** l'azione impostata dal toggle
`🟢 DEPOSITA (+1)` / `🔴 PRELEVA (-1)` in alto nella barra di ricerca, e
registra il movimento con badge **🟢 Barcode Verified**. Le stesse azioni
richiamate manualmente dai pulsanti nella scheda articolo vengono registrate
con badge **⚠️ Manual Entry**.

### 3. Registro movimenti live
In fondo alla home, `ActivityLog.vue` mostra il feed scorrevole degli ultimi
movimenti (ora, operatore, azione, quantità, P/N, badge di tracciabilità),
alimentato dal nuovo endpoint `GET /movements`.

### 4. Etichette 28×89mm
Le etichette generate da `POST /items/label/{id}` sono ora **712×224px**
(28×89mm a 203dpi, lo standard delle stampanti termiche industriali), con lo
scaffale di destinazione stampato in grande per una lettura rapida durante il
prelievo/deposito.

## Nuovi endpoint backend

| Metodo | Path                | Descrizione                                          |
|--------|---------------------|-------------------------------------------------------|
| POST   | `/items/withdraw`   | Preleva stock (ora richiede `source` + `operator`, logga il movimento) |
| POST   | `/items/deposit`    | **Nuovo** — deposita stock (+N), stessa logica di audit |
| GET    | `/movements`        | **Nuovo** — ultimi movimenti (query `limit`, default 50) |

`StockMoveRequest` (`app/schemas/movement.py`):
```json
{
  "barcode": "BC1001",
  "quantity": 1,
  "source": "barcode" | "manual",
  "operator": "Mario Rossi"
}
```

## Struttura dei nuovi file frontend

```
frontend/
├── components/
│   ├── UnifiedSearchBar.vue   # input unificato scan/manuale + toggle modalità
│   ├── ItemDetailCard.vue     # scheda articolo, azioni rapide, stampa etichetta
│   ├── ActivityLog.vue        # registro movimenti live
│   └── map/
│       ├── WarehouseMap.vue   # griglia flat, ora con glow + auto-scroll
│       └── FreeformMap.vue    # canvas Konva, ora con pan/zoom animato + glow
├── composables/
│   ├── useBarcodeScanner.ts   # rilevamento scanner vs digitazione
│   ├── useOperationMode.ts    # toggle DEPOSITA/PRELEVA condiviso
│   └── useOperator.ts         # nome operatore condiviso, per il log
└── pages/
    └── index.vue              # orchestrazione: search bar → mappa → scheda → log
```

## Setup

Vedi `backend/README.md` e i `Dockerfile` in `backend/` e `frontend/` per
l'esecuzione via Docker Compose. In sviluppo locale:

```bash
# Backend
cd backend && poetry install && poetry run uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```
