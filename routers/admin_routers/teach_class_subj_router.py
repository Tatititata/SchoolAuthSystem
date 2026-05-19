
from app.database import SessionDep
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.database import SessionDep
from models import Class, Subject, User, TeacherClassSubject, ClassSubject


teach_class_subj_router = APIRouter(
    prefix='/teacher-class-subject',
    tags=['Admin', 'Teacher', 'Class', 'Subject']
)

@teach_class_subj_router.post("")
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


@teach_class_subj_router.delete("")
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

@teach_class_subj_router.get("")
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