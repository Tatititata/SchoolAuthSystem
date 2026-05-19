from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from class_subject import ClassSubject
    from user import User

class TeacherClassSubject(Base):
    __tablename__ = "teacher_class_subject"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_subject_id: Mapped[int] = mapped_column(ForeignKey("class_subjects.id", ondelete="CASCADE"), nullable=False)

    teacher: Mapped["User"] = relationship("User", back_populates="teacher_classes")
    class_subject: Mapped["ClassSubject"] = relationship("ClassSubject", back_populates="teacher_assignments")