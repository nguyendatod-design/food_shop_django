from django.contrib import admin

from .models import Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "phone", "address")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_name", "quantity", "line_total")
    search_fields = ("product_name",)

