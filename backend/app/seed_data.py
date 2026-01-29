from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

import pandas as pd

from .database import get_session
from .models import (
    Country,
    Currency,
    DataAction,
    Language,
    Timezone,
)


@dataclass(frozen=True)
class DataActionSeed:
    name: str
    lookup_value: str


DATA_ACTION_SEEDS = [
    DataActionSeed(name="Create", lookup_value="create"),
    DataActionSeed(name="Update", lookup_value="update"),
    DataActionSeed(name="Delete", lookup_value="harddelete"),
    DataActionSeed(name="Remove", lookup_value="softdelete"),
    DataActionSeed(name="Read", lookup_value="read"),
    DataActionSeed(name="Validate", lookup_value="validate"),
]


def seed_data_actions():
    with get_session() as session:
        for seed in DATA_ACTION_SEEDS:
            exists = session.query(DataAction).filter(DataAction.lookup_value == seed.lookup_value).one_or_none()
            if exists:
                continue
            session.add(DataAction(name=seed.name, lookup_value=seed.lookup_value, is_active=True))


def seed_languages_from_wikipedia(url: str):
    tables = pd.read_html(url)
    for table in tables:
        if "ISO 639-2" in table.columns and "Language name" in table.columns:
            language_table = table
            break
    else:
        raise ValueError("Could not find ISO 639-2 table on Wikipedia.")

    with get_session() as session:
        for _, row in language_table.iterrows():
            name = str(row.get("Language name", "")).strip()
            iso_code = str(row.get("ISO 639-2", "")).strip()
            if not name or not iso_code:
                continue
            exists = session.query(Language).filter(Language.iso639_2_code == iso_code).one_or_none()
            if exists:
                continue
            session.add(Language(name=name[:100], iso639_2_code=iso_code[:2], is_active=True))


def seed_timezones_from_wikipedia(url: str):
    tables = pd.read_html(url)
    timezone_table = None
    for table in tables:
        if "TZ identifier" in table.columns and "UTC offset" in table.columns:
            timezone_table = table
            break
    if timezone_table is None:
        raise ValueError("Could not find timezone table on Wikipedia.")

    with get_session() as session:
        for _, row in timezone_table.iterrows():
            name = str(row.get("TZ identifier", "")).strip()
            utc_offset = str(row.get("UTC offset", "")).strip()
            if not name or not utc_offset:
                continue
            offset_value = Decimal(utc_offset.replace("UTC", "").strip() or "0")
            exists = session.query(Timezone).filter(Timezone.name == name).one_or_none()
            if exists:
                continue
            session.add(
                Timezone(
                    name=name[:100],
                    utc_offset_sdt=offset_value,
                    utc_offset_dst=offset_value,
                    timezone_abbreviation_sdt=None,
                    timezone_abbreviation_dst=None,
                    is_active=True,
                )
            )


def seed_countries_from_wikipedia(url: str):
    tables = pd.read_html(url)
    country_table = None
    for table in tables:
        if "Common and formal names" in table.columns:
            country_table = table
            break
    if country_table is None:
        raise ValueError("Could not find country table on Wikipedia.")

    with get_session() as session:
        for _, row in country_table.iterrows():
            names = str(row.get("Common and formal names", "")).split("–")
            if not names:
                continue
            common_name = names[0].strip()
            formal_name = names[1].strip() if len(names) > 1 else names[0].strip()
            code = str(row.get("ISO 3166-1 alpha-2", "")).strip()
            if not common_name or not formal_name or not code:
                continue
            exists = session.query(Country).filter(Country.country_code == code).one_or_none()
            if exists:
                continue
            session.add(
                Country(
                    common_name=common_name[:200],
                    formal_name=formal_name[:200],
                    country_code=code[:5],
                    is_active=True,
                )
            )


def seed_currencies_from_wikipedia(url: str):
    tables = pd.read_html(url)
    currency_table = None
    for table in tables:
        if {"Code", "Num", "D", "Currency"}.issubset(set(table.columns)):
            currency_table = table
            break
    if currency_table is None:
        raise ValueError("Could not find active ISO 4217 currency table on Wikipedia.")

    with get_session() as session:
        for _, row in currency_table.iterrows():
            code = str(row.get("Code", "")).strip()
            num = str(row.get("Num", "")).strip()
            digits = row.get("D", "")
            name = str(row.get("Currency", "")).strip()
            if not code or not num or not name or digits == "":
                continue
            try:
                decimal_digits = Decimal(str(digits))
            except Exception:
                continue
            exists = session.query(Currency).filter(Currency.alphabetic_code == code).one_or_none()
            if exists:
                continue
            session.add(
                Currency(
                    name=name[:200],
                    alphabetic_code=code[:3],
                    numeric_code=num[:3],
                    decimal_digits=decimal_digits,
                    is_active=True,
                )
            )


def run_all_seeds():
    seed_data_actions()
    seed_languages_from_wikipedia("https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes")
    seed_timezones_from_wikipedia("https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
    seed_countries_from_wikipedia("https://en.wikipedia.org/wiki/List_of_sovereign_states")
    seed_currencies_from_wikipedia("https://en.wikipedia.org/wiki/ISO_4217")


__all__ = [
    "seed_data_actions",
    "seed_languages_from_wikipedia",
    "seed_timezones_from_wikipedia",
    "seed_countries_from_wikipedia",
    "seed_currencies_from_wikipedia",
    "run_all_seeds",
]


if __name__ == "__main__":
    run_all_seeds()
