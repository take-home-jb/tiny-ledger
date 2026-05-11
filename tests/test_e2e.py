from fastapi.testclient import TestClient


# End-to-end smoke tests. Unlike test_routes (which checks status codes only),
# these assert on response bodies — the goal is to catch wiring bugs that the
# layered tests would miss when each layer is correct in isolation but their
# composition isn't.
class TestEndToEnd:
    def test_deposit_then_balance(self, client: TestClient) -> None:
        client.post("/deposit", json={"amount": "50.00"})
        assert client.get("/balance").json() == {"balance": "50.00"}

    def test_full_deposit_withdraw_flow(self, client: TestClient) -> None:
        client.post("/deposit", json={"amount": "50.00"})
        client.post("/withdraw", json={"amount": "20.00"})

        assert client.get("/balance").json() == {"balance": "30.00"}

        transactions = client.get("/transactions").json()
        assert len(transactions) == 2
        # Newest first.
        assert transactions[0]["kind"] == "withdrawal"
        assert transactions[0]["amount"] == "20.00"
        assert transactions[1]["kind"] == "deposit"
        assert transactions[1]["amount"] == "50.00"

    def test_failed_withdraw_does_not_persist(self, client: TestClient) -> None:
        # Verifies the rollback path end-to-end through the wire: a 400 from
        # withdraw must leave neither the balance nor the history changed.
        client.post("/deposit", json={"amount": "10.00"})
        r = client.post("/withdraw", json={"amount": "999.00"})
        assert r.status_code == 400
        assert r.json() == {"detail": "Insufficient funds"}

        assert client.get("/balance").json() == {"balance": "10.00"}
        transactions = client.get("/transactions").json()
        assert len(transactions) == 1
        assert transactions[0]["kind"] == "deposit"
        assert transactions[0]["amount"] == "10.00"
