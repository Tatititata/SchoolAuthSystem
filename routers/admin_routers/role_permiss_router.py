
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import Permission, Class, Subject, TeacherSubject
from models import User, Role, RolePermission, TeacherClassSubject, ClassSubject, UserRole
from app import auth
from .role_router import roles_router
from .user_role_router import user_role_router

role_permiss_router = APIRouter(
    prefix='/roles',
    tags=['Admin', 'Roles']
)


# ----Permissions----

@role_permiss_router.post("/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    token: str,
    session: SessionDep
):
    """Назначить разрешение роли (только admin)"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверка admin
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles))
    )
    current_user = result.scalar_one_or_none()
    
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    
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
    session: SessionDep
):
    """Снять разрешение с роли (только admin)"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверка admin
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles))
    )
    current_user = result.scalar_one_or_none()
    
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    
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


