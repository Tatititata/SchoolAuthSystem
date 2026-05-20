from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from class_subject import ClassSubject



class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    class_subjects: Mapped[list["ClassSubject"]] = relationship("ClassSubject", back_populates="subject")
  