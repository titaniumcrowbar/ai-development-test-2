from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from .database import Base


class GUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)


class TimestampMixin:
    timestamp = Column(DateTime, nullable=False)


class IsActiveMixin:
    is_active = Column(Boolean, nullable=False, default=True)


class Country(Base, IsActiveMixin):
    __tablename__ = "countries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    common_name = Column(String(200), nullable=False)
    formal_name = Column(String(200), nullable=False)
    country_code = Column(String(5), nullable=False)


class Language(Base, IsActiveMixin):
    __tablename__ = "languages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    iso639_2_code = Column(String(2), nullable=False)


class CountryLanguage(Base, IsActiveMixin):
    __tablename__ = "country_languages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    country_id = Column(GUID(), ForeignKey("countries.id"), nullable=False)
    language_id = Column(GUID(), ForeignKey("languages.id"), nullable=False)
    is_official_language = Column(Boolean, nullable=False)

    country = relationship("Country")
    language = relationship("Language")


class Province(Base, IsActiveMixin):
    __tablename__ = "provinces"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    country_id = Column(GUID(), ForeignKey("countries.id"), nullable=False)

    country = relationship("Country")


class Timezone(Base, IsActiveMixin):
    __tablename__ = "timezones"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    utc_offset_sdt = Column(Numeric, nullable=False)
    utc_offset_dst = Column(Numeric, nullable=False)
    timezone_abbreviation_sdt = Column(String(10), nullable=True)
    timezone_abbreviation_dst = Column(String(10), nullable=True)


class Address(Base, IsActiveMixin):
    __tablename__ = "addresses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    line1 = Column(String(200), nullable=False)
    line2 = Column(String(200), nullable=True)
    city = Column(String(200), nullable=False)
    province_id = Column(GUID(), ForeignKey("provinces.id"), nullable=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    timezone_id = Column(GUID(), ForeignKey("timezones.id"), nullable=False)
    notes = Column(String(5000), nullable=True)

    province = relationship("Province")
    timezone = relationship("Timezone")


class OptIn(Base, IsActiveMixin):
    __tablename__ = "opt_ins"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    is_marketing_allowed = Column(Boolean, nullable=False)
    is_order_related_allowed = Column(Boolean, nullable=False)


class EmailAddress(Base, IsActiveMixin):
    __tablename__ = "email_addresses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email_address = Column(String(250), nullable=False)
    opt_in_id = Column(GUID(), ForeignKey("opt_ins.id"), nullable=False)

    opt_in = relationship("OptIn")


class Customer(Base, IsActiveMixin):
    __tablename__ = "customers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    primary_address_id = Column(GUID(), ForeignKey("addresses.id"), nullable=False)
    mailing_address_id = Column(GUID(), ForeignKey("addresses.id"), nullable=True)
    email_address_id = Column(GUID(), ForeignKey("email_addresses.id"), nullable=False)

    primary_address = relationship("Address", foreign_keys=[primary_address_id])
    mailing_address = relationship("Address", foreign_keys=[mailing_address_id])
    email_address = relationship("EmailAddress")


class DataAction(Base, IsActiveMixin):
    __tablename__ = "data_actions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(20), nullable=False)
    lookup_value = Column(String(20), nullable=False)


class Currency(Base, IsActiveMixin):
    __tablename__ = "currencies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    alphabetic_code = Column(String(3), nullable=False)
    numeric_code = Column(String(3), nullable=False)
    decimal_digits = Column(Numeric, nullable=False)


class Invoice(Base, IsActiveMixin):
    __tablename__ = "invoices"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_id = Column(GUID(), ForeignKey("customers.id"), nullable=False)
    currency_id = Column(GUID(), ForeignKey("currencies.id"), nullable=False)
    total_item_amount = Column(Numeric, nullable=False)
    total_tax_amount = Column(Numeric, nullable=False)
    total_amount = Column(Numeric, nullable=False)
    total_amount_paid = Column(Numeric, nullable=False)
    total_amount_due = Column(Numeric, nullable=False)
    notes = Column(String(5000), nullable=True)

    customer = relationship("Customer")
    currency = relationship("Currency")


class DataLog(Base):
    __tablename__ = "data_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    data_action_id = Column(GUID(), ForeignKey("data_actions.id"), nullable=False)
    is_success = Column(Boolean, nullable=False)
    record_id = Column(GUID(), nullable=True)
    message = Column(String, nullable=True)
    detailed_log = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)

    data_action = relationship("DataAction")
