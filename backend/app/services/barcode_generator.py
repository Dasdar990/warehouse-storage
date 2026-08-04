from app.core.timezone import now_rome
from app.models.item import Item
from sqlalchemy import func, select
from sqlalchemy.orm import Session

DIGITS = 8


def generate_unique_barcode(db: Session) -> str:
    prefix = now_rome().strftime("%YIENER")

    max_id = db.execute(select(func.max(Item.id))).scalar()
    next_id = (max_id or 0) + 1

    formatted_id = f"{next_id:0{DIGITS}d}"
    return f"{prefix}{formatted_id}"
