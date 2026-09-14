"""Program catalog endpoints, managed from the admin Programs page and
consumed as an (optional) dropdown by the item creation form."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.schemas.program import ProgramCreate, ProgramOut, ProgramUpdate
from app.services import program_service

router = APIRouter(prefix="/programs", tags=["programs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ProgramOut])
def list_programs(db: Session = Depends(get_db)):
    """All programs in the catalog, alphabetically."""
    return program_service.list_programs(db)


@router.post("", response_model=ProgramOut, status_code=201)
def create_program(payload: ProgramCreate, db: Session = Depends(get_db)):
    """Add a new program to the catalog. Fails with 409 if the name already exists."""
    existing = program_service.get_program_by_name(db, payload.name)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f'Program "{payload.name}" already exists')
    return program_service.create_program(db, payload.name)


@router.patch("/{program_id}", response_model=ProgramOut)
def update_program(program_id: int, payload: ProgramUpdate, db: Session = Depends(get_db)):
    """
    Rename a program. The new name also replaces the old one on every
    item that currently uses it (see program_service.update_program),
    so item lists and filters stay consistent with the catalog.
    """
    existing = program_service.get_program_by_name(db, payload.name)
    if existing is not None and existing.id != program_id:
        raise HTTPException(status_code=409, detail=f'Program "{payload.name}" already exists')

    program = program_service.update_program(db, program_id, payload.name)
    if program is None:
        raise HTTPException(status_code=404, detail=f"No program found with id {program_id}")
    return program


@router.delete("/{program_id}", status_code=204)
def delete_program(program_id: int, db: Session = Depends(get_db)):
    """
    Remove a program from the catalog. Items that already used it keep
    their program text -- only the dropdown option disappears.
    """
    deleted = program_service.delete_program(db, program_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No program found with id {program_id}")
