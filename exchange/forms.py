from django import forms
from django.contrib.auth.models import User
from .models import ExchangeRequest, UserProfile
import re


class UserRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Votre nom complet'}),
        label='Nom complet',
    )
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+253 77 XX XX XX'}),
        label='Numéro de téléphone',
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'votre@email.com'}),
        label='Adresse email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Minimum 8 caractères'}),
        label='Mot de passe',
        min_length=8,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirmez le mot de passe'}),
        label='Confirmer le mot de passe',
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Un compte avec cet email existe déjà.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise forms.ValidationError('Numéro de téléphone invalide.')
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', 'Les mots de passe ne correspondent pas.')
        return cleaned

    def save(self):
        email = self.cleaned_data['email']
        full_name = self.cleaned_data['full_name'].strip()
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        # username = email (unique)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
        )
        UserProfile.objects.create(user=user, phone_number=self.cleaned_data['phone'])
        return user


class UserExchangeForm(forms.ModelForm):
    """Formulaire de demande depuis le dashboard utilisateur (wallet choisi avant)."""
    class Meta:
        model = ExchangeRequest
        fields = ['amount_sent', 'screenshot', 'moneygo_wallet']
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
                'placeholder': 'Votre ID MoneyGo (ex: U123456789)',
            }),
        }
        labels = {
            'amount_sent': 'Montant envoyé (DJF)',
            'screenshot': 'Capture d\'écran de la transaction',
            'moneygo_wallet': 'Votre MoneyGo Wallet ID',
        }

    def clean_amount_sent(self):
        amount = self.cleaned_data.get('amount_sent')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Entrez un montant valide.')
        return amount

    def clean_screenshot(self):
        screenshot = self.cleaned_data.get('screenshot')
        if screenshot:
            allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
            if hasattr(screenshot, 'content_type') and screenshot.content_type not in allowed_types:
                raise forms.ValidationError('Seuls les formats PNG, JPG et WebP sont acceptés.')
            if screenshot.size > 70 * 1024 * 1024:
                raise forms.ValidationError('L\'image doit faire moins de 70 Mo.')
        return screenshot


class ExchangeForm(forms.ModelForm):
    """Formulaire public (ancienne page)."""
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
            if screenshot.size > 70 * 1024 * 1024:
                raise forms.ValidationError('Image must be smaller than 70 MB.')
        return screenshot

    def clean_whatsapp_number(self):
        number = self.cleaned_data.get('whatsapp_number', '').strip()
        cleaned = re.sub(r'[\s\-\(\)]', '', number)
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise forms.ValidationError('Please enter a valid phone number.')
        return number
