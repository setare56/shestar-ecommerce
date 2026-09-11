"""
SHESTAR admin-panel configuration.

Change this file when you want to adjust /admin/: columns, filters, inline
stock editing, owner-only settings or order-management actions.
"""

from django.contrib import admin, messages
from django.utils import timezone
from .models import (
    Brand, Coupon, HomePageContent, Order, OrderItem, PaymentReceipt, Product, ProductImage,
    ProductVariant, SiteSetting,
)

admin.site.site_header = "مدیریت فروشگاه SHESTAR"
admin.site.site_title = "SHESTAR Admin"
admin.site.index_title = "داشبورد مدیریت"


class SingletonAdminMixin:
    """For models that should only ever have one row (SiteSetting,
    HomePageContent): hides the "add" option once a row exists, and
    disallows deleting the only row.
    """
    def has_add_permission(self, request):
        return not self.model.objects.exists() and super().has_add_permission(request)
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "active")
    list_editable = ("display_order", "active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (("اطلاعات Brand", {"fields": ("name", "slug", "description", "website", "display_order", "active")}),)


class ProductVariantInline(admin.TabularInline):
    """Lets staff add/edit a product's sizes and stock directly on the
    Product edit page, instead of needing a separate screen."""
    model = ProductVariant
    extra = 1
    min_num = 0
    verbose_name = "سایز و موجودی"
    verbose_name_plural = "سایزها و موجودی — سایز، تعداد و فعال بودن را همین‌جا وارد کنید"


class ProductImageInline(admin.TabularInline):
    """Lets staff add extra gallery photos directly on the Product edit page."""
    model = ProductImage
    extra = 1
    verbose_name = "عکس اضافه"
    verbose_name_plural = "گالری محصول — در صورت نیاز چند عکس اضافه کنید"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Main product-management screen. Numbered fieldsets (۱-۵) guide
    store staff through entering a new product top to bottom."""
    list_display = ("title", "brand", "category", "pretty_price", "stock_total", "is_new", "is_featured", "is_active")
    list_filter = ("brand", "category", "status", "is_active", "is_featured", "is_new")
    search_fields = ("title", "brand__name", "sku", "brand_product_code")
    list_editable = ("is_new", "is_featured", "is_active")
    list_per_page = 30
    autocomplete_fields = ("brand",)
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductVariantInline, ProductImageInline]
    save_on_top = True
    fieldsets = (
        ("۱) اطلاعات اصلی", {"description": "Brand، نام، دسته‌بندی و عکس اصلی را وارد کنید.", "fields": ("brand", "title", "category", "status", "image", "description")}),
        ("۲) قیمت", {"fields": ("price", "compare_at_price", "price_note")}),
        ("۳) مشخصات محصول", {"classes": ("collapse",), "fields": ("color", "material", "fit", "care")}),
        ("۴) اصالت و کدها", {"classes": ("collapse",), "fields": ("sku", "brand_product_code", "source_url", "original_guarantee")}),
        ("۵) نمایش در سایت", {"fields": ("is_new", "is_featured", "is_active")}),
        ("تنظیمات فنی", {"classes": ("collapse",), "fields": ("slug", "created_at", "updated_at")}),
    )

    @admin.display(description="قیمت")
    def pretty_price(self, obj):
        return obj.display_price

    @admin.display(description="موجودی کل")
    def stock_total(self, obj):
        return sum(v.stock for v in obj.variants.all() if v.active)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "stock", "active")
    list_filter = ("active", "product__brand")
    search_fields = ("product__title", "size")
    list_editable = ("stock", "active")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "min_order_amount", "used_count", "usage_limit", "active")
    list_filter = ("active", "discount_type")
    search_fields = ("code",)
    list_editable = ("active",)
    fieldsets = (("کد تخفیف", {"fields": ("code", "discount_type", "value", "min_order_amount", "max_discount_amount", "starts_at", "ends_at", "usage_limit", "active")}),)


class OrderItemInline(admin.TabularInline):
    """Read-only list of items within an order - line items are a snapshot
    taken at checkout and shouldn't be edited from the admin after the fact."""
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "variant", "brand_name", "product_title", "sku", "size", "quantity", "unit_price", "line_total")


class PaymentReceiptInline(admin.TabularInline):
    """Uploaded payment-proof screenshots for this order, editable so
    staff can mark them accepted/rejected."""
    model = PaymentReceipt
    extra = 0
    readonly_fields = ("uploaded_at",)


# --- Bulk order actions (shown in the "Action" dropdown on the order list) ---

@admin.action(description="✓ تایید پرداخت سفارش‌های انتخاب‌شده")
def mark_paid(modeladmin, request, queryset):
    """Mark selected orders as paid and auto-accept any pending receipts
    attached to them (skips already-cancelled orders)."""
    count = 0
    for order in queryset.exclude(status=Order.STATUS_CANCELLED):
        order.status = Order.STATUS_PAID
        order.paid_at = order.paid_at or timezone.now()
        order.save(update_fields=["status", "paid_at", "updated_at"])
        order.receipts.filter(status=PaymentReceipt.STATUS_PENDING).update(status=PaymentReceipt.STATUS_ACCEPTED)
        count += 1
    messages.success(request, f"پرداخت {count} سفارش تایید شد.")


@admin.action(description="→ انتقال به در حال آماده‌سازی")
def mark_preparing(modeladmin, request, queryset):
    """Bulk-move selected (non-cancelled) orders to 'preparing' status."""
    queryset.exclude(status=Order.STATUS_CANCELLED).update(status=Order.STATUS_PREPARING)


@admin.action(description="✕ لغو سفارش و برگرداندن موجودی")
def cancel_restore_stock(modeladmin, request, queryset):
    """Cancel selected orders and credit their reserved stock back to
    the relevant ProductVariants (via Order.release_stock, which is
    safe to call even if some orders were already cancelled/released)."""
    count = 0
    for order in queryset:
        if order.status != Order.STATUS_CANCELLED:
            order.status = Order.STATUS_CANCELLED
            order.save(update_fields=["status", "updated_at"])
        if not order.stock_released:
            order.release_stock()
        count += 1
    messages.success(request, f"{count} سفارش لغو و موجودی آن بررسی شد.")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order management screen: money fields are read-only (set once at
    checkout), with bulk actions for the common status changes."""
    list_display = ("order_number", "customer_name", "mobile", "display_total_admin", "status", "shipping_method", "created_at")
    list_filter = ("status", "shipping_method", "payment_method", "created_at")
    search_fields = ("order_number", "customer_name", "mobile", "parcel_tracking_code")
    readonly_fields = ("order_number", "subtotal", "discount_amount", "shipping_fee", "total", "created_at", "updated_at", "stock_released")
    autocomplete_fields = ("coupon",)
    inlines = [OrderItemInline, PaymentReceiptInline]
    actions = [mark_paid, mark_preparing, cancel_restore_stock]
    save_on_top = True
    fieldsets = (
        ("وضعیت سفارش", {"fields": ("order_number", "status", "parcel_tracking_code", "created_at", "updated_at")}),
        ("اطلاعات مشتری", {"fields": ("customer_name", "mobile", "email", "province", "city", "address", "postal_code", "notes")}),
        ("ارسال و پرداخت", {"fields": ("shipping_method", "payment_method", "paid_at", "coupon")}),
        ("مبالغ", {"fields": ("subtotal", "discount_amount", "shipping_fee", "total")}),
        ("تنظیمات سیستمی", {"classes": ("collapse",), "fields": ("stock_released",)}),
    )

    @admin.display(description="مبلغ")
    def display_total_admin(self, obj):
        return f"{obj.total:,} تومان"


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "uploaded_at")
    list_filter = ("status", "uploaded_at")
    search_fields = ("order__order_number", "order__mobile")
    list_editable = ("status",)


@admin.register(SiteSetting)
class SiteSettingAdmin(SingletonAdminMixin, admin.ModelAdmin):
    """Store-wide settings (shipping fees, bank card, etc). Restricted to
    superusers since it includes the bank card number for payments."""
    save_on_top = True
    fieldsets = (
        ("ارتباط با مشتری", {"fields": ("shop_name", "instagram_url", "support_phone", "support_hours")}),
        ("ارسال و مرجوعی", {"fields": ("standard_shipping_fee", "express_shipping_fee", "free_shipping_threshold", "return_days")}),
        ("پرداخت کارت به کارت", {"fields": ("bank_name", "card_holder", "card_number")}),
        ("متن ضمانت اصالت", {"fields": ("authenticity_text",)}),
    )

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)


@admin.register(HomePageContent)
class HomePageContentAdmin(SingletonAdminMixin, admin.ModelAdmin):
    """Advanced copy editor available only to the main administrator."""
    save_on_top = True
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("Hero / بخش اول صفحه", {"description": "متن‌هایی که کاربر بلافاصله بعد از ورود می‌بیند.", "fields": ("announcement_text", "hero_kicker", "hero_title", "hero_text", "hero_primary_button", "hero_secondary_button")}),
        ("سه مزیت زیر Hero", {"fields": (("promise_1_title", "promise_1_text"), ("promise_2_title", "promise_2_text"), ("promise_3_title", "promise_3_text"))}),
        ("دسته‌بندی و جدیدها", {"fields": (("category_kicker", "category_title"), ("new_kicker", "new_title"))}),
        ("THE SHESTAR EDIT", {"fields": ("lookbook_kicker", "lookbook_title", "lookbook_text", "lookbook_button")}),
        ("Brandها و Why SHESTAR", {"fields": ("brands_kicker", "brands_title", "brands_disclaimer", "why_kicker", "why_title")}),
        ("Instagram Banner", {"fields": ("instagram_handle", "instagram_title")}),
        ("Footer", {"fields": ("footer_about", "footer_shop_heading", "footer_help_heading", "footer_about_heading", "footer_bottom_text")}),
        ("SEO / Advanced", {"classes": ("collapse",), "description": "این بخش روی عنوان و توضیحات نتایج موتورهای جستجو اثر می‌گذارد.", "fields": ("meta_title", "meta_description", "updated_at")}),
    )

    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)
