from decimal import Decimal

from django.db import models


class Product(models.Model):
    CATEGORY_FOOD = "Món chính"
    CATEGORY_DRINK = "Đồ uống"
    CATEGORY_DESSERT = "Tráng miệng"
    CATEGORY_CHOICES = [
        (CATEGORY_FOOD, "Món chính"),
        (CATEGORY_DRINK, "Đồ uống"),
        (CATEGORY_DESSERT, "Tráng miệng"),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    desc = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PAID = "paid"

    STATUS_CHOICES = [
        (STATUS_NEW, "Mới"),
        (STATUS_PAID, "Đã đặt"),
    ]

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField()
    notes = models.TextField(blank=True, default="")

    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product_name} x{self.quantity}"

