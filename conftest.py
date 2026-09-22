import pytest
from apps.accounts.factories import UserFactory, CompanyFactory
from apps.catalog.factories import ProductFactory, UoMFactory, ProductCategoryFactory
from apps.inventory.factories import WarehouseFactory, LocationFactory, StockQuantFactory

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
def product_category(company):
    return ProductCategoryFactory(company=company)

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
def stock_quant(location, product):
    return StockQuantFactory(location=location, product=product)