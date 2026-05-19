
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import Permission, Class, Subject, TeacherSubject
from models import User, Role, RolePermission, TeacherClassSubject, ClassSubject, UserRole
from app import auth
from .role_router import roles_router

user_role_router = APIRouter(
    prefix='/users',
    tags=['Admin', 'Users']
)

# ----Roles + Users----

@user_role_router.post("/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    token: str,
    session: SessionDep
):
    """Назначить роль пользователю (только admin)"""
    admin_id = auth.verify_token(token)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверка admin
    result = await session.execute(
        select(User)
        .where(User.id == admin_id)
        .options(selectinload(User.roles))
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user or not admin_user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not any(role.name == "admin" for role in admin_user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Проверяем, существует ли пользователь
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем, существует ли роль
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Проверяем, не назначена ли уже роль
    result = await session.execute(
        select(UserRole)
        .where(UserRole.user_id == user_id)
        .where(UserRole.role_id == role_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has this role")
    
    session.add(UserRole(user_id=user_id, role_id=role_id))
    await session.commit()
    
    return {"message": f"Role '{role.name}' assigned to user {user.email}"}


@user_role_router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    token: str,
    session: SessionDep
):
    """Снять роль с пользователя (только admin)"""
    admin_id = auth.verify_token(token)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверка admin
    result = await session.execute(
        select(User)
        .where(User.id == admin_id)
        .options(selectinload(User.roles))
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user or not admin_user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not any(role.name == "admin" for role in admin_user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Находим связь
    result = await session.execute(
        select(UserRole)
        .where(UserRole.user_id == user_id)
        .where(UserRole.role_id == role_id)
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        raise HTTPException(status_code=404, detail="User does not have this role")
    
    await session.delete(user_role)
    await session.commit()
    
    return {"message": "Role removed from user"}


@user_role_router.get("/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    token: str,
    session: SessionDep
):
    """Получить роли пользователя (только admin)"""
    admin_id = auth.verify_token(token)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверка admin
    result = await session.execute(
        select(User)
        .where(User.id == admin_id)
        .options(selectinload(User.roles))
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user or not admin_user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not any(role.name == "admin" for role in admin_user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return [{"id": r.id, "name": r.name, "description": r.description} for r in user.roles]