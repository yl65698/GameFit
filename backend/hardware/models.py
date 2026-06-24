from django.db import models
from accounts.models import User


class Hardware(models.Model):
    CATEGORY_CHOICES = [
        ('cpu', 'CPU'),
        ('gpu', 'GPU'),
        ('ram', 'RAM'),
        ('storage', 'Storage'),
        ('power', 'Power Supply'),
        ('monitor', 'Monitor'),
        ('mouse', 'Mouse'),
        ('keyboard', 'Keyboard'),
        ('headset', 'Headset'),
        ('motherboard', 'Motherboard'),
        ('cooler', 'Cooler'),
        ('case', 'Case'),
        ('vr', 'VR'),
        ('console', 'Console'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    manufacturer = models.CharField(max_length=100, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.IntegerField(default=0)
    image_url = models.URLField(blank=True, default='')
    specs = models.TextField(blank=True, default='')
    benchmark_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category.upper()}] {self.name}"


class UserHardware(models.Model):
    STATUS_CHOICES = [
        ('owned', '보유'),
        ('interested', '관심'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_hardware')
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, related_name='user_hardware')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='owned')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'hardware')

    def __str__(self):
        return f"{self.user.nickname} - {self.hardware.name}"


class HardwarePriceHistory(models.Model):
    """Naver 쇼핑 API 기반 장비 가격 변동 스냅샷 (가격변동 그래프용)"""
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, related_name='price_history')
    shop_name = models.CharField(max_length=200, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.IntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.hardware.name} ({self.recorded_at:%Y-%m-%d})"
