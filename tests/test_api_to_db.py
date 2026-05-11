import pytest
from pydantic import ValidationError

from app.schemas import DepositRequest, WithdrawRequest


class TestDepositRequest:
    def test_happy_path(self) -> None:
        req = DepositRequest.model_validate_json('{"amount": "100.50"}')
        assert req.amount == 10050

    def test_small_amount(self) -> None:
        req = DepositRequest.model_validate_json('{"amount": "0.01"}')
        assert req.amount == 1

    def test_no_decimals(self) -> None:
        req = DepositRequest.model_validate_json('{"amount": "42"}')
        assert req.amount == 4200

    @pytest.mark.parametrize(
        "body",
        [
            '{"amount": "0"}',
            '{"amount": "-1"}',
            '{"amount": "0.005"}',
            '{"amount": "abc"}',
            '{"amount": 0.10}',
            '{"amount": 100}',
            '{"amount": null}',
            "{}",
        ],
    )
    def test_rejections(self, body: str) -> None:
        with pytest.raises(ValidationError):
            DepositRequest.model_validate_json(body)


class TestWithdrawRequest:
    def test_happy_path(self) -> None:
        req = WithdrawRequest.model_validate_json('{"amount": "30.00"}')
        assert req.amount == 3000

    def test_small_amount(self) -> None:
        req = WithdrawRequest.model_validate_json('{"amount": "0.01"}')
        assert req.amount == 1

    def test_no_decimals(self) -> None:
        req = WithdrawRequest.model_validate_json('{"amount": "42"}')
        assert req.amount == 4200

    @pytest.mark.parametrize(
            "body",
        [
            '{"amount": "0"}',
            '{"amount": "-1"}',
            '{"amount": "0.005"}',
            '{"amount": "abc"}',
            '{"amount": 0.10}',
            '{"amount": 100}',
            '{"amount": null}',
            "{}",
        ],
    )
    def test_rejection(self, body: str) -> None:
        with pytest.raises(ValidationError):
            WithdrawRequest.model_validate_json(body)
