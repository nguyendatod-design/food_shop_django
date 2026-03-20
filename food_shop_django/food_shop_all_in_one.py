import argparse
import os
from pathlib import Path


FILES: dict[str, str] = {
    "manage.py": """#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "food_shop.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không tìm thấy Django. Vui lòng cài đặt dependencies: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
""",
    "requirements.txt": """Django>=4.2,<6.0
""",
    "README.md": """# Food Shop (Django)

Demo website bán đồ ăn: menu + giỏ hàng + checkout (lưu Order vào SQLite).

## Cài đặt

```bat
cd /d YOUR_TARGET_FOLDER
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Mở trình duyệt

Truy cập: `http://127.0.0.1:8000/`
""",
    "food_shop/__init__.py": """""",
    "food_shop/settings.py": """from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "food_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "food_shop.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
""",
    "food_shop/urls.py": """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("shop.urls")),
]
""",
    "food_shop/wsgi.py": """import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "food_shop.settings")

application = get_wsgi_application()
""",
    "shop/__init__.py": """default_app_config = "shop.apps.ShopConfig"
""",
    "shop/apps.py": """from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"
""",
    "shop/models.py": """from decimal import Decimal

from django.db import models


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
""",
    "shop/views.py": """from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Order, OrderItem


MENU_ITEMS: list[dict[str, Any]] = [
    {
        "id": "pho_bo",
        "name": "Phở bò",
        "category": "Món chính",
        "desc": "Bánh phở, thịt bò, hành lá và nước dùng đậm đà.",
        "image": "https://source.unsplash.com/600x400/?pho,vietnam",
        "price": Decimal("55000"),
    },
    {
        "id": "com_ga",
        "name": "Cơm gà sốt",
        "category": "Món chính",
        "desc": "Cơm, gà chiên giòn, sốt đặc biệt thơm ngon.",
        "image": "https://source.unsplash.com/600x400/?chicken,rice",
        "price": Decimal("65000"),
    },
    {
        "id": "bap_thit",
        "name": "Bắp thịt nướng",
        "category": "Món chính",
        "desc": "Thịt nướng tẩm gia vị, ăn kèm rau sống.",
        "image": "https://source.unsplash.com/600x400/?grilled,meat",
        "price": Decimal("72000"),
    },
    {
        "id": "tra_dao",
        "name": "Trà đào",
        "category": "Đồ uống",
        "desc": "Trà đào thơm, thanh mát (đá tùy chọn).",
        "image": "https://source.unsplash.com/600x400/?tea,drink",
        "price": Decimal("35000"),
    },
    {
        "id": "nuoc_cam",
        "name": "Nước cam ép",
        "category": "Đồ uống",
        "desc": "Cam ép tươi, vị ngọt tự nhiên.",
        "image": "https://source.unsplash.com/600x400/?orange,juice",
        "price": Decimal("42000"),
    },
    {
        "id": "kem_vani",
        "name": "Kem vani",
        "category": "Tráng miệng",
        "desc": "Kem vani mát lạnh, ăn là ghiền.",
        "image": "https://source.unsplash.com/600x400/?ice-cream,vanilla",
        "price": Decimal("28000"),
    },
]

MENU_BY_CATEGORY: dict[str, list[dict[str, Any]]] = {}
for _it in MENU_ITEMS:
    MENU_BY_CATEGORY.setdefault(_it["category"], []).append(_it)

MENU_DICT = {it["id"]: it for it in MENU_ITEMS}


def _get_cart(session: Any) -> dict[str, int]:
    cart = session.get("cart", {})
    if not isinstance(cart, dict):
        return {}
    cleaned: dict[str, int] = {}
    for k, v in cart.items():
        try:
            qty = int(v)
        except (TypeError, ValueError):
            continue
        if qty > 0:
            cleaned[str(k)] = qty
    return cleaned


def _set_cart(session: Any, cart: dict[str, int]) -> None:
    session["cart"] = cart
    session.modified = True


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html", {"menu_by_category": MENU_BY_CATEGORY})


def cart(request: HttpRequest) -> HttpResponse:
    cart_data = _get_cart(request.session)
    cart_items: list[dict[str, Any]] = []
    total = Decimal("0")
    for item_id, qty in cart_data.items():
        item = MENU_DICT.get(item_id)
        if not item:
            continue
        line_total = item["price"] * qty
        total += line_total
        cart_items.append(
            {
                "id": item_id,
                "name": item["name"],
                "price": item["price"],
                "qty": qty,
                "line_total": line_total,
            }
        )
    return render(
        request,
        "cart.html",
        {"cart_items": cart_items, "total": total},
    )


def cart_add(request: HttpRequest, item_id: str) -> HttpResponse:
    item = MENU_DICT.get(item_id)
    if not item:
        return redirect("cart")

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    qty = max(1, min(10, qty))
    cart_data = _get_cart(request.session)
    cart_data[item_id] = cart_data.get(item_id, 0) + qty
    cart_data[item_id] = min(20, cart_data[item_id])
    _set_cart(request.session, cart_data)
    return redirect("cart")


def cart_update(request: HttpRequest, item_id: str) -> HttpResponse:
    item = MENU_DICT.get(item_id)
    if not item:
        return redirect("cart")

    try:
        qty = int(request.POST.get("qty", "0"))
    except ValueError:
        qty = 0

    qty = max(-1000, min(1000, qty))
    cart_data = _get_cart(request.session)
    if qty <= 0:
        cart_data.pop(item_id, None)
    else:
        cart_data[item_id] = min(20, qty)
    _set_cart(request.session, cart_data)
    return redirect("cart")


def cart_clear(request: HttpRequest) -> HttpResponse:
    _set_cart(request.session, {})
    return redirect("cart")


def checkout(request: HttpRequest) -> HttpResponse:
    cart_data = _get_cart(request.session)
    if not cart_data:
        return redirect("index")

    cart_items: list[dict[str, Any]] = []
    total = Decimal("0")
    for item_id, qty in cart_data.items():
        item = MENU_DICT.get(item_id)
        if not item:
            continue
        line_total = item["price"] * qty
        total += line_total
        cart_items.append(
            {"id": item_id, "name": item["name"], "price": item["price"], "qty": qty, "line_total": line_total}
        )

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        address = (request.POST.get("address") or "").strip()
        notes = (request.POST.get("notes") or "").strip()

        error = None
        if not name:
            error = "Vui lòng nhập tên."
        elif not address:
            error = "Vui lòng nhập địa chỉ."

        if error:
            return render(
                request,
                "checkout.html",
                {"cart_items": cart_items, "total": total, "error": error},
            )

        order = Order.objects.create(
            name=name,
            phone=phone,
            address=address,
            notes=notes,
            total=total,
            status=Order.STATUS_PAID,
        )

        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                product_name=ci["name"],
                unit_price=ci["price"],
                quantity=ci["qty"],
                line_total=ci["line_total"],
            )

        _set_cart(request.session, {})
        return redirect(reverse("thanks", kwargs={"order_id": order.id}))

    return render(request, "checkout.html", {"cart_items": cart_items, "total": total})


def thanks(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, id=order_id)
    return render(request, "thanks.html", {"order": order})
""",
    "shop/urls.py": """from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<str:item_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<str:item_id>/", views.cart_update, name="cart_update"),
    path("cart/clear/", views.cart_clear, name="cart_clear"),
    path("checkout/", views.checkout, name="checkout"),
    path("thanks/<int:order_id>/", views.thanks, name="thanks"),
]
""",
    "templates/base.html": """{% load static %}
<!doctype html>
<html lang="vi">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{% block title %}Food Shop{% endblock %}</title>
        <link rel="stylesheet" href="{% static 'styles.css' %}" />
    </head>
    <body>
        <header class="header">
            <div class="container header__inner">
                <a class="brand" href="{% url 'index' %}">Food Shop</a>
                <nav class="nav">
                    <a class="nav__link" href="{% url 'index' %}">Menu</a>
                    <a class="nav__link" href="{% url 'cart' %}">Giỏ hàng</a>
                </nav>
            </div>
        </header>

        <main class="container">
            {% block content %}{% endblock %}
        </main>

        <footer class="footer">
            <div class="container footer__inner">Demo web bán đồ ăn bằng Django.</div>
        </footer>
    </body>
</html>
""",
    "templates/index.html": """{% extends "base.html" %}

{% block title %}Menu - Food Shop{% endblock %}

{% block content %}
    <h1 class="page-title">Menu</h1>

    {% for category, items in menu_by_category.items %}
        <section class="card card--section">
            <h2 class="section-title">{{ category }}</h2>
            <div class="grid">
                {% for item in items %}
                    <div class="menu-item">
                        <img class="menu-item__img" src="{{ item.image }}" alt="{{ item.name }}" loading="lazy" />
                        <div class="menu-item__top">
                            <div>
                                <div class="menu-item__name">{{ item.name }}</div>
                                <div class="menu-item__desc">{{ item.desc }}</div>
                            </div>
                            <div class="menu-item__price">{{ item.price|floatformat:0 }} đ</div>
                        </div>

                        <form class="menu-item__actions" method="post" action="{% url 'cart_add' item.id %}">
                            {% csrf_token %}
                            <label class="label">
                                Số lượng:
                                <input class="input" type="number" name="qty" value="1" min="1" max="10" />
                            </label>
                            <button class="btn" type="submit">Thêm</button>
                        </form>
                    </div>
                {% endfor %}
            </div>
        </section>
    {% endfor %}
{% endblock %}
""",
    "templates/cart.html": """{% extends "base.html" %}

{% block title %}Giỏ hàng - Food Shop{% endblock %}

{% block content %}
    <h1 class="page-title">Giỏ hàng</h1>

    {% if not cart_items %}
        <div class="empty">
            Giỏ hàng của bạn đang trống.
            <div class="empty__actions">
                <a class="btn btn--secondary" href="{% url 'index' %}">Xem menu</a>
            </div>
        </div>
    {% else %}
        <div class="card">
            <table class="table">
                <thead>
                    <tr>
                        <th>Món</th>
                        <th>Đơn giá</th>
                        <th>Số lượng</th>
                        <th>Thành tiền</th>
                    </tr>
                </thead>
                <tbody>
                    {% for it in cart_items %}
                        <tr>
                            <td>{{ it.name }}</td>
                            <td>{{ it.price|floatformat:0 }} đ</td>
                            <td class="table__qty">
                                <form method="post" action="{% url 'cart_update' it.id %}">
                                    {% csrf_token %}
                                    <input class="input input--qty" type="number" name="qty" value="{{ it.qty }}" min="0" max="20" />
                                    <button class="btn btn--tiny" type="submit">Cập nhật</button>
                                </form>
                            </td>
                            <td>{{ it.line_total|floatformat:0 }} đ</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>

            <div class="cart-summary">
                <div class="cart-summary__total">
                    Tổng: <span class="money">{{ total|floatformat:0 }} đ</span>
                </div>
                <div class="cart-summary__actions">
                    <form method="post" action="{% url 'cart_clear' %}">
                        {% csrf_token %}
                        <button class="btn btn--secondary" type="submit">Xóa giỏ</button>
                    </form>
                    <a class="btn" href="{% url 'checkout' %}">Đặt hàng</a>
                </div>
            </div>
        </div>
    {% endif %}
{% endblock %}
""",
    "templates/checkout.html": """{% extends "base.html" %}

{% block title %}Thanh toán - Food Shop{% endblock %}

{% block content %}
    <h1 class="page-title">Thanh toán</h1>

    <div class="card card--form">
        <h2 class="card-title">Thông tin đơn hàng</h2>

        {% if error %}
            <div class="alert alert--error">{{ error }}</div>
        {% endif %}

        <form method="post" class="form">
            {% csrf_token %}
            <div class="form__grid">
                <label class="label">
                    Họ tên
                    <input class="input" type="text" name="name" placeholder="Nguyễn Văn A" required />
                </label>
                <label class="label">
                    Số điện thoại
                    <input class="input" type="text" name="phone" placeholder="0123 456 789" />
                </label>
            </div>

            <label class="label">
                Địa chỉ nhận hàng
                <textarea class="input input--textarea" name="address" placeholder="Số nhà, đường, phường/xã..." required></textarea>
            </label>

            <label class="label">
                Ghi chú (tùy chọn)
                <textarea class="input input--textarea" name="notes" placeholder="Ví dụ: Không hành, giao giờ 5h..."></textarea>
            </label>

            <div class="checkout-summary">
                <div class="checkout-summary__total">
                    Tổng tiền: <span class="money">{{ total|floatformat:0 }} đ</span>
                </div>
                <div class="checkout-summary__items">
                    <div class="checkout-summary__items-title">Các món</div>
                    <ul class="list">
                        {% for it in cart_items %}
                            <li class="list__item">
                                {{ it.name }} x{{ it.qty }} - {{ it.line_total|floatformat:0 }} đ
                            </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>

            <button class="btn btn--primary" type="submit">Đặt hàng</button>
        </form>
    </div>
{% endblock %}
""",
    "templates/thanks.html": """{% extends "base.html" %}

{% block title %}Cảm ơn - Food Shop{% endblock %}

{% block content %}
    <h1 class="page-title">Cảm ơn bạn!</h1>

    <div class="card">
        <div class="thanks">
            <div class="thanks__title">Đơn hàng đã được tạo.</div>
            <div class="thanks__meta">
                Mã đơn: <strong>#{{ order.id }}</strong><br />
                Trạng thái: <strong>{{ order.get_status_display }}</strong><br />
                Thời gian: <strong>{{ order.created_at }}</strong>
            </div>

            <div class="thanks__total">
                Tổng tiền: <span class="money">{{ order.total|floatformat:0 }} đ</span>
            </div>

            <div class="thanks__items-title">Chi tiết:</div>
            <ul class="list">
                {% for it in order.items.all %}
                    <li class="list__item">
                        {{ it.product_name }} x{{ it.quantity }} - {{ it.line_total|floatformat:0 }} đ
                    </li>
                {% endfor %}
            </ul>

            <div class="thanks__actions">
                <a class="btn" href="{% url 'index' %}">Quay lại menu</a>
            </div>
        </div>
    </div>
{% endblock %}
""",
    "static/styles.css": """:root {
    --bg: #fff7ed;
    --card: #ffffff;
    --text: #111827;
    --muted: #6b7280;
    --primary: #ff6a00;
    --primary2: #ffb000;
    --danger: #e11d48;
    --border: rgba(17, 24, 39, 0.12);
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
    background: radial-gradient(900px 420px at 10% 0%, rgba(255, 166, 0, 0.18), transparent 60%), var(--bg);
    color: var(--text);
}

.container {
    width: min(1000px, calc(100% - 32px));
    margin: 0 auto;
}

.header {
    position: sticky;
    top: 0;
    backdrop-filter: blur(8px);
    background: rgba(255, 255, 255, 0.72);
    border-bottom: 1px solid var(--border);
}

.header__inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0;
}

.brand {
    font-weight: 800;
    letter-spacing: 0.3px;
    text-decoration: none;
    color: var(--text);
}

.nav {
    display: flex;
    gap: 16px;
}

.nav__link {
    color: var(--muted);
    text-decoration: none;
    font-weight: 600;
}

.nav__link:hover {
    color: var(--text);
}

.page-title {
    margin: 26px 0 14px;
    font-size: 28px;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 6px 26px rgba(17, 24, 39, 0.06);
}

.card--section {
    padding: 18px 18px 10px;
    margin-bottom: 18px;
}

.section-title {
    margin: 0 0 12px;
    font-size: 18px;
    color: var(--text);
}

.grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

@media (max-width: 720px) {
    .grid {
        grid-template-columns: 1fr;
    }
}

.menu-item {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: rgba(255, 255, 255, 0.75);
}

.menu-item__img {
    width: 100%;
    height: 140px;
    object-fit: cover;
    border-radius: 10px;
    display: block;
}

.menu-item__top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}

.menu-item__name {
    font-weight: 800;
}

.menu-item__desc {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.35;
    margin-top: 6px;
}

.menu-item__price {
    font-weight: 900;
    color: var(--primary);
    white-space: nowrap;
}

.menu-item__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: flex-end;
    justify-content: space-between;
}

.label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    color: var(--muted);
    font-weight: 700;
    font-size: 13px;
}

.input {
    width: 100%;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.95);
    color: var(--text);
    outline: none;
}

.input--qty {
    max-width: 130px;
}

.input--textarea {
    min-height: 80px;
    resize: vertical;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.9);
    color: var(--text);
    font-weight: 800;
    cursor: pointer;
    text-decoration: none;
}

.btn:hover {
    border-color: rgba(17, 24, 39, 0.22);
}

.btn--primary {
    background: linear-gradient(180deg, var(--primary), var(--primary2));
    border-color: rgba(255, 106, 0, 0.35);
    color: #111827;
}

.btn--secondary {
    background: rgba(255, 255, 255, 0.95);
}

.btn--tiny {
    padding: 8px 10px;
    font-size: 13px;
}

.table {
    width: 100%;
    border-collapse: collapse;
}

.table th,
.table td {
    text-align: left;
    padding: 10px 6px;
    border-bottom: 1px solid var(--border);
}

.table th {
    color: var(--muted);
    font-size: 13px;
}

.table__qty form {
    display: flex;
    gap: 10px;
    align-items: center;
}

.cart-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 14px;
    flex-wrap: wrap;
}

.cart-summary__total {
    font-weight: 900;
}

.money {
    color: var(--primary);
}

.cart-summary__actions {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
}

.card--form {
    max-width: 760px;
}

.form {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.form__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

@media (max-width: 720px) {
    .form__grid {
        grid-template-columns: 1fr;
    }
}

.alert {
    border-radius: 12px;
    padding: 12px 14px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.9);
}

.alert--error {
    border-color: rgba(255, 92, 122, 0.6);
    background: rgba(255, 92, 122, 0.12);
    color: #ffd3da;
}

.footer {
    margin-top: 30px;
    border-top: 1px solid var(--border);
    padding: 18px 0;
    color: var(--muted);
}

.footer__inner {
    font-size: 13px;
}

.empty {
    padding: 18px;
    border-radius: 14px;
    border: 1px dashed var(--border);
    color: var(--muted);
}

.empty__actions {
    margin-top: 12px;
}

.checkout-summary {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    background: rgba(255, 255, 255, 0.9);
}

.checkout-summary__total {
    font-weight: 900;
    margin-bottom: 10px;
}

.checkout-summary__items-title {
    color: var(--muted);
    font-weight: 800;
    font-size: 13px;
    margin-bottom: 8px;
}

.list {
    padding-left: 18px;
    margin: 0;
}

.list__item {
    padding: 6px 0;
    color: var(--text);
}

.thanks__title {
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 10px;
}

.thanks__meta {
    color: var(--muted);
    line-height: 1.6;
}

.thanks__total {
    margin-top: 12px;
    font-weight: 900;
    font-size: 18px;
}

.thanks__items-title {
    margin-top: 14px;
    color: var(--muted);
    font-weight: 800;
    margin-bottom: 6px;
}

.thanks__actions {
    margin-top: 14px;
}
""",
}


def write_file(root: Path, rel_path: str, content: str, *, force: bool) -> None:
    dst = root / rel_path
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo project Django bán đồ ăn từ 1 file.")
    parser.add_argument(
        "--target",
        default=str(Path(__file__).resolve().parent / "food_shop_django_generated"),
        help="Thư mục đích để sinh project.",
    )
    parser.add_argument("--force", action="store_true", help="Ghi đè nếu đã tồn tại file.")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    print(f"Tạo project vào: {target}")

    for rel_path, content in FILES.items():
        write_file(target, rel_path, content, force=args.force)

    print("Xong. Tiếp theo bạn chạy các lệnh sau:")
    print(f"cd /d \"{target}\"")
    print("python -m venv .venv")
    print(r".venv\Scripts\activate")
    print("pip install -r requirements.txt")
    print("python manage.py makemigrations")
    print("python manage.py migrate")
    print("python manage.py runserver")


if __name__ == "__main__":
    main()

