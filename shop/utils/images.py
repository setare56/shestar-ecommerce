"""
Image helpers for SHESTAR.

Product photos are usually the heaviest files in a fashion store.
This helper lets the admin upload JPG/PNG normally, then converts the file
to WebP automatically before Django stores it.

Keeping this logic here avoids cluttering models.py with Pillow details.
"""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def convert_field_image_to_webp(instance, field_name, *, quality=82):
    """
    Convert one Django ImageField to WebP.

    ``instance`` is a model instance such as Product.
    ``field_name`` is usually "image".
    ``quality`` controls the size/quality tradeoff.

    The function quietly returns if there is no image, the file is already
    WebP, or Pillow cannot open it. Image optimization should never stop the
    owner from saving a product.
    """
    field_file = getattr(instance, field_name, None)
    if not field_file:
        return

    current_name = getattr(field_file, "name", "") or ""
    if current_name.lower().endswith(".webp"):
        return

    try:
        field_file.open("rb")
        image = Image.open(field_file)
    except Exception:
        return

    # Correct rotation from phone-camera EXIF metadata.
    image = ImageOps.exif_transpose(image)

    # Keep transparency only when the source actually needs it.
    has_alpha = "A" in image.getbands()
    image = image.convert("RGBA" if has_alpha else "RGB")

    output = BytesIO()
    image.save(
        output,
        format="WEBP",
        quality=quality,
        method=6,
        optimize=True,
    )
    output.seek(0)

    new_name = f"{Path(current_name).stem}.webp"
    getattr(instance, field_name).save(
        new_name,
        ContentFile(output.read()),
        save=False,
    )
