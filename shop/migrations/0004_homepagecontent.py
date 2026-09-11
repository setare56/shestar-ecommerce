from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("shop", "0003_shestar_categories")]
    operations = [
        migrations.CreateModel(
            name="HomePageContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("announcement_text", models.CharField(default="ضمانت اصالت کالا • ارسال به سراسر ایران • پیگیری سفارش", max_length=180, verbose_name="نوار بالای سایت")),
                ("hero_kicker", models.CharField(default="SHESTAR COLLECTION · ORIGINAL BRAND FASHION", max_length=160, verbose_name="تیتر کوچک Hero")),
                ("hero_title", models.CharField(default="استایل‌هایی که دلت می‌خواد بپوشی.", max_length=220, verbose_name="عنوان اصلی Hero")),
                ("hero_text", models.TextField(default="انتخاب آیتم‌های اورجینال از Brandهای مختلف؛ با سایز و موجودی واقعی، قیمت شفاف و امکان ثبت و پیگیری سفارش از خود سایت.", verbose_name="متن Hero")),
                ("hero_primary_button", models.CharField(default="شروع خرید", max_length=80, verbose_name="متن دکمه اصلی Hero")),
                ("hero_secondary_button", models.CharField(default="Instagram", max_length=80, verbose_name="متن دکمه دوم Hero")),
                ("promise_1_title", models.CharField(default="اورجینال", max_length=80, verbose_name="مزیت ۱ - عنوان")),
                ("promise_1_text", models.CharField(default="بدون فیک و Dupe", max_length=140, verbose_name="مزیت ۱ - توضیح")),
                ("promise_2_title", models.CharField(default="شفاف", max_length=80, verbose_name="مزیت ۲ - عنوان")),
                ("promise_2_text", models.CharField(default="قیمت، سایز و موجودی واقعی", max_length=140, verbose_name="مزیت ۲ - توضیح")),
                ("promise_3_title", models.CharField(default="قابل پیگیری", max_length=80, verbose_name="مزیت ۳ - عنوان")),
                ("promise_3_text", models.CharField(default="از ثبت تا ارسال", max_length=140, verbose_name="مزیت ۳ - توضیح")),
                ("category_kicker", models.CharField(default="SHOP BY CATEGORY", max_length=100, verbose_name="دسته‌بندی - تیتر کوچک")),
                ("category_title", models.CharField(default="دسته‌بندی‌ها", max_length=100, verbose_name="دسته‌بندی - عنوان")),
                ("new_kicker", models.CharField(default="JUST IN", max_length=100, verbose_name="جدیدها - تیتر کوچک")),
                ("new_title", models.CharField(default="جدیدها", max_length=100, verbose_name="جدیدها - عنوان")),
                ("lookbook_kicker", models.CharField(default="THE SHESTAR EDIT", max_length=100, verbose_name="Lookbook - تیتر کوچک")),
                ("lookbook_title", models.CharField(default="از Instagram تا سبد خرید.", max_length=180, verbose_name="Lookbook - عنوان")),
                ("lookbook_text", models.TextField(default="عکس‌های واقعی استایل و محصول می‌توانند کنار عکس رسمی Brand روی صفحه محصول قرار بگیرند تا مشتری دقیق‌تر انتخاب کند.", verbose_name="Lookbook - متن")),
                ("lookbook_button", models.CharField(default="دیدن Instagram", max_length=80, verbose_name="Lookbook - متن دکمه")),
                ("brands_kicker", models.CharField(default="MULTI-BRAND", max_length=100, verbose_name="Brandها - تیتر کوچک")),
                ("brands_title", models.CharField(default="Brandها", max_length=100, verbose_name="Brandها - عنوان")),
                ("brands_disclaimer", models.TextField(default="SHESTAR یک فروشگاه مستقل Multi-brand است و نمایش نام Brand به معنی نمایندگی رسمی آن Brand نیست.", verbose_name="متن زیر Brandها")),
                ("why_kicker", models.CharField(default="WHY SHESTAR", max_length=100, verbose_name="Why SHESTAR - تیتر کوچک")),
                ("why_title", models.CharField(default="اصل بودن فقط یک جمله نیست.", max_length=180, verbose_name="Why SHESTAR - عنوان")),
                ("instagram_handle", models.CharField(default="@SHESTAR.COLLECTION", max_length=80, verbose_name="Instagram handle")),
                ("instagram_title", models.CharField(default="Dropهای جدید را از دست نده.", max_length=180, verbose_name="Instagram banner - عنوان")),
                ("footer_about", models.TextField(default="فروشگاه مستقل پوشاک اورجینال از Brandهای مختلف. نام و علائم تجاری هر Brand متعلق به صاحب همان Brand است.", verbose_name="متن معرفی Footer")),
                ("footer_shop_heading", models.CharField(default="خرید", max_length=60, verbose_name="عنوان ستون خرید Footer")),
                ("footer_help_heading", models.CharField(default="راهنما", max_length=60, verbose_name="عنوان ستون راهنما Footer")),
                ("footer_about_heading", models.CharField(default="درباره", max_length=60, verbose_name="عنوان ستون درباره Footer")),
                ("footer_bottom_text", models.CharField(default="Independent multi-brand retailer", max_length=160, verbose_name="متن پایین Footer")),
                ("meta_title", models.CharField(default="SHESTAR | Original Brand Fashion", max_length=180, verbose_name="SEO - عنوان صفحه اصلی")),
                ("meta_description", models.CharField(default="فروش آنلاین پوشاک اورجینال برندهای مختلف با نمایش موجودی، سایز، ثبت سفارش و پیگیری سفارش.", max_length=300, verbose_name="SEO - توضیحات صفحه اصلی")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")),
            ],
            options={"verbose_name": "محتوای صفحه اصلی", "verbose_name_plural": "محتوای صفحه اصلی"},
        ),
    ]
