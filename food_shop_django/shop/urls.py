from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/clear/", views.cart_clear, name="cart_clear"),
    path("checkout/", views.checkout, name="checkout"),
    path("thanks/<int:order_id>/", views.thanks, name="thanks"),
]

