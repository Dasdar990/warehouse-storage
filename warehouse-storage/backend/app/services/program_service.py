"""Manages the admin-curated program catalog used by the item creation form."""
from sqlalchemy import select
from sqlalchemy.orm import Session

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


def delete_program(db: Session, program_id: int) -> bool:
    """Remove a program from the catalog. Existing items keep their (free-text) program value."""
    program = db.get(Program, program_id)
    if program is None:
        return False
    db.delete(program)
    db.commit()
    return True
