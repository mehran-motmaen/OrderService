from rest_framework import generics
from .models import Order
from .serializers import OrderSerializer
from rest_framework.response import Response
from rest_framework import status
import json
import pika


class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
