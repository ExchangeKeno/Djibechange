from django.contrib import admin
from .models import ExchangeRequest


@admin.register(ExchangeRequest)
class ExchangeRequestAdmin(admin.ModelAdmin):
    list_display = ['short_ref', 'wallet', 'amount_sent', 'moneygo_wallet', 'status', 'created_at']
    list_filter = ['status', 'wallet', 'created_at']
    search_fields = ['moneygo_wallet', 'email', 'whatsapp_number']
    readonly_fields = ['reference_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
