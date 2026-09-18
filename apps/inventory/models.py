from django.db import models
from apps.core.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.conf import settings

class Warehouse(TimeStampedModel):
    company = models.ForeignKey("accounts.company", on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "code"], name="uniq_warehouse_code_per_company")]

    def __str__(self):
        return f"{self.name} / {self.code}"

class Location(TimeStampedModel):
    warehouse = models.ForeignKey("inventory.warehouse", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("inventory.location", on_delete=models.PROTECT, null=True, related_name="children")

    LOCATION_CHOICES = [
        # internal, supplier, customer, inventory_loss, production, view
        ("internal", "Internal"),
        ("supplier", "Supplier"),
        ("customer", "Customer"),
        ("inventory_loss", "Inventory Loss"),
        ("production", "Production"),
        ("view", "View"),
    ]
    usage = models.CharField(max_length=20, choices=LOCATION_CHOICES)

    company = models.ForeignKey("accounts.company", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "name"], name="uniq_location_name_per_company")]

    def __str__(self):
        return f"{self.warehouse.name} / {self.parent.name if self.parent else None} / {self.name}"

class StockQuant(TimeStampedModel):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    location = models.ForeignKey("inventory.Location", on_delete=models.PROTECT)
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reserved_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "product", "location"],
                name="uniq_stock_quant_per_company_product_location",
            ),
            models.CheckConstraint(condition=Q(quantity__gte=0), name="quantity_non_negative"),
            models.CheckConstraint(condition=Q(reserved_qty__gte=0), name="reserved_qty_non_negative"),
            models.CheckConstraint(condition=Q(quantity__gte=F("reserved_qty")), name="reserved_qty_lte_quantity"),
        ]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_qty

    def update_stock(self, quantity):
        self.quantity += quantity
        self.save()

    def clean(self):
        if self.company_id != self.location.company_id:
            raise ValidationError({"location": "Location must belong to the same company."})

    def __str__(self):
        return f"{self.location.name} / {self.product.name} / {self.quantity}"

class StockMove(TimeStampedModel):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_moves")
    from_location = models.ForeignKey("inventory.Location", on_delete=models.PROTECT, related_name="outgoing_moves")
    to_location = models.ForeignKey("inventory.Location", on_delete=models.PROTECT, related_name="incoming_moves")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="stock_moves")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_moves")
    reference = models.CharField(max_length=50, blank=True, default="")
    notes     = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.product.name} / {self.from_location.name} -> {self.to_location.name} / {self.quantity}"
