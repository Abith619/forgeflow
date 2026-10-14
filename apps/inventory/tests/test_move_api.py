from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from apps.inventory.models import StockMove
from apps.inventory.factories import (
    CompanyFactory,
    ProductFactory,
    LocationFactory,
    StockQuantFactory,
)
from apps.accounts.factories import UserFactory


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        (User.Role.ADMIN, status.HTTP_201_CREATED),
        (User.Role.INVENTORY_MANAGER, status.HTTP_201_CREATED),
        (User.Role.OPERATOR, status.HTTP_201_CREATED),
        (User.Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_create_stock_move_by_role(
    api_client,
    role,
    expected_status,
):
    company = CompanyFactory()
    user = UserFactory(company=company, role=role)

    product = ProductFactory(company=company)
    source_location = LocationFactory(company=company)
    dest_location = LocationFactory(company=company)

    StockQuantFactory(
        company=company,
        product=product,
        location=source_location,
        quantity=Decimal("100.00"),
        reserved_qty=Decimal("0.00"),
    )

    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("stock-move-create"),  # Use your actual URL name.
        {
            "product": product.pk,
            "from_location": source_location.pk,
            "to_location": dest_location.pk,
            "quantity": "10.00",
        },
        format="json",
    )

    assert response.status_code == expected_status

    if role == User.Role.VIEWER:
        assert StockMove.objects.count() == 0


def test_anonymous_cannot_create_stock_move(api_client):
    response = api_client.post(
        reverse("stock-move-create"),
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert StockMove.objects.count() == 0
