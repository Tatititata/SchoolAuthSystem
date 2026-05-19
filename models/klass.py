from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from user import User
    from class_subject import ClassSubject
    from schedule import Schedule


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 5А, 9Б
    year: Mapped[int] = mapped_column(Integer, nullable=False)     # 2025

    students: Mapped[list["User"]] = relationship("User", back_populates="class_info")
    class_subjects: Mapped[list["ClassSubject"]] = relationship("ClassSubject", back_populates="class_info")
    schedule_entries: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="class_info")