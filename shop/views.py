"""
Views connect browser requests to database data and HTML templates.

Typical flow:
request -> query models -> prepare context -> render template

Filtering, checkout, order tracking and cart actions mostly live here.
"""

import json
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .cart import cart_snapshot, clear_cart, get_cart, get_coupon, money, save_cart, set_coupon
from .forms import CheckoutForm, ReceiptUploadForm, TrackOrderForm
from .models import (
    Brand,
    Coupon,
    Order,
    OrderItem,
    PaymentReceipt,
    Product,
    ProductVariant,
    SiteSetting,
)


# ---------------------------------------------------------------------------
# Small helpers shared by several views below
# ---------------------------------------------------------------------------

def _categories():
    """Shortcut for the category dropdown/filter options."""
    return Product.CATEGORY_CHOICES


def _wants_json(request):
    """True if the client is calling us as an API (fetch/AJAX) rather than
    a normal browser page load, so we know whether to return JSON or a
    redirect + flash message.
    """
    return "application/json" in request.headers.get("Content-Type", "") or request.headers.get("Accept") == "application/json"


def _payload(request):
    """Read request body as either JSON (for fetch/AJAX calls) or a normal
    POST form, so cart endpoints work with both.
    """
    if "application/json" in request.headers.get("Content-Type", ""):
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


def _safe_next(request, default="shop:cart_page"):
    """Where to redirect after a cart action. Only allows relative,
    same-site paths (must start with a single '/') to avoid an open
    redirect if someone tampers with the 'next' parameter.
    """
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return reverse(default)


def _shipping_fee(setting, method, merchandise_total):
    """Shipping cost for an order: free above the store's threshold,
    otherwise the standard or express flat fee from SiteSetting.
    """
    if setting.free_shipping_threshold and merchandise_total >= setting.free_shipping_threshold:
        return 0
    if method == Order.SHIPPING_EXPRESS:
        return setting.express_shipping_fee
    return setting.standard_shipping_fee


# ---------------------------------------------------------------------------
# HOMEPAGE
# ---------------------------------------------------------------------------
@ensure_csrf_cookie
def home(request):
    """Storefront homepage: hero product, a few featured items, newest
    arrivals, and the active brand list.
    """
    base = (
        Product.objects.filter(is_active=True, brand__active=True)
        .select_related("brand")
        .prefetch_related("variants", "images")
    )
    featured = list(base.filter(is_featured=True)[:4])
    hero_product = featured[0] if featured else base.first()
    new_products = list(base.filter(is_new=True).order_by("-created_at")[:8])
    if not new_products:
        new_products = list(base[:8])
    brands = Brand.objects.filter(active=True).order_by("display_order", "name")
    return render(request, "shop/home.html", {
        "hero_product": hero_product,
        "featured_products": featured[1:4],
        "new_products": new_products,
        "brands": brands,
        "categories": _categories(),
    })


# ---------------------------------------------------------------------------
# SHOP / FILTERING
# ---------------------------------------------------------------------------
@ensure_csrf_cookie
def shop_list(request):
    """Product listing page with search, brand/category/price filters,
    an "in stock only" toggle, sorting, and pagination - all driven by
    query-string parameters so filtered views are shareable/bookmarkable.
    """
    products = (
        Product.objects.filter(is_active=True, brand__active=True)
        .select_related("brand")
        .prefetch_related("variants")
    )

    q = request.GET.get("q", "").strip()
    brand = request.GET.get("brand", "").strip()
    category = request.GET.get("category", "").strip()
    available = request.GET.get("available", "").strip()
    sort = request.GET.get("sort", "newest")

    if q:
        products = products.filter(
            Q(title__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(sku__icontains=q)
            | Q(brand_product_code__icontains=q)
            | Q(color__icontains=q)
        )
    if brand:
        products = products.filter(brand__slug=brand)
    if category:
        products = products.filter(category=category)
    if available == "1":
        products = products.filter(variants__active=True, variants__stock__gt=0).distinct()

    try:
        min_price = int(request.GET.get("min_price", "") or 0)
    except ValueError:
        min_price = 0
    try:
        max_price = int(request.GET.get("max_price", "") or 0)
    except ValueError:
        max_price = 0
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    sort_map = {
        "newest": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "brand": "brand__name",
    }
    products = products.order_by(sort_map.get(sort, "-created_at"))

    paginator = Paginator(products, 16)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(request, "shop/shop.html", {
        "page_obj": page_obj,
        "brands": Brand.objects.filter(active=True).order_by("display_order", "name"),
        "categories": _categories(),
        "selected": {
            "q": q,
            "brand": brand,
            "category": category,
            "available": available,
            "min_price": min_price or "",
            "max_price": max_price or "",
            "sort": sort,
        },
        "querystring": query_params.urlencode(),
    })


# ---------------------------------------------------------------------------
# PRODUCT DETAIL
# ---------------------------------------------------------------------------
@ensure_csrf_cookie
def product_detail(request, slug):
    """Single product page, plus up to 4 related products from the same
    category to encourage further browsing.
    """
    product = get_object_or_404(
        Product.objects.select_related("brand").prefetch_related("variants", "images"),
        slug=slug,
        is_active=True,
        brand__active=True,
    )
    related = (
        Product.objects.filter(is_active=True, category=product.category, brand__active=True)
        .exclude(pk=product.pk)
        .select_related("brand")
        .prefetch_related("variants")[:4]
    )
    return render(request, "shop/product_detail.html", {
        "product": product,
        "variants": product.variants.filter(active=True).order_by("id"),
        "related_products": related,
    })


# ---------------------------------------------------------------------------
# CART
# The cart itself is stored in the session (see cart.py). These views are
# thin wrappers that validate the request, mutate the session cart, then
# respond either as a redirect+flash-message (normal form post) or JSON
# (fetch/AJAX call) depending on _wants_json().
# ---------------------------------------------------------------------------

def cart_page(request):
    """Full cart page (as opposed to the JSON snapshot used by the mini-cart)."""
    return render(request, "shop/cart.html", {"cart": cart_snapshot(request)})


@require_GET
def cart_detail(request):
    """JSON snapshot of the current cart - used to refresh the mini-cart
    widget without a full page reload.
    """
    return JsonResponse(cart_snapshot(request))


@require_POST
def cart_add(request):
    """Add a size/variant to the cart, checking stock along the way."""
    data = _payload(request)
    try:
        variant_id = int(data.get("variant_id"))
        quantity = max(1, int(data.get("quantity", 1)))
    except (TypeError, ValueError):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "سایز را انتخاب کنید."}, status=400)
        messages.error(request, "لطفاً سایز محصول را انتخاب کنید.")
        return redirect(_safe_next(request, "shop:shop_list"))

    try:
        variant = ProductVariant.objects.select_related("product", "product__brand").get(
            id=variant_id,
            active=True,
            product__is_active=True,
            product__brand__active=True,
        )
    except ProductVariant.DoesNotExist:
        error = "این سایز در دسترس نیست."
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": error}, status=404)
        messages.error(request, error)
        return redirect(_safe_next(request, "shop:shop_list"))

    if variant.stock < 1:
        error = "این سایز تمام شده است."
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": error}, status=409)
        messages.error(request, error)
        return redirect(_safe_next(request, "shop:shop_list"))

    cart = get_cart(request)
    key = str(variant.id)
    current = int(cart.get(key, 0))
    new_qty = current + quantity
    if new_qty > variant.stock:
        error = f"از این سایز فقط {variant.stock} عدد موجود است."
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": error}, status=409)
        messages.error(request, error)
        return redirect(_safe_next(request, "shop:cart_page"))

    cart[key] = new_qty
    save_cart(request, cart)
    snapshot = cart_snapshot(request)
    if _wants_json(request):
        snapshot["ok"] = True
        return JsonResponse(snapshot)
    messages.success(request, "محصول به سبد خرید اضافه شد.")
    return redirect(_safe_next(request, "shop:cart_page"))


@require_POST
def cart_update(request):
    """Change a cart line's quantity (or remove it, if set to 0)."""
    data = _payload(request)
    try:
        variant_id = int(data.get("variant_id"))
        quantity = max(0, int(data.get("quantity", 0)))
    except (TypeError, ValueError):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "درخواست نامعتبر است."}, status=400)
        return redirect("shop:cart_page")

    cart = get_cart(request)
    key = str(variant_id)
    if quantity == 0:
        cart.pop(key, None)
    else:
        variant = ProductVariant.objects.filter(pk=variant_id, active=True).first()
        if not variant or variant.stock < quantity:
            error = "تعداد انتخاب شده بیشتر از موجودی است."
            if _wants_json(request):
                return JsonResponse({"ok": False, "error": error}, status=409)
            messages.error(request, error)
            return redirect("shop:cart_page")
        cart[key] = quantity
    save_cart(request, cart)
    snapshot = cart_snapshot(request)
    if _wants_json(request):
        snapshot["ok"] = True
        return JsonResponse(snapshot)
    return redirect("shop:cart_page")


@require_POST
def cart_remove(request):
    """Remove one line entirely from the cart."""
    data = _payload(request)
    try:
        variant_id = str(int(data.get("variant_id")))
    except (TypeError, ValueError):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "درخواست نامعتبر است."}, status=400)
        return redirect("shop:cart_page")
    cart = get_cart(request)
    cart.pop(variant_id, None)
    save_cart(request, cart)
    snapshot = cart_snapshot(request)
    if _wants_json(request):
        snapshot["ok"] = True
        return JsonResponse(snapshot)
    return redirect("shop:cart_page")


@require_POST
def cart_clear(request):
    """Empty the whole cart."""
    clear_cart(request)
    if _wants_json(request):
        return JsonResponse({"ok": True, "items": [], "count": 0})
    return redirect("shop:cart_page")


@require_POST
def coupon_apply(request):
    """Attach (or, with an empty code, remove) a discount coupon to the
    session. Validity/eligibility is re-checked again at checkout time,
    since stock and prices can change between now and then.
    """
    code = (_payload(request).get("code") or "").strip().upper()
    if not code:
        set_coupon(request, None)
        messages.info(request, "کد تخفیف حذف شد.")
        return redirect("shop:cart_page")

    snapshot = cart_snapshot(request)
    coupon = Coupon.objects.filter(code__iexact=code, active=True).first()
    if not coupon or not coupon.is_valid(snapshot["subtotal"]):
        messages.error(request, "این کد تخفیف معتبر نیست یا شرایط استفاده از آن برقرار نیست.")
        return redirect("shop:cart_page")
    set_coupon(request, coupon.code)
    messages.success(request, "کد تخفیف اعمال شد.")
    return redirect("shop:cart_page")


# ---------------------------------------------------------------------------
# CHECKOUT
# ---------------------------------------------------------------------------
@ensure_csrf_cookie
def checkout(request):
    """Checkout page: shows the form on GET, and on a valid POST turns the
    session cart into a real Order (+ OrderItems) and decrements stock.

    Runs inside a DB transaction with select_for_update() to lock the
    relevant ProductVariant rows, so two customers checking out at the
    same moment can't both oversell the last unit of a size.
    """
    snapshot = cart_snapshot(request)
    if not snapshot["items"]:
        messages.info(request, "سبد خرید شما خالی است.")
        return redirect("shop:shop_list")
    if not snapshot["can_checkout"]:
        messages.error(request, "برای یکی از محصولات قیمت نهایی ثبت نشده و امکان پرداخت آنلاین سفارش وجود ندارد.")
        return redirect("shop:cart_page")

    setting = SiteSetting.load()
    form = CheckoutForm(request.POST or None)
    selected_shipping = request.POST.get("shipping_method", Order.SHIPPING_STANDARD)
    shipping_fee_preview = _shipping_fee(setting, selected_shipping, snapshot["total_after_discount"])
    grand_total_preview = snapshot["total_after_discount"] + shipping_fee_preview

    if request.method == "POST" and form.is_valid():
        cart = get_cart(request)
        variant_ids = []
        for raw_id in cart.keys():
            try:
                variant_ids.append(int(raw_id))
            except (TypeError, ValueError):
                pass

        with transaction.atomic():
            # Lock these rows for the duration of the transaction so stock
            # counts can't change underneath us while we validate + commit.
            variants = (
                ProductVariant.objects.select_for_update()
                .filter(id__in=variant_ids, active=True, product__is_active=True, product__brand__active=True)
                .select_related("product", "product__brand")
            )
            by_id = {v.id: v for v in variants}
            order_rows = []  # (variant, quantity, unit_price) validated so far
            subtotal = 0
            for raw_id, raw_qty in cart.items():
                try:
                    variant_id = int(raw_id)
                    qty = max(1, int(raw_qty))
                except (TypeError, ValueError):
                    continue
                variant = by_id.get(variant_id)
                if not variant or variant.stock < qty:
                    form.add_error(None, "موجودی یکی از محصولات تغییر کرده است. لطفاً سبد خرید را دوباره بررسی کنید.")
                    break
                unit_price = int(variant.product.price or 0)
                if unit_price <= 0:
                    form.add_error(None, f"قیمت {variant.product.title} هنوز نهایی نشده است.")
                    break
                subtotal += unit_price * qty
                order_rows.append((variant, qty, unit_price))

            if not form.errors and order_rows:
                # Re-validate the coupon against the final subtotal (it may
                # have expired or hit its usage cap since it was applied).
                coupon = get_coupon(request, subtotal)
                discount = coupon.discount_for(subtotal) if coupon else 0
                merchandise_total = max(0, subtotal - discount)
                shipping_fee = _shipping_fee(setting, form.cleaned_data["shipping_method"], merchandise_total)
                total = merchandise_total + shipping_fee

                order = Order.objects.create(
                    customer_name=form.cleaned_data["customer_name"],
                    mobile=form.cleaned_data["mobile"],
                    email=form.cleaned_data["email"],
                    province=form.cleaned_data["province"],
                    city=form.cleaned_data["city"],
                    address=form.cleaned_data["address"],
                    postal_code=form.cleaned_data["postal_code"],
                    notes=form.cleaned_data["notes"],
                    shipping_method=form.cleaned_data["shipping_method"],
                    payment_method=form.cleaned_data["payment_method"],
                    coupon=coupon,
                    subtotal=subtotal,
                    discount_amount=discount,
                    shipping_fee=shipping_fee,
                    total=total,
                )

                for variant, qty, unit_price in order_rows:
                    product = variant.product
                    # Snapshot brand/title/sku/price onto the order line so
                    # this receipt stays accurate even if the product record
                    # changes or is deleted later.
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        variant=variant,
                        brand_name=product.brand.name,
                        product_title=product.title,
                        sku=product.brand_product_code or product.sku,
                        size=variant.size,
                        quantity=qty,
                        unit_price=unit_price,
                        line_total=unit_price * qty,
                    )
                    variant.stock -= qty
                    variant.save(update_fields=["stock"])

                if coupon:
                    Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)

                clear_cart(request)
                request.session["last_order_number"] = order.order_number
                request.session.modified = True
                return redirect("shop:order_success", order_number=order.order_number)

    return render(request, "shop/checkout.html", {
        "form": form,
        "cart": snapshot,
        "shipping_fee_preview": shipping_fee_preview,
        "grand_total_preview": grand_total_preview,
        "setting": setting,
    })


def order_success(request, order_number):
    """Order confirmation page, shown right after checkout.

    Gated on a session flag (`last_order_number`) rather than just the
    order number in the URL, so a stranger can't view someone else's
    order by guessing/incrementing the order number.
    """
    if request.session.get("last_order_number") != order_number:
        messages.info(request, "برای مشاهده سفارش، شماره سفارش و موبایل را در بخش پیگیری وارد کنید.")
        return redirect("shop:track_order")
    order = get_object_or_404(Order.objects.prefetch_related("items", "receipts"), order_number=order_number)
    receipt_form = ReceiptUploadForm()
    return render(request, "shop/order_success.html", {
        "order": order,
        "receipt_form": receipt_form,
        "setting": SiteSetting.load(),
    })


# ---------------------------------------------------------------------------
# ORDER TRACKING
# ---------------------------------------------------------------------------
def track_order(request):
    """Let a customer look up their order with order number + mobile
    number (no account/login system in this store).
    """
    order = None
    receipt_form = ReceiptUploadForm()
    form = TrackOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = (
            Order.objects.filter(
                order_number__iexact=form.cleaned_data["order_number"],
                mobile=form.cleaned_data["mobile"],
            )
            .prefetch_related("items", "receipts")
            .first()
        )
        if not order:
            form.add_error(None, "سفارشی با این شماره سفارش و موبایل پیدا نشد.")
        else:
            request.session["last_order_number"] = order.order_number
    return render(request, "shop/track_order.html", {
        "form": form,
        "order": order,
        "receipt_form": receipt_form,
        "setting": SiteSetting.load(),
    })


@require_POST
def receipt_upload(request, order_number):
    """Accept a card-to-card payment screenshot for an order.

    Access is allowed either via the post-checkout session flag, or by
    re-submitting the matching mobile number (covers the "track order"
    flow, where there's no session flag from checkout).
    """
    order = get_object_or_404(Order, order_number=order_number)
    session_authorized = request.session.get("last_order_number") == order.order_number
    posted_mobile = (request.POST.get("mobile") or "").strip()
    if not session_authorized and posted_mobile != order.mobile:
        messages.error(request, "برای ارسال رسید ابتدا سفارش را پیگیری کنید.")
        return redirect("shop:track_order")

    form = ReceiptUploadForm(request.POST, request.FILES)
    if form.is_valid():
        receipt = form.save(commit=False)
        receipt.order = order
        receipt.save()
        if order.status == Order.STATUS_PENDING_PAYMENT:
            order.status = Order.STATUS_PAYMENT_REVIEW
            order.save(update_fields=["status", "updated_at"])
        messages.success(request, "رسید پرداخت ثبت شد و برای بررسی مدیریت ارسال شد.")
    else:
        messages.error(request, "تصویر رسید معتبر نیست یا حجم آن بیشتر از حد مجاز است.")

    if session_authorized:
        return redirect("shop:order_success", order_number=order.order_number)
    params = urlencode({"order": order.order_number})
    return redirect(f"{reverse('shop:track_order')}?{params}")


# ---------------------------------------------------------------------------
# STATIC INFO PAGES
# Content for these lives here in code rather than the database, since it
# changes rarely and doesn't need a store-staff editing UI.
# ---------------------------------------------------------------------------
INFO_PAGES = {
    "authenticity": {
        "title": "ضمانت اصالت کالا",
        "lead": "SHESTAR فقط محصولات اصلی برندها را عرضه می کند و هر کالا با اطلاعات واقعی خودش ثبت می شود.",
        "sections": [
            ("کد و مشخصات واقعی", "نام برند، کد محصول برند، رنگ، سایز و وضعیت کالا در صفحه محصول درج می شود. در صورت وجود، لینک مرجع رسمی برند هم قابل ثبت است."),
            ("بدون فیک و دوپ", "محصولی که اصالت آن برای فروشگاه قابل تایید نباشد نباید با نام برند در سایت منتشر شود."),
            ("سوال قبل از خرید", "اگر درباره کد محصول، لیبل یا جزئیات اصالت سوال دارید، قبل از ثبت سفارش از پشتیبانی بپرسید."),
        ],
    },
    "shipping": {
        "title": "ارسال و تحویل",
        "lead": "روش و هزینه ارسال در مرحله ثبت سفارش به شکل شفاف نمایش داده می شود.",
        "sections": [
            ("ارسال عادی", "برای سفارش های سراسر ایران قابل انتخاب است. مبلغ دقیق را مدیریت فروشگاه از پنل تنظیم می کند."),
            ("ارسال سریع", "برای مواردی که امکان ارسال سریع وجود دارد انتخاب می شود و ممکن است نیاز به هماهنگی با پشتیبانی داشته باشد."),
            ("کد رهگیری", "بعد از ارسال، کد رهگیری مرسوله از پنل مدیریت روی سفارش ثبت می شود و مشتری آن را در صفحه پیگیری می بیند."),
        ],
    },
    "returns": {
        "title": "تعویض و مرجوعی",
        "lead": "شرایط نهایی مرجوعی باید متناسب با سیاست واقعی فروشگاه در پنل و متن سایت تنظیم شود.",
        "sections": [
            ("قبل از استفاده", "کالا باید استفاده نشده باشد و تگ، بسته بندی و متعلقات آن حفظ شده باشد."),
            ("سایز", "برای پوشاک، قبل از خرید جدول سایز و اندازه های محصول را بررسی کنید. شرایط تعویض سایز به موجودی بستگی دارد."),
            ("ثبت درخواست", "برای درخواست مرجوعی شماره سفارش را همراه با توضیح مشکل برای پشتیبانی ارسال کنید."),
        ],
    },
    "faq": {
        "title": "سوالات متداول",
        "lead": "پاسخ کوتاه به سوال هایی که مشتری قبل از خرید معمولاً دارد.",
        "sections": [
            ("محصولات اصل هستند؟", "بله؛ سیاست فروشگاه عرضه محصول اصلی است. در سایت برای هر آیتم برند و کد واقعی ثبت می شود."),
            ("چطور سفارشم را پیگیری کنم؟", "از صفحه پیگیری سفارش، شماره سفارش و شماره موبایلی که هنگام خرید وارد کرده اید را ثبت کنید."),
            ("چطور رسید پرداخت بفرستم؟", "بعد از ثبت سفارش کارت به کارت، از همان صفحه تایید یا صفحه پیگیری می توانید تصویر رسید را آپلود کنید."),
        ],
    },
    "about": {
        "title": "درباره SHESTAR",
        "lead": "SHESTAR یک فروشگاه مستقل برای انتخاب و عرضه پوشاک اورجینال برندهای مختلف است.",
        "sections": [
            ("فروشگاه مستقل", "SHESTAR نماینده رسمی برندهای نمایش داده شده نیست، مگر جایی که به طور مشخص و مستند اعلام شود."),
            ("انتخاب محصول", "تمرکز فروشگاه روی آیتم های قابل پوشیدن، ترند و قابل ست کردن از برندهای مختلف است."),
            ("ارتباط", "برای سوال های قبل از خرید می توانید از اینستاگرام یا راه ارتباطی ثبت شده در سایت استفاده کنید."),
        ],
    },
}


def info_page(request, slug):
    """Render one of the static pages above (authenticity, shipping, etc)."""
    page = INFO_PAGES.get(slug)
    if not page:
        return redirect("shop:home")
    return render(request, "shop/info_page.html", {"page": page, "slug": slug})


@require_GET
def health(request):
    """Simple uptime check for hosting platforms / monitoring."""
    return JsonResponse({"ok": True, "service": "shestar"})
