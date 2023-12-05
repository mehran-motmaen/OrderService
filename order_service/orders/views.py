from rest_framework import generics
from .models import Order
from .serializers import OrderSerializer
from rest_framework.response import Response
from rest_framework import status
import json
import pika
import requests

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Fetch customer_fullname from user-service
        user_id = serializer.validated_data['user_id']
        user_service_url = f'http://user-service:8080/users/{user_id}'
        user_response = requests.get(user_service_url)

        if user_response.status_code == 200:
            user_data = user_response.json()
            serializer.validated_data['customer_fullname'] = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}"
        else:
            return Response({"error": "Unable to fetch user information"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Fetch product_name and total_amount from product-service
        product_code = serializer.validated_data['product_code']
        product_service_url = f'http://product-service:8080/products/{product_code}'
        product_response = requests.get(product_service_url)
        if product_response.status_code == 200:
            product_data = product_response.json()
            serializer.validated_data['product_name'] = product_data.get('name', '')
            serializer.validated_data['total_amount'] = product_data.get('price', 0.0)
        else:
            return Response({"error": "Unable to fetch product information"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Publish to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='rabbitmq',
                credentials=pika.PlainCredentials('hellofresh', 'food')
            )
        )
        channel = connection.channel()
        channel.exchange_declare(exchange='orders', exchange_type='direct')

        message = {
            "producer": "Order Service",
            "sent_at": str(serializer.data['created_at']),
            "type": "created_order",
            "payload": {
                "order": {
                    "order_id": serializer.data['id'],
                    "customer_fullname": serializer.data['customer_fullname'],
                    "product_name": serializer.data['product_name'],
                    "total_amount": serializer.data['total_amount'],
                    "created_at": str(serializer.data['created_at']),
                }
            }
        }

        channel.basic_publish(exchange='orders', routing_key='created_order', body=json.dumps(message))
        connection.close()

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
