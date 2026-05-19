from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import User, Role
from app import auth, schemas


user_router = APIRouter(
    prefix='/users',
    tags=['Users']
)

# ============== ПОЛЬЗОВАТЕЛИ ==============

@user_router.get("", response_model=list[schemas.UserOut])
async def get_users(token: str, session: SessionDep):
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    current_user = result.scalar_one_or_none()
    
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    can_read_all = any(
        perm.resource_type == "user" and perm.action == "read_all"
        for role in current_user.roles
        for perm in role.permissions
    )
    
    if can_read_all:
        result = await session.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        return users
    else:
        return [current_user]