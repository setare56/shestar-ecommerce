"""Basic smoke tests for the storefront's core purchase flow.

Run with: python manage.py test
"""

from django.test import Client, TestCase
from django.urls import reverse
from .models import Brand, Order, Product, ProductVariant

class StoreFlowTests(TestCase):
    def setUp(self):
        """One brand, one product, one size with 2 in stock - enough to
        exercise add-to-cart and checkout."""
        self.client = Client()
        brand = Brand.objects.create(name="TestBrand", slug="testbrand")
        product = Product.objects.create(brand=brand, title="Test Top", slug="test-top", category="tops", price=1000000)
        self.variant = ProductVariant.objects.create(product=product, size="M", stock=2)

    def test_cart_add_and_checkout_order(self):
        """Adding 1 to cart then completing checkout should create exactly
        one Order and decrement stock by the quantity ordered."""
        response = self.client.post(reverse("shop:cart_add"), {"variant_id": self.variant.id, "quantity": 1})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("shop:checkout"), {
            "customer_name":"Test User","mobile":"09121234567","email":"","province":"تهران","city":"تهران",
            "address":"آدرس تست","postal_code":"1234567890","shipping_method":"standard",
            "payment_method":"card_transfer","notes":"","terms":"on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)

    def test_cannot_oversell(self):
        """Requesting more than available stock (3 of 2) must be rejected
        and leave the cart empty rather than allowing an overselling line item."""
        response = self.client.post(reverse("shop:cart_add"), {"variant_id": self.variant.id, "quantity": 3})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get("shestar_cart"))
