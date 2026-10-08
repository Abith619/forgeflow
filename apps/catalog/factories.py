from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.accounts.factories import CompanyFactory
from apps.catalog.models import Product, ProductCategory, UoM


class UoMFactory(DjangoModelFactory):
    class Meta:
        model = UoM

    name = factory.Sequence(lambda n: f"UoM {n}")
    code = factory.Sequence(lambda n: f"UoM-{n}")
    unit_of_measure = factory.Iterator(["kg", "g", "mg", "mcg", "iu", "other"])

class ProductCategoryFactory(DjangoModelFactory):
    class Meta:
        model = ProductCategory
    
    name = factory.Sequence(lambda n: f"Category {n}")
    parent = None

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    type = factory.Iterator(["storable", "consumable", "service"])
    category = factory.SubFactory(ProductCategoryFactory)
    company = factory.SubFactory(CompanyFactory)
    uom = factory.SubFactory(UoMFactory)
    cost_price = factory.LazyFunction(lambda: Decimal("0.00"))
    sale_price = factory.LazyFunction(lambda: Decimal("0.00"))
    is_active = True
    sku = factory.Sequence(lambda n: f"SKU-{n}")
