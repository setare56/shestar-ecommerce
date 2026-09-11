"""
Small values made globally available to templates, such as store settings and
cart information.
"""

from .cart import cart_snapshot
from .models import HomePageContent, Product, SiteSetting


def storefront(request):
    """Registered in settings.py's TEMPLATES so every template can use
    {{ global_cart_count }}, {{ site_settings }}, {{ home_content }} and
    {{ categories }} without each view having to pass them explicitly -
    handy since the header/footer (cart badge, contact info, nav) appear
    on every single page.
    """
    snapshot = cart_snapshot(request)
    return {
        "global_cart_count": snapshot["count"],
        "site_settings": SiteSetting.load(),
        "home_content": HomePageContent.load(),
        "categories": Product.CATEGORY_CHOICES,
    }
