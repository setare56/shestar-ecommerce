# نقشه کد SHESTAR

## ظاهر سایت
- `shop/templates/shop/` — HTML صفحه‌ها
- `shop/static/shop/css/site.css` — ظاهر، رنگ و Responsive
- `shop/static/shop/js/site.js` — منوی کشویی و رفتار مرورگر

## منطق فروشگاه
- `shop/models.py` — دیتابیس
- `shop/views.py` — منطق صفحه‌ها
- `shop/forms.py` — فرم‌ها
- `shop/cart.py` — سبد خرید
- `shop/urls.py` — URLها

## پنل مدیریت
- `shop/admin.py` — تنظیمات `/admin/`

## عکس‌ها
عکس‌های ثابت در `shop/static/shop/images/` همگی WebP هستند.

مدیر می‌تواند JPG/PNG آپلود کند؛ `shop/utils/images.py` آن را قبل از ذخیره
خودکار WebP می‌کند:
- Product/Gallery: quality 84
- Payment receipt: quality 90

## قانون ساده
- models = چه اطلاعاتی داریم
- views = با آن اطلاعات چه کار می‌کنیم
- templates = چه چیزی نمایش می‌دهیم
- CSS = چه شکلی نمایش می‌دهیم
- admin = مدیر چطور داده‌ها را مدیریت می‌کند
