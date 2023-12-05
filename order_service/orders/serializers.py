from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    def validate_total_amount(self, value):
        """
        Validate that the total_amount is not negative.

        Args:
            value (float): The total amount to be validated.

        Returns:
            float: The validated total amount.

        Raises:
            serializers.ValidationError: If the total_amount is negative.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("Total amount cannot be negative.")
        return value
