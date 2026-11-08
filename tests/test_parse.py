from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 11, 8)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("today", date(2025, 11, 8)),
        ("tomorrow", date(2025, 11, 9)),
        ("yesterday", date(2025, 11, 7)),
        ("next tuesday", date(2025, 11, 11)),
        ("last friday", date(2025, 11, 7)),
        ("in 3 days", date(2025, 11, 11)),
        ("3 days ago", date(2025, 11, 5)),
        ("2 weeks from now", date(2025, 11, 22)),
    ],
)
def test_relative_to_today(text: str, expected: date) -> None:
    assert parse(text, TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("december 1st, 2025", date(2025, 12, 1)),
        ("December 1, 2025", date(2025, 12, 1)),
        ("1st december 2025", date(2025, 12, 1)),
        ("2025-12-01", date(2025, 12, 1)),
        ("12/01/2025", date(2025, 12, 1)),
        ("on december 1st, 2025", date(2025, 12, 1)),
    ],
)
def test_explicit_dates(text: str, expected: date) -> None:
    assert parse(text, TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("5 days before december 1st, 2025", date(2025, 11, 26)),
        ("five days before december 1st, 2025", date(2025, 11, 26)),
        ("3 weeks after january 10, 2025", date(2025, 1, 31)),
        ("1 day after december 31, 2025", date(2026, 1, 1)),
    ],
)
def test_relative_to_explicit_date(text: str, expected: date) -> None:
    assert parse(text, TODAY) == expected


def test_month_without_year_uses_next_occurrence() -> None:
    assert parse("december 1st", TODAY) == date(2025, 12, 1)
    assert parse("january 5", TODAY) == date(2026, 1, 5)


def test_next_weekday_is_always_in_the_future() -> None:
    tuesday = date(2025, 11, 11)
    assert parse("next tuesday", tuesday) == date(2025, 11, 18)


def test_parsing_is_case_insensitive() -> None:
    assert parse("Next Tuesday", TODAY) == date(2025, 11, 11)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not a date",
        "february 30, 2025",
        "december 1st, 20205",
    ],
)
def test_invalid_input_raises_value_error(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text, TODAY)
