from rest_framework import generics
from .models import Order
from .serializers import OrderSerializer
from rest_framework.response import Response
from rest_framework import status
import json
import pika
import requests
import concurrent.futures


class OrderCreateView(generics.CreateAPIView):
    """
    Create a new order by fetching user and product information concurrently.

    This view performs the following steps:
    1. Fetch customer_fullname from user-service using the provided user_id concurrently.
    2. Fetch product_name and total_amount from product-service using the provided product_code concurrently.
    3. Create a new order with the fetched information.
    4. Publish the order information to RabbitMQ.

    Endpoint: POST /orders/

    Parameters:
        - user_id: ID of the user placing the order.
        - product_code: Code of the product being ordered.

    Returns:
        - 201 Created: Order successfully created.
        - 500 Internal Server Error: If there are issues fetching user or product information.

    Note: External service calls to user-service and product-service are performed concurrently
          using ThreadPoolExecutor for improved performance.

    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def fetch_user_info(self, user_id):
        """
        Fetch user information from user-service.

        Parameters:
            user_id (int): ID of the user.

        Returns:
            str: Full name of the user.
        """

        user_service_url = f"http://user-service:8080/users/{user_id}"
        user_response = requests.get(user_service_url)
        user_response.raise_for_status()
        user_data = user_response.json()
        return f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}"

    def fetch_product_info(self, product_code):
        """
        Fetch product information from product-service.

        Parameters:
            product_code (str): Code of the product.

        Returns:
            tuple: A tuple containing product name and total amount.
        """

        product_service_url = f"http://product-service:8080/products/{product_code}"
        product_response = requests.get(product_service_url)
        product_response.raise_for_status()
        product_data = product_response.json()
        return product_data.get("name", ""), product_data.get("price", 0.0)

    def create(self, request, *args, **kwargs):
        """
        Create a new order by fetching user and product information concurrently.

        Parameters:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: HTTP response containing the order data or error information.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Fetch customer_fullname from user-service in a separate thread
            user_id = serializer.validated_data["user_id"]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                user_fullname_future = executor.submit(self.fetch_user_info, user_id)

            # Fetch product_name and total_amount from product-service in a separate thread
            product_code = serializer.validated_data["product_code"]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                product_info_future = executor.submit(
                    self.fetch_product_info, product_code
                )

            # Wait for both threads to complete
            customer_fullname = user_fullname_future.result()
            product_name, total_amount = product_info_future.result()

            # Update serializer data
            serializer.validated_data["customer_fullname"] = customer_fullname
            serializer.validated_data["product_name"] = product_name
            serializer.validated_data["total_amount"] = total_amount

            # Perform the rest of the processing as before
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # Publish to RabbitMQ
            with pika.BlockingConnection(
                pika.ConnectionParameters(
                    host="rabbitmq",
                    credentials=pika.PlainCredentials("hellofresh", "food"),
                )
            ) as connection:
                channel = connection.channel()
                channel.exchange_declare(exchange="orders", exchange_type="direct")

                message = {
                    "producer": "Order Service",
                    "sent_at": str(serializer.data["created_at"]),
                    "type": "created_order",
                    "payload": {
                        "order": {
                            "order_id": serializer.data["id"],
                            "customer_fullname": serializer.data["customer_fullname"],
                            "product_name": serializer.data["product_name"],
                            "total_amount": serializer.data["total_amount"],
                            "created_at": str(serializer.data["created_at"]),
                        }
                    },
                }

                channel.basic_publish(
                    exchange="orders",
                    routing_key="created_order",
                    body=json.dumps(message),
                )

            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        except requests.RequestException as e:
            error_message = f"Request to external service failed: {str(e)}"
            return Response(
                {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except pika.exceptions.AMQPError as e:
            error_message = f"Error connecting to RabbitMQ: {str(e)}"
            return Response(
                {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
