from django.db import models
from django.utils import timezone
import uuid


def screenshot_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f'uploads/{instance.reference_id}.{ext}'


class ExchangeRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    WALLET_CHOICES = [
        ('waafi', 'Waafi Mobile Money'),
        ('cac', 'CAC International Bank'),
        ('dmoney', 'D-Money'),
        ('saba', 'Saba African Bank'),
    ]

    reference_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    wallet = models.CharField(max_length=20, choices=WALLET_CHOICES)
    amount_sent = models.DecimalField(max_digits=12, decimal_places=2)
    screenshot = models.ImageField(upload_to=screenshot_upload_path)
    moneygo_wallet = models.CharField(max_length=100, verbose_name='MoneyGo Wallet ID')
    whatsapp_number = models.CharField(max_length=30)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.TextField(blank=True, verbose_name='Admin Note')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exchange Request'
        verbose_name_plural = 'Exchange Requests'

    def __str__(self):
        return f'#{str(self.reference_id)[:8].upper()} — {self.get_wallet_display()} → MoneyGo'

    @property
    def short_ref(self):
        return str(self.reference_id)[:8].upper()

    @property
    def amount_to_receive(self):
        from exchange.constants import EXCHANGE_RATE
        return round(float(self.amount_sent) * EXCHANGE_RATE, 6)

    @property
    def status_badge_class(self):
        return {
            'pending': 'badge-pending',
            'processing': 'badge-processing',
            'completed': 'badge-completed',
            'rejected': 'badge-rejected',
        }.get(self.status, 'badge-pending')
