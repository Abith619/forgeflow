from django.urls import path
from apps.inventory.views import StockMoveCreateView

urlpatterns = [
    path("moves/", StockMoveCreateView.as_view(), name="stock-move-create"),
]