from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from .models import ExchangeRequest, UserProfile
from .forms import ExchangeForm, UserRegistrationForm, UserExchangeForm
from .constants import WALLETS, EXCHANGE_RATE, MIN_AMOUNT, MAX_AMOUNT
import json


# ── Pages publiques ────────────────────────────────────────────────────────────

def home(request):
    wallets = [{'key': k, **v} for k, v in WALLETS.items()]
    context = {
        'wallets': wallets,
        'exchange_rate': EXCHANGE_RATE,
        'min_amount': MIN_AMOUNT,
        'max_amount': MAX_AMOUNT,
    }
    return render(request, 'exchange/home.html', context)


def wallet_detail(request, wallet_key):
    if wallet_key not in WALLETS:
        messages.error(request, 'Wallet not found.')
        return redirect('home')
    wallet = {'key': wallet_key, **WALLETS[wallet_key]}
    form = ExchangeForm()
    if request.method == 'POST':
        form = ExchangeForm(request.POST, request.FILES)
        if form.is_valid():
            exchange = form.save(commit=False)
            exchange.wallet = wallet_key
            exchange.save()
            return redirect('exchange_success', ref=str(exchange.reference_id))
    context = {
        'wallet': wallet,
        'form': form,
        'exchange_rate': EXCHANGE_RATE,
        'min_amount': MIN_AMOUNT,
        'max_amount': MAX_AMOUNT,
    }
    return render(request, 'exchange/wallet_detail.html', context)


def exchange_success(request, ref):
    exchange = get_object_or_404(ExchangeRequest, reference_id=ref)
    return render(request, 'exchange/success.html', {'exchange': exchange})


def track_order(request):
    exchange = None
    ref = ''
    if request.method == 'POST':
        ref = request.POST.get('reference', '').strip()
        try:
            exchange = ExchangeRequest.objects.get(reference_id=ref)
        except (ExchangeRequest.DoesNotExist, Exception):
            messages.error(request, 'No order found with this reference ID.')
    return render(request, 'exchange/track.html', {'exchange': exchange, 'ref': ref})


def set_language(request):
    lang = request.POST.get('language', 'en')
    if lang in ('en', 'fr'):
        request.session['lang'] = lang
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ── Authentification utilisateur ───────────────────────────────────────────────

def user_register(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('user_dashboard')
    form = UserRegistrationForm()
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name} ! Votre compte a été créé.')
            return redirect('user_dashboard')
    return render(request, 'user/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dashboard')
        return redirect('user_dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('dashboard')
            return redirect('user_dashboard')
        messages.error(request, 'Email ou mot de passe incorrect.')
    return render(request, 'user/login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


# ── Dashboard utilisateur ──────────────────────────────────────────────────────

@login_required(login_url='/connexion/')
def user_dashboard(request):
    if request.user.is_staff:
        return redirect('dashboard')
    qs = ExchangeRequest.objects.filter(user=request.user)
    stats = {
        'total':      qs.count(),
        'pending':    qs.filter(status='pending').count(),
        'processing': qs.filter(status='processing').count(),
        'completed':  qs.filter(status='completed').count(),
        'rejected':   qs.filter(status='rejected').count(),
    }
    recent = qs[:10]
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    context = {
        'stats': stats,
        'recent': recent,
        'wallets': WALLETS,
        'profile': profile,
    }
    return render(request, 'user/dashboard.html', context)


@login_required(login_url='/connexion/')
def user_new_request(request):
    if request.user.is_staff:
        return redirect('dashboard')
    wallet_key = request.GET.get('wallet', '')
    if wallet_key not in WALLETS:
        wallet_key = ''
    wallet = {'key': wallet_key, **WALLETS[wallet_key]} if wallet_key else None
    form = UserExchangeForm()
    if request.method == 'POST':
        wallet_key = request.POST.get('wallet_key', '')
        if wallet_key not in WALLETS:
            messages.error(request, 'Veuillez sélectionner un portefeuille valide.')
            return redirect('user_new_request')
        form = UserExchangeForm(request.POST, request.FILES)
        if form.is_valid():
            exchange = form.save(commit=False)
            exchange.wallet = wallet_key
            exchange.user = request.user
            exchange.whatsapp_number = getattr(request.user.profile, 'phone_number', '')
            exchange.email = request.user.email
            exchange.save()
            messages.success(request, 'Votre demande a été soumise avec succès !')
            return redirect('user_request_detail', pk=exchange.pk)
    context = {
        'form': form,
        'wallets': WALLETS,
        'wallet': wallet,
        'wallet_key': wallet_key,
        'exchange_rate': EXCHANGE_RATE,
        'min_amount': MIN_AMOUNT,
        'max_amount': MAX_AMOUNT,
    }
    return render(request, 'user/new_request.html', context)


@login_required(login_url='/connexion/')
def user_request_detail(request, pk):
    if request.user.is_staff:
        return redirect('dashboard')
    exchange = get_object_or_404(ExchangeRequest, pk=pk, user=request.user)
    status_order = ['pending', 'processing', 'completed']
    current_idx = status_order.index(exchange.status) if exchange.status in status_order else -1
    steps = []
    for i, (key, label, icon) in enumerate([
        ('pending',    'En attente',   '⏳'),
        ('processing', 'En traitement','⚡'),
        ('completed',  'Envoyé',       '✅'),
    ]):
        steps.append((key, label, icon))
    return render(request, 'user/request_detail.html', {
        'exchange': exchange,
        'wallets': WALLETS,
        'steps': steps,
        'step_reached': current_idx,
    })


@login_required(login_url='/connexion/')
def user_requests(request):
    if request.user.is_staff:
        return redirect('dashboard')
    qs = ExchangeRequest.objects.filter(user=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'user/requests.html', {
        'requests': qs,
        'wallets': WALLETS,
        'status_filter': status_filter,
        'status_choices': ExchangeRequest.STATUS_CHOICES,
    })


# ── Dashboard admin ────────────────────────────────────────────────────────────

def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Identifiants invalides ou permissions insuffisantes.')
    return render(request, 'dashboard/login.html')


def dashboard_logout(request):
    logout(request)
    return redirect('home')


def _get_sidebar_counts():
    qs = ExchangeRequest.objects
    return {
        'count_pending':    qs.filter(status='pending').count(),
        'count_processing': qs.filter(status='processing').count(),
        'count_completed':  qs.filter(status='completed').count(),
        'count_rejected':   qs.filter(status='rejected').count(),
        'count_total':      qs.count(),
    }


@login_required(login_url='/dashboard/login/')
def dashboard(request):
    requests_qs = ExchangeRequest.objects.all()
    pending_qs = requests_qs.filter(status='pending')
    stats = {
        'total':      requests_qs.count(),
        'pending':    pending_qs.count(),
        'processing': requests_qs.filter(status='processing').count(),
        'completed':  requests_qs.filter(status='completed').count(),
        'rejected':   requests_qs.filter(status='rejected').count(),
    }
    wallet_stats = (
        requests_qs.values('wallet')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    context = {
        'stats': stats,
        'wallet_stats': wallet_stats,
        'pending_requests': pending_qs,
        'wallets': WALLETS,
        **_get_sidebar_counts(),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='/dashboard/login/')
def dashboard_requests(request):
    qs = ExchangeRequest.objects.all()
    status_filter  = request.GET.get('status', '')
    wallet_filter  = request.GET.get('wallet', '')
    search         = request.GET.get('q', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if wallet_filter:
        qs = qs.filter(wallet=wallet_filter)
    if search:
        qs = qs.filter(
            Q(moneygo_wallet__icontains=search) |
            Q(email__icontains=search) |
            Q(whatsapp_number__icontains=search)
        )
    context = {
        'requests': qs,
        'wallets': WALLETS,
        'status_filter': status_filter,
        'wallet_filter': wallet_filter,
        'search': search,
        'status_choices': ExchangeRequest.STATUS_CHOICES,
        **_get_sidebar_counts(),
    }
    return render(request, 'dashboard/requests.html', context)


@login_required(login_url='/dashboard/login/')
def dashboard_request_detail(request, pk):
    exchange = get_object_or_404(ExchangeRequest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_note = request.POST.get('admin_note', '')
        if new_status in dict(ExchangeRequest.STATUS_CHOICES):
            exchange.status = new_status
            exchange.admin_note = admin_note
            exchange.save()
            messages.success(request, f'Demande mise à jour : {exchange.get_status_display()}.')
            return redirect('dashboard_request_detail', pk=pk)
    context = {
        'exchange': exchange,
        'wallets': WALLETS,
        'status_choices': ExchangeRequest.STATUS_CHOICES,
        **_get_sidebar_counts(),
    }
    return render(request, 'dashboard/request_detail.html', context)


@login_required(login_url='/dashboard/login/')
@require_POST
def dashboard_update_status(request, pk):
    exchange = get_object_or_404(ExchangeRequest, pk=pk)
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        admin_note = data.get('admin_note', '')
        if new_status in dict(ExchangeRequest.STATUS_CHOICES):
            exchange.status = new_status
            if admin_note:
                exchange.admin_note = admin_note
            exchange.save()
            return JsonResponse({
                'success': True,
                'status': exchange.get_status_display(),
                'status_key': exchange.status,
            })
    except Exception:
        pass
    return JsonResponse({'success': False}, status=400)


@login_required(login_url='/dashboard/login/')
def dashboard_history_sent(request):
    qs = ExchangeRequest.objects.filter(status='completed').order_by('-updated_at')
    search = request.GET.get('q', '')
    wallet_filter = request.GET.get('wallet', '')
    if search:
        qs = qs.filter(
            Q(moneygo_wallet__icontains=search) |
            Q(email__icontains=search) |
            Q(whatsapp_number__icontains=search)
        )
    if wallet_filter:
        qs = qs.filter(wallet=wallet_filter)
    context = {
        'requests': qs,
        'wallets': WALLETS,
        'search': search,
        'wallet_filter': wallet_filter,
        **_get_sidebar_counts(),
    }
    return render(request, 'dashboard/history_sent.html', context)


@login_required(login_url='/dashboard/login/')
def dashboard_history_rejected(request):
    qs = ExchangeRequest.objects.filter(status='rejected').order_by('-updated_at')
    search = request.GET.get('q', '')
    wallet_filter = request.GET.get('wallet', '')
    if search:
        qs = qs.filter(
            Q(moneygo_wallet__icontains=search) |
            Q(email__icontains=search) |
            Q(whatsapp_number__icontains=search)
        )
    if wallet_filter:
        qs = qs.filter(wallet=wallet_filter)
    context = {
        'requests': qs,
        'wallets': WALLETS,
        'search': search,
        'wallet_filter': wallet_filter,
        **_get_sidebar_counts(),
    }
    return render(request, 'dashboard/history_rejected.html', context)
