from decimal import Decimal
import pytest
from apps.inventory.factories import StockQuantFactory, LocationFactory
from apps.inventory.services import move_stock
from apps.inventory.models import StockMove, StockQuant
from apps.accounts.factories import CompanyFactory, UserFactory
from apps.catalog.factories import ProductFactory
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_quant_factory_keeps_one_company():
    quant = StockQuantFactory()

    assert quant.company == quant.location.company
    assert quant.location.company == quant.product.company
    assert quant.location.warehouse.company == quant.company
    assert quant.product.company == quant.company

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


@pytest.mark.django_db
def test_move_stock_rejects_location_from_other_company():
    # Arrange
    company_a = CompanyFactory()
    product = ProductFactory(company=company_a)
    source_location = LocationFactory(warehouse__company=company_a)

    source_quant = StockQuantFactory(
        company=company_a,
        product=product,
        location=source_location,
        quantity=100,
        reserved_qty=0,
    )

    # No company argument -> creates a location belonging to another company
    destination_location = LocationFactory()

    user = UserFactory(company=company_a)

    # Make sure our test setup is actually cross-company
    assert destination_location.company_id != company_a.id

    # Act
    with pytest.raises(ValidationError, match="To location does not belong to the specified company"):
        move_stock(
            product=product,
            from_location=source_location,
            to_location=destination_location,
            quantity=10,
            company=company_a,
            user=user,
        )
