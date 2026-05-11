from collections.abc import Generator
from datetime import datetime
from enum import StrEnum

from fastapi import Request
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool


class TransactionKind(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[TransactionKind] = mapped_column(
        SAEnum(TransactionKind, name="transaction_kind"),
        nullable=False,
    )
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )


def make_engine() -> Engine:
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def get_session(request: Request) -> Generator[Session, None, None]:
    """Yield a Session wrapped in one transaction per request.

    The `with session.begin()` block commits when the route returns normally
    and rolls back on any raised exception (including HTTPException for
    insufficient-funds withdrawals). Query functions never need to commit.
    """
    session_local = request.app.state.session_local
    session = session_local()
    try:
        with session.begin():
            yield session
    finally:
        session.close()
