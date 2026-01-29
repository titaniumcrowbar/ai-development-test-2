from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from . import models


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    required: bool
    max_length: int | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None


TABLE_CONFIGS = {
    models.Country: {
        "columns": [
            ColumnSpec("common_name", True, max_length=200),
            ColumnSpec("formal_name", True, max_length=200),
            ColumnSpec("country_code", True, max_length=5),
        ],
        "children": [models.Province, models.CountryLanguage],
    },
    models.Language: {
        "columns": [
            ColumnSpec("name", True, max_length=100),
            ColumnSpec("iso639_2_code", True, max_length=2),
        ],
        "children": [models.CountryLanguage],
    },
    models.CountryLanguage: {
        "columns": [
            ColumnSpec("country_id", True),
            ColumnSpec("language_id", True),
            ColumnSpec("is_official_language", True),
        ],
        "children": [],
    },
    models.Province: {
        "columns": [
            ColumnSpec("name", True, max_length=200),
            ColumnSpec("abbreviation", True, max_length=10),
            ColumnSpec("country_id", True),
        ],
        "children": [models.Address],
    },
    models.Timezone: {
        "columns": [
            ColumnSpec("name", True, max_length=100),
            ColumnSpec("utc_offset_sdt", True, min_value=Decimal("-24"), max_value=Decimal("24")),
            ColumnSpec("utc_offset_dst", True, min_value=Decimal("-24"), max_value=Decimal("24")),
            ColumnSpec("timezone_abbreviation_sdt", False, max_length=10),
            ColumnSpec("timezone_abbreviation_dst", False, max_length=10),
        ],
        "children": [models.Address],
    },
    models.Address: {
        "columns": [
            ColumnSpec("line1", True, max_length=200),
            ColumnSpec("line2", False, max_length=200),
            ColumnSpec("city", True, max_length=200),
            ColumnSpec("province_id", True),
            ColumnSpec("latitude", True, min_value=Decimal("-180"), max_value=Decimal("180")),
            ColumnSpec("longitude", True, min_value=Decimal("-180"), max_value=Decimal("180")),
            ColumnSpec("timezone_id", True),
            ColumnSpec("notes", False, max_length=5000),
        ],
        "children": [models.Customer],
    },
    models.OptIn: {
        "columns": [
            ColumnSpec("is_marketing_allowed", True),
            ColumnSpec("is_order_related_allowed", True),
        ],
        "children": [models.EmailAddress],
    },
    models.EmailAddress: {
        "columns": [
            ColumnSpec("email_address", True, max_length=250),
            ColumnSpec("opt_in_id", True),
        ],
        "children": [models.Customer],
    },
    models.Customer: {
        "columns": [
            ColumnSpec("first_name", True, max_length=100),
            ColumnSpec("last_name", True, max_length=100),
            ColumnSpec("primary_address_id", True),
            ColumnSpec("mailing_address_id", False),
            ColumnSpec("email_address_id", True),
        ],
        "children": [models.Invoice],
    },
    models.DataAction: {
        "columns": [
            ColumnSpec("name", True, max_length=20),
            ColumnSpec("lookup_value", True, max_length=20),
        ],
        "children": [models.DataLog],
    },
    models.Currency: {
        "columns": [
            ColumnSpec("name", True, max_length=200),
            ColumnSpec("alphabetic_code", True, max_length=3),
            ColumnSpec("numeric_code", True, max_length=3),
            ColumnSpec("decimal_digits", True, min_value=Decimal("0"), max_value=Decimal("5")),
        ],
        "children": [models.Invoice],
    },
    models.Invoice: {
        "columns": [
            ColumnSpec("customer_id", True),
            ColumnSpec("currency_id", True),
            ColumnSpec("total_item_amount", True, min_value=Decimal("0")),
            ColumnSpec("total_tax_amount", True, min_value=Decimal("0")),
            ColumnSpec("total_amount", True, min_value=Decimal("0")),
            ColumnSpec("total_amount_paid", True, min_value=Decimal("0")),
            ColumnSpec("total_amount_due", True, min_value=Decimal("0")),
            ColumnSpec("notes", False, max_length=5000),
        ],
        "children": [],
    },
    models.DataLog: {
        "columns": [
            ColumnSpec("data_action_id", True),
            ColumnSpec("is_success", True),
            ColumnSpec("record_id", False),
            ColumnSpec("message", False),
            ColumnSpec("detailed_log", False),
            ColumnSpec("user_id", False),
            ColumnSpec("timestamp", True),
        ],
        "children": [],
    },
}
