
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import User, Role, UserRole
from app import auth
from .dependences import AdminDep


user_role_router = APIRouter(
    prefix='/users',
    tags=['Admin', 'Users', "Roles"]
)

# ----Roles + Users----

@user_role_router.post("/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    admin: AdminDep,
    session: SessionDep
    
):
    """Назначить роль пользователю (только admin)"""

    
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
    admin: AdminDep,
    session: SessionDep
):
    """Снять роль с пользователя (только admin)"""
    
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
    admin: AdminDep,
    session: SessionDep
):
    """Получить роли пользователя (только admin)"""
    
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return [{"id": r.id, "name": r.name, "description": r.description} for r in user.roles]