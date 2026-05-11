import pytest

from app.schemas import format_minor, parse_money_str


class TestParseMoneyStr:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("100.50", 10050),
            ("0.5", 50),
            ("0.50", 50),
            ("7", 700),
            ("0.01", 1),
            ("999999.99", 99999999),
        ],
    )
    def test_happy_path(self, raw: str, expected: int) -> None:
        assert parse_money_str(raw) == expected

    @pytest.mark.parametrize(
        "bad",
        [
            "0",
            "0.00",
            "-1",
            "0.005",
            "1e2",
            " 10",
            "10 ",
            "",
            "abc",
            "10.",
            ".5",
            "1,000",
            "007.50",
            "01",
        ],
    )
    def test_string_rejections(self, bad: str) -> None:
        with pytest.raises(ValueError):
            parse_money_str(bad)

    @pytest.mark.parametrize("bad", [10, 10.5, None, True, [], {}])
    def test_non_string_rejections(self, bad: object) -> None:
        with pytest.raises(ValueError):
            parse_money_str(bad)


class TestFormatMinor:
    @pytest.mark.parametrize(
        ("minor", "expected"),
        [
            (10050, "100.50"),
            (7, "0.07"),
            (0, "0.00"),
            (100, "1.00"),
            (99999999, "999999.99"),
        ],
    )
    def test_happy_path(self, minor: int, expected: str) -> None:
        assert format_minor(minor) == expected

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            format_minor(-1)
