import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from app import queries
from app.db import Base, TransactionKind, get_session, make_engine
from app.schemas import (
    BalanceOut,
    DepositRequest,
    TransactionOut,
    WithdrawRequest,
    format_minor,
)

_withdraw_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine()
    Base.metadata.create_all(engine)
    app.state.engine = engine
    app.state.session_local = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Tiny Ledger", lifespan=lifespan)


# Route handlers don't annotate their returns — response_model= carries the
# wire contract and FastAPI converts via Pydantic (from_attributes=True for
# ORM-backed responses).


@app.post("/deposit", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def deposit(req: DepositRequest, session: Session = Depends(get_session)):
    return queries.insert_transaction(
        session, kind=TransactionKind.DEPOSIT, amount_minor=req.amount
    )


@app.post("/withdraw", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def withdraw(req: WithdrawRequest, session: Session = Depends(get_session)):
    async with _withdraw_lock:
        balance = queries.get_balance_minor(session)
        if balance - req.amount < 0:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        return queries.insert_transaction(
            session, kind=TransactionKind.WITHDRAWAL, amount_minor=req.amount
        )


@app.get("/balance", response_model=BalanceOut)
def balance(session: Session = Depends(get_session)):
    return BalanceOut(balance=format_minor(queries.get_balance_minor(session)))


@app.get("/transactions", response_model=list[TransactionOut])
def transactions(session: Session = Depends(get_session)):
    return queries.list_transactions(session)
