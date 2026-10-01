from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CentreStaff(Base):
    __tablename__ = "centre_staff"
    __table_args__ = (UniqueConstraint("centre_id", "user_id", name="uq_centre_staff"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    centre_id: Mapped[UUID] = mapped_column(ForeignKey("diagnostic_centres.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
