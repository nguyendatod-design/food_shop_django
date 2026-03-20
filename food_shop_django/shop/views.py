from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Order, OrderItem, Product


def _get_cart(session: Any) -> dict[str, int]:
    cart = session.get("cart", {})
    if not isinstance(cart, dict):
        return {}
    # Đảm bảo kiểu dữ liệu an toàn
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
    products = Product.objects.filter(active=True).order_by("category", "name")
    menu_by_category: dict[str, list[Product]] = {}
    for p in products:
        menu_by_category.setdefault(p.category, []).append(p)
    return render(request, "index.html", {"menu_by_category": menu_by_category})


def cart(request: HttpRequest) -> HttpResponse:
    cart_data = _get_cart(request.session)
    cart_items: list[dict[str, Any]] = []
    total = Decimal("0")

    # Lấy product theo danh sách id có trong cart (giảm query)
    product_ids: list[int] = []
    for pid_str in cart_data.keys():
        try:
            product_ids.append(int(pid_str))
        except (TypeError, ValueError):
            continue
    products_by_id = Product.objects.filter(active=True, id__in=product_ids).in_bulk()

    for pid_str, qty in cart_data.items():
        try:
            pid = int(pid_str)
        except (TypeError, ValueError):
            continue
        product = products_by_id.get(pid)
        if not product:
            continue
        line_total = product.price * qty
        total += line_total
        cart_items.append(
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "qty": qty,
                "line_total": line_total,
            }
        )
    return render(
        request,
        "cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        },
    )


def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, active=True, id=product_id)

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    qty = max(1, min(10, qty))
    cart_data = _get_cart(request.session)
    key = str(product.id)
    cart_data[key] = cart_data.get(key, 0) + qty
    cart_data[key] = min(20, cart_data[key])
    _set_cart(request.session, cart_data)
    return redirect("cart")


def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    get_object_or_404(Product, active=True, id=product_id)

    try:
        qty = int(request.POST.get("qty", "0"))
    except ValueError:
        qty = 0

    qty = max(-1000, min(1000, qty))

    cart_data = _get_cart(request.session)
    key = str(product_id)
    if qty <= 0:
        cart_data.pop(key, None)
    else:
        cart_data[key] = min(20, qty)
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

    product_ids: list[int] = []
    for pid_str in cart_data.keys():
        try:
            product_ids.append(int(pid_str))
        except (TypeError, ValueError):
            continue
    products_by_id = Product.objects.filter(active=True, id__in=product_ids).in_bulk()

    for pid_str, qty in cart_data.items():
        try:
            pid = int(pid_str)
        except (TypeError, ValueError):
            continue
        product = products_by_id.get(pid)
        if not product:
            continue
        line_total = product.price * qty
        total += line_total
        cart_items.append(
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "qty": qty,
                "line_total": line_total,
            }
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
                {
                    "cart_items": cart_items,
                    "total": total,
                    "error": error,
                },
            )

        order = Order.objects.create(
            name=name,
            phone=phone,
            address=address,
            notes=notes,
            total=total,
            status=Order.STATUS_PAID,
        )

        # Lưu chi tiết món
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

