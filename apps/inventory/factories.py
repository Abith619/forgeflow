from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.accounts.factories import CompanyFactory
from apps.catalog.factories import ProductFactory
from apps.inventory.models import Location, StockQuant, Warehouse


class WarehouseFactory(DjangoModelFactory):
    class Meta:
        model = Warehouse

    company = factory.SubFactory(CompanyFactory)
    code = factory.Sequence(lambda n: f"WH-{n:04d}")
    name = factory.Sequence(lambda n: f"Warehouse {n}")
    address = "Chennai"

class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    warehouse = factory.SubFactory(WarehouseFactory)
    company = factory.SelfAttribute('warehouse.company')
    name = factory.Sequence(lambda n: f"Location {n}")
    usage = "internal"

class StockQuantFactory(DjangoModelFactory):
    class Meta:
        model = StockQuant

    location = factory.SubFactory(LocationFactory)
    company = factory.SelfAttribute('location.company')
    product = factory.SubFactory(ProductFactory, company=factory.SelfAttribute('..company'))
    quantity = factory.LazyFunction(lambda: Decimal("0.00"))
    reserved_qty = factory.LazyFunction(lambda: Decimal("0.00"))
