"""App config for the shop app - registers it with Django and sets its
display name (used in the admin sidebar)."""

from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"
    verbose_name = "فروشگاه SHESTAR"
