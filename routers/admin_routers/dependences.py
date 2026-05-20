from typing import Annotated
from fastapi import Depends, HTTPException
from app.database import SessionDep
from app import auth
from models import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_user(token: str, session: SessionDep) -> User:
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid token")
    
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    
    return user

UserDep = Annotated[User, Depends(get_user)]

async def get_current_admin(user: UserDep) -> User:
    if not any(role.name == "admin" for role in user.roles):
        raise HTTPException(403, "Admin access required")
    
    return user

async def get_director_or_admin(user: UserDep) -> User:
    if not any(role.name in ("admin", "director") for role in user.roles):
        raise HTTPException(403, "Admin or Director access required")
    
    return user

AdminDep = Annotated[User, Depends(get_current_admin)]
DirectorDep = Annotated[User, Depends(get_director_or_admin)]