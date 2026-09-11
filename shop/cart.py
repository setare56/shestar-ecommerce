"""
Session-based shopping cart logic.

This file stores selected variants/quantities in the Django session and
calculates cart values.
"""

from .models import Coupon, ProductVariant

CART_SESSION_KEY = "shestar_cart"
COUPON_SESSION_KEY = "shestar_coupon"


def money(value):
    """Format an integer تومان amount with thousands separators, e.g. '250,000 تومان'."""
    return f"{int(value):,} تومان"


def get_cart(request):
    """Raw cart dict from the session: {variant_id (str): quantity (int)}."""
    return request.session.get(CART_SESSION_KEY, {})


def save_cart(request, cart):
    """Write the cart back to the session, dropping any zero/negative
    quantities and normalizing keys to strings (session data is JSON, so
    dict keys always round-trip as strings anyway).
    """
    cleaned = {str(k): max(0, int(v)) for k, v in cart.items() if int(v) > 0}
    request.session[CART_SESSION_KEY] = cleaned
    request.session.modified = True


def clear_cart(request):
    """Empty the cart and drop any applied coupon."""
    request.session.pop(CART_SESSION_KEY, None)
    request.session.pop(COUPON_SESSION_KEY, None)
    request.session.modified = True


def set_coupon(request, code):
    """Store (or, with a falsy code, remove) the applied coupon code on the session."""
    if code:
        request.session[COUPON_SESSION_KEY] = code.strip().upper()
    else:
        request.session.pop(COUPON_SESSION_KEY, None)
    request.session.modified = True


def get_coupon(request, subtotal=0):
    """The currently applied Coupon object, or None if there isn't one or
    it's no longer valid for the given subtotal (expired, over its usage
    limit, below its minimum order amount, etc).
    """
    code = request.session.get(COUPON_SESSION_KEY)
    if not code:
        return None
    coupon = Coupon.objects.filter(code__iexact=code, active=True).first()
    if not coupon or not coupon.is_valid(subtotal):
        return None
    return coupon


def cart_snapshot(request):
    """Build the full cart view used by templates and the JSON cart API:
    resolves each line to its live Product/ProductVariant, recalculates
    prices and totals, clamps quantities down to current stock, and
    silently drops lines for products that were deleted/deactivated.

    As a side effect, re-saves the cart if anything had to be clamped or
    dropped, so the session stays in sync with what's actually available.
    """
    cart = get_cart(request)
    if not cart:
        return {
            "items": [], "count": 0, "subtotal": 0, "discount": 0, "total_after_discount": 0,
            "subtotal_display": money(0), "discount_display": money(0), "total_after_discount_display": money(0),
            "coupon": None, "can_checkout": False,
        }

    valid_ids = []
    for raw_id in cart.keys():
        try:
            valid_ids.append(int(raw_id))
        except (TypeError, ValueError):
            pass

    variants = (
        ProductVariant.objects
        .filter(id__in=valid_ids, active=True, product__is_active=True, product__brand__active=True)
        .select_related("product", "product__brand")
    )
    by_id = {v.id: v for v in variants}
    items = []
    total_count = 0
    subtotal = 0
    normalized_cart = {}
    can_checkout = True

    for raw_id, raw_qty in cart.items():
        try:
            variant_id = int(raw_id)
            qty = max(1, int(raw_qty))
        except (TypeError, ValueError):
            continue
        variant = by_id.get(variant_id)
        if not variant or variant.stock < 1:
            continue
        qty = min(qty, variant.stock)
        normalized_cart[str(variant_id)] = qty
        product = variant.product
        unit_price = int(product.price or 0)
        if unit_price <= 0:
            can_checkout = False
        line_total = unit_price * qty
        subtotal += line_total
        total_count += qty
        items.append({
            "variant_id": variant.id,
            "product_id": product.id,
            "product_url": product.get_absolute_url(),
            "brand": product.brand.name,
            "title": product.title,
            "size": variant.size,
            "quantity": qty,
            "stock": variant.stock,
            "unit_price": unit_price,
            "unit_price_display": money(unit_price),
            "line_total": line_total,
            "line_total_display": money(line_total),
            "image": product.image.url if product.image else "",
        })

    if normalized_cart != cart:
        save_cart(request, normalized_cart)

    coupon = get_coupon(request, subtotal)
    discount = coupon.discount_for(subtotal) if coupon else 0
    total_after_discount = max(0, subtotal - discount)
    return {
        "items": items,
        "count": total_count,
        "subtotal": subtotal,
        "discount": discount,
        "total_after_discount": total_after_discount,
        "subtotal_display": money(subtotal),
        "discount_display": money(discount),
        "total_after_discount_display": money(total_after_discount),
        "coupon": coupon.code if coupon else None,
        "can_checkout": bool(items) and can_checkout,
    }
