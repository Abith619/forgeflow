from rest_framework import serializers
from apps.catalog.models import Product
from apps.inventory.models import Location, StockMove

class StockMoveRequestSerializer(serializers.Serializer):

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.none())
    from_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.none())
    to_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.none())
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    reference = serializers.CharField(max_length=50, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request is None:
            return

        company = request.user.company

        self.fields["product"].queryset = Product.objects.filter(company=company)
        self.fields["from_location"].queryset = Location.objects.filter(company=company)
        self.fields["to_location"].queryset = Location.objects.filter(company=company)

class StockMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMove
        fields = ["id", "product", "from_location", "to_location", "quantity", "reference", "notes", "user", "created_at"]