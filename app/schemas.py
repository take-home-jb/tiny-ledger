import re
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field

_AMOUNT_RE = re.compile(r"^(0|[1-9]\d*)(\.\d{1,2})?$")


class TransactionKindOut(StrEnum):
    """API-layer transaction kind. Kept distinct from the DB-layer
    TransactionKind so the wire contract isn't accidentally coupled to
    storage. The two enums must stay in sync — divergence tests in
    tests/test_db_to_api.py guard against drift.
    """

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


def parse_money_str(v: object) -> int:
    """Parse an inbound amount string into integer cents.

    Rejects 0 — an empty transaction is a no-op and would clutter history.
    """
    if not isinstance(v, str):
        raise ValueError('amount must be a string in major units, e.g. "100.50"')
    if not _AMOUNT_RE.match(v):
        raise ValueError(f"amount must match {_AMOUNT_RE.pattern}")
    d = Decimal(v)
    if d <= 0:
        raise ValueError("amount must be > 0")
    return int(d * 100)


def format_minor(minor: int) -> str:
    """Format a non-negative ledger value (cents) as a major-unit string.

    0 is allowed — the balance is legitimately 0 on an empty ledger.
    Negatives are rejected: balances can't go negative (overdraft is
    rejected) and individual transaction amounts are always positive.
    """
    if minor < 0:
        raise ValueError("format_minor expects non-negative input")
    return f"{minor // 100}.{minor % 100:02d}"


MoneyMinor = Annotated[int, BeforeValidator(parse_money_str)]


class DepositRequest(BaseModel):
    amount: MoneyMinor


class WithdrawRequest(BaseModel):
    amount: MoneyMinor


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: TransactionKindOut
    amount_minor: int = Field(exclude=True)
    created_at: datetime

    @computed_field
    @property
    def amount(self) -> str:
        return format_minor(self.amount_minor)


class BalanceOut(BaseModel):
    balance: str
