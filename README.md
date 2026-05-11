# tiny-ledger

A tiny single-account ledger as a local FastAPI service. In-memory SQLite via SQLAlchemy. Records deposits and withdrawals; exposes current balance and transaction history. No persistence across restarts; no auth; no UI.

## Run

```bash
uv sync
uv run uvicorn app.main:app --reload
```

OpenAPI docs at <http://localhost:8000/docs>.

## Assumptions

These are the simplifying choices the implementation rests on. Each one is the reason something is *not* in the codebase.

- **Single account.** No `accounts` table, no path scoping like `/accounts/{id}/balance`. One global running balance.
- **Single currency.** Responses don't include a `currency` field — see [Money representation](#money-representation) below.
- **No auth.** Any caller can deposit or withdraw. Out of scope per the brief.
- **No persistence across restarts.** Backed by `sqlite:///:memory:` with `StaticPool` so all sessions share one connection. Process exit = data gone.
- **Single uvicorn worker.** A module-level `asyncio.Lock` serializes withdraws within the process; it's not shared across processes, so multi-worker deployment would break the overdraft check.
- **Withdrawals that would push the balance negative are rejected (`400`).** Not a logging-only ledger.
- **Two decimal places, integer cents.** Amounts beyond that precision (e.g. `"0.005"`) are rejected with `422`. Amounts cross the wire as decimal *strings* in major units (`"100.50"`); JSON numbers are rejected to avoid float-rounding ambiguity.
- **Newest-first transaction history.** Ordered by `created_at DESC, id DESC`; the `id`-DESC tiebreaker keeps ordering deterministic when timestamps collide.
- **`created_at` is a naive local-time datetime.** SQLite doesn't preserve `tzinfo` cleanly, and adding a `TypeDecorator` to fake it is overkill for a tiny dev ledger.
- **No pagination on `/transactions`.** Tiny dataset; would add `limit`/`offset` if it grew.
- **Storage is SQL via SQLAlchemy, not a Python `list`/`dict`.** The brief suggested a map/array; I picked SQLite to get real query semantics (`SUM`, `ORDER BY`, `WHERE`) without installing a DB server. A `list[dict]` would also have worked.

## Endpoints

| Method | Path             | Body                   | Returns                                |
|--------|------------------|------------------------|----------------------------------------|
| POST   | `/deposit`       | `{"amount": "100.50"}` | `201` → `Transaction`                  |
| POST   | `/withdraw`      | `{"amount": "30.00"}`  | `201` → `Transaction`; `400` if it would go negative |
| GET    | `/balance`       | —                      | `{"balance": "70.50"}`                 |
| GET    | `/transactions`  | —                      | `[Transaction, ...]`, newest first     |

## Money representation

The ledger assumes a **single, implicit currency** — responses do not include a `currency` field. There's nothing to disambiguate, and an unused field would invite clients to read meaning into it. If you ever need multi-currency, that's a different ledger.

Storage is in **integer minor units (cents)** — `SUM(INTEGER)` is exact, comparisons are unambiguous, and there's no risk of float-rounding drift.

The API exchanges **decimal-string amounts in major units** (e.g. `"100.50"`). Strings only — JSON numbers like `100.50` are rejected with `422`, since binary floats can't represent decimal cents exactly. The schema also rejects negative amounts, zero, scientific notation (`"1e2"`), surrounding whitespace, and more than two decimal places.

## Tests

```bash
uv run pytest -v
```

Tests are layered: pure helpers (`test_types.py`), request-schema validation (`test_api_to_db.py`), response-schema serialization (`test_db_to_api.py`), DB queries (`test_queries.py`), route wiring / status codes (`test_routes.py`), and end-to-end smoke (`test_e2e.py`).

## Quality gates

```bash
uv run pytest          # 82 tests
uv run ruff check .    # lint
uv run ty check .      # type check
```

## Example run

```bash
➜  curl -s -X POST http://localhost:8000/deposit -H 'content-type: application/json' -d '{"amount": "100.50"}' | jq
{
  "id": 1,
  "kind": "deposit",
  "created_at": "2026-05-11T08:14:13.255346",
  "amount": "100.50"
}
➜  curl -s -X POST http://localhost:8000/deposit -H 'content-type: application/json' -d '{"amount": "100.50"}' | jq
{
  "id": 2,
  "kind": "deposit",
  "created_at": "2026-05-11T08:14:18.321906",
  "amount": "100.50"
}
➜  curl -s -X POST http://localhost:8000/withdraw -H 'content-type: application/json' -d '{"amount": "100"}' | jq
{
  "id": 3,
  "kind": "withdrawal",
  "created_at": "2026-05-11T08:14:24.282275",
  "amount": "100.00"
}
➜  curl -s -X GET http://localhost:8000/balance -H 'content-type: application/json' | jq
{
  "balance": "101.00"
}
➜  curl -s -X GET http://localhost:8000/transactions -H 'content-type: application/json' | jq
[
  {
    "id": 3,
    "kind": "withdrawal",
    "created_at": "2026-05-11T08:14:24.282275",
    "amount": "100.00"
  },
  {
    "id": 2,
    "kind": "deposit",
    "created_at": "2026-05-11T08:14:18.321906",
    "amount": "100.50"
  },
  {
    "id": 1,
    "kind": "deposit",
    "created_at": "2026-05-11T08:14:13.255346",
    "amount": "100.50"
  }
]
```
