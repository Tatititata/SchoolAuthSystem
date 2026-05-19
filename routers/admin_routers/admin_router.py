
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import Permission, Class, Subject, TeacherSubject
from models import User, TeacherClassSubject, ClassSubject
from app import auth
from .role_router import roles_router
from .user_role_router import user_role_router
from .role_permiss_router import role_permiss_router
from .teach_class_subj_router import teach_class_subj_router

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
    token: str,
    resource_type: str,
    action: str,
    session: SessionDep
):
    """Создать новое разрешение (только admin)"""
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


@admin_router.post("/teacher-class-subject")
async def assign_teacher_to_class_subject(
    teacher_id: int,
    class_subject_id: int,
    session: SessionDep
):
    """Назначить учителя на конкретный предмет в конкретном классе"""
    
    # Проверяем, существует ли учитель
    teacher = await session.get(User, teacher_id)
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    
    # Проверяем, существует ли class_subject
    class_subject = await session.get(ClassSubject, class_subject_id)
    if not class_subject:
        raise HTTPException(404, "Class-subject relationship not found")
    
    # Проверяем, не назначен ли уже
    existing = await session.execute(
        select(TeacherClassSubject).where(
            TeacherClassSubject.teacher_id == teacher_id,
            TeacherClassSubject.class_subject_id == class_subject_id
        )
    )
    if existing.first():
        raise HTTPException(400, "Teacher already assigned to this class-subject")
    
    # Назначаем
    assignment = TeacherClassSubject(
        teacher_id=teacher_id,
        class_subject_id=class_subject_id
    )
    session.add(assignment)
    await session.commit()
    
    return {"message": "Teacher assigned successfully"}


@admin_router.delete("/teacher-class-subject")
async def remove_teacher_from_class_subject(
    teacher_id: int,
    class_subject_id: int,
    session: SessionDep
):
    """Снять учителя с предмета в классе"""
    
    result = await session.execute(
        select(TeacherClassSubject).where(
            TeacherClassSubject.teacher_id == teacher_id,
            TeacherClassSubject.class_subject_id == class_subject_id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    await session.delete(assignment)
    await session.commit()
    
    return {"message": "Teacher removed successfully"}

@admin_router.get("/teacher-class-subject")
async def get_all_assignments(session: SessionDep):
    """Получить список всех назначений учителей"""
    
    result = await session.execute(
        select(
            TeacherClassSubject.id,
            User.email.label("teacher_email"),
            User.full_name.label("teacher_name"),
            Class.name.label("class_name"),
            Subject.name.label("subject_name")
        )
        .join(User, TeacherClassSubject.teacher_id == User.id)
        .join(ClassSubject, TeacherClassSubject.class_subject_id == ClassSubject.id)
        .join(Class, ClassSubject.class_id == Class.id)
        .join(Subject, ClassSubject.subject_id == Subject.id)
    )
    assignments = result.all()
    
    return [
        {
            "id": a.id,
            "teacher_email": a.teacher_email,
            "teacher_name": a.teacher_name,
            "class_name": a.class_name,
            "subject_name": a.subject_name
        }
        for a in assignments
    ]


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
    session: SessionDep
):
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


@admin_router.post("/teacher-subject")
async def assign_teacher_subject(
    teacher_id: int,
    subject_id: int,
    session: SessionDep
):
    """Назначить учителю компетенцию (какой предмет он может вести)"""
    
    existing = await session.execute(
        select(TeacherSubject).where(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.subject_id == subject_id
        )
    )
    if existing.first():
        raise HTTPException(400, "Teacher already has this subject competency")
    
    ts = TeacherSubject(teacher_id=teacher_id, subject_id=subject_id)
    session.add(ts)
    await session.commit()
    
    return {"message": "Subject competency assigned"}