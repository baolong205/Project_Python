from django import forms
from .models import Product, Order


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'image', 'stock']


class CheckoutForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('cod',  'Thanh toán khi nhận hàng'),
        ('bank', 'Chuyển khoản ngân hàng'),
        ('card', 'Thẻ ngân hàng'),
    ]
    payment_method = forms.ChoiceField(
        label="Phương thức thanh toán",
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Order
        fields = ['full_name', 'address', 'city', 'postal_code', 'payment_method']
        labels = {
            'full_name': 'Họ và tên',
            'address': 'Địa chỉ giao hàng',
            'city': 'Thành phố',
            'postal_code': 'Mã bưu điện',
        }
