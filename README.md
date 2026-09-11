# SHESTAR — Django Real Store · Personalized Edition

نسخه فارسی RTL فروشگاه **SHESTAR** برای فروش پوشاک اورجینال Multi-brand. نام **SHESTAR**، نام Brandها و Product nameهای انگلیسی بدون ترجمه اجباری نمایش داده می‌شوند.

## تغییرات نسخه شخصی‌سازی‌شده

- استفاده از لوگوی واقعی `SHESTAR / she` در Header، Drawer، Footer و Favicon
- پالت رنگی برگرفته از لوگو: Burgundy + Pink + Cream
- منوی کشویی از **گوشه سمت راست** روی موبایل، تبلت و دسکتاپ
- دسته‌بندی‌های فعلی:
  - کیف و کلاه — `Bags & Hats`
  - پیراهن — `Dresses`
  - شلوارک و دامن — `Shorts & Skirts`
  - کراپ و تیشرت — `Crops & T-shirts`
- صفحه اصلی Photo-led با عکس‌های SHESTAR
- Responsive polish برای عرض‌های حدود 320px تا مانیتورهای Wide
- Header اختصاصی موبایل با Menu سمت راست، Logo وسط و Cart سمت چپ
- Safe-area برای iPhone و Bottom Navigation موبایل
- Grid تطبیقی محصولات: 2 ستون موبایل، 3 ستون تبلت، 4 ستون دسکتاپ

## امکانات فروشگاهی

- Django 5.x + Python
- PostgreSQL-ready برای Production و SQLite برای توسعه محلی
- مدیریت Brand، Product، Price، Product Code، SKU، عکس، وضعیت و موجودی از `/admin/`
- چند عکس برای هر Product
- موجودی جداگانه برای هر Size
- Cart واقعی مبتنی بر Django Session
- جلوگیری از خرید بیشتر از موجودی
- Search و Filter بر اساس Brand، Category، Price و Availability
- Coupon
- Checkout با نام، موبایل، استان، شهر، آدرس و کد پستی
- روش ارسال و محاسبه Shipping fee
- ثبت Order واقعی در Database
- کاهش خودکار Stock بعد از ثبت سفارش
- Order Tracking با شماره سفارش + موبایل
- Card-to-card + Upload payment receipt
- مدیریت وضعیت سفارش و Tracking code از Admin
- Gunicorn + WhiteNoise برای Deployment

## نکته مهم درباره Brand محصولات دمو

عکس‌های دمو از محتوای SHESTAR هستند اما تا وقتی Brand دقیق هر لباس تایید نشده، عمداً با Brand `DEMO` ساخته می‌شوند. قبل از Publish کردن فروشگاه، برای هر Product موارد زیر را واقعی وارد کن:

- Brand
- Product name
- Brand Product Code / SKU
- Price
- Size & Stock
- Source URL در صورت وجود
- عکس‌های محصول

## اجرا روی Windows

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py manage.py migrate
py manage.py seed_demo
py manage.py createsuperuser
py manage.py runserver
```

## اجرا روی macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

سایت محلی:

```text
http://127.0.0.1:8000/
```

Admin:

```text
http://127.0.0.1:8000/admin/
```

## تست روی گوشی داخل یک Wi-Fi

روی کامپیوتر:

```bash
python manage.py runserver 0.0.0.0:8000
```

بعد IP کامپیوتر را در `DJANGO_ALLOWED_HOSTS` اضافه کن و روی گوشی آدرس زیر را باز کن:

```text
http://IP-OF-COMPUTER:8000
```

## فایل‌های مهم

- `shop/templates/shop/base.html` — Header / Drawer / Footer
- `shop/templates/shop/home.html` — Homepage شخصی‌سازی‌شده
- `shop/static/shop/css/site.css` — Responsive UI
- `shop/static/shop/js/site.js` — Menu / Cart UI / Interaction
- `shop/static/shop/images/shestar-logo.webp` — لوگوی فعلی
- `shop/models.py` — Product / Brand / Order / Inventory
- `shop/admin.py` — پنل مدیریت
- `shop/management/commands/seed_demo.py` — Demo data

## Production

برای انتشار عمومی، `DJANGO_DEBUG=0`، یک `DJANGO_SECRET_KEY` امن، دامنه در `DJANGO_ALLOWED_HOSTS` و `DATABASE_URL` مربوط به PostgreSQL را در Environment Variables تنظیم کن. برای فایل‌های Media در Production بهتر است Object Storage استفاده شود.

## پنل مدیریت ساده‌تر (نسخه جدید)

پنل `/admin/` در این نسخه برای استفاده روزمره فروشگاه بازطراحی شده است:

- داشبورد با میانبرهای بزرگ برای «محصول جدید»، محصولات، سفارش‌ها، Brandها و کدهای تخفیف
- فرم محصول مرحله‌بندی شده؛ بخش‌های فنی و کم‌استفاده به صورت جمع‌شونده هستند
- سایز و موجودی و گالری عکس داخل همان صفحه محصول مدیریت می‌شوند
- روی موبایل هم پنل مدیریت چیدمان ساده‌تر و دکمه‌های Save بزرگ‌تر دارد
- لینک «مشاهده فروشگاه» همیشه بالای پنل مدیریت قرار دارد

### ویرایش نوشته‌های سایت توسط مدیریت اصلی

فقط Superuser دو بخش حساس زیر را می‌بیند:

1. **محتوای صفحه اصلی**: Hero، مزیت‌ها، عنوان دسته‌بندی، جدیدها، THE SHESTAR EDIT، Brandها، WHY SHESTAR، Instagram banner، Footer و SEO.
2. **تنظیمات فروشگاه**: هزینه ارسال، مرجوعی، شماره پشتیبانی، Instagram، اطلاعات کارت به کارت و متن ضمانت اصالت.

پس از اجرای migration، کافی است از پنل مدیریت وارد «محتوای صفحه اصلی» شوید و متن را Save کنید؛ تغییر بلافاصله در سایت دیده می‌شود.

بعد از دریافت این نسخه حتما یک بار اجرا کنید:

```bash
python manage.py migrate
```


## خواندن و فهمیدن کد
فایل `CODE_MAP_FA.md` نقشه ساده کل پروژه است. داخل فایل‌های مهم Python، HTML،
CSS و JavaScript هم توضیحات اضافه شده.

## WebP
تصاویر ثابت و Demo پروژه WebP شده‌اند و عکس‌های جدید Product/Gallery که از
Admin آپلود می‌شوند نیز خودکار WebP می‌شوند.
