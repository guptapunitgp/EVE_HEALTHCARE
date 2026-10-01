from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class CentreTest(Base):
    __tablename__ = "centre_tests"

    __table_args__ = (
        UniqueConstraint(
            "centre_id",
            "test_id",
            name="uq_centre_test",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    centre_id: Mapped[UUID] = mapped_column(
        ForeignKey("diagnostic_centres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    test_id: Mapped[UUID] = mapped_column(
        ForeignKey("diagnostic_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )