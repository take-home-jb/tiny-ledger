import json
from datetime import datetime

import pytest

from app.db import Transaction, TransactionKind
from app.schemas import TransactionOut


def _make_transaction(
    *,
    id: int = 1,
    kind: TransactionKind = TransactionKind.DEPOSIT,
    amount_minor: int = 10050,
    created_at: datetime = datetime(2026, 5, 9, 12, 34, 56),
) -> Transaction:
    return Transaction(
        id=id, kind=kind, amount_minor=amount_minor, created_at=created_at
    )


class TestTransactionOut:
    def test_dump_shape(self) -> None:
        out = TransactionOut.model_validate(_make_transaction())
        dumped = out.model_dump(mode="json")
        assert dumped["id"] == 1
        assert dumped["kind"] == "deposit"
        assert dumped["amount"] == "100.50"
        assert dumped["created_at"].startswith("2026-05-09T12:34:56")
        assert "amount_minor" not in dumped

    def test_json_excludes_amount_minor(self) -> None:
        out = TransactionOut.model_validate(
            _make_transaction(id=2, kind=TransactionKind.WITHDRAWAL, amount_minor=50)
        )
        parsed = json.loads(out.model_dump_json())
        assert parsed["amount"] == "0.50"
        assert parsed["kind"] == "withdrawal"
        assert "amount_minor" not in parsed

    def test_formats_zero_padded(self) -> None:
        out = TransactionOut.model_validate(_make_transaction(amount_minor=7))
        assert out.model_dump(mode="json")["amount"] == "0.07"


class TestKindEnumCompatibility:
    # If you add a member to TransactionKind (DB) without adding it to
    # TransactionKindOut (API), this test fails — Pydantic can't coerce the
    # new value into the API enum and TransactionOut.model_validate raises.
    # (The reverse direction — API gains a value DB lacks — is harmless dead
    # code on the wire, since the route never produces unknown DB kinds.)
    @pytest.mark.parametrize("db_kind", list(TransactionKind), ids=lambda k: k.name)
    def test_db_kind_serializes_to_matching_api_string(
        self, db_kind: TransactionKind
    ) -> None:
        out = TransactionOut.model_validate(_make_transaction(kind=db_kind))
        dumped = out.model_dump(mode="json")
        assert dumped["kind"] == db_kind.value
