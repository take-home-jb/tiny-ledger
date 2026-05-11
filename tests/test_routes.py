from fastapi.testclient import TestClient


class TestDeposit:
    def test_valid_returns_201(self, client: TestClient) -> None:
        r = client.post("/deposit", json={"amount": "100.50"})
        assert r.status_code == 201

    def test_too_many_decimals_returns_422(self, client: TestClient) -> None:
        r = client.post("/deposit", json={"amount": "0.005"})
        assert r.status_code == 422

    def test_zero_returns_422(self, client: TestClient) -> None:
        r = client.post("/deposit", json={"amount": "0"})
        assert r.status_code == 422

    def test_missing_amount_returns_422(self, client: TestClient) -> None:
        r = client.post("/deposit", json={})
        assert r.status_code == 422

    def test_json_number_returns_422(self, client: TestClient) -> None:
        r = client.post("/deposit", json={"amount": 100.50})
        assert r.status_code == 422


class TestWithdraw:
    def test_sufficient_returns_201(self, client: TestClient) -> None:
        client.post("/deposit", json={"amount": "100.00"})
        r = client.post("/withdraw", json={"amount": "30.00"})
        assert r.status_code == 201

    def test_insufficient_returns_400(self, client: TestClient) -> None:
        client.post("/deposit", json={"amount": "10.00"})
        r = client.post("/withdraw", json={"amount": "999.00"})
        assert r.status_code == 400

    def test_exactly_balance_returns_201(self, client: TestClient) -> None:
        # Boundary: balance - amount == 0 must be allowed (check is `< 0`, not `<= 0`).
        client.post("/deposit", json={"amount": "100.00"})
        r = client.post("/withdraw", json={"amount": "100.00"})
        assert r.status_code == 201

    def test_one_cent_over_balance_returns_400(self, client: TestClient) -> None:
        # Boundary: 1 cent overshoot must reject.
        client.post("/deposit", json={"amount": "100.00"})
        r = client.post("/withdraw", json={"amount": "100.01"})
        assert r.status_code == 400


class TestBalance:
    def test_returns_200(self, client: TestClient) -> None:
        r = client.get("/balance")
        assert r.status_code == 200


class TestTransactions:
    def test_returns_200(self, client: TestClient) -> None:
        r = client.get("/transactions")
        assert r.status_code == 200
