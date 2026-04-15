from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=30)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'


def screenshot_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f'uploads/{instance.reference_id}.{ext}'


class ExchangeRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_PROCESSING, 'En traitement'),
        (STATUS_COMPLETED, 'Envoyé'),
        (STATUS_REJECTED, 'Refusé'),
    ]

    WALLET_CHOICES = [
        ('waafi', 'Waafi Mobile Money'),
        ('cac', 'CAC International Bank'),
        ('dmoney', 'D-Money'),
        ('saba', 'Saba African Bank'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exchange_requests'
    )
    reference_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    wallet = models.CharField(max_length=20, choices=WALLET_CHOICES)
    amount_sent = models.DecimalField(max_digits=12, decimal_places=2)
    screenshot = models.ImageField(upload_to=screenshot_upload_path)
    moneygo_wallet = models.CharField(max_length=100, verbose_name='MoneyGo Wallet ID')
    whatsapp_number = models.CharField(max_length=30)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.TextField(blank=True, verbose_name='Note admin')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Demande d\'échange'
        verbose_name_plural = 'Demandes d\'échange'

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
