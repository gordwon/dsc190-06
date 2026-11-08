from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_MONTH_ABBREVIATIONS = {
    "jan": "january",
    "feb": "february",
    "mar": "march",
    "apr": "april",
    "jun": "june",
    "jul": "july",
    "aug": "august",
    "sep": "september",
    "sept": "september",
    "oct": "october",
    "nov": "november",
    "dec": "december",
}

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_UNIT_ALIASES = {
    "day": "day",
    "days": "day",
    "week": "week",
    "weeks": "week",
    "month": "month",
    "months": "month",
    "year": "year",
    "years": "year",
    "hour": "hour",
    "hours": "hour",
    "minute": "minute",
    "minutes": "minute",
}


def _normalize_number_words(text: str) -> str:
    tokens = text.split()
    result: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        parts = token.split("-")
        if parts and all(part in _NUMBER_WORDS for part in parts):
            value = _NUMBER_WORDS[parts[0]]
            for part in parts[1:]:
                value += _NUMBER_WORDS[part]
            if (
                value % 10 == 0
                and i + 1 < len(tokens)
                and tokens[i + 1] in _NUMBER_WORDS
                and 0 < _NUMBER_WORDS[tokens[i + 1]] < 10
            ):
                value += _NUMBER_WORDS[tokens[i + 1]]
                i += 1
            result.append(str(value))
        else:
            result.append(token)
        i += 1
    return " ".join(result)


def _normalize(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    normalized = re.sub(r"(\d+)(?:st|nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"\b(?:a|an)\b", "1", normalized)
    normalized = _normalize_number_words(normalized)
    normalized = re.sub(r"^(?:on|the)\s+", "", normalized)
    return normalized


def _parse_duration(text: str) -> tuple[int, str]:
    match = re.fullmatch(r"(?:(\d+|an?)\s+)?([a-z]+)", text)
    if match is None:
        raise ValueError(f"invalid duration: {text!r}")
    amount_text, unit_text = match.groups()
    amount = 1 if amount_text is None or amount_text in ("a", "an") else int(amount_text)
    unit = _UNIT_ALIASES.get(unit_text)
    if unit is None:
        raise ValueError(f"invalid duration unit: {unit_text!r}")
    return amount, unit


def _parse_durations(text: str) -> list[tuple[int, str]]:
    parts = re.split(r"\s*(?:,|\band\b)\s*", text)
    return [_parse_duration(part) for part in parts if part]


def _add_months(value: date, months: int) -> date:
    total = value.year * 12 + (value.month - 1) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _add_years(value: date, years: int) -> date:
    year = value.year + years
    day = min(value.day, calendar.monthrange(year, value.month)[1])
    return date(year, value.month, day)


def _shift(value: date, amount: int, unit: str) -> date:
    if unit == "day":
        return value + timedelta(days=amount)
    if unit == "week":
        return value + timedelta(weeks=amount)
    if unit == "month":
        return _add_months(value, amount)
    if unit == "year":
        return _add_years(value, amount)
    if unit == "hour":
        return value + timedelta(hours=amount)
    if unit == "minute":
        return value + timedelta(minutes=amount)
    raise ValueError(f"invalid unit: {unit!r}")


def _resolve_year(month: int, day: int, year: int | None, today: date) -> date:
    if year is not None:
        return date(year, month, day)

    candidate = date(today.year, month, day)
    if candidate < today:
        candidate = date(today.year + 1, month, day)
    return candidate


def _parse_explicit(text: str, today: date) -> date:
    iso_match = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if iso_match is not None:
        year, month, day = (int(part) for part in iso_match.groups())
        return date(year, month, day)

    numeric_match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if numeric_match is not None:
        month, day, year = (int(part) for part in numeric_match.groups())
        return date(year, month, day)

    month_first = re.fullmatch(r"([a-z]+)\.?\s+(\d{1,2})(?:,?\s+(\d{4}))?", text)
    if month_first is not None:
        month_name, day_text, year_text = month_first.groups()
        month = _month_number(month_name)
        return _resolve_year(
            month,
            int(day_text),
            int(year_text) if year_text is not None else None,
            today,
        )

    day_first = re.fullmatch(
        r"(\d{1,2})\s+(?:of\s+)?([a-z]+)\.?(?:,?\s+(\d{4}))?", text
    )
    if day_first is not None:
        day_text, month_name, year_text = day_first.groups()
        month = _month_number(month_name)
        return _resolve_year(
            month,
            int(day_text),
            int(year_text) if year_text is not None else None,
            today,
        )

    raise ValueError(f"could not parse date: {text!r}")


def _month_number(name: str) -> int:
    name = _MONTH_ABBREVIATIONS.get(name, name)
    try:
        return _MONTHS[name]
    except KeyError:
        raise ValueError(f"invalid month: {name!r}") from None


def parse(text: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()
    if not isinstance(text, str):
        raise TypeError(f"expected a string, got {type(text).__name__}")

    normalized = _normalize(text)
    if not normalized:
        raise ValueError("cannot parse an empty string")

    if normalized in ("today", "now"):
        return today
    if normalized == "tomorrow":
        return today + timedelta(days=1)
    if normalized == "yesterday":
        return today - timedelta(days=1)

    weekday_match = re.fullmatch(r"(?:(next|last|this)\s+)?([a-z]+)", normalized)
    if weekday_match is not None:
        direction, weekday_name = weekday_match.groups()
        if weekday_name in _WEEKDAYS:
            target = _WEEKDAYS[weekday_name]
            if direction == "next":
                days = (target - today.weekday()) % 7 or 7
                return today + timedelta(days=days)
            if direction == "last":
                days = (today.weekday() - target) % 7 or 7
                return today - timedelta(days=days)
            return today + timedelta(days=(target - today.weekday()) % 7)

    period_match = re.fullmatch(r"(next|last)\s+(week|month|year)", normalized)
    if period_match is not None:
        direction, unit = period_match.groups()
        amount = 1 if direction == "next" else -1
        return _shift(today, amount, unit)

    offset_match = re.fullmatch(r"(.+?)\s+(before|after|from)\s+(.+)", normalized)
    if offset_match is not None:
        duration_text, direction, base_text = offset_match.groups()
        try:
            durations = _parse_durations(duration_text)
        except ValueError:
            durations = []
        if durations:
            base = parse(base_text, today)
            sign = -1 if direction == "before" else 1
            for amount, unit in durations:
                base = _shift(base, sign * amount, unit)
            return base

    in_match = re.fullmatch(r"in\s+(.+)", normalized)
    if in_match is not None:
        try:
            durations = _parse_durations(in_match.group(1))
        except ValueError:
            durations = []
        if durations:
            base = today
            for amount, unit in durations:
                base = _shift(base, amount, unit)
            return base

    ago_match = re.fullmatch(r"(.+?)\s+ago", normalized)
    if ago_match is not None:
        try:
            durations = _parse_durations(ago_match.group(1))
        except ValueError:
            durations = []
        if durations:
            base = today
            for amount, unit in durations:
                base = _shift(base, -amount, unit)
            return base

    return _parse_explicit(normalized, today)


def main() -> None:
    print(parse("today"))


if __name__ == "__main__":
    main()
