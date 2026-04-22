from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("cart/clear/", views.cart_clear, name="cart_clear"),

    path("product/<int:product_id>/", views.product_detail, name="product_detail"),

    path("checkout/", views.checkout, name="checkout"),
    path("thanks/<int:order_id>/", views.thanks, name="thanks"),
    path("orders/", views.order_history, name="order_history"),

    path("chat/", views.chat_page, name="chat"),
    path("chat/api/", views.chat_api, name="chat_api"),

    # LOGIN REGISTER
    path("login/", views.user_login, name="login"),
    path("register/", views.user_register, name="register"),
    path("logout/", views.user_logout, name="logout"),
]