from decimal import Decimal
import pytest
from apps.inventory.factories import StockQuantFactory, LocationFactory
from apps.inventory.services import move_stock
from apps.accounts.factories import UserFactory
from apps.inventory.models import StockMove, StockQuant
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_quant_factory_keeps_one_company():
    quant = StockQuantFactory()

    assert quant.company == quant.location.company
    assert quant.location.company == quant.product.company
    assert quant.location.warehouse.company == quant.company
    assert quant.product.company == quant.company

@pytest.mark.django_db
def test_move_stock_sufficient_stock():
    quant = StockQuantFactory(quantity=Decimal("150.00"))
    user = UserFactory(company=quant.company)
    dest_location = LocationFactory(warehouse=quant.location.warehouse)
    move_stock(
        product=quant.product,
        from_location=quant.location,
        to_location=dest_location,
        quantity=Decimal("100.00"),
        user=user,
        company=quant.company
    )

@pytest.mark.django_db(transaction=True)
def test_move_stock_sufficient_stock(
    product,
    source_location,
    dest_location,
    user,
):
    # Arrange
    quant = StockQuantFactory(
        product=product,
        location=source_location,
        quantity=Decimal("150.00"),
    )

    # Act
    move, source, destination = move_stock(
        product=product,
        from_location=source_location,
        to_location=dest_location,
        quantity=Decimal("100.00"),
        user=user,
        company=quant.company,
    )

    # Assert 1: source quantity is reduced
    source.refresh_from_db()
    assert source.quantity == Decimal("50.00")

    # Assert 2: destination quantity is actually persisted
    destination_from_db = StockQuant.objects.get(
        product=product,
        location=dest_location,
    )
    assert destination_from_db.quantity == Decimal("100.00")

    # Assert 3: exactly one stock movement was created
    assert StockMove.objects.count() == 1

    # Assert 4: movement details
    assert move.user == user
    assert move.quantity == Decimal("100.00")

    # Assert 5: movement locations
    assert move.from_location == quant.location
    assert move.to_location == dest_location

@pytest.mark.django_db(transaction=True)
def test_move_stock_insufficient_stock_changes_nothing(
    product,
    source_location,
    dest_location,
    user,
):
    # Arrange
    source_quant = StockQuantFactory(
        product=product,
        location=source_location,
        quantity=Decimal("10.00"),
    )

    # Act
    with pytest.raises(ValidationError) as exc_info:
        move_stock(
            product=product,
            from_location=source_location,
            to_location=dest_location,
            quantity=Decimal("50.00"),
            user=user,
            company=source_quant.company,
        )

    # Assert 1: exact error message
    assert exc_info.value.messages == ["Insufficient stock"]

    # Assert 2: source quantity is unchanged
    source_quant.refresh_from_db()
    assert source_quant.quantity == Decimal("10.00")

    # Assert 3: destination quant creation was rolled back
    assert not StockQuant.objects.filter(
        product=product,
        location=dest_location,
    ).exists()

    # Assert 4: no stock movement was created
    assert StockMove.objects.count() == 0