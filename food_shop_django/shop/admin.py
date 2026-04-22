from django.contrib import admin

from .models import CustomerProfile, Discount, Order, OrderItem, Product


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "phone")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "name", "phone", "subtotal", "discount_code", "discount_amount", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "phone", "address")
    list_editable = ("status",)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "active", "created_at")
    list_filter = ("active", "discount_type")
    search_fields = ("code",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_name", "quantity", "line_total")
    search_fields = ("product_name",)

