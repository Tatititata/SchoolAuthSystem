from sqlalchemy import func
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from datetime import datetime


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from role import Role
    from klass import Class
    from grade import Grade
    from teacher_class_subject import TeacherClassSubject
    from token_blacklist import TokenBlacklist
    from teacher_subject import TeacherSubject
    from parent_student import ParentStudent


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)

    # Связи
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )
    blacklisted_tokens: Mapped[list["TokenBlacklist"]] = relationship(
        "TokenBlacklist", back_populates="user"
    )
    # Учительские связи
    teacher_subjects: Mapped[list["TeacherSubject"]] = relationship(
        "TeacherSubject", back_populates="teacher", foreign_keys="TeacherSubject.teacher_id"
    )
    teacher_classes: Mapped[list["TeacherClassSubject"]] = relationship(
        "TeacherClassSubject", back_populates="teacher"
    )
    # Оценки
    grades_as_student: Mapped[list["Grade"]] = relationship(
        "Grade", back_populates="student", foreign_keys="Grade.student_id"
    )
    grades_as_teacher: Mapped[list["Grade"]] = relationship(
        "Grade", back_populates="teacher", foreign_keys="Grade.teacher_id"
    )
    grades_deleted_by: Mapped[list["Grade"]] = relationship(
        "Grade", back_populates="deleted_by_user", foreign_keys="Grade.deleted_by"
    )
    # Родительские связи
    children: Mapped[list["ParentStudent"]] = relationship(
        "ParentStudent", back_populates="parent", foreign_keys="ParentStudent.parent_id"
    )
    # Класс ученика
    class_info: Mapped["Class"] = relationship("Class", back_populates="students", foreign_keys=[class_id])