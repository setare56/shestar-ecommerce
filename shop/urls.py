"""URL routes for the shop app, mounted at the site root by config/urls.py."""

from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    # Storefront pages
    path("", views.home, name="home"),
    path("shop/", views.shop_list, name="shop_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_page, name="cart_page"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<str:order_number>/", views.order_success, name="order_success"),
    path("order/track/", views.track_order, name="track_order"),
    path("order/<str:order_number>/receipt/", views.receipt_upload, name="receipt_upload"),
    path("info/<slug:slug>/", views.info_page, name="info_page"),
    path("health/", views.health, name="health"),

    # JSON endpoints used by the cart's fetch/AJAX calls
    path("api/cart/", views.cart_detail, name="cart_detail"),
    path("api/cart/add/", views.cart_add, name="cart_add"),
    path("api/cart/update/", views.cart_update, name="cart_update"),
    path("api/cart/remove/", views.cart_remove, name="cart_remove"),
    path("api/cart/clear/", views.cart_clear, name="cart_clear"),
    path("cart/coupon/", views.coupon_apply, name="coupon_apply"),
]
