
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import SessionDep
from models import Permission, Class, Subject, TeacherSubject
from models import User, Role, RolePermission, TeacherClassSubject, ClassSubject, UserRole
from app import auth


admin_router = APIRouter(
    prefix='/admin',
    tags=['Admin']
)

# ----Roles----

@admin_router.post("/roles")
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


@admin_router.get("/roles")
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


@admin_router.delete("/roles/{role_id}")
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


# ----Roles + Users----

@admin_router.post("/users/{user_id}/roles/{role_id}")
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


@admin_router.delete("/users/{user_id}/roles/{role_id}")
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


@admin_router.get("/users/{user_id}/roles")
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


@admin_router.post("/roles/{role_id}/permissions/{permission_id}")
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


@admin_router.delete("/roles/{role_id}/permissions/{permission_id}")
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