from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from subject import Subject
    from user import User

class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    teacher: Mapped["User"] = relationship("User", back_populates="teacher_subjects", foreign_keys=[teacher_id])
    subject: Mapped["Subject"] = relationship("Subject", back_populates="teacher_subjects")