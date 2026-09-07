from django.db import models
from django.db.models import Q
from apps.accounts.models import Company
from apps.core.models import TimeStampedModel

class UoM(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=10, unique=True)

    UoM_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('mg', 'Milligram'),
        ('mcg', 'Microgram'),
        ('iu', 'International Unit'),
        ('other', 'Other'),
    ]

    unit_of_measure = models.CharField(max_length=10, choices=UoM_CHOICES)

    def __str__(self):
        return self.code

class ProductCategory(TimeStampedModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["parent", "name"], name='uniq_product_category_name', nulls_distinct=False)]

    def __str__(self):
        return self.name

class Product(TimeStampedModel):
    name = models.CharField(max_length=100)
    ProductType_CHOICES = [
        ('storable', 'Storable'),
        ('consumable', 'Consumable'),
        ('service', 'Service'),
    ]
    type = models.CharField(max_length=100, choices=ProductType_CHOICES)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    sku = models.CharField(max_length=50)
    uom = models.ForeignKey(UoM, on_delete=models.PROTECT, related_name='products')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'sku'], name='uniq_product_sku_per_company', ), models.CheckConstraint(condition=Q(sale_price__gte=0) & Q(cost_price__gte=0), name='check_price_constraint')]

    def __str__(self):
        return self.name
