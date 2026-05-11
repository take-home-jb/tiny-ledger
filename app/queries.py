from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db import Transaction, TransactionKind


def get_balance_minor(session: Session) -> int:
    stmt = select(
        func.coalesce(
            func.sum(
                case(
                    (Transaction.kind == TransactionKind.DEPOSIT, Transaction.amount_minor),
                    else_=-Transaction.amount_minor,
                )
            ),
            0,
        )
    )
    return session.execute(stmt).scalar_one()


def list_transactions(session: Session) -> list[Transaction]:
    stmt = select(Transaction).order_by(
        Transaction.created_at.desc(), Transaction.id.desc()
    )
    return list(session.execute(stmt).scalars().all())


def insert_transaction(
    session: Session, kind: TransactionKind, amount_minor: int
) -> Transaction:
    transaction = Transaction(kind=kind, amount_minor=amount_minor)
    session.add(transaction)
    session.flush()
    return transaction
