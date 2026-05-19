
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import User, Role
from app import auth


roles_router = APIRouter(
    prefix='/roles',
    tags=['Admin', 'Roles']
)

# ----Roles----

@roles_router.post("")
async def create_role(
    token: str,
    name: str,
    session: SessionDep,
    description: str | None = None
):
    """Создать новую роль (только admin)"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверяем, что пользователь admin
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
    token: str,
    session: SessionDep
):
    """Список всех ролей (только admin)"""
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
    
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]


@roles_router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    token: str,
    session: SessionDep
):
    """Удалить роль (только admin)"""
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