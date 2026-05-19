
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.database import SessionDep
from models import User, TeacherClassSubject, ClassSubject, Role, Grade, ParentStudent
from app import auth


grades_router = APIRouter(
    prefix='/grades',
    tags=['Grades']
)


# 1. Журнал оценок (grades)
@grades_router.get("")
async def get_grades(token: str, session: SessionDep, student_id: int | None = None):
    """Получить оценки. 
    - Ученик: только свои
    - Родитель: только своего ребёнка
    - Учитель: все оценки по своим предметам
    - Директор: все оценки
    """
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
    
    # Определяем права пользователя
    user_roles = [role.name for role in current_user.roles]
    
    # Директор - видит всё
    if "director" in user_roles or "admin" in user_roles:
        result = await session.execute(
            select(Grade)
            .where(Grade.deleted_at.is_(None))
            .options(selectinload(Grade.student), 
                     selectinload(Grade.class_subject).selectinload(ClassSubject.subject))
        )
        return result.scalars().all()
    
    # Учитель - только оценки по своим предметам
    if "teacher" in user_roles:
        result = await session.execute(
            select(TeacherClassSubject)
            .where(TeacherClassSubject.teacher_id == user_id)
        )
        teacher_class_subjects = result.scalars().all()
        class_subject_ids = [tcs.class_subject_id for tcs in teacher_class_subjects]
        
        result = await session.execute(
            select(Grade)
            .where(Grade.class_subject_id.in_(class_subject_ids))
            .where(Grade.deleted_at.is_(None))
        )
        return result.scalars().all()
    
    # Родитель - оценки своих детей
    if "parent" in user_roles:
        result = await session.execute(
            select(ParentStudent)
            .where(ParentStudent.parent_id == user_id)
        )
        children = result.scalars().all()
        child_ids = [child.student_id for child in children]
        
        if student_id and student_id not in child_ids:
            raise HTTPException(status_code=403, detail="You don't have access to this student's grades")
        
        target_ids = child_ids if not student_id else [student_id]
        
        result = await session.execute(
            select(Grade)
            .where(Grade.student_id.in_(target_ids))
            .where(Grade.deleted_at.is_(None))
        )
        return result.scalars().all()
    
    # Ученик - только свои оценки
    if "student" in user_roles:
        result = await session.execute(
            select(Grade)
            .where(Grade.student_id == user_id)
            .where(Grade.deleted_at.is_(None))
        )
        return result.scalars().all()
    
    raise HTTPException(status_code=403, detail="Access denied")


@grades_router.post("")
async def create_grade(
    token: str,
    student_id: int,
    class_subject_id: int,
    grade: int,
    comment: str,
    session: SessionDep
    
):
    """Поставить оценку. Только учитель по своему предмету"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверяем, что пользователь - учитель
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles))
    )
    teacher = result.scalar_one_or_none()
    
    if not teacher or not any(r.name == "teacher" for r in teacher.roles):
        raise HTTPException(status_code=403, detail="Only teachers can create grades")
    
    # Проверяем, что учитель ведёт этот предмет в этом классе
    result = await session.execute(
        select(TeacherClassSubject)
        .where(TeacherClassSubject.teacher_id == user_id)
        .where(TeacherClassSubject.class_subject_id == class_subject_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You don't teach this subject in this class")
    
    # Проверяем, что студент существует и учится в нужном классе
    result = await session.execute(
        select(ClassSubject)
        .where(ClassSubject.id == class_subject_id)
    )
    class_subject = result.scalar_one_or_none()
    if not class_subject:
        raise HTTPException(status_code=404, detail="Class-subject not found")
    
    result = await session.execute(
        select(User)
        .where(User.id == student_id)
        .where(User.class_id == class_subject.class_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in this class")
    
    # Ставим оценку
    new_grade = Grade(
        student_id=student_id,
        class_subject_id=class_subject_id,
        grade=grade,
        teacher_id=user_id,
        comment = comment
    )
    session.add(new_grade)
    await session.commit()
    
    return {"message": "Grade created", "grade_id": new_grade.id}


@grades_router.delete("/{grade_id}")
async def delete_grade(
    grade_id: int,
    token: str,
    comment: str,
    session: SessionDep
):
    """Мягкое удаление оценки. Только учитель по своему предмету"""
    user_id = auth.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Находим оценку
    result = await session.execute(
        select(Grade)
        .where(Grade.id == grade_id)
        .where(Grade.deleted_at.is_(None))
    )
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    # Проверяем, что пользователь - учитель, который ведёт этот предмет
    result = await session.execute(
        select(TeacherClassSubject)
        .where(TeacherClassSubject.teacher_id == user_id)
        .where(TeacherClassSubject.class_subject_id == grade.class_subject_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You cannot delete this grade")
    
    # Мягкое удаление
    grade.deleted_at = datetime.utcnow()
    grade.deleted_by = user_id
    grade.comment = comment
    
    await session.commit()
    
    return {"message": "Grade deleted"}
