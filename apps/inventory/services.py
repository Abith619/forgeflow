from django.db import transaction, OperationalError
from psycopg.errors import DeadlockDetected
from apps.inventory.models import StockQuant, StockMove
from django.core.exceptions import ValidationError

MAX_MOVE_RETRIES = 3
def move_stock(*, product, from_location, to_location, quantity, company, user, reference='', notes=''):
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0")
    if from_location == to_location:
        raise ValidationError("From location and to location cannot be same")
    for attempt in range(MAX_MOVE_RETRIES):
        try:
            with transaction.atomic():
                stock_quants = list(StockQuant.objects.select_for_update().filter(company=company, product=product, location__in=[from_location, to_location]).order_by("location_id"))

                quants = {
                    quant.location : quant
                    for quant in stock_quants
                }

                source = quants.get(from_location)
                destination = quants.get(to_location)

                if not source:
                    raise ValidationError("Insufficient stock at source")

                if source == destination:
                    raise ValidationError("From location and to location cannot be same")

                if not destination:
                    with transaction.atomic():
                        destination, created = StockQuant.objects.get_or_create(
                            company=company,
                            product=product,
                            location=to_location,
                            defaults={
                                "quantity": 0,
                                "reserved_qty": 0,
                            },
                        )
                        destination = StockQuant.objects.select_for_update().get(pk=destination.id)

                if source.available_quantity < quantity:
                    raise ValidationError("Insufficient stock")
                source.update_stock(-quantity)
                destination.update_stock(quantity)

                stock_move = StockMove.objects.create(
                    product=product,
                    from_location=from_location,
                    to_location=to_location,
                    quantity=quantity,
                    company=company,
                    user=user,
                    reference=reference,
                    notes=notes,
                )
                return stock_move, source, destination
        except OperationalError as e:
            if not isinstance(e.__cause__, DeadlockDetected):
                raise
            if attempt == MAX_MOVE_RETRIES - 1:
                raise
            else:
                continue
