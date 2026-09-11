"""Management command: `python manage.py seed_demo`

Populates a fresh install with a handful of real brand names (no products
attached) plus a small set of placeholder "DEMO" products, so the storefront
has something to look at before real inventory is entered. Safe to re-run -
uses get_or_create everywhere so it won't create duplicates.
"""

from pathlib import Path
from django.core.files import File
from django.core.management.base import BaseCommand
from shop.models import Brand, Product, ProductVariant, SiteSetting

# عکس های دمو از محتوای خود SHESTAR هستند، اما تا وقتی Brand دقیق محصول تایید نشده
# عمدا به هیچ Brand واقعی نسبت داده نمی شوند.
# (Demo photos are SHESTAR's own content, but are deliberately NOT attributed
# to any real brand until the product's actual brand has been confirmed.)
DEMO_PRODUCTS = [
    {"slug":"demo-black-mini-bag","title":"Black Mini Bag","category":"bags-hats","image":"black-bag-look.webp","sizes":["One Size"],"price":1490000},
    {"slug":"demo-printed-mini-dress","title":"Printed Mini Dress","category":"dresses","image":"printed-dress.webp","sizes":["XS","S","M","L"],"price":1690000},
    {"slug":"demo-denim-mini-skirt","title":"Denim Mini Skirt","category":"skirts-shorts","image":"polka-skirt.webp","sizes":["32","34","36","38","40"],"price":1390000},
    {"slug":"demo-polka-dot-top","title":"Polka Dot Top","category":"crops-tees","image":"polka-skirt.webp","sizes":["XS","S","M","L"],"price":990000},
    {"slug":"demo-ribbed-maxi-dress","title":"Ribbed Maxi Dress","category":"dresses","image":"maxi-dress.webp","sizes":["XS","S","M","L"],"price":1890000},
    {"slug":"demo-ivory-crop-top","title":"Ivory Crop Top","category":"crops-tees","image":"crop-look.webp","sizes":["XS","S","M","L"],"price":890000},
]


class Command(BaseCommand):
    help = "Create safe SHESTAR demo content. Photos are NOT attributed to real brands."

    def handle(self, *args, **options):
        # Real brand names, added with no products attached to them - useful
        # for the brand filter/list to look realistic without misattributing
        # any placeholder product to a brand that hasn't actually confirmed it.
        real_brands = ["SHEIN", "H&M", "Mango", "Stradivarius", "Bershka", "Nike", "Zara", "Pull&Bear"]
        for order, name in enumerate(real_brands):
            slug = name.lower().replace("&", "").replace(" ", "-")
            Brand.objects.get_or_create(name=name, defaults={"slug": slug, "display_order": order})

        demo_brand, _ = Brand.objects.get_or_create(
            name="DEMO",
            defaults={"slug":"demo","display_order":999,"description":"فقط برای پیش نمایش سایت؛ قبل از انتشار محصول واقعی، Brand دقیق را ثبت کنید."},
        )
        SiteSetting.load()
        asset_dir = Path(__file__).resolve().parents[2] / "demo_assets"
        created = 0
        for i, row in enumerate(DEMO_PRODUCTS):
            product, was_created = Product.objects.get_or_create(
                slug=row["slug"],
                defaults={
                    "brand": demo_brand,
                    "title": row["title"],
                    "category": row["category"],
                    "price": row["price"],
                    "description": "این محصول برای تست ظاهر و روند خرید سایت است. قبل از انتشار، Brand، Product Code، قیمت و موجودی واقعی را وارد کنید.",
                    "original_guarantee": False,
                    "is_featured": i < 3,
                    "is_new": True,
                },
            )
            if was_created:
                image_path = asset_dir / row["image"]
                if image_path.exists():
                    with image_path.open("rb") as fh:
                        product.image.save(row["image"], File(fh), save=True)
                created += 1
            for size in row["sizes"]:
                ProductVariant.objects.get_or_create(product=product, size=size, defaults={"stock":3})
        self.stdout.write(self.style.SUCCESS(
            f"SHESTAR demo ready: {created} products. Real Brand names were added without fake product attribution."
        ))
