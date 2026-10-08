from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import CompanyScopedQuerysetMixin
from apps.inventory.models import StockQuant
from apps.inventory.serializers import (
    StockMoveRequestSerializer,
    StockMoveSerializer,
    StockQuantSerializer,
)
from apps.inventory.services import move_stock


class StockMoveCreateView(APIView):
    def post(self, request):
        serializer = StockMoveRequestSerializer(data=request.data, context={"request": request})
        if serializer:
            serializer.is_valid(raise_exception=True)

        try:
            move, _source, _destination = move_stock(
                **serializer.validated_data,
                user=request.user,
                company=request.user.company,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, "message_dict") else e.messages)

        return Response(StockMoveSerializer(move).data, status=status.HTTP_201_CREATED)

class StockQuantListView(CompanyScopedQuerysetMixin, ListAPIView):
    serializer_class = StockQuantSerializer

    queryset = StockQuant.objects.select_related("product", "location")
    