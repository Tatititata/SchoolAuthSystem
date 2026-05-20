
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import Permission, Class, Subject
from models import User, TeacherClassSubject, ClassSubject
from app import auth
from .role_router import roles_router
from .user_role_router import user_role_router
from .role_permiss_router import role_permiss_router
from .teach_class_subj_router import teach_class_subj_router
from .dependences import AdminDep

admin_router = APIRouter(
    prefix='/admin',
    tags=['Admin']
)

admin_router.include_router(roles_router)
admin_router.include_router(user_role_router)
admin_router.include_router(role_permiss_router)
admin_router.include_router(teach_class_subj_router)

# ----Permissions----

@admin_router.post("/permissions")
async def create_permission(
    resource_type: str,
    action: str,
    session: SessionDep,
    admin: AdminDep
):
    # """Создать новое разрешение (только admin)"""
    
    # Проверяем, не существует ли уже
    existing = await session.execute(
        select(Permission)
        .where(Permission.resource_type == resource_type)
        .where(Permission.action == action)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Permission already exists")
    
    new_perm = Permission(resource_type=resource_type, action=action)
    session.add(new_perm)
    await session.commit()
    await session.refresh(new_perm)
    
    return {"id": new_perm.id, "resource_type": resource_type, "action": action}



@admin_router.get("/class-subjects")
async def get_class_subjects(session: SessionDep):
    """Получить все связки классов и предметов"""
    
    result = await session.execute(
        select(ClassSubject.id, Class.name.label("class_name"), Subject.name.label("subject_name"))
        .join(Class, ClassSubject.class_id == Class.id)
        .join(Subject, ClassSubject.subject_id == Subject.id)
    )
    items = result.all()
    
    return [
        {"id": item.id, "class_name": item.class_name, "subject_name": item.subject_name}
        for item in items
    ]


@admin_router.patch("/users/{user_id}/class")
async def set_student_class(
    user_id: int,
    class_id: int,
    session: SessionDep,
    admin: AdminDep):
    """Установить класс ученику"""
    
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    # Проверяем, существует ли класс
    class_obj = await session.get(Class, class_id)
    if not class_obj:
        raise HTTPException(404, "Class not found")
    
    user.class_id = class_id
    await session.commit()
    
    return {"message": f"Class set to {class_obj.name}"}

