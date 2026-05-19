from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from user import User



class ParentStudent(Base):
    __tablename__ = "parent_student"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    parent: Mapped["User"] = relationship("User", back_populates="children", foreign_keys=[parent_id])
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])

