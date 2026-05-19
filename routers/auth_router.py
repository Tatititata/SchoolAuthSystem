
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.database import SessionDep
from models import User, Role, UserRole
from app import auth, schemas
from datetime import datetime

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autentication"]
)

@auth_router.post("/register", response_model=schemas.UserOut)
async def register(user_data: schemas.UserCreate, session: SessionDep):

    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    result = await session.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = auth.hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed,
        full_name=user_data.full_name,
        is_active=True
    )
    session.add(new_user)
    await session.flush()
    
    result = await session.execute(select(Role).where(Role.name == "student"))
    student_role = result.scalar_one()
    session.add(UserRole(user_id=new_user.id, role_id=student_role.id))
    
    await session.commit()
    await session.refresh(new_user)
    return new_user


@auth_router.post("/login")
async def login(login_data: schemas.LoginRequest, session: SessionDep):
    result = await session.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    token = auth.create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/logout")
async def logout(token: str, session: SessionDep):
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth.revoke_token(token)
    return {"message": "Successfully logged out"}


@auth_router.get("/me", response_model=schemas.UserOut)
async def get_me(token: str, session: SessionDep):
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@auth_router.patch("/me", response_model=schemas.UserOut)
async def update_me(
    token: str,
    update_data: schemas.UserUpdate,
    session: SessionDep
):
    """Обновить свой профиль"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Обновляем только переданные поля
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.email is not None:
        # Проверяем, не занят ли новый email
        existing = await session.execute(
            select(User).where(User.email == update_data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = update_data.email
    if update_data.password is not None:
        user.password_hash = auth.hash_password(update_data.password)
    
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return user

@auth_router.delete("/me")
async def delete_me(
    token: str,
    session: SessionDep
):
    """Мягкое удаление аккаунта (is_active=False)"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account already deactivated")
    
    # Мягкое удаление
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    
    # Отзываем токен (логаут)
    auth.revoke_token(token)
    
    return {"message": "Account deactivated successfully"}