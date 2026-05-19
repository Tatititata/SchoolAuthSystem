
from sqlalchemy import ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from subject import Subject
    from klass import Class
    from grade import Grade
    from teacher_class_subject import TeacherClassSubject


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    class_info: Mapped["Class"] = relationship("Class", back_populates="class_subjects")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="class_subjects")
    teacher_assignments: Mapped[list["TeacherClassSubject"]] = relationship("TeacherClassSubject", 
                                                                            back_populates="class_subject")
    grades: Mapped[list["Grade"]] = relationship("Grade", back_populates="class_subject")