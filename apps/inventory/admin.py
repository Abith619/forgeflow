from django.contrib import admin
from .models import Warehouse, Location, StockQuant, StockMove

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "address", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "warehouse", "parent", "usage")
    list_filter = ("usage", "warehouse")
    search_fields = ("name", "warehouse__name")

@admin.register(StockQuant)
class StockQuantAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity", "reserved_qty", "available_quantity")
    list_filter = ("location__warehouse", "product__name", "location")
    search_fields = ("product__name", "location__name")

@admin.register(StockMove)
class StockMoveAdmin(admin.ModelAdmin):
    list_display = ("product", "from_location", "to_location", "quantity", "company")
    list_filter = ("company", "from_location__warehouse", "to_location__warehouse")
    search_fields = ("product__name", "from_location__name", "to_location__name")