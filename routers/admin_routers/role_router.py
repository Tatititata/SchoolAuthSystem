
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import User, Role
from app import auth
from .dependences import AdminDep

roles_router = APIRouter(
    prefix='/roles',
    tags=['Admin', 'Roles']
)

# ----Roles----

@roles_router.post("")
async def create_role(
    admin: AdminDep,
    session: SessionDep,
    name: str,
    description: str | None = None
):
    
    # Проверяем, не существует ли уже роль с таким именем
    existing = await session.execute(
        select(Role).where(Role.name == name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already exists")
    
    new_role = Role(name=name, description=description)
    session.add(new_role)
    await session.commit()
    await session.refresh(new_role)
    
    return {"id": new_role.id, "name": new_role.name, "description": new_role.description}


@roles_router.get("")
async def list_roles(
    admin: AdminDep,
    session: SessionDep
):
    # """Список всех ролей (только admin)"""
    
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]


@roles_router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    admin: AdminDep,
    session: SessionDep
):
    """Удалить роль (только admin)"""
    
    # Нельзя удалить роль admin
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.name == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin role")
    
    await session.delete(role)
    await session.commit()
    
    return {"message": f"Role '{role.name}' deleted"}