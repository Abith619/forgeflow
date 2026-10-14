import pytest

from apps.accounts.factories import CompanyFactory
from apps.inventory.factories import WarehouseFactory
from apps.inventory.models import Warehouse

pytestmark = pytest.mark.django_db


def test_for_company_returns_only_matching_company_warehouses():
    company_a = CompanyFactory()
    company_b = CompanyFactory()

    warehouse_a = WarehouseFactory(company=company_a)
    WarehouseFactory(company=company_b)

    result = Warehouse.objects.for_company(company_a.id)

    assert list(result.values_list("pk", flat=True)) == [warehouse_a.pk]


def test_for_company_none_returns_no_warehouses():
    WarehouseFactory()

    result = Warehouse.objects.for_company(None)

    assert result.exists() is False
