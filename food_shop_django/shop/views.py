from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Discount, Order, OrderItem, Product


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


def _get_products(q: str, category: str, sort: str):
    qs = Product.objects.filter(active=True)

    if category and category != "all":
        qs = qs.filter(category=category)

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(desc__icontains=q))

    if sort == "price_asc":
        qs = qs.order_by("price", "name")
    elif sort == "price_desc":
        qs = qs.order_by("-price", "name")
    elif sort == "name_asc":
        qs = qs.order_by("name")
    else:
        # "new" (mặc định): coi `id` mới hơn
        qs = qs.order_by("-id")

    return qs


def index(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    category = (request.GET.get("category") or "all").strip()
    sort = (request.GET.get("sort") or "new").strip()

    products = _get_products(q=q, category=category, sort=sort)
    menu_by_category: dict[str, list[Product]] = {}
    for p in products:
        menu_by_category.setdefault(p.category, []).append(p)

    categories = list(
        Product.objects.filter(active=True)
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "index.html",
        {
            "menu_by_category": menu_by_category,
            "categories": categories,
            "q": q,
            "category": category,
            "sort": sort,
        },
    )


def product_detail(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, active=True, id=product_id)

    if request.method == "POST":
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

    return render(request, "product_detail.html", {"product": product})


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


def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("cart")

    cart_data = _get_cart(request.session)
    key = str(product_id)
    cart_data.pop(key, None)
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
    subtotal = Decimal("0")

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
        subtotal += line_total
        cart_items.append(
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "qty": qty,
                "line_total": line_total,
            }
        )

    total = subtotal
    discount_amount = Decimal("0")
    discount_code = ""

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        address = (request.POST.get("address") or "").strip()
        notes = (request.POST.get("notes") or "").strip()
        promo_code = (request.POST.get("promo_code") or "").strip()

        error = None
        if not name:
            error = "Vui lòng nhập tên."
        elif not address:
            error = "Vui lòng nhập địa chỉ."

        if not error and promo_code:
            discount = Discount.objects.filter(active=True, code__iexact=promo_code).first()
            if not discount:
                error = "Mã giảm giá không hợp lệ."
            else:
                discount_code = discount.code
                if discount.discount_type == Discount.DISCOUNT_PERCENT:
                    discount_amount = (subtotal * discount.value) / Decimal("100")
                else:
                    discount_amount = discount.value

                # Không cho giảm vượt quá tạm tính
                if discount_amount > subtotal:
                    discount_amount = subtotal

                total = subtotal - discount_amount

        if error:
            return render(
                request,
                "checkout.html",
                {
                    "cart_items": cart_items,
                    "subtotal": subtotal,
                    "discount_amount": discount_amount,
                    "discount_code": discount_code,
                    "total": total,
                    "error": error,
                },
            )

        order = Order.objects.create(
            customer=request.user if request.user.is_authenticated else None,
            name=name,
            phone=phone,
            address=address,
            notes=notes,
            subtotal=subtotal,
            discount_code=discount_code,
            discount_amount=discount_amount,
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

    return render(
        request,
        "checkout.html",
        {
            "cart_items": cart_items,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "discount_code": discount_code,
            "total": total,
        },
    )


def thanks(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, id=order_id)
    return render(request, "thanks.html", {"order": order})


@login_required
def order_history(request: HttpRequest) -> HttpResponse:
    orders = Order.objects.filter(customer=request.user).order_by("-created_at")
    return render(request, "orders.html", {"orders": orders})


def chat_page(request: HttpRequest) -> HttpResponse:
    return render(request, "chat.html")


def chat_api(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"reply": "Chỉ hỗ trợ POST."}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    message = (payload.get("message") or "").strip()
    message_l = message.lower()

    if not message:
        return JsonResponse(
            {
                "reply": "Bạn muốn hỏi/ tìm món gì ạ? Ví dụ: 'Tìm phở', 'Menu đồ uống', 'Giỏ hàng của tôi'."
            }
        )

    # --- Giỏ hàng ---
    if any(x in message_l for x in ["giỏ", "cart", "xem giỏ", "món trong giỏ"]):
        cart_data = _get_cart(request.session)
        if not cart_data:
            return JsonResponse({"reply": "Giỏ hàng của bạn đang trống. Bạn muốn xem menu món nào không?"})

        product_ids: list[int] = []
        for pid_str in cart_data.keys():
            try:
                product_ids.append(int(pid_str))
            except (TypeError, ValueError):
                continue
        products_by_id = Product.objects.filter(active=True, id__in=product_ids).in_bulk()

        parts: list[str] = []
        total = Decimal("0")
        for pid_str, qty in cart_data.items():
            try:
                pid = int(pid_str)
            except (TypeError, ValueError):
                continue
            p = products_by_id.get(pid)
            if not p:
                continue
            line = p.price * qty
            total += line
            parts.append(f"{p.name} x{qty} ({line:,.0f} đ)".replace(",", "."))

        return JsonResponse(
            {"reply": f"Giỏ hàng của bạn: {', '.join(parts)}. Tổng: {total:,.0f} đ.".replace(",", ".")}
        )

    # --- Menu / tìm món ---
    if any(x in message_l for x in ["menu", "món", "đồ ăn", "đồ uống", "tráng miệng", "tìm", "gợi ý"]):
        if "đồ uống" in message_l:
            qs = _get_products(q="", category="Đồ uống", sort="new")[:6]
        elif "tráng miệng" in message_l or "dessert" in message_l:
            qs = _get_products(q="", category="Tráng miệng", sort="new")[:6]
        elif "món chính" in message_l:
            qs = _get_products(q="", category="Món chính", sort="new")[:6]
        else:
            # Tách từ khóa: ví dụ "Tìm phở" -> "phở"
            clean = message
            for prefix in ["tìm ", "menu ", "gợi ý ", "món ", "đồ ăn ", "đồ uống ", "tráng miệng "]:
                if clean.lower().startswith(prefix):
                    clean = clean[len(prefix):]
                    break
            clean = clean.strip()
            qs = _get_products(q=clean, category="all", sort="new")[:6]

        products = list(qs)
        if not products:
            return JsonResponse({"reply": "Mình chưa tìm thấy món phù hợp. Bạn thử viết lại: 'phở', 'trà đào', 'kem'..."})

        lines = [f"- {p.name}: {p.price:,.0f} đ".replace(",", ".") for p in products]
        return JsonResponse({"reply": "Mình gợi ý:\n" + "\n".join(lines) + "\n\nBạn muốn thêm món nào vào giỏ?"})

    # --- Checkout ---
    if any(x in message_l for x in ["đặt hàng", "checkout", "thanh toán", "đặt", "đơn hàng"]):
        return JsonResponse({"reply": "Bạn hãy vào trang 'Giỏ hàng' rồi bấm 'Đặt hàng'. Mình sẽ tạo đơn và lưu vào hệ thống."})

    # --- Mặc định: tìm gần đúng theo tên/ mô tả ---
    qs = _get_products(q=message, category="all", sort="new")[:3]
    products = list(qs)
    if products:
        p = products[0]
        return JsonResponse(
            {"reply": f"Mình tìm thấy: {p.name} ({p.price:,.0f} đ). Bạn muốn thêm món này không?"}.replace(",", ".")
        )

    return JsonResponse({"reply": "Mình chưa hiểu. Bạn có thể hỏi: 'Menu đồ uống', 'Tìm phở', hoặc 'Giỏ hàng của tôi'."})

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            return render(request, "login.html", {"error": "Sai tài khoản hoặc mật khẩu"})

    return render(request, "login.html")


def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        if password != confirm:
            return render(request, "register.html", {"error": "Mật khẩu không khớp"})

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Tài khoản đã tồn tại"})

        User.objects.create_user(username=username, password=password)

        return redirect("login")

    return render(request, "register.html")


def user_logout(request):
    logout(request)
    return redirect("index")