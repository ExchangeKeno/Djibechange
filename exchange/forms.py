from django import forms
from .models import ExchangeRequest
import re


class ExchangeForm(forms.ModelForm):
    class Meta:
        model = ExchangeRequest
        fields = ['amount_sent', 'screenshot', 'moneygo_wallet', 'whatsapp_number', 'email']
        widgets = {
            'amount_sent': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01',
            }),
            'screenshot': forms.ClearableFileInput(attrs={
                'class': 'form-input file-input',
                'accept': 'image/png,image/jpeg,image/jpg,image/webp',
            }),
            'moneygo_wallet': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your MoneyGo wallet ID (e.g. U123456789)',
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+253 77 XX XX XX',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your@email.com',
            }),
        }
        labels = {
            'amount_sent': 'Amount Sent',
            'screenshot': 'Transaction Screenshot',
            'moneygo_wallet': 'Your MoneyGo Wallet ID',
            'whatsapp_number': 'WhatsApp Number',
            'email': 'Email Address',
        }

    def clean_amount_sent(self):
        amount = self.cleaned_data.get('amount_sent')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Please enter a valid amount.')
        return amount

    def clean_screenshot(self):
        screenshot = self.cleaned_data.get('screenshot')
        if screenshot:
            allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
            if hasattr(screenshot, 'content_type') and screenshot.content_type not in allowed_types:
                raise forms.ValidationError('Only PNG, JPG, and WebP images are accepted.')
            if screenshot.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Image must be smaller than 10 MB.')
        return screenshot

    def clean_moneygo_wallet(self):
        wallet = self.cleaned_data.get('moneygo_wallet', '').strip()
        if not wallet:
            raise forms.ValidationError('Please enter your MoneyGo wallet ID.')
        return wallet

    def clean_whatsapp_number(self):
        number = self.cleaned_data.get('whatsapp_number', '').strip()
        cleaned = re.sub(r'[\s\-\(\)]', '', number)
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise forms.ValidationError('Please enter a valid phone number.')
        return number
