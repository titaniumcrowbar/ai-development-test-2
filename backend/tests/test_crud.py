from __future__ import annotations

from decimal import Decimal

from app.crud import CrudService, create_data_log
from app.models import Address, Country, Currency, Customer, EmailAddress, Invoice, OptIn, Province, Timezone


def test_create_data_log_missing_action(session):
    try:
        create_data_log(session, data_action="missing", is_success=False)
    except Exception as exc:
        assert "Could not find DataAction" in str(exc)
    else:
        raise AssertionError("Expected RecordNotFound exception")


def test_read_not_found(session):
    service = CrudService(Country)
    result = service.read(session, record_id="00000000-0000-0000-0000-000000000000")
    assert result.data_log.is_success is False
    assert result.record is None


def test_read_success(session):
    country = Country(common_name="Test", formal_name="Testland", country_code="TT", is_active=True)
    session.add(country)
    session.commit()
    service = CrudService(Country)
    result = service.read(session, record_id=country.id)
    assert result.data_log.is_success is True
    assert result.record.id == country.id


def test_validate_required_and_length(session):
    service = CrudService(Country)
    country = Country(common_name="", formal_name="F" * 201, country_code=None, is_active=True)
    result = service.validate(session, source=country)
    assert result.data_log.is_success is False
    assert "common_name must contain at least one character" in result.data_log.detailed_log
    assert "formal_name must be at most" in result.data_log.detailed_log
    assert "country_code is required" in result.data_log.detailed_log


def test_validate_numeric_bounds(session):
    timezone = Timezone(name="UTC", utc_offset_sdt=Decimal("25"), utc_offset_dst=Decimal("-25"))
    service = CrudService(Timezone)
    result = service.validate(session, source=timezone)
    assert result.data_log.is_success is False
    assert "utc_offset_sdt must be less than or equal to 24" in result.data_log.detailed_log
    assert "utc_offset_dst must be greater than or equal to -24" in result.data_log.detailed_log


def test_validate_id_not_found(session):
    country = Country(id="11111111-1111-1111-1111-111111111111", common_name="Test", formal_name="Test", country_code="TT")
    service = CrudService(Country)
    result = service.validate(session, source=country)
    assert result.data_log.is_success is False
    assert "does not exist" in result.data_log.detailed_log


def test_get_can_remove_missing(session):
    service = CrudService(Country)
    result = service.get_can_remove(session, record_id="22222222-2222-2222-2222-222222222222")
    assert result.data_log.is_success is False
    assert "does not exist" in result.data_log.message


def test_get_can_remove_already_removed(session):
    country = Country(common_name="Test", formal_name="Test", country_code="TT", is_active=False)
    session.add(country)
    session.commit()
    service = CrudService(Country)
    result = service.get_can_remove(session, record_id=country.id)
    assert result.data_log.is_success is False
    assert "already been removed" in result.data_log.message


def test_upsert_create_and_update(session):
    service = CrudService(Country)
    new_country = Country(common_name="Test", formal_name="Test", country_code="TT")
    create_result = service.upsert(session, source=new_country)
    assert create_result.data_log.is_success is True

    new_country.common_name = "Updated"
    update_result = service.upsert(session, source=new_country)
    assert update_result.data_log.is_success is True
    assert session.query(Country).filter(Country.id == new_country.id).one().common_name == "Updated"


def test_remove_soft_delete(session):
    country = Country(common_name="Test", formal_name="Test", country_code="TT", is_active=True)
    session.add(country)
    session.commit()
    service = CrudService(Country)
    result = service.remove(session, record_id=country.id)
    assert result.data_log.is_success is True
    assert session.query(Country).filter(Country.id == country.id).one().is_active is False


def test_delete_hard_delete_with_children(session):
    country = Country(common_name="Test", formal_name="Test", country_code="TT", is_active=True)
    session.add(country)
    session.flush()
    province = Province(name="Test", abbreviation="TT", country_id=country.id, is_active=True)
    session.add(province)
    session.commit()

    service = CrudService(Country)
    result = service.delete(session, record_id=country.id)
    assert result.data_log.is_success is True
    assert session.query(Country).filter(Country.id == country.id).count() == 0
    assert session.query(Province).filter(Province.id == province.id).count() == 0


def test_address_numeric_bounds(session):
    country = Country(common_name="Test", formal_name="Test", country_code="TT", is_active=True)
    session.add(country)
    session.flush()
    province = Province(name="Test", abbreviation="TT", country_id=country.id, is_active=True)
    session.add(province)
    timezone = Timezone(name="UTC", utc_offset_sdt=Decimal("0"), utc_offset_dst=Decimal("0"), is_active=True)
    session.add(timezone)
    session.commit()

    address = Address(
        line1="Line",
        city="City",
        province_id=province.id,
        latitude=Decimal("181"),
        longitude=Decimal("-181"),
        timezone_id=timezone.id,
        is_active=True,
    )
    service = CrudService(Address)
    result = service.validate(session, source=address)
    assert result.data_log.is_success is False
    assert "latitude must be less than or equal to 180" in result.data_log.detailed_log
    assert "longitude must be greater than or equal to -180" in result.data_log.detailed_log


def test_currency_decimal_digits_bounds(session):
    service = CrudService(Currency)
    currency = Currency(name="Test", alphabetic_code="TST", numeric_code="999", decimal_digits=Decimal("6"))
    result = service.validate(session, source=currency)
    assert result.data_log.is_success is False
    assert "decimal_digits must be less than or equal to 5" in result.data_log.detailed_log


def test_invoice_upsert_sets_total_due(session):
    country = Country(common_name="Test", formal_name="Test", country_code="TT", is_active=True)
    session.add(country)
    session.flush()
    province = Province(name="Test", abbreviation="TT", country_id=country.id, is_active=True)
    session.add(province)
    timezone = Timezone(name="UTC", utc_offset_sdt=Decimal("0"), utc_offset_dst=Decimal("0"), is_active=True)
    session.add(timezone)
    session.flush()
    address = Address(
        line1="Line",
        city="City",
        province_id=province.id,
        latitude=Decimal("10"),
        longitude=Decimal("10"),
        timezone_id=timezone.id,
        is_active=True,
    )
    session.add(address)
    session.flush()
    opt_in = OptIn(is_marketing_allowed=True, is_order_related_allowed=True, is_active=True)
    session.add(opt_in)
    session.flush()
    email = EmailAddress(email_address="test@example.com", opt_in_id=opt_in.id, is_active=True)
    session.add(email)
    session.flush()
    customer = Customer(
        first_name="Test",
        last_name="User",
        primary_address_id=address.id,
        mailing_address_id=None,
        email_address_id=email.id,
        is_active=True,
    )
    session.add(customer)
    session.flush()
    currency = Currency(name="Test Currency", alphabetic_code="TST", numeric_code="001", decimal_digits=Decimal("2"))
    session.add(currency)
    session.commit()

    invoice = Invoice(
        customer_id=customer.id,
        currency_id=currency.id,
        total_item_amount=Decimal("100"),
        total_tax_amount=Decimal("20"),
        total_amount=Decimal("120"),
        total_amount_paid=Decimal("30"),
        total_amount_due=Decimal("120"),
        is_active=True,
    )
    service = CrudService(Invoice)
    result = service.upsert(session, source=invoice)
    assert result.data_log.is_success is True
    stored = session.query(Invoice).filter(Invoice.id == invoice.id).one()
    assert stored.total_amount_due == Decimal("90")
