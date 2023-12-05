from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Order
from .serializers import OrderSerializer


class OrderModelTest(TestCase):
    def test_order_creation(self):
        # Arrange
        data = {
            "user_id": "test_user",
            "product_code": "test_product",
            "customer_fullname": "Test Customer",
            "product_name": "Test Product",
            "total_amount": 50.0
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
        # Arrange
        data = {
            "user_id": "test_user",
            "product_code": "test_product",
            "customer_fullname": "Test Customer",
            "product_name": "Test Product",
            "total_amount": 50.0
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
        # Arrange
        invalid_data = {
            "user_id": "7c11ee2741",
            "product_code": "test_product",
            "total_amount": -10.0  # Negative total amount
        }

        # Act
        serializer = OrderSerializer(data=invalid_data)
        is_valid = serializer.is_valid()

        # Assert
        self.assertFalse(is_valid)


class OrderCreateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_order(self):
        # Arrange
        url = reverse('order-create')
        data = {
            "user_id": "test_user",
            "product_code": "test_product",
            "customer_fullname": "Test Customer",
            "product_name": "Test Product",
            "total_amount": 50.0
        }

        # Act
        response = self.client.post(url, data, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['id'])
        self.assertEqual(response.data['user_id'], "test_user")
        self.assertEqual(response.data['product_code'], "test_product")
        self.assertEqual(response.data['customer_fullname'], "Test Customer")
        self.assertEqual(response.data['product_name'], "Test Product")
        self.assertEqual(response.data['total_amount'], 50.0)
        self.assertIsNotNone(response.data['created_at'])

    def test_create_order_invalid_data(self):
        # Arrange
        url = reverse('order-create')
        invalid_data = {
            "user_id": "7c11ee2741",
            "product_code": "test_product",
            "total_amount": -10.0  # Negative total amount
        }

        # Act
        response = self.client.post(url, invalid_data, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
