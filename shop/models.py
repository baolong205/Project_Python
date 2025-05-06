# -*- shop/models.py-*-
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.db.models import Avg

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
    brand = models.CharField("Thương hiệu", max_length=100, blank=True)
    category    = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    image       = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    stock       = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def price_vnd(self):
        amt = int(self.price)
        s = f"{amt:,}".replace(",", ".")
        return f"{s} VND"

    @property
    def avg_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return avg or 0.0

    @property
    def avg_stars(self):
        # trả về range cho template lặp
        return range(int(self.avg_rating))


class Review(models.Model):
    RATING_CHOICES = [(i, f"{i} sao") for i in range(1, 6)]  # 1..5

    product    = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating     = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} đánh giá {self.product.name}"

    @property
    def stars(self):
        # trả về range để template hiển thị đúng số sao
        return range(self.rating)


class Order(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name   = models.CharField(max_length=255)
    address     = models.CharField(max_length=500)
    city        = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    created_at  = models.DateTimeField(auto_now_add=True)
    paid        = models.BooleanField(default=False)

    PAYMENT_CHOICES = [
        ('cod',  'Thanh toán khi nhận hàng'),
        ('bank', 'Chuyển khoản ngân hàng'),
        ('card', 'Thẻ ngân hàng'),
    ]
    STATUS_CHOICES = [
        ('pending',           'Chờ xử lý'),
        ('awaiting_shipment', 'Sắp được vận chuyển'),
        ('shipped',           'Đã vận chuyển'),
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
        amt = int(self.total_cost)
        s = f"{amt:,}".replace(",", ".")
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
        amt = int(self.cost)
        s = f"{amt:,}".replace(",", ".")
        return f"{s} VND"

    @property
    def price_vnd(self):
        amt = int(self.price)
        s = f"{amt:,}".replace(",", ".")
        return f"{s} VND"
