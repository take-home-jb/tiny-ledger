import pytest
from sqlalchemy.orm import Session

from app.db import TransactionKind
from app.queries import get_balance_minor, insert_transaction, list_transactions


class TestGetBalanceMinor:
    def test_empty(self, session: Session) -> None:
        assert get_balance_minor(session) == 0

    def test_deposits_only(self, session: Session) -> None:
        insert_transaction(session, TransactionKind.DEPOSIT, 1000)
        insert_transaction(session, TransactionKind.DEPOSIT, 2500)
        assert get_balance_minor(session) == 3500

    def test_with_withdrawals(self, session: Session) -> None:
        insert_transaction(session, TransactionKind.DEPOSIT, 10000)
        insert_transaction(session, TransactionKind.WITHDRAWAL, 3000)
        insert_transaction(session, TransactionKind.DEPOSIT, 500)
        assert get_balance_minor(session) == 7500


class TestInsertTransaction:
    @pytest.mark.parametrize("kind", list(TransactionKind), ids=lambda k: k.name)
    def test_populates_id_and_created_at(
        self, session: Session, kind: TransactionKind
    ) -> None:
        transaction = insert_transaction(session, kind, 100)
        assert transaction.id is not None
        assert transaction.created_at is not None

    @pytest.mark.parametrize("kind", list(TransactionKind), ids=lambda k: k.name)
    def test_round_trips_kind_and_amount(
        self, session: Session, kind: TransactionKind
    ) -> None:
        transaction = insert_transaction(session, kind, 4242)
        assert transaction.kind == kind
        assert transaction.amount_minor == 4242


class TestListTransactions:
    def test_empty(self, session: Session) -> None:
        assert list_transactions(session) == []

    def test_orders_newest_first(self, session: Session) -> None:
        a = insert_transaction(session, TransactionKind.DEPOSIT, 100)
        b = insert_transaction(session, TransactionKind.DEPOSIT, 200)
        c = insert_transaction(session, TransactionKind.DEPOSIT, 300)
        rows = list_transactions(session)
        assert [r.id for r in rows] == [c.id, b.id, a.id]
