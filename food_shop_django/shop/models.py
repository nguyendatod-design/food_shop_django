from decimal import Decimal

from django.contrib.auth.models import User
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


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, related_name="customer_profile", on_delete=models.CASCADE)
    phone = models.CharField(max_length=30, blank=True, default="")
    default_address = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return self.user.get_username()


class Discount(models.Model):
    DISCOUNT_PERCENT = "percent"
    DISCOUNT_FIXED = "fixed"
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_PERCENT, "Phần trăm (%)"),
        (DISCOUNT_FIXED, "Số tiền cố định"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=DISCOUNT_PERCENT)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PAID = "paid"
    STATUS_PREPARING = "preparing"
    STATUS_DELIVERING = "delivering"
    STATUS_DONE = "done"

    STATUS_CHOICES = [
        (STATUS_NEW, "Mới"),
        (STATUS_PAID, "Đã đặt"),
        (STATUS_PREPARING, "Đang chuẩn bị"),
        (STATUS_DELIVERING, "Đang giao"),
        (STATUS_DONE, "Hoàn tất"),
    ]

    customer = models.ForeignKey(
        "auth.User",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField()
    notes = models.TextField(blank=True, default="")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount_code = models.CharField(max_length=50, blank=True, default="")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
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

