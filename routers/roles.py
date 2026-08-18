from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.engine.connection import get_db
from schemas.role import Roles
from models.role import Role
from routers.users import PermissionChecker

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    responses={404: {"description": "Not found"}}
)

@router.post("/")
def create_rol(rol: Roles, db: Session = Depends(get_db)):
    new_role = Role(**rol.model_dump())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@router.get("/")
def list_roles(authorize: bool = Depends(PermissionChecker('roles:read'))):
    return {"roles": "se muestra"}

