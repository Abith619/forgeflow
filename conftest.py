import pytest

from apps.accounts.factories import CompanyFactory, UserFactory
from apps.catalog.factories import ProductFactory, UoMFactory
from apps.inventory.factories import (
    LocationFactory,
    StockQuantFactory,
    WarehouseFactory,
)


@pytest.fixture
def company():
    return CompanyFactory()


@pytest.fixture
def user(company):
    return UserFactory(company=company)


@pytest.fixture
def product(company):
    return ProductFactory(company=company)


@pytest.fixture
def uom():
    return UoMFactory()


@pytest.fixture
def warehouse(company):
    return WarehouseFactory(company=company)


@pytest.fixture
def source_location(warehouse):
    return LocationFactory(warehouse=warehouse)


@pytest.fixture
def dest_location(warehouse):
    return LocationFactory(warehouse=warehouse)


@pytest.fixture
def stock_quant(source_location, product):
    return StockQuantFactory(location=source_location, product=product)
