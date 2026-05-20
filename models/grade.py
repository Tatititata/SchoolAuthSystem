from sqlalchemy import func
from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from datetime import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from user import User
    from class_subject import ClassSubject


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_subject_id: Mapped[int] = mapped_column(ForeignKey("class_subjects.id", ondelete="CASCADE"), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # 2,3,4,5
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    # Мягкое удаление
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    comment: Mapped[str] 

    student: Mapped["User"] = relationship("User", back_populates="grades_as_student", foreign_keys=[student_id])
    teacher: Mapped["User"] = relationship("User", back_populates="grades_as_teacher", foreign_keys=[teacher_id])
    deleted_by_user: Mapped["User | None"] = relationship("User", back_populates="grades_deleted_by", foreign_keys=[deleted_by])
    class_subject: Mapped["ClassSubject"] = relationship("ClassSubject", back_populates="grades")