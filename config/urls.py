"""Top-level URL router for the SHESTAR project."""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),      # Django admin dashboard
    path("", include("shop.urls")),       # All storefront pages (see shop/urls.py)
]

# Only serve uploaded media files (product photos, receipts) directly from
# Django when DEBUG is on. In production a real web server / CDN should
# serve MEDIA_URL instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
