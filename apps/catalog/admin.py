from django.contrib import admin
from .models import UoM, ProductCategory, Product

@admin.register(UoM)
class UoMAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "unit_of_measure"]
    search_fields = ["name", "code"]
    list_filter = ["unit_of_measure"]

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent"]
    search_fields = ["name"]
    list_filter = ["parent"]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'uom', 'company', 'cost_price', 'sale_price', 'is_active']
    search_fields = ['sku', 'name']
    list_filter = ['type','is_active', 'company']
    list_select_related = ['category', 'uom', 'company']
