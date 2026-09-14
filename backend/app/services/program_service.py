"""Manages the admin-curated program catalog used by the item creation form."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.program import Program


def list_programs(db: Session) -> list[Program]:
    """All programs, alphabetically -- populates the item form's (optional) dropdown."""
    return list(db.execute(select(Program).order_by(Program.name)).scalars().all())



def get_program_by_name(db: Session, name: str) -> Program | None:
    return db.execute(select(Program).where(Program.name == name)).scalar_one_or_none()


def create_program(db: Session, name: str) -> Program:
    program = Program(name=name)
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


def update_program(db: Session, program_id: int, name: str) -> Program | None:
    """Rename a program and cascade the new name onto every item that
    currently carries the old one, so `Item.program` (free text) never
    drifts out of sync with the catalog it was chosen from."""
    program = db.get(Program, program_id)
    if program is None:
        return None

    old_name = program.name
    if old_name == name:
        return program

    db.execute(
        update(Item).where(Item.program == old_name).values(program=name)
    )
    program.name = name
    db.commit()
    db.refresh(program)
    return program


def delete_program(db: Session, program_id: int) -> bool:
    """Remove a program from the catalog. Existing items keep their (free-text) program value."""
    program = db.get(Program, program_id)
    if program is None:
        return False
    db.delete(program)
    db.commit()
    return True
