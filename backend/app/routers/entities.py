from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Entity as DBEntity

router = APIRouter(prefix="/entities", tags=["entities"])

@router.get("")
async def get_entities(db: Session = Depends(get_db)):
    """Get all entities"""
    entities = db.query(DBEntity).all()
    return [{"id": e.id, "name": e.name, "type": e.entity_type} for e in entities]
