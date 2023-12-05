from django.db import models


class Order(models.Model):
    """
    Represents an order in the system.

    Attributes:
        user_id (str): The identifier of the user placing the order.
        product_code (str): The code associated with the ordered product.
        customer_fullname (str, optional): The full name of the customer (can be blank or null).
        product_name (str, optional): The name of the ordered product (can be blank or null).
        total_amount (float, optional): The total amount of the order (can be null).
        created_at (DateTime): The timestamp when the order was created (auto-generated).

    Note:
        - `customer_fullname`, `product_name`, and `total_amount` are optional fields.
        - `created_at` is automatically set to the current timestamp when the order is created.
    """

    user_id = models.CharField(max_length=255)
    product_code = models.CharField(max_length=255)
    customer_fullname = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
