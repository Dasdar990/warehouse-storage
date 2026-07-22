from app.schemas.item import ItemCreate
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_part_number_is_optional_when_creating_an_item() -> None:
    item = ItemCreate(
        name="Hex Bolt",
        barcode="ABC-123",
        category="Fasteners",
        size="small",
        shelf_position="12B",
        quantity=5,
    )

    assert item.pn == ""
