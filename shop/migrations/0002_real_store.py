from django.db import migrations, models
import django.db.models.deletion
import shop.models


def fill_null_prices(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.filter(price__isnull=True).update(price=0)


class Migration(migrations.Migration):
    dependencies = [("shop", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="brand",
            name="description",
            field=models.TextField(blank=True, verbose_name="توضیح کوتاه"),
        ),
        migrations.AddField(
            model_name="brand",
            name="website",
            field=models.URLField(blank=True, verbose_name="وب سایت رسمی"),
        ),
        migrations.RunPython(fill_null_prices, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.PositiveBigIntegerField(default=0, verbose_name="قیمت به تومان"),
        ),
        migrations.AlterField(
            model_name="product",
            name="price_note",
            field=models.CharField(blank=True, max_length=100, verbose_name="یادداشت قیمت"),
        ),
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.ImageField(blank=True, upload_to="products/", verbose_name="عکس اصلی"),
        ),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.CharField(
                choices=[
                    ("tops", "تاپ و تیشرت"), ("shirts", "شومیز و پیراهن"), ("knitwear", "بافت و سویشرت"),
                    ("dresses", "پیراهن و لباس"), ("sets", "ست"), ("bottoms", "شلوار و دامن"),
                    ("outerwear", "کت و کاپشن"), ("shoes", "کفش"), ("bags", "کیف"), ("accessories", "اکسسوری"),
                ],
                max_length=20,
                verbose_name="دسته بندی",
            ),
        ),
        migrations.AddField(model_name="product", name="brand_product_code", field=models.CharField(blank=True, max_length=100, verbose_name="کد محصول برند")),
        migrations.AddField(model_name="product", name="source_url", field=models.URLField(blank=True, verbose_name="لینک مرجع / صفحه رسمی محصول")),
        migrations.AddField(model_name="product", name="color", field=models.CharField(blank=True, max_length=80, verbose_name="رنگ")),
        migrations.AddField(model_name="product", name="material", field=models.CharField(blank=True, max_length=180, verbose_name="جنس")),
        migrations.AddField(model_name="product", name="fit", field=models.CharField(blank=True, max_length=120, verbose_name="فیت")),
        migrations.AddField(model_name="product", name="care", field=models.TextField(blank=True, verbose_name="راهنمای شستشو")),
        migrations.AddField(model_name="product", name="compare_at_price", field=models.PositiveBigIntegerField(blank=True, null=True, verbose_name="قیمت قبل از تخفیف")),
        migrations.AddField(model_name="product", name="is_new", field=models.BooleanField(default=True, verbose_name="جدید")),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["is_active", "category"], name="shop_prod_active_cat")),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["is_active", "created_at"], name="shop_prod_active_created")),
        migrations.CreateModel(
            name="ProductImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="products/gallery/", verbose_name="تصویر")),
                ("alt_text", models.CharField(blank=True, max_length=180, verbose_name="متن جایگزین")),
                ("display_order", models.PositiveIntegerField(default=0, verbose_name="ترتیب")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="shop.product", verbose_name="محصول")),
            ],
            options={"verbose_name": "تصویر محصول", "verbose_name_plural": "تصاویر محصول", "ordering": ["display_order", "id"]},
        ),
        migrations.CreateModel(
            name="Coupon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=40, unique=True, verbose_name="کد تخفیف")),
                ("discount_type", models.CharField(choices=[("percent", "درصدی"), ("fixed", "مبلغ ثابت")], default="percent", max_length=10, verbose_name="نوع تخفیف")),
                ("value", models.PositiveBigIntegerField(default=0, verbose_name="مقدار")),
                ("min_order_amount", models.PositiveBigIntegerField(default=0, verbose_name="حداقل مبلغ سفارش")),
                ("max_discount_amount", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="سقف تخفیف")),
                ("starts_at", models.DateTimeField(blank=True, null=True, verbose_name="شروع")),
                ("ends_at", models.DateTimeField(blank=True, null=True, verbose_name="پایان")),
                ("usage_limit", models.PositiveIntegerField(blank=True, null=True, verbose_name="سقف استفاده")),
                ("used_count", models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده")),
                ("active", models.BooleanField(default=True, verbose_name="فعال")),
            ],
            options={"verbose_name": "کد تخفیف", "verbose_name_plural": "کدهای تخفیف"},
        ),
        migrations.CreateModel(
            name="SiteSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("shop_name", models.CharField(default="SHESTAR", max_length=100, verbose_name="نام فروشگاه")),
                ("instagram_url", models.URLField(default="https://www.instagram.com/shestar.collection/", verbose_name="لینک اینستاگرام")),
                ("support_phone", models.CharField(blank=True, max_length=30, verbose_name="شماره پشتیبانی")),
                ("support_hours", models.CharField(blank=True, max_length=120, verbose_name="ساعات پشتیبانی")),
                ("standard_shipping_fee", models.PositiveBigIntegerField(default=0, verbose_name="هزینه ارسال عادی")),
                ("express_shipping_fee", models.PositiveBigIntegerField(default=0, verbose_name="هزینه ارسال سریع")),
                ("free_shipping_threshold", models.PositiveBigIntegerField(default=0, verbose_name="ارسال رایگان از مبلغ")),
                ("bank_name", models.CharField(blank=True, max_length=80, verbose_name="نام بانک")),
                ("card_holder", models.CharField(blank=True, max_length=120, verbose_name="نام صاحب کارت")),
                ("card_number", models.CharField(blank=True, max_length=30, verbose_name="شماره کارت")),
                ("authenticity_text", models.TextField(default="تمام محصولات با نام و کد واقعی برند ثبت می‌شوند و SHESTAR کالای فیک یا دوپ عرضه نمی‌کند.", verbose_name="متن ضمانت اصالت")),
                ("return_days", models.PositiveSmallIntegerField(default=7, verbose_name="مهلت درخواست مرجوعی (روز)")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "تنظیمات فروشگاه", "verbose_name_plural": "تنظیمات فروشگاه"},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(default=shop.models.generate_order_number, editable=False, max_length=24, unique=True, verbose_name="شماره سفارش")),
                ("customer_name", models.CharField(max_length=140, verbose_name="نام و نام خانوادگی")),
                ("mobile", models.CharField(db_index=True, max_length=20, verbose_name="شماره موبایل")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="ایمیل")),
                ("province", models.CharField(max_length=80, verbose_name="استان")),
                ("city", models.CharField(max_length=80, verbose_name="شهر")),
                ("address", models.TextField(verbose_name="آدرس")),
                ("postal_code", models.CharField(blank=True, max_length=20, verbose_name="کد پستی")),
                ("notes", models.TextField(blank=True, verbose_name="توضیحات مشتری")),
                ("shipping_method", models.CharField(choices=[("standard", "ارسال عادی"), ("express", "ارسال سریع / هماهنگی")], default="standard", max_length=20, verbose_name="روش ارسال")),
                ("payment_method", models.CharField(choices=[("card_transfer", "کارت به کارت"), ("instagram", "هماهنگی پرداخت در اینستاگرام")], default="card_transfer", max_length=24, verbose_name="روش پرداخت")),
                ("subtotal", models.PositiveBigIntegerField(default=0, verbose_name="جمع کالاها")),
                ("discount_amount", models.PositiveBigIntegerField(default=0, verbose_name="تخفیف")),
                ("shipping_fee", models.PositiveBigIntegerField(default=0, verbose_name="هزینه ارسال")),
                ("total", models.PositiveBigIntegerField(default=0, verbose_name="مبلغ نهایی")),
                ("status", models.CharField(choices=[("pending_payment", "در انتظار پرداخت"), ("payment_review", "در انتظار تایید پرداخت"), ("paid", "پرداخت تایید شده"), ("preparing", "در حال آماده سازی"), ("shipped", "ارسال شده"), ("delivered", "تحویل شده"), ("cancelled", "لغو شده")], db_index=True, default="pending_payment", max_length=24, verbose_name="وضعیت")),
                ("parcel_tracking_code", models.CharField(blank=True, max_length=120, verbose_name="کد رهگیری مرسوله")),
                ("stock_released", models.BooleanField(default=False, verbose_name="موجودی پس از لغو برگشت داده شده")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")),
                ("paid_at", models.DateTimeField(blank=True, null=True, verbose_name="زمان تایید پرداخت")),
                ("coupon", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="shop.coupon", verbose_name="کد تخفیف")),
            ],
            options={"verbose_name": "سفارش", "verbose_name_plural": "سفارش ها", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["order_number", "mobile"], name="shop_order_num_mobile")),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("brand_name", models.CharField(max_length=100, verbose_name="برند")),
                ("product_title", models.CharField(max_length=200, verbose_name="نام محصول")),
                ("sku", models.CharField(blank=True, max_length=100, verbose_name="کد محصول")),
                ("size", models.CharField(max_length=40, verbose_name="سایز")),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="تعداد")),
                ("unit_price", models.PositiveBigIntegerField(default=0, verbose_name="قیمت واحد")),
                ("line_total", models.PositiveBigIntegerField(default=0, verbose_name="جمع")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shop.order", verbose_name="سفارش")),
                ("product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_items", to="shop.product", verbose_name="محصول")),
                ("variant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_items", to="shop.productvariant", verbose_name="واریانت")),
            ],
            options={"verbose_name": "آیتم سفارش", "verbose_name_plural": "آیتم های سفارش"},
        ),
        migrations.CreateModel(
            name="PaymentReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="receipts/%Y/%m/", verbose_name="تصویر رسید")),
                ("note", models.CharField(blank=True, max_length=240, verbose_name="توضیح")),
                ("status", models.CharField(choices=[("pending", "در انتظار بررسی"), ("accepted", "تایید شده"), ("rejected", "رد شده")], default="pending", max_length=12, verbose_name="وضعیت")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="receipts", to="shop.order", verbose_name="سفارش")),
            ],
            options={"verbose_name": "رسید پرداخت", "verbose_name_plural": "رسیدهای پرداخت", "ordering": ["-uploaded_at"]},
        ),
    ]
