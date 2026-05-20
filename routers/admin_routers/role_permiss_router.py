
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import Permission, User, Role, RolePermission
from app import auth
from .dependences import AdminDep
role_permiss_router = APIRouter(
    prefix='/roles',
    tags=['Admin', 'Roles']
)


# ----Permissions----

@role_permiss_router.post("/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    admin: AdminDep,
    session: SessionDep):
    
    # Проверяем существование
    result = await session.execute(select(Role).where(Role.id == role_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Role not found")
    
    result = await session.execute(select(Permission).where(Permission.id == permission_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Проверяем, не назначено ли уже
    existing = await session.execute(
        select(RolePermission)
        .where(RolePermission.role_id == role_id)
        .where(RolePermission.permission_id == permission_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already has this permission")
    
    session.add(RolePermission(role_id=role_id, permission_id=permission_id))
    await session.commit()
    
    return {"message": "Permission assigned to role"}


@role_permiss_router.delete("/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    token: str,
    admin: AdminDep,
    session: SessionDep
):
    """Снять разрешение с роли (только admin)"""
    
    # Находим связь
    result = await session.execute(
        select(RolePermission)
        .where(RolePermission.role_id == role_id)
        .where(RolePermission.permission_id == permission_id)
    )
    rp = result.scalar_one_or_none()
    if not rp:
        raise HTTPException(status_code=404, detail="Role does not have this permission")
    
    await session.delete(rp)
    await session.commit()
    
    return {"message": "Permission removed from role"}


