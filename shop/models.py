"""
Database models for the SHESTAR online shop.

READING MAP
-----------
1. Brand            -> fashion brand information
2. Product          -> product information, price, main image
3. ProductImage     -> extra gallery images
4. ProductVariant   -> size + stock
5. Coupon           -> discount codes
6. SiteSetting      -> owner-controlled global shop settings
7. HomePageContent  -> owner-editable homepage text
8. Order            -> customer order
9. OrderItem        -> products inside an order
10. PaymentReceipt  -> card-to-card payment proof

Rule of thumb:
- Change DATA structure here.
- Change page DESIGN in templates/CSS.
- Change admin presentation in admin.py.
"""

import secrets
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

# Image optimization is isolated in a helper to keep this file readable.
from .utils.images import convert_field_image_to_webp


def generate_order_number():
    """Build a human-friendly order number like 'SH-260912-483920'.

    Format: SH-<YYMMDD>-<6 random digits>. Not guaranteed unique on its own,
    but the Order.order_number field is unique=True so a collision would
    raise an IntegrityError (astronomically unlikely at this volume).
    """
    stamp = timezone.localtime().strftime("%y%m%d")
    return f"SH-{stamp}-{secrets.randbelow(900000) + 100000}"


# ============================================================================
# 1) BRANDS
# ============================================================================
class Brand(models.Model):
    """A fashion brand carried by the store (e.g. Nike, Zara).

    Field labels below are in Persian since that's what shows up in the
    Django admin, which store staff use day-to-day.
    """
    name = models.CharField("نام برند", max_length=80, unique=True)
    slug = models.SlugField("شناسه", max_length=90, unique=True)
    description = models.TextField("توضیح کوتاه", blank=True)
    website = models.URLField("وب سایت رسمی", blank=True)
    display_order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "برند"
        verbose_name_plural = "برندها"

    def __str__(self):
        return self.name


# ============================================================================
# 2) PRODUCTS
# ============================================================================
class Product(models.Model):
    """A single item for sale: one brand, one title, one price, one main image.

    Sizes and per-size stock live separately on ProductVariant (a Product
    can have several sizes, each with its own stock count).
    """
    # دسته بندی های فعلی SHESTAR. نام برندها و نام های محصول می توانند انگلیسی بمانند.
    CATEGORY_BAGS_HATS = "bags-hats"
    CATEGORY_DRESSES = "dresses"
    CATEGORY_SKIRTS_SHORTS = "skirts-shorts"
    CATEGORY_CROPS_TEES = "crops-tees"
    CATEGORY_CHOICES = [
        (CATEGORY_BAGS_HATS, "کیف و کلاه"),
        (CATEGORY_DRESSES, "پیراهن"),
        (CATEGORY_SKIRTS_SHORTS, "شلوارک و دامن"),
        (CATEGORY_CROPS_TEES, "کراپ و تیشرت"),
    ]

    STATUS_NEW = "new"
    STATUS_OUTLET = "outlet"
    STATUS_PREORDER = "preorder"
    STATUS_CHOICES = [
        (STATUS_NEW, "نو"),
        (STATUS_OUTLET, "اوتلت"),
        (STATUS_PREORDER, "پیش سفارش"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products", verbose_name="برند")
    title = models.CharField("نام محصول", max_length=180)
    slug = models.SlugField("شناسه", max_length=200, unique=True, blank=True)
    category = models.CharField("دسته بندی", max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    description = models.TextField("توضیحات", blank=True)
    sku = models.CharField("کد داخلی / SKU", max_length=80, blank=True)
    brand_product_code = models.CharField("کد محصول برند", max_length=100, blank=True)
    source_url = models.URLField("لینک مرجع / صفحه رسمی محصول", blank=True)
    color = models.CharField("رنگ", max_length=80, blank=True)
    material = models.CharField("جنس", max_length=180, blank=True)
    fit = models.CharField("فیت", max_length=120, blank=True)
    care = models.TextField("راهنمای شستشو", blank=True)
    price = models.PositiveBigIntegerField("قیمت به تومان", default=0)
    compare_at_price = models.PositiveBigIntegerField("قیمت قبل از تخفیف", null=True, blank=True)
    price_note = models.CharField("یادداشت قیمت", max_length=100, blank=True)
    image = models.ImageField("عکس اصلی", upload_to="products/", blank=True)
    original_guarantee = models.BooleanField("تضمین اصالت", default=True)
    is_new = models.BooleanField("جدید", default=True)
    is_featured = models.BooleanField("ویژه", default=False)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        indexes = [
            models.Index(fields=["is_active", "category"], name="shop_prod_active_cat"),
            models.Index(fields=["is_active", "created_at"], name="shop_prod_active_created"),
        ]

    def save(self, *args, **kwargs):
        """Prepare a product before saving it to the database."""

        # Slug = readable URL part, e.g. /product/polka-dot-top/
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "product"
            slug = base
            n = 2
            while Product.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        # The admin can upload JPG/PNG normally.
        # We store WebP automatically to keep the storefront lighter.
        convert_field_image_to_webp(self, "image", quality=84)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand.name} — {self.title}"

    def get_absolute_url(self):
        return reverse("shop:product_detail", kwargs={"slug": self.slug})

    @property
    def display_price(self):
        """Price formatted for the storefront, e.g. '1,250,000 تومان'."""
        if self.price:
            return f"{self.price:,} تومان"
        return self.price_note or "برای قیمت تماس بگیرید"

    @property
    def display_compare_price(self):
        """Formatted 'was' price, shown struck-through next to a sale price."""
        if self.compare_at_price and self.compare_at_price > self.price:
            return f"{self.compare_at_price:,} تومان"
        return ""

    @property
    def discount_percent(self):
        """Whole-number discount badge, e.g. 20 for a 20% markdown."""
        if self.compare_at_price and self.compare_at_price > self.price > 0:
            return round((self.compare_at_price - self.price) * 100 / self.compare_at_price)
        return 0

    @property
    def available_sizes(self):
        """Sizes that are both enabled and actually in stock."""
        return self.variants.filter(active=True, stock__gt=0)

    @property
    def total_stock(self):
        """Sum of stock across all active size variants."""
        return sum(v.stock for v in self.variants.all() if v.active)

    @property
    def in_stock(self):
        """True if at least one active size variant has stock left."""
        return any(v.active and v.stock > 0 for v in self.variants.all())


# ============================================================================
# 3) PRODUCT GALLERY IMAGES
# ============================================================================
class ProductImage(models.Model):
    """Extra gallery photos for a product, beyond its main `image`."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="محصول")
    image = models.ImageField("تصویر", upload_to="products/gallery/")
    alt_text = models.CharField("متن جایگزین", max_length=180, blank=True)
    display_order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"

    def save(self, *args, **kwargs):
        """Optimize gallery photos automatically."""
        convert_field_image_to_webp(self, "image", quality=84)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"تصویر {self.product.title}"


# ============================================================================
# 4) SIZE + STOCK
# ============================================================================
class ProductVariant(models.Model):
    """One purchasable size of a product, with its own stock count.

    A (product, size) pair is unique - see the UniqueConstraint below.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants", verbose_name="محصول")
    size = models.CharField("سایز", max_length=30)
    stock = models.PositiveIntegerField("موجودی", default=1)
    active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["product", "size"], name="unique_product_size")]
        verbose_name = "سایز / موجودی"
        verbose_name_plural = "سایزها و موجودی"

    def __str__(self):
        return f"{self.product.title} / {self.size}"


# ============================================================================
# 5) DISCOUNT CODES
# ============================================================================
class Coupon(models.Model):
    """A discount code, either a flat percentage or a fixed تومان amount off."""
    TYPE_PERCENT = "percent"
    TYPE_FIXED = "fixed"
    TYPE_CHOICES = [(TYPE_PERCENT, "درصدی"), (TYPE_FIXED, "مبلغ ثابت")]

    code = models.CharField("کد تخفیف", max_length=40, unique=True)
    discount_type = models.CharField("نوع تخفیف", max_length=10, choices=TYPE_CHOICES, default=TYPE_PERCENT)
    value = models.PositiveBigIntegerField("مقدار", default=0)
    min_order_amount = models.PositiveBigIntegerField("حداقل مبلغ سفارش", default=0)
    max_discount_amount = models.PositiveBigIntegerField("سقف تخفیف", null=True, blank=True)
    starts_at = models.DateTimeField("شروع", null=True, blank=True)
    ends_at = models.DateTimeField("پایان", null=True, blank=True)
    usage_limit = models.PositiveIntegerField("سقف استفاده", null=True, blank=True)
    used_count = models.PositiveIntegerField("تعداد استفاده", default=0)
    active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return self.code

    def is_valid(self, subtotal=0):
        """Check the coupon against the "is it usable at all" rules:
        active flag, date window, usage cap, and minimum order size.
        Does not calculate the discount amount - see discount_for().
        """
        now = timezone.now()
        if not self.active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        if subtotal < self.min_order_amount:
            return False
        return True

    def discount_for(self, subtotal):
        """Compute the تومان discount for a given cart subtotal.

        Returns 0 if the coupon isn't valid for this subtotal. Otherwise
        applies the percent/fixed value, then clamps to max_discount_amount
        and to the subtotal itself (a coupon can never make the total negative).
        """
        if not self.is_valid(subtotal):
            return 0
        if self.discount_type == self.TYPE_PERCENT:
            discount = subtotal * min(self.value, 100) // 100
        else:
            discount = min(self.value, subtotal)
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        return max(0, min(discount, subtotal))


# ============================================================================
# 6) GLOBAL STORE SETTINGS
# ============================================================================
class SiteSetting(models.Model):
    """Singleton (always pk=1) holding store-wide settings: shipping fees,
    bank card info for card-to-card payment, return policy, etc.
    Use SiteSetting.load() to fetch (or auto-create) the single row.
    """
    shop_name = models.CharField("نام فروشگاه", max_length=100, default="SHESTAR")
    instagram_url = models.URLField("لینک اینستاگرام", default="https://www.instagram.com/shestar.collection/")
    support_phone = models.CharField("شماره پشتیبانی", max_length=30, blank=True)
    support_hours = models.CharField("ساعات پشتیبانی", max_length=120, blank=True)
    standard_shipping_fee = models.PositiveBigIntegerField("هزینه ارسال عادی", default=0)
    express_shipping_fee = models.PositiveBigIntegerField("هزینه ارسال سریع", default=0)
    free_shipping_threshold = models.PositiveBigIntegerField("ارسال رایگان از مبلغ", default=0)
    bank_name = models.CharField("نام بانک", max_length=80, blank=True)
    card_holder = models.CharField("نام صاحب کارت", max_length=120, blank=True)
    card_number = models.CharField("شماره کارت", max_length=30, blank=True)
    authenticity_text = models.TextField(
        "متن ضمانت اصالت",
        default="تمام محصولات با نام و کد واقعی برند ثبت می‌شوند و SHESTAR کالای فیک یا دوپ عرضه نمی‌کند.",
    )
    return_days = models.PositiveSmallIntegerField("مهلت درخواست مرجوعی (روز)", default=7)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات فروشگاه"
        verbose_name_plural = "تنظیمات فروشگاه"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "تنظیمات SHESTAR"


# ============================================================================
# 7) EDITABLE HOMEPAGE CONTENT
# ============================================================================
class HomePageContent(models.Model):
    """Editable storefront copy for the main page. Singleton and superuser-only in admin."""
    announcement_text = models.CharField("نوار بالای سایت", max_length=180, default="ضمانت اصالت کالا • ارسال به سراسر ایران • پیگیری سفارش")
    hero_kicker = models.CharField("تیتر کوچک Hero", max_length=160, default="SHESTAR COLLECTION · ORIGINAL BRAND FASHION")
    hero_title = models.CharField("عنوان اصلی Hero", max_length=220, default="استایل‌هایی که دلت می‌خواد بپوشی.")
    hero_text = models.TextField("متن Hero", default="انتخاب آیتم‌های اورجینال از Brandهای مختلف؛ با سایز و موجودی واقعی، قیمت شفاف و امکان ثبت و پیگیری سفارش از خود سایت.")
    hero_primary_button = models.CharField("متن دکمه اصلی Hero", max_length=80, default="شروع خرید")
    hero_secondary_button = models.CharField("متن دکمه دوم Hero", max_length=80, default="Instagram ↗")

    promise_1_title = models.CharField("مزیت ۱ - عنوان", max_length=80, default="اورجینال")
    promise_1_text = models.CharField("مزیت ۱ - توضیح", max_length=140, default="بدون فیک و Dupe")
    promise_2_title = models.CharField("مزیت ۲ - عنوان", max_length=80, default="شفاف")
    promise_2_text = models.CharField("مزیت ۲ - توضیح", max_length=140, default="قیمت، سایز و موجودی واقعی")
    promise_3_title = models.CharField("مزیت ۳ - عنوان", max_length=80, default="قابل پیگیری")
    promise_3_text = models.CharField("مزیت ۳ - توضیح", max_length=140, default="از ثبت تا ارسال")

    category_kicker = models.CharField("دسته‌بندی - تیتر کوچک", max_length=100, default="SHOP BY CATEGORY")
    category_title = models.CharField("دسته‌بندی - عنوان", max_length=100, default="دسته‌بندی‌ها")
    new_kicker = models.CharField("جدیدها - تیتر کوچک", max_length=100, default="JUST IN")
    new_title = models.CharField("جدیدها - عنوان", max_length=100, default="جدیدها")

    lookbook_kicker = models.CharField("Lookbook - تیتر کوچک", max_length=100, default="THE SHESTAR EDIT")
    lookbook_title = models.CharField("Lookbook - عنوان", max_length=180, default="از Instagram تا سبد خرید.")
    lookbook_text = models.TextField("Lookbook - متن", default="عکس‌های واقعی استایل و محصول می‌توانند کنار عکس رسمی Brand روی صفحه محصول قرار بگیرند تا مشتری دقیق‌تر انتخاب کند.")
    lookbook_button = models.CharField("Lookbook - متن دکمه", max_length=80, default="دیدن Instagram")

    brands_kicker = models.CharField("Brandها - تیتر کوچک", max_length=100, default="MULTI-BRAND")
    brands_title = models.CharField("Brandها - عنوان", max_length=100, default="Brandها")
    brands_disclaimer = models.TextField("متن زیر Brandها", default="SHESTAR یک فروشگاه مستقل Multi-brand است و نمایش نام Brand به معنی نمایندگی رسمی آن Brand نیست.")

    why_kicker = models.CharField("Why SHESTAR - تیتر کوچک", max_length=100, default="WHY SHESTAR")
    why_title = models.CharField("Why SHESTAR - عنوان", max_length=180, default="اصل بودن فقط یک جمله نیست.")
    instagram_handle = models.CharField("Instagram handle", max_length=80, default="@SHESTAR.COLLECTION")
    instagram_title = models.CharField("Instagram banner - عنوان", max_length=180, default="Dropهای جدید را از دست نده.")

    footer_about = models.TextField("متن معرفی Footer", default="فروشگاه مستقل پوشاک اورجینال از Brandهای مختلف. نام و علائم تجاری هر Brand متعلق به صاحب همان Brand است.")
    footer_shop_heading = models.CharField("عنوان ستون خرید Footer", max_length=60, default="خرید")
    footer_help_heading = models.CharField("عنوان ستون راهنما Footer", max_length=60, default="راهنما")
    footer_about_heading = models.CharField("عنوان ستون درباره Footer", max_length=60, default="درباره")
    footer_bottom_text = models.CharField("متن پایین Footer", max_length=160, default="Independent multi-brand retailer")

    meta_title = models.CharField("SEO - عنوان صفحه اصلی", max_length=180, default="SHESTAR | Original Brand Fashion")
    meta_description = models.CharField("SEO - توضیحات صفحه اصلی", max_length=300, default="فروش آنلاین پوشاک اورجینال برندهای مختلف با نمایش موجودی، سایز، ثبت سفارش و پیگیری سفارش.")
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "محتوای صفحه اصلی"
        verbose_name_plural = "محتوای صفحه اصلی"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "ویرایش محتوای صفحه اصلی SHESTAR"


# ============================================================================
# 8) ORDERS
# ============================================================================
class Order(models.Model):
    """A customer order, from checkout through delivery or cancellation.

    Holds a snapshot of totals (subtotal/discount/shipping/total) computed
    at checkout time - these don't recalculate later even if product
    prices change, so past orders stay accurate.
    """
    STATUS_PENDING_PAYMENT = "pending_payment"
    STATUS_PAYMENT_REVIEW = "payment_review"
    STATUS_PAID = "paid"
    STATUS_PREPARING = "preparing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, "در انتظار پرداخت"),
        (STATUS_PAYMENT_REVIEW, "در انتظار تایید پرداخت"),
        (STATUS_PAID, "پرداخت تایید شده"),
        (STATUS_PREPARING, "در حال آماده سازی"),
        (STATUS_SHIPPED, "ارسال شده"),
        (STATUS_DELIVERED, "تحویل شده"),
        (STATUS_CANCELLED, "لغو شده"),
    ]

    SHIPPING_STANDARD = "standard"
    SHIPPING_EXPRESS = "express"
    SHIPPING_CHOICES = [
        (SHIPPING_STANDARD, "ارسال عادی"),
        (SHIPPING_EXPRESS, "ارسال سریع / هماهنگی"),
    ]

    PAYMENT_CARD = "card_transfer"
    PAYMENT_INSTAGRAM = "instagram"
    PAYMENT_CHOICES = [
        (PAYMENT_CARD, "کارت به کارت"),
        (PAYMENT_INSTAGRAM, "هماهنگی پرداخت در اینستاگرام"),
    ]

    order_number = models.CharField("شماره سفارش", max_length=24, unique=True, default=generate_order_number, editable=False)
    customer_name = models.CharField("نام و نام خانوادگی", max_length=140)
    mobile = models.CharField("شماره موبایل", max_length=20, db_index=True)
    email = models.EmailField("ایمیل", blank=True)
    province = models.CharField("استان", max_length=80)
    city = models.CharField("شهر", max_length=80)
    address = models.TextField("آدرس")
    postal_code = models.CharField("کد پستی", max_length=20, blank=True)
    notes = models.TextField("توضیحات مشتری", blank=True)
    shipping_method = models.CharField("روش ارسال", max_length=20, choices=SHIPPING_CHOICES, default=SHIPPING_STANDARD)
    payment_method = models.CharField("روش پرداخت", max_length=24, choices=PAYMENT_CHOICES, default=PAYMENT_CARD)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders", verbose_name="کد تخفیف")
    subtotal = models.PositiveBigIntegerField("جمع کالاها", default=0)
    discount_amount = models.PositiveBigIntegerField("تخفیف", default=0)
    shipping_fee = models.PositiveBigIntegerField("هزینه ارسال", default=0)
    total = models.PositiveBigIntegerField("مبلغ نهایی", default=0)
    status = models.CharField("وضعیت", max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT, db_index=True)
    parcel_tracking_code = models.CharField("کد رهگیری مرسوله", max_length=120, blank=True)
    stock_released = models.BooleanField("موجودی پس از لغو برگشت داده شده", default=False)
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)
    paid_at = models.DateTimeField("زمان تایید پرداخت", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش ها"
        indexes = [models.Index(fields=["order_number", "mobile"], name="shop_order_num_mobile")]

    def __str__(self):
        return f"{self.order_number} — {self.customer_name}"

    @property
    def display_total(self):
        return f"{self.total:,} تومان"

    @property
    def display_subtotal(self):
        return f"{self.subtotal:,} تومان"

    def release_stock(self):
        """Put reserved stock back (e.g. when an order is cancelled).

        Idempotent via the `stock_released` flag, so calling this twice on
        the same order won't double-credit the stock back.
        Uses F() to increment in the database directly and avoid a
        read-then-write race if two requests run at the same time.
        """
        if self.stock_released:
            return
        for item in self.items.select_related("variant"):
            if item.variant_id:
                ProductVariant.objects.filter(pk=item.variant_id).update(stock=models.F("stock") + item.quantity)
        self.stock_released = True
        self.save(update_fields=["stock_released", "updated_at"])


# ============================================================================
# 9) ORDER ITEMS
# ============================================================================
class OrderItem(models.Model):
    """One product line within an Order.

    Brand/title/sku/price are copied from the Product at checkout time
    (rather than always looked up live) so the order stays an accurate
    receipt even if the product is later edited or deleted.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="سفارش")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items", verbose_name="محصول")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items", verbose_name="واریانت")
    brand_name = models.CharField("برند", max_length=100)
    product_title = models.CharField("نام محصول", max_length=200)
    sku = models.CharField("کد محصول", max_length=100, blank=True)
    size = models.CharField("سایز", max_length=40)
    quantity = models.PositiveIntegerField("تعداد", default=1)
    unit_price = models.PositiveBigIntegerField("قیمت واحد", default=0)
    line_total = models.PositiveBigIntegerField("جمع", default=0)

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم های سفارش"

    def __str__(self):
        return f"{self.order.order_number} / {self.product_title}"


# ============================================================================
# 10) PAYMENT RECEIPTS
# ============================================================================
class PaymentReceipt(models.Model):
    """A screenshot/photo the customer uploads as proof of a card-to-card
    transfer, which store staff then review and accept or reject.
    """
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار بررسی"),
        (STATUS_ACCEPTED, "تایید شده"),
        (STATUS_REJECTED, "رد شده"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="receipts", verbose_name="سفارش")
    image = models.ImageField("تصویر رسید", upload_to="receipts/%Y/%m/")
    note = models.CharField("توضیح", max_length=240, blank=True)
    status = models.CharField("وضعیت", max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    uploaded_at = models.DateTimeField("زمان ارسال", auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "رسید پرداخت"
        verbose_name_plural = "رسیدهای پرداخت"

    def save(self, *args, **kwargs):
        """Compress receipt images but keep text readable."""
        convert_field_image_to_webp(self, "image", quality=90)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"رسید {self.order.order_number}"
