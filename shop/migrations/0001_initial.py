from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Brand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True, verbose_name="نام برند")),
                ("slug", models.SlugField(max_length=90, unique=True, verbose_name="شناسه")),
                ("display_order", models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")),
                ("active", models.BooleanField(default=True, verbose_name="فعال")),
            ],
            options={"verbose_name": "برند", "verbose_name_plural": "برندها", "ordering": ["display_order", "name"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="نام محصول")),
                ("slug", models.SlugField(blank=True, max_length=200, unique=True, verbose_name="شناسه")),
                ("category", models.CharField(choices=[("tops", "تاپ و بلوز"), ("sets", "ست"), ("bottoms", "دامن و شلوار"), ("accessories", "اکسسوری")], max_length=20, verbose_name="دسته بندی")),
                ("status", models.CharField(choices=[("new", "نو"), ("outlet", "اوتلت"), ("preorder", "پیش سفارش")], default="new", max_length=20, verbose_name="وضعیت")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                ("sku", models.CharField(blank=True, max_length=80, verbose_name="کد محصول / SKU")),
                ("price", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="قیمت به تومان")),
                ("price_note", models.CharField(blank=True, default="قیمت در دایرکت", max_length=100, verbose_name="متن قیمت")),
                ("image", models.FileField(blank=True, upload_to="products/", verbose_name="عکس اصلی")),
                ("original_guarantee", models.BooleanField(default=True, verbose_name="تضمین اصالت")),
                ("is_featured", models.BooleanField(default=False, verbose_name="ویژه")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="shop.brand", verbose_name="برند")),
            ],
            options={"verbose_name": "محصول", "verbose_name_plural": "محصولات", "ordering": ["-is_featured", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("size", models.CharField(max_length=30, verbose_name="سایز")),
                ("stock", models.PositiveIntegerField(default=1, verbose_name="موجودی")),
                ("active", models.BooleanField(default=True, verbose_name="فعال")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="variants", to="shop.product", verbose_name="محصول")),
            ],
            options={"verbose_name": "سایز / موجودی", "verbose_name_plural": "سایزها و موجودی", "ordering": ["id"]},
        ),
        migrations.AddConstraint(
            model_name="productvariant",
            constraint=models.UniqueConstraint(fields=("product", "size"), name="unique_product_size"),
        ),
    ]
