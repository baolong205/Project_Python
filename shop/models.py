from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category    = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    image       = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    stock       = models.IntegerField(default=0)
    rating      = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    @property
    def price_vnd(self):
        try:
            amount = int(self.price)
        except (ValueError, TypeError):
            return str(self.price)
        s = f"{amount:,}".replace(",", ".")
        return f"{s} VND"


class Order(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name   = models.CharField(max_length=255)
    address     = models.CharField(max_length=500)
    city        = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    created_at  = models.DateTimeField(auto_now_add=True)
    paid        = models.BooleanField(default=False)

    PAYMENT_CHOICES = [
        ('cod', 'Thanh toán khi nhận hàng'),
        ('bank', 'Chuyển khoản ngân hàng'),
        ('card', 'Thẻ ngân hàng'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('awaiting_shipment', 'Sắp được vận chuyển'),
        ('shipped', 'Đã vận chuyển'),
    ]

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='cod'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.username} ({self.get_status_display()})"

    @property
    def total_cost(self):
        return sum(item.cost for item in self.items.all())

    @property
    def total_cost_vnd(self):
        try:
            amount = int(self.total_cost)
        except (ValueError, TypeError):
            return str(self.total_cost)
        s = f"{amount:,}".replace(",", ".")
        return f"{s} VND"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def cost(self):
        return self.price * self.quantity

    @property
    def cost_vnd(self):
        try:
            amount = int(self.cost)
        except (ValueError, TypeError):
            return str(self.cost)
        s = f"{amount:,}".replace(",", ".")
        return f"{s} VND"

    @property
    def price_vnd(self):
        try:
            amount = int(self.price)
        except (ValueError, TypeError):
            return str(self.price)
        s = f"{amount:,}".replace(",", ".")
        return f"{s} VND"
