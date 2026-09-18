from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.inventory.serializers import StockMoveRequestSerializer, StockMoveSerializer
from apps.inventory.services import move_stock

class StockMoveCreateView(APIView):
    def post(self, request):
        serializer = StockMoveRequestSerializer(data=request.data, context={"request": request})
        if serializer:
            serializer.is_valid(raise_exception=True)

        try:
            move, source, destination = move_stock(
                **serializer.validated_data,
                user=request.user,
                company=request.user.company,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, "message_dict") else e.messages)

        return Response(StockMoveSerializer(move).data, status=status.HTTP_201_CREATED)
