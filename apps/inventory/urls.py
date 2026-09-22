from django.urls import path
from apps.inventory.views import StockMoveCreateView, StockQuantListView

urlpatterns = [
    path("moves/", StockMoveCreateView.as_view(), name="stock-move-create"),
    path("quants/", StockQuantListView.as_view(), name="stock-quant-list")
]