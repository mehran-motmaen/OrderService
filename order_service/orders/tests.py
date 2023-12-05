from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Order
from .serializers import OrderSerializer
from unittest.mock import patch, MagicMock


class OrderModelTest(TestCase):
    def test_order_creation(self):
        """
        Test the creation of an Order instance.

        The test verifies that an Order instance is created correctly with the provided data.

        Returns:
            None
        """
        # Arrange
        data = {
            "user_id": "test_user",
            "product_code": "test_product",
            "customer_fullname": "Test Customer",
            "product_name": "Test Product",
            "total_amount": 50.0,
        }

        # Act
        order = Order.objects.create(**data)

        # Assert
        self.assertIsInstance(order, Order)
        self.assertIsNotNone(order.id)
        self.assertEqual(order.user_id, "test_user")
        self.assertEqual(order.product_code, "test_product")
        self.assertEqual(order.customer_fullname, "Test Customer")
        self.assertEqual(order.product_name, "Test Product")
        self.assertEqual(order.total_amount, 50.0)
        self.assertIsNotNone(order.created_at)


class OrderSerializerTest(TestCase):
    def test_order_serializer_valid_data(self):
        """
        Test the OrderSerializer with valid input data.

        The test ensures that the OrderSerializer correctly processes and validates valid input data.

        Returns:
            None
        """
        # Arrange
        data = {
            "user_id": "test_user",
            "product_code": "test_product",
            "customer_fullname": "Test Customer",
            "product_name": "Test Product",
            "total_amount": 50.0,
        }

        # Act
        serializer = OrderSerializer(data=data)
        is_valid = serializer.is_valid()

        # Assert
        self.assertTrue(is_valid)
        order_instance = serializer.save()
        self.assertIsInstance(order_instance, Order)
        self.assertIsNotNone(order_instance.id)
        self.assertEqual(order_instance.user_id, "test_user")
        self.assertEqual(order_instance.product_code, "test_product")
        self.assertEqual(order_instance.customer_fullname, "Test Customer")
        self.assertEqual(order_instance.product_name, "Test Product")
        self.assertEqual(order_instance.total_amount, 50.0)
        self.assertIsNotNone(order_instance.created_at)

    def test_order_serializer_invalid_data(self):
        """
        Test the OrderSerializer with invalid input data.

        The test checks that the OrderSerializer handles invalid input data appropriately.

        Returns:
            None
        """
        # Arrange
        invalid_data = {
            "user_id": "7c11ee2741",
            "product_code": "test_product",
            "total_amount": -10.0,  # Negative total amount
        }

        # Act
        serializer = OrderSerializer(data=invalid_data)
        is_valid = serializer.is_valid()

        # Assert
        self.assertFalse(is_valid)


class OrderCreateViewTest(TestCase):
    def setUp(self):
        """
        Set up the OrderCreateViewTest.

        This method initializes the APIClient for making HTTP requests in subsequent tests.

        Returns:
            None
        """
        self.client = APIClient()

    @patch("orders.views.requests.get")
    @patch("orders.views.pika.BlockingConnection")
    def test_create_order(self, mock_rabbitmq, mock_get):
        """
        Test the creation of an order using the OrderCreateView.

        The test mocks external service responses for user-service and product-service and ensures
        that the OrderCreateView processes the request correctly.

        Returns:
            None
        """
        # Arrange
        url = reverse("order-create")
        data = {
            "user_id": "test_user",
            "product_code": "test_product",
            "customer_fullname": "Test Customer",
            "product_name": "Test Product",
            "total_amount": 50.0,
        }

        # Mock the user-service and product-service responses
        user_service_response = MagicMock()
        user_service_response.status_code = 200
        user_service_response.json.return_value = {
            "firstName": "Test",
            "lastName": "User",
        }

        product_service_response = MagicMock()
        product_service_response.status_code = 200
        product_service_response.json.return_value = {
            "name": "Test Product",
            "price": 50.0,
        }

        mock_get.side_effect = [
            user_service_response,
            product_service_response,
        ]  # User-service, Product-service

        # Mock RabbitMQ connection and channel
        mock_channel = MagicMock()
        mock_rabbitmq.return_value.__enter__.return_value.channel.return_value = (
            mock_channel
        )

        # Act
        response = self.client.post(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data["id"])
        self.assertEqual(response.data["user_id"], "test_user")
        self.assertEqual(response.data["product_code"], "test_product")
        self.assertEqual(
            response.data["customer_fullname"], "Test User"
        )  # Comes from mocked response
        self.assertEqual(
            response.data["product_name"], "Test Product"
        )  # Comes from mocked response
        self.assertEqual(response.data["total_amount"], 50.0)
        self.assertIsNotNone(response.data["created_at"])
