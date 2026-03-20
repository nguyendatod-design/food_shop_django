# Food Shop (Django)

Demo website bán đồ ăn: menu + giỏ hàng + checkout (lưu Order vào SQLite).

## Cài đặt

```bat
cd /d d:\python\food_shop_django
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Mở trình duyệt

Truy cập: `http://127.0.0.1:8000/`

