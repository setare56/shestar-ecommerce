"""
Customer-facing Django forms.

Forms validate customer input before it is trusted or saved.
"""

import re
from django import forms
from .models import Order, PaymentReceipt

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value):
    """Convert Persian (۰-۹) and Arabic-Indic (٠-٩) digit characters to
    plain ASCII 0-9, since customers may type phone/postal numbers using
    either keyboard.
    """
    return (value or "").translate(_DIGITS)


class CheckoutForm(forms.Form):
    """Shipping address + payment/shipping method choice, filled in at checkout."""
    customer_name = forms.CharField(
        label="نام و نام خانوادگی",
        max_length=140,
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "مثلاً مریم احمدی"}),
    )
    mobile = forms.CharField(
        label="شماره موبایل",
        max_length=20,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "placeholder": "09xxxxxxxxx"}),
    )
    email = forms.EmailField(
        label="ایمیل (اختیاری)",
        required=False,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "name@example.com"}),
    )
    province = forms.CharField(label="استان", max_length=80, widget=forms.TextInput(attrs={"autocomplete": "address-level1"}))
    city = forms.CharField(label="شهر", max_length=80, widget=forms.TextInput(attrs={"autocomplete": "address-level2"}))
    address = forms.CharField(
        label="آدرس کامل",
        widget=forms.Textarea(attrs={"rows": 4, "autocomplete": "street-address", "placeholder": "خیابان، کوچه، پلاک، واحد"}),
    )
    postal_code = forms.CharField(
        label="کد پستی (اختیاری)",
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "postal-code"}),
    )
    shipping_method = forms.ChoiceField(label="روش ارسال", choices=Order.SHIPPING_CHOICES, widget=forms.RadioSelect)
    payment_method = forms.ChoiceField(label="روش پرداخت", choices=Order.PAYMENT_CHOICES, widget=forms.RadioSelect)
    notes = forms.CharField(label="توضیحات سفارش (اختیاری)", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    terms = forms.BooleanField(label="قوانین خرید و شرایط مرجوعی را خوانده و می پذیرم.")

    def clean_mobile(self):
        """Normalize to the standard 09xxxxxxxxx format, accepting inputs
        like +98..., 0098..., spaces/dashes, or Persian digits.
        """
        value = normalize_digits(self.cleaned_data["mobile"])
        value = re.sub(r"[\s\-()+]", "", value)
        if value.startswith("98") and len(value) == 12:
            value = "0" + value[2:]
        if not re.fullmatch(r"09\d{9}", value):
            raise forms.ValidationError("شماره موبایل را به شکل 09xxxxxxxxx وارد کنید.")
        return value

    def clean_postal_code(self):
        """Optional field, but if provided must be exactly 10 digits (Iran postal code)."""
        value = normalize_digits(self.cleaned_data.get("postal_code", ""))
        value = re.sub(r"\D", "", value)
        if value and len(value) != 10:
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد.")
        return value


class TrackOrderForm(forms.Form):
    """Order number + mobile number, used to look up an existing order
    (there's no customer account system, so this pair acts as the lookup key).
    """
    order_number = forms.CharField(
        label="شماره سفارش",
        max_length=24,
        widget=forms.TextInput(attrs={"placeholder": "مثلاً SH-260816-123456", "dir": "ltr"}),
    )
    mobile = forms.CharField(
        label="شماره موبایل سفارش",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "09xxxxxxxxx", "inputmode": "tel", "dir": "ltr"}),
    )

    def clean_order_number(self):
        return self.cleaned_data["order_number"].strip().upper()

    def clean_mobile(self):
        value = normalize_digits(self.cleaned_data["mobile"])
        return re.sub(r"\D", "", value)


class ReceiptUploadForm(forms.ModelForm):
    """Upload a payment-proof screenshot for card-to-card orders."""
    class Meta:
        model = PaymentReceipt
        fields = ["image", "note"]
        widgets = {"note": forms.TextInput(attrs={"placeholder": "اگر لازم است توضیح کوتاهی بنویسید"})}

    def clean_image(self):
        """Reject receipts over 5 MB (mirrors settings.py's upload limits)."""
        image = self.cleaned_data["image"]
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("حجم تصویر رسید باید کمتر از ۵ مگابایت باشد.")
        return image
